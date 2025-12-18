import { useState, useCallback } from 'react'
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export const useApi = () => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const request = useCallback(async (method, url, data = null) => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await api({ method, url, data })
      return response.data
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }, [])

  const get = useCallback((url) => request('GET', url), [request])
  const post = useCallback((url, data) => request('POST', url, data), [request])
  const put = useCallback((url, data) => request('PUT', url, data), [request])
  const del = useCallback((url) => request('DELETE', url), [request])

  return { loading, error, get, post, put, delete: del }
}

export const useExperimentApi = () => {
  const { loading, error, get, post, del } = useApi()

  return {
    loading,
    error,
    createExperiment: (config) => post('/experiments', config),
    runExperiment: (workflowFile) => post('/experiments/run', { workflowFile }),
    createAndRunExperiment: (config) => post('/experiments/create-and-run', config),
    listExperiments: () => get('/experiments'),
    getExperimentStatus: (name) => get(`/experiments/${name}`),
    stopExperiment: (name) => del(`/experiments/${name}`),
    getExperimentLogs: (name) => get(`/experiments/${name}/logs`),
    buildDockerImage: (config) => post('/docker/build', config),
    listDockerImages: () => get('/docker/images'),
    searchDockerImages: (query) => get(`/docker/images/search${query ? `?q=${query}` : ''}`),
  }
}
