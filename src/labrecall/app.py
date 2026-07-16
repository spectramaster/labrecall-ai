import json
import logging
import platform
import time
from functools import lru_cache
from pathlib import Path
from uuid import UUID, uuid4

import boto3
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from mangum import Mangum

from labrecall.agent import RepairAgent
from labrecall.config import get_settings
from labrecall.embeddings import BedrockTitanEmbedder, HashEmbedder
from labrecall.generation import BedrockNovaExplainer
from labrecall.memory import CockroachMemoryStore, LocalMemoryStore
from labrecall.models import (
    AuditEvent,
    ErrorResponse,
    IncidentInput,
    MemoryStats,
    OutcomeInput,
    OutcomeReceipt,
    Recommendation,
)

app = FastAPI(title="LabRecall AI", version="0.2.0")
logger = logging.getLogger("labrecall")
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.middleware("http")
async def request_context(request: Request, call_next: object) -> object:
    request_id = request.headers.get("x-request-id") or str(uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "request_failed",
            extra={"request_id": request_id, "path": request.url.path},
        )
        raise
    response.headers["x-request-id"] = request_id
    response.headers["x-content-type-options"] = "nosniff"
    response.headers["referrer-policy"] = "no-referrer"
    response.headers["permissions-policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["content-security-policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'"
    )
    logger.info(
        "request_completed",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "latency_ms": round((time.perf_counter() - started) * 1000, 3),
        },
    )
    return response


@app.exception_handler(ValueError)
async def conflict_error(request: Request, error: ValueError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid4()))
    return JSONResponse(
        status_code=409,
        content=ErrorResponse(error=str(error), request_id=request_id).model_dump(),
        headers={"x-request-id": request_id},
    )


@app.exception_handler(RuntimeError)
async def dependency_error(request: Request, error: RuntimeError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid4()))
    logger.error(
        "dependency_unavailable",
        extra={"request_id": request_id, "error_type": type(error).__name__},
    )
    return JSONResponse(
        status_code=503,
        content=ErrorResponse(
            error="A required dependency is temporarily unavailable.",
            request_id=request_id,
        ).model_dump(),
        headers={"x-request-id": request_id},
    )


def _database_url() -> str:
    settings = get_settings()
    if settings.database_url:
        return settings.database_url
    if not settings.database_secret_arn:
        raise RuntimeError("DATABASE_URL or DATABASE_SECRET_ARN is required in cloud mode")
    client = boto3.client("secretsmanager", region_name=settings.aws_region)
    response = client.get_secret_value(SecretId=settings.database_secret_arn)
    secret = json.loads(response["SecretString"])
    if not isinstance(secret.get("DATABASE_URL"), str):
        raise RuntimeError("secret must contain a DATABASE_URL string")
    return secret["DATABASE_URL"]


def _session_namespace(session_id: str | None) -> str:
    settings = get_settings()
    provider = settings.embedding_provider if settings.labrecall_mode == "cloud" else "hash"
    base_namespace = f"{settings.memory_namespace}-{provider}"
    if not session_id:
        return base_namespace
    import hashlib

    suffix = hashlib.sha256(session_id.encode()).hexdigest()[:12]
    return f"{base_namespace}-{suffix}"


@lru_cache(maxsize=128)
def get_agent(session_id: str | None = None) -> RepairAgent:
    settings = get_settings()
    namespace = _session_namespace(session_id)
    if settings.labrecall_mode == "cloud":
        if settings.embedding_provider == "bedrock":
            bedrock = boto3.client("bedrock-runtime", region_name=settings.aws_region)
            embedder = BedrockTitanEmbedder(
                bedrock,
                settings.bedrock_embed_model,
                settings.embedding_dimensions,
            )
            explainer = BedrockNovaExplainer(bedrock, settings.bedrock_text_model)
        else:
            embedder = HashEmbedder(settings.embedding_dimensions)
            explainer = None
        return RepairAgent(
            store=CockroachMemoryStore(_database_url(), namespace),
            embedder=embedder,
            mode=settings.labrecall_mode,
            retrieval_limit=settings.retrieval_limit,
            retrieval_min_similarity=settings.retrieval_min_similarity,
            explainer=explainer,
        )
    return RepairAgent(
        store=LocalMemoryStore(),
        embedder=HashEmbedder(settings.embedding_dimensions),
        mode=settings.labrecall_mode,
        retrieval_limit=settings.retrieval_limit,
        retrieval_min_similarity=settings.retrieval_min_similarity,
    )


@app.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "mode": settings.labrecall_mode,
        "embedding_provider": (
            settings.embedding_provider if settings.labrecall_mode == "cloud" else "hash"
        ),
        "version": "0.2.0",
        "architecture": platform.machine(),
    }


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/ready")
def readiness(x_labrecall_session: str | None = Header(default=None)) -> dict[str, object]:
    return {
        "status": "ready",
        "memory": get_agent(x_labrecall_session).store.stats().model_dump(),
    }


@app.post("/api/incidents", response_model=Recommendation)
def analyze_incident(
    incident: IncidentInput,
    x_labrecall_session: str | None = Header(default=None),
) -> Recommendation:
    return get_agent(x_labrecall_session).analyze(incident)


@app.post("/api/incidents/{incident_id}/outcome", response_model=OutcomeReceipt)
def record_outcome(
    incident_id: UUID,
    outcome: OutcomeInput,
    x_labrecall_session: str | None = Header(default=None),
) -> OutcomeReceipt:
    try:
        return get_agent(x_labrecall_session).learn(incident_id, outcome)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Incident not found") from error


@app.get("/api/memory/stats", response_model=MemoryStats)
def memory_stats(x_labrecall_session: str | None = Header(default=None)) -> MemoryStats:
    return get_agent(x_labrecall_session).store.stats()


@app.get("/api/memory/timeline", response_model=list[AuditEvent])
def memory_timeline(
    limit: int = 20,
    x_labrecall_session: str | None = Header(default=None),
) -> list[AuditEvent]:
    bounded_limit = min(max(limit, 1), 50)
    return get_agent(x_labrecall_session).store.recent_audit_events(bounded_limit)


handler = Mangum(app)
