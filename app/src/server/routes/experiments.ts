import { Router } from 'express';
import { ExperimentService } from '../services/ExperimentService.js';
import { WorkflowGenerator } from '../services/WorkflowGenerator.js';
import { ArgoService } from '../services/ArgoService.js';

const router = Router();
const experimentService = new ExperimentService();
const workflowGenerator = new WorkflowGenerator();
const argoService = new ArgoService();

// Create experiment workflow
router.post('/', async (req, res) => {
  try {
    const config = req.body;
    const workflow = workflowGenerator.generateWorkflow(config);
    const workflowFile = await experimentService.saveWorkflow(workflow, config.name);
    
    res.json({
      success: true,
      data: { workflowFile }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to create experiment'
    });
  }
});

// Run existing workflow
router.post('/run', async (req, res) => {
  try {
    const { workflowFile } = req.body;
    const workflowName = await argoService.submitWorkflow(workflowFile);
    
    res.json({
      success: true,
      data: { workflowName }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to run experiment'
    });
  }
});

// Create and run experiment
router.post('/create-and-run', async (req, res) => {
  try {
    const config = req.body;
    const workflow = workflowGenerator.generateWorkflow(config);
    const workflowFile = await experimentService.saveWorkflow(workflow, config.name);
    const workflowName = await argoService.submitWorkflow(workflowFile);
    
    res.json({
      success: true,
      data: { workflowName, workflowFile }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to create and run experiment'
    });
  }
});

// List experiments
router.get('/', async (req, res) => {
  try {
    const experiments = await argoService.listWorkflows();
    
    res.json({
      success: true,
      data: experiments
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to list experiments'
    });
  }
});

// Get experiment status
router.get('/:name', async (req, res) => {
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
      error: error instanceof Error ? error.message : 'Failed to get experiment status'
    });
  }
});

// Stop experiment
router.delete('/:name', async (req, res) => {
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
      error: error instanceof Error ? error.message : 'Failed to stop experiment'
    });
  }
});

// Get experiment logs
router.get('/:name/logs', async (req, res) => {
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
      error: error instanceof Error ? error.message : 'Failed to get experiment logs'
    });
  }
});

export { router as experimentRoutes };
