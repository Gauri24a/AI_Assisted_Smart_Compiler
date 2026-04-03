import React from 'react'
import { useEffect, useMemo, useState } from 'react'

const API_BASE_CANDIDATES = ['http://127.0.0.1:8001', 'http://localhost:8001', '']

async function requestJson(path, options) {
  let lastError = null

  for (const base of API_BASE_CANDIDATES) {
    try {
      const res = await fetch(`${base}${path}`, options)
      if (!res.ok) {
        const text = await res.text()
        throw new Error(`${res.status} ${res.statusText} - ${text}`)
      }
      return await res.json()
    } catch (err) {
      lastError = err
    }
  }

  throw lastError || new Error('API request failed')
}

const PHASE_LOGIC = {
  lexer: 'Tokenizes source code into keywords, identifiers, literals, operators, and delimiters.',
  parser: 'Builds AST using grammar rules and validates syntax structure.',
  classification: 'Converts AST statements to text and predicts statement class using TF-IDF + RandomForest.',
  semantic: 'Checks types, scope rules, symbol table consistency, and undefined variables.',
  llm: 'If semantic issues exist, asks Gemini for concise explanation and corrected code suggestion.',
}

const PHASE_EXAMPLES = [
  {
    title: '1) Lexical Analysis',
    purpose: 'Break source code into tokens (keywords, identifiers, operators, literals).',
    input: 'x = 5;\nif (x > 3) { print(x); }',
    output: 'IDENTIFIER(x), ASSIGN(=), NUMBER(5), SEMICOLON(;)\nIF, LPAREN, IDENTIFIER(x), GREATER, NUMBER(3), RPAREN, LBRACE, PRINT, LPAREN, IDENTIFIER(x), RPAREN, SEMICOLON, RBRACE',
  },
  {
    title: '2) Syntax Analysis (Parser)',
    purpose: 'Validate grammar and build AST structure.',
    input: 'x = 5;\nprint(x);',
    output: 'ProgramNode\n  AssignmentNode(target=x, value=5)\n  PrintNode(expression=x)',
  },
  {
    title: '3) ML Classification',
    purpose: 'Classify each statement intent using TF-IDF + RandomForest.',
    input: 'if (x > 10) { }',
    output: 'Predicted Type: Conditional\nConfidence: 83% (example)',
  },
  {
    title: '4) Semantic Analysis',
    purpose: 'Validate meaning: types, scope, symbol table, undefined variables.',
    input: 'x = 5;\nx = "hello";\nprint(y);',
    output: 'ERROR: Type mismatch for x (number vs string)\nERROR: Use of undefined variable y',
  },
  {
    title: '5) LLM Layer',
    purpose: 'When semantic errors exist, generate concise explanation + corrected code suggestion.',
    input: 'semantic status = error + issue list',
    output: 'Short human-readable explanation\nFix suggestions\nCorrected code block',
  },
]

const ML_METRICS = {
  datasetSize: '15,000 samples',
  classes: 15,
  split: 'Train: 12,000 | Test: 3,000',
  cv: '0.9578 ± 0.0027 (5-fold stratified)',
  testAcc: '0.9607 (96.07%)',
  notable: [
    'Loop: precision 1.00, recall 1.00',
    'Return: precision 1.00, recall 0.99',
    'Memory Allocation: precision 0.98, recall 0.98',
    'Increment/Decrement: precision 0.86, recall 0.86',
  ],
}

const ML_TRAINING_LOG = `Loaded 15,000 samples, 15 classes.

Train : 12,000  |  Test : 3,000

Running 5-fold stratified cross-validation à
CV Accuracy:  0.9578 ▒ 0.0027

Fitting final model on full training set à

============================================================
  Test Accuracy : 0.9607  (96.07%)
============================================================

Per-class report:
                     precision    recall  f1-score   support

         Assignment       0.94      0.98      0.96       200
               Loop       1.00      1.00      1.00       200
        Conditional       0.96      0.99      0.97       200
        Declaration       0.99      0.92      0.95       200
      Function Call       0.97      0.94      0.95       200
             Return       1.00      0.99      1.00       200
       Array Access       0.95      0.97      0.96       200
  Pointer Operation       0.91      0.93      0.92       200
      Struct Access       0.96      0.91      0.93       200
Increment/Decrement       0.86      0.86      0.86       200
  Bitwise Operation       1.00      0.99      1.00       200
 Logical Expression       0.99      0.98      0.99       200
    Cast Expression       0.95      0.96      0.96       200
  Memory Allocation       0.98      0.98      0.98       200
 Exception Handling       0.96      0.99      0.98       200

           accuracy                           0.96      3000
          macro avg       0.96      0.96      0.96      3000
       weighted avg       0.96      0.96      0.96      3000

Saved confusion matrix  ->  confusion.png
Saved feature importances  ->  feature_importance.png
Saved model             ->  model.pkl
Saved label encoder     ->  label_encoder.pkl

-- Inference demo --------------------------------------
Statement                                      Predicted Class
----------------------------------------------------------------------
  x = y + 5;                                   Assignment
  for (int i = 0; i < n; i++) { }              Loop
  if (count > 10) { }                          Conditional
  int result = 0;                              Assignment
  free(ptr);                                   Function Call
  return value;                                Return
  arr[i] = 42;                                 Array Access
  *ptr = x;                                    Assignment
  node->next = NULL;                           Struct Access
  x++;                                         Increment/Decrement
  flags = flags & 0xFF;                        Bitwise Operation
  ret = (x > 0) && (y < n);                    Logical Expression
  value = (int) ptr;                           Cast Expression
  buf = malloc(sizeof(int) * n);               Memory Allocation
  throw std::runtime_error("err");             Exception Handling`

export default function App() {
  const [page, setPage] = useState('pipeline')
  const [files, setFiles] = useState([])
  const [selectedPath, setSelectedPath] = useState('')
  const [isRunning, setIsRunning] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    requestJson('/api/files')
      .then((data) => {
        const loaded = data.files || []
        setFiles(loaded)
        if (loaded.length > 0) setSelectedPath(loaded[0].path)
      })
      .catch((e) => setError(String(e)))
  }, [])

  const selectedFile = useMemo(
    () => files.find((f) => f.path === selectedPath),
    [files, selectedPath]
  )

  async function runCompiler() {
    if (!selectedPath) return
    setIsRunning(true)
    setError('')
    try {
      const data = await requestJson('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_path: selectedPath }),
      })
      setResult(data)
    } catch (e) {
      setError(String(e))
    } finally {
      setIsRunning(false)
    }
  }

  const predictions = result?.compiler_output?.predictions || []
  const semantic = result?.compiler_output?.semantic || null
  const llm = result?.compiler_output?.llm_feedback || null
  const latency = result?.latency_comparison || null

  return (
    <div className="page">
      <header>
        <div>
          <h1>AI Assisted Smart Compiler</h1>
          <p className="muted">Interactive compiler pipeline + explainable ML/semantic flow</p>
        </div>
        <div className="top-nav">
          <button className={page === 'pipeline' ? 'nav-btn active' : 'nav-btn'} onClick={() => setPage('pipeline')}>
            Pipeline Page
          </button>
          <button className={page === 'learn' ? 'nav-btn active' : 'nav-btn'} onClick={() => setPage('learn')}>
            Phase Guide Page
          </button>
        </div>
      </header>

      {error && <div className="error">{error}</div>}

      {page === 'pipeline' ? (
        <>
          <section className="panel run-toolbar">
            <div>
              <h2>Run Compiler Pipeline</h2>
              <p className="muted">Select file on the left, then run. Outputs for each phase are shown below.</p>
            </div>
            <button disabled={!selectedPath || isRunning} onClick={runCompiler}>
              {isRunning ? 'Running...' : 'Run Pipeline'}
            </button>
          </section>

          <section className="layout">
            <aside className="panel">
              <h2>Source Files</h2>
              <ul className="file-list">
                {files.map((file) => (
                  <li key={file.path}>
                    <button
                      className={file.path === selectedPath ? 'active' : ''}
                      onClick={() => setSelectedPath(file.path)}
                    >
                      {file.path}
                    </button>
                  </li>
                ))}
              </ul>
            </aside>

            <main className="panel">
              <h2>Code Preview</h2>
              <pre className="tall">{selectedFile?.content || 'Select a file...'}</pre>
            </main>
          </section>

          <section className="panel">
            <h2>Phase Outputs</h2>
            <div className="phase-stack">
              <Phase title="Lexical Analysis" logic={PHASE_LOGIC.lexer} body={result?.phase_logs?.lexer} />
              <Phase title="Syntax Analysis" logic={PHASE_LOGIC.parser} body={result?.phase_logs?.parser} />
              <Phase title="ML Classification" logic={PHASE_LOGIC.classification} body={result?.phase_logs?.classification} />
              <Phase title="Semantic Analysis" logic={PHASE_LOGIC.semantic} body={result?.phase_logs?.semantic} />
              <Phase title="LLM Layer" logic={PHASE_LOGIC.llm} body={result?.phase_logs?.llm || 'Not triggered'} />
            </div>
          </section>

          <section className="panel">
            <h2>Compile Latency Comparison (to Semantic Analyzer)</h2>
            <LatencyView latency={latency} />
          </section>

          <section className="panel">
            <h2>Predictions</h2>
            {predictions.length === 0 ? (
              <p>No predictions yet.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Statement</th>
                    <th>Predicted Type</th>
                    <th>Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {predictions.map((p, i) => (
                    <tr key={i}>
                      <td>{p.statement}</td>
                      <td>{p.predicted_type}</td>
                      <td>{Math.round((p.confidence || 0) * 100)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>

          <section className="layout two">
            <div className="panel">
              <h2>Semantic Analysis</h2>
              <SemanticView semantic={semantic} />
            </div>
            <div className="panel">
              <h2>LLM Feedback</h2>
              <LLMView llm={llm} />
            </div>
          </section>

          <section className="panel">
            <h2>Raw Compiler Logs</h2>
            <pre className="tall">{result?.stdout || 'No run yet.'}</pre>
          </section>
        </>
      ) : (
        <>
          <section className="layout two">
            <div className="panel">
              <h2>Know More (ML + Dataset)</h2>
              <KnowMoreView />
            </div>
            <div className="panel">
              <h2>FAQ</h2>
              <FAQView />
            </div>
          </section>

          <section className="panel">
            <h2>How Each Phase Works (with examples)</h2>
            <div className="learn-grid">
              {PHASE_EXAMPLES.map((item, idx) => (
                <article key={idx} className="learn-card">
                  <h3>{item.title}</h3>
                  <p className="muted">{item.purpose}</p>
                  <h4>Input Example</h4>
                  <pre>{item.input}</pre>
                  <h4>Output Example</h4>
                  <pre>{item.output}</pre>
                </article>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  )
}

function Phase({ title, logic, body }) {
  return (
    <article className="phase phase-output">
      <h3>{title}</h3>
      <p className="muted phase-logic">{logic}</p>
      <pre className="phase-pre">{body || 'No output yet.'}</pre>
    </article>
  )
}

function LatencyView({ latency }) {
  if (!latency) return <p>No timing data yet. Run the pipeline first.</p>
  if (latency.status !== 'ok') {
    return <p className="muted">Timing comparison unavailable: {latency.reason || latency.status}</p>
  }

  return (
    <div>
      <p className="muted">
        ML timing depends on classification source: live model inference is slower than warm-cache reuse.
      </p>
      <table>
        <thead>
          <tr>
            <th>Pipeline</th>
            <th>Time to Semantic (ms)</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>ML-Assisted</td>
            <td>{latency.ml?.to_semantic_ms}</td>
          </tr>
          <tr>
            <td>Traditional</td>
            <td>{latency.traditional?.to_semantic_ms}</td>
          </tr>
        </tbody>
      </table>
      <p>
        <strong>Faster:</strong> {latency.faster} | <strong>Difference:</strong> {latency.difference_ms} ms |
        <strong> Speedup:</strong> {latency.speedup_percent_vs_traditional}%
      </p>
      <p>
        <strong>ML Classification Source:</strong> {latency.ml?.classification_source || 'unknown'}
      </p>
    </div>
  )
}

function MLModelCard() {
  const architectureSteps = useMemo(
    () => [
      {
        title: '1. Tokenizer',
        description:
          "Custom character-aware function (c_tokenizer) that splits code into syntax-aware tokens (->, *, &, identifiers, etc.).",
      },
      {
        title: '2. Vectorizer (TF-IDF)',
        description:
          'Converts tokens into a 5000-feature numerical vector, using unigrams, bigrams, and trigrams to capture structure.',
      },
      {
        title: '3. Classifier (Random Forest)',
        description:
          'A Random Forest with 300 estimators makes the final prediction. It is trained on a balanced dataset to handle class variety.',
      },
    ],
    []
  )

  const metrics = useMemo(
    () => [
      { label: 'Dataset', value: ML_METRICS.datasetSize },
      { label: 'Test Accuracy', value: ML_METRICS.testAcc, strong: true },
      { label: 'Cross-Validation', value: '0.9578 (5-fold stratified)' },
    ],
    []
  )

  return (
    <article className="ml-model-card" aria-label="ML Statement Classification Model">
      <header className="ml-model-card-header">
        <p className="ml-model-kicker">Model Overview</p>
        <h3>ML Statement Classification Model</h3>
      </header>

      <section className="ml-model-section">
        <h4>Overview</h4>
        <div className="ml-kv-grid">
          <div className="ml-kv-item">
            <span className="ml-kv-label">Model Pipeline</span>
            <span className="ml-kv-value mono">TfidfVectorizer + RandomForestClassifier</span>
          </div>
          <div className="ml-kv-item">
            <span className="ml-kv-label">Purpose</span>
            <span className="ml-kv-value">
              To classify C/C++ code statements into one of 15 categories (e.g., Loop, Assignment, Conditional).
            </span>
          </div>
        </div>
      </section>

      <section className="ml-model-section">
        <h4>How It Works</h4>
        <div className="ml-steps">
          {architectureSteps.map((step) => (
            <article className="ml-step" key={step.title}>
              <h5>{step.title}</h5>
              <p>{step.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="ml-model-section">
        <h4>Performance</h4>
        <ul className="ml-metrics">
          {metrics.map((m) => (
            <li key={m.label} className="ml-metric-row">
              <span className="ml-metric-label">{m.label}</span>
              <span className={m.strong ? 'ml-metric-value strong' : 'ml-metric-value'}>{m.value}</span>
            </li>
          ))}
        </ul>
      </section>
    </article>
  )
}

function KnowMoreView() {
  return (
    <div className="know-more-wrap">
      <MLModelCard />

      <h3>Classification Report Highlights</h3>
      <ul className="issue-list">
        {ML_METRICS.notable.map((item, idx) => (
          <li key={idx}>{item}</li>
        ))}
      </ul>

      <details>
        <summary>ML Training Log (training_log.txt)</summary>
        <pre className="tall">{ML_TRAINING_LOG}</pre>
      </details>
    </div>
  )
}

function FAQView() {
  const faqItems = [
    {
      question: 'What model is used for statement classification?',
      answer: 'TF-IDF vectorizer + RandomForest classifier, trained on 15 statement categories.',
    },
    {
      question: 'How accurate is the ML model?',
      answer: 'Test accuracy is 96.07%, and 5-fold CV is 0.9578 ± 0.0027.',
    },
    {
      question: 'Why does the LLM run only sometimes?',
      answer:
        'The LLM is triggered only when semantic issues are found. If the semantic status is OK, the LLM is skipped.',
    },
    {
      question: 'Why do some examples show no semantic errors?',
      answer: 'Some examples are syntactically and semantically valid, so the analyzer reports no issues.',
    },
    {
      question: 'What does each phase do?',
      points: [
        'Lexer tokenizes code.',
        'Parser builds the AST.',
        'ML classifies statements.',
        'Semantic analyzer checks scope/type rules.',
        'LLM provides feedback on errors.',
      ],
    },
  ]

  return (
    <div className="faq-wrap">
      <h3>Frequently Asked Questions</h3>
      <div className="faq-grid">
        {faqItems.map((item, idx) => (
          <article className="faq-card" key={item.question}>
            <div className="faq-card-header">
              <span className="faq-index">{idx + 1}</span>
              <h4>{item.question}</h4>
            </div>
            {item.points ? (
              <ul>
                {item.points.map((point) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
            ) : (
              <p>{item.answer}</p>
            )}
          </article>
        ))}
      </div>
    </div>
  )
}

function SemanticView({ semantic }) {
  if (!semantic) return <p>No semantic report yet.</p>

  const issues = semantic.issues || []
  const symbols = semantic.symbol_table || []

  return (
    <div className="semantic-wrap">
      <div className={`badge ${semantic.status === 'ok' ? 'ok' : 'error'}`}>
        Status: {semantic.status?.toUpperCase()}
      </div>

      <h3>Issues</h3>
      {issues.length === 0 ? (
        <p className="muted">No semantic issues found.</p>
      ) : (
        <ul className="issue-list">
          {issues.map((issue, idx) => (
            <li key={idx}>
              <strong>{issue.level?.toUpperCase()}:</strong> {issue.message}
              <span className="node-chip">{issue.node_type}</span>
            </li>
          ))}
        </ul>
      )}

      <h3>Symbol Table</h3>
      {symbols.length === 0 ? (
        <p className="muted">No symbols recorded.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Scope</th>
            </tr>
          </thead>
          <tbody>
            {symbols.map((s, i) => (
              <tr key={`${s.name}-${i}`}>
                <td>{s.name}</td>
                <td>{s.type}</td>
                <td>{s.scope_level}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

function LLMView({ llm }) {
  if (!llm) return <p>No LLM feedback yet.</p>

  if (llm.status !== 'ok') {
    return (
      <div className="llm-fallback">
        <div className="badge warn">Status: {String(llm.status).toUpperCase()}</div>
        <p>{llm.reason || 'LLM response unavailable.'}</p>
      </div>
    )
  }

  const responseText = llm.result_text || 'No LLM response text available.'
  const correctedCode = llm.corrected_code || ''
  const statementSuggestions = llm.statement_suggestions || []

  return (
    <div className="llm-wrap">
      <div className="badge ok">Status: OK</div>
      <p><strong>Model:</strong> {llm.model || 'Gemini'}</p>

      <h3>Intelligent Explanation + Suggestions</h3>
      <pre>{responseText}</pre>

      {statementSuggestions.length > 0 && (
        <>
          <h3>Suggested New Statements</h3>
          <pre>{statementSuggestions.join('\n')}</pre>
        </>
      )}

      {correctedCode && (
        <>
          <h3>Suggested Corrected Code</h3>
          <pre>{correctedCode}</pre>
        </>
      )}
    </div>
  )
}
