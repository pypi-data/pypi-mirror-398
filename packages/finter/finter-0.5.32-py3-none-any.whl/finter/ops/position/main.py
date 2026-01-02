"""
틸팅 설정 메인 예제
(기존 tilting.py의 예제 부분)
"""

from datetime import date

from pydantic import ValidationError

from finter.ops.position.core.handler import MPConfigHandler


def main():
    """메인 실행 예제"""
    try:
        print("=== 분리된 모듈로 구현한 틸팅 API ===")

        # 설정 핸들러 생성 (기존 파일이 있으면 자동 로드)
        handler = MPConfigHandler("flexible_fund.krx.krx.stock.smpark.sample")

        # v1 생성 및 operations 추가
        handler.create_new_version(date(2025, 2, 1), date(2025, 6, 30))
        handler.add_replace_op("AAPL", "MSFT")
        handler.add_split_op("GOOGL", {"META": 0.6, "AMZN": 0.4})
        handler.add_merge_op(["IWM", "QQQ"], "SPY")

        # v2 생성 및 operations 추가
        handler.create_new_version(date(2025, 7, 1), continue_flag=True)

        handler.add_replace_op("AAPL", "MSFT")

        # v2 생성 및 operations 추가
        handler.add_operations(
            [
                {"replace": {"AAPL": "MSFT"}},
                {"split": {"GOOGL": {"META": 0.6, "AMZN": 0.4}}},
                {"merge": {"sources": ["IWM", "QQQ"], "to": "SPY"}},
            ]
        )

        # 저장
        path = handler.save()
        print(f"Saved: {path}")
        print(f"Current version: {handler.get_current_version()}")
        print(f"Config: {handler.get_config_dict()}")
        print(f"Versions: {handler.get_versions()}")
        print(f"V1 ops: {handler.get_version_ops('v1')}")
        print(f"Current effective range: {handler.get_effective_date_range()}")

    except ValidationError as e:
        print(e.json(indent=2))


if __name__ == "__main__":
    main()
