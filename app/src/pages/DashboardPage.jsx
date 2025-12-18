import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useExperimentApi } from '../hooks/useApi'

const DashboardPage = () => {
  const { listExperiments } = useExperimentApi()
  const [stats, setStats] = useState({
    running: 0,
    succeeded: 0,
    failed: 0,
    pending: 0
  })

  useEffect(() => {
    loadQuickStats()
  }, [])

  const loadQuickStats = async () => {
    try {
      const response = await listExperiments()
      if (response.success && response.data) {
        const experiments = response.data
        setStats({
          running: experiments.filter(e => e.status === 'Running').length,
          succeeded: experiments.filter(e => e.status === 'Succeeded').length,
          failed: experiments.filter(e => e.status === 'Failed' || e.status === 'Error').length,
          pending: experiments.filter(e => e.status === 'Pending').length
        })
      }
    } catch (error) {
      console.error('Failed to load quick stats:', error)
    }
  }

  return (
    <div className="dashboard-page">
      <div className="row">
        <div className="col-12">
          <div className="jumbotron bg-light p-5 rounded">
            <h1 className="display-4">🔬 Research Workflow Manager</h1>
            <p className="lead">Manage your machine learning experiments with ease</p>
            <hr className="my-4" />
            <p>Create, monitor, and manage your research experiments using Kubernetes and Argo Workflows.</p>
          </div>
        </div>
      </div>
      
      <div className="row mt-4">
        <div className="col-md-4 mb-4">
          <div className="card h-100 text-center">
            <div className="card-body">
              <div className="display-1 text-primary">🚀</div>
              <h5 className="card-title">Create Experiment</h5>
              <p className="card-text">Set up new experiments with custom environment variables and resource allocation</p>
              <Link to="/create" className="btn btn-primary">Get Started</Link>
            </div>
          </div>
        </div>
        
        <div className="col-md-4 mb-4">
          <div className="card h-100 text-center">
            <div className="card-body">
              <div className="display-1 text-success">📊</div>
              <h5 className="card-title">Monitor Experiments</h5>
              <p className="card-text">Track running experiments, view logs, and manage workflow status</p>
              <Link to="/monitor" className="btn btn-success">Monitor</Link>
            </div>
          </div>
        </div>
        
        <div className="col-md-4 mb-4">
          <div className="card h-100 text-center">
            <div className="card-body">
              <div className="display-1 text-info">🐳</div>
              <h5 className="card-title">Build Docker Images</h5>
              <p className="card-text">Create custom Docker images for your research environments</p>
              <Link to="/docker" className="btn btn-info">Build</Link>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="row mt-4">
        <div className="col-12">
          <div className="card">
            <div className="card-header">
              <h5 className="mb-0">Quick Stats</h5>
            </div>
            <div className="card-body">
              <div className="row text-center">
                <div className="col-md-3">
                  <div className="h3 text-primary">{stats.running}</div>
                  <div className="text-muted">Running</div>
                </div>
                <div className="col-md-3">
                  <div className="h3 text-success">{stats.succeeded}</div>
                  <div className="text-muted">Succeeded</div>
                </div>
                <div className="col-md-3">
                  <div className="h3 text-danger">{stats.failed}</div>
                  <div className="text-muted">Failed</div>
                </div>
                <div className="col-md-3">
                  <div className="h3 text-warning">{stats.pending}</div>
                  <div className="text-muted">Pending</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DashboardPage
