import unittest
from unittest.mock import MagicMock
from src.remediation import RemediationEngine


class TestRemediationEngine(unittest.TestCase):
    def setUp(self):
        self.mock_session = MagicMock()
        self.mock_ec2_client = MagicMock()
        self.mock_session.client.return_value = self.mock_ec2_client

    def test_is_resource_protected_true(self):
        remediator = RemediationEngine(session=self.mock_session, dry_run=True)
        tags = [{"Key": "Protection", "Value": "true"}]
        self.assertTrue(remediator.is_resource_protected(tags))

    def test_is_resource_protected_false(self):
        remediator = RemediationEngine(session=self.mock_session, dry_run=True)
        tags = [{"Key": "Environment", "Value": "Dev"}]
        self.assertFalse(remediator.is_resource_protected(tags))

    def test_stop_ec2_instance_dry_run(self):
        remediator = RemediationEngine(session=self.mock_session, dry_run=True)
        self.mock_ec2_client.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"Tags": []}]}]
        }
        
        result = remediator.stop_ec2_instance("i-0123456789abcdef0")
        
        self.assertTrue(result)
        # Verify stop_instances was NOT called in dry-run mode
        self.mock_ec2_client.stop_instances.assert_not_called()

    def test_stop_ec2_instance_protected(self):
        remediator = RemediationEngine(session=self.mock_session, dry_run=False)
        self.mock_ec2_client.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"Tags": [{"Key": "DoNotDelete", "Value": "true"}]}]}]
        }
        
        result = remediator.stop_ec2_instance("i-0123456789abcdef0")
        
        self.assertFalse(result)
        # Verify stop_instances was blocked due to protection tag
        self.mock_ec2_client.stop_instances.assert_not_called()


if __name__ == "__main__":
    unittest.main()