import { Router } from 'express';
import { TemplateService } from '../services/TemplateService.js';

const router = Router();
const templateService = new TemplateService();

// Get all templates
router.get('/', async (req, res) => {
  try {
    const templates = await templateService.getAllTemplates();
    
    res.json({
      success: true,
      data: templates
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to get templates'
    });
  }
});

// Create template
router.post('/', async (req, res) => {
  try {
    const template = req.body;
    const savedTemplate = await templateService.saveTemplate(template);
    
    res.json({
      success: true,
      data: savedTemplate
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to save template'
    });
  }
});

// Get template by ID
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const template = await templateService.getTemplate(id);
    
    if (!template) {
      return res.status(404).json({
        success: false,
        error: 'Template not found'
      });
    }
    
    res.json({
      success: true,
      data: template
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to get template'
    });
  }
});

// Update template
router.put('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const updates = req.body;
    const updatedTemplate = await templateService.updateTemplate(id, updates);
    
    res.json({
      success: true,
      data: updatedTemplate
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to update template'
    });
  }
});

// Delete template
router.delete('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    await templateService.deleteTemplate(id);
    
    res.json({
      success: true,
      data: null
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to delete template'
    });
  }
});

export { router as templateRoutes };
