import json
import os
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from labrecall.agent import RepairAgent
from labrecall.embeddings import HashEmbedder
from labrecall.memory import CockroachMemoryStore
from labrecall.models import IncidentInput, OutcomeInput


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    template = os.environ.get("DATABASE_URL_TEMPLATE")
    password = os.environ.get("DATABASE_PASSWORD")
    if not database_url and template and password:
        parts = urlsplit(template)
        host = parts.hostname or ""
        if ":" in host:
            host = f"[{host}]"
        port = f":{parts.port}" if parts.port else ""
        user = quote(unquote(parts.username or ""), safe="")
        netloc = f"{user}:{quote(password, safe='')}@{host}{port}"
        database_url = urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
    if not database_url:
        raise SystemExit("DATABASE_URL is required")

    agent = RepairAgent(
        CockroachMemoryStore(database_url, "client-proof"),
        HashEmbedder(1024),
        mode="cloud",
        retrieval_limit=3,
    )
    training = agent.analyze(
        IncidentInput(
            pipeline="synthetic spectral calibration",
            error="dark-reference drift after instrument warm restart",
            environment="synthetic fixture, no private data",
            constraints=["read-only diagnosis first"],
        )
    )
    receipt = agent.learn(
        training.incident_id,
        OutcomeInput(
            status="worked",
            action_taken="Wait for thermal stabilization and acquire a fresh dark reference.",
            observation="Synthetic residual returned below the acceptance threshold.",
        ),
    )
    recalled = agent.analyze(
        IncidentInput(
            pipeline="synthetic spectral calibration",
            error="warm restart produced drift in the dark reference",
            environment="synthetic fixture, no private data",
            constraints=["read-only diagnosis first"],
        )
    )
    stats = agent.store.stats()
    print(
        json.dumps(
            {
                "learned": receipt.learned,
                "recalled": bool(recalled.evidence),
                "top_similarity": round(recalled.evidence[0].similarity, 6),
                "top_confidence": round(recalled.evidence[0].confidence, 6),
                "stats": stats.model_dump(),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
