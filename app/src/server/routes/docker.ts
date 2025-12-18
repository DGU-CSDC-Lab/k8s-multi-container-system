import { Router } from 'express';
import { DockerService } from '../services/DockerService.js';

const router = Router();
const dockerService = new DockerService();

// Build Docker image
router.post('/build', async (req, res) => {
  try {
    const config = req.body;
    const imageName = await dockerService.buildImage(config);
    
    res.json({
      success: true,
      data: { imageName }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to build Docker image'
    });
  }
});

// Search Docker images
router.get('/images/search', async (req, res) => {
  try {
    const query = req.query.q as string || '';
    const images = await dockerService.searchImages(query);
    
    res.json({
      success: true,
      data: images
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to search Docker images'
    });
  }
});

// List Docker images
router.get('/images', async (req, res) => {
  try {
    const images = await dockerService.listImages();
    
    res.json({
      success: true,
      data: images
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to list Docker images'
    });
  }
});

// Remove Docker image
router.delete('/images/:name', async (req, res) => {
  try {
    const { name } = req.params;
    await dockerService.removeImage(name);
    
    res.json({
      success: true,
      data: null
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to remove Docker image'
    });
  }
});

export { router as dockerRoutes };
