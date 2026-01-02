from typing import Any, Dict
from urllib.parse import urlparse

from clipped.types.base_url import BaseUrl


class S3Path(BaseUrl):
    allowed_schemes = ["s3"]

    @classmethod
    def _validate(cls, value: Any):
        if isinstance(value, Dict):
            _value = value.get("bucket")
            if not _value:
                raise ValueError("Received a wrong bucket definition: %s", value)
            if "://" not in _value:
                _value = "s3://{}".format(_value)
            key = value.get("key")
            if key:
                _value = "{}/{}".format(_value, key)
            value = _value
        cls.get_structured_value(value)
        return value

    def to_param(self):
        return str(self)

    @staticmethod
    def get_structured_value(value):
        value = str(value)
        try:
            parsed_url = urlparse(value)
        except Exception as e:
            raise ValueError(f"Received a wrong URL definition: {e}")

        if parsed_url.scheme != "s3":
            raise ValueError(f"Invalid scheme in S3 URL: {parsed_url.scheme}")

        bucket = parsed_url.netloc
        key = parsed_url.path.strip("/")

        if not bucket:
            raise ValueError("S3 URL must include a bucket name.")

        return dict(bucket=bucket, key=key)
