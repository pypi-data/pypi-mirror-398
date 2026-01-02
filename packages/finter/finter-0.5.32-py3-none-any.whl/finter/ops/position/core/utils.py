"""
틸팅 관련 유틸리티 함수들
"""

import json
import os
from typing import Any, Dict, List

import boto3

from finter.ops.position.config import S3_BUCKET
from finter.ops.position.core.models import MPConfig


def save_config(cfg: MPConfig, s3_bucket: str = S3_BUCKET) -> str:
    """설정을 S3에 .ops 파일로 저장"""
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "ap-northeast-2"),
    )

    file_name = f"{cfg.identity_name}.ops"
    s3_uri = f"s3://{s3_bucket}/{file_name}"

    clean_data: Dict[str, Any] = {"identity_name": cfg.identity_name, "versions": []}
    versions: List[Dict[str, Any]] = clean_data["versions"]

    for version in cfg.versions:
        version_data: Dict[str, Any] = {
            "ver": version.ver,
            "effective": version.effective.model_dump(by_alias=True),
        }
        if version.author:
            version_data["author"] = version.author

        # operations를 깔끔하게 변환
        clean_op = {}
        op_data = version.ops.model_dump()
        for key, value in op_data.items():
            if value is not None:
                clean_op[key] = value
        version_data["ops"] = clean_op

        versions.append(version_data)

    json_content = json.dumps(clean_data, ensure_ascii=False, indent=2, default=str)
    s3_client.put_object(
        Bucket=s3_bucket,
        Key=file_name,
        Body=json_content.encode("utf-8"),
        ContentType="application/json",
    )

    return s3_uri
