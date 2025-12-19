import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { useExperimentApi } from '../hooks/useApi'
import { showNotification } from '../utils/notifications'

const CreateExperimentPage = () => {
  const { createAndRunExperiment, createExperiment, loading } = useExperimentApi()
  
  const [formData, setFormData] = useState({
    name: '',
    image: 'proto-gcn:latest',
    command: './monitor_training.sh configs/ntu60_xsub/bm.py bm_single',
    envVars: {
      'MASTER_ADDR': '127.0.0.1',
      'MASTER_PORT': '12355',
      'CUDA_MPS_ACTIVE_THREAD_PERCENTAGE': '50'
    },
    resources: {
      gpuCount: 1,
      cpuCores: '4',
      memory: '8Gi',
      parallelJobs: 1
    }
  })

  const [envVars, setEnvVars] = useState([
    { name: 'MASTER_ADDR', value: '127.0.0.1' },
    { name: 'MASTER_PORT', value: '12355' },
    { name: 'CUDA_MPS_ACTIVE_THREAD_PERCENTAGE', value: '50' }
  ])

  const handleInputChange = (e) => {
    const { name, value } = e.target
    if (name.startsWith('resources.')) {
      const resourceKey = name.split('.')[1]
      setFormData(prev => ({
        ...prev,
        resources: { ...prev.resources, [resourceKey]: value }
      }))
    } else {
      setFormData(prev => ({ ...prev, [name]: value }))
    }
  }

  const addEnvVar = () => {
    setEnvVars([...envVars, { name: '', value: '' }])
  }

  const removeEnvVar = (index) => {
    setEnvVars(envVars.filter((_, i) => i !== index))
  }

  const updateEnvVar = (index, field, value) => {
    const updated = [...envVars]
    updated[index][field] = value
    setEnvVars(updated)
  }

  const handleSubmit = async (runImmediately = false) => {
    try {
      const envVarsObj = {}
      envVars.forEach(env => {
        if (env.name && env.value) {
          envVarsObj[env.name] = env.value
        }
      })

      const config = {
        ...formData,
        envVars: envVarsObj
      }

      if (runImmediately) {
        const response = await createAndRunExperiment(config)
        if (response.success) {
          showNotification(`Experiment "${config.name}" started successfully!`, 'success')
        }
      } else {
        const response = await createExperiment(config)
        if (response.success) {
          showNotification(`Workflow created: ${response.data?.workflowFile}`, 'success')
        }
      }
    } catch (error) {
      showNotification(`Error: ${error.message}`, 'error')
    }
  }

  return (
    <div className="create-experiment-page">
      <div className="row">
        <div className="col-12">
          <nav aria-label="breadcrumb">
            <ol className="breadcrumb">
              <li className="breadcrumb-item"><Link to="/">Dashboard</Link></li>
              <li className="breadcrumb-item active">Create Experiment</li>
            </ol>
          </nav>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h5 className="mb-0">🚀 Create New Experiment</h5>
        </div>
        <div className="card-body">
          {/* Basic Information */}
          <div className="mb-4">
            <h6 className="text-primary">Basic Information</h6>
            <div className="row">
              <div className="col-md-6 mb-3">
                <label className="form-label">Experiment Name *</label>
                <input
                  type="text"
                  className="form-control"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                />
              </div>
              <div className="col-md-6 mb-3">
                <label className="form-label">Docker Image</label>
                <input
                  type="text"
                  className="form-control"
                  name="image"
                  value={formData.image}
                  onChange={handleInputChange}
                />
              </div>
            </div>
            <div className="mb-3">
              <label className="form-label">Command to Execute *</label>
              <textarea
                className="form-control"
                name="command"
                rows="2"
                value={formData.command}
                onChange={handleInputChange}
                required
              />
            </div>
          </div>

          {/* Environment Variables */}
          <div className="mb-4">
            <h6 className="text-primary">Environment Variables</h6>
            {envVars.map((envVar, index) => (
              <div key={index} className="row mb-2 env-var-row bg-light p-2 rounded">
                <div className="col-5">
                  <input
                    type="text"
                    className="form-control"
                    placeholder="Variable Name"
                    value={envVar.name}
                    onChange={(e) => updateEnvVar(index, 'name', e.target.value)}
                  />
                </div>
                <div className="col-5">
                  <input
                    type="text"
                    className="form-control"
                    placeholder="Value"
                    value={envVar.value}
                    onChange={(e) => updateEnvVar(index, 'value', e.target.value)}
                  />
                </div>
                <div className="col-2">
                  <button
                    type="button"
                    className="btn btn-outline-danger btn-sm"
                    onClick={() => removeEnvVar(index)}
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
            <button
              type="button"
              className="btn btn-outline-primary btn-sm"
              onClick={addEnvVar}
            >
              + Add Variable
            </button>
          </div>

          {/* Resource Configuration */}
          <div className="mb-4">
            <h6 className="text-primary">Resource Configuration</h6>
            <div className="row">
              <div className="col-md-3 mb-3">
                <label className="form-label">GPU Count</label>
                <select
                  className="form-control"
                  name="resources.gpuCount"
                  value={formData.resources.gpuCount}
                  onChange={handleInputChange}
                >
                  <option value="1">1 GPU</option>
                  <option value="2">2 GPUs</option>
                  <option value="4">4 GPUs</option>
                  <option value="8">8 GPUs</option>
                </select>
              </div>
              <div className="col-md-3 mb-3">
                <label className="form-label">CPU Cores</label>
                <input
                  type="text"
                  className="form-control"
                  name="resources.cpuCores"
                  value={formData.resources.cpuCores}
                  onChange={handleInputChange}
                />
              </div>
              <div className="col-md-3 mb-3">
                <label className="form-label">Memory</label>
                <input
                  type="text"
                  className="form-control"
                  name="resources.memory"
                  value={formData.resources.memory}
                  onChange={handleInputChange}
                />
              </div>
              <div className="col-md-3 mb-3">
                <label className="form-label">Parallel Jobs</label>
                <input
                  type="number"
                  className="form-control"
                  name="resources.parallelJobs"
                  value={formData.resources.parallelJobs}
                  onChange={handleInputChange}
                  min="1"
                  max="10"
                />
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="d-flex gap-2">
            <button
              type="button"
              className="btn btn-success"
              onClick={() => handleSubmit(true)}
              disabled={loading}
            >
              {loading && <span className="spinner-border spinner-border-sm me-2"></span>}
              Create & Run
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => handleSubmit(false)}
              disabled={loading}
            >
              Create Only
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CreateExperimentPage
