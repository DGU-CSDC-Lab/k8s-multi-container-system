import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useExperimentApi } from '../hooks/useApi'
import { showNotification } from '../utils/notifications'

const DockerBuilderPage = () => {
  const { buildDockerImage, searchDockerImages, loading } = useExperimentApi()
  
  const [formData, setFormData] = useState({
    name: '',
    baseImage: '',
    requirements: '',
    workdir: '/workspace',
  })
  
  const [images, setImages] = useState([])
  const [showDropdown, setShowDropdown] = useState(false)
  const [dockerCommands, setDockerCommands] = useState([])
  const [currentCommand, setCurrentCommand] = useState({ command: 'RUN', value: '' })
  const [requirementsFile, setRequirementsFile] = useState(null)
  const [draggedIndex, setDraggedIndex] = useState(null)
  const [buildOutput, setBuildOutput] = useState('')
  const [showBuildOutput, setShowBuildOutput] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [previewDockerfile, setPreviewDockerfile] = useState('')

  const handleDragStart = (e, index) => {
    setDraggedIndex(index)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  const handleDrop = (e, dropIndex) => {
    e.preventDefault()
    
    if (draggedIndex === null || draggedIndex === dropIndex) return
    
    setDockerCommands(prev => {
      const newCommands = [...prev]
      const draggedItem = newCommands[draggedIndex]
      
      // Remove dragged item
      newCommands.splice(draggedIndex, 1)
      
      // Insert at new position
      const insertIndex = draggedIndex < dropIndex ? dropIndex - 1 : dropIndex
      newCommands.splice(insertIndex, 0, draggedItem)
      
      return newCommands
    })
    
    setDraggedIndex(null)
  }

  const handleDragEnd = () => {
    setDraggedIndex(null)
  }

  const dockerCommandOptions = [
    'RUN', 'COPY', 'ADD', 'ENV', 'EXPOSE', 'WORKDIR', 'USER', 'VOLUME', 'LABEL', 'ARG', 'ENTRYPOINT', 'CMD'
  ]

  useEffect(() => {
    searchImages('')
  }, [])

  const searchImages = async (query = '') => {
    try {
      const response = await searchDockerImages(query)
      if (response.success && response.data) {
        const actualData = response.data.data || response.data
        setImages(Array.isArray(actualData) ? actualData : [])
      }
    } catch (error) {
      console.error('Failed to search images:', error)
    }
  }

  const normalizeImageName = (name) => {
    return name
      .toLowerCase()
      .replace(/\s+/g, '-')
      .replace(/[^a-z0-9\-_./]/g, '')
      .replace(/^[^a-z0-9]+/, '')
      .replace(/--+/g, '-')
      .replace(/-+$/, '')
      .substring(0, 128)
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    
    if (name === 'name') {
      const normalized = normalizeImageName(value)
      setFormData(prev => ({ ...prev, [name]: normalized }))
    } else {
      setFormData(prev => ({ ...prev, [name]: value }))
    }
    
    if (name === 'baseImage') {
      searchImages(value)
      setShowDropdown(true)
    }
  }

  const selectImage = (image) => {
    setFormData(prev => ({ ...prev, baseImage: image }))
    setShowDropdown(false)
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (file) {
      try {
        const text = await file.text()
        setFormData(prev => ({ ...prev, requirements: text }))
        setRequirementsFile(file)
        showNotification('Requirements file loaded successfully!', 'success')
      } catch (error) {
        showNotification('Failed to read requirements file', 'error')
      }
    }
  }

  const addDockerCommand = () => {
    if (!currentCommand.value.trim()) {
      showNotification('Please enter command arguments', 'error')
      return
    }
    
    setDockerCommands(prev => [...prev, { ...currentCommand }])
    setCurrentCommand({ command: 'RUN', value: '' })
  }

  const removeCommand = (index) => {
    setDockerCommands(prev => prev.filter((_, i) => i !== index))
  }

  const moveCommand = (index, direction) => {
    const newIndex = index + direction
    if (newIndex < 0 || newIndex >= dockerCommands.length) return
    
    setDockerCommands(prev => {
      const newCommands = [...prev]
      ;[newCommands[index], newCommands[newIndex]] = [newCommands[newIndex], newCommands[index]]
      return newCommands
    })
  }

  const handleBuild = async () => {
    if (!formData.name || !formData.baseImage) {
      showNotification('Please enter image name and base image', 'error')
      return
    }

    try {
      setBuildOutput('🚀 Initializing Docker build...\n')
      setShowBuildOutput(true)
      
      const requirements = formData.requirements
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0)

      // Generate custom dockerfile if commands exist
      let dockerfile = undefined
      if (dockerCommands.length > 0) {
        dockerfile = generateDockerfile(
          formData.baseImage, 
          requirements, 
          dockerCommands, 
          formData.workdir,
          !!requirementsFile
        )
      }

      const config = {
        name: formData.name,
        baseImage: formData.baseImage,
        requirements,
        dockerfile
      }

      setBuildOutput(prev => prev + `📦 Image name: ${config.name}:latest\n`)
      setBuildOutput(prev => prev + `🐳 Base image: ${config.baseImage}\n`)
      
      if (requirements.length > 0) {
        setBuildOutput(prev => prev + `📋 Requirements: ${requirements.join(', ')}\n`)
      }
      
      if (dockerCommands.length > 0) {
        setBuildOutput(prev => prev + `⚙️  Custom commands: ${dockerCommands.length} commands\n`)
      }
      
      setBuildOutput(prev => prev + '\n🔨 Starting Docker build...\n\n')

      const response = await buildDockerImage(config)
      
      if (response.success) {
        // 서버에서 받은 빌드 로그 표시
        if (response.data?.buildLog) {
          setBuildOutput(prev => prev + response.data.buildLog + '\n')
        }
        
        setBuildOutput(prev => prev + `\n🎉 Build completed successfully!\n`)
        setBuildOutput(prev => prev + `📦 Image created: ${response.data?.imageName}\n`)
        setBuildOutput(prev => prev + `\n✅ You can now use this image in your experiments.\n`)
        showNotification(`Docker image built successfully: ${response.data?.imageName}`, 'success')
      } else {
        setBuildOutput(prev => prev + `\n❌ Build failed!\n`)
        setBuildOutput(prev => prev + `Error: ${response.error}\n`)
        
        // 에러 응답에 빌드 로그가 있으면 표시
        if (response.buildLog) {
          setBuildOutput(prev => prev + '\n--- Build Log ---\n')
          setBuildOutput(prev => prev + response.buildLog + '\n')
        }
        
        showNotification(`Build failed: ${response.error}`, 'error')
      }
    } catch (error) {
      setBuildOutput(prev => prev + `\n💥 Build error occurred!\n`)
      setBuildOutput(prev => prev + `Error: ${error.message}\n`)
      
      // 에러 객체에 빌드 로그가 있으면 표시
      if (error.response?.data?.buildLog) {
        setBuildOutput(prev => prev + '\n--- Error Details ---\n')
        setBuildOutput(prev => prev + error.response.data.buildLog + '\n')
      }
      
      showNotification(`Build failed: ${error.message}`, 'error')
    }
  }

  const handlePreview = () => {
    const requirements = formData.requirements
      .split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 0)

    const dockerfile = generateDockerfile(
      formData.baseImage, 
      requirements, 
      dockerCommands, 
      formData.workdir,
      !!requirementsFile
    )
    setPreviewDockerfile(dockerfile)
    setShowPreview(true)
  }

  const getImageCategory = (image) => {
    if (image.includes('cuda')) return 'CUDA'
    if (image.includes('pytorch')) return 'PyTorch'
    if (image.includes('tensorflow')) return 'TensorFlow'
    if (image.includes('jupyter')) return 'Jupyter'
    if (image.includes('python')) return 'Python'
    return 'Other'
  }

  const generateDockerfile = (baseImage, requirements, commands, workdir = '/workspace', hasRequirementsFile = false) => {
    let dockerfile = `FROM ${baseImage || 'python:3.8'}\n\n`
    dockerfile += `ENV DEBIAN_FRONTEND=noninteractive\n\n`

    // System dependencies based on base image
    if (baseImage && (baseImage.includes('ubuntu') || baseImage.includes('debian'))) {
      dockerfile += `RUN apt-get update && apt-get install -y \\\n`
      dockerfile += `    python3-pip python3-dev \\\n`
      dockerfile += `    git curl wget unzip nano vim \\\n`
      dockerfile += `    build-essential \\\n`
      dockerfile += `    && apt-get clean \\\n`
      dockerfile += `    && rm -rf /var/lib/apt/lists/*\n\n`
    }

    // Python setup for non-python base images
    if (baseImage && !baseImage.includes('python') && !baseImage.includes('pytorch') && !baseImage.includes('tensorflow')) {
      dockerfile += `RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1\n`
      dockerfile += `RUN pip3 install --upgrade pip setuptools wheel\n\n`
    }

    // CUDA/GPU specific setup
    if (baseImage && baseImage.includes('cuda')) {
      dockerfile += `# CUDA environment setup\n`
      dockerfile += `ENV CUDA_HOME=/usr/local/cuda\n`
      dockerfile += `ENV PATH=$CUDA_HOME/bin:$PATH\n`
      dockerfile += `ENV LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH\n\n`
    }

    // Set working directory
    dockerfile += `WORKDIR ${workdir}\n`
    dockerfile += `COPY . ${workdir}/\n\n`

    // Install requirements.txt first if file was uploaded
    if (hasRequirementsFile) {
      dockerfile += `# Install requirements from uploaded file\n`
      dockerfile += `RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; fi\n\n`
    }

    // Custom commands from user
    if (commands && commands.length > 0) {
      dockerfile += `# Custom commands\n`
      commands.forEach(cmd => {
        if (cmd.command === 'ENTRYPOINT' || cmd.command === 'CMD') {
          // Convert comma-separated values to JSON array format
          const values = cmd.value.split(',').map(v => v.trim()).filter(v => v)
          const jsonArray = JSON.stringify(values)
          dockerfile += `${cmd.command} ${jsonArray}\n`
        } else {
          dockerfile += `${cmd.command} ${cmd.value}\n`
        }
      })
      dockerfile += `\n`
    }

    // Install additional Python requirements (manual entry)
    if (requirements && requirements.length > 0) {
      dockerfile += `# Install additional Python packages\n`
      dockerfile += `RUN pip install --no-cache-dir \\\n`
      requirements.forEach((req, index) => {
        const isLast = index === requirements.length - 1
        dockerfile += `    ${req}${isLast ? '\n\n' : ' \\\n'}`
      })
    }

    // Install project dependencies
    dockerfile += `# Install project dependencies\n`
    dockerfile += `RUN if [ -f setup.py ]; then pip install -e .; fi\n\n`

    // Default entry point and cmd if not specified in custom commands
    const hasEntrypoint = commands?.some(cmd => cmd.command === 'ENTRYPOINT')
    const hasCmd = commands?.some(cmd => cmd.command === 'CMD')
    
    if (!hasEntrypoint || !hasCmd) {
      dockerfile += `# Default entry point\n`
      if (!hasEntrypoint) {
        dockerfile += `ENTRYPOINT ["/bin/bash", "-c"]\n`
      }
      if (!hasCmd) {
        dockerfile += `CMD ["python auto_protogcn.py"]\n`
      }
    }

    return dockerfile
  }

  return (
    <div className="docker-builder-page">
      <div className="row">
        <div className="col-12">
          <nav aria-label="breadcrumb">
            <ol className="breadcrumb">
              <li className="breadcrumb-item"><Link to="/">Dashboard</Link></li>
              <li className="breadcrumb-item active">Docker Builder</li>
            </ol>
          </nav>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h5 className="mb-0">🐳 Docker Image Builder</h5>
        </div>
        <div className="card-body">
          <div className="row mb-3">
            <div className="col-md-6">
              <label className="form-label">Image Name</label>
              <input
                type="text"
                className="form-control"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                placeholder="research-experiment"
                required
              />
            </div>
            <div className="col-md-6">
              <label className="form-label">Base Image</label>
              <div className="position-relative">
                <div className="input-group">
                  <input
                    type="text"
                    className="form-control"
                    name="baseImage"
                    value={formData.baseImage}
                    onChange={handleInputChange}
                    placeholder="Search or enter image name..."
                  />
                </div>
                {showDropdown && images.length > 0 && (
                  <div className="dropdown-menu show w-100" style={{maxHeight: '200px', overflowY: 'auto', position: 'absolute', top: '100%', zIndex: 1000}}>
                    {images.slice(0, 10).map((image, index) => (
                      <button
                        key={index}
                        className="dropdown-item"
                        onClick={() => selectImage(image)}
                      >
                        <div className="d-flex justify-content-between align-items-center">
                          <span>{image}</span>
                          <small className="text-muted">{getImageCategory(image)}</small>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Requirements File Upload */}
          <div className="mb-3">
            <label className="form-label">Requirements File</label>
            <input
              type="file"
              className="form-control"
              accept=".txt"
              onChange={handleFileUpload}
            />
            <div className="form-text">Upload requirements.txt file or use manual entry below</div>
          </div>
          
          {/* Working Directory */}
          <div className="mb-3">
            <label className="form-label">Working Directory</label>
            <input
              type="text"
              className="form-control"
              name="workdir"
              value={formData.workdir}
              onChange={handleInputChange}
              placeholder="/workspace"
            />
            <div className="form-text">Directory where your application will run</div>
          </div>

          {/* Docker Commands Builder */}
          <div className="mb-3">
            <label className="form-label">Custom Dockerfile Commands</label>
            <div>
                <div className="row align-items-end mb-2">
                  <div className="col-3">
                    <select
                      className="form-control"
                      value={currentCommand.command}
                      onChange={(e) => setCurrentCommand(prev => ({ ...prev, command: e.target.value }))}
                    >
                      {dockerCommandOptions.map(cmd => (
                        <option key={cmd} value={cmd}>{cmd}</option>
                      ))}
                    </select>
                  </div>
                  <div className="col-7">
                    <input
                      type="text"
                      className="form-control"
                      placeholder={
                        currentCommand.command === 'ENTRYPOINT' ? 'e.g., /bin/bash, -c (comma-separated)' :
                        currentCommand.command === 'CMD' ? 'e.g., python, app.py (comma-separated)' :
                        'Enter command arguments...'
                      }
                      value={currentCommand.value}
                      onChange={(e) => setCurrentCommand(prev => ({ ...prev, value: e.target.value }))}
                      onKeyPress={(e) => e.key === 'Enter' && addDockerCommand()}
                    />
                    {(currentCommand.command === 'ENTRYPOINT' || currentCommand.command === 'CMD') && (
                      <div className="form-text">Use comma-separated values for array format: ["value1", "value2"]</div>
                    )}
                  </div>
                  <div className="col-2">
                    <button
                      type="button"
                      className="btn btn-outline-primary btn-sm w-100 d-flex align-items-center justify-content-center"
                      onClick={addDockerCommand}
                      style={{ height: '38px' }}
                    >
                      <i className="fas fa-plus"></i>
                    </button>
                  </div>
                </div>
                
                <div className="">
                  {dockerCommands.length === 0 ? (
                    <div className="text-muted"></div>
                  ) : (
                    dockerCommands.map((cmd, index) => (
                      <div
                        key={index}
                        className={`d-flex align-items-center mb-2 p-2 rounded docker-command-item ${
                          draggedIndex === index ? 'bg-primary bg-opacity-25' : 'bg-light'
                        }`}
                        draggable
                        onDragStart={(e) => handleDragStart(e, index)}
                        onDragOver={handleDragOver}
                        onDrop={(e) => handleDrop(e, index)}
                        onDragEnd={handleDragEnd}
                        style={{ 
                          cursor: 'move',
                          border: draggedIndex === index ? '2px dashed #0d6efd' : '1px solid transparent'
                        }}
                      >
                        <div className="me-2">
                          <i className="fas fa-grip-vertical text-muted"></i>
                        </div>
                        <div className="flex-grow-1">
                          <span className="badge bg-primary me-2">{cmd.command}</span>
                          <code>{cmd.value}</code>
                        </div>
                        <div className="ms-2">
                          <button
                            className="btn btn-outline-danger btn-sm"
                            onClick={() => removeCommand(index)}
                          >
                            <i className="fas fa-trash"></i>
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
            </div>
          </div>

          <div className="d-flex gap-2">
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleBuild}
              disabled={loading}
            >
              {loading && <span className="spinner-border spinner-border-sm me-2"></span>}
              Build Image
            </button>
            <button
              type="button"
              className="btn btn-outline-secondary"
              onClick={handlePreview}
            >
              Preview Dockerfile
            </button>
            {showBuildOutput && (
              <button
                type="button"
                className="btn btn-outline-info"
                onClick={() => setShowBuildOutput(false)}
              >
                Hide Build Log
              </button>
            )}
          </div>

          {/* Build Output */}
          {showBuildOutput && (
            <div className="mt-4">
              <div className="card">
                <div className="card-header d-flex justify-content-between align-items-center">
                  <h6 className="mb-0">🔨 Build Output</h6>
                  <button
                    className="btn btn-outline-secondary btn-sm"
                    onClick={() => setBuildOutput('')}
                  >
                    Clear
                  </button>
                </div>
                <div className="card-body">
                  <pre 
                    className="bg-dark text-light p-3 rounded" 
                    style={{maxHeight: '400px', overflowY: 'auto', fontSize: '0.875rem'}}
                  >
                    {buildOutput || 'No build output yet...'}
                  </pre>
                </div>
              </div>
            </div>
          )}

          {/* Dockerfile Preview Modal */}
          {showPreview && (
            <div className="modal fade show d-block" style={{backgroundColor: 'rgba(0,0,0,0.5)'}}>
              <div className="modal-dialog modal-lg">
                <div className="modal-content">
                  <div className="modal-header">
                    <h5 className="modal-title">Dockerfile Preview</h5>
                    <button
                      type="button"
                      className="btn-close"
                      onClick={() => setShowPreview(false)}
                    ></button>
                  </div>
                  <div className="modal-body">
                    <pre 
                      className="bg-light p-3 rounded" 
                      style={{maxHeight: '500px', overflowY: 'auto', fontSize: '0.875rem'}}
                    >
                      {previewDockerfile}
                    </pre>
                  </div>
                  <div className="modal-footer">
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => setShowPreview(false)}
                    >
                      Close
                    </button>
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={() => {
                        navigator.clipboard.writeText(previewDockerfile)
                        showNotification('Dockerfile copied to clipboard!', 'success')
                      }}
                    >
                      Copy to Clipboard
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default DockerBuilderPage
