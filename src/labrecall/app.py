from functools import lru_cache
from uuid import UUID

import boto3
from fastapi import FastAPI, HTTPException
from mangum import Mangum

from labrecall.agent import RepairAgent
from labrecall.config import get_settings
from labrecall.embeddings import BedrockTitanEmbedder, HashEmbedder
from labrecall.memory import CockroachMemoryStore, LocalMemoryStore
from labrecall.models import (
    IncidentInput,
    MemoryStats,
    OutcomeInput,
    OutcomeReceipt,
    Recommendation,
)

app = FastAPI(title="LabRecall AI", version="0.1.0")


@lru_cache
def get_agent() -> RepairAgent:
    settings = get_settings()
    if settings.labrecall_mode == "cloud":
        if not settings.database_url:
            raise RuntimeError("DATABASE_URL is required in cloud mode")
        bedrock = boto3.client("bedrock-runtime", region_name=settings.aws_region)
        return RepairAgent(
            store=CockroachMemoryStore(settings.database_url, settings.memory_namespace),
            embedder=BedrockTitanEmbedder(
                bedrock,
                settings.bedrock_embed_model,
                settings.embedding_dimensions,
            ),
            mode=settings.labrecall_mode,
            retrieval_limit=settings.retrieval_limit,
        )
    return RepairAgent(
        store=LocalMemoryStore(),
        embedder=HashEmbedder(settings.embedding_dimensions),
        mode=settings.labrecall_mode,
        retrieval_limit=settings.retrieval_limit,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": get_settings().labrecall_mode, "version": "0.1.0"}


@app.post("/api/incidents", response_model=Recommendation)
def analyze_incident(incident: IncidentInput) -> Recommendation:
    return get_agent().analyze(incident)


@app.post("/api/incidents/{incident_id}/outcome", response_model=OutcomeReceipt)
def record_outcome(incident_id: UUID, outcome: OutcomeInput) -> OutcomeReceipt:
    try:
        return get_agent().learn(incident_id, outcome)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Incident not found") from error


@app.get("/api/memory/stats", response_model=MemoryStats)
def memory_stats() -> MemoryStats:
    return get_agent().store.stats()


handler = Mangum(app)
