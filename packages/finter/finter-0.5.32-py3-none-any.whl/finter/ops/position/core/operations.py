"""
틸팅 operation 헬퍼 함수들
"""

from typing import Dict, List, Optional

from finter.ops.position.core.models import MergeSpec, Operation


def replace_op(src: str, dst: str) -> Operation:
    """replace operation 생성"""
    return Operation(replace=[{src: dst}])


def split_op(src: str, ratios: Dict[str, float]) -> Operation:
    """split operation 생성"""
    return Operation(split=[{src: ratios}])


def merge_op(sources: List[str], to: str) -> Operation:
    """merge operation 생성"""
    return Operation(merge=[MergeSpec(sources=sources, to=to)])


def combined_op(
    replaces: Optional[List[Dict[str, str]]] = None,
    splits: Optional[List[Dict[str, Dict[str, float]]]] = None,
    merges: Optional[List[MergeSpec]] = None,
) -> Operation:
    """여러 operation을 하나의 Operation 객체로 합침"""
    return Operation(replace=replaces, split=splits, merge=merges)
