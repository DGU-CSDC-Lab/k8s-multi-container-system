import fs from 'fs/promises';
import path from 'path';
import yaml from 'js-yaml';
import { ArgoWorkflow } from '../../shared/types/workflow.js';

export class ExperimentService {
  private workflowsDir: string;

  constructor() {
    this.workflowsDir = path.join(process.cwd(), 'workflows');
    this.ensureWorkflowsDirectory();
  }

  private async ensureWorkflowsDirectory(): Promise<void> {
    try {
      await fs.access(this.workflowsDir);
    } catch {
      await fs.mkdir(this.workflowsDir, { recursive: true });
    }
  }

  async saveWorkflow(workflow: ArgoWorkflow, experimentName: string): Promise<string> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const filename = `${experimentName}-${timestamp}.yaml`;
    const filepath = path.join(this.workflowsDir, filename);

    const yamlContent = yaml.dump(workflow, {
      indent: 2,
      lineWidth: -1,
      noRefs: true
    });

    await fs.writeFile(filepath, yamlContent, 'utf8');
    return filepath;
  }

  async loadWorkflow(filename: string): Promise<ArgoWorkflow> {
    const filepath = path.join(this.workflowsDir, filename);
    const content = await fs.readFile(filepath, 'utf8');
    return yaml.load(content) as ArgoWorkflow;
  }

  async listWorkflowFiles(): Promise<string[]> {
    try {
      const files = await fs.readdir(this.workflowsDir);
      return files.filter(file => file.endsWith('.yaml') || file.endsWith('.yml'));
    } catch {
      return [];
    }
  }

  async deleteWorkflowFile(filename: string): Promise<void> {
    const filepath = path.join(this.workflowsDir, filename);
    await fs.unlink(filepath);
  }

  async getWorkflowHistory(experimentName: string): Promise<string[]> {
    const files = await this.listWorkflowFiles();
    return files.filter(file => file.startsWith(experimentName));
  }

  async archiveWorkflow(filename: string): Promise<void> {
    const archiveDir = path.join(this.workflowsDir, 'archive');
    
    try {
      await fs.access(archiveDir);
    } catch {
      await fs.mkdir(archiveDir, { recursive: true });
    }

    const sourcePath = path.join(this.workflowsDir, filename);
    const targetPath = path.join(archiveDir, filename);
    
    await fs.rename(sourcePath, targetPath);
  }

  async validateWorkflow(workflow: ArgoWorkflow): Promise<{ valid: boolean; errors: string[] }> {
    const errors: string[] = [];

    // Basic validation
    if (!workflow.apiVersion) {
      errors.push('Missing apiVersion');
    }

    if (!workflow.kind || workflow.kind !== 'Workflow') {
      errors.push('Invalid or missing kind');
    }

    if (!workflow.metadata?.namespace) {
      errors.push('Missing namespace in metadata');
    }

    if (!workflow.spec?.entrypoint) {
      errors.push('Missing entrypoint in spec');
    }

    if (!workflow.spec?.templates || workflow.spec.templates.length === 0) {
      errors.push('Missing templates in spec');
    }

    // Template validation
    if (workflow.spec?.templates) {
      workflow.spec.templates.forEach((template, index) => {
        if (!template.name) {
          errors.push(`Template ${index} missing name`);
        }

        if (!template.container && !template.script) {
          errors.push(`Template ${template.name} must have either container or script`);
        }

        if (template.container) {
          if (!template.container.image) {
            errors.push(`Template ${template.name} container missing image`);
          }
        }
      });
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  async getWorkflowStats(): Promise<{
    totalWorkflows: number;
    recentWorkflows: number;
    averageExecutionTime: number;
  }> {
    const files = await this.listWorkflowFiles();
    const now = new Date();
    const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);

    let recentCount = 0;
    let totalExecutionTime = 0;
    let completedWorkflows = 0;

    for (const file of files) {
      const filepath = path.join(this.workflowsDir, file);
      const stats = await fs.stat(filepath);
      
      if (stats.mtime > oneDayAgo) {
        recentCount++;
      }

      // Try to extract execution time from workflow (if available)
      try {
        const workflow = await this.loadWorkflow(file);
        // This would require additional logic to track execution times
        // For now, we'll use a placeholder
      } catch {
        // Ignore errors when loading workflow files
      }
    }

    return {
      totalWorkflows: files.length,
      recentWorkflows: recentCount,
      averageExecutionTime: completedWorkflows > 0 ? totalExecutionTime / completedWorkflows : 0
    };
  }

  async cleanupOldWorkflows(daysOld: number = 30): Promise<number> {
    const files = await this.listWorkflowFiles();
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - daysOld);

    let cleanedCount = 0;

    for (const file of files) {
      const filepath = path.join(this.workflowsDir, file);
      const stats = await fs.stat(filepath);
      
      if (stats.mtime < cutoffDate) {
        await this.archiveWorkflow(file);
        cleanedCount++;
      }
    }

    return cleanedCount;
  }
}
