import { useState } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [user, setUser] = useState('')
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploadResult, setUploadResult] = useState('')
  const [workflowResult, setWorkflowResult] = useState('')
  const [summary, setSummary] = useState('')

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!user || files.length === 0) return

    setLoading(true)
    const formData = new FormData()
    formData.append('user', user)
    Array.from(files).forEach(file => formData.append('files', file))

    try {
      const response = await axios.post('/upload-multi', formData)
      setUploadResult(`✅ 업로드 완료: ${response.data.files.join(', ')}`)
    } catch (error) {
      setUploadResult(`❌ 업로드 실패: ${error.message}`)
    }
    setLoading(false)
  }

  const runWorkflow = async () => {
    if (!user) return
    
    setLoading(true)
    const formData = new FormData()
    formData.append('user', user)

    try {
      const response = await axios.post('/run', formData)
      setWorkflowResult(response.data.status === 'submitted' 
        ? '✅ 워크플로우 실행됨' 
        : `❌ 실행 실패: ${response.data.stderr || response.data.message}`)
    } catch (error) {
      setWorkflowResult(`❌ 실행 실패: ${error.message}`)
    }
    setLoading(false)
  }

  const loadSummary = async () => {
    if (!user) return

    try {
      const response = await axios.get(`/summary/${user}`)
      setSummary(response.data)
    } catch (error) {
      setSummary('❌ 요약을 찾을 수 없습니다.')
    }
  }

  return (
    <div className="container">
      <div className="card">
        <h1>🧠 ProtoGCN Workflow</h1>
        <p className="subtitle">Kubernetes 기반 머신러닝 파이프라인</p>

        <div className="step">
          <h3>1️⃣ 사용자 ID</h3>
          <input
            type="text"
            placeholder="영문 이름을 입력하세요"
            value={user}
            onChange={(e) => setUser(e.target.value)}
            className="input"
          />
        </div>

        <div className="step">
          <h3>2️⃣ 파일 업로드</h3>
          <form onSubmit={handleUpload}>
            <input
              type="file"
              multiple
              accept=".pkl"
              onChange={(e) => setFiles(e.target.files)}
              className="file-input"
            />
            <button type="submit" disabled={loading || !user} className="btn primary">
              {loading ? '업로드 중...' : '업로드'}
            </button>
          </form>
          {uploadResult && <div className="result">{uploadResult}</div>}
        </div>

        <div className="step">
          <h3>3️⃣ 워크플로우 실행</h3>
          <p className="info">Argo UI: http://192.168.0.62:2749</p>
          <button onClick={runWorkflow} disabled={loading || !user} className="btn success">
            {loading ? '실행 중...' : '🚀 Run'}
          </button>
          {workflowResult && <div className="result">{workflowResult}</div>}
        </div>

        <div className="step">
          <h3>4️⃣ 결과 다운로드</h3>
          <button onClick={loadSummary} disabled={!user} className="btn secondary">
            📊 요약 로드
          </button>
          {summary && (
            <div className="summary">
              <pre>{summary}</pre>
              <a 
                href={`data:text/csv;charset=utf-8,${encodeURIComponent(summary)}`}
                download={`${user}_summary.csv`}
                className="download-link"
              >
                💾 CSV 다운로드
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
