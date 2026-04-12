import json

import boto3
from botocore.exceptions import ClientError

from config import CDN_PUBLIC_URL, S3_ACCESS_KEY, S3_BUCKET, S3_ENDPOINT_URL, S3_REGION, S3_SECRET_KEY


s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name=S3_REGION,
)


def build_report_object_key(username: str, requested_from: str, requested_to: str, cache_version: str) -> str:
    safe_username = username.replace("/", "_")

    return f"reports/{safe_username}/{cache_version}/{requested_from}_{requested_to}.json"


def get_report_url_if_exists(object_key: str) -> str | None:
    try:
        s3.head_object(Bucket=S3_BUCKET, Key=object_key)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in {"404", "NoSuchKey", "NotFound"}:
            return None
        raise

    return f"{CDN_PUBLIC_URL}/{object_key}"


def upload_report(object_key: str, report: dict) -> str:
    payload = json.dumps(report, ensure_ascii=False, indent=4).encode("utf-8")
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=object_key,
        Body=payload,
        ContentType="application/json; charset=utf-8",
        CacheControl="public, max-age=3600, immutable",
    )

    return f"{CDN_PUBLIC_URL}/{object_key}"
