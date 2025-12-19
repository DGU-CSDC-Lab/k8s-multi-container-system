import fs from 'fs/promises';
import path from 'path';
import { ExperimentTemplate } from '../../shared/types/experiment.js';

export class TemplateService {
  private templatesDir: string;
  private templatesFile: string;

  constructor() {
    this.templatesDir = path.join(process.cwd(), 'templates');
    this.templatesFile = path.join(this.templatesDir, 'templates.json');
    this.ensureTemplatesDirectory();
  }

  private async ensureTemplatesDirectory(): Promise<void> {
    try {
      await fs.access(this.templatesDir);
    } catch {
      await fs.mkdir(this.templatesDir, { recursive: true });
    }

    try {
      await fs.access(this.templatesFile);
    } catch {
      await this.saveTemplatesFile([]);
    }
  }

  async getAllTemplates(): Promise<ExperimentTemplate[]> {
    try {
      const content = await fs.readFile(this.templatesFile, 'utf8');
      return JSON.parse(content);
    } catch {
      return [];
    }
  }

  async getTemplate(id: string): Promise<ExperimentTemplate | null> {
    const templates = await this.getAllTemplates();
    return templates.find(template => template.id === id) || null;
  }

  async saveTemplate(template: Omit<ExperimentTemplate, 'id'>): Promise<ExperimentTemplate> {
    const templates = await this.getAllTemplates();
    
    const newTemplate: ExperimentTemplate = {
      ...template,
      id: this.generateId()
    };

    templates.push(newTemplate);
    await this.saveTemplatesFile(templates);
    
    return newTemplate;
  }

  async updateTemplate(id: string, updates: Partial<ExperimentTemplate>): Promise<ExperimentTemplate> {
    const templates = await this.getAllTemplates();
    const index = templates.findIndex(template => template.id === id);
    
    if (index === -1) {
      throw new Error('Template not found');
    }

    templates[index] = { ...templates[index], ...updates, id };
    await this.saveTemplatesFile(templates);
    
    return templates[index];
  }

  async deleteTemplate(id: string): Promise<void> {
    const templates = await this.getAllTemplates();
    const filteredTemplates = templates.filter(template => template.id !== id);
    
    if (filteredTemplates.length === templates.length) {
      throw new Error('Template not found');
    }

    await this.saveTemplatesFile(filteredTemplates);
  }

  async getTemplatesByTag(tag: string): Promise<ExperimentTemplate[]> {
    const templates = await this.getAllTemplates();
    return templates.filter(template => template.tags.includes(tag));
  }

  async searchTemplates(query: string): Promise<ExperimentTemplate[]> {
    const templates = await this.getAllTemplates();
    const lowerQuery = query.toLowerCase();
    
    return templates.filter(template => 
      template.name.toLowerCase().includes(lowerQuery) ||
      template.description.toLowerCase().includes(lowerQuery) ||
      template.tags.some(tag => tag.toLowerCase().includes(lowerQuery))
    );
  }

  async duplicateTemplate(id: string, newName?: string): Promise<ExperimentTemplate> {
    const template = await this.getTemplate(id);
    
    if (!template) {
      throw new Error('Template not found');
    }

    const duplicatedTemplate = {
      ...template,
      name: newName || `${template.name} (Copy)`,
      tags: [...template.tags, 'duplicated']
    };

    delete (duplicatedTemplate as any).id;
    return this.saveTemplate(duplicatedTemplate);
  }

  async exportTemplate(id: string): Promise<string> {
    const template = await this.getTemplate(id);
    
    if (!template) {
      throw new Error('Template not found');
    }

    return JSON.stringify(template, null, 2);
  }

  async importTemplate(templateJson: string): Promise<ExperimentTemplate> {
    try {
      const template = JSON.parse(templateJson);
      
      // Validate template structure
      if (!template.name || !template.config) {
        throw new Error('Invalid template format');
      }

      // Remove ID if present (will be generated)
      delete template.id;
      
      return this.saveTemplate(template);
    } catch (error) {
      throw new Error(`Failed to import template: ${error}`);
    }
  }

  async getDefaultTemplates(): Promise<ExperimentTemplate[]> {
    return [
      {
        id: 'default-pytorch',
        name: 'PyTorch Training',
        description: 'Standard PyTorch model training template',
        config: {
          name: 'pytorch-experiment',
          image: 'pytorch/pytorch:1.11.0-cuda11.3-cudnn8-runtime',
          command: 'python train.py',
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
        },
        tags: ['pytorch', 'training', 'default']
      },
      {
        id: 'default-tensorflow',
        name: 'TensorFlow Training',
        description: 'Standard TensorFlow model training template',
        config: {
          name: 'tensorflow-experiment',
          image: 'tensorflow/tensorflow:2.8.0-gpu',
          command: 'python train.py',
          envVars: {
            'TF_CPP_MIN_LOG_LEVEL': '2',
            'CUDA_VISIBLE_DEVICES': '0'
          },
          resources: {
            gpuCount: 1,
            cpuCores: '4',
            memory: '8Gi',
            parallelJobs: 1
          }
        },
        tags: ['tensorflow', 'training', 'default']
      },
      {
        id: 'default-hyperparameter-sweep',
        name: 'Hyperparameter Sweep',
        description: 'Template for hyperparameter optimization experiments',
        config: {
          name: 'hyperparam-sweep',
          image: 'python:3.8',
          command: 'python sweep.py --lr ${LR} --batch_size ${BATCH_SIZE}',
          envVars: {
            'LR': '0.001',
            'BATCH_SIZE': '32',
            'EPOCHS': '100'
          },
          resources: {
            gpuCount: 1,
            cpuCores: '2',
            memory: '4Gi',
            parallelJobs: 4
          }
        },
        tags: ['hyperparameter', 'sweep', 'optimization']
      }
    ];
  }

  private async saveTemplatesFile(templates: ExperimentTemplate[]): Promise<void> {
    await fs.writeFile(this.templatesFile, JSON.stringify(templates, null, 2), 'utf8');
  }

  private generateId(): string {
    return `template_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  async getTemplateStats(): Promise<{
    total: number;
    byTag: Record<string, number>;
    mostUsed: ExperimentTemplate[];
  }> {
    const templates = await this.getAllTemplates();
    
    const byTag: Record<string, number> = {};
    templates.forEach(template => {
      template.tags.forEach(tag => {
        byTag[tag] = (byTag[tag] || 0) + 1;
      });
    });

    // For now, we'll return all templates as "most used"
    // In a real implementation, you'd track usage statistics
    const mostUsed = templates.slice(0, 5);

    return {
      total: templates.length,
      byTag,
      mostUsed
    };
  }
}
