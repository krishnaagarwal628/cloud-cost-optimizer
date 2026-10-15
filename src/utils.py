import time
import functools
import boto3
from botocore.exceptions import ClientError
from rich import print


def retry_on_throttling(max_retries: int = 3, initial_delay: float = 1.0):
    """
    AWS API Throttling / Rate-Limit errors handle karne ke liye decorator.
    Agar AWS API rate-limit error throw kare, toh yeh exponential backoff delay ke sath retry karega.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "")
                    if error_code in ["Throttling", "RequestLimitExceeded", "ThrottlingException", "TooManyRequestsException"]:
                        if attempt == max_retries:
                            print(f"[bold red]API Rate Limit exceeded after {max_retries} attempts.[/bold red]")
                            raise e
                        print(f"[yellow]Rate limit encountered. Retrying in {delay}s (Attempt {attempt}/{max_retries})...[/yellow]")
                        time.sleep(delay)
                        delay *= 2  # Exponential backoff
                    else:
                        raise e
            return None
        return wrapper
    return decorator


@retry_on_throttling(max_retries=3)
def get_available_aws_regions(session: boto3.Session, service_name: str = "ec2") -> list:
    """
    AWS account ke saare available aur active regions return karta hai.
    """
    try:
        client = session.client(service_name)
        regions_info = client.describe_regions(AllRegions=False)
        region_names = [region["RegionName"] for region in regions_info.get("Regions", [])]
        return region_names
    except Exception as e:
        print(f"[red]Failed to fetch regions: {str(e)}[/red]")
        return ["us-east-1"]  # Fallback region