import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

def get_aws_session(profile_name: str = None, region_name: str = "us-east-1"):
    """
    AWS Boto3 Session create karta hai using local profile ya environment variables.
    """
    try:
        if profile_name:
            session = boto3.Session(profile_name=profile_name, region_name=region_name)
        else:
            session = boto3.Session(region_name=region_name)
        return session
    except Exception as e:
        raise RuntimeError(f"Failed to create AWS session: {str(e)}")

def verify_aws_credentials(session: boto3.Session) -> dict:
    """
    AWS STS (Security Token Service) call karke credentials validity verify karta hai.
    """
    try:
        sts_client = session.client('sts')
        identity = sts_client.get_caller_identity()
        return {
            "status": True,
            "account_id": identity.get("Account"),
            "arn": identity.get("Arn"),
            "user_id": identity.get("UserId")
        }
    except (NoCredentialsError, PartialCredentialsError):
        return {
            "status": False,
            "error": "AWS credentials not found or incomplete. Please configure AWS CLI or set environment variables."
        }
    except ClientError as e:
        return {
            "status": False,
            "error": f"AWS Authentication failed: {e.response['Error']['Message']}"
        }
    except Exception as e:
        return {
            "status": False,
            "error": f"An unexpected error occurred during auth check: {str(e)}"
        }