import pytest
import requests_mock
from unittest.mock import Mock, patch

from instavm import (
    InstaVM, BrowserError, BrowserSessionError, BrowserInteractionError,
    ElementNotFoundError, QuotaExceededError
)
from instavm.sandbox_client import BrowserSession


class TestInstaVMBrowserIntegration:
    """Test the browser integration features of InstaVM SDK"""

    @pytest.fixture
    def client(self):
        """Create InstaVM client without auto-starting session"""
        with patch.object(InstaVM, 'start_session'):
            client = InstaVM(api_key="test_api_key", base_url="https://api.test.com")
            client.session_id = "test_session_id"  # Set manually for code execution
        return client

    def test_create_browser_session(self, client):
        """Test creating a browser session"""
        with requests_mock.Mocker() as m:
            m.post(
                "https://api.test.com/v1/browser/sessions/",
                json={"session_id": "browser_session_123"}
            )
            
            session_id = client.create_browser_session(
                viewport_width=1280,
                viewport_height=720,
                user_agent="test-agent"
            )
            
            assert session_id == "browser_session_123"
            
            # Verify request payload
            request = m.last_request
            assert request.headers["X-API-Key"] == "test_api_key"
            assert request.json()["viewport_width"] == 1280
            assert request.json()["viewport_height"] == 720
            assert request.json()["user_agent"] == "test-agent"

    def test_create_browser_session_quota_exceeded(self, client):
        """Test quota exceeded error when creating browser session"""
        with requests_mock.Mocker() as m:
            m.post(
                "https://api.test.com/v1/browser/sessions/",
                status_code=429,
                json={"detail": "Quota exceeded"}
            )
            
            with pytest.raises(QuotaExceededError):
                client.create_browser_session()

    def test_browser_navigate(self, client):
        """Test browser navigation"""
        with requests_mock.Mocker() as m:
            m.post(
                "https://api.test.com/v1/browser/interactions/navigate",
                json={
                    "success": True,
                    "message": "Navigation completed",
                    "execution_time": 1.5,
                    "session_id": "browser_session_123",
                    "data": {"url": "https://example.com"}
                }
            )
            
            result = client.browser_navigate(
                url="https://example.com",
                session_id="browser_session_123"
            )
            
            assert result["success"] is True
            assert result["data"]["url"] == "https://example.com"
            
            # Verify request
            request = m.last_request
            assert request.json()["url"] == "https://example.com"
            assert request.json()["session_id"] == "browser_session_123"

    def test_browser_click(self, client):
        """Test browser click interaction"""
        with requests_mock.Mocker() as m:
            m.post(
                "https://api.test.com/v1/browser/interactions/click",
                json={
                    "success": True,
                    "message": "Click completed",
                    "execution_time": 0.5,
                    "session_id": "browser_session_123",
                    "data": {"element": "#button"}
                }
            )
            
            result = client.browser_click(
                selector="#button",
                session_id="browser_session_123",
                force=True
            )
            
            assert result["success"] is True
            assert result["data"]["element"] == "#button"
            
            # Verify request
            request = m.last_request
            assert request.json()["selector"] == "#button"
            assert request.json()["force"] is True

    def test_browser_click_element_not_found(self, client):
        """Test element not found error"""
        with requests_mock.Mocker() as m:
            m.post(
                "https://api.test.com/v1/browser/interactions/click",
                status_code=404,
                json={"detail": "Element not found"}
            )
            
            with pytest.raises(ElementNotFoundError):
                client.browser_click(
                    selector="#nonexistent",
                    session_id="browser_session_123"
                )

    def test_browser_type(self, client):
        """Test browser type interaction"""
        with requests_mock.Mocker() as m:
            m.post(
                "https://api.test.com/v1/browser/interactions/type",
                json={
                    "success": True,
                    "message": "Typing completed",
                    "execution_time": 1.2,
                    "session_id": "browser_session_123",
                    "data": {"text": "Hello World"}
                }
            )
            
            result = client.browser_type(
                selector="#input",
                text="Hello World",
                session_id="browser_session_123",
                delay=50
            )
            
            assert result["success"] is True
            assert result["data"]["text"] == "Hello World"

    def test_browser_screenshot(self, client):
        """Test browser screenshot"""
        with requests_mock.Mocker() as m:
            m.post(
                "https://api.test.com/v1/browser/interactions/screenshot",
                json={
                    "screenshot": "base64_encoded_image_data",
                    "format": "png",
                    "execution_time": 2.0,
                    "session_id": "browser_session_123"
                }
            )
            
            screenshot = client.browser_screenshot(
                session_id="browser_session_123",
                full_page=True,
                format="png"
            )
            
            assert screenshot == "base64_encoded_image_data"

    def test_browser_extract_elements(self, client):
        """Test DOM element extraction"""
        with requests_mock.Mocker() as m:
            m.post(
                "https://api.test.com/v1/browser/interactions/extract",
                json={
                    "elements": [
                        {"tag": "div", "id": "content", "text": "Hello"},
                        {"tag": "button", "id": "submit", "text": "Submit"}
                    ],
                    "count": 2,
                    "execution_time": 0.8,
                    "session_id": "browser_session_123"
                }
            )
            
            elements = client.browser_extract_elements(
                session_id="browser_session_123",
                selector="div, button"
            )
            
            assert len(elements) == 2
            assert elements[0]["id"] == "content"
            assert elements[1]["id"] == "submit"

    def test_close_browser_session(self, client):
        """Test closing a browser session"""
        with requests_mock.Mocker() as m:
            m.delete(
                "https://api.test.com/v1/browser/sessions/browser_session_123",
                status_code=200
            )
            
            result = client.close_browser_session("browser_session_123")
            
            assert result is True

    def test_list_browser_sessions(self, client):
        """Test listing browser sessions"""
        with requests_mock.Mocker() as m:
            m.get(
                "https://api.test.com/v1/browser/sessions/",
                json={
                    "sessions": [
                        {
                            "session_id": "session_1",
                            "status": "active",
                            "viewport_width": 1920,
                            "viewport_height": 1080
                        }
                    ],
                    "total_count": 1
                }
            )
            
            sessions = client.list_browser_sessions()
            
            assert len(sessions) == 1
            assert sessions[0]["session_id"] == "session_1"


class TestBrowserManager:
    """Test the BrowserManager class"""

    @pytest.fixture
    def client(self):
        """Create InstaVM client without auto-starting session"""
        with patch.object(InstaVM, 'start_session'):
            client = InstaVM(api_key="test_api_key", base_url="https://api.test.com")
            client.session_id = "test_session_id"
        return client

    def test_browser_manager_navigate_auto_session(self, client):
        """Test browser manager auto-creates session for navigation"""
        with requests_mock.Mocker() as m:
            # Mock session creation
            m.post(
                "https://api.test.com/v1/browser/sessions/",
                json={"session_id": "auto_session_123"}
            )
            # Mock navigation
            m.post(
                "https://api.test.com/v1/browser/interactions/navigate",
                json={"success": True, "url": "https://example.com"}
            )
            
            result = client.browser.navigate("https://example.com")
            
            assert result["success"] is True
            assert result["url"] == "https://example.com"
            
            # Verify session was created
            session_request = m.request_history[0]
            assert session_request.method == "POST"
            assert "/sessions/" in session_request.url

    def test_browser_manager_click(self, client):
        """Test browser manager click functionality"""
        with requests_mock.Mocker() as m:
            # Mock session creation
            m.post(
                "https://api.test.com/v1/browser/sessions/",
                json={"session_id": "auto_session_123"}
            )
            # Mock click
            m.post(
                "https://api.test.com/v1/browser/interactions/click",
                json={"success": True, "element": "#button"}
            )
            
            result = client.browser.click("#button", force=True)
            
            assert result["success"] is True
            assert result["element"] == "#button"

    def test_browser_manager_screenshot(self, client):
        """Test browser manager screenshot functionality"""
        with requests_mock.Mocker() as m:
            # Mock session creation
            m.post(
                "https://api.test.com/v1/browser/sessions/",
                json={"session_id": "auto_session_123"}
            )
            # Mock screenshot
            m.post(
                "https://api.test.com/v1/browser/interactions/screenshot",
                json={
                    "screenshot": "base64data",
                    "format": "png",
                    "execution_time": 1.0,
                    "session_id": "auto_session_123"
                }
            )
            
            screenshot = client.browser.screenshot(full_page=True)
            
            assert screenshot == "base64data"


class TestBrowserSession:
    """Test the BrowserSession wrapper class"""

    @pytest.fixture
    def client(self):
        """Create InstaVM client without auto-starting session"""
        with patch.object(InstaVM, 'start_session'):
            client = InstaVM(api_key="test_api_key", base_url="https://api.test.com")
            client.session_id = "test_session_id"
        return client

    def test_browser_session_context_manager(self, client):
        """Test browser session as context manager"""
        with requests_mock.Mocker() as m:
            # Mock session creation
            m.post(
                "https://api.test.com/v1/browser/sessions/",
                json={"session_id": "ctx_session_123"}
            )
            # Mock navigation
            m.post(
                "https://api.test.com/v1/browser/interactions/navigate",
                json={"success": True, "url": "https://example.com"}
            )
            # Mock session close
            m.delete(
                "https://api.test.com/v1/browser/sessions/ctx_session_123",
                status_code=200
            )
            
            browser_session = client.browser.create_session(viewport_width=1280)
            
            with browser_session:
                result = browser_session.navigate("https://example.com")
                assert result["success"] is True
            
            # Verify close was called
            close_request = m.request_history[-1]
            assert close_request.method == "DELETE"
            assert "ctx_session_123" in close_request.url

    def test_browser_session_methods(self, client):
        """Test browser session method delegation"""
        session = BrowserSession("test_session", client)
        
        with patch.object(client, 'browser_navigate') as mock_nav:
            mock_nav.return_value = {"success": True}
            
            result = session.navigate("https://example.com", wait_timeout=5000)
            
            mock_nav.assert_called_once_with(
                "https://example.com", "test_session", 5000
            )
            assert result["success"] is True

    def test_mixed_usage_workflow(self, client):
        """Test mixed code execution and browser automation workflow"""
        with requests_mock.Mocker() as m:
            # Mock code execution
            m.post(
                "https://api.test.com/execute",
                json={"output": "Hello from Python!", "success": True}
            )
            # Mock browser session creation
            m.post(
                "https://api.test.com/v1/browser/sessions/",
                json={"session_id": "mixed_session_123"}
            )
            # Mock browser navigation
            m.post(
                "https://api.test.com/v1/browser/interactions/navigate",
                json={"success": True, "url": "https://api.example.com"}
            )
            # Mock element extraction
            m.post(
                "https://api.test.com/v1/browser/interactions/extract",
                json={
                    "elements": [{"tag": "div", "text": "API Data"}],
                    "count": 1
                }
            )
            
            # Execute code
            result = client.execute("print('Hello from Python!')")
            assert result["success"] is True
            
            # Use browser to navigate and extract data
            client.browser.navigate("https://api.example.com")
            elements = client.browser.extract_elements("div")
            
            assert len(elements) == 1
            assert elements[0]["text"] == "API Data"
            
            # Execute more code with extracted data
            with patch.object(client, 'execute') as mock_exec:
                mock_exec.return_value = {"output": "Processed data", "success": True}
                
                client.execute(f"process_data({elements})")
                mock_exec.assert_called_once_with(f"process_data({elements})")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])