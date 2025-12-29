"""Module for RPC client handling Matrice.ai backend API requests."""

import os
import logging
import time
import threading
from datetime import datetime, timedelta, timezone
from importlib.metadata import version
from typing import Optional, Dict, Any, Tuple, Callable, List
from concurrent.futures import ThreadPoolExecutor, Future
import requests
from .token_auth import (
    AuthToken,
    RefreshToken,
)
from .utils import log_errors


class RPC:
    """RPC class for handling backend API requests with token-based authentication."""

    def __init__(
        self,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        project_id: Optional[str] = None,
        base_url: Optional[str] = None,
        max_workers: int = 5,
    ) -> None:
        """Initialize the RPC client with optional project ID and base URL.
        
        Args:
            access_key: API access key (or set MATRICE_ACCESS_KEY_ID env var)
            secret_key: API secret key (or set MATRICE_SECRET_ACCESS_KEY env var)
            project_id: Optional project ID to include in requests
            base_url: Optional custom base URL
            max_workers: Maximum number of workers for background request queue (default: 5)
        """
        self.project_id: Optional[str] = project_id
        self.BASE_URL: str = base_url or (
            f"https://{os.environ.get('ENV', 'prod')}.backend.app.matrice.ai"
        )

        access_key = access_key or os.environ.get("MATRICE_ACCESS_KEY_ID")
        secret_key = secret_key or os.environ.get("MATRICE_SECRET_ACCESS_KEY")

        if not access_key or not secret_key:
            raise ValueError(
                "Access key and Secret key are required. "
                "Set them as environment variables MATRICE_ACCESS_KEY_ID and MATRICE_SECRET_ACCESS_KEY or pass them explicitly."
            )

        os.environ["MATRICE_ACCESS_KEY_ID"] = access_key
        os.environ["MATRICE_SECRET_ACCESS_KEY"] = secret_key

        self.access_key: str = access_key
        self.secret_key: str = secret_key
        self.Refresh_Token: RefreshToken = RefreshToken(access_key, secret_key)
        self.AUTH_TOKEN: AuthToken = AuthToken(
            access_key,
            secret_key,
            self.Refresh_Token,
        )
        self.url_projectID: str = f"projectId={self.project_id}" if self.project_id else ""
        try:
            self.sdk_version: str = version("matrice")
        except Exception:
            self.sdk_version: str = "0.0.0"
        
        # Store max_workers for recreating executor after unpickling
        self._max_workers: int = max_workers
        
        # Thread pool for background requests
        self._executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=max_workers)
        self._background_futures: List[Future] = []
        self._futures_lock: threading.Lock = threading.Lock()
        self._shutdown: bool = False

    @log_errors(default_return=None, raise_exception=True, log_error=True)
    def send_request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        timeout: int = 120,
        raise_exception: bool = True,
        base_url: Optional[str] = None,
        max_retries: int = 0,
        retry_delay: float = 1.0,
        exponential_backoff: bool = True,
        default_return_value: Optional[Dict[str, Any]] = None,
        background: bool = False,
        on_complete: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Send an HTTP request to the specified endpoint with retry and background execution support.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: API endpoint path
            headers: Optional request headers
            payload: Optional JSON payload
            files: Optional files to upload
            data: Optional raw data
            timeout: Request timeout in seconds (default: 60)
            raise_exception: Whether to raise exceptions on error (default: True)
            base_url: Optional custom base URL
            max_retries: Maximum number of retry attempts on failure (default: 0)
            retry_delay: Initial delay between retries in seconds (default: 1.0)
            exponential_backoff: Whether to use exponential backoff for retries (default: True)
            default_return_value: Value to return on failure when raise_exception=False
            background: Execute request in background without blocking (default: False)
            on_complete: Optional callback function to call with the result when background=True
            
        Returns:
            Response data dict, or None if background=True
        """
        if self._shutdown:
            raise RuntimeError("RPC client has been shutdown and cannot accept new requests")
        
        if background:
            # Queue the request for background execution
            future = self._executor.submit(
                self._execute_request,
                method=method,
                path=path,
                headers=headers,
                payload=payload,
                files=files,
                data=data,
                timeout=timeout,
                raise_exception=False,  # Don't raise in background - use callback instead
                base_url=base_url,
                max_retries=max_retries,
                retry_delay=retry_delay,
                exponential_backoff=exponential_backoff,
                default_return_value=default_return_value,
            )
            
            # Add callback if provided
            if on_complete:
                def safe_callback(f: Future) -> None:
                    try:
                        exc = f.exception()
                        if exc is None:
                            on_complete(f.result())
                        else:
                            logging.error(f"Background request failed with exception: {exc}")
                            if default_return_value is not None:
                                on_complete(default_return_value)
                            else:
                                on_complete({"success": False, "data": None, "error": str(exc)})
                    except Exception as callback_error:
                        logging.error(f"Error in on_complete callback: {callback_error}")
                
                future.add_done_callback(safe_callback)
            
            with self._futures_lock:
                self._background_futures.append(future)
            
            logging.debug(f"Queued background request: {method} {path}")
            return None
        
        # Execute request synchronously
        return self._execute_request(
            method=method,
            path=path,
            headers=headers,
            payload=payload,
            files=files,
            data=data,
            timeout=timeout,
            raise_exception=raise_exception,
            base_url=base_url,
            max_retries=max_retries,
            retry_delay=retry_delay,
            exponential_backoff=exponential_backoff,
            default_return_value=default_return_value,
        )

    def _execute_request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        timeout: int = 120,
        raise_exception: bool = True,
        base_url: Optional[str] = None,
        max_retries: int = 0,
        retry_delay: float = 1.0,
        exponential_backoff: bool = True,
        default_return_value: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Internal method to execute HTTP request with retry logic."""
        if default_return_value is None:
            default_return_value = {"success": False, "data": None, "error": None}
        
        self.refresh_token()
        request_base_url = base_url or self.BASE_URL
        request_url = f"{request_base_url}{path}"
        request_url = self.add_project_id(request_url)

        if headers is None:
            headers = {}
        if payload is None:
            payload = {}

        headers["sdk_version"] = self.sdk_version
        
        last_exception: Optional[Exception] = None
        current_delay = retry_delay
        total_attempts = max_retries + 1
        
        # Attempt request with retries
        for attempt in range(total_attempts):
            response = None
            try:
                response = requests.request(
                    method,
                    request_url,
                    auth=self.AUTH_TOKEN,
                    headers=headers,
                    json=payload if payload else None,
                    data=data,
                    files=files,
                    timeout=timeout,
                    allow_redirects=True,
                )
                response.raise_for_status()
                response_data = response.json()
                
                # Log retry success if this wasn't the first attempt
                if attempt > 0:
                    logging.info(f"Request succeeded on attempt {attempt + 1}/{total_attempts}")
                
                return response_data
                
            except Exception as e:
                last_exception = e
                
                # Safely extract response information
                if response is not None:
                    try:
                        response_text = response.text
                    except Exception:
                        response_text = "Unable to read response"
                    try:
                        response_status_code = response.status_code
                    except Exception:
                        response_status_code = "Unable to get status code"
                else:
                    response_text = "No response"
                    response_status_code = "No response received"

                error_text = f"""
                Error in api call (attempt {attempt + 1}/{total_attempts})
                request:{payload}
                url:{request_url}
                response:{response_text}
                status_code:{response_status_code}
                exception:{str(e)}
                """
                
                # If we have retries left, wait and retry
                if attempt < max_retries:
                    logging.warning(f"Request failed, retrying in {current_delay:.1f}s... {error_text.strip()}")
                    time.sleep(current_delay)
                    
                    # Apply exponential backoff with a cap
                    if exponential_backoff:
                        current_delay = min(current_delay * 2, 60.0)  # Cap at 60 seconds
                    
                    # Refresh token before retry
                    self.refresh_token()
                else:
                    # No more retries left
                    logging.error(error_text)
                    if raise_exception:
                        raise Exception(error_text)
                    return default_return_value
        
        # This should never be reached, but just in case
        return default_return_value

    @log_errors(default_return=None, raise_exception=True, log_error=True)
    async def async_send_request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        timeout: int = 120,
        raise_exception: bool = True,
        base_url: Optional[str] = None,
        max_retries: int = 0,
        retry_delay: float = 1.0,
        exponential_backoff: bool = True,
        default_return_value: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send an async HTTP request to the specified endpoint with retry support.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: API endpoint path
            headers: Optional request headers
            payload: Optional JSON payload
            files: Optional files to upload
            data: Optional raw data
            timeout: Request timeout in seconds (default: 60)
            raise_exception: Whether to raise exceptions on error (default: True)
            base_url: Optional custom base URL
            max_retries: Maximum number of retry attempts on failure (default: 0)
            retry_delay: Initial delay between retries in seconds (default: 1.0)
            exponential_backoff: Whether to use exponential backoff for retries (default: True)
            default_return_value: Value to return on failure when raise_exception=False
            
        Returns:
            Response data dict
        """
        import aiohttp
        import asyncio
        
        if default_return_value is None:
            default_return_value = {"success": False, "data": None, "error": None}
        
        self.refresh_token()
        request_base_url = base_url or self.BASE_URL
        request_url = f"{request_base_url}{path}"
        request_url = self.add_project_id(request_url)

        if headers is None:
            headers = {}
        if payload is None:
            payload = {}

        headers["sdk_version"] = self.sdk_version
        
        # Set up authorization header
        self.AUTH_TOKEN.set_bearer_token()
        headers["Authorization"] = self.AUTH_TOKEN.bearer_token
        
        current_delay = retry_delay
        total_attempts = max_retries + 1
        
        # Attempt request with retries
        for attempt in range(total_attempts):
            response = None
            try:
                timeout_config = aiohttp.ClientTimeout(total=timeout)
                async with aiohttp.ClientSession(timeout=timeout_config) as session:
                    kwargs: Dict[str, Any] = {
                        'method': method,
                        'url': request_url,
                        'headers': headers,
                        'allow_redirects': True,
                    }
                    
                    if files:
                        # For file uploads, use data with FormData
                        form_data = aiohttp.FormData()
                        for key, value in files.items():
                            form_data.add_field(key, value)
                        if payload:
                            for key, value in payload.items():
                                form_data.add_field(key, str(value))
                        kwargs['data'] = form_data
                    elif data:
                        kwargs['data'] = data
                    elif payload:
                        kwargs['json'] = payload
                    
                    async with session.request(**kwargs) as response:
                        response.raise_for_status()
                        response_data = await response.json()
                        
                        # Log retry success if this wasn't the first attempt
                        if attempt > 0:
                            logging.info(f"Async request succeeded on attempt {attempt + 1}/{total_attempts}")
                        
                        return response_data
                        
            except Exception as e:
                # Safely extract response information
                if response is not None:
                    try:
                        response_text = await response.text()
                    except Exception:
                        response_text = "Unable to read response"
                    try:
                        response_status_code = response.status
                    except Exception:
                        response_status_code = "Unable to get status code"
                else:
                    response_text = "No response"
                    response_status_code = "No response received"

                error_text = f"""
                Error in async api call (attempt {attempt + 1}/{total_attempts})
                request:{payload}
                url:{request_url}
                response:{response_text}
                status_code:{response_status_code}
                exception:{str(e)}
                """
                
                # If we have retries left, wait and retry
                if attempt < max_retries:
                    logging.warning(f"Async request failed, retrying in {current_delay:.1f}s... {error_text.strip()}")
                    await asyncio.sleep(current_delay)
                    
                    # Apply exponential backoff with a cap
                    if exponential_backoff:
                        current_delay = min(current_delay * 2, 60.0)  # Cap at 60 seconds
                    
                    # Refresh token before retry
                    self.refresh_token()
                else:
                    # No more retries left
                    logging.error(error_text)
                    if raise_exception:
                        raise Exception(error_text)
                    return default_return_value
        
        return default_return_value

    async def get_async(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 120,
        raise_exception: bool = True,
        base_url: Optional[str] = None,
        max_retries: int = 0,
        retry_delay: float = 1.0,
        exponential_backoff: bool = True,
        default_return_value: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send an async GET request to the specified endpoint."""
        return await self.async_send_request(
            "GET",
            path,
            payload=params or {},
            timeout=timeout,
            raise_exception=raise_exception,
            base_url=base_url,
            max_retries=max_retries,
            retry_delay=retry_delay,
            exponential_backoff=exponential_backoff,
            default_return_value=default_return_value,
        )

    async def post_async(
        self,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        files: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        timeout: int = 120,
        raise_exception: bool = True,
        base_url: Optional[str] = None,
        max_retries: int = 0,
        retry_delay: float = 1.0,
        exponential_backoff: bool = True,
        default_return_value: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send an async POST request to the specified endpoint."""
        return await self.async_send_request(
            "POST",
            path,
            headers=headers or {},
            payload=payload or {},
            files=files,
            data=data,
            timeout=timeout,
            raise_exception=raise_exception,
            base_url=base_url,
            max_retries=max_retries,
            retry_delay=retry_delay,
            exponential_backoff=exponential_backoff,
            default_return_value=default_return_value,
        )

    async def put_async(
        self,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 120,
        raise_exception: bool = True,
        base_url: Optional[str] = None,
        max_retries: int = 0,
        retry_delay: float = 1.0,
        exponential_backoff: bool = True,
        default_return_value: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send an async PUT request to the specified endpoint."""
        return await self.async_send_request(
            "PUT",
            path,
            headers=headers or {},
            payload=payload or {},
            timeout=timeout,
            raise_exception=raise_exception,
            base_url=base_url,
            max_retries=max_retries,
            retry_delay=retry_delay,
            exponential_backoff=exponential_backoff,
            default_return_value=default_return_value,
        )

    async def delete_async(
        self,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 120,
        raise_exception: bool = True,
        base_url: Optional[str] = None,
        max_retries: int = 0,
        retry_delay: float = 1.0,
        exponential_backoff: bool = True,
        default_return_value: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send an async DELETE request to the specified endpoint."""
        return await self.async_send_request(
            "DELETE",
            path,
            headers=headers or {},
            payload=payload or {},
            timeout=timeout,
            raise_exception=raise_exception,
            base_url=base_url,
            max_retries=max_retries,
            retry_delay=retry_delay,
            exponential_backoff=exponential_backoff,
            default_return_value=default_return_value,
        )

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 120,
        raise_exception: bool = True,
        base_url: Optional[str] = None,
        max_retries: int = 0,
        retry_delay: float = 1.0,
        exponential_backoff: bool = True,
        default_return_value: Optional[Dict[str, Any]] = None,
        background: bool = False,
        on_complete: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Send a GET request to the specified endpoint."""
        return self.send_request(
            "GET",
            path,
            payload=params or {},
            timeout=timeout,
            raise_exception=raise_exception,
            base_url=base_url,
            max_retries=max_retries,
            retry_delay=retry_delay,
            exponential_backoff=exponential_backoff,
            default_return_value=default_return_value,
            background=background,
            on_complete=on_complete,
        )

    def post(
        self,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        files: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        timeout: int = 120,
        raise_exception: bool = True,
        base_url: Optional[str] = None,
        max_retries: int = 0,
        retry_delay: float = 1.0,
        exponential_backoff: bool = True,
        default_return_value: Optional[Dict[str, Any]] = None,
        background: bool = False,
        on_complete: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Send a POST request to the specified endpoint."""
        return self.send_request(
            "POST",
            path,
            headers=headers or {},
            payload=payload or {},
            files=files,
            data=data,
            timeout=timeout,
            raise_exception=raise_exception,
            base_url=base_url,
            max_retries=max_retries,
            retry_delay=retry_delay,
            exponential_backoff=exponential_backoff,
            default_return_value=default_return_value,
            background=background,
            on_complete=on_complete,
        )

    def put(
        self,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 120,
        raise_exception: bool = True,
        base_url: Optional[str] = None,
        max_retries: int = 0,
        retry_delay: float = 1.0,
        exponential_backoff: bool = True,
        default_return_value: Optional[Dict[str, Any]] = None,
        background: bool = False,
        on_complete: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Send a PUT request to the specified endpoint."""
        return self.send_request(
            "PUT",
            path,
            headers=headers or {},
            payload=payload or {},
            timeout=timeout,
            raise_exception=raise_exception,
            base_url=base_url,
            max_retries=max_retries,
            retry_delay=retry_delay,
            exponential_backoff=exponential_backoff,
            default_return_value=default_return_value,
            background=background,
            on_complete=on_complete,
        )

    def delete(
        self,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 120,
        raise_exception: bool = True,
        base_url: Optional[str] = None,
        max_retries: int = 0,
        retry_delay: float = 1.0,
        exponential_backoff: bool = True,
        default_return_value: Optional[Dict[str, Any]] = None,
        background: bool = False,
        on_complete: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Send a DELETE request to the specified endpoint."""
        return self.send_request(
            "DELETE",
            path,
            headers=headers or {},
            payload=payload or {},
            timeout=timeout,
            raise_exception=raise_exception,
            base_url=base_url,
            max_retries=max_retries,
            retry_delay=retry_delay,
            exponential_backoff=exponential_backoff,
            default_return_value=default_return_value,
            background=background,
            on_complete=on_complete,
        )

    def wait_for_background_requests(self, timeout: Optional[float] = None) -> int:
        """Wait for all background requests to complete.
        
        Args:
            timeout: Optional timeout in seconds to wait for all requests to complete.
                    If None, waits indefinitely.
        
        Returns:
            Number of requests that completed successfully
        """
        completed_count = 0
        failed_count = 0
        
        with self._futures_lock:
            futures_to_wait = list(self._background_futures)
        
        for future in futures_to_wait:
            if not future.done():
                try:
                    future.result(timeout=timeout)
                    completed_count += 1
                except Exception as e:
                    failed_count += 1
                    logging.error(f"Background request failed: {e}")
            else:
                # Already done - check if it succeeded
                try:
                    future.result()
                    completed_count += 1
                except Exception:
                    failed_count += 1
        
        # Clear completed futures
        with self._futures_lock:
            self._background_futures = [f for f in self._background_futures if not f.done()]
        
        logging.debug(f"Background requests: {completed_count} completed, {failed_count} failed, {len(self._background_futures)} remaining")
        return completed_count

    def get_background_request_count(self) -> Tuple[int, int]:
        """Get the count of pending and completed background requests.
        
        Returns:
            Tuple of (pending_count, completed_count)
        """
        with self._futures_lock:
            pending = sum(1 for f in self._background_futures if not f.done())
            completed = sum(1 for f in self._background_futures if f.done())
        return (pending, completed)

    def clear_completed_background_requests(self) -> int:
        """Clear completed background requests from the queue.
        
        Returns:
            Number of completed requests that were cleared
        """
        with self._futures_lock:
            initial_count = len(self._background_futures)
            self._background_futures = [f for f in self._background_futures if not f.done()]
            cleared = initial_count - len(self._background_futures)
        
        logging.debug(f"Cleared {cleared} completed background requests")
        return cleared

    def shutdown(self, wait: bool = True, timeout: Optional[float] = None) -> None:
        """Shutdown the RPC client and cleanup resources.
        
        Args:
            wait: Whether to wait for all background requests to complete before shutdown
            timeout: Optional timeout in seconds when waiting for requests (only used if wait=True)
        """
        self._shutdown = True
        
        if wait:
            logging.info("Waiting for background requests to complete before shutdown...")
            self.wait_for_background_requests(timeout=timeout)
        else:
            logging.info("Shutting down without waiting for background requests...")
        
        try:
            self._executor.shutdown(wait=wait, cancel_futures=not wait)
        except TypeError:
            # Python < 3.9 doesn't support cancel_futures
            self._executor.shutdown(wait=wait)
        
        logging.info("RPC client shutdown complete")

    def __enter__(self) -> "RPC":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Context manager exit - ensures cleanup."""
        self.shutdown(wait=True)
        return False

    def __del__(self) -> None:
        """Destructor - attempt cleanup if not already done."""
        if not self._shutdown:
            try:
                self.shutdown(wait=False)
            except Exception:
                pass  # Ignore errors during cleanup in destructor

    def __getstate__(self) -> Dict[str, Any]:
        """Prepare the object state for pickling.
        
        Removes non-picklable objects (ThreadPoolExecutor, threading.Lock, Future objects)
        so that the RPC instance can be safely passed to multiprocessing workers.
        
        Returns:
            Dictionary of picklable state
        """
        state = self.__dict__.copy()
        
        # Remove unpicklable objects before pickling
        state["_executor"] = None
        state["_futures_lock"] = None
        state["_background_futures"] = []
        state["_shutdown"] = False
        
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        """Restore the object state after unpickling.
        
        Recreates non-picklable objects (ThreadPoolExecutor, threading.Lock)
        that were removed during pickling.
        
        Args:
            state: Dictionary of state to restore
        """
        self.__dict__.update(state)
        
        # Recreate thread-based components inside the subprocess
        max_workers = state.get("_max_workers", 5)
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._futures_lock = threading.Lock()
        self._background_futures = []
        self._shutdown = False

    def refresh_token(self) -> None:
        """Refresh the authentication token if expired."""
        try:
            time_difference = datetime.now(timezone.utc) - self.AUTH_TOKEN.expiry_time.replace(tzinfo=timezone.utc)
            time_diff = time_difference - timedelta(0)
            if time_diff.total_seconds() >= 0:
                # Try to refresh existing token first
                self.AUTH_TOKEN.set_bearer_token()

                # If refresh failed (bearer_token is None), create new token objects
                if self.AUTH_TOKEN.bearer_token is None:
                    logging.warning("Token refresh failed, regenerating tokens from credentials")
                    self.Refresh_Token = RefreshToken(self.access_key, self.secret_key)
                    self.AUTH_TOKEN = AuthToken(
                        self.access_key,
                        self.secret_key,
                        self.Refresh_Token,
                    )
                    logging.debug("New authentication tokens created")
                else:
                    logging.debug("Authentication token refreshed successfully")

        except Exception as e:
            logging.error(f"Error refreshing token: {e}", exc_info=True)
            # Create new tokens to recover from error state
            try:
                self.Refresh_Token = RefreshToken(self.access_key, self.secret_key)
                self.AUTH_TOKEN = AuthToken(
                    self.access_key,
                    self.secret_key,
                    self.Refresh_Token,
                )
                logging.info("Created fresh authentication tokens after error")
            except Exception as recovery_error:
                logging.error(f"Failed to recover from token error: {recovery_error}", exc_info=True)
                raise

    def add_project_id(self, url: str) -> str:
        """Add project ID to the URL if present and not already included."""
        if not self.url_projectID or "?projectId" in url or "&projectId" in url:
            return url
        if "?" in url:
            url = url + "&" + self.url_projectID
        else:
            url = url + "?" + self.url_projectID
        return url
