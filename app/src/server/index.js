const express = require('express');
const cors = require('cors');
const path = require('path');

// Services
const DockerService = require('./services/DockerService');
const ArgoService = require('./services/ArgoService');
const WorkflowGenerator = require('./services/WorkflowGenerator');
const ExperimentService = require('./services/ExperimentService');

const app = express();
const PORT = process.env.PORT || 3000;

// Initialize services
const dockerService = new DockerService();
const argoService = new ArgoService();
const workflowGenerator = new WorkflowGenerator();
const experimentService = new ExperimentService();

// Middleware
app.use(cors());
app.use(express.json());

// Serve static files only in production
if (process.env.NODE_ENV === 'production') {
  app.use(express.static(path.join(__dirname, '../../dist/client')));
}

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Experiment Routes
app.post('/api/experiments', async (req, res) => {
  try {
    const config = req.body;
    const workflow = workflowGenerator.generateWorkflow(config);
    const workflowFile = await experimentService.saveWorkflow(workflow, config.name);
    
    res.json({
      success: true,
      data: { workflowFile: path.basename(workflowFile) }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.post('/api/experiments/run', async (req, res) => {
  try {
    const { workflowFile } = req.body;
    const fullPath = path.join(process.cwd(), 'workflows', workflowFile);
    const workflowName = await argoService.submitWorkflow(fullPath);
    
    res.json({
      success: true,
      data: { workflowName }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.post('/api/experiments/create-and-run', async (req, res) => {
  try {
    const config = req.body;
    const workflow = workflowGenerator.generateWorkflow(config);
    const workflowFile = await experimentService.saveWorkflow(workflow, config.name);
    const workflowName = await argoService.submitWorkflow(workflowFile);
    
    res.json({
      success: true,
      data: { workflowName, workflowFile: path.basename(workflowFile) }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.get('/api/experiments', async (req, res) => {
  try {
    const experiments = await argoService.listWorkflows();
    
    res.json({
      success: true,
      data: experiments
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.get('/api/experiments/:name', async (req, res) => {
  try {
    const { name } = req.params;
    const status = await argoService.getWorkflowStatus(name);
    
    res.json({
      success: true,
      data: status
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.delete('/api/experiments/:name', async (req, res) => {
  try {
    const { name } = req.params;
    await argoService.stopWorkflow(name);
    
    res.json({
      success: true,
      data: null
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.get('/api/experiments/:name/logs', async (req, res) => {
  try {
    const { name } = req.params;
    const logs = await argoService.getWorkflowLogs(name);
    
    res.json({
      success: true,
      data: { logs }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Docker Routes
app.post('/api/docker/build', async (req, res) => {
  try {
    const config = req.body;
    const result = await dockerService.buildImage(config);
    
    res.json({
      success: true,
      data: {
        imageName: result.imageName,
        buildLog: result.buildLog,
        dockerfile: result.dockerfile
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message,
      buildLog: error.message // 에러도 빌드 로그로 포함
    });
  }
});

app.get('/api/docker/images', async (req, res) => {
  try {
    const images = await dockerService.listImages();
    
    res.json({
      success: true,
      data: images
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.get('/api/docker/images/search', async (req, res) => {
  try {
    const query = req.query.q || '';
    const images = await dockerService.searchImages(query);
    
    res.json({
      success: true,
      data: images
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Serve client app for all other routes (production only)
if (process.env.NODE_ENV === 'production') {
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '../../dist/client/index.html'));
  });
} else {
  app.get('/', (req, res) => {
    res.json({ 
      message: 'Research Workflow Manager API',
      frontend: 'http://localhost:8080',
      api: 'http://localhost:3000/api'
    });
  });
}

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({
    success: false,
    error: err.message || 'Internal server error'
  });
});

app.listen(PORT, () => {
  console.log(`🚀 Research Workflow Manager server running on port ${PORT}`);
  console.log(`📊 Dashboard: http://localhost:${PORT}`);
  console.log(`🔧 API: http://localhost:3000/api`);
  console.log(`🐳 Docker service initialized`);
  console.log(`⚡ Argo service initialized`);
});
