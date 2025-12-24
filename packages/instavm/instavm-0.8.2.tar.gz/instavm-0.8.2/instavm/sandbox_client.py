import requests
import time
import json
import base64
from typing import Optional, Dict, Any, Generator, Callable, List
from .exceptions import (
    InstaVMError, AuthenticationError, SessionError, ExecutionError,
    NetworkError, RateLimitError, BrowserError, BrowserSessionError,
    BrowserInteractionError, BrowserTimeoutError, BrowserNavigationError,
    ElementNotFoundError, QuotaExceededError, UnsupportedOperationError
)
class BrowserSession:
    """Represents a browser session for automation"""

    def __init__(self, session_id: str, client: 'InstaVM'):
        self.session_id = session_id
        self.client = client
        self._active = True

    def navigate(self, url: str, wait_timeout: int = 30000) -> Dict[str, Any]:
        """Navigate to a URL"""
        return self.client.browser_navigate(url, self.session_id, wait_timeout)

    def click(self, selector: str, force: bool = False, timeout: int = 30000) -> Dict[str, Any]:
        """Click an element"""
        return self.client.browser_click(selector, self.session_id, force, timeout)

    def type(self, selector: str, text: str, delay: int = 100, timeout: int = 30000) -> Dict[str, Any]:
        """Type text into an element"""
        return self.client.browser_type(selector, text, self.session_id, delay, timeout)

    def fill(self, selector: str, value: str, timeout: int = 30000) -> Dict[str, Any]:
        """Fill a form field"""
        return self.client.browser_fill(selector, value, self.session_id, timeout)

    def scroll(self, selector: str = None, x: int = None, y: int = None) -> Dict[str, Any]:
        """Scroll the page or an element. If a selector is provided, scrolls the element into view. If x and y coordinates are provided, scrolls the page to those absolute coordinates."""
        return self.client.browser_scroll(self.session_id, selector, x, y)

    def wait_for(self, condition: str, selector: str = None, timeout: int = 30000) -> Dict[str, Any]:
        """Wait for a condition"""
        return self.client.browser_wait(condition, self.session_id, selector, timeout)

    def screenshot(self, full_page: bool = True, clip: Dict = None, format: str = "png", quality: int = None) -> str:
        """Take a screenshot (returns base64 string)"""
        return self.client.browser_screenshot(self.session_id, full_page, clip, format, quality)

    def extract_elements(self, selector: str = None, attributes: List[str] = None) -> List[Dict[str, Any]]:
        """Extract DOM elements"""
        return self.client.browser_extract_elements(self.session_id, selector, attributes)

    def extract_content(self, url: str = None, include_interactive: bool = True,
                       include_anchors: bool = True, max_anchors: int = 50) -> Dict[str, Any]:
        """Extract LLM-friendly content with clean text, interactive elements, and anchors"""
        return self.client.browser_extract_content(self.session_id, url, include_interactive,
                                                   include_anchors, max_anchors)

    def close(self) -> bool:
        """Close this browser session"""
        if self._active:
            result = self.client.close_browser_session(self.session_id)
            self._active = False
            return result
        return True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class BrowserManager:
    """Manager for browser automation functionality"""

    def __init__(self, client: 'InstaVM'):
        self.client = client
        self._default_session_id = None

    def create_session(self, viewport_width: int = 1920, viewport_height: int = 1080,
                      user_agent: str = None) -> BrowserSession:
        """Create a new browser session"""
        session_id = self.client.create_browser_session(viewport_width, viewport_height, user_agent)
        return BrowserSession(session_id, self.client)

    def _ensure_default_session(self) -> str:
        """Ensure a default browser session exists"""
        if not self._default_session_id:
            session = self.create_session()
            self._default_session_id = session.session_id
        return self._default_session_id

    def navigate(self, url: str, session_id: str = None, wait_timeout: int = 30000) -> Dict[str, Any]:
        """Navigate to URL (auto-creates session if none provided)"""
        if not session_id:
            session_id = self._ensure_default_session()
        return self.client.browser_navigate(url, session_id, wait_timeout)

    def click(self, selector: str, session_id: str = None, force: bool = False, timeout: int = 30000) -> Dict[str, Any]:
        """Click element by CSS selector"""
        if not session_id:
            session_id = self._ensure_default_session()
        return self.client.browser_click(selector, session_id, force, timeout)

    def type(self, selector: str, text: str, session_id: str = None, delay: int = 100, timeout: int = 30000) -> Dict[str, Any]:
        """Type text into element"""
        if not session_id:
            session_id = self._ensure_default_session()
        return self.client.browser_type(selector, text, session_id, delay, timeout)

    def fill(self, selector: str, value: str, session_id: str = None, timeout: int = 30000) -> Dict[str, Any]:
        """Fill form field"""
        if not session_id:
            session_id = self._ensure_default_session()
        return self.client.browser_fill(selector, value, session_id, timeout)

    def wait_for(self, condition: str, selector: str = None, session_id: str = None, timeout: int = 30000) -> Dict[str, Any]:
        """Wait for condition"""
        if not session_id:
            session_id = self._ensure_default_session()
        return self.client.browser_wait(condition, session_id, selector, timeout)

    def screenshot(self, session_id: str = None, full_page: bool = True, clip: Dict = None,
                  format: str = "png", quality: int = None) -> str:
        """Take screenshot (returns base64)"""
        if not session_id:
            session_id = self._ensure_default_session()
        return self.client.browser_screenshot(session_id, full_page, clip, format, quality)

    def extract_elements(self, selector: str = None, session_id: str = None, attributes: List[str] = None) -> List[Dict]:
        """Extract DOM elements"""
        if not session_id:
            session_id = self._ensure_default_session()
        return self.client.browser_extract_elements(session_id, selector, attributes)

    def extract_content(self, session_id: str = None, url: str = None,
                       include_interactive: bool = True, include_anchors: bool = True,
                       max_anchors: int = 50) -> Dict[str, Any]:
        """Extract LLM-friendly content (auto-creates session if none provided in cloud mode)"""
        if not self.client.local and not session_id:
            session_id = self._ensure_default_session()
        return self.client.browser_extract_content(session_id, url, include_interactive,
                                                   include_anchors, max_anchors)

    def close(self):
        """Closes the default browser session, if one was created."""
        if self._default_session_id:
            self.client.close_browser_session(self._default_session_id)
            self._default_session_id = None


class InstaVM:
    def __init__(self, api_key=None, base_url="https://api.instavm.io", timeout=300, max_retries=0,
                 local=False, local_url="http://coderunner.local:8222"):
        """
        Initialize InstaVM client

        Args:
            api_key: API key for cloud mode (not required for local mode)
            base_url: Base URL for cloud API (ignored if local=True)
            timeout: VM lifetime in seconds (used when creating session). Also used as default HTTP request timeout. Range: 20-86400 seconds. Default: 300
            max_retries: Maximum number of retries for failed requests
            local: Use local container instead of cloud API
            local_url: Local container URL (default: http://coderunner.local:8222)
        """
        self.local = local
        self.base_url = local_url if local else base_url
        self.api_key = api_key
        self.session_id = None  # Code execution session
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()

        # Browser automation manager
        self.browser = BrowserManager(self)

        # Only start cloud session if not in local mode
        if not self.local and self.api_key:
            self.start_session()

    def _ensure_not_local(self, operation_name: str):
        """Raise UnsupportedOperationError if in local mode"""
        if self.local:
            raise UnsupportedOperationError(
                f"{operation_name} is not supported in local mode. "
                f"This operation is only available when using the cloud API."
            )

    def _make_request(self, method: str, url: str, timeout: Optional[int] = None, **kwargs) -> requests.Response:
        """Make HTTP request with retry logic and proper error handling"""
        last_exception = None
        request_timeout = timeout if timeout is not None else self.timeout

        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(
                    method, url, timeout=request_timeout, **kwargs
                )

                # Handle specific HTTP status codes
                if response.status_code == 401:
                    raise AuthenticationError("Invalid API key or session expired")
                elif response.status_code == 429:
                    detail = response.json().get('detail', 'Rate limit exceeded')
                    raise RateLimitError(detail)
                elif response.status_code >= 500:
                    # More details for debugging
                    status_reason = response.reason or ""
                    try:
                        error_text = response.text.strip()
                    except Exception:
                        error_text = "<No response body>"

                    if response.status_code == 504:
                        raise NetworkError(
                            f"504 Gateway Timeout: The server (or a proxy) didn't get a timely response from the upstream service.\n"
                            f"Reason: {status_reason}\n"
                            f"Details: {error_text}"
                        )
                    else:
                        raise NetworkError(
                            f"Server error: {response.status_code} {status_reason}\n"
                            f"Details: {error_text}"
                        )


                response.raise_for_status()
                return response

            except requests.exceptions.Timeout as e:
                last_exception = NetworkError(f"Request timeout after {request_timeout}s")
            except requests.exceptions.ConnectionError as e:
                last_exception = NetworkError(f"Connection failed: {str(e)}")
            except (AuthenticationError, RateLimitError) as e:
                # Don't retry these
                raise e
            except requests.exceptions.HTTPError as e:
                if e.response.status_code < 500:
                    # Re-raise the original exception to allow for specific handling by the caller
                    raise
                last_exception = NetworkError(f"HTTP error: {str(e)}")

            if attempt < self.max_retries:
                # Exponential backoff
                time.sleep(2 ** attempt)

        raise last_exception or NetworkError("Max retries exceeded")

    def _ensure_api_key(self):
        """Raise AuthenticationError if API key is not set."""
        if not self.api_key:
            raise AuthenticationError("API key not set")

    def start_session(self):
        self._ensure_not_local("Session management")

        if not self.api_key:
            raise AuthenticationError("API key not set. Please provide an API key or create one first.")

        url = f"{self.base_url}/v1/sessions/session"
        data = {
            "api_key": self.api_key,
            "vm_lifetime_seconds": self.timeout
        }

        try:
            response = self._make_request("POST", url, json=data)
            result = response.json()
            self.session_id = result.get("session_id")
            if not self.session_id:
                raise SessionError("Failed to get session ID from server response")
            return self.session_id
        except Exception as e:
            if isinstance(e, (InstaVMError)):
                raise e
            raise SessionError(f"Failed to start session: {str(e)}")

    def execute(self, command: str, language: Optional[str] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute a command in the VM

        Args:
            command: Command to execute
            language: Programming language (optional)
            timeout: Request timeout in seconds (used both for HTTP request timeout and sent to API)

        Returns:
            Dict containing execution results
        """
        # In local mode, session_id is not required
        if not self.local and not self.session_id:
            raise SessionError("Session ID not set. Please start a session first.")

        url = f"{self.base_url}/execute"
        headers = {"X-API-Key": self.api_key} if self.api_key else {}
        data = {"command": command}

        # Only include session_id in cloud mode
        if not self.local:
            data["session_id"] = self.session_id
        if language:
            data["language"] = language
        if timeout is not None:
            data["timeout"] = timeout

        # Use custom timeout for this request, or fall back to instance default
        request_timeout = timeout if timeout is not None else self.timeout

        try:
            response = self._make_request("POST", url, headers=headers, json=data, timeout=request_timeout)
            return response.json()
        except Exception as e:
            if isinstance(e, InstaVMError):
                raise e
            raise ExecutionError(f"Failed to execute command: {str(e)}")

    def get_usage(self) -> Dict[str, Any]:
        self._ensure_not_local("Usage tracking")

        if not self.session_id:
            raise SessionError("Session ID not set. Please start a session first.")

        url = f"{self.base_url}/v1/sessions/usage/{self.session_id}"

        try:
            response = self._make_request("GET", url)
            return response.json()
        except Exception as e:
            if isinstance(e, InstaVMError):
                raise e
            raise InstaVMError(f"Failed to get usage: {str(e)}")

    def upload_file(self, file_path: str, remote_path: str,
                    recursive: bool = False) -> Dict[str, Any]:
        self._ensure_not_local("File upload")

        if not self.session_id:
            raise SessionError("Session ID not set. Please start a session first.")

        url = f"{self.base_url}/upload"
        headers = {"X-API-Key": self.api_key}
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path, f)}
                data = {
                    "remote_path": remote_path,
                    "session_id": self.session_id,
                    "recursive": str(recursive).lower()  # ensures 'true'/'false'
                }
                response = self._make_request("POST", url, headers=headers, data=data, files=files)
            return response.json()
        except FileNotFoundError:
            raise InstaVMError(f"File not found: {file_path}")
        except Exception as e:
            if isinstance(e, InstaVMError):
                raise
            raise InstaVMError(f"Failed to upload file: {str(e)}")

    def download_file(self, filename: str, local_path: Optional[str] = None) -> Dict[str, Any]:
        """Download a file from the remote VM

        Args:
            filename: Name of the file to download from the remote VM
            local_path: Optional local path to save the file. If not provided, returns file content in response

        Returns:
            Dict containing download status and file information
        """
        self._ensure_not_local("File download")

        if not self.session_id:
            raise SessionError("Session ID not set. Please start a session first.")

        url = f"{self.base_url}/download"
        headers = {"X-API-Key": self.api_key}
        data = {
            "filename": filename,
            "session_id": self.session_id
        }

        try:
            response = self._make_request("POST", url, headers=headers, data=data)

            # Parse JSON response
            response_data = response.json()

            # Extract and decode file content (assuming base64-encoded)
            encoded_content = response_data.get("content", "")
            if encoded_content:
                file_content = base64.b64decode(encoded_content)
            else:
                # Fallback: if no 'content' field, try raw response
                file_content = response.content

            if local_path:
                # Save to local file
                with open(local_path, 'wb') as f:
                    f.write(file_content)
                return {
                    "status": "success",
                    "filename": filename,
                    "local_path": local_path,
                    "size": len(file_content)
                }
            else:
                # Return content in response
                return {
                    "status": "success",
                    "filename": filename,
                    "content": file_content,
                    "size": len(file_content)
                }
        except Exception as e:
            if isinstance(e, InstaVMError):
                raise
            raise InstaVMError(f"Failed to download file: {str(e)}")

    def execute_async(self, command: str, language: Optional[str] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Execute command asynchronously"""
        self._ensure_not_local("Async execution")

        if not self.session_id:
            raise SessionError("Session ID not set. Please start a session first.")

        url = f"{self.base_url}/execute_async"
        headers = {"X-API-Key": self.api_key}
        data = {
            "command": command,
            "session_id": self.session_id,
        }

        if language:
            data["language"] = language
        if timeout is not None:
            data["timeout"] = timeout

        try:
            response = self._make_request("POST", url, headers=headers, json=data)
            return response.json()
        except Exception as e:
            if isinstance(e, InstaVMError):
                raise e
            raise ExecutionError(f"Failed to execute command asynchronously: {str(e)}")

    def execute_streaming(self, command: str, on_output: Optional[Callable[[str], None]] = None) -> Generator[str, None, None]:
        """Execute command with real-time streaming output (deprecated - streaming not supported by current API)"""
        import warnings
        warnings.warn("execute_streaming is deprecated. The API does not support streaming execution. Use execute() or execute_async() instead.", DeprecationWarning, stacklevel=2)

        # Fallback to regular execution
        result = self.execute(command)
        output = result.get('output', str(result))
        if on_output:
            on_output(output)
        yield output

    def close_session(self) -> bool:
        """Close the current session (sessions auto-expire on server side)"""
        if not self.session_id:
            return True

        # Note: API doesn't provide explicit session deletion endpoint
        # Sessions will auto-expire on the server side
        print(f"Info: Session {self.session_id} will auto-expire on server side.")
        self.session_id = None
        return True

    def is_session_active(self) -> bool:
        """Check if current session is still active by attempting to get usage"""
        try:
            self.get_usage()
            return True
        except (SessionError, AuthenticationError):
            return False
        except Exception:
            return False

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically close session"""
        self.close_session()
        # Parameters are standard context manager signature

    # Browser Automation Methods
    def create_browser_session(self, viewport_width: int = 1920, viewport_height: int = 1080,
                              user_agent: str = None) -> str:
        """Create a new browser session"""
        self._ensure_not_local("Browser session management")
        self._ensure_api_key()

        url = f"{self.base_url}/v1/browser/sessions/"
        headers = {"X-API-Key": self.api_key}
        data = {
            "viewport_width": viewport_width,
            "viewport_height": viewport_height
        }
        if user_agent:
            data["user_agent"] = user_agent

        try:
            response = self._make_request("POST", url, headers=headers, json=data)
            result = response.json()
            return result.get("session_id")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise QuotaExceededError("Browser API quota exceeded")
            raise BrowserSessionError(f"Failed to create browser session: {str(e)}")
        except Exception as e:
            raise BrowserSessionError(f"Failed to create browser session: {str(e)}")

    def get_browser_session(self, session_id: str) -> Dict[str, Any]:
        """Get browser session information"""
        self._ensure_not_local("Browser session management")
        self._ensure_api_key()

        url = f"{self.base_url}/v1/browser/sessions/{session_id}"
        headers = {"X-API-Key": self.api_key}

        try:
            response = self._make_request("GET", url, headers=headers)
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise BrowserSessionError("Browser session not found or expired")
            raise BrowserSessionError(f"Failed to get browser session: {str(e)}")
        except Exception as e:
            raise BrowserSessionError(f"Failed to get browser session: {str(e)}")

    def close_browser_session(self, session_id: str) -> bool:
        """Close a browser session"""
        self._ensure_not_local("Browser session management")
        self._ensure_api_key()

        url = f"{self.base_url}/v1/browser/sessions/{session_id}"
        headers = {"X-API-Key": self.api_key}

        try:
            response = self._make_request("DELETE", url, headers=headers)
            return response.status_code == 200
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return True  # Already closed
            raise BrowserSessionError(f"Failed to close browser session: {str(e)}")
        except Exception as e:
            raise BrowserSessionError(f"Failed to close browser session: {str(e)}")

    def list_browser_sessions(self) -> List[Dict[str, Any]]:
        """List active browser sessions"""
        self._ensure_not_local("Browser session management")
        self._ensure_api_key()

        url = f"{self.base_url}/v1/browser/sessions/"
        headers = {"X-API-Key": self.api_key}

        try:
            response = self._make_request("GET", url, headers=headers)
            result = response.json()
            return result.get("sessions", [])
        except Exception as e:
            raise BrowserSessionError(f"Failed to list browser sessions: {str(e)}")

    def browser_navigate(self, url: str, session_id: str = None, wait_timeout: int = 30000) -> Dict[str, Any]:
        """Navigate to a URL in browser session

        Args:
            url: URL to navigate to
            session_id: Browser session ID (not required in local mode)
            wait_timeout: Timeout in milliseconds
        """
        # In cloud mode, require API key and session_id
        if not self.local:
            self._ensure_api_key()
            if not session_id:
                raise ValueError("session_id is required in cloud mode")

        api_url = f"{self.base_url}/v1/browser/interactions/navigate"
        headers = {"X-API-Key": self.api_key} if self.api_key else {}
        data = {"url": url, "wait_timeout": wait_timeout}

        # Only include session_id in cloud mode
        if not self.local and session_id:
            data["session_id"] = session_id

        try:
            response = self._make_request("POST", api_url, headers=headers, json=data)
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise BrowserSessionError("Browser session not found or expired")
            if e.response.status_code == 408:
                raise BrowserTimeoutError("Navigation timeout")
            raise BrowserNavigationError(f"Failed to navigate: {str(e)}")
        except Exception as e:
            raise BrowserNavigationError(f"Failed to navigate: {str(e)}")

    def browser_click(self, selector: str, session_id: str, force: bool = False, timeout: int = 30000) -> Dict[str, Any]:
        """Click an element in browser session"""
        self._ensure_not_local("Browser click interaction")
        self._ensure_api_key()

        url = f"{self.base_url}/v1/browser/interactions/click"
        headers = {"X-API-Key": self.api_key}
        data = {
            "selector": selector,
            "session_id": session_id,
            "force": force,
            "timeout": timeout
        }

        try:
            response = self._make_request("POST", url, headers=headers, json=data)
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ElementNotFoundError(f"Element not found: {selector}")
            if e.response.status_code == 408:
                raise BrowserTimeoutError("Click timeout")
            raise BrowserInteractionError(f"Failed to click element: {str(e)}")
        except Exception as e:
            raise BrowserInteractionError(f"Failed to click element: {str(e)}")

    def browser_type(self, selector: str, text: str, session_id: str, delay: int = 100, timeout: int = 30000) -> Dict[str, Any]:
        """Type text into an element"""
        self._ensure_not_local("Browser type interaction")
        self._ensure_api_key()

        url = f"{self.base_url}/v1/browser/interactions/type"
        headers = {"X-API-Key": self.api_key}
        data = {
            "selector": selector,
            "text": text,
            "session_id": session_id,
            "delay": delay,
            "timeout": timeout
        }

        try:
            response = self._make_request("POST", url, headers=headers, json=data)
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ElementNotFoundError(f"Element not found: {selector}")
            if e.response.status_code == 408:
                raise BrowserTimeoutError("Type timeout")
            raise BrowserInteractionError(f"Failed to type text: {str(e)}")
        except Exception as e:
            raise BrowserInteractionError(f"Failed to type text: {str(e)}")

    def browser_fill(self, selector: str, value: str, session_id: str, timeout: int = 30000) -> Dict[str, Any]:
        """Fill a form field"""
        self._ensure_not_local("Browser fill interaction")
        self._ensure_api_key()

        url = f"{self.base_url}/v1/browser/interactions/fill"
        headers = {"X-API-Key": self.api_key}
        data = {
            "selector": selector,
            "value": value,
            "session_id": session_id,
            "timeout": timeout
        }

        try:
            response = self._make_request("POST", url, headers=headers, json=data)
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ElementNotFoundError(f"Element not found: {selector}")
            if e.response.status_code == 408:
                raise BrowserTimeoutError("Fill timeout")
            raise BrowserInteractionError(f"Failed to fill form: {str(e)}")
        except Exception as e:
            raise BrowserInteractionError(f"Failed to fill form: {str(e)}")

    def browser_scroll(self, session_id: str, selector: str = None, x: int = None, y: int = None) -> Dict[str, Any]:
        """Scroll the page or an element"""
        self._ensure_not_local("Browser scroll interaction")
        self._ensure_api_key()

        if selector is None and x is None and y is None:
            raise ValueError("At least one of 'selector', 'x', or 'y' must be provided for scrolling.")

        url = f"{self.base_url}/v1/browser/interactions/scroll"
        headers = {"X-API-Key": self.api_key}
        data = {"session_id": session_id}
        if selector:
            data["selector"] = selector
        if x is not None:
            data["x"] = x
        if y is not None:
            data["y"] = y

        try:
            response = self._make_request("POST", url, headers=headers, json=data)
            return response.json()
        except Exception as e:
            raise BrowserInteractionError(f"Failed to scroll: {str(e)}")

    def browser_wait(self, condition: str, session_id: str, selector: str = None, timeout: int = 30000) -> Dict[str, Any]:
        """Wait for a condition to be met"""
        self._ensure_not_local("Browser wait interaction")
        self._ensure_api_key()

        url = f"{self.base_url}/v1/browser/interactions/wait"
        headers = {"X-API-Key": self.api_key}
        data = {
            "condition": condition,
            "session_id": session_id,
            "timeout": timeout
        }
        if selector:
            data["selector"] = selector

        try:
            response = self._make_request("POST", url, headers=headers, json=data)
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 408:
                raise BrowserTimeoutError(f"Wait timeout for condition: {condition}")
            raise BrowserInteractionError(f"Failed to wait for condition: {str(e)}")
        except Exception as e:
            raise BrowserInteractionError(f"Failed to wait for condition: {str(e)}")

    def browser_screenshot(self, session_id: str, full_page: bool = True, clip: Dict = None,
                          format: str = "png", quality: int = None) -> str:
        """Take a screenshot (returns base64 string)"""
        self._ensure_not_local("Browser screenshot")
        self._ensure_api_key()

        url = f"{self.base_url}/v1/browser/interactions/screenshot"
        headers = {"X-API-Key": self.api_key}
        data = {
            "session_id": session_id,
            "full_page": full_page,
            "format": format
        }
        if clip:
            data["clip"] = clip
        if quality:
            data["quality"] = quality

        try:
            response = self._make_request("POST", url, headers=headers, json=data)
            result = response.json()
            return result.get("screenshot", "")
        except Exception as e:
            raise BrowserInteractionError(f"Failed to take screenshot: {str(e)}")

    def browser_extract_elements(self, session_id: str, selector: str = None, attributes: List[str] = None) -> List[Dict[str, Any]]:
        """Extract DOM elements"""
        self._ensure_not_local("Browser element extraction")
        self._ensure_api_key()

        url = f"{self.base_url}/v1/browser/interactions/extract"
        headers = {"X-API-Key": self.api_key}
        data = {"session_id": session_id}
        if selector:
            data["selector"] = selector
        if attributes:
            data["attributes"] = attributes

        try:
            response = self._make_request("POST", url, headers=headers, json=data)
            result = response.json()
            return result.get("elements", [])
        except Exception as e:
            raise BrowserInteractionError(f"Failed to extract elements: {str(e)}")

    def browser_extract_content(self, session_id: str = None, url: str = None,
                                include_interactive: bool = True,
                                include_anchors: bool = True, max_anchors: int = 50) -> Dict[str, Any]:
        """
        Extract LLM-friendly content from current page.

        Returns clean article content, interactive elements, and content anchors
        for intelligent browser automation.

        Args:
            session_id: Browser session ID (not required in local mode, required in cloud mode)
            url: URL to extract content from (required in local mode, optional in cloud mode)
            include_interactive: Include interactive elements mapping (default: True)
            include_anchors: Include content-to-selector anchors (default: True)
            max_anchors: Maximum number of content anchors (default: 50)

        Returns:
            Dict with:
            - readable_content: Clean article text (no JS/CSS/ads)
            - interactive_elements: Clickable/typeable elements with selectors
            - content_anchors: Text snippets mapped to DOM selectors

        Example:
            ```python
            # Cloud mode
            content = client.browser_extract_content(session_id="session123")

            # Local mode
            content = client.browser_extract_content(url="https://example.com")

            # LLM reads clean content
            article = content['readable_content']['content']

            # LLM finds "Sign Up" in content
            # LLM searches content_anchors for selector
            for anchor in content['content_anchors']:
                if 'sign up' in anchor['text'].lower():
                    selector = anchor['selector']
                    client.browser_click(selector, session_id)
                    break
            ```
        """
        # In cloud mode, require API key and session_id
        if not self.local:
            self._ensure_api_key()
            if not session_id:
                raise ValueError("session_id is required in cloud mode")
        else:
            # In local mode, require url
            if not url:
                raise ValueError("url is required in local mode")

        api_url = f"{self.base_url}/v1/browser/interactions/content"
        headers = {"X-API-Key": self.api_key} if self.api_key else {}
        data = {
            "include_interactive": include_interactive,
            "include_anchors": include_anchors,
            "max_anchors": max_anchors
        }

        # Include session_id in cloud mode
        if not self.local and session_id:
            data["session_id"] = session_id

        # Include url in local mode
        if self.local and url:
            data["url"] = url

        try:
            response = self._make_request("POST", api_url, headers=headers, json=data)
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise BrowserSessionError("Browser session not found or expired")
            raise BrowserInteractionError(f"Failed to extract content: {str(e)}")
        except json.JSONDecodeError as e:
            raise BrowserInteractionError(f"Failed to parse server response: {str(e)}")