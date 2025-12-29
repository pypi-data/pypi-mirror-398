"""
Tencent Cloud Provider
[tencentcloud-sdk-python](https://github.com/TencentCloud/tencentcloud-sdk-python)
"""

import json

from pydantic import BaseModel, ConfigDict
from pydantic import Field, TypeAdapter, ValidationError
from typing import Annotated

from tencentcloud.common import credential, retry

PositiveInt = Annotated[int, Field(gt=0)]

__all__ = []


class A:
    s: str


class TencentCloudCredential(credential.Credential, BaseModel):
    pass


from pydantic import BaseModel, Field
from typing import Optional, Annotated


class TencentCredentialParams(BaseModel):
    model_config = ConfigDict(
        extra="forbid",  # 'forbid'：不允许提供额外数据。
    )

    x: str = "ss"
    secret_id: str = Field(
        ..., description="Tencent Cloud SecretId", json_schema_extra={"env": "TENCENTCLOUD_SECRET_ID"}
    )
    secret_key: str = Field(
        ..., description="Tencent Cloud SecretKey", json_schema_extra={"env": "TENCENTCLOUD_SECRET_KEY"}
    )


x: TencentCredentialParams = TencentCredentialParams(secret_id="123", secret_key="456", x="s")
# print(type( x.secret_id))
# print(x)
print(json.dumps(x.model_json_schema(), indent=2))
print(x.model_extra)
print(x.model_fields_set)
