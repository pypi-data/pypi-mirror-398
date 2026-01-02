"""
MPConfig 핸들러 클래스
"""

import json
import os
from datetime import date
from typing import Dict, List, Optional

import boto3

from finter.ops.position.config import S3_BUCKET
from finter.ops.position.core.models import (
    Effective,
    MergeSpec,
    MPConfig,
    Operation,
    Version,
)
from finter.ops.position.core.operations import (
    combined_op,
    merge_op,
    replace_op,
    split_op,
)
from finter.ops.position.core.utils import save_config


class MPConfigHandler:
    """MPConfig를 쉽게 관리할 수 있는 핸들러"""

    def __init__(
        self,
        identity_name: str,
        config: Optional[MPConfig] = None,
        s3_bucket: str = S3_BUCKET,
    ):
        if config is None:
            # 기존 설정 파일이 있으면 로드, 없으면 새로 생성
            try:
                loaded_handler = self.load_from_file(identity_name, s3_bucket)
                self.config = loaded_handler.config
            except Exception:
                # 파일이 없거나 로드 실패 시 새로 생성
                self.config = MPConfig(identity_name=identity_name, versions=[])
        else:
            self.config = config

    def create_new_version(
        self,
        from_date: date,
        to_date: Optional[date] = None,
        continue_flag: bool = False,
        author: Optional[str] = None,
    ) -> str:
        """새 버전을 생성하고 버전 문자열을 반환"""
        version_num = len(self.config.versions) + 1
        version_str = f"v{version_num}"

        new_version = Version(
            ver=version_str,
            author=author or os.getenv("USER", "unknown"),
            effective=Effective.model_validate(
                {"from": from_date, "to": to_date, "continue": continue_flag}
            ),
            ops=Operation(),
        )
        self.config.versions.append(new_version)
        return version_str

    def get_current_version(self) -> str:
        """현재 최신 버전 반환"""
        if not self.config.versions:
            raise ValueError("No versions exist")
        return self.config.versions[-1].ver

    def add_replace_op(self, src: str, dst: str, version: Optional[str] = None):
        """replace operation 추가"""
        if version is None:
            version = self.get_current_version()
        version_obj = self._find_version(version)

        # 기존 operations와 새 operation 합침
        existing_ops = version_obj.ops
        new_op = replace_op(src, dst)

        replaces = existing_ops.replace or []
        if new_op.replace:
            replaces.extend(new_op.replace)

        new_ops = combined_op(
            replaces=replaces, splits=existing_ops.split, merges=existing_ops.merge
        )

        # Validation
        self._validate_operations(new_ops)
        version_obj.ops = new_ops

    def add_split_op(
        self, src: str, ratios: Dict[str, float], version: Optional[str] = None
    ):
        """split operation 추가"""
        if version is None:
            version = self.get_current_version()
        version_obj = self._find_version(version)

        # 기존 operations와 새 operation 합침
        existing_ops = version_obj.ops
        new_op = split_op(src, ratios)

        splits = existing_ops.split or []
        if new_op.split:
            splits.extend(new_op.split)

        new_ops = combined_op(
            replaces=existing_ops.replace, splits=splits, merges=existing_ops.merge
        )

        # Validation
        self._validate_operations(new_ops)
        version_obj.ops = new_ops

    def add_merge_op(self, sources: List[str], to: str, version: Optional[str] = None):
        """merge operation 추가"""
        if version is None:
            version = self.get_current_version()
        version_obj = self._find_version(version)

        # 기존 operations와 새 operation 합침
        existing_ops = version_obj.ops
        new_op = merge_op(sources, to)

        merges = existing_ops.merge or []
        if new_op.merge:
            merges.extend(new_op.merge)

        new_ops = combined_op(
            replaces=existing_ops.replace, splits=existing_ops.split, merges=merges
        )

        # Validation
        self._validate_operations(new_ops)
        version_obj.ops = new_ops

    def add_operations(self, operations: List[Dict], version: Optional[str] = None):
        """여러 operation을 한번에 추가"""
        if version is None:
            version = self.get_current_version()
        version_obj = self._find_version(version)

        # 기존 operations 가져오기
        existing_ops = version_obj.ops
        replaces = existing_ops.replace[:] if existing_ops.replace else []
        splits = existing_ops.split[:] if existing_ops.split else []
        merges = existing_ops.merge[:] if existing_ops.merge else []

        # 새 operations 추가
        for op_data in operations:
            if "replace" in op_data:
                replaces.append(op_data["replace"])
            elif "split" in op_data:
                splits.append(op_data["split"])
            elif "merge" in op_data:
                merge_spec = op_data["merge"]
                merges.append(
                    MergeSpec(sources=merge_spec["sources"], to=merge_spec["to"])
                )

        # 모든 operations 합침
        new_ops = combined_op(
            replaces=replaces if replaces else None,
            splits=splits if splits else None,
            merges=merges if merges else None,
        )

        # Validation
        self._validate_operations(new_ops)
        version_obj.ops = new_ops

    def delete_version(self, version: str):
        """특정 버전 삭제"""
        for i, v in enumerate(self.config.versions):
            if v.ver == version:
                self.config.versions.pop(i)
                return
        raise ValueError(f"Version '{version}' not found")

    def _find_version(self, version: str) -> Version:
        for v in self.config.versions:
            if v.ver == version:
                return v
        raise ValueError(f"Version '{version}' not found")

    def _validate_operations(self, ops: Operation) -> None:
        """Operations 내의 중복 검증"""
        errors = []

        # Replace operation 중복 검증
        if ops.replace:
            replace_sources = set()
            for replace_dict in ops.replace:
                for src in replace_dict.keys():
                    if src in replace_sources:
                        errors.append(f"Replace source '{src}'가 중복됩니다")
                    replace_sources.add(src)

        # Split operation 중복 검증
        if ops.split:
            split_sources = set()
            for split_dict in ops.split:
                for src in split_dict.keys():
                    if src in split_sources:
                        errors.append(f"Split source '{src}'가 중복됩니다")
                    split_sources.add(src)

        # Merge operation sources 간 교집합 검증
        if ops.merge:
            all_merge_sources: List[List[str]] = []
            for merge_spec in ops.merge:
                sources_set = set(merge_spec.sources)
                # 각 merge 내부에서도 중복 검증
                if len(sources_set) != len(merge_spec.sources):
                    errors.append(
                        f"Merge sources {merge_spec.sources}에 중복이 있습니다"
                    )

                # 다른 merge와의 교집합 검증
                for prev_sources in all_merge_sources:
                    intersection = sources_set & set(prev_sources)
                    if intersection:
                        errors.append(
                            f"Merge sources 간 교집합이 있습니다: {list(intersection)} "
                            f"(sources1: {prev_sources}, sources2: {merge_spec.sources})"
                        )
                all_merge_sources.append(merge_spec.sources)

        # Replace, Split, Merge 간 중복 검증
        all_keys = set()

        if ops.replace:
            for replace_dict in ops.replace:
                for src in replace_dict.keys():
                    if src in all_keys:
                        errors.append(f"'{src}'가 여러 operation에서 사용됩니다")
                    all_keys.add(src)

        if ops.split:
            for split_dict in ops.split:
                for src in split_dict.keys():
                    if src in all_keys:
                        errors.append(f"'{src}'가 여러 operation에서 사용됩니다")
                    all_keys.add(src)

        if ops.merge:
            for merge_spec in ops.merge:
                for src in merge_spec.sources:
                    if src in all_keys:
                        errors.append(f"'{src}'가 여러 operation에서 사용됩니다")
                    all_keys.add(src)

        if errors:
            raise ValueError("Operation validation 실패:\n" + "\n".join(errors))

    def save(self, s3_bucket: str = S3_BUCKET) -> str:
        """설정 S3에 저장"""
        # 모든 버전이 최소 하나의 operation을 가지고 있는지 검증
        for version in self.config.versions:
            op = version.ops
            op_count = sum(
                [1 if op.replace else 0, 1 if op.split else 0, 1 if op.merge else 0]
            )
            if op_count == 0:
                raise ValueError(
                    f"Version {version.ver}는 최소 하나의 operation을 가져야 합니다"
                )

            # 각 버전의 operations 중복 검증
            self._validate_operations(op)

        return save_config(self.config, s3_bucket)

    def get_config_dict(self) -> dict:
        """설정을 딕셔너리로 반환"""
        return self.config.model_dump(by_alias=True)

    def get_versions(self) -> List[dict]:
        """모든 버전 정보를 리스트로 반환"""
        return [v.model_dump(by_alias=True) for v in self.config.versions]

    def get_version_ops(self, version: Optional[str] = None) -> dict:
        """특정 버전의 operations 반환"""
        if version is None:
            version = self.get_current_version()
        version_obj = self._find_version(version)
        return version_obj.ops.model_dump()

    def get_effective_date_range(self, version: Optional[str] = None) -> dict:
        """특정 버전의 유효 날짜 범위 반환"""
        if version is None:
            version = self.get_current_version()
        version_obj = self._find_version(version)
        return version_obj.effective.model_dump(by_alias=True)

    @classmethod
    def load_from_file(cls, identity_name: str, s3_bucket: str = S3_BUCKET):
        """S3에서 설정 파일 로드"""
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_DEFAULT_REGION", "ap-northeast-2"),
        )

        file_name = f"{identity_name}.ops"

        try:
            response = s3_client.get_object(Bucket=s3_bucket, Key=file_name)
            data = json.loads(response["Body"].read().decode("utf-8"))
            config = MPConfig.model_validate(data)
            return cls(identity_name, config)
        except s3_client.exceptions.NoSuchKey:
            return cls(identity_name)

    @classmethod
    def list_configs(cls, identity_name: str, s3_bucket: str = S3_BUCKET) -> List[str]:
        """S3에서 사용 가능한 설정 파일들의 identity_name 리스트 반환"""
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_DEFAULT_REGION", "ap-northeast-2"),
        )

        try:
            response = s3_client.list_objects_v2(
                Bucket=s3_bucket, Prefix="", Delimiter="/"
            )
            configs = []
            if "Contents" in response:
                for obj in response["Contents"]:
                    key = obj["Key"]
                    if key.endswith(".ops"):
                        identity_name = key.replace(".ops", "")
                        configs.append(identity_name)
            return configs
        except Exception:
            return []
