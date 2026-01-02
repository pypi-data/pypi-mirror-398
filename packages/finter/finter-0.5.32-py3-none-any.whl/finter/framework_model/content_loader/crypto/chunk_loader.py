"""
Crypto Chunk Loader for S3 chunk-based parquet data.

TODO: [TEMP] 테스트용 모듈 - 정식 배포 시 수정 필요
      - AWS 인증: 현재 환경변수 fallback 사용, 정식 배포 시 get_aws_credentials() 사용
      - 참조: docs/TODO_crypto_test_migration.md

S3 Structure:
    s3://finter-parquet/crypto/{data_name}/
    ├── metadata.json
    └── {interval}/
        └── {item}/
            ├── {timestamp1}
            ├── {timestamp2}
            └── ...
"""

from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List

import pandas as pd
import s3fs

from finter.framework_model.content import Loader


class CryptoChunkLoader(Loader):
    """
    S3에 저장된 crypto chunk parquet 파일들을 로드하는 로더.

    cm_name 형식: content.crypto.{data_name}.{item}.{interval}
    예: content.crypto.bnp_usdt.close.600
    """

    _metadata_cache: Dict[str, dict] = {}
    _chunk_list_cache: Dict[str, List[int]] = {}

    S3_BUCKET = "finter-parquet"
    S3_PREFIX = "crypto"

    def __init__(self, cm_name: str):
        self._cm_name = cm_name
        self._parse_cm_name(cm_name)

    def _parse_cm_name(self, cm_name: str):
        """
        cm_name에서 data_name, item, interval 추출.

        형식: content.crypto.{data_name}.{item}.{interval}
        예시: content.crypto.bnp_usdt.close.600
        """
        parts = cm_name.split(".")
        if len(parts) != 5:
            raise ValueError(
                f"Invalid cm_name format: {cm_name}. "
                f"Expected: content.crypto.{{data_name}}.{{item}}.{{interval}}"
            )
        self._data_name = parts[2]
        self._item = parts[3]
        self._interval = int(parts[4])

    def _get_s3_filesystem(self) -> s3fs.S3FileSystem:
        """AWS 인증된 S3 파일시스템 반환."""
        import os

        # 환경 변수 우선 사용 (crypto chunk는 기존 API에 등록 안 됨)
        aws_key = os.environ.get("AWS_ACCESS_KEY_ID")
        aws_secret = os.environ.get("AWS_SECRET_ACCESS_KEY")
        aws_token = os.environ.get("AWS_SESSION_TOKEN")

        if aws_key and aws_secret:
            return s3fs.S3FileSystem(
                key=aws_key,
                secret=aws_secret,
                token=aws_token,
            )

        # 기본 boto3 credentials chain 사용 (IAM role, ~/.aws/credentials 등)
        return s3fs.S3FileSystem(anon=False)

    def _get_base_path(self) -> str:
        """S3 base path 반환."""
        return f"s3://{self.S3_BUCKET}/{self.S3_PREFIX}/{self._data_name}"

    def _get_chunk_dir(self) -> str:
        """청크 디렉토리 경로 반환."""
        return f"{self._get_base_path()}/{self._interval}/{self._item}"

    def _list_chunk_files(self, fs: s3fs.S3FileSystem) -> List[int]:
        """
        해당 item/interval의 모든 청크 타임스탬프 목록 반환.
        """
        cache_key = f"{self._data_name}/{self._interval}/{self._item}"
        if cache_key in self._chunk_list_cache:
            return self._chunk_list_cache[cache_key]

        chunk_dir = self._get_chunk_dir()
        try:
            files = fs.ls(chunk_dir)
        except FileNotFoundError:
            return []

        timestamps = []
        for f in files:
            filename = f.split("/")[-1]
            if filename.isdigit():
                timestamps.append(int(filename))

        timestamps.sort()
        self._chunk_list_cache[cache_key] = timestamps
        return timestamps

    def _select_chunks(
        self,
        chunk_timestamps: List[int],
        start_ts: int,
        end_ts: int
    ) -> List[int]:
        """
        시간 범위에 해당하는 청크 선택.
        """
        if not chunk_timestamps:
            return []

        selected = []
        for i, ts in enumerate(chunk_timestamps):
            next_ts = chunk_timestamps[i + 1] if i + 1 < len(chunk_timestamps) else float('inf')
            if ts <= end_ts and next_ts > start_ts:
                selected.append(ts)

        return selected

    def _load_single_chunk(self, fs: s3fs.S3FileSystem, chunk_ts: int) -> pd.DataFrame:
        """단일 청크 파일 로드."""
        chunk_path = f"{self._get_chunk_dir()}/{chunk_ts}"
        with fs.open(chunk_path, "rb") as f:
            return pd.read_parquet(f, engine="pyarrow")

    def _load_chunks_parallel(
        self,
        fs: s3fs.S3FileSystem,
        chunk_timestamps: List[int],
        max_workers: int = 4
    ) -> pd.DataFrame:
        """
        여러 청크를 병렬로 로드하여 병합.
        """
        if not chunk_timestamps:
            return pd.DataFrame()

        if len(chunk_timestamps) == 1:
            return self._load_single_chunk(fs, chunk_timestamps[0])

        dfs = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._load_single_chunk, fs, ts): ts
                for ts in chunk_timestamps
            }
            for future in futures:
                try:
                    df = future.result()
                    dfs.append((futures[future], df))
                except Exception as e:
                    print(f"Failed to load chunk {futures[future]}: {e}")

        if not dfs:
            return pd.DataFrame()

        dfs.sort(key=lambda x: x[0])
        return pd.concat([df for _, df in dfs], axis=0)

    def _datetime_to_unix(self, dt_int: int) -> int:
        """YYYYMMDD 또는 YYYYMMDDHHmmss 형식을 Unix timestamp로 변환."""
        dt_str = str(dt_int)
        str_len = len(dt_str)

        if str_len == 8:  # YYYYMMDD
            dt = pd.to_datetime(dt_str, format="%Y%m%d")
        elif str_len == 12:  # YYYYMMDDHHmm
            dt = pd.to_datetime(dt_str, format="%Y%m%d%H%M")
        elif str_len == 14:  # YYYYMMDDHHmmss
            dt = pd.to_datetime(dt_str, format="%Y%m%d%H%M%S")
        else:
            dt = pd.to_datetime(dt_str)

        return int(dt.timestamp())

    def get_df(
        self,
        start: int,
        end: int,
        fill_nan: bool = True,
        columns: List[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        지정된 시간 범위의 데이터를 로드.

        Args:
            start: 시작 시간 (YYYYMMDD 또는 YYYYMMDDHHmmss)
            end: 종료 시간
            fill_nan: NaN 채우기 여부 (미사용, 호환성 유지)
            columns: 로드할 컬럼 (종목) 리스트

        Returns:
            시간 범위에 해당하는 DataFrame
        """
        fs = self._get_s3_filesystem()

        start_ts = self._datetime_to_unix(start)
        end_ts = self._datetime_to_unix(end)

        # end가 YYYYMMDD 형식이면 해당 일의 끝으로 설정
        if len(str(end)) == 8:
            end_ts += 86400 - 1  # 23:59:59

        all_chunks = self._list_chunk_files(fs)
        selected_chunks = self._select_chunks(all_chunks, start_ts, end_ts)

        if not selected_chunks:
            return pd.DataFrame()

        df = self._load_chunks_parallel(fs, selected_chunks)

        if df.empty:
            return df

        # 시간 범위로 슬라이싱
        start_dt = pd.to_datetime(start_ts, unit='s', utc=True)
        end_dt = pd.to_datetime(end_ts, unit='s', utc=True)

        # 인덱스가 DatetimeIndex인 경우에만 timezone 처리
        if isinstance(df.index, pd.DatetimeIndex):
            if df.index.tz is None:
                df.index = df.index.tz_localize('UTC')
            df = df.loc[start_dt:end_dt]
        else:
            # 인덱스가 datetime이 아닌 경우 (timestamp 등)
            df = df[(df.index >= start_ts) & (df.index <= end_ts)]

        # timestamp 인덱스를 DatetimeIndex로 변환 (timezone-naive로 통일)
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index, unit='s', utc=True).tz_localize(None)

        # 컬럼 필터링
        if columns:
            available_cols = [c for c in columns if c in df.columns]
            df = df[available_cols]

        return df
