from boto3 import resource
from botocore.config import Config
from splash.env import AWS_REGION, AWS_BUCKET_NAME, AWS_ENDPOINT_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

s3 = resource(
        's3',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        endpoint_url=AWS_ENDPOINT_URL,
        config=Config(
            connect_timeout=5,
            read_timeout=30,
            retries={'max_attempts': 3, 'mode': 'standard'},
        ),
)

bucket = s3.Bucket(AWS_BUCKET_NAME)
