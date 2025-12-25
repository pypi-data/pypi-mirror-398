from __future__ import annotations

import io
import json
import threading
from typing import Any, Optional
from urllib.parse import urlparse

from xlog.event.base import EventLike
from xlog.group.base import BaseGroup

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    boto3 = None  # type: ignore
    BotoCoreError = Exception  # type: ignore
    ClientError = Exception  # type: ignore


class S3Group(BaseGroup):
    """
    DESC:
        S3-based logging group that writes events to JSONL format in AWS S3.
        Events are buffered in memory and written to S3 on flush or close.
        Requires boto3 (install with: pip install lib-x17-log[aws]).

    Params:
        uri: str, S3 URI where log file will be created (e.g., s3://bucket/path/to/file.log).
        id: Optional[str] = None, unique identifier for the group.
        name: Optional[str] = None, name of the group.
        profile: Optional[str] = None, AWS profile name to use.
        region: Optional[str] = None, AWS region name.
        session: Optional[boto3.Session] = None, existing boto3 session to use.
        encoding: str = "utf-8", text encoding for log entries.
        ensure_ascii: bool = False, whether to escape non-ASCII characters in JSON.
        store: bool = True, whether to store events in memory.
        async_: bool = False, whether to process events asynchronously.
        max_queue: int = 1000, maximum queue size for async processing.
        max_len: Optional[int] = 100_000, maximum events to store per stream.

    Examples:
        ```python
        from xlog.group.s3group import S3Group

        # Write logs to S3 with default credentials
        group = S3Group(
            uri="s3://my-bucket/logs/app.log",
            name="app",
            async_=True,
        )

        # With specific AWS profile
        group = S3Group(
            uri="s3://my-bucket/logs/app.log",
            profile="production",
            region="us-west-2",
        )

        # With existing session
        import boto3
        session = boto3.Session(profile_name="dev")
        group = S3Group(
            uri="s3://my-bucket/logs/app.log",
            session=session,
        )
        ```
    """

    def __init__(
        self,
        uri: str,
        id: Optional[str] = None,
        name: Optional[str] = None,
        profile: Optional[str] = None,
        region: Optional[str] = None,
        session: Optional[Any] = None,
        encoding: str = "utf-8",
        ensure_ascii: bool = False,
        store: bool = True,
        async_: bool = False,
        max_queue: int = 1000,
        max_len: Optional[int] = 100_000,
    ):
        if not HAS_BOTO3:
            raise ImportError("boto3 is required for S3Group.")

        super().__init__(
            id=id,
            name=name,
            store=store,
            async_=async_,
            max_queue=max_queue,
            max_len=max_len,
        )
        self.uri = uri
        self.parsed_uri = self._parse_s3_uri(uri)
        self.bucket = self._resolve_s3_bucket(self.parsed_uri)
        self.key = self._resolve_s3_key(self.parsed_uri)
        self.encoding = encoding
        self.ensure_ascii = ensure_ascii
        self._lock = threading.RLock()
        self._buffer = io.StringIO()

        self.profile = profile
        self.region = region
        self.session = self._resolve_session(session)
        self.client = self._resolve_client()

    def _parse_s3_uri(
        self,
        uri: str,
    ) -> urlparse:
        parsed = urlparse(uri)
        if parsed.scheme != "s3":
            raise ValueError(f"Invalid S3 URI scheme: {uri}. Expected s3://")
        if not parsed.netloc:
            raise ValueError(f"Invalid S3 URI: {uri}. Missing bucket name")
        return parsed

    def _resolve_s3_bucket(
        self,
        resolved_uri: urlparse,
    ) -> str:
        return resolved_uri.netloc

    def _resolve_s3_key(
        self,
        resolved_uri: urlparse,
    ) -> str:
        key = resolved_uri.path.lstrip("/")
        if not key:
            raise ValueError(f"Invalid S3 URI: {self.uri}. Missing object key")
        return key

    def _resolve_session(
        self,
        session: Optional[Any] = None,
    ) -> Any:
        if session is not None:
            resolved = session
        elif self.profile or self.region:
            resolved = boto3.Session(
                profile_name=self.profile,
                region_name=self.region,
            )
        else:
            resolved = boto3.Session()
        return resolved

    def _resolve_client(
        self,
    ) -> Any:
        return self.session.client("s3")

    def _consume(
        self,
        stream: str,
        event: EventLike,
    ) -> None:
        payload = event.to_dict()
        line = json.dumps(
            payload,
            ensure_ascii=self.ensure_ascii,
            sort_keys=True,
        )
        with self._lock:
            self._buffer.write(line + "\n")

    def flush(self) -> None:
        super().flush()
        with self._lock:
            content = self._buffer.getvalue()
            if content:
                self._write_to_s3(content)
                self._buffer.truncate(0)
                self._buffer.seek(0)

    def _write_to_s3(
        self,
        content: str,
    ) -> None:
        try:
            current = ""
            try:
                response = self.client.get_object(
                    Bucket=self.bucket,
                    Key=self.key,
                )
                current = response["Body"].read().decode(self.encoding)
            except ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchKey":
                    pass  # Object does not exist yet
                else:
                    raise

            full = current + content
            self.client.put_object(
                Bucket=self.bucket,
                Key=self.key,
                Body=full.encode(self.encoding),
                ContentType="application/x-ndjson",
            )
        except (BotoCoreError, ClientError):
            raise

    def _on_close(self) -> None:
        with self._lock:
            try:
                content = self._buffer.getvalue()
                if content:
                    self._write_to_s3(content)
            finally:
                self._buffer.close()
