const chat = document.getElementById("chat");
const form = document.getElementById("composer");
const promptInput = document.getElementById("prompt");
const sendBtn = document.getElementById("send");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const clearChatBtn = document.getElementById("clearChat");
const MAX_PROMPT_HEIGHT = 140;

function setStatus(state, text) {
  statusText.textContent = text;
  if (state === "ready") {
    statusDot.style.background = "var(--good)";
    statusDot.style.boxShadow = "0 0 0 4px rgba(47,191,113,.16)";
  } else if (state === "busy") {
    statusDot.style.background = "var(--warn)";
    statusDot.style.boxShadow = "0 0 0 4px rgba(246,179,75,.18)";
  } else {
    statusDot.style.background = "var(--bad)";
    statusDot.style.boxShadow = "0 0 0 4px rgba(229,75,75,.16)";
  }
}

function escapeText(s) {
  return (s ?? "").toString();
}

function resizePrompt() {
  promptInput.style.height = "auto";
  const nextHeight = Math.min(promptInput.scrollHeight, MAX_PROMPT_HEIGHT);
  promptInput.style.height = `${nextHeight}px`;
}

function createMessage(role, text) {
  const msg = document.createElement("div");
  msg.className = `msg ${role}`;

  const header = document.createElement("div");
  header.className = "msgHeader";

  const badge = document.createElement("div");
  badge.className = "badge";
  const pill = document.createElement("span");
  pill.className = "pill";
  pill.textContent = role === "user" ? "You" : "AskCSV";
  badge.appendChild(pill);

  const copyBtn = document.createElement("button");
  copyBtn.className = "copyBtn";
  copyBtn.type = "button";
  copyBtn.textContent = "Copy";
  copyBtn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(body.textContent || "");
      copyBtn.textContent = "Copied";
      setTimeout(() => (copyBtn.textContent = "Copy"), 900);
    } catch {
      copyBtn.textContent = "Nope";
      setTimeout(() => (copyBtn.textContent = "Copy"), 900);
    }
  });

  header.appendChild(badge);
  header.appendChild(copyBtn);

  const body = document.createElement("div");
  body.className = "msgBody";
  body.textContent = escapeText(text);

  msg.appendChild(header);
  msg.appendChild(body);

  chat.appendChild(msg);
  chat.scrollTop = chat.scrollHeight;

  return { msg, body };
}

function addLoadingTo(bodyEl) {
  bodyEl.textContent = "";
  const wrap = document.createElement("span");
  wrap.className = "loadingDots";
  wrap.innerHTML = "<span></span><span></span><span></span>";
  bodyEl.appendChild(wrap);
}

function addChart(msgEl, base64png) {
  const card = document.createElement("div");
  card.className = "card";

  const header = document.createElement("div");
  header.className = "cardHeader";
  header.textContent = "Chart";

  const body = document.createElement("div");
  body.className = "cardBody";

  const img = document.createElement("img");
  img.src = `data:image/png;base64,${base64png}`;

  body.appendChild(img);
  card.appendChild(header);
  card.appendChild(body);
  msgEl.appendChild(card);

  chat.scrollTop = chat.scrollHeight;
}

function addTable(msgEl, rows) {
  if (!rows || rows.length === 0) return;

  const card = document.createElement("div");
  card.className = "card";

  const header = document.createElement("div");
  header.className = "cardHeader";
  header.textContent = `Table (showing ${rows.length} rows)`;

  const body = document.createElement("div");
  body.className = "cardBody";

  const wrap = document.createElement("div");
  wrap.className = "tableWrap";

  const table = document.createElement("table");
  const cols = Object.keys(rows[0] || {});

  const thead = document.createElement("thead");
  const hr = document.createElement("tr");
  cols.forEach((c) => {
    const th = document.createElement("th");
    th.textContent = c;
    hr.appendChild(th);
  });
  thead.appendChild(hr);

  const tbody = document.createElement("tbody");
  rows.forEach((r) => {
    const tr = document.createElement("tr");
    cols.forEach((c) => {
      const td = document.createElement("td");
      const v = r[c];
      td.textContent = v === null || v === undefined ? "" : String(v);
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });

  table.appendChild(thead);
  table.appendChild(tbody);
  wrap.appendChild(table);
  body.appendChild(wrap);

  card.appendChild(header);
  card.appendChild(body);
  msgEl.appendChild(card);

  chat.scrollTop = chat.scrollHeight;
}

async function apiChat(prompt) {
  const r = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });

  if (!r.ok) {
    // FastAPI often returns {"detail": "..."}
    let detail = await r.text();
    try {
      const j = JSON.parse(detail);
      detail = j.detail || detail;
    } catch {}
    throw new Error(detail);
  }

  return await r.json();
}

async function sendPrompt(prompt) {
  if (!prompt) return;

  setStatus("busy", "Thinking...");
  sendBtn.disabled = true;
  promptInput.disabled = true;

  createMessage("user", prompt);

  const { msg: assistantMsg, body: assistantBody } = createMessage("assistant", "");
  addLoadingTo(assistantBody);

  try {
    const res = await apiChat(prompt);
    assistantBody.textContent = res.text || "(no text returned)";

    if (res.chart_base64_png) addChart(assistantMsg, res.chart_base64_png);
    if (res.table_preview) addTable(assistantMsg, res.table_preview);

    setStatus("ready", "Ready");
  } catch (e) {
    assistantBody.textContent = `Error: ${e.message || e}`;
    setStatus("error", "Error");
  } finally {
    sendBtn.disabled = false;
    promptInput.disabled = false;
    promptInput.focus();
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const prompt = promptInput.value.trim();
  if (!prompt) return;
  promptInput.value = "";
  resizePrompt();
  await sendPrompt(prompt);
});

promptInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    form.requestSubmit();
  }
});

promptInput.addEventListener("input", resizePrompt);

document.querySelectorAll(".chip").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const p = btn.getAttribute("data-prompt");
    await sendPrompt(p);
  });
});

clearChatBtn.addEventListener("click", () => {
  chat.innerHTML = "";
  boot();
});

function boot() {
  setStatus("ready", "Ready");
  createMessage(
    "assistant",
    "Welcome to AskCSV.\n\nTry:\n- \"Describe this dataset\"\n- \"Total amount for Food\"\n- \"Total amount by category, pie chart\"\n\nTip: if it guesses wrong, mention the exact column names."
  );
  resizePrompt();
}

boot();
