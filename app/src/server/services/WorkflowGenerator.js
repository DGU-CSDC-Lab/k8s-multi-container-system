class WorkflowGenerator {
  
  generateWorkflow(config) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    
    return {
      apiVersion: 'argoproj.io/v1alpha1',
      kind: 'Workflow',
      metadata: {
        generateName: `${config.name}-${timestamp}-`,
        namespace: 'argo',
        labels: {
          'app': 'research-experiment',
          'experiment': config.name,
          'created-by': 'workflow-manager'
        }
      },
      spec: {
        entrypoint: 'run-experiment',
        arguments: {
          parameters: [
            { name: 'experiment-name', value: config.name },
            { name: 'image', value: config.image },
            { name: 'command', value: config.command }
          ]
        },
        templates: [{
          name: 'run-experiment',
          container: {
            image: config.image,
            command: ['/bin/bash', '-c'],
            args: [config.command],
            env: this.generateEnvironmentVariables(config.envVars),
            resources: {
              requests: {
                'nvidia.com/gpu': config.resources.gpuCount.toString(),
                'cpu': config.resources.cpuCores,
                'memory': config.resources.memory
              },
              limits: {
                'nvidia.com/gpu': config.resources.gpuCount.toString(),
                'cpu': (parseInt(config.resources.cpuCores) * 2).toString(),
                'memory': config.resources.memory
              }
            },
            volumeMounts: [
              {
                name: 'data-volume',
                mountPath: config.dataPath || '/data'
              },
              {
                name: 'results-volume',
                mountPath: config.resultsPath || '/results'
              },
              {
                name: 'workspace-volume',
                mountPath: '/workspace'
              }
            ]
          }
        }],
        volumes: [
          {
            name: 'data-volume',
            persistentVolumeClaim: {
              claimName: 'research-data-pvc'
            }
          },
          {
            name: 'results-volume',
            persistentVolumeClaim: {
              claimName: 'research-results-pvc'
            }
          },
          {
            name: 'workspace-volume',
            emptyDir: {}
          }
        ],
        parallelism: config.resources.parallelJobs
      }
    };
  }

  generateEnvironmentVariables(envVars) {
    return Object.entries(envVars).map(([name, value]) => ({
      name,
      value: value.toString()
    }));
  }
}

module.exports = WorkflowGenerator;
