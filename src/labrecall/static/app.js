const $ = (selector) => document.querySelector(selector);

let activeIncidentId = null;
let activeActions = [];

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
    headers: { "content-type": "application/json", ...(options.headers || {}) },
  });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || body.detail || "Request failed");
  return body;
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
    header.append(similarity, confidence);
    const signature = document.createElement("p");
    signature.textContent = item.failure_signature;
    const repair = document.createElement("p");
    repair.textContent = `Confirmed repair: ${item.repair_action}`;
    card.append(header, signature, repair);
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
  } catch (error) {
    $("#message").textContent = error.message;
  } finally {
    setBusy(button, false, "Save human-confirmed outcome");
  }
});

async function boot() {
  try {
    const health = await api("/health");
    $("#service-status").classList.add("ready");
    $("#service-status").lastChild.textContent = ` ${health.mode} service ready`;
  } catch (_) {
    $("#service-status").lastChild.textContent = " Service unavailable";
  }
  await refreshStats();
}

boot();
