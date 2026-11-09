/**
 * ThesisFlow Frontend Application Logic
 * Pure ES6+ JavaScript: Modular, Responsive, and Glassmorphic
 */

// --- 1. Global Application State ---
const State = {
  theme: localStorage.getItem("color-scheme") || "dark",
  activeView: "dashboard",
  papers: [],
  activePaperId: null,
  activePaper: null,
  activePaperPagesText: [],
  equations: [],
  activePageNum: 1,
  activeEquation: null,
  chatHistory: [],
  constants: [],
  playground: {
    model: "einstein",
    params: { m: 1.0, c: 299792458.0 },
    primaryX: "m",
    depVar: "E",
    minX: 0.001,
    maxX: 100.0,
    latex: "E = m c^2"
  }
};

// --- 2. API Service Layer ---
const API = {
  async getStatus() {
    const res = await fetch("/api/status");
    return res.json();
  },
  async getPapers(search = "") {
    const res = await fetch(`/api/papers${search ? "?search=" + encodeURIComponent(search) : ""}`);
    return res.json();
  },
  async getPaper(id) {
    const res = await fetch(`/api/papers/${id}`);
    return res.json();
  },
  async uploadPaper(file) {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch("/api/papers/upload", { method: "POST", body: fd });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to upload PDF");
    }
    return res.json();
  },
  async resetDemos() {
    const res = await fetch("/api/papers/reset-demos", { method: "POST" });
    return res.json();
  },
  async deletePaper(id) {
    const res = await fetch(`/api/papers/${id}`, { method: "DELETE" });
    return res.json();
  },
  async deconstructEquation(id, depth = "Intermediate") {
    const res = await fetch(`/api/equations/${id}/deconstruct`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ depth_level: depth, paper_title: State.activePaper ? State.activePaper.title : "Paper" })
    });
    return res.json();
  },
  async getCodeSuite(latex, depVar, indepVars, eqName) {
    const res = await fetch("/api/equations/code", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ latex, dependent_var: depVar, independent_vars: indepVars, equation_name: eqName })
    });
    return res.json();
  },
  async evaluatePlaygroundGrid(payload) {
    const res = await fetch("/api/playground/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    return res.json();
  },
  async sendChat(query, depth = "Intermediate") {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        paper_id: State.activePaperId,
        query,
        depth_level: depth,
        history: State.chatHistory
      })
    });
    return res.json();
  },
  async getConstants(cat = "", search = "") {
    let url = "/api/constants?";
    if (cat && cat !== "All") url += `category=${encodeURIComponent(cat)}&`;
    if (search) url += `search=${encodeURIComponent(search)}`;
    const res = await fetch(url);
    return res.json();
  },
  async saveExperiment(exp) {
    const res = await fetch("/api/experiments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(exp)
    });
    return res.json();
  },
  async updateApiKey(key) {
    const res = await fetch("/api/settings/api-key", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ api_key: key })
    });
    return res.json();
  }
};

// --- 3. UI Helpers & Toast Notifications ---
function showToast(msg, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.innerHTML = `<span>ℹ️</span><span>${msg}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(20px)";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function renderMath(element) {
  if (window.renderMathInElement) {
    window.renderMathInElement(element || document.body, {
      delimiters: [
        { left: "$$", right: "$$", display: true },
        { left: "\\[", right: "\\]", display: true },
        { left: "$", right: "$", display: false },
        { left: "\\(", right: "\\)", display: false }
      ],
      throwOnError: false
    });
  }
}

// --- 4. Modern Theme Management (Modern Web Guidance) ---
function initTheme() {
  const stored = localStorage.getItem("color-scheme") || "dark";
  setTheme(stored);

  // Sync if system preference changes and user has not hard-coded setting
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
    if (!localStorage.getItem("color-scheme")) {
      setTheme(e.matches ? "dark" : "light");
    }
  });

  const toggleBtn = document.getElementById("btn-theme-toggle");
  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      const nextTheme = State.theme === "dark" ? "light" : "dark";
      setTheme(nextTheme);
    });
  }
}

function setTheme(theme) {
  State.theme = theme;
  localStorage.setItem("color-scheme", theme);
  document.documentElement.setAttribute("data-theme", theme);

  const meta = document.querySelector('meta[name="color-scheme"]');
  if (meta) meta.content = theme;

  const toggleBtn = document.getElementById("btn-theme-toggle");
  if (toggleBtn) {
    toggleBtn.innerHTML = theme === "dark" ? "☀️" : "🌙";
    toggleBtn.title = `Switch to ${theme === "dark" ? "Light" : "Dark"} Mode`;
  }

  // Re-render plotly charts if present in current theme
  if (State.activeView === "playground") {
    renderPlaygroundChart();
  }
}

// --- 5. Navigation & View Routing ---
function initNavigation() {
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach((item) => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const target = item.getAttribute("data-view");
      switchView(target);

      // Close mobile sidebar if open
      document.querySelector(".sidebar")?.classList.remove("mobile-open");
    });
  });

  const mobileToggle = document.getElementById("mobile-toggle");
  if (mobileToggle) {
    mobileToggle.addEventListener("click", () => {
      document.querySelector(".sidebar")?.classList.toggle("mobile-open");
    });
  }
}

function switchView(viewName) {
  State.activeView = viewName;
  document.querySelectorAll(".nav-item").forEach((el) => {
    el.classList.toggle("active", el.getAttribute("data-view") === viewName);
  });
  document.querySelectorAll(".view-section").forEach((sec) => {
    sec.classList.toggle("active", sec.id === `view-${viewName}`);
  });

  // Lifecycle hooks per view
  if (viewName === "dashboard") refreshDashboard();
  else if (viewName === "library") renderLibraryView();
  else if (viewName === "explorer") renderExplorerView();
  else if (viewName === "playground") initPlaygroundView();
  else if (viewName === "constants") renderConstantsView();
  else if (viewName === "comparison") renderComparisonView();
  else if (viewName === "assistant") renderAssistantView();
}

// --- 6. Active Paper Management ---
async function loadPaperContext(paperId) {
  try {
    const data = await API.getPaper(paperId);
    State.activePaperId = paperId;
    State.activePaper = data.paper;
    State.equations = data.equations;
    State.activePaperPagesText = data.pages_text || [];
    State.activePageNum = 1;

    // Update Topbar Dropdown
    const select = document.getElementById("topbar-paper-select");
    if (select) select.value = paperId;

    // Update active view
    if (State.activeView === "dashboard") renderDashboardEquations();
    else if (State.activeView === "explorer") renderExplorerView();
    else if (State.activeView === "playground") initPlaygroundView();
  } catch (err) {
    showToast("Error loading paper details: " + err.message, "error");
  }
}

// --- 7. Dashboard View ---
async function refreshDashboard() {
  try {
    const status = await API.getStatus();
    document.getElementById("stat-papers").innerText = status.counts.papers;
    document.getElementById("stat-equations").innerText = status.counts.equations;
    document.getElementById("stat-experiments").innerText = status.counts.experiments;
    document.getElementById("stat-constants").innerText = status.counts.constants;

    const geminiStatus = document.getElementById("gemini-status-text");
    const geminiDot = document.getElementById("gemini-status-dot");
    if (status.gemini.connected) {
      geminiStatus.innerText = `Gemini Online (${status.gemini.latency_ms}ms)`;
      geminiDot.className = "status-dot status-online";
    } else {
      geminiStatus.innerText = "Offline / SymPy Mode";
      geminiDot.className = "status-dot status-offline";
    }

    // Refresh papers list
    const papers = await API.getPapers();
    State.papers = papers;
    populatePaperDropdowns(papers);

    if (papers.length > 0 && !State.activePaperId) {
      await loadPaperContext(papers[0].id);
    } else if (State.activePaperId) {
      renderDashboardEquations();
    }
  } catch (err) {
    console.error("Dashboard refresh error:", err);
  }
}

function populatePaperDropdowns(papers) {
  const topSelect = document.getElementById("topbar-paper-select");
  if (!topSelect) return;
  topSelect.innerHTML = "";
  papers.forEach((p) => {
    const opt = document.createElement("option");
    opt.value = p.id;
    opt.innerText = p.title.length > 40 ? p.title.substring(0, 40) + "..." : p.title;
    if (p.id === State.activePaperId) opt.selected = true;
    topSelect.appendChild(opt);
  });

  topSelect.onchange = (e) => {
    loadPaperContext(parseInt(e.target.value));
  };
}

function renderDashboardEquations() {
  const container = document.getElementById("dashboard-equations-list");
  if (!container) return;

  if (!State.equations || State.equations.length === 0) {
    container.innerHTML = `<p style="color: var(--text-muted);">No equations cataloged for the active paper.</p>`;
    return;
  }

  container.innerHTML = "";
  State.equations.slice(0, 6).forEach((eq) => {
    const card = createEquationCardElement(eq);
    container.appendChild(card);
  });
  renderMath(container);
}

// --- 8. Equation Card DOM Component ---
function createEquationCardElement(eq) {
  const card = document.createElement("div");
  card.className = "equation-card";

  const confPercent = Math.round(eq.confidence * 100);
  card.innerHTML = `
    <div class="eq-header">
      <div style="display: flex; align-items: center; gap: 8px;">
        <span class="thesisflow-badge">${eq.eq_id}</span>
        <span style="font-weight: 600; font-size: 0.9rem;">${eq.section_title}</span>
        <span style="font-size: 0.76rem; color: var(--text-muted);">• Page ${eq.page_number}</span>
      </div>
      <div>
        <span class="thesisflow-badge badge-emerald">${eq.category} (${confPercent}%)</span>
      </div>
    </div>
    <div class="eq-latex-box">
      $$${eq.latex}$$
    </div>
    <p style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 8px;">
      ${eq.context_paragraph ? eq.context_paragraph.substring(0, 160) + '...' : ''}
    </p>
    <div class="eq-actions">
      <button class="btn btn-primary btn-sm" onclick="openEquationInPlayground(${eq.id})">🔬 Playground</button>
      <button class="btn btn-glass btn-sm" onclick="openDeconstructModal(${eq.id})">✨ Deconstruct</button>
      <button class="btn btn-glass btn-sm" onclick="openCodeModal(${eq.id})">💻 Python Code</button>
    </div>
  `;
  return card;
}

// --- 9. Paper Upload Handler ---
function initUploadHandler() {
  const dropzone = document.getElementById("upload-dropzone");
  const fileInput = document.getElementById("paper-file-input");

  if (!dropzone || !fileInput) return;

  dropzone.addEventListener("click", () => fileInput.click());

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      handleFileUpload(fileInput.files[0]);
    }
  });
}

async function handleFileUpload(file) {
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    showToast("Please select a PDF document.", "error");
    return;
  }
  showToast(`Uploading and extracting '${file.name}'...`, "info");
  try {
    const res = await API.uploadPaper(file);
    showToast(`Successfully extracted ${res.equations_count} equations!`, "success");
    await refreshDashboard();
    await loadPaperContext(res.paper.id);
  } catch (err) {
    showToast(`Upload failed: ${err.message}`, "error");
  }
}

// --- 10. Paper Explorer (Split-Screen) ---
function renderExplorerView() {
  const pageNav = document.getElementById("explorer-page-num");
  const maxPages = State.activePaper ? State.activePaper.total_pages : 1;
  if (pageNav) {
    pageNav.innerText = `Page ${State.activePageNum} of ${maxPages}`;
  }

  const docViewer = document.getElementById("explorer-doc-text");
  if (docViewer) {
    const text = State.activePaperPagesText[State.activePageNum - 1] || State.activePaper?.abstract || "No text available for this page.";
    docViewer.innerText = text;
  }

  const feed = document.getElementById("explorer-eq-feed");
  if (feed) {
    feed.innerHTML = "";
    const pageEqs = State.equations.filter((e) => e.page_number === State.activePageNum);
    if (pageEqs.length === 0) {
      feed.innerHTML = `<p style="color: var(--text-muted); padding: 16px;">No specific equations on this page. Browse previous or next pages.</p>`;
    } else {
      pageEqs.forEach((eq) => feed.appendChild(createEquationCardElement(eq)));
      renderMath(feed);
    }
  }
}

function prevPage() {
  if (State.activePageNum > 1) {
    State.activePageNum--;
    renderExplorerView();
  }
}

function nextPage() {
  const maxPages = State.activePaper ? State.activePaper.total_pages : 1;
  if (State.activePageNum < maxPages) {
    State.activePageNum++;
    renderExplorerView();
  }
}

// --- 11. Interactive Equation Playground ---
const PLAYGROUND_CANONICAL = {
  einstein: {
    title: "Einstein's Mass-Energy Equivalence",
    latex: "E = m c^2",
    primaryX: "m",
    depVar: "E",
    params: { m: 1.0, c: 299792458.0 },
    sliders: [
      { key: "m", label: "Mass (m)", min: 0.01, max: 50.0, step: 0.1, unit: "kg" }
    ],
    constants: [{ key: "c", label: "Speed of Light (c)", val: "299,792,458 m/s" }]
  },
  newton: {
    title: "Newton's Second Law of Motion",
    latex: "F = m a",
    primaryX: "a",
    depVar: "F",
    params: { m: 10.0, a: 9.81 },
    sliders: [
      { key: "m", label: "Mass (m)", min: 0.1, max: 100.0, step: 0.5, unit: "kg" },
      { key: "a", label: "Acceleration (a)", min: -50.0, max: 50.0, step: 0.5, unit: "m/s²" }
    ]
  },
  harmonic: {
    title: "Simple Harmonic Motion",
    latex: "x = A \\cos(\\omega t + \\phi)",
    primaryX: "t",
    depVar: "x",
    isHarmonic: true,
    params: { A: 2.0, omega: 2.0, phi: 0.0, t_max: 10.0 },
    sliders: [
      { key: "A", label: "Amplitude (A)", min: 0.1, max: 10.0, step: 0.1, unit: "m" },
      { key: "omega", label: "Angular Frequency (ω)", min: 0.1, max: 15.0, step: 0.1, unit: "rad/s" },
      { key: "phi", label: "Phase Angle (φ)", min: -3.14, max: 3.14, step: 0.1, unit: "rad" },
      { key: "t_max", label: "Time Span", min: 2.0, max: 30.0, step: 1.0, unit: "s" }
    ]
  },
  gaussian: {
    title: "Gaussian Normal Distribution",
    latex: "f = \\frac{1}{\\sigma \\sqrt{2 \\pi}} \\exp\\left(-\\frac{(x - \\mu)^2}{2 \\sigma^2}\\right)",
    primaryX: "x",
    depVar: "f",
    isGaussian: true,
    params: { mu: 0.0, sigma: 1.0, span: 4.0 },
    sliders: [
      { key: "mu", label: "Mean (μ)", min: -10.0, max: 10.0, step: 0.2, unit: "" },
      { key: "sigma", label: "Std Deviation (σ)", min: 0.1, max: 6.0, step: 0.1, unit: "" }
    ]
  },
  gravitation: {
    title: "Newton's Universal Gravitation",
    latex: "F = G \\frac{m_1 m_2}{r^2}",
    primaryX: "r",
    depVar: "F",
    params: { m_1: 50000.0, m_2: 1000.0, r: 20.0, G: 6.6743e-11 },
    sliders: [
      { key: "m_1", label: "Mass 1 (m₁)", min: 100.0, max: 100000.0, step: 500.0, unit: "kg" },
      { key: "m_2", label: "Mass 2 (m₂)", min: 100.0, max: 10000.0, step: 100.0, unit: "kg" },
      { key: "r", label: "Separation Radius (r)", min: 2.0, max: 200.0, step: 1.0, unit: "m" }
    ],
    constants: [{ key: "G", label: "Gravitational Constant (G)", val: "6.6743 × 10⁻¹¹ N m²/kg²" }]
  }
};

function initPlaygroundView() {
  const modelSelect = document.getElementById("playground-model-select");
  if (!modelSelect) return;

  modelSelect.onchange = (e) => {
    loadPlaygroundModel(e.target.value);
  };

  loadPlaygroundModel(modelSelect.value || "einstein");
}

function loadPlaygroundModel(key) {
  const model = PLAYGROUND_CANONICAL[key] || PLAYGROUND_CANONICAL.einstein;
  State.playground.model = key;
  State.playground.latex = model.latex;
  State.playground.params = { ...model.params };
  State.playground.primaryX = model.primaryX;
  State.playground.depVar = model.depVar;

  document.getElementById("playground-eq-title").innerText = model.title;
  const eqBox = document.getElementById("playground-latex");
  eqBox.innerHTML = `$$${model.latex}$$`;
  renderMath(eqBox);

  // Generate Sliders UI
  const controls = document.getElementById("playground-sliders");
  controls.innerHTML = "";

  (model.sliders || []).forEach((s) => {
    const val = State.playground.params[s.key];
    const grp = document.createElement("div");
    grp.className = "slider-group";
    grp.innerHTML = `
      <div class="slider-header">
        <span>${s.label}</span>
        <span id="slider-val-${s.key}" style="color: var(--cyan-primary); font-family: var(--font-mono);">${val} ${s.unit}</span>
      </div>
      <input type="range" class="slider-input" min="${s.min}" max="${s.max}" step="${s.step}" value="${val}"
        oninput="updatePlaygroundParam('${s.key}', this.value, '${s.unit}')">
    `;
    controls.appendChild(grp);
  });

  renderPlaygroundChart();
}

function updatePlaygroundParam(key, val, unit) {
  const fval = parseFloat(val);
  State.playground.params[key] = fval;
  const numSpan = document.getElementById(`slider-val-${key}`);
  if (numSpan) numSpan.innerText = `${fval} ${unit}`;
  renderPlaygroundChart();
}

async function renderPlaygroundChart() {
  const key = State.playground.model;
  const isDark = State.theme === "dark";
  const paperBg = isDark ? "#0A0E1A" : "#FFFFFF";
  const plotBg = isDark ? "#0D1322" : "#F8FAFC";
  const gridColor = isDark ? "#1E293B" : "#E2E8F0";
  const textColor = isDark ? "#F8FAFC" : "#0F172A";

  const chartDiv = document.getElementById("playground-plot");
  if (!chartDiv) return;

  if (key === "harmonic") {
    const A = State.playground.params.A;
    const w = State.playground.params.omega;
    const phi = State.playground.params.phi;
    const tMax = State.playground.params.t_max || 10.0;

    const t = [];
    const x = [];
    const v = [];
    for (let time = 0; time <= tMax; time += tMax / 300) {
      t.push(time);
      x.push(A * Math.cos(w * time + phi));
      v.push(-A * w * Math.sin(w * time + phi));
    }

    const traceX = { x: t, y: x, name: "Displacement x(t) [m]", line: { color: "#00E5FF", width: 2.5 } };
    const traceV = { x: t, y: v, name: "Velocity v(t) [m/s]", line: { color: "#10B981", width: 2, dash: "dot" } };

    const layout = {
      title: { text: "Simple Harmonic Motion: x(t) & v(t)", font: { color: textColor } },
      paper_bgcolor: paperBg,
      plot_bgcolor: plotBg,
      xaxis: { title: "Time (t) [s]", gridcolor: gridColor },
      yaxis: { title: "Response", gridcolor: gridColor },
      legend: { font: { color: textColor } },
      margin: { l: 50, r: 40, t: 50, b: 50 }
    };

    Plotly.newPlot(chartDiv, [traceX, traceV], layout, { responsive: true, displayModeBar: false });

    // Live readout
    const currX = A * Math.cos(phi);
    document.getElementById("playground-live-val").innerText = `${currX.toFixed(3)} m (at t=0)`;
    return;
  }

  if (key === "gaussian") {
    const mu = State.playground.params.mu;
    const sigma = State.playground.params.sigma;

    const x = [];
    const y = [];
    const xMin = mu - 4 * sigma;
    const xMax = mu + 4 * sigma;
    for (let step = xMin; step <= xMax; step += (xMax - xMin) / 300) {
      x.push(step);
      const pdf = (1 / (sigma * Math.sqrt(2 * Math.PI))) * Math.exp(-Math.pow(step - mu, 2) / (2 * Math.pow(sigma, 2)));
      y.push(pdf);
    }

    const trace = {
      x, y,
      type: "scatter",
      mode: "lines",
      fill: "tozeroy",
      fillcolor: isDark ? "rgba(0, 229, 255, 0.15)" : "rgba(2, 132, 199, 0.15)",
      line: { color: "#00E5FF", width: 2.5 },
      name: "f(x) Density"
    };

    const layout = {
      title: { text: `Gaussian Normal Distribution (μ=${mu}, σ=${sigma})`, font: { color: textColor } },
      paper_bgcolor: paperBg,
      plot_bgcolor: plotBg,
      xaxis: { title: "Variable x", gridcolor: gridColor },
      yaxis: { title: "Probability Density", gridcolor: gridColor },
      margin: { l: 50, r: 40, t: 50, b: 50 }
    };

    Plotly.newPlot(chartDiv, [trace], layout, { responsive: true, displayModeBar: false });
    const peak = 1 / (sigma * Math.sqrt(2 * Math.PI));
    document.getElementById("playground-live-val").innerText = `${peak.toFixed(4)} (Peak Density)`;
    return;
  }

  // Generalized Numerical Engine call
  try {
    const payload = {
      latex: State.playground.latex,
      independent_var: State.playground.primaryX,
      min_val: 0.1,
      max_val: 50.0,
      fixed_params: State.playground.params,
      target_dep_var: State.playground.depVar
    };
    const res = await API.evaluatePlaygroundGrid(payload);
    if (res.success) {
      const trace = {
        x: res.x,
        y: res.y,
        mode: "lines",
        name: `${State.playground.depVar}(${State.playground.primaryX})`,
        line: { color: "#00E5FF", width: 2.8 }
      };

      const layout = {
        title: { text: `${State.playground.depVar} vs ${State.playground.primaryX}`, font: { color: textColor } },
        paper_bgcolor: paperBg,
        plot_bgcolor: plotBg,
        xaxis: { title: State.playground.primaryX, gridcolor: gridColor },
        yaxis: { title: State.playground.depVar, gridcolor: gridColor },
        margin: { l: 50, r: 40, t: 50, b: 50 }
      };

      Plotly.newPlot(chartDiv, [trace], layout, { responsive: true, displayModeBar: false });
      const opY = res.operating_point_y;
      document.getElementById("playground-live-val").innerText = opY !== null && opY !== undefined ? opY.toExponential(4) : "Evaluated";
    }
  } catch (err) {
    console.warn("Playground evaluation warning:", err);
  }
}

function openEquationInPlayground(eqId) {
  const eq = State.equations.find((e) => e.id === eqId);
  if (!eq) return;
  switchView("playground");
  State.playground.latex = eq.latex;
  State.playground.model = "custom";
  State.playground.primaryX = eq.variables.find((v) => v.var_type === "Variable")?.symbol || "x";
  State.playground.depVar = eq.variables.find((v) => v.var_type === "Dependent quantity")?.symbol || "y";

  document.getElementById("playground-eq-title").innerText = `${eq.eq_id}: ${eq.section_title}`;
  const eqBox = document.getElementById("playground-latex");
  eqBox.innerHTML = `$$${eq.latex}$$`;
  renderMath(eqBox);

  // Build parameter sliders
  const controls = document.getElementById("playground-sliders");
  controls.innerHTML = "";
  State.playground.params = {};

  eq.variables.forEach((v) => {
    if (v.is_constant) {
      State.playground.params[v.symbol] = v.default_val || 1.0;
    } else {
      const val = v.default_val || 1.0;
      State.playground.params[v.symbol] = val;
      const grp = document.createElement("div");
      grp.className = "slider-group";
      grp.innerHTML = `
        <div class="slider-header">
          <span>${v.meaning} (${v.symbol})</span>
          <span id="slider-val-${v.symbol}" style="color: var(--cyan-primary); font-family: var(--font-mono);">${val} ${v.unit || ''}</span>
        </div>
        <input type="range" class="slider-input" min="${v.min_val || 0.1}" max="${v.max_val || 50}" step="0.5" value="${val}"
          oninput="updatePlaygroundParam('${v.symbol}', this.value, '${v.unit || ''}')">
      `;
      controls.appendChild(grp);
    }
  });

  renderPlaygroundChart();
}

// --- 12. AI Deconstruction Modal ---
async function openDeconstructModal(eqId) {
  const eq = State.equations.find((e) => e.id === eqId);
  if (!eq) return;

  const modal = document.getElementById("deconstruct-modal");
  const body = document.getElementById("deconstruct-modal-body");
  modal.classList.add("open");
  body.innerHTML = `<div style="text-align: center; padding: 40px;"><p>Analyzing mathematical structure & physical meaning...</p></div>`;

  try {
    const res = await API.deconstructEquation(eqId);
    const expl = res.explanation;
    const math = expl.mathematical_interpretation || {};

    let varsHtml = "";
    (expl.variable_breakdown || eq.variables || []).forEach((v) => {
      varsHtml += `<tr><td><span class="var-symbol">${v.symbol}</span></td><td>${v.meaning}</td><td>${v.unit || 'unspecified'}</td><td>${v.type || v.var_type || 'Variable'}</td></tr>`;
    });

    let appsHtml = "";
    (expl.applications || []).forEach((a) => {
      appsHtml += `<li>${a}</li>`;
    });

    let limsHtml = "";
    (expl.limitations || []).forEach((l) => {
      limsHtml += `<li>⚠️ ${l}</li>`;
    });

    body.innerHTML = `
      <div class="eq-header">
        <span class="thesisflow-badge">${eq.eq_id}</span>
        <span style="font-weight: 700; font-size: 1.1rem;">${eq.section_title}</span>
      </div>
      <div class="eq-latex-box">$$${eq.latex}$$</div>
      <h4 style="margin: 16px 0 6px 0; color: var(--cyan-primary);">Plain-Language Explanation</h4>
      <p style="color: var(--text-secondary); line-height: 1.6;">${expl.plain_language_explanation || ''}</p>
      
      <h4 style="margin: 20px 0 6px 0; color: var(--cyan-primary);">Mathematical Interpretation</h4>
      <p><b>Structure:</b> ${math.structure || 'Algebraic formulation'}</p>
      <p><b>Variable Interactions:</b> ${math.relationships || 'Coupled state scaling'}</p>
      <p><b>Core Assumptions:</b> ${math.assumptions || 'Continuum approximation'}</p>
      
      <h4 style="margin: 20px 0 6px 0; color: var(--cyan-primary);">Variable Breakdown</h4>
      <table class="modern-table">
        <thead><tr><th>Symbol</th><th>Meaning</th><th>Unit</th><th>Type</th></tr></thead>
        <tbody>${varsHtml}</tbody>
      </table>

      <h4 style="margin: 20px 0 6px 0; color: var(--cyan-primary);">Physical Intuition</h4>
      <p style="color: var(--text-secondary);">${expl.physical_intuition || ''}</p>
      <ul style="margin-left: 20px; color: var(--text-secondary);">${appsHtml}</ul>

      <h4 style="margin: 20px 0 6px 0; color: var(--cyan-primary);">Limitations & Validity Bounds</h4>
      <ul style="margin-left: 20px; color: var(--rose-primary);">${limsHtml}</ul>
    `;
    renderMath(body);
  } catch (err) {
    body.innerHTML = `<p style="color: var(--rose-primary);">Error generating deconstruction: ${err.message}</p>`;
  }
}

// --- 13. Python Code Generator Modal ---
async function openCodeModal(eqId) {
  const eq = State.equations.find((e) => e.id === eqId);
  if (!eq) return;

  const modal = document.getElementById("code-modal");
  const body = document.getElementById("code-modal-body");
  modal.classList.add("open");
  body.innerHTML = `<div style="text-align: center; padding: 40px;"><p>Generating production Python & NumPy suites...</p></div>`;

  try {
    const depVar = eq.variables.find((v) => v.var_type === "Dependent quantity")?.symbol || "y";
    const indepVars = eq.variables.filter((v) => v.var_type !== "Constant").map((v) => v.symbol);
    const res = await API.getCodeSuite(eq.latex, depVar, indepVars, `${eq.eq_id}_${eq.section_title}`);
    const code = res.code;

    body.innerHTML = `
      <div class="eq-header">
        <span class="thesisflow-badge">${eq.eq_id}</span>
        <span style="font-weight: 700;">Executable Code Suite</span>
      </div>
      <div style="display: flex; gap: 8px; margin: 12px 0;">
        <button class="btn btn-glass btn-sm active" onclick="switchCodeTab('pure', this)">Pure Python</button>
        <button class="btn btn-glass btn-sm" onclick="switchCodeTab('numpy', this)">NumPy Vectorized</button>
        <button class="btn btn-glass btn-sm" onclick="switchCodeTab('sympy', this)">SymPy Symbolic</button>
        <button class="btn btn-glass btn-sm" onclick="switchCodeTab('plotly', this)">Plotly Script</button>
      </div>
      <pre id="code-display" style="background: var(--input-bg); padding: 18px; border-radius: 8px; border: 1px solid var(--glass-border); overflow-x: auto; font-family: var(--font-mono); font-size: 0.85rem;"><code class="language-python">${escapeHtml(code.pure_python)}</code></pre>
      <div style="display: flex; gap: 10px; margin-top: 14px;">
        <button class="btn btn-primary btn-sm" onclick="copyCurrentCode()">📋 Copy Code</button>
      </div>
    `;
    window.currentCodeSuite = code;
  } catch (err) {
    body.innerHTML = `<p style="color: var(--rose-primary);">Error: ${err.message}</p>`;
  }
}

function switchCodeTab(type, btn) {
  document.querySelectorAll("#code-modal .btn-sm").forEach((b) => b.classList.remove("active"));
  btn.classList.add("active");
  const pre = document.getElementById("code-display");
  const code = window.currentCodeSuite[type === "pure" ? "pure_python" : type];
  pre.innerHTML = `<code class="language-python">${escapeHtml(code)}</code>`;
}

function copyCurrentCode() {
  const pre = document.getElementById("code-display");
  if (pre) {
    navigator.clipboard.writeText(pre.innerText);
    showToast("Code copied to clipboard!", "success");
  }
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function closeModal(modalId) {
  document.getElementById(modalId)?.classList.remove("open");
}

// --- 14. Grounded AI Research Assistant ---
function renderAssistantView() {
  const paperTitleSpan = document.getElementById("chat-paper-title");
  if (paperTitleSpan) {
    paperTitleSpan.innerText = State.activePaper ? State.activePaper.title : "No Active Paper";
  }
}

async function sendChatMessage() {
  const input = document.getElementById("chat-input-field");
  const query = input.value.trim();
  if (!query) return;

  input.value = "";
  const historyDiv = document.getElementById("chat-history-container");

  // Append user bubble
  const userBubble = document.createElement("div");
  userBubble.className = "chat-bubble user";
  userBubble.innerText = query;
  historyDiv.appendChild(userBubble);
  historyDiv.scrollTop = historyDiv.scrollHeight;

  // Append loading assistant bubble
  const botBubble = document.createElement("div");
  botBubble.className = "chat-bubble assistant";
  botBubble.innerHTML = `<em>Reasoning with grounded citations...</em>`;
  historyDiv.appendChild(botBubble);
  historyDiv.scrollTop = historyDiv.scrollHeight;

  try {
    const res = await API.sendChat(query);
    let citationsHtml = "";
    (res.citations || []).forEach((c) => {
      citationsHtml += `<span class="citation-badge">Page ${c.page}: ${c.section}</span>`;
    });

    botBubble.innerHTML = `
      <div>${res.response.replace(/\n/g, '<br>')}</div>
      ${citationsHtml ? `<div style="margin-top: 10px; border-top: 1px solid var(--glass-border); padding-top: 8px;"><small style="color: var(--text-muted);">Verified Citations:</small><br>${citationsHtml}</div>` : ''}
    `;
    renderMath(botBubble);
  } catch (err) {
    botBubble.innerHTML = `<span style="color: var(--rose-primary);">Error: ${err.message}</span>`;
  }
  historyDiv.scrollTop = historyDiv.scrollHeight;
}

// --- 15. Constants Explorer ---
async function renderConstantsView() {
  const container = document.getElementById("constants-grid");
  if (!container) return;
  container.innerHTML = `<p>Loading physical constants...</p>`;

  try {
    const consts = await API.getConstants();
    container.innerHTML = "";
    consts.forEach((c) => {
      const card = document.createElement("div");
      card.className = "glass-panel";
      card.style.padding = "18px";
      card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
          <div>
            <span class="thesisflow-badge badge-purple">${c.category}</span>
            <h4 style="margin: 6px 0 2px 0;">${c.name}</h4>
            <div style="color: var(--cyan-primary); font-family: var(--font-mono); font-weight: 700;">${c.symbol}</div>
          </div>
          <div style="text-align: right;">
            <div style="font-weight: 700; font-family: var(--font-mono);">${c.value_display}</div>
            <div style="font-size: 0.76rem; color: var(--text-muted);">${c.unit}</div>
          </div>
        </div>
        <p style="font-size: 0.85rem; color: var(--text-secondary); margin: 8px 0;">${c.meaning}</p>
        <div class="eq-latex-box" style="padding: 10px; font-size: 1rem;">$$${c.canonical_equation}$$</div>
        <div style="font-size: 0.74rem; color: var(--text-muted); border-top: 1px solid var(--glass-border); padding-top: 8px;">
          ${c.reference}
        </div>
      `;
      container.appendChild(card);
    });
    renderMath(container);
  } catch (err) {
    container.innerHTML = `<p style="color: var(--rose-primary);">Error loading constants: ${err.message}</p>`;
  }
}

// --- 16. Research Library View ---
async function renderLibraryView() {
  const container = document.getElementById("library-cards-container");
  if (!container) return;

  const papers = await API.getPapers();
  container.innerHTML = "";
  papers.forEach((p) => {
    const isAct = p.id === State.activePaperId;
    const card = document.createElement("div");
    card.className = `glass-panel ${isAct ? 'glow-cyan' : ''}`;
    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start;">
        <div>
          <h3 style="margin-bottom: 4px;">${p.title}</h3>
          <p style="color: var(--cyan-primary); font-size: 0.86rem;">Authors: ${p.authors}</p>
        </div>
        <div>
          ${isAct ? '<span class="thesisflow-badge badge-emerald">Active Selection</span>' : ''}
        </div>
      </div>
      <p style="color: var(--text-secondary); font-size: 0.88rem; margin: 12px 0;">${p.abstract ? p.abstract.substring(0, 240) + '...' : ''}</p>
      <div style="display: flex; gap: 16px; font-size: 0.8rem; color: var(--text-muted); margin-bottom: 14px;">
        <span>📄 <b>${p.total_pages}</b> Pages</span>
        <span>∑ <b>${p.equations_count}</b> Equations</span>
        <span>📅 ${p.uploaded_at.substring(0, 10)}</span>
      </div>
      <div style="display: flex; gap: 10px;">
        <button class="btn btn-primary btn-sm" onclick="loadPaperContext(${p.id}); switchView('explorer');">📖 Open in Explorer</button>
        <a class="btn btn-glass btn-sm" href="/api/reports/paper/${p.id}/pdf" target="_blank">📥 Export PDF</a>
        <a class="btn btn-glass btn-sm" href="/api/reports/paper/${p.id}/markdown" target="_blank">📝 Markdown</a>
        <button class="btn btn-glass btn-sm" style="color: var(--rose-primary);" onclick="deletePaperItem(${p.id})">🗑️ Delete</button>
      </div>
    `;
    container.appendChild(card);
  });
}

async function deletePaperItem(id) {
  if (confirm("Delete this research paper from your library?")) {
    await API.deletePaper(id);
    showToast("Paper deleted.", "info");
    if (State.activePaperId === id) State.activePaperId = null;
    await refreshDashboard();
    renderLibraryView();
  }
}

// --- 17. Equation Comparison View ---
async function renderComparisonView() {
  const selA = document.getElementById("compare-eq-a");
  const selB = document.getElementById("compare-eq-b");
  if (!selA || !selB) return;

  selA.innerHTML = "";
  selB.innerHTML = "";

  State.equations.forEach((eq, idx) => {
    const optA = document.createElement("option");
    optA.value = eq.id;
    optA.innerText = `[${eq.eq_id}] ${eq.latex.substring(0, 30)}`;
    if (idx === 0) optA.selected = true;
    selA.appendChild(optA);

    const optB = document.createElement("option");
    optB.value = eq.id;
    optB.innerText = `[${eq.eq_id}] ${eq.latex.substring(0, 30)}`;
    if (idx === 1 || (idx === 0 && State.equations.length === 1)) optB.selected = true;
    selB.appendChild(optB);
  });

  updateComparisonDetails();
  selA.onchange = updateComparisonDetails;
  selB.onchange = updateComparisonDetails;
}

function updateComparisonDetails() {
  const selA = document.getElementById("compare-eq-a");
  const selB = document.getElementById("compare-eq-b");
  if (!selA || !selB) return;

  const eqA = State.equations.find((e) => e.id === parseInt(selA.value));
  const eqB = State.equations.find((e) => e.id === parseInt(selB.value));
  if (!eqA || !eqB) return;

  document.getElementById("compare-latex-a").innerHTML = `$$${eqA.latex}$$`;
  document.getElementById("compare-latex-b").innerHTML = `$$${eqB.latex}$$`;
  renderMath(document.getElementById("view-comparison"));

  // Analyze variable sets
  const symsA = new Set(eqA.variables.map((v) => v.symbol));
  const symsB = new Set(eqB.variables.map((v) => v.symbol));

  const shared = [...symsA].filter((x) => symsB.has(x));
  const uniqueA = [...symsA].filter((x) => !symsB.has(x));
  const uniqueB = [...symsB].filter((x) => !symsA.has(x));

  document.getElementById("compare-shared-vars").innerText = shared.length > 0 ? shared.join(", ") : "None";
  document.getElementById("compare-unique-a").innerText = uniqueA.length > 0 ? uniqueA.join(", ") : "None";
  document.getElementById("compare-unique-b").innerText = uniqueB.length > 0 ? uniqueB.join(", ") : "None";
}

// --- 18. Initialize on Page Load ---
window.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initNavigation();
  initUploadHandler();
  refreshDashboard();
});
