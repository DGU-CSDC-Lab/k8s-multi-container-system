import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Navigation from './components/Navigation'
import DashboardPage from './pages/DashboardPage'
import CreateExperimentPage from './pages/CreateExperimentPage'
import MonitorPage from './pages/MonitorPage'
import DockerBuilderPage from './pages/DockerBuilderPage'
import './App.css'

function App() {
  return (
    <Router>
      <div className="app">
        <Navigation />
        <div className="container mt-4">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/create" element={<CreateExperimentPage />} />
            <Route path="/monitor" element={<MonitorPage />} />
            <Route path="/docker" element={<DockerBuilderPage />} />
          </Routes>
        </div>
        
        {/* Notifications Container */}
        <div id="notifications" className="position-fixed top-0 end-0 p-3" style={{zIndex: 1050}}></div>
      </div>
    </Router>
  )
}

export default App
