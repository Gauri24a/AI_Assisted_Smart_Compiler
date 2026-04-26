/* ═══════════════════════════════════════════════════════════════
   script.js — AI-Assisted Smart Compiler (Compiler Page)
   ═══════════════════════════════════════════════════════════════ */

const API = 'http://localhost:8000';

/* ── Sample codes ─────────────────────────────────────────────── */
const SAMPLES = {
  hello: `# Hello World — clean compile
name = "World"
greeting = "Hello, " + name
x = 42
y = x + 8
print(greeting)
print(y)`,

  fibonacci: `# Fibonacci — recursive function (clean)
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)

result = fib(10)
print(result)`,

  lex_parser: `# Lexer + Parser errors
x = 10
y = x @ 5
if x > 0
    print(x)`,

  // Notes:
  //   '@' is not a valid token in this compiler → Lexer Error
  //   'if x > 0' missing colon       → Parser Error

  parser_sem: `# Parser + Semantic errors
def greet(name)
    print(message)`,

  // Notes:
  //   missing ':' after def greet(name)  → Parser Error
  //   'message' is never defined          → Semantic Error

  lex_sem: `# Lexer + Semantic errors
result = 42
y = result + z
w = result $ 2`,

  // Notes:
  //   'z' used but never defined   → Semantic Error
  //   '$' is not a valid token     → Lexer Error

  all_three: `# All three error types
def calc(a, b)
    total = a + c
    return total @ 2`,

  // Notes:
  //   missing ':' after def calc(a, b)  → Parser Error
  //   'c' is never defined               → Semantic Error
  //   '@' is not a valid token           → Lexer Error

  blank: `# Write your Python here...

`,
};

/* ── DOM refs ─────────────────────────────────────────────────── */
const editor        = document.getElementById('code-editor');
const btnCompile    = document.getElementById('btn-compile');
const btnClear      = document.getElementById('btn-clear');
const sampleGrid    = document.getElementById('sample-grid');
const phaseTabs     = document.getElementById('phase-tabs');
const latencyPanel  = document.getElementById('latency-panel');
const mlBar         = document.getElementById('ml-bar');
const tradBar       = document.getElementById('trad-bar');
const mlTimeLabel   = document.getElementById('ml-time-label');
const tradTimeLabel = document.getElementById('trad-time-label');
const speedupVal    = document.getElementById('speedup-val');
const timingBreak   = document.getElementById('timing-breakdown');

/* ── Tab switching ────────────────────────────────────────────── */
phaseTabs.addEventListener('click', e => {
  const tab = e.target.closest('.tab');
  if (!tab) return;
  const phase = tab.dataset.phase;
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.phase-pane').forEach(p => p.classList.remove('active'));
  tab.classList.add('active');
  document.getElementById(`pane-${phase}`).classList.add('active');
});

/* ── Sample buttons ───────────────────────────────────────────── */
sampleGrid.addEventListener('click', e => {
  const btn = e.target.closest('.sample-btn');
  if (!btn) return;
  const code = SAMPLES[btn.dataset.sample];
  if (code !== undefined) editor.value = code;
});

/* ── Clear ────────────────────────────────────────────────────── */
btnClear.addEventListener('click', () => {
  editor.value = '';
  resetOutput();
});

/* ── Tab key in editor ────────────────────────────────────────── */
editor.addEventListener('keydown', e => {
  if (e.key === 'Tab') {
    e.preventDefault();
    const s = editor.selectionStart, en = editor.selectionEnd;
    editor.value = editor.value.substring(0, s) + '    ' + editor.value.substring(en);
    editor.selectionStart = editor.selectionEnd = s + 4;
  }
  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    doCompile();
  }
});

/* ── Compile ──────────────────────────────────────────────────── */
btnCompile.addEventListener('click', doCompile);

async function doCompile() {
  const code = editor.value;
  if (!code.trim()) return;

  setCompiling(true);
  resetOutput();

  let data;
  try {
    const res = await fetch(`${API}/compile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code }),
    });
    data = await res.json();
    if (!res.ok) {
      showFatalError(data.detail || `HTTP ${res.status}`);
      setCompiling(false);
      return;
    }
  } catch (err) {
    showFatalError(`Cannot reach backend at ${API}. Is the server running?\n\n${err.message}`);
    setCompiling(false);
    return;
  }

  renderResult(data);
  setCompiling(false);
}

/* ── Rendering ────────────────────────────────────────────────── */
function renderResult(data) {
  const phases = data.phases || {};

  renderLexer(phases.lexer, phases.llm);
  renderParser(phases.parser, phases.llm);
  renderSemantic(phases.semantic, phases.llm);
  renderIR(phases.ir);
  renderOptimizer(phases.optimizer);
  renderAssembly(phases.assembly);
  updateTabBadges(phases);
  renderLatency(data.timings_ms, data.traditional_ms, data.speedup);
}

// ─── Lexer ────────────────────────────────────────────────────────
function renderLexer(phase, llm) {
  const el = document.getElementById('inner-lexer');
  if (!phase) { el.innerHTML = emptyState('⬡', 'Lexer did not run.'); return; }

  let html = '';
  if (phase.status === 'ERROR' && phase.errors?.length) {
    html += errorList(phase.errors);
    if (llm && llm.status === 'OK' && llm.output && llm.output.triggered_by === 'Lexer') {
      html += renderLLMOutput(llm.output);
    }
  }
  if (phase.tokens?.length) {
    html += `
    <div style="overflow:auto;margin-top:${phase.errors?.length ? '0.75rem' : '0'}">
      <div style="font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--text-3);margin-bottom:.4rem;">
        ${phase.token_count} token${phase.token_count !== 1 ? 's' : ''}
      </div>
      <table class="data-table">
        <thead><tr>
          <th>#</th><th>Type</th><th>Value</th><th>Line</th><th>Col</th>
        </tr></thead>
        <tbody>
          ${phase.tokens.map((t, i) => `
            <tr>
              <td style="color:var(--text-3)">${i + 1}</td>
              <td><span class="mono tok-${t.type}">${esc(t.type)}</span></td>
              <td><span class="mono">${esc(t.value)}</span></td>
              <td style="color:var(--text-3)">${t.line}</td>
              <td style="color:var(--text-3)">${t.col ?? '—'}</td>
            </tr>`).join('')}
        </tbody>
      </table>
    </div>`;
  } else if (phase.status === 'OK') {
    html = emptyState('⬡', 'No tokens produced.');
  }
  el.innerHTML = html;
}

// ─── Parser / AST ─────────────────────────────────────────────────
function renderParser(phase, llm) {
  const el = document.getElementById('inner-parser');
  if (!phase) { el.innerHTML = emptyState('⟨⟩', 'Parser did not run.'); return; }

  let html = '';
  if (phase.status === 'ERROR' && phase.errors?.length) {
    html += errorList(phase.errors);
    if (llm && llm.status === 'OK' && llm.output && llm.output.triggered_by === 'Parser') {
      html += renderLLMOutput(llm.output);
    }
    html += `<div style="margin-top:.5rem;font-size:.75rem;color:var(--text-3)">Partial AST shown below (if available).</div>`;
  }

  if (phase.cache_stats && phase.cache_stats.total > 0) {
    const cs = phase.cache_stats;
    const hitPct = Math.round(cs.hit_rate * 100);
    html += `
    <div style="display:flex;gap:.5rem;flex-wrap:wrap;margin:.75rem 0 .5rem;font-size:.78rem;">
      <span class="badge badge-ml">ML Layer 1</span>
      <span style="color:var(--text-2)">Cache hits: <b style="color:var(--green)">${cs.hits}</b> / ${cs.total}
        <span style="color:var(--text-3)">(${hitPct}%)</span>
      </span>
    </div>`;
  }

  if (phase.tree) {
    html += `
    <div style="font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--text-3);margin-bottom:.4rem;">Abstract Syntax Tree</div>
    <pre class="code-output" style="border-radius:var(--radius);max-height:100%;overflow:auto">${esc(JSON.stringify(phase.tree, null, 2))}</pre>`;
  } else if (phase.status === 'SKIPPED') {
    html = emptyState('⟨⟩', phase.errors?.[0] || 'Parser skipped.');
  }

  el.innerHTML = html || emptyState('⟨⟩', 'No AST produced.');
}

// ─── Semantic ─────────────────────────────────────────────────────
function renderSemantic(phase, llm) {
  const el = document.getElementById('inner-semantic');
  if (!phase) { el.innerHTML = emptyState('✦', 'Semantic analysis did not run.'); return; }

  if (phase.status === 'SKIPPED') {
    el.innerHTML = emptyState('✦', phase.errors?.[0] || 'Skipped.');
    return;
  }

  if (phase.errors?.length) {
    let html = errorList(phase.errors);
    if (llm && llm.status === 'OK' && llm.output && llm.output.triggered_by === 'Semantic') {
      html += renderLLMOutput(llm.output);
    }
    el.innerHTML = html;
  } else {
    el.innerHTML = `<div class="success-msg">
      <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.75.75 0 0 1 1.06-1.06L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0z"/></svg>
      No semantic errors detected.
    </div>`;
  }
}

// ─── IR ───────────────────────────────────────────────────────────
function renderIR(phase) {
  const el = document.getElementById('inner-ir');
  if (!phase) { el.innerHTML = emptyState('≡', 'IR did not run.'); return; }

  if (phase.status === 'ERROR') {
    el.innerHTML = errorList(phase.errors || ['IR generation failed.']);
    return;
  }
  if (phase.status === 'SKIPPED') {
    el.innerHTML = emptyState('≡', 'IR skipped due to earlier errors.');
    return;
  }

  el.innerHTML = `
    <div style="font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--text-3);margin-bottom:.5rem;">
      ${phase.instr_count} instruction${phase.instr_count !== 1 ? 's' : ''}
    </div>
    <div style="overflow:auto">
      <table class="data-table">
        <thead><tr>
          <th>#</th><th>Op</th><th>Dest</th><th>A</th><th>B</th>
        </tr></thead>
        <tbody>
          ${(phase.instructions || []).map((instr, i) => `
            <tr>
              <td style="color:var(--text-3)">${i + 1}</td>
              <td><span class="mono" style="color:var(--accent)">${esc(instr.op)}</span></td>
              <td><span class="mono" style="color:var(--green)">${esc(instr.dest ?? '—')}</span></td>
              <td><span class="mono">${esc(instr.a ?? '—')}</span></td>
              <td><span class="mono">${esc(instr.b ?? '—')}</span></td>
            </tr>`).join('')}
        </tbody>
      </table>
    </div>`;
}

// ─── Optimizer ────────────────────────────────────────────────────
function renderOptimizer(phase) {
  const el = document.getElementById('inner-optimizer');
  if (!phase) { el.innerHTML = emptyState('⚡', 'Optimizer did not run.'); return; }

  if (phase.status === 'SKIPPED') {
    el.innerHTML = emptyState('⚡', 'Optimizer skipped due to earlier errors.');
    return;
  }

  const strategies = phase.strategies_applied || [];
  const delta = (phase.original_count ?? 0) - (phase.optimized_count ?? 0);

  let html = `
    <div style="display:flex;flex-wrap:wrap;gap:.5rem;margin-bottom:.75rem;align-items:center;">
      <span class="badge badge-ml">ML Layer 3</span>
      ${strategies.length
        ? strategies.map(s => `<span class="badge badge-ok">${esc(s)}</span>`).join('')
        : '<span class="badge badge-skip">no strategies applied</span>'}
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:.75rem;margin-bottom:.75rem;">
      ${statBox('Original', phase.original_count ?? '—', 'instructions')}
      ${statBox('Optimized', phase.optimized_count ?? '—', 'instructions')}
      ${statBox('Reduction', delta > 0 ? `−${delta}` : (delta < 0 ? `+${Math.abs(delta)}` : '0'), 'instructions')}
    </div>`;

  if (phase.instructions?.length) {
    html += `
    <div style="font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--text-3);margin-bottom:.4rem;">Optimized IR</div>
    <div style="overflow:auto">
      <table class="data-table">
        <thead><tr><th>#</th><th>Op</th><th>Dest</th><th>A</th><th>B</th></tr></thead>
        <tbody>
          ${phase.instructions.map((instr, i) => `
            <tr>
              <td style="color:var(--text-3)">${i + 1}</td>
              <td><span class="mono" style="color:var(--accent)">${esc(instr.op)}</span></td>
              <td><span class="mono" style="color:var(--green)">${esc(instr.dest ?? '—')}</span></td>
              <td><span class="mono">${esc(instr.a ?? '—')}</span></td>
              <td><span class="mono">${esc(instr.b ?? '—')}</span></td>
            </tr>`).join('')}
        </tbody>
      </table>
    </div>`;
  }

  el.innerHTML = html;
}

// ─── Assembly ─────────────────────────────────────────────────────
function renderAssembly(phase) {
  const el = document.getElementById('inner-assembly');
  if (!phase) { el.innerHTML = emptyState('⬟', 'Assembly did not run.'); return; }

  if (phase.status === 'SKIPPED') {
    el.innerHTML = emptyState('⬟', 'Assembly skipped due to earlier errors.');
    return;
  }

  const lines = phase.lines || [];
  const formatted = lines.map((line, i) => {
    const ln = String(i + 1).padStart(3, ' ');
    if (!line.trim()) return `<div class="asm-line"><span class="ln">${ln}</span><span></span></div>`;
    const isLabel = /^[A-Za-z_]\w*:/.test(line.trim());
    if (isLabel) {
      return `<div class="asm-line"><span class="ln">${ln}</span><span class="label-def">${esc(line)}</span></div>`;
    }
    const parts = line.trim().split(/\s+/);
    const opCode = parts[0];
    const rest = parts.slice(1).map(p => {
      if (/^r\d+$/.test(p)) return `<span class="reg">${esc(p)}</span>`;
      return esc(p);
    }).join('  ');
    return `<div class="asm-line"><span class="ln">${ln}</span><span class="op-code">${esc(opCode)}</span>&nbsp;&nbsp;${rest}</div>`;
  }).join('');

  el.innerHTML = `
    <div style="font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--text-3);margin-bottom:.5rem;">
      ${lines.length} line${lines.length !== 1 ? 's' : ''}
    </div>
    <div class="code-output" style="border-radius:var(--radius)">${formatted}</div>`;
}

/* ── Update tab badges ────────────────────────────────────────── */
function updateTabBadges(phases) {
  const phaseMap = {
    lexer: 'lexer', parser: 'parser', semantic: 'semantic',
    ir: 'ir', optimizer: 'optimizer', assembly: 'assembly',
  };
  for (const [key, tabId] of Object.entries(phaseMap)) {
    const tab = document.getElementById(`tab-${tabId}`);
    if (!tab) continue;
    const badge = tab.querySelector('.tab-badge');
    if (badge) badge.remove();

    const phase = phases[key];
    if (!phase) continue;

    const b = document.createElement('span');
    b.className = 'tab-badge';

    if (phase.status === 'ERROR') {
      const count = phase.errors?.length || 1;
      b.textContent = count;
      b.classList.add('err');
      tab.appendChild(b);
    } else if (phase.status === 'OK' || phase.status === undefined) {
      b.textContent = '✓';
      b.classList.add('ok');
      tab.appendChild(b);
    }
  }

  // Auto-switch to first error tab
  const errorPhases = ['lexer','parser','semantic','ir','optimizer','assembly'];
  for (const ph of errorPhases) {
    const p = phases[ph];
    if (p && p.status === 'ERROR') {
      switchTab(ph);
      break;
    }
  }
}

function switchTab(phase) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.phase-pane').forEach(p => p.classList.remove('active'));
  const tab = document.querySelector(`[data-phase="${phase}"]`);
  if (tab) tab.classList.add('active');
  const pane = document.getElementById(`pane-${phase}`);
  if (pane) pane.classList.add('active');
}

/* ── Latency panel ────────────────────────────────────────────── */
function renderLatency(mlMs, tradMs, speedup) {
  if (!mlMs) return;

  latencyPanel.style.display = 'flex';

  const mlTotal   = mlMs.total   || 0;
  const tradTotal = tradMs?.total || 0;
  const maxMs     = Math.max(mlTotal, tradTotal, 0.01);

  mlTimeLabel.textContent   = `${mlTotal.toFixed(2)} ms`;
  tradTimeLabel.textContent = tradTotal > 0 ? `~${tradTotal.toFixed(2)} ms` : '—';

  // Animate bars after paint
  requestAnimationFrame(() => {
    setTimeout(() => {
      mlBar.style.width   = `${Math.min((mlTotal   / maxMs) * 100, 100)}%`;
      tradBar.style.width = `${Math.min((tradTotal / maxMs) * 100, 100)}%`;
    }, 60);
  });

  if (speedup && speedup > 0) {
    speedupVal.textContent = `${speedup}× faster`;
  } else {
    speedupVal.textContent = '';
  }

  // Breakdown string  
  const parts = ['lexer','parser','semantic','ir','optimizer','assembly']
    .filter(k => mlMs[k] != null)
    .map(k => `${k}: ${mlMs[k].toFixed(2)}ms`);
  timingBreak.textContent = parts.join(' · ');
}

/* ── Fatal error display ──────────────────────────────────────── */
function showFatalError(msg) {
  ['lexer','parser','semantic','ir','optimizer','assembly'].forEach(ph => {
    document.getElementById(`inner-${ph}`).innerHTML =
      `<div class="error-item"><span class="err-icon">✕</span><span class="err-text">${esc(msg)}</span></div>`;
  });
}

/* ── Reset output ─────────────────────────────────────────────── */
function resetOutput() {
  const empties = {
    lexer:     ['⬡',  'Tokens will appear here after compilation.'],
    parser:    ['⟨⟩', 'AST will appear here after compilation.'],
    semantic:  ['✦',  'Semantic analysis results will appear here.'],
    ir:        ['≡',  'IR instructions will appear here after compilation.'],
    optimizer: ['⚡',  'Optimizer results will appear here after compilation.'],
    assembly:  ['⬟',  'Assembly output will appear here after compilation.'],
  };
  for (const [ph, [icon, msg]] of Object.entries(empties)) {
    document.getElementById(`inner-${ph}`).innerHTML = emptyState(icon, msg);
  }
  document.querySelectorAll('.tab .tab-badge').forEach(b => b.remove());
  latencyPanel.style.display = 'none';
  mlBar.style.width   = '0%';
  tradBar.style.width = '0%';
}

/* ── Compile button state ─────────────────────────────────────── */
function setCompiling(on) {
  btnCompile.disabled = on;
  btnCompile.innerHTML = on
    ? `<span class="spinner"></span> Compiling…`
    : `<svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M5 3.5l7 4.5-7 4.5V3.5z"/></svg> Compile`;
}

/* ── Helpers ──────────────────────────────────────────────────── */
function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function emptyState(icon, msg) {
  return `<div class="empty-state"><div class="empty-icon">${icon}</div><div>${msg}</div></div>`;
}

function errorList(errors) {
  return `<ul class="error-list">${errors.map(e =>
    `<li class="error-item"><span class="err-icon">✕</span><span class="err-text">${esc(e)}</span></li>`
  ).join('')}</ul>`;
}

function statBox(label, value, unit) {
  return `
    <div style="background:var(--bg-2);border:1px solid var(--border);border-radius:var(--radius);padding:.6rem .75rem;">
      <div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--text-3);margin-bottom:.25rem;">${label}</div>
      <div style="font-family:var(--mono);font-size:1.1rem;font-weight:600;color:var(--text)">${value}</div>
      <div style="font-size:.7rem;color:var(--text-3)">${unit}</div>
    </div>`;
}

function renderLLMOutput(llm) {
  if (!llm || !llm.llm_response) return '';
  
  let raw = llm.llm_response;
  const blocks = [];
  raw = raw.replace(/```(?:python)?\n?([\s\S]*?)```/g, (m, code) => {
    blocks.push(code);
    return `%%%BLOCK${blocks.length - 1}%%%`;
  });
  
  raw = esc(raw);
  
  raw = raw.replace(/%%%BLOCK(\d+)%%%/g, (m, idx) => {
    return `<pre class="code-output" style="margin:0.5rem 0;padding:0.5rem;background:var(--bg-1);border-radius:var(--radius);">${esc(blocks[idx])}</pre>`;
  });
  
  raw = raw.replace(/### (.*?)(?:\n|$)/g, '<h4 style="color:var(--accent);margin:0.5rem 0 0.25rem;">$1</h4>\n');
  raw = raw.replace(/\*\*(.*?)\*\*/g, '<strong style="color:var(--text)">$1</strong>');
  raw = raw.replace(/`([^`]+)`/g, '<span class="mono" style="color:var(--green)">$1</span>');
  
  return `
    <div style="margin-top:1rem; border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; background: var(--bg-1);">
      <div style="background: var(--bg-2); padding: 0.5rem 0.75rem; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 0.5rem;">
        <span style="font-size: 1rem;">✨</span>
        <span style="font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--accent);">AI Repair Analysis (${llm.gemini_model || 'Gemini'})</span>
      </div>
      <div style="padding: 0.75rem; font-size: 0.85rem; color: var(--text-2); white-space: pre-wrap; line-height: 1.5;">${raw}</div>
    </div>
  `;
}
