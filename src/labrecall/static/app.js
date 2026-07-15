const $ = (selector) => document.querySelector(selector);

let activeIncidentId = null;
let activeActions = [];
let sessionId = localStorage.getItem("labrecall-session") || crypto.randomUUID();
localStorage.setItem("labrecall-session", sessionId);

function setBusy(button, busy, idleText) {
  button.disabled = busy;
  button.textContent = busy ? "Working…" : idleText;
}

function splitLines(value) {
  return value.split("\n").map((item) => item.trim()).filter(Boolean).slice(0, 12);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      "content-type": "application/json",
      "x-labrecall-session": sessionId,
      ...(options.headers || {}),
    },
  });
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json")
    ? await response.json()
    : { error: `Unexpected service response (${response.status})` };
  if (!response.ok) throw new Error(body.error || body.detail || "Request failed");
  return body;
}

function shortId(value) {
  return value ? `${value.slice(0, 8)}…` : "—";
}

function eventLabel(eventType) {
  return {
    "incident.created": "Incident captured",
    "memory.retrieved": "Memory search completed",
    "recommendation.created": "Recommendation created",
    "outcome.recorded": "Human outcome recorded",
    "memory.promoted": "Confirmed repair promoted",
    "memory.consolidated": "Evidence consolidated",
    "memory.confidence_updated": "Confidence recalibrated",
  }[eventType] || eventType;
}

async function refreshTimeline() {
  try {
    const events = await api("/api/memory/timeline?limit=20");
    const timeline = $("#timeline");
    timeline.replaceChildren();
    $("#timeline-empty").hidden = events.length > 0;
    for (const event of events) {
      const item = document.createElement("li");
      const marker = document.createElement("span");
      marker.className = "timeline-marker";
      const body = document.createElement("div");
      const heading = document.createElement("strong");
      heading.textContent = eventLabel(event.event_type);
      const meta = document.createElement("p");
      const time = new Date(event.created_at).toLocaleTimeString([], {
        hour: "2-digit", minute: "2-digit", second: "2-digit",
      });
      const evidence = event.evidence_ids.length
        ? ` · ${event.evidence_ids.length} cited record${event.evidence_ids.length === 1 ? "" : "s"}`
        : "";
      meta.textContent = `${time} · ${shortId(event.subject_id)}${evidence}`;
      body.append(heading, meta);
      item.append(marker, body);
      timeline.append(item);
    }
  } catch (_) {
    $("#timeline-empty").hidden = false;
    $("#timeline-empty").textContent = "Audit events are temporarily unavailable.";
  }
}

async function refreshStats() {
  try {
    const stats = await api("/api/memory/stats");
    $("#stat-incidents").textContent = stats.incidents;
    $("#stat-outcomes").textContent = stats.outcomes;
    $("#stat-memories").textContent = stats.reusable_memories;
    $("#stat-audits").textContent = stats.audit_events;
  } catch (_) {
    $("#message").textContent = "Memory statistics are temporarily unavailable.";
  }
}

function renderEvidence(items) {
  const list = $("#evidence");
  list.replaceChildren();
  $("#evidence-block").hidden = items.length === 0;
  for (const item of items) {
    const card = document.createElement("article");
    card.className = "evidence-card";
    const header = document.createElement("header");
    const similarity = document.createElement("span");
    similarity.textContent = `Similarity ${item.similarity.toFixed(3)}`;
    const confidence = document.createElement("span");
    confidence.textContent = `Confidence ${item.confidence.toFixed(3)}`;
    const score = document.createElement("span");
    score.textContent = `Decision ${item.ranking_score.toFixed(3)}`;
    header.append(similarity, confidence, score);
    const signature = document.createElement("p");
    signature.textContent = item.failure_signature;
    const repair = document.createElement("p");
    repair.textContent = `Confirmed repair: ${item.repair_action}`;
    const provenance = document.createElement("code");
    provenance.textContent = `memory ${item.memory_id}`;
    card.append(header, signature, repair, provenance);
    list.append(card);
  }
}

function renderRecommendation(result) {
  activeIncidentId = result.incident_id;
  activeActions = result.proposed_actions;
  $("#empty-result").hidden = true;
  $("#recommendation").hidden = false;
  $("#incident-id").textContent = result.incident_id;
  $("#summary").textContent = result.summary;
  $("#generation-mode").textContent = result.generation_degraded
    ? "Deterministic fallback"
    : result.generation_mode === "bedrock" ? "Bedrock Nova" : "Fixture mode";
  const actions = $("#actions");
  actions.replaceChildren();
  for (const action of result.proposed_actions) {
    const item = document.createElement("li");
    item.textContent = action;
    actions.append(item);
  }
  renderEvidence(result.evidence);
  $("#action-taken").value = result.proposed_actions[1] || result.proposed_actions[0] || "";
}

$("#incident-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = $("#analyze-button");
  setBusy(button, true, "Analyze with memory");
  $("#message").textContent = "";
  try {
    const result = await api("/api/incidents", {
      method: "POST",
      body: JSON.stringify({
        pipeline: $("#pipeline").value,
        error: $("#error").value,
        environment: $("#environment").value,
        attempted_actions: [],
        constraints: splitLines($("#constraints").value),
      }),
    });
    renderRecommendation(result);
    $("#message").textContent = "Recommendation created. Verify before recording an outcome.";
    await refreshStats();
    await refreshTimeline();
  } catch (error) {
    $("#message").textContent = error.message;
  } finally {
    setBusy(button, false, "Analyze with memory");
  }
});

$("#outcome-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!activeIncidentId) return;
  const button = $("#outcome-button");
  setBusy(button, true, "Save human-confirmed outcome");
  try {
    const status = document.querySelector('input[name="status"]:checked').value;
    const receipt = await api(`/api/incidents/${activeIncidentId}/outcome`, {
      method: "POST",
      body: JSON.stringify({
        status,
        action_taken: $("#action-taken").value,
        observation: $("#observation").value,
        side_effects: [],
      }),
    });
    $("#message").textContent = receipt.learned
      ? "Confirmed repair promoted to reusable memory."
      : "Outcome recorded; no reusable memory was promoted.";
    await refreshStats();
    await refreshTimeline();
  } catch (error) {
    $("#message").textContent = error.message;
  } finally {
    setBusy(button, false, "Save human-confirmed outcome");
  }
});

function setProofStage(stage, state) {
  const card = document.querySelector(`[data-proof-stage="${stage}"]`);
  card.classList.toggle("active", state === "active");
  card.classList.toggle("complete", state === "complete");
}

async function runProof() {
  const button = $("#proof-button");
  setBusy(button, true, "Run the 20-second proof");
  sessionId = crypto.randomUUID();
  localStorage.setItem("labrecall-session", sessionId);
  activeIncidentId = null;
  ["cold", "confirm", "recall"].forEach((stage) => setProofStage(stage, "idle"));
  try {
    setProofStage("cold", "active");
    const cold = await api("/api/incidents", {
      method: "POST",
      body: JSON.stringify({
        pipeline: "spectral calibration acceptance",
        error: "Dark-reference drift after an instrument warm restart",
        environment: "Synthetic TDLAS fixture, Python 3.12",
        attempted_actions: [],
        constraints: ["read-only diagnosis first", "preserve verified artifacts"],
      }),
    });
    if (cold.evidence.length !== 0) throw new Error("Fresh session did not begin cold.");
    setProofStage("cold", "complete");
    setProofStage("confirm", "active");
    await api(`/api/incidents/${cold.incident_id}/outcome`, {
      method: "POST",
      body: JSON.stringify({
        status: "worked",
        action_taken: "Wait for thermal stabilization and acquire a fresh dark reference.",
        observation: "Synthetic residual returned below the acceptance threshold.",
        side_effects: [],
      }),
    });
    setProofStage("confirm", "complete");
    setProofStage("recall", "active");
    const warm = await api("/api/incidents", {
      method: "POST",
      body: JSON.stringify({
        pipeline: "spectral calibration acceptance",
        error: "Warm restart caused drift in dark-reference calibration residuals",
        environment: "Synthetic TDLAS fixture, Python 3.12",
        attempted_actions: [],
        constraints: ["read-only diagnosis first", "preserve verified artifacts"],
      }),
    });
    if (warm.evidence.length === 0) throw new Error("Confirmed memory was not recalled.");
    renderRecommendation(warm);
    setProofStage("recall", "complete");
    $("#message").textContent = "Proof complete: cold abstention → human confirmation → cited recall.";
    await Promise.all([refreshStats(), refreshTimeline()]);
    $("#lifecycle").scrollIntoView({ behavior: "smooth", block: "center" });
  } catch (error) {
    $("#message").textContent = error.message;
  } finally {
    setBusy(button, false, "Run the 20-second proof");
  }
}

$("#proof-button").addEventListener("click", runProof);

async function boot() {
  try {
    const health = await api("/health");
    $("#service-status").classList.add("ready");
    $("#service-status").lastChild.textContent = ` ${health.mode} service ready`;
  } catch (_) {
    $("#service-status").lastChild.textContent = " Service unavailable";
  }
  await Promise.all([refreshStats(), refreshTimeline()]);
}

boot();
