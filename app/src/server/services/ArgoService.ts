import { exec } from 'child_process';
import { promisify } from 'util';
import { WorkflowStatus } from '../../shared/types/experiment.js';

const execAsync = promisify(exec);

export class ArgoService {
  
  async submitWorkflow(workflowFile: string): Promise<string> {
    try {
      const { stdout } = await execAsync(`argo submit ${workflowFile} -o name`);
      return stdout.trim();
    } catch (error) {
      throw new Error(`Failed to submit workflow: ${error}`);
    }
  }

  async listWorkflows(): Promise<WorkflowStatus[]> {
    try {
      const { stdout } = await execAsync('argo list -o json');
      const argoOutput = JSON.parse(stdout);
      
      if (!argoOutput.items) {
        return [];
      }

      return argoOutput.items.map((workflow: any) => ({
        name: workflow.metadata.name,
        status: this.mapArgoStatus(workflow.status?.phase || 'Unknown'),
        createdAt: workflow.metadata.creationTimestamp,
        finishedAt: workflow.status?.finishedAt,
        duration: this.calculateDuration(
          workflow.metadata.creationTimestamp,
          workflow.status?.finishedAt
        )
      }));
    } catch (error) {
      throw new Error(`Failed to list workflows: ${error}`);
    }
  }

  async getWorkflowStatus(name: string): Promise<WorkflowStatus> {
    try {
      const { stdout } = await execAsync(`argo get ${name} -o json`);
      const workflow = JSON.parse(stdout);
      
      return {
        name: workflow.metadata.name,
        status: this.mapArgoStatus(workflow.status?.phase || 'Unknown'),
        createdAt: workflow.metadata.creationTimestamp,
        finishedAt: workflow.status?.finishedAt,
        duration: this.calculateDuration(
          workflow.metadata.creationTimestamp,
          workflow.status?.finishedAt
        )
      };
    } catch (error) {
      throw new Error(`Failed to get workflow status: ${error}`);
    }
  }

  async stopWorkflow(name: string): Promise<void> {
    try {
      await execAsync(`argo stop ${name}`);
    } catch (error) {
      throw new Error(`Failed to stop workflow: ${error}`);
    }
  }

  async deleteWorkflow(name: string): Promise<void> {
    try {
      await execAsync(`argo delete ${name}`);
    } catch (error) {
      throw new Error(`Failed to delete workflow: ${error}`);
    }
  }

  async getWorkflowLogs(name: string): Promise<string> {
    try {
      const { stdout } = await execAsync(`argo logs ${name}`);
      return stdout;
    } catch (error) {
      throw new Error(`Failed to get workflow logs: ${error}`);
    }
  }

  async retryWorkflow(name: string): Promise<string> {
    try {
      const { stdout } = await execAsync(`argo retry ${name} -o name`);
      return stdout.trim();
    } catch (error) {
      throw new Error(`Failed to retry workflow: ${error}`);
    }
  }

  async suspendWorkflow(name: string): Promise<void> {
    try {
      await execAsync(`argo suspend ${name}`);
    } catch (error) {
      throw new Error(`Failed to suspend workflow: ${error}`);
    }
  }

  async resumeWorkflow(name: string): Promise<void> {
    try {
      await execAsync(`argo resume ${name}`);
    } catch (error) {
      throw new Error(`Failed to resume workflow: ${error}`);
    }
  }

  async getWorkflowEvents(name: string): Promise<any[]> {
    try {
      const { stdout } = await execAsync(`kubectl get events --field-selector involvedObject.name=${name} -o json`);
      const events = JSON.parse(stdout);
      return events.items || [];
    } catch (error) {
      throw new Error(`Failed to get workflow events: ${error}`);
    }
  }

  private mapArgoStatus(argoStatus: string): WorkflowStatus['status'] {
    const statusMap: Record<string, WorkflowStatus['status']> = {
      'Pending': 'Pending',
      'Running': 'Running',
      'Succeeded': 'Succeeded',
      'Failed': 'Failed',
      'Error': 'Error',
      'Skipped': 'Failed',
      'Omitted': 'Failed'
    };

    return statusMap[argoStatus] || 'Error';
  }

  private calculateDuration(startTime: string, endTime?: string): string {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    
    const durationMs = end.getTime() - start.getTime();
    const seconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  }

  async getWorkflowMetrics(): Promise<{
    total: number;
    running: number;
    succeeded: number;
    failed: number;
    pending: number;
  }> {
    try {
      const workflows = await this.listWorkflows();
      
      return {
        total: workflows.length,
        running: workflows.filter(w => w.status === 'Running').length,
        succeeded: workflows.filter(w => w.status === 'Succeeded').length,
        failed: workflows.filter(w => w.status === 'Failed' || w.status === 'Error').length,
        pending: workflows.filter(w => w.status === 'Pending').length
      };
    } catch (error) {
      throw new Error(`Failed to get workflow metrics: ${error}`);
    }
  }
}
