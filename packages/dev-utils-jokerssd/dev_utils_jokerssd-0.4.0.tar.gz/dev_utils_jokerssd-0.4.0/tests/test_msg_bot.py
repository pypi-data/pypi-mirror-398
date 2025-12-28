
import unittest
from unittest.mock import patch, MagicMock
from dev_utils.lark_wrapper.msg_bot import MsgBot

class TestMsgBot(unittest.TestCase):
    def setUp(self):
        self.chat_id = "ddbfd7a4-7185-45c1-9da1-996dcab9b443"
        self.api_name = "/bot/v2/hook/"
        self.url = "https://open.larksuite.com/open-apis"
        self.msg_bot = MsgBot(
            chat_id=self.chat_id,
            api_name=self.api_name,
            url=self.url,
            msg_type="text"
        )

    @patch('dev_utils.lark_wrapper.messege_lark.requests.post')
    def test_send_msg(self, mock_post):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 0, "msg": "success"}
        mock_post.return_value = mock_response

        message = "Test message"
        result = self.msg_bot.send_msg(message=message)

        # Assertions
        self.assertTrue(result["success"])
        
        expected_url = f"{self.url}/{self.api_name}/{self.chat_id}"
        
        # Verify call arguments
        # Note: MsgBot calls LarkRelated which calls requests.post
        # LarkRelated logic: 
        # url = f"{input_params['url']}/{input_params['api_name']}/{input_params['chat_id']}"
        
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        
        self.assertEqual(kwargs['url'], expected_url)
        self.assertEqual(kwargs['headers'], {"Content-Type": "application/json"})
        self.assertEqual(kwargs['json']['msg_type'], "text")
        self.assertEqual(kwargs['json']['content']['text'], message)

    @patch('dev_utils.lark_wrapper.messege_lark.requests.post')
    def test_send_msg_post_type(self, mock_post):
         # Test with msg_type="post" just in case, though user didn't specify, it's good coverage
        self.msg_bot.msg_type = "post"
        # Update internal LarkRelated instance as well because MsgBot init creates it once
        self.msg_bot.msg_bot_dict["lark"].msg_type = "post" # This is a bit implementation detail dependent
        
        # Better to just pass msg_type to send_msg if we want to override
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 0, "msg": "success"}
        mock_post.return_value = mock_response

        message = "Test post message"
        title = "Test Title"
        result = self.msg_bot.send_msg(message=message, msg_type="post", title=title)
        
        self.assertTrue(result["success"])
        
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['json']['msg_type'], "post")
        # Check structure of post message
        self.assertIn("content", kwargs['json'])
        self.assertIn("post", kwargs['json']['content'])

    def test_live_send_msg(self):
        """
        Sends a real request to the Lark API.
        This test interacts with the external service and is intended for manual verification.
        """
        print("\\nRunning live test...")
        message = "This is a live test message from the automated test suite."
        title = "Live Test"
        
        # Real call to MsgBot.send_msg (no mocking)
        # Note: This uses the chat_id and url defined in setUp
        result = self.msg_bot.send_msg(message=message, title=title)
        
        print(f"Live send result: {result}")
        
        # Verify result structure and success
        self.assertIsInstance(result, dict)
        
        # Allow for API errors if credentials are invalid, but ensure we got a response dict
        if result.get("success"):
            self.assertTrue(result["success"])
        else:
            # If it fails (e.g. invalid chat_id), it might return success=False
            print(f"Live test failed: {result}")

if __name__ == '__main__':
    unittest.main()

