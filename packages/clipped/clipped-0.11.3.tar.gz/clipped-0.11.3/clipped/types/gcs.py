from typing import Any, Dict
from urllib.parse import urlparse

from clipped.types.base_url import BaseUrl


class GcsPath(BaseUrl):
    allowed_schemes = ["gcs", "gs"]

    @classmethod
    def _validate(cls, value: Any):
        if isinstance(value, Dict):
            _value = value.get("bucket")
            if not _value:
                raise ValueError("Received a wrong bucket definition: %s", value)
            if "://" not in _value:
                _value = "gs://{}".format(_value)
            blob = value.get("blob")
            if blob:
                _value = "{}/{}".format(_value, blob)
            value = _value
        cls.get_structured_value(value)
        return value

    def to_param(self):
        return str(self)

    @staticmethod
    def get_structured_value(value):
        if not isinstance(value, str):
            value = str(value)
        try:
            parsed_url = urlparse(value)
        except Exception as e:
            raise ValueError(f"Received a wrong URL definition: {e}")

        if parsed_url.scheme not in {"gs", "gcs"}:
            raise ValueError(f"Invalid scheme in GCS URL: {parsed_url.scheme}")

        bucket = parsed_url.netloc
        blob = parsed_url.path.strip("/")

        if not bucket:
            raise ValueError("GCS URL must include a bucket name.")

        return dict(bucket=bucket, blob=blob)
