/**
 * DocuGen AI - Frontend Client Architecture
 * Handles file uploads, AST analysis data binding, Markdown preview, and navigation.
 */

// Global State
const state = {
  currentFileId: null,
  currentFileName: null,
  filesList: [],
  analysisResult: null,
  docContent: null,
};

// Built-in Sample Code for 1-Click Instant Testing
const BUILTIN_SAMPLE_PY = `\"\"\"
DocuGen Sample Module: Advanced Data Processing Engine
Demonstrates comprehensive Python language constructs for AST static analysis.
\"\"\"

import math
from typing import List, Dict, Optional, Any
from pathlib import Path
import logging

MODULE_VERSION: str = "2.4.0"
DEFAULT_TIMEOUT: float = 30.0
MAX_BATCH_SIZE: int = 500
GLOBAL_CACHE: Dict[str, Any] = {}

class BaseEntity:
    \"\"\"Base entity providing identification and state tracking.\"\"\"

    def __init__(self, entity_id: str, name: str) -> None:
        \"\"\"Initialize base entity with unique identifier.\"\"\"
        self.entity_id = entity_id
        self.name = name
        self.is_active = True

    def get_display_name(self) -> str:
        \"\"\"Return formatted display name.\"\"\"
        return f"[{self.entity_id}] {self.name}"

    def deactivate(self) -> bool:
        \"\"\"Deactivate entity.\"\"\"
        self.is_active = False
        return self.is_active

class DataPipeline(BaseEntity):
    \"\"\"Data pipeline orchestrator capable of staging and batching data records.\"\"\"

    class MetricsTracker:
        \"\"\"Nested tracker for metrics.\"\"\"
        def __init__(self) -> None:
            self.total_processed: int = 0

    def __init__(self, pipeline_id: str, name: str, buffer_size: int = 100) -> None:
        super().__init__(entity_id=pipeline_id, name=name)
        self.buffer_size = buffer_size
        self.records: List[Dict[str, Any]] = []

    def add_record(self, record: Dict[str, Any]) -> int:
        \"\"\"Add record to buffer and return count.\"\"\"
        self.records.append(record)
        return len(self.records)

    def compute_summary_statistics(self, key: str) -> Dict[str, float]:
        \"\"\"Calculate average and maximum values.\"\"\"
        values = [r[key] for r in self.records if key in r and isinstance(r[key], (int, float))]
        if not values:
            return {"count": 0.0, "average": 0.0, "max": 0.0}
        return {"count": float(len(values)), "average": sum(values) / len(values), "max": float(max(values))}

def calculate_statistical_variance(numbers: List[float], /, sample: bool = True, *, precision: int = 4) -> float:
    \"\"\"Calculate variance of a sequence of floating-point numbers.\"\"\"
    if len(numbers) < 2:
        return 0.0
    mean_val = sum(numbers) / len(numbers)
    denom = len(numbers) - 1 if sample else len(numbers)
    return round(sum((x - mean_val) ** 2 for x in numbers) / denom, precision)

async def fetch_remote_metrics(endpoint: str, timeout: float = DEFAULT_TIMEOUT, *tags: str, **params: Any) -> Dict[str, Any]:
    \"\"\"Asynchronously fetch remote metrics.\"\"\"
    def sanitize(t: str) -> str:
        return t.strip().lower()
    return {"status": 200, "endpoint": endpoint, "tags": [sanitize(t) for t in tags], "params": params}
`;

// Helper: Toast Notifications
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  
  let icon = "ℹ️";
  if (type === "success") icon = "✅";
  if (type === "error") icon = "❌";

  toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Helper: Escape HTML
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Helper: Simple Markdown to HTML Renderer
function renderMarkdown(md) {
  if (!md) return "<p>No documentation generated yet.</p>";

  // Handle headers
  let html = md
    .replace(/^# (.*$)/gim, '<h1 class="mt-4 mb-3">$1</h1>')
    .replace(/^## (.*$)/gim, '<h2 class="mt-4 mb-3 border-bottom pb-2">$1</h2>')
    .replace(/^### (.*$)/gim, '<h3 class="mt-3 mb-2 text-primary">$1</h3>')
    .replace(/^#### (.*$)/gim, '<h4 class="mt-2 mb-2">$1</h4>');

  // Handle blockquotes
  html = html.replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>');

  // Handle bold and italic
  html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/gim, '<em>$1</em>');

  // Handle code blocks
  html = html.replace(/```([a-z]*)\n([\s\S]*?)```/gim, '<pre><code>$2</code></pre>');

  // Handle inline code
  html = html.replace(/`([^`]+)`/gim, '<code>$1</code>');

  // Handle horizontal rules
  html = html.replace(/^---$/gim, '<hr class="my-4"/>');

  // Handle simple markdown tables
  html = html.replace(/\|(.+)\|/gim, (match) => {
    const cells = match.split('|').filter(c => c.trim() !== '');
    if (cells.some(c => c.includes('---'))) {
      return ''; // Header separator line
    }
    const tdCells = cells.map(c => `<td>${c.trim()}</td>`).join('');
    return `<tr>${tdCells}</tr>`;
  });

  // Wrap table rows in table element
  html = html.replace(/(<tr>[\s\S]*?<\/tr>)+/gim, (match) => {
    return `<div class="table-responsive my-3"><table class="custom-table">${match}</table></div>`;
  });

  // Handle paragraphs and line breaks
  html = html.replace(/\n\n/gim, '<br/><br/>');

  return html;
}

// Navigation View Switcher
function switchView(viewName) {
  // Update sidebar active link
  document.querySelectorAll(".nav-item").forEach(item => {
    item.classList.toggle("active", item.getAttribute("data-view") === viewName);
  });

  // Toggle visible section
  document.querySelectorAll(".view-section").forEach(sec => {
    sec.classList.remove("active");
  });

  const targetSec = document.getElementById(`view-${viewName}`);
  if (targetSec) {
    targetSec.classList.add("active");
  }

  // View-specific initialization
  if (viewName === "dashboard") {
    loadFilesList();
  } else if (viewName === "download") {
    renderDownloadView();
  }
}

// Check Health Status
async function checkHealth() {
  try {
    const res = await fetch("/api/health");
    if (res.ok) {
      const data = await res.json();
      const badge = document.getElementById("header-health-badge");
      if (badge) {
        badge.innerHTML = `
          <span class="status-dot"></span>
          <span>FastAPI Online ${data.ai_enabled ? '• AI Ready' : '• AST Ready'}</span>
        `;
      }
    }
  } catch (e) {
    console.warn("Health check error:", e);
  }
}

// Load List of Files
async function loadFilesList() {
  try {
    const res = await fetch("/api/files");
    if (!res.ok) throw new Error("Failed to load files");
    const files = await res.json();
    state.filesList = files;
    renderFilesTable(files);
    updateDashboardStats(files);
  } catch (e) {
    console.error("Error loading files list:", e);
  }
}

// Update Top Dashboard Counter Cards
function updateDashboardStats(files) {
  const totalFilesElem = document.getElementById("stat-total-files");
  const totalLinesElem = document.getElementById("stat-total-lines");
  const totalFuncsElem = document.getElementById("stat-total-funcs");
  const totalClassesElem = document.getElementById("stat-total-classes");

  if (!totalFilesElem) return;

  totalFilesElem.textContent = files.length;

  let totalLines = 0;
  let totalFuncs = 0;
  let totalClasses = 0;

  files.forEach(f => {
    if (f.metrics) {
      totalLines += f.metrics.total_lines || 0;
      totalFuncs += f.metrics.total_functions || 0;
      totalClasses += f.metrics.total_classes || 0;
    }
  });

  if (totalLinesElem) totalLinesElem.textContent = totalLines.toLocaleString();
  if (totalFuncsElem) totalFuncsElem.textContent = totalFuncs.toLocaleString();
  if (totalClassesElem) totalClassesElem.textContent = totalClasses.toLocaleString();
}

// Render Dashboard Files Table
function renderFilesTable(files) {
  const tbody = document.getElementById("files-table-body");
  if (!tbody) return;

  if (files.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="text-center py-4 text-muted">
          No Python files uploaded yet. Click <strong>Upload Python File</strong> or <strong>Try Sample File</strong> above.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = files.map(file => {
    const statusBadge = file.is_analyzed
      ? `<span class="badge badge-success"><i class="bi bi-check-circle"></i> Analyzed</span>`
      : `<span class="badge badge-secondary"><i class="bi bi-clock"></i> Uploaded</span>`;

    return `
      <tr>
        <td>
          <div class="d-flex align-items-center gap-2">
            <span class="text-primary fs-5"><i class="bi bi-filetype-py"></i></span>
            <strong>${escapeHtml(file.filename)}</strong>
          </div>
        </td>
        <td>${escapeHtml(file.file_size_formatted)}</td>
        <td>${escapeHtml(file.uploaded_at)}</td>
        <td>${statusBadge}</td>
        <td>
          <div class="d-flex gap-1">
            <button class="btn btn-outline btn-sm" onclick="analyzeAndDisplay('${file.file_id}')" title="Analyze File">
              <i class="bi bi-play-fill text-primary"></i> Analyze
            </button>
            ${file.has_doc ? `
              <button class="btn btn-outline btn-sm" onclick="viewDocs('${file.file_id}')" title="View Docs">
                <i class="bi bi-file-earmark-text"></i> Docs
              </button>
              <a href="/api/download/${file.file_id}" class="btn btn-outline btn-sm" title="Download .md">
                <i class="bi bi-download"></i>
              </a>
            ` : ''}
            <button class="btn btn-danger-outline btn-sm" onclick="deleteFileRecord('${file.file_id}')" title="Delete">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join("");
}

// Delete File Record
async function deleteFileRecord(fileId) {
  if (!confirm("Are you sure you want to delete this file and its generated documentation?")) return;
  try {
    const res = await fetch(`/api/files/${fileId}`, { method: "DELETE" });
    if (!res.ok) throw new Error("Failed to delete file");
    showToast("File deleted successfully", "success");
    loadFilesList();
    if (state.currentFileId === fileId) {
      state.currentFileId = null;
      state.analysisResult = null;
      state.docContent = null;
    }
  } catch (e) {
    showToast(e.message, "error");
  }
}

// Upload File Pipeline
async function handleFileUpload(file) {
  if (!file) return;

  // Validation
  if (!file.name.endsWith(".py")) {
    showToast("Invalid file extension. Please select a .py file.", "error");
    return;
  }
  if (file.size === 0) {
    showToast("Uploaded file is empty (0 bytes).", "error");
    return;
  }
  if (file.size > 5 * 1024 * 1024) {
    showToast("File size exceeds 5MB limit.", "error");
    return;
  }

  const progressCard = document.getElementById("upload-progress-card");
  const progressText = document.getElementById("upload-progress-text");
  const progressSubtext = document.getElementById("upload-progress-subtext");
  const previewCard = document.getElementById("upload-preview-card");

  if (previewCard) previewCard.style.display = "none";
  if (progressCard) progressCard.style.display = "block";

  try {
    // Step 1: Upload
    if (progressText) progressText.textContent = "Uploading Python source file...";
    if (progressSubtext) progressSubtext.textContent = `Validating ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;

    const formData = new FormData();
    formData.append("file", file);

    const uploadRes = await fetch("/api/upload", {
      method: "POST",
      body: formData,
    });

    if (!uploadRes.ok) {
      const err = await uploadRes.json();
      throw new Error(err.detail || "Upload failed");
    }

    const uploadData = await uploadRes.json();
    const fileId = uploadData.file_id;
    state.currentFileId = fileId;
    state.currentFileName = uploadData.filename;

    // Step 2: Analyze AST
    if (progressText) progressText.textContent = "Analyzing Abstract Syntax Tree...";
    if (progressSubtext) progressSubtext.textContent = "Extracting functions, classes, types, and generating explanations...";

    const analyzeRes = await fetch(`/api/analyze/${fileId}`, { method: "POST" });
    if (!analyzeRes.ok) {
      const err = await analyzeRes.json();
      throw new Error(err.detail || "Analysis failed");
    }

    const analysisData = await analyzeRes.json();
    state.analysisResult = analysisData;

    showToast(`Successfully analyzed ${uploadData.filename}!`, "success");
    if (progressCard) progressCard.style.display = "none";

    // Switch to Analysis View & Render
    renderAnalysisView(analysisData);
    switchView("analysis");
    loadFilesList();

  } catch (err) {
    if (progressCard) progressCard.style.display = "none";
    showToast(err.message, "error");
  }
}

// 1-Click Builtin Sample Loader
function loadSampleFile() {
  const blob = new Blob([BUILTIN_SAMPLE_PY], { type: "text/x-python" });
  const sampleFile = new File([blob], "sample_pipeline.py", { type: "text/x-python" });
  handleFileUpload(sampleFile);
}

// Trigger Analysis on Existing File
async function analyzeAndDisplay(fileId) {
  try {
    showToast("Analyzing file...", "info");
    const res = await fetch(`/api/analyze/${fileId}`, { method: "POST" });
    if (!res.ok) throw new Error("Analysis failed");
    const data = await res.json();
    state.currentFileId = fileId;
    state.currentFileName = data.filename;
    state.analysisResult = data;
    renderAnalysisView(data);
    switchView("analysis");
    loadFilesList();
  } catch (e) {
    showToast(e.message, "error");
  }
}

// Render Complete Analysis View
function renderAnalysisView(data) {
  state.analysisResult = data;
  state.currentFileId = data.file_id;
  state.currentFileName = data.filename;

  // Header Title
  const activeFileNameElem = document.getElementById("analysis-file-name");
  if (activeFileNameElem) activeFileNameElem.textContent = data.filename;

  // 4 Top Metric Cards
  const m = data.metrics || {};
  const linesVal = document.getElementById("metric-lines");
  const funcsVal = document.getElementById("metric-funcs");
  const classesVal = document.getElementById("metric-classes");
  const importsVal = document.getElementById("metric-imports");

  if (linesVal) linesVal.textContent = (m.total_lines || 0).toLocaleString();
  if (funcsVal) funcsVal.textContent = (m.total_functions || 0).toLocaleString();
  if (classesVal) classesVal.textContent = (m.total_classes || 0).toLocaleString();
  if (importsVal) importsVal.textContent = (m.total_imports || 0).toLocaleString();

  // Metrics sub-labels
  const linesSub = document.getElementById("metric-lines-sub");
  if (linesSub) linesSub.textContent = `${m.code_lines || 0} code • ${m.comment_lines || 0} comments • ${m.blank_lines || 0} blank`;

  // Syntax Banner
  const syntaxBanner = document.getElementById("analysis-syntax-banner");
  if (syntaxBanner) {
    if (data.syntax && data.syntax.is_valid) {
      syntaxBanner.className = "syntax-banner valid";
      syntaxBanner.innerHTML = `
        <span class="fs-4">✅</span>
        <div>
          <strong>Python Syntax Valid</strong> — Abstract Syntax Tree (AST) parsed and inspected with zero errors.
        </div>
      `;
    } else {
      const err = data.syntax || {};
      syntaxBanner.className = "syntax-banner invalid";
      syntaxBanner.innerHTML = `
        <span class="fs-4">❌</span>
        <div>
          <strong>Syntax Error Detected at Line ${err.error_line || '?'}:</strong> ${escapeHtml(err.error_message || 'Syntax error')}
          ${err.error_text ? `<div class="mt-1 font-monospace small bg-white p-1 rounded border">${escapeHtml(err.error_text)}</div>` : ''}
        </div>
      `;
    }
  }

  // 1. Functions Table
  renderFunctionsTable(data.functions || []);

  // 2. Classes Table
  renderClassesTable(data.classes || []);

  // 3. Imports Table
  renderImportsTable(data.imports || []);

  // 4. Global Variables Table
  renderGlobalsTable(data.global_variables || []);

  // 5. Code Structure ASCII Tree
  renderStructureTree(data);

  // 6. Simple English Explanation
  renderExplanationSection(data.explanation || {});
}

// Render Functions Table
function renderFunctionsTable(functions) {
  const tbody = document.getElementById("functions-table-body");
  if (!tbody) return;

  if (functions.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center py-3 text-muted">No standalone functions detected.</td></tr>`;
    return;
  }

  tbody.innerHTML = functions.map((f, idx) => {
    const paramsList = f.parameters.map(p => {
      const ann = p.type_annotation ? `<span class="text-muted">: ${escapeHtml(p.type_annotation)}</span>` : '';
      const dflt = p.default_value !== null ? `<span class="text-info">= ${escapeHtml(p.default_value)}</span>` : '';
      return `<code>${escapeHtml(p.name)}${ann}${dflt}</code>`;
    }).join(", ");

    const retAnn = f.return_annotation ? `<code>${escapeHtml(f.return_annotation)}</code>` : '<span class="text-muted">None</span>';
    const asyncBadge = f.is_async ? '<span class="badge badge-primary me-1">async</span>' : '';

    return `
      <tr>
        <td>
          <div class="fw-bold">${asyncBadge}<code>${escapeHtml(f.name)}()</code></div>
          ${f.docstring ? `<div class="small text-muted text-truncate" style="max-width:250px;">${escapeHtml(f.docstring)}</div>` : ''}
        </td>
        <td>${paramsList || '<span class="text-muted">None</span>'}</td>
        <td>${retAnn}</td>
        <td><span class="badge badge-secondary">L${f.line_start} - L${f.line_end}</span></td>
        <td>
          <button class="btn btn-outline btn-sm" onclick="showFunctionDetails(${idx})">Details</button>
        </td>
      </tr>
    `;
  }).join("");
}

// Modal or Alert for Function Details
function showFunctionDetails(index) {
  if (!state.analysisResult || !state.analysisResult.functions) return;
  const f = state.analysisResult.functions[index];
  if (!f) return;

  let modalContent = `
    <h4>def ${escapeHtml(f.name)}(...)</h4>
    <p><strong>Lines:</strong> ${f.line_start} - ${f.line_end}</p>
    <p><strong>Simple English Explanation:</strong> ${escapeHtml(f.explanation || 'N/A')}</p>
    ${f.docstring ? `<blockquote>${escapeHtml(f.docstring)}</blockquote>` : ''}
    <h5>Parameters</h5>
    <ul>
      ${f.parameters.map(p => `<li><strong>${escapeHtml(p.name)}</strong> (${p.kind}): ${escapeHtml(p.description || '')}</li>`).join('')}
    </ul>
    <p><strong>Return Annotation:</strong> ${escapeHtml(f.return_annotation || 'None')}</p>
    ${f.detected_returns && f.detected_returns.length ? `<p><strong>Detected Returns:</strong> ${f.detected_returns.map(r => `<code>${escapeHtml(r)}</code>`).join(', ')}</p>` : ''}
  `;

  const detailsContainer = document.getElementById("function-details-container");
  if (detailsContainer) {
    detailsContainer.innerHTML = modalContent;
    const modalElem = document.getElementById("function-details-modal");
    if (modalElem) modalElem.style.display = "block";
  } else {
    alert(`Function: ${f.name}\nExplanation: ${f.explanation || ''}`);
  }
}

// Render Classes Table
function renderClassesTable(classes) {
  const tbody = document.getElementById("classes-table-body");
  if (!tbody) return;

  if (classes.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center py-3 text-muted">No classes detected.</td></tr>`;
    return;
  }

  tbody.innerHTML = classes.map(c => {
    const basesStr = c.bases.length ? c.bases.map(b => `<code>${escapeHtml(b)}</code>`).join(", ") : '<span class="text-muted">object</span>';
    const methodNames = c.methods.map(m => `<code>${escapeHtml(m.name)}()</code>`).join(", ");

    return `
      <tr>
        <td>
          <div class="fw-bold"><code>class ${escapeHtml(c.name)}</code></div>
          ${c.docstring ? `<div class="small text-muted text-truncate" style="max-width:260px;">${escapeHtml(c.docstring)}</div>` : ''}
        </td>
        <td>${basesStr}</td>
        <td><span class="badge badge-primary">${c.methods.length} methods</span></td>
        <td>${methodNames || '<span class="text-muted">None</span>'}</td>
        <td><span class="badge badge-secondary">L${c.line_start} - L${c.line_end}</span></td>
      </tr>
    `;
  }).join("");
}

// Render Imports Table
function renderImportsTable(imports) {
  const tbody = document.getElementById("imports-table-body");
  if (!tbody) return;

  if (imports.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" class="text-center py-3 text-muted">No imports found.</td></tr>`;
    return;
  }

  tbody.innerHTML = imports.map(imp => {
    let stmt = imp.is_from ? `from ${imp.module} import ${imp.imported_names.join(', ')}` : `import ${imp.module}`;
    if (imp.alias) stmt += ` as ${imp.alias}`;

    return `
      <tr>
        <td><code>${escapeHtml(stmt)}</code></td>
        <td><strong>${escapeHtml(imp.module)}</strong></td>
        <td><span class="badge badge-secondary">L${imp.lineno}</span></td>
        <td>${escapeHtml(imp.purpose || 'Library dependency')}</td>
      </tr>
    `;
  }).join("");
}

// Render Global Variables Table
function renderGlobalsTable(globalsList) {
  const tbody = document.getElementById("globals-table-body");
  if (!tbody) return;

  if (globalsList.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" class="text-center py-3 text-muted">No global variables or constants detected.</td></tr>`;
    return;
  }

  tbody.innerHTML = globalsList.map(g => `
    <tr>
      <td><strong>${escapeHtml(g.name)}</strong></td>
      <td>${g.type_annotation ? `<code>${escapeHtml(g.type_annotation)}</code>` : '<span class="text-muted">-</span>'}</td>
      <td><code>${escapeHtml(g.value_preview || '-')}</code></td>
      <td><span class="badge badge-secondary">L${g.lineno}</span></td>
    </tr>
  `).join("");
}

// Render Structure Tree
function renderStructureTree(data) {
  const treeContainer = document.getElementById("structure-tree-content");
  if (!treeContainer) return;

  let lines = [`📄 ${data.filename}`];

  if (data.global_variables && data.global_variables.length) {
    lines.push("├── 🌐 Global Variables");
    data.global_variables.forEach((g, i) => {
      const isLast = (i === data.global_variables.length - 1) && !data.classes.length && !data.functions.length;
      lines.push(`│   ${isLast ? '└──' : '├──'} ${g.name} (L${g.lineno})`);
    });
  }

  if (data.classes && data.classes.length) {
    lines.push("├── 🏛️ Classes");
    data.classes.forEach((c, i) => {
      const isLast = (i === data.classes.length - 1) && !data.functions.length;
      lines.push(`│   ${isLast ? '└──' : '├──'} class ${c.name} (L${c.line_start}-L${c.line_end})`);
      c.methods.forEach((m, j) => {
        const mLast = j === c.methods.length - 1;
        lines.push(`│   ${isLast ? '    ' : '│   '}${mLast ? '└──' : '├──'} def ${m.name}() (L${m.line_start}-L${m.line_end})`);
      });
    });
  }

  if (data.functions && data.functions.length) {
    lines.push("└── ⚡ Standalone Functions");
    data.functions.forEach((f, i) => {
      const isLast = i === data.functions.length - 1;
      lines.push(`    ${isLast ? '└──' : '├──'} def ${f.name}() (L${f.line_start}-L${f.line_end})`);
    });
  }

  treeContainer.textContent = lines.join("\n");
}

// Render Simple English Explanation
function renderExplanationSection(expl) {
  const summaryElem = document.getElementById("explanation-module-summary");
  if (summaryElem) {
    summaryElem.innerHTML = escapeHtml(expl.module_summary || "No explanation generated yet.").replace(/\n/g, "<br/>");
  }

  const insightsElem = document.getElementById("explanation-insights-list");
  if (insightsElem) {
    if (expl.general_insights && expl.general_insights.length) {
      insightsElem.innerHTML = expl.general_insights.map(i => `<li>${escapeHtml(i)}</li>`).join("");
    } else {
      insightsElem.innerHTML = `<li>Static code analysis completed successfully.</li>`;
    }
  }
}

// View Generated Documentation Content
async function viewDocs(fileId) {
  try {
    const res = await fetch(`/api/documentation/${fileId}`);
    if (!res.ok) throw new Error("Documentation not found. Analyze file first.");
    const data = await res.json();
    state.currentFileId = fileId;
    state.currentFileName = data.filename;
    state.docContent = data.markdown_content;

    // Render Preview
    const previewContainer = document.getElementById("doc-preview-container");
    if (previewContainer) {
      previewContainer.innerHTML = renderMarkdown(data.markdown_content);
    }

    const rawContainer = document.getElementById("doc-raw-content");
    if (rawContainer) {
      rawContainer.textContent = data.markdown_content;
    }

    switchView("documentation");
  } catch (e) {
    showToast(e.message, "error");
  }
}

// Copy Raw Markdown to Clipboard
function copyMarkdownToClipboard() {
  if (!state.docContent) {
    showToast("No markdown content to copy.", "error");
    return;
  }
  navigator.clipboard.writeText(state.docContent).then(() => {
    showToast("Markdown copied to clipboard!", "success");
  }).catch(() => {
    showToast("Failed to copy to clipboard", "error");
  });
}

// Render Download View Details
function renderDownloadView() {
  const nameElem = document.getElementById("download-view-filename");
  const dlBtn = document.getElementById("download-view-btn");

  if (!state.currentFileId) {
    if (state.filesList.length > 0) {
      state.currentFileId = state.filesList[0].file_id;
      state.currentFileName = state.filesList[0].filename;
    }
  }

  if (state.currentFileId) {
    if (nameElem) nameElem.textContent = `${state.currentFileName || 'document'}_documentation.md`;
    if (dlBtn) dlBtn.href = `/api/download/${state.currentFileId}`;
  } else {
    if (nameElem) nameElem.textContent = "No file currently selected";
    if (dlBtn) dlBtn.href = "#";
  }
}

// Event Listeners on DOM Loaded
document.addEventListener("DOMContentLoaded", () => {
  // Navigation tabs
  document.querySelectorAll(".nav-item").forEach(item => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const view = item.getAttribute("data-view");
      if (view) switchView(view);
    });
  });

  // Mobile nav toggle
  const toggleBtn = document.getElementById("nav-toggle-btn");
  const sidebar = document.querySelector(".sidebar");
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("open");
    });
  }

  // File Dropzone
  const dropzone = document.getElementById("upload-dropzone");
  const fileInput = document.getElementById("file-input");

  if (dropzone && fileInput) {
    dropzone.addEventListener("click", () => fileInput.click());

    dropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });

    dropzone.addEventListener("dragleave", () => {
      dropzone.classList.remove("dragover");
    });

    dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleFileUpload(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener("change", () => {
      if (fileInput.files && fileInput.files.length > 0) {
        handleFileUpload(fileInput.files[0]);
      }
    });
  }

  // Sample load buttons
  const sampleBtn1 = document.getElementById("btn-load-sample");
  const sampleBtn2 = document.getElementById("btn-load-sample-2");
  if (sampleBtn1) sampleBtn1.addEventListener("click", loadSampleFile);
  if (sampleBtn2) sampleBtn2.addEventListener("click", loadSampleFile);

  // Markdown Subtabs (Rendered vs Raw)
  document.querySelectorAll(".doc-subtab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".doc-subtab-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const mode = btn.getAttribute("data-mode");
      const renderedTab = document.getElementById("doc-tab-rendered");
      const rawTab = document.getElementById("doc-tab-raw");
      if (mode === "rendered") {
        if (renderedTab) renderedTab.style.display = "block";
        if (rawTab) rawTab.style.display = "none";
      } else {
        if (renderedTab) renderedTab.style.display = "none";
        if (rawTab) rawTab.style.display = "block";
      }
    });
  });

  // Initial Load & Hash Route Support
  checkHealth();
  loadFilesList();

  const hash = window.location.hash.replace("#", "");
  if (hash && ["dashboard", "upload", "analysis", "documentation", "download", "about"].includes(hash)) {
    switchView(hash);
  }
});
