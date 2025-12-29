"""
HTTP extraction utilities for ETL orchestrator.

This module handles:
- HTTP request configuration
- Retry logic
- Response parsing
- Data extraction from various response formats
- Pagination support (page, offset, cursor, next_url, link_header)
- Streaming extraction for high-volume data
"""

import asyncio
import re
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from pycharter.utils.value_injector import resolve_values


# Default configuration values
DEFAULT_RATE_LIMIT_DELAY = 0.2
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BACKOFF_FACTOR = 2.0
DEFAULT_RETRY_STATUS_CODES = [429, 500, 502, 503, 504]
DEFAULT_TIMEOUT_CONNECT = 10.0
DEFAULT_TIMEOUT_READ = 30.0
DEFAULT_TIMEOUT_WRITE = 10.0
DEFAULT_TIMEOUT_POOL = 10.0

# Common response data keys
RESPONSE_DATA_KEYS = ['data', 'results', 'items', 'records', 'values']


def resolve_rate_limit_delay(
    rate_limit_delay: Any,
    contract_dir: Optional[Any] = None,
    config_context: Optional[Dict[str, Any]] = None,
) -> float:
    """Resolve and convert rate_limit_delay to float."""
    if isinstance(rate_limit_delay, str):
        source_file = str(contract_dir / "extract.yaml") if contract_dir else None
        resolved = resolve_values(rate_limit_delay, context=config_context, source_file=source_file)
        return float(resolved)
    return float(rate_limit_delay)


def build_request_url(
    base_url: str,
    api_endpoint: str,
    path_params: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build full request URL from base URL and endpoint, with optional path parameter substitution.
    
    Args:
        base_url: Base URL (e.g., 'https://api.example.com')
        api_endpoint: API endpoint (e.g., '/v1/data' or '/v2/aggs/ticker/{symbol}/range/1/day/{start_date}/{end_date}')
        path_params: Optional dictionary of path parameters to substitute (e.g., {'symbol': 'AAPL', 'start_date': '2024-01-01'})
        
    Returns:
        Full URL with path parameters substituted
        
    Raises:
        ValueError: If URL cannot be constructed or required path parameters are missing
    """
    if api_endpoint.startswith(('http://', 'https://')):
        url = api_endpoint
    elif base_url:
        base_url = base_url.rstrip('/')
        endpoint = api_endpoint.lstrip('/')
        url = f"{base_url}/{endpoint}"
    else:
        raise ValueError(
            "Either 'api_endpoint' must be a full URL (starting with http:// or https://) "
            "or 'base_url' must be provided in extract.yaml"
        )
    
    # Substitute path parameters (e.g., {symbol} -> AAPL)
    if path_params and '{' in url:
        try:
            url = url.format(**path_params)
        except KeyError as e:
            raise ValueError(
                f"Missing required path parameter in URL: {e}. "
                f"URL: {url}, Available params: {list(path_params.keys())}"
            ) from e
    
    return url


def configure_timeout(timeout_config: Dict[str, Any]) -> httpx.Timeout:
    """Configure HTTP timeout from config dictionary."""
    return httpx.Timeout(
        connect=float(timeout_config.get('connect', DEFAULT_TIMEOUT_CONNECT)),
        read=float(timeout_config.get('read', DEFAULT_TIMEOUT_READ)),
        write=float(timeout_config.get('write', DEFAULT_TIMEOUT_WRITE)),
        pool=float(timeout_config.get('pool', DEFAULT_TIMEOUT_POOL)),
    )


def extract_by_path(data: Any, path: str) -> List[Dict[str, Any]]:
    """
    Extract data using a simple path notation (e.g., 'data.items').
    
    Args:
        data: Data structure to traverse
        path: Dot-separated path (e.g., 'data.items')
        
    Returns:
        List of records
    """
    current = data
    for part in path.split('.'):
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and part.isdigit():
            current = current[int(part)]
        else:
            return []
        
        if current is None:
            return []
    
    if isinstance(current, list):
        return current
    elif isinstance(current, dict):
        return [current]
    else:
        return []


def extract_data_array(data: Any) -> List[Dict[str, Any]]:
    """
    Extract data array from response, handling common response structures.
    
    Args:
        data: Response data (dict, list, or other)
        
    Returns:
        List of records
    """
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        # Try common keys for data arrays
        for key in RESPONSE_DATA_KEYS:
            if key in data and isinstance(data[key], list):
                return data[key]
        # If no array found, return as single-item list
        return [data]
    else:
        return []


async def make_http_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    params: Dict[str, Any],
    headers: Dict[str, Any],
    body: Optional[Any] = None,
) -> httpx.Response:
    """
    Make HTTP request with specified method.
    
    Args:
        client: HTTPX async client
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        params: Query parameters
        headers: Request headers
        body: Request body (for POST requests)
        
    Returns:
        HTTP response
        
    Raises:
        ValueError: If method is unsupported
    """
    method = method.upper()
    
    if method == 'GET':
        return await client.get(url, params=params, headers=headers)
    elif method == 'POST':
        if body:
            return await client.post(
                url,
                json=body if isinstance(body, dict) else body,
                params=params,
                headers=headers,
            )
        else:
            return await client.post(url, params=params, headers=headers)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")


async def _extract_single_page(
    extract_config: Dict[str, Any],
    params: Dict[str, Any],
    headers: Dict[str, Any],
    contract_dir: Optional[Any] = None,
    return_full_response: bool = False,
    config_context: Optional[Dict[str, Any]] = None,
) -> tuple[List[Dict[str, Any]], Optional[Any], Optional[httpx.Response]]:
    """
    Extract data from a single API request with retry logic.
    
    Args:
        extract_config: Extract configuration dictionary
        params: Request parameters
        headers: Request headers
        contract_dir: Contract directory (for variable resolution)
        return_full_response: If True, also return full response data and response object
        
    Returns:
        Tuple of (extracted_data, full_response_data, response_object)
        - extracted_data: List of extracted records
        - full_response_data: Full response JSON/data (None if return_full_response=False)
        - response_object: HTTP response object (None if return_full_response=False)
        
    Raises:
        RuntimeError: If extraction fails after all retries
    """
    # Get configuration
    base_url = extract_config.get('base_url', '')
    api_endpoint = extract_config.get('api_endpoint', '')
    method = extract_config.get('method', 'GET').upper()
    timeout_config = extract_config.get('timeout', {})
    retry_config = extract_config.get('retry', {})
    response_path = extract_config.get('response_path')
    response_format = extract_config.get('response_format', 'json')
    rate_limit_delay = extract_config.get('rate_limit_delay', DEFAULT_RATE_LIMIT_DELAY)
    body = extract_config.get('body')
    
    # Resolve variables and convert types
    source_file = str(contract_dir / "extract.yaml") if contract_dir else None
    resolved_params = resolve_values(params, context=config_context, source_file=source_file)
    resolved_headers = resolve_values(headers, context=config_context, source_file=source_file)
    resolved_timeout_config = resolve_values(timeout_config, context=config_context, source_file=source_file)
    resolved_rate_limit_delay = resolve_rate_limit_delay(rate_limit_delay, contract_dir, config_context=config_context)
    
    if body:
        resolved_body = resolve_values(body, context=config_context, source_file=source_file)
    else:
        resolved_body = None
    
    # Extract path parameters from api_endpoint (e.g., {symbol}, {start_date})
    # These should be removed from query params and used in URL substitution
    path_params = {}
    if '{' in api_endpoint:
        # Find all {param} patterns in the endpoint
        path_param_names = re.findall(r'\{(\w+)\}', api_endpoint)
        for param_name in path_param_names:
            if param_name in resolved_params:
                path_params[param_name] = resolved_params.pop(param_name)
    
    # Build URL with path parameter substitution
    url = build_request_url(base_url, api_endpoint, path_params)
    
    # Configure timeout
    timeout = configure_timeout(resolved_timeout_config)
    
    # Configure retry
    max_attempts = int(retry_config.get('max_attempts', DEFAULT_MAX_ATTEMPTS))
    backoff_factor = float(retry_config.get('backoff_factor', DEFAULT_BACKOFF_FACTOR))
    retry_on_status = retry_config.get('retry_on_status', DEFAULT_RETRY_STATUS_CODES)
    
    # Make request with retry logic
    last_exception = None
    for attempt in range(max_attempts):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Check if we should retry based on previous response
                if attempt > 0:
                    wait_time = backoff_factor ** (attempt - 1)
                    await asyncio.sleep(wait_time)
                
                response = await make_http_request(
                    client, method, url, resolved_params, resolved_headers, resolved_body
                )
                
                # Check if we should retry based on status code
                if response.status_code in retry_on_status and attempt < max_attempts - 1:
                    wait_time = backoff_factor ** attempt
                    await asyncio.sleep(wait_time)
                    continue
                
                # Raise for non-2xx status codes
                response.raise_for_status()
                
                # Parse response
                if response_format == 'json':
                    data = response.json()
                else:
                    data = response.text
                
                # Extract data array
                if response_path:
                    extracted_data = extract_by_path(data, response_path)
                else:
                    extracted_data = extract_data_array(data)
                
                # Apply rate limiting delay
                if resolved_rate_limit_delay > 0:
                    await asyncio.sleep(resolved_rate_limit_delay)
                
                if return_full_response:
                    return extracted_data, data, response
                return extracted_data, None, None
                
        except httpx.HTTPStatusError as e:
            last_exception = e
            if e.response.status_code in retry_on_status and attempt < max_attempts - 1:
                wait_time = backoff_factor ** attempt
                await asyncio.sleep(wait_time)
                continue
            raise RuntimeError(
                f"HTTP error {e.response.status_code}: {e.response.text}"
            ) from e
        except (httpx.RequestError, httpx.TimeoutException) as e:
            last_exception = e
            if attempt < max_attempts - 1:
                wait_time = backoff_factor ** attempt
                await asyncio.sleep(wait_time)
                continue
            raise RuntimeError(f"Request failed: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Extraction failed: {e}") from e
    
    # If we exhausted all retries
    if last_exception:
        raise RuntimeError(
            f"Extraction failed after {max_attempts} attempts: {last_exception}"
        ) from last_exception
    raise RuntimeError("Extraction failed: unknown error")


async def extract_with_retry(
    extract_config: Dict[str, Any],
    params: Dict[str, Any],
    headers: Dict[str, Any],
    contract_dir: Optional[Any] = None,
    config_context: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Extract data from API with retry logic.
    
    Args:
        extract_config: Extract configuration dictionary
        params: Request parameters
        headers: Request headers
        contract_dir: Contract directory (for variable resolution)
        config_context: Optional context dictionary for value injection
        
    Returns:
        List of extracted records
        
    Raises:
        RuntimeError: If extraction fails after all retries
    """
    extracted_data, _, _ = await _extract_single_page(
        extract_config, params, headers, contract_dir, return_full_response=False, config_context=config_context
    )
    return extracted_data


def _check_stop_conditions(
    page_data: List[Dict[str, Any]],
    stop_conditions: List[Dict[str, Any]],
    params: Dict[str, Any],
    response_data: Any = None,
) -> bool:
    """
    Check if pagination should stop based on configured stop conditions.
    
    Args:
        page_data: Data from current page
        stop_conditions: List of stop condition configurations
        params: Current request parameters
        response_data: Full response data (for custom conditions)
        
    Returns:
        True if pagination should stop, False otherwise
    """
    if not stop_conditions:
        # Default: stop if fewer records than limit
        limit = params.get('limit', 100)
        return len(page_data) < limit
    
    for condition in stop_conditions:
        condition_type = condition.get('type')
        
        if condition_type == 'empty_response':
            if not page_data:
                return True
        
        elif condition_type == 'fewer_records':
            limit = params.get('limit', 100)
            if len(page_data) < limit:
                return True
        
        elif condition_type == 'max_pages':
            max_pages = condition.get('value', 1000)
            current_page = params.get('page', 0)
            if current_page >= max_pages:
                return True
        
        elif condition_type == 'max_records':
            # This would need to be tracked externally
            max_records = condition.get('value', 10000)
            # Note: This requires total count tracking, which is handled in extract_with_pagination
            pass
        
        elif condition_type == 'custom':
            # Custom condition based on response path
            response_path = condition.get('response_path')
            expected_value = condition.get('value')
            if response_path and response_data:
                try:
                    current = response_data
                    for part in response_path.split('.'):
                        if isinstance(current, dict):
                            current = current.get(part)
                        elif isinstance(current, list) and part.isdigit():
                            current = current[int(part)]
                        else:
                            break
                    if current == expected_value:
                        return True
                except (KeyError, IndexError, TypeError):
                    pass
    
    return False


def _extract_link_header_url(response: httpx.Response) -> Optional[str]:
    """
    Extract next URL from Link header (RFC 5988).
    
    Args:
        response: HTTP response with Link header
        
    Returns:
        Next URL if found, None otherwise
    """
    link_header = response.headers.get('Link', '')
    if not link_header:
        return None
    
    # Parse Link header: <url>; rel="next"
    pattern = r'<([^>]+)>;\s*rel=["\']?next["\']?'
    match = re.search(pattern, link_header, re.IGNORECASE)
    if match:
        return match.group(1)
    
    return None


async def extract_with_pagination_streaming(
    extract_config: Dict[str, Any],
    params: Dict[str, Any],
    headers: Dict[str, Any],
    contract_dir: Optional[Any] = None,
    batch_size: int = 1000,
    max_records: Optional[int] = None,
    config_context: Optional[Dict[str, Any]] = None,
) -> AsyncIterator[List[Dict[str, Any]]]:
    """
    Extract data with pagination support, yielding batches for memory-efficient processing.
    
    Yields batches as they are extracted, preventing memory exhaustion for large datasets.
    
    Args:
        extract_config: Extract configuration dictionary
        params: Request parameters
        headers: Request headers
        contract_dir: Contract directory (for variable resolution)
        batch_size: Number of records to yield per batch
        max_records: Maximum total records to extract (None = all)
    
    Yields:
        Batches of extracted records (lists of dictionaries)
    """
    pagination_config = extract_config.get('pagination', {})
    
    # If pagination is not enabled, extract all and yield in batches
    if not pagination_config.get('enabled', False):
        all_data = await extract_with_retry(extract_config, params, headers, contract_dir, config_context=config_context)
        if max_records:
            all_data = all_data[:max_records]
        
        for i in range(0, len(all_data), batch_size):
            yield all_data[i:i + batch_size]
        return
    
    # Pagination enabled - stream pages and yield in batches
    strategy = pagination_config.get('strategy', 'page')
    stop_conditions = pagination_config.get('stop_conditions', [])
    page_delay = float(pagination_config.get('page_delay', 0.1))
    max_pages = 1000
    max_records_from_config = None
    
    # Get max_pages and max_records from stop conditions
    for condition in stop_conditions:
        if condition.get('type') == 'max_pages':
            max_pages = condition.get('value', 1000)
        elif condition.get('type') == 'max_records':
            max_records_from_config = condition.get('value')
    
    # Use config max_records if not provided as parameter
    if max_records is None:
        max_records = max_records_from_config
    
    current_batch = []
    total_extracted = 0
    page_count = 0
    current_url = None
    current_cursor = None
    
    # Initialize pagination state
    if strategy == 'page':
        page_config = pagination_config.get('page', {})
        current_page = page_config.get('start', 0)
        page_increment = page_config.get('increment', 1)
        page_param_name = page_config.get('param_name', 'page')
    elif strategy == 'offset':
        offset_config = pagination_config.get('offset', {})
        current_offset = offset_config.get('start', 0)
        offset_param_name = offset_config.get('param_name', 'offset')
        increment_by = offset_config.get('increment_by', 'limit')
    elif strategy == 'cursor':
        cursor_config = pagination_config.get('cursor', {})
        cursor_param_name = cursor_config.get('param_name', 'cursor')
        cursor_response_path = cursor_config.get('response_path', 'next_cursor')
    elif strategy == 'next_url':
        next_url_config = pagination_config.get('next_url', {})
        next_url_response_path = next_url_config.get('response_path', 'next_url')
    elif strategy == 'link_header':
        pass
    else:
        raise ValueError(f"Unsupported pagination strategy: {strategy}")
    
    extract_config_copy = extract_config.copy()
    original_endpoint = extract_config_copy.get('api_endpoint')
    original_base_url = extract_config_copy.get('base_url', '')
    
    while page_count < max_pages:
        # Check max_records limit
        if max_records and total_extracted >= max_records:
            if current_batch:
                yield current_batch
            return
        
        # Update params/URL based on strategy
        if strategy == 'page':
            params[page_param_name] = current_page
        elif strategy == 'offset':
            params[offset_param_name] = current_offset
        elif strategy == 'cursor' and current_cursor:
            params[cursor_param_name] = current_cursor
        elif strategy == 'next_url' and current_url:
            extract_config_copy['api_endpoint'] = current_url
            extract_config_copy['base_url'] = ''
        
        # Make request
        need_full_response = strategy in ['cursor', 'next_url', 'link_header']
        try:
            page_data, full_response_data, response_obj = await _extract_single_page(
                extract_config_copy, params, headers, contract_dir, return_full_response=need_full_response, config_context=config_context
            )
        except Exception as e:
            # Yield what we have so far before raising
            if current_batch:
                yield current_batch
            raise
        
        # Restore original endpoint if modified
        if strategy == 'next_url' and current_url:
            extract_config_copy['api_endpoint'] = original_endpoint
            extract_config_copy['base_url'] = original_base_url
        
        # Check stop conditions
        if not page_data:
            if current_batch:
                yield current_batch
            break
        
        # Add page data to current batch
        for record in page_data:
            current_batch.append(record)
            total_extracted += 1
            
            # Yield batch when full
            if len(current_batch) >= batch_size:
                yield current_batch
                current_batch = []
            
            # Check max_records limit
            if max_records and total_extracted >= max_records:
                if current_batch:
                    yield current_batch
                return
        
        page_count += 1
        
        # Check stop conditions
        should_stop = _check_stop_conditions(page_data, stop_conditions, params, full_response_data)
        if should_stop:
            if current_batch:
                yield current_batch
            break
        
        # Extract pagination token/URL for next iteration
        if strategy == 'cursor' and full_response_data:
            try:
                current = full_response_data
                for part in cursor_response_path.split('.'):
                    if isinstance(current, dict):
                        current = current.get(part)
                    elif isinstance(current, list) and part.isdigit():
                        current = current[int(part)]
                    else:
                        current = None
                        break
                
                if current and isinstance(current, str):
                    current_cursor = current
                elif current:
                    current_cursor = str(current)
                else:
                    if current_batch:
                        yield current_batch
                    break
            except (KeyError, IndexError, TypeError, ValueError):
                if current_batch:
                    yield current_batch
                break
        
        elif strategy == 'next_url' and full_response_data:
            try:
                current = full_response_data
                for part in next_url_response_path.split('.'):
                    if isinstance(current, dict):
                        current = current.get(part)
                    elif isinstance(current, list) and part.isdigit():
                        current = current[int(part)]
                    else:
                        current = None
                        break
                
                if current and isinstance(current, str):
                    current_url = current
                else:
                    current_url = None
                
                if not current_url:
                    if current_batch:
                        yield current_batch
                    break
            except (KeyError, IndexError, TypeError, ValueError):
                if current_batch:
                    yield current_batch
                break
        
        elif strategy == 'link_header' and response_obj:
            current_url = _extract_link_header_url(response_obj)
            if not current_url:
                if current_batch:
                    yield current_batch
                break
            extract_config_copy['api_endpoint'] = current_url
            extract_config_copy['base_url'] = ''
        
        # Update pagination state
        if strategy == 'page':
            current_page += page_increment
        elif strategy == 'offset':
            limit = params.get('limit', 100)
            if increment_by == 'limit':
                current_offset += limit
            else:
                current_offset += int(increment_by)
        
        # Delay between pages
        if page_delay > 0:
            await asyncio.sleep(page_delay)
    
    # Yield remaining records
    if current_batch:
        yield current_batch
