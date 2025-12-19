import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useExperimentApi } from '../hooks/useApi'

const MonitorPage = () => {
  const { listExperiments, stopExperiment, getExperimentLogs } = useExperimentApi()
  const [experiments, setExperiments] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadExperiments()
  }, [])

  const loadExperiments = async () => {
    setLoading(true)
    try {
      const response = await listExperiments()
      if (response.success && response.data) {
        setExperiments(response.data)
      }
    } catch (error) {
      console.error('Failed to load experiments:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleStop = async (name) => {
    if (!confirm(`Are you sure you want to stop experiment "${name}"?`)) return
    
    try {
      await stopExperiment(name)
      loadExperiments()
    } catch (error) {
      console.error('Failed to stop experiment:', error)
    }
  }

  const getStatusBadge = (status) => {
    const badges = {
      'Pending': 'warning',
      'Running': 'primary',
      'Succeeded': 'success',
      'Failed': 'danger',
      'Error': 'danger'
    }
    return badges[status] || 'secondary'
  }

  return (
    <div className="monitor-page">
      <div className="row">
        <div className="col-12">
          <nav aria-label="breadcrumb">
            <ol className="breadcrumb">
              <li className="breadcrumb-item"><Link to="/">Dashboard</Link></li>
              <li className="breadcrumb-item active">Monitor Experiments</li>
            </ol>
          </nav>
        </div>
      </div>

      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h5 className="mb-0">📊 Experiment Monitor</h5>
          <button className="btn btn-outline-primary btn-sm" onClick={loadExperiments} disabled={loading}>
            {loading && <span className="spinner-border spinner-border-sm me-2"></span>}
            Refresh
          </button>
        </div>
        <div className="card-body">
          {experiments.length === 0 ? (
            <div className="text-center text-muted">
              <p>No experiments found</p>
              <small>Create your first experiment to see it here</small>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Duration</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {experiments.map((exp) => (
                    <tr key={exp.name}>
                      <td><strong>{exp.name}</strong></td>
                      <td>
                        <span className={`badge bg-${getStatusBadge(exp.status)}`}>
                          {exp.status}
                        </span>
                      </td>
                      <td>
                        <small>{new Date(exp.createdAt).toLocaleString()}</small>
                      </td>
                      <td>
                        <small>{exp.duration || 'N/A'}</small>
                      </td>
                      <td>
                        <div className="btn-group btn-group-sm">
                          <button className="btn btn-outline-info">Logs</button>
                          {exp.status === 'Running' && (
                            <button 
                              className="btn btn-outline-danger"
                              onClick={() => handleStop(exp.name)}
                            >
                              Stop
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default MonitorPage
