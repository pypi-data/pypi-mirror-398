from enum import Enum


class LogLevel(str, Enum):
    trace = "trace"
    debug = "debug"
    info = "info"
    warning = "warn"
    error = "error"
    critical = "critical"

class LogCategory(str, Enum):
    request = "request"
    response = "response"
    service = "service"
    outbound = "outbound"
    excel = "excel"
    access = "access"
    query = "query"
    engine = "engine"
    authorize = "authorize"
    metrics = "metrics"
    database = "database"
