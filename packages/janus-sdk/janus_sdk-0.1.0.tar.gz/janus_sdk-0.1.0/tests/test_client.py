import unittest
from unittest.mock import MagicMock, patch
from janus import JanusClient, Decision, CheckResult

class TestJanusClient(unittest.TestCase):

    def setUp(self):
        self.client = JanusClient(
            tenant_id="test-tenant",
            api_key="test-key",
            base_url="http://mock-api"
        )

    @patch("janus.client.httpx.Client.post")
    def test_check_allowed(self, mock_post):
        # Mock successful ALLOW response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "decision": "ALLOW",
            "reason": "Policy matched",
            "policy_id": "pol_123",
            "latency_ms": 10
        }
        mock_post.return_value = mock_response

        # Execute
        result = self.client.check("payment.process", {"amount": 100})

        # Verify
        self.assertEqual(result.decision, Decision.ALLOW)
        self.assertTrue(result.allowed)
        self.assertEqual(result.policy_id, "pol_123")
        
        # Check call args
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn("/api/sentinel/action/check", args[0])
        self.assertEqual(kwargs["json"]["action"], "payment.process")

    @patch("janus.client.httpx.Client.post")
    def test_check_denied(self, mock_post):
        # Mock DENY response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "decision": "DENY",
            "reason": "Rate limit",
            "policy_id": "pol_rate",
            "latency_ms": 5
        }
        mock_post.return_value = mock_response

        result = self.client.check("email.send", {})

        self.assertEqual(result.decision, Decision.DENY)
        self.assertTrue(result.denied)
        self.assertEqual(result.reason, "Rate limit")

    @patch("janus.client.httpx.Client.post")
    def test_report_success(self, mock_post):
        # Result to report
        check_result = CheckResult(
            decision=Decision.ALLOW,
            reason="ok",
            policy_id="pol_1",
            latency_ms=10,
            request_id="req_123"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        self.client.report(check_result, status="success", result={"id": 1})

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn("/api/sentinel/action/report", args[0])
        self.assertEqual(kwargs["json"]["request_id"], "req_123")
        self.assertEqual(kwargs["json"]["status"], "success")

if __name__ == "__main__":
    unittest.main()
