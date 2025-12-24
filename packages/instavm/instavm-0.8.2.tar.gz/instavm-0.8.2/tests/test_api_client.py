import unittest
from unittest.mock import patch, MagicMock
from instavm import InstaVM

LIVE_API_KEY = ""

class TestInstaVMClient(unittest.TestCase):
    @unittest.skipIf(not LIVE_API_KEY, "No live API key set in LIVE_API_KEY")
    def test_live_api_execute(self):
        client = InstaVM(api_key=LIVE_API_KEY, base_url="https://api.instavm.io")
        # 2. Execute a simple command
        exec_result = client.execute("print('Hello from live test')")
        print(exec_result)
        self.assertTrue(isinstance(exec_result, dict))
        print("Execution result:", exec_result)

        # 3. Get usage info for this session
        usage_info = client.get_usage()
        self.assertTrue(isinstance(usage_info, dict))
        print("Usage info:", usage_info)




    @patch('instavm.sandbox_client.InstaVM._make_request')
    def setUp(self, mock_make_request):
        # Mock _make_request for session initialization
        mock_response = MagicMock()
        mock_response.json.return_value = {"session_id": "init_session_id"}
        mock_make_request.return_value = mock_response

        self.client = InstaVM(api_key="test_api_key", base_url="http://api.instavm.io")
        self.mock_session_id = "test_session_id"


    @patch('instavm.sandbox_client.InstaVM._make_request')
    def test_start_session(self, mock_make_request):

        mock_response = MagicMock()
        mock_response.json.return_value = {"session_id": self.mock_session_id}
        mock_make_request.return_value = mock_response

        session_id = self.client.start_session()
        self.assertEqual(session_id, self.mock_session_id)
        mock_make_request.assert_called_with(
            "POST",
            f"{self.client.base_url}/v1/sessions/session",
            json={"api_key": self.client.api_key}
        )


    @patch('instavm.sandbox_client.InstaVM._make_request')
    def test_execute(self, mock_make_request):

        self.client.session_id = self.mock_session_id
        command = "test_command"

        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "success"}
        mock_make_request.return_value = mock_response

        response = self.client.execute(command)
        self.assertEqual(response, {"result": "success"})
        mock_make_request.assert_called_once_with(
            "POST",
            f"{self.client.base_url}/execute",
            headers={"X-API-Key": self.client.api_key},
            json={
                "command": command,
                "session_id": self.client.session_id
            }
        )

    @patch('instavm.sandbox_client.InstaVM._make_request')
    def test_execute_async(self, mock_make_request):
        self.client.session_id = self.mock_session_id
        command = "test_async_command"

        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "async_success"}
        mock_make_request.return_value = mock_response

        response = self.client.execute_async(command, language="python", timeout=60)
        self.assertEqual(response, {"result": "async_success"})
        mock_make_request.assert_called_once_with(
            "POST",
            f"{self.client.base_url}/execute_async",
            headers={"X-API-Key": self.client.api_key},
            json={
                "command": command,
                "session_id": self.client.session_id,
                "language": "python",
                "timeout": 60
            }
        )


    @patch('instavm.sandbox_client.InstaVM._make_request')
    def test_get_usage(self, mock_make_request):

        self.client.session_id = self.mock_session_id

        mock_response = MagicMock()
        mock_response.json.return_value = {"usage": "test_usage"}
        mock_make_request.return_value = mock_response

        usage = self.client.get_usage()
        self.assertEqual(usage, {"usage": "test_usage"})
        mock_make_request.assert_called_once_with(
            "GET",
            f"{self.client.base_url}/v1/sessions/usage/{self.client.session_id}"
        )


    @patch('instavm.sandbox_client.InstaVM._make_request')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="data")
    def test_upload_file(self, mock_open, mock_make_request):
        self.client.session_id = self.mock_session_id
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "file_uploaded"}
        mock_make_request.return_value = mock_response

        response = self.client.upload_file('test.txt', '/remote/test.txt')
        self.assertEqual(response, {"status": "file_uploaded"})
        mock_make_request.assert_called_once()

if __name__ == '__main__':
    unittest.main()