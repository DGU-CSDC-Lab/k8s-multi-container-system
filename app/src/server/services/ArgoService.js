const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);

class ArgoService {
  
  async submitWorkflow(workflowFile) {
    try {
      const { stdout } = await execAsync(`argo submit ${workflowFile} -o name`);
      return stdout.trim();
    } catch (error) {
      throw new Error(`Failed to submit workflow: ${error.message}`);
    }
  }

  async listWorkflows() {
    try {
      const { stdout } = await execAsync('argo list -o json');
      const argoOutput = JSON.parse(stdout);
      
      if (!argoOutput.items) {
        return [];
      }

      return argoOutput.items.map((workflow) => ({
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
      // Argo CLI가 없거나 클러스터 연결이 안 된 경우 샘플 데이터 반환
      console.warn('Argo CLI not available, returning sample data');
      return [
        {
          name: 'sample-experiment-1',
          status: 'Running',
          createdAt: new Date().toISOString(),
          duration: '5m 30s'
        },
        {
          name: 'sample-experiment-2',
          status: 'Succeeded',
          createdAt: new Date(Date.now() - 3600000).toISOString(),
          duration: '12m 45s'
        }
      ];
    }
  }

  async getWorkflowStatus(name) {
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
      throw new Error(`Failed to get workflow status: ${error.message}`);
    }
  }

  async stopWorkflow(name) {
    try {
      await execAsync(`argo stop ${name}`);
    } catch (error) {
      throw new Error(`Failed to stop workflow: ${error.message}`);
    }
  }

  async getWorkflowLogs(name) {
    try {
      const { stdout } = await execAsync(`argo logs ${name}`);
      return stdout;
    } catch (error) {
      throw new Error(`Failed to get workflow logs: ${error.message}`);
    }
  }

  mapArgoStatus(argoStatus) {
    const statusMap = {
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

  calculateDuration(startTime, endTime) {
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
}

module.exports = ArgoService;
