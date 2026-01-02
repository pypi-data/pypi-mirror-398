from datetime import date, datetime, timedelta
from typing import Any, Dict

from clipped.compact.pydantic import (
    ByteSize,
    FiniteFloat,
    FutureDate,
    Json,
    NegativeFloat,
    NegativeInt,
    NonNegativeFloat,
    NonNegativeInt,
    NonPositiveFloat,
    NonPositiveInt,
    PastDate,
    PaymentCardNumber,
    PositiveFloat,
    PositiveInt,
    SecretBytes,
    SecretStr,
    StrictBool,
    StrictBytes,
    StrictFloat,
    StrictInt,
    StrictStr,
)
from clipped.types.docker_image import ImageStr
from clipped.types.email import EmailStr
from clipped.types.gcs import GcsPath
from clipped.types.lists import ListStr
from clipped.types.s3 import S3Path
from clipped.types.strings import GenericStr
from clipped.types.uri import Uri
from clipped.types.uuids import UUIDStr
from clipped.types.wasb import WasbPath

URI = "uri"
AUTH = "auth"
LIST = "list"
GCS = "gcs"
S3 = "s3"
WASB = "wasb"
IMAGE = "image"
PATH = "path"
METRIC = "metric"
METADATA = "metadata"
DATE = "date"
DATETIME = "datetime"
UUID = "uuid"
EMAIL = "email"

MAPPING = {
    URI: Uri,
    IMAGE: ImageStr,
    GCS: GcsPath,
    S3: S3Path,
    WASB: WasbPath,
    PATH: str,
    METRIC: float,
    METADATA: Dict,
    UUID: UUIDStr,
    EMAIL: EmailStr,
    "any": Any,
    "str": GenericStr,
    "date": date,
    "datetime": date,
    "timedelta": timedelta,
}


FORWARDING = {
    "GenericStr": GenericStr,
    "Uri": Uri,
    "ImageStr": ImageStr,
    "GcsPath": GcsPath,
    "S3Path": S3Path,
    "WasbPath": WasbPath,
    "UUIDStr": UUIDStr,
    "EmailStr": EmailStr,
    "ListStr": ListStr,
    "StrictStr": StrictStr,
    "PositiveInt": PositiveInt,
    "NegativeInt": NegativeInt,
    "NonNegativeInt": NonNegativeInt,
    "NonPositiveInt": NonPositiveInt,
    "PositiveFloat": PositiveFloat,
    "NegativeFloat": NegativeFloat,
    "NonNegativeFloat": NonNegativeFloat,
    "NonPositiveFloat": NonPositiveFloat,
    "FiniteFloat": FiniteFloat,
    "Json": Json,
    "SecretStr": SecretStr,
    "SecretBytes": SecretBytes,
    "StrictBool": StrictBool,
    "StrictBytes": StrictBytes,
    "StrictInt": StrictInt,
    "StrictFloat": StrictFloat,
    "PaymentCardNumber": PaymentCardNumber,
    "ByteSize": ByteSize,
    "PastDate": PastDate,
    "FutureDate": FutureDate,
}

NON_LOADABLE = {
    "any",
    "str",
    "bool",
    "path",
    "date",
    "datetime",
    "timedelta",
    "uuid",
    "email",
    "Any",
    Any,
    str,
    bool,
    IMAGE,
    ImageStr,
    URI,
    Uri,
    GCS,
    GcsPath,
    S3,
    S3Path,
    WASB,
    WasbPath,
    EmailStr,
    UUIDStr,
    ListStr,
    GenericStr,
    date,
    datetime,
    timedelta,
}


COMPATIBLE_TYPES = [
    ["str", PATH, S3, GCS, WASB],
    [float, METRIC],
]


def are_compatible(type1: str, type2: str) -> bool:
    if type1 == type2:
        return True

    if type1 == "Any" and type2 == "Any":
        return True
    # Compatible types
    for compatible_type in COMPATIBLE_TYPES:
        if type1 in compatible_type and type2 in compatible_type:
            return True

    return False
