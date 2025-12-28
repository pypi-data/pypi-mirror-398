# 소개

**PyLogger**는 Python 애플리케이션에서 구조화된 로그를 남기고, Fluent Bit 등 외부 로깅 시스템으로 전송할 수 있도록 도와주는 로깅 유틸리티입니다.

# 설정

### 환경 변수 설정

**PyLogger**는 프로젝트 `.env` 파일에서 다음 값을 읽어옵니다:

- `FLUENTBIT_URL`: 로그를 전송할 Fluent Bit의 URL
- `COMPONENT_NAME`: 로그에 출력할 서비스 이름 (e.g. `datatransfer`, `noti`)
- `SYSTEM_NAME`: 로그에 출력할 시스템 이름 (e.g. `aps`, `dp`, `common`, `cp`)

# 지원하는 로그 레벨 및 카테고리

### 로그 레벨

- `trace`
- `debug`
- `info`
- `warn`
- `error`
- `critical`

### 로그 카테고리

- `request`
- `response`
- `service`
- `outbound`
- `excel`
- `access`
- `query`
- `engine`
- `authorize`

# 주요 메서드

- `bind_base_info()`: 컴포넌트와 시스템 정보로 기본 로그 컨텍스트를 초기화합니다.
- `bind_request_properties(request)`: 요청 정보(URL, 메서드, `tenant-id`, `tenant-name`, `project-name` 등 헤더)를 로그 컨텍스트에 바인딩합니다.
- `send_log(level, category, message, data=None, force_clean=False)`: 구조화된 로그를 Fluent Bit으로 전송합니다. `data` 딕셔너리로 추가 속성을 전달할 수 있으며, `force_clean=True`로 설정하면 기존 컨텍스트 없이 로깅합니다.
- `begin_request()`: 새로운 요청 로그 컨텍스트를 시작하고 Token을 반환합니다.
- `end_request(token)`: 요청이 끝난 후 로그 컨텍스트를 정리합니다.

# 설치

### 필요한 패키지

- `loguru`
- `pydantic-settings`
- `requests`

### 설치 방법

1. `Aleatorik-UI-Backend-Net` 디렉토리로 이동하세요.
2. `uv` 또는 `pip`로 설치하세요:

```bash
cd pycommon
uv sync
```

또는 pip 사용 시:

```bash
cd pycommon
pip install -e .
```

# 기본 사용법

### 1. 인스턴스 가져오기

```python
from pylogger.logger import logger_instance
```

### 2. 로그 컨텍스트 바인딩

로그를 남기기 전에 기본 정보와 요청 정보를 바인딩합니다:

```python
from fastapi import Request

async def some_endpoint(request: Request):
    logger_instance.bind_base_info()
    logger_instance.bind_request_properties(request)
    # ... 로직 ...
```

### 3. 로그 보내기

```python
logger_instance.send_log(level="info", category="response", message="사용자가 로그인했습니다.")
```

# 커스텀 속성 추가

`send_log`의 `data` 파라미터를 사용하여 추가 정보를 포함할 수 있습니다:

```python
@app.get("/items/{item_id}")
async def read_item(request: Request, item_id: int):
    request.state.logger.send_log(
        level="info",
        category="request",
        message=f"아이템 {item_id} 조회 요청",
        data={"item_price": 20.5, "user_role": "guest"}
    )
    return {"item_id": item_id}
```

# FastAPI 미들웨어 연동

`LoggingClient` 패턴을 사용하여 요청별 로깅 컨텍스트를 관리합니다.

### LoggingClient 정의

```python
from typing import Any
from pydantic import BaseModel
from pylogger.logger import logger_instance
from pylogger.utils.template import LogCategory, LogLevel


class LoggingClient:
    """요청 컨텍스트를 관리하고 모든 로그에 첨부합니다."""

    class RequestEntry(BaseModel):
        traceId: str | None = None
        userId: str | None = None
        userAgent: str | None = None
        requestPath: str | None = None
        method: str | None = None
        tenantInfo: dict[str, Any] | None = None

    def __init__(self, request_entry: RequestEntry | None = None):
        self._request_entry = request_entry or self.RequestEntry()

    def send(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        data: dict[str, Any] | None = None,
        force_clean: bool = False,
    ) -> None:
        request_data = self._request_entry.model_dump(exclude_none=True)
        merged = {**request_data, **(data or {})}

        logger_instance.bind_base_info()
        logger_instance.send_log(
            level=level,
            category=category,
            message=message,
            data=merged,
            force_clean=force_clean,
        )


# 시작/종료 로깅용 전역 인스턴스
logger_client = LoggingClient()
```

### 미들웨어 설정

```python
from urllib.parse import urlparse
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pylogger.logger import logger_instance


def setup_logging_middleware(app: FastAPI) -> None:
    """FastAPI 앱에 로깅 미들웨어를 등록합니다."""

    @app.middleware("http")
    async def logging_ctx(request: Request, call_next):
        token = logger_instance.begin_request()
        try:
            logger_instance.bind_base_info()
            fields = logger_instance.bind_request_properties(request)

            # 요청별 로깅 클라이언트 생성
            entry = LoggingClient.RequestEntry(**fields)
            request.state.logger = LoggingClient(entry)

            clean_path = urlparse(str(request.url)).path.rstrip("/")
            excluded_suffixes = ("/health", "/openapi.json", "/docs", "/metrics")

            if clean_path.endswith(excluded_suffixes):
                return await call_next(request)

            request.state.logger.send_log(level="info", category="access", message=clean_path)

            response = await call_next(request)

            if isinstance(response, JSONResponse):
                body = response.body
            else:
                body = b"".join([chunk async for chunk in response.body_iterator])

            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        finally:
            logger_instance.end_request(token)
```

### main.py에서 등록

```python
from fastapi import FastAPI
from app.middleware.logging_middleware import setup_logging_middleware
from app.middleware.logging_client import logger_client

app = FastAPI(title="Your Service")
setup_logging_middleware(app)

# 라이프사이클 이벤트에는 logger_client 사용
logger_client.send_log(level="info", category="service", message="애플리케이션 시작")

# 커스텀 속성을 properties 필드에 추가하려면 data 파라미터 사용
logger_client.send_log(
    level="info",
    category="service",
    message="애플리케이션 시작",
    data={"partitionVer": "1.0.0", "userId": "me@vms-solutions.com"}
)
```

# 백그라운드 태스크 & ProcessPool

백그라운드 태스크나 ProcessPoolExecutor에서 로깅할 때는 (HTTP 요청 컨텍스트가 없음) 로그 컨텍스트를 전달하고 worker logger를 생성합니다:

```python
# 백그라운드 태스크 생성 전에 요청에서 컨텍스트 캡처
log_context = request.state.logger._request_entry.model_dump(exclude_none=True)

# 백그라운드 태스크에서 worker logger 생성
worker_logger = LoggingClient(LoggingClient.RequestEntry(**log_context))
worker_logger.send_log(level="info", category="service", message="백그라운드 처리 중...")
```

이렇게 하면 백그라운드 워커의 로그에도 원본 요청의 `traceId`, `userId`, `tenantInfo`가 유지되어 로그 추적이 가능합니다.