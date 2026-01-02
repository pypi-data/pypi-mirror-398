"""
틸팅 관련 Pydantic 모델들
"""

import math
from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class Effective(BaseModel):
    from_: date = Field(..., alias="from")
    to: Optional[date] = None
    continue_: bool = Field(default=False, alias="continue")

    @model_validator(mode="after")
    def validate_effective(self) -> "Effective":
        if not self.continue_ and self.to is None:
            raise ValueError("effective 'to' 필드는 continue가 false일 때 필수입니다")
        return self


class MergeSpec(BaseModel):
    sources: List[str]
    to: str


class Operation(BaseModel):
    replace: Optional[List[Dict[str, str]]] = None
    split: Optional[List[Dict[str, Dict[str, float]]]] = None
    merge: Optional[List[MergeSpec]] = None

    def model_dump(self, **kwargs):
        """null 필드들을 제외하고 실제 데이터만 반환"""
        data = super().model_dump(**kwargs)
        # null이 아닌 필드만 반환
        return {k: v for k, v in data.items() if v is not None}


class Version(BaseModel):
    ver: str
    author: Optional[str] = None
    effective: Effective
    ops: Operation

    @model_validator(mode="after")
    def validate_ops(self) -> "Version":
        def _is_symbol(s: str) -> bool:
            return isinstance(s, str) and len(s) > 0

        def _validate_split_ratios(ratios: Dict[str, float]):
            total = 0.0
            for dst, r in ratios.items():
                if not _is_symbol(dst):
                    raise ValueError(f"split 대상 심볼이 유효하지 않습니다: {dst}")
                if not isinstance(r, (int, float)) or r < 0:
                    raise ValueError(
                        f"split 비율은 0 이상 숫자여야 합니다: {dst} -> {r}"
                    )
                total += float(r)
            if not math.isclose(total, 1.0, rel_tol=0, abs_tol=1e-9):
                raise ValueError(f"split 비율의 합은 1.0이어야 합니다 (현재 {total})")

        op = self.ops

        # Operation이 있는 경우에만 validation 수행
        if op.replace:
            for replace_item in op.replace:
                for src, dst in replace_item.items():
                    if not _is_symbol(src) or not _is_symbol(dst):
                        raise ValueError(
                            f"replace에서 유효하지 않은 심볼: {src} -> {dst}"
                        )

        if op.split:
            for split_item in op.split:
                for src, ratios in split_item.items():
                    if not _is_symbol(src):
                        raise ValueError(f"split 소스 심볼이 유효하지 않습니다: {src}")
                    _validate_split_ratios(ratios)

        if op.merge:
            for merge_spec in op.merge:
                if len(merge_spec.sources) < 2:
                    raise ValueError(
                        f"merge는 2개 이상 소스가 필요합니다: {merge_spec.sources}"
                    )
                if not all(_is_symbol(s) for s in merge_spec.sources) or not _is_symbol(
                    merge_spec.to
                ):
                    raise ValueError(
                        f"merge에서 유효하지 않은 심볼: {merge_spec.sources} -> {merge_spec.to}"
                    )

        return self


class MPConfig(BaseModel):
    identity_name: str
    versions: List[Version]
