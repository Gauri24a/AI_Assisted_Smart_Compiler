import React from 'react'
import { useEffect, useMemo, useState } from 'react'

const API_BASE = 'http://127.0.0.1:8000'

export default function App() {
  const [files, setFiles] = useState([])
  const [selectedPath, setSelectedPath] = useState('')
  const [isRunning, setIsRunning] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch(`${API_BASE}/api/files`)
      .then((res) => res.json())
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
      const res = await fetch(`${API_BASE}/api/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_path: selectedPath }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Run failed')
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

  return (
    <div className="page">
      <header>
        <h1>AI Assisted Smart Compiler</h1>
        <button disabled={!selectedPath || isRunning} onClick={runCompiler}>
          {isRunning ? 'Running...' : 'Run Pipeline'}
        </button>
      </header>

      {error && <div className="error">{error}</div>}

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
          <pre>{selectedFile?.content || 'Select a file...'}</pre>
        </main>
      </section>

      <section className="panel">
        <h2>Phase Outputs</h2>
        <div className="grid">
          <Phase title="Lexical Analysis" body={result?.phase_logs?.lexer} />
          <Phase title="Syntax Analysis" body={result?.phase_logs?.parser} />
          <Phase title="ML Classification" body={result?.phase_logs?.classification} />
          <Phase title="Semantic Analysis" body={result?.phase_logs?.semantic} />
          <Phase title="LLM Layer" body={result?.phase_logs?.llm || 'Not triggered'} />
        </div>
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
        <pre>{result?.stdout || 'No run yet.'}</pre>
      </section>
    </div>
  )
}

function Phase({ title, body }) {
  return (
    <article className="phase">
      <h3>{title}</h3>
      <pre>{body || 'No output yet.'}</pre>
    </article>
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

  return (
    <div className="llm-wrap">
      <div className="badge ok">Status: OK</div>
      <p><strong>Model:</strong> {llm.model || 'Gemini'}</p>

      <h3>Intelligent Explanation + Suggestions</h3>
      <pre>{responseText}</pre>

      {correctedCode && (
        <>
          <h3>Suggested Corrected Code</h3>
          <pre>{correctedCode}</pre>
        </>
      )}
    </div>
  )
}
