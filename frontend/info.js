/* ═══════════════════════════════════════════════════════════════
   info.js — Info & FAQ Page
   Loads data from GET /info, renders pipeline, phases, ML cards, FAQ
   ═══════════════════════════════════════════════════════════════ */

const API = 'http://localhost:8000';

async function loadInfo() {
  let data;
  try {
    const res = await fetch(`${API}/info`);
    data = await res.json();
  } catch (err) {
    // Backend offline — use embedded fallback data
    data = FALLBACK_DATA;
  }

  renderPipeline(data.phases);
  renderPhases(data.phases);
  renderMLCards(data.ml_models);
  renderFAQ(data.faq);
  animateAccuracyBars();
}

/* ── Pipeline flow diagram ────────────────────────────────────── */
function renderPipeline(phases) {
  const el = document.getElementById('pipeline-flow');
  if (!el) return;

  const nodes = [
    { label: 'Source\nCode',  sub: '',               ml: false },
    { label: 'Lexer',         sub: 'Lexical Analysis', ml: false },
    { label: 'ML Layer 1',    sub: 'Cache Lookup',    ml: true  },
    { label: 'ML Layer 2',    sub: 'Dispatch Hint',   ml: true  },
    { label: 'Parser',        sub: 'AST Builder',     ml: false },
    { label: 'Semantic',      sub: 'Analyzer',        ml: false },
    { label: 'IR Gen',        sub: 'Intermediate Rep',ml: false },
    { label: 'ML Layer 3',    sub: 'Opt Predictor',   ml: true  },
    { label: 'Optimizer',     sub: 'Code Optimizer',  ml: false },
    { label: 'Assembly',      sub: 'Code Emitter',    ml: false },
  ];

  el.innerHTML = nodes.map((n, i) => `
    <div class="pipe-node">
      <div class="pipe-box${n.ml ? ' ml-node' : ''}">${n.label.replace('\n','<br>')}</div>
      <div class="pipe-label">${n.sub}</div>
    </div>
    ${i < nodes.length - 1 ? '<div class="pipe-arrow">→</div>' : ''}
  `).join('');
}

/* ── Phase cards ──────────────────────────────────────────────── */
function renderPhases(phases) {
  const el = document.getElementById('phase-grid');
  if (!el) return;

  el.innerHTML = phases.map(p => `
    <div class="phase-card${p.ml ? ' has-ml' : ''}">
      <div class="phase-card-header">
        <div>
          <h3>${esc(p.name)}</h3>
          <div class="phase-subtitle">${esc(p.subtitle)}</div>
        </div>
        ${p.ml
          ? `<span class="badge badge-ml">ML</span>`
          : `<span class="badge badge-skip">Det.</span>`}
      </div>
      <p style="font-size:.82rem;line-height:1.65;">${esc(p.description)}</p>
      ${p.ml && p.ml_layers ? `
        <div style="margin-top:.6rem;display:flex;flex-wrap:wrap;gap:.3rem;">
          ${p.ml_layers.map(l => `<span class="badge badge-ml" style="font-size:.68rem">${esc(l)}</span>`).join('')}
        </div>` : ''}
      <div class="io-row">
        <div class="io-item">
          <span class="io-key">In</span>
          <span class="io-val">${esc(p.input)}</span>
        </div>
        <div class="io-item">
          <span class="io-key">Out</span>
          <span class="io-val">${esc(p.output)}</span>
        </div>
      </div>
    </div>
  `).join('');
}

/* ── ML model cards ───────────────────────────────────────────── */
function renderMLCards(models) {
  const el = document.getElementById('ml-cards');
  if (!el) return;

  el.innerHTML = models.map(m => {
    if (m.id === 'layer1') return renderLayer1Card(m);
    if (m.id === 'layer2') return renderLayer2Card(m);
    if (m.id === 'layer3') return renderLayer3Card(m);
    return '';
  }).join('');
}

function renderLayer1Card(m) {
  return `
  <div class="ml-card">
    <div class="ml-card-header">
      <div class="layer-tag">${esc(m.name)}</div>
      <h3>${esc(m.title)}</h3>
      <p>${esc(m.position)}</p>
    </div>
    <div class="ml-card-body">
      <div class="ml-stat-row">
        <div class="ml-stat-label">Mechanism</div>
        <div class="ml-stat-val">${esc(m.mechanism)}</div>
      </div>
      <div class="ml-stat-row">
        <div class="ml-stat-label">Model Type</div>
        <div class="ml-stat-val">${esc(m.model_type)}</div>
      </div>
      <div class="ml-stat-row">
        <div class="ml-stat-label">Latency Saving</div>
        <div class="ml-stat-val accent">${esc(m.latency_saving)}</div>
      </div>
      <div class="ml-stat-row">
        <div class="ml-stat-label">Key Insight</div>
        <div class="ml-stat-val" style="font-size:.8rem;color:var(--text-2)">${esc(m.key_insight)}</div>
      </div>
      <div class="ml-stat-row">
        <div class="ml-stat-label">Training</div>
        <div class="ml-stat-val" style="font-size:.8rem;color:var(--text-2)">${esc(m.training)}</div>
      </div>
    </div>
  </div>`;
}

function renderLayer2Card(m) {
  const classBadges = (m.class_list || []).map(c =>
    `<span class="badge badge-ok" style="font-size:.65rem">${esc(c)}</span>`
  ).join('');

  return `
  <div class="ml-card">
    <div class="ml-card-header">
      <div class="layer-tag">${esc(m.name)}</div>
      <h3>${esc(m.title)}</h3>
      <p>${esc(m.position)}</p>
    </div>
    <div class="ml-card-body">
      <div class="ml-stat-row">
        <div class="ml-stat-label">Model Type</div>
        <div class="ml-stat-val">${esc(m.model_type)}</div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:.5rem;">
        <div class="ml-stat-row">
          <div class="ml-stat-label">Training Samples</div>
          <div class="ml-stat-val accent">${(m.training_samples||0).toLocaleString()}</div>
        </div>
        <div class="ml-stat-row">
          <div class="ml-stat-label">Classes</div>
          <div class="ml-stat-val accent">${m.classes}</div>
        </div>
        <div class="ml-stat-row">
          <div class="ml-stat-label">CV Accuracy</div>
          <div class="ml-stat-val green">${esc(m.cv_accuracy)}</div>
        </div>
        <div class="ml-stat-row">
          <div class="ml-stat-label">Test Accuracy</div>
          <div class="ml-stat-val green">${esc(m.test_accuracy)}</div>
        </div>
      </div>
      <div class="accuracy-bar-wrap">
        <div class="accuracy-bar-label">
          <span>Test Accuracy</span>
          <span>${esc(m.test_accuracy)}</span>
        </div>
        <div class="accuracy-bar">
          <div class="accuracy-fill" data-pct="100"></div>
        </div>
      </div>
      <div class="ml-stat-row">
        <div class="ml-stat-label">Confidence Threshold</div>
        <div class="ml-stat-val">${m.confidence_threshold} (fallback: rule-based)</div>
      </div>
      <div class="ml-stat-row">
        <div class="ml-stat-label">Statement Classes</div>
        <div style="display:flex;flex-wrap:wrap;gap:.3rem;margin-top:.25rem;">${classBadges}</div>
      </div>
      <div class="ml-stat-row">
        <div class="ml-stat-label">Safety Guarantee</div>
        <div class="ml-stat-val" style="font-size:.8rem;color:var(--text-2)">${esc(m.safety)}</div>
      </div>
    </div>
  </div>`;
}

function renderLayer3Card(m) {
  const stratRows = Object.entries(m.per_strategy_metrics || {}).map(([strat, stats]) => {
    const pct = Math.round(parseFloat(stats.test_accuracy) || 0);
    return `
    <div style="margin-bottom:.6rem;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.2rem;">
        <span style="font-size:.78rem;font-weight:600;color:var(--text)">${esc(strat)}</span>
        <span style="font-size:.75rem;color:var(--text-2)">${esc(stats.test_accuracy)} &nbsp;·&nbsp; F1 ${esc(stats.cv_f1)}</span>
      </div>
      <div class="accuracy-bar">
        <div class="accuracy-fill" data-pct="${pct}"></div>
      </div>
    </div>`;
  }).join('');

  return `
  <div class="ml-card">
    <div class="ml-card-header">
      <div class="layer-tag">${esc(m.name)}</div>
      <h3>${esc(m.title)}</h3>
      <p>${esc(m.position)}</p>
    </div>
    <div class="ml-card-body">
      <div class="ml-stat-row">
        <div class="ml-stat-label">Model Type</div>
        <div class="ml-stat-val">${esc(m.model_type)}</div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:.5rem;">
        <div class="ml-stat-row">
          <div class="ml-stat-label">Training Samples</div>
          <div class="ml-stat-val accent">${(m.training_samples||0).toLocaleString()}</div>
        </div>
        <div class="ml-stat-row">
          <div class="ml-stat-label">Strategies</div>
          <div class="ml-stat-val accent">${(m.strategies||[]).length}</div>
        </div>
        <div class="ml-stat-row">
          <div class="ml-stat-label">CV Folds</div>
          <div class="ml-stat-val">${m.cv_folds}-fold</div>
        </div>
        <div class="ml-stat-row">
          <div class="ml-stat-label">Mean Accuracy</div>
          <div class="ml-stat-val green">${esc(m.mean_accuracy)}</div>
        </div>
      </div>
      <div class="ml-stat-row">
        <div class="ml-stat-label">Per-Strategy Accuracy</div>
        <div style="margin-top:.4rem">${stratRows}</div>
      </div>
      <div class="ml-stat-row">
        <div class="ml-stat-label">IR Features Used</div>
        <div style="display:flex;flex-wrap:wrap;gap:.3rem;margin-top:.25rem;">
          ${(m.features_used||[]).map(f =>
            `<span class="badge badge-skip" style="font-size:.65rem">${esc(f)}</span>`
          ).join('')}
        </div>
      </div>
      <div class="ml-stat-row">
        <div class="ml-stat-label">Latency Saving</div>
        <div class="ml-stat-val accent">${esc(m.latency_saving)}</div>
      </div>
    </div>
  </div>`;
}

/* ── FAQ ──────────────────────────────────────────────────────── */
function renderFAQ(faq) {
  const el = document.getElementById('faq-list');
  if (!el) return;

  el.innerHTML = faq.map((item, i) => `
    <div class="faq-item" id="faq-${i}">
      <div class="faq-q" onclick="toggleFAQ(${i})">
        <span>${esc(item.q)}</span>
        <svg class="chevron" width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
          <path d="M4 6l4 4 4-4"/>
        </svg>
      </div>
      <div class="faq-a"><p>${esc(item.a)}</p></div>
    </div>
  `).join('');
}

function toggleFAQ(i) {
  const item = document.getElementById(`faq-${i}`);
  const isOpen = item.classList.contains('open');
  document.querySelectorAll('.faq-item').forEach(el => el.classList.remove('open'));
  if (!isOpen) item.classList.add('open');
}

/* ── Animate accuracy bars ────────────────────────────────────── */
function animateAccuracyBars() {
  const obs = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const fills = entry.target.querySelectorAll('.accuracy-fill');
        fills.forEach(fill => {
          const pct = fill.dataset.pct || '0';
          setTimeout(() => { fill.style.width = `${pct}%`; }, 100);
        });
      }
    });
  }, { threshold: 0.2 });

  document.querySelectorAll('.ml-card').forEach(card => obs.observe(card));
}

/* ── Helpers ──────────────────────────────────────────────────── */
function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/* ── Fallback data (used when backend is offline) ─────────────── */
const FALLBACK_DATA = {
  phases: [
    { id:'lexer',     name:'Lexer',              subtitle:'Lexical Analysis',             ml:false, input:'Source code', output:'Token stream',         description:'Converts raw Python source into typed tokens. Handles indentation stack (INDENT/DEDENT), comments, strings, numbers, keywords, and identifiers. Any unrecognized character raises a LexerError with line and column.' },
    { id:'parser',    name:'Parser',             subtitle:'Syntax Analysis + ML 1 & 2',  ml:true,  input:'Token stream', output:'AST',                 ml_layers:['ML Layer 1 — Statement Cache','ML Layer 2 — Parser Dispatch Hint'], description:'Recursive-descent parser that builds an AST. ML Layer 1 checks a cache (token-type pattern → cached AST node) and skips parsing on hits. ML Layer 2 predicts statement type to eliminate conditional dispatch overhead.' },
    { id:'semantic',  name:'Semantic Analyzer',  subtitle:'Meaning-Level Correctness',   ml:false, input:'AST',          output:'Validated AST or errors', description:'Checks use-before-define, type mismatches, wrong argument counts, return outside function, and scope violations. Maintains a symbol table. No ML — deterministic rule-based analysis.' },
    { id:'ir',        name:'IR Generator',       subtitle:'Intermediate Representation', ml:false, input:'Validated AST', output:'IR instructions',      description:'Lowers AST to three-address IR: LOAD, STORE, BINOP, JUMP, CALL, RETURN. Flattens nested expressions with temp variables. Fully deterministic.' },
    { id:'optimizer', name:'Code Optimizer',     subtitle:'IR Optimization + ML 3',      ml:true,  input:'IR',           output:'Optimized IR',          ml_layers:['ML Layer 3 — Optimization Strategy Predictor'], description:'ML Layer 3 predicts which optimization strategies to run. Strategies: constant_fold, dead_code, loop_unroll, inline. Optimizer itself is deterministic — ML only advises what to try.' },
    { id:'assembly',  name:'Assembly Generator', subtitle:'Target Code Emission',        ml:false, input:'Optimized IR',  output:'Assembly lines',       description:'Translates optimized IR to target assembly via fixed rules. Handles register assignment, stack frames, CALL/RET conventions, and instruction selection (MOV, ADD, JMP, etc.).' },
  ],
  ml_models: [
    {
      id:'layer1', name:'ML Layer 1', title:'Statement Cache', position:'Before Parser',
      mechanism:'Online frequency table (token-type pattern → cached AST node)',
      model_type:'Online learning — frequency table built during compilation run',
      training:'No offline training. Learns from the current file as it processes.',
      latency_saving:'Skips parser entirely on cache hit',
      key_insight:"Cache key = token types only (not values). 'x = 5' and 'count = 0' share key 'IDENTIFIER OPERATOR INTEGER', giving high hit rates in real code.",
      accuracy:'N/A — hit rate grows with repetition',
    },
    {
      id:'layer2', name:'ML Layer 2', title:'Parser Dispatch Hint', position:'Inside Parser (on cache miss)',
      mechanism:'TF-IDF token sequence → Random Forest → statement type label',
      model_type:'TF-IDF vectorizer + Random Forest (Pipeline)',
      training_samples:15000, train_test_split:'12,000 / 3,000',
      classes:15,
      class_list:['assignment','funcdef','classdef','for_loop','while_loop','if_stmt','return_stmt','import_stmt','func_call','list_expr','dict_expr','lambda_expr','try_except','raise_stmt','assert_stmt'],
      cv_folds:5, cv_accuracy:'1.0000 ± 0.0000', test_accuracy:'100.00%',
      confidence_threshold:0.45,
      fallback:'Rule-based keyword map',
      latency_saving:'Eliminates conditional dispatch chain in the parser',
      safety:'Parser falls back to full dispatch if grammar rejects predicted type',
    },
    {
      id:'layer3', name:'ML Layer 3', title:'Optimization Strategy Predictor', position:'Before Code Optimizer',
      mechanism:'Numeric IR features → MultiOutputClassifier → binary flags per strategy',
      model_type:'MultiOutputClassifier (multi-label binary classification)',
      training_samples:8000, train_test_split:'6,400 / 1,600',
      strategies:['constant_fold','dead_code','loop_unroll','inline'],
      cv_folds:5, mean_accuracy:'94.03%',
      features_used:['n_instrs','n_assigns','n_binops','n_calls','n_labels','n_literals','n_temps','has_loop','call_density','assign_ratio','avg_use_count','depth_score'],
      latency_saving:'Skips optimization passes that will not help for the current IR block',
      per_strategy_metrics:{
        constant_fold:{ cv_f1:'0.9420 ± 0.0070', test_accuracy:'95.25%', precision_apply:0.95, recall_apply:0.96, f1_apply:0.95 },
        dead_code:    { cv_f1:'0.9136 ± 0.0047', test_accuracy:'93.00%', precision_apply:0.91, recall_apply:0.90, f1_apply:0.91 },
        loop_unroll:  { cv_f1:'0.8130 ± 0.0277', test_accuracy:'93.81%', precision_apply:0.88, recall_apply:0.80, f1_apply:0.84 },
        inline:       { cv_f1:'0.8922 ± 0.0052', test_accuracy:'94.06%', precision_apply:0.91, recall_apply:0.91, f1_apply:0.91 },
      },
    },
  ],
  faq: [
    { q:'Why put ML inside the compiler at all?', a:'The three ML layers target the three most expensive decisions: whether to re-parse a statement already seen, which grammar rule to try first, and which optimization passes are worth running. In each case ML reduces work for the deterministic components — the core logic stays correct.' },
    { q:'What exactly does ML Layer 1 cache?', a:"It caches AST node templates keyed on the token-type sequence — not the values. 'x = 5' and 'count = 0' share key 'IDENTIFIER OPERATOR INTEGER'. On a hit the parser is skipped entirely." },
    { q:'Does the compiler produce wrong output if ML Layer 2 makes a wrong prediction?', a:"No. The hint is advisory. If the parser's grammar rules reject the predicted type, it silently falls back to full recursive dispatch. Correctness is never sacrificed." },
    { q:'Why is ML Layer 2 accuracy 100%?', a:'Python statement types are almost perfectly determined by their opening token sequence. The TF-IDF + Random Forest model learns these near-deterministic patterns from 15,000 samples and achieves perfect separation on the test set.' },
    { q:'What IR features does ML Layer 3 use?', a:'12 numeric features: instruction count, counts of assigns/binops/calls/labels/literals/temps, loop presence flag, call density ratio, assign ratio, average variable use count, and depth score.' },
    { q:'How does the latency comparison work?', a:'Per-phase timings are multiplied by overhead factors: Parser ×3.5 (no cache), Optimizer ×4.0 (all passes). Lexer, IR, Assembly unchanged. This simulates a traditional compiler without ML acceleration.' },
    { q:'What errors can the compiler detect?', a:'Three tiers: (1) Lexer — illegal characters. (2) Parser — valid tokens in invalid order. (3) Semantic — scope/type violations. The pipeline continues through all reachable phases even after an error.' },
    { q:'What does the LLM layer do?', a:'When errors are found, the LLM layer receives the source code and all collected errors across all three tiers and generates a repair suggestion. It is invoked once with the full error set.' },
  ],
};

/* ── Init ─────────────────────────────────────────────────────── */
loadInfo();
