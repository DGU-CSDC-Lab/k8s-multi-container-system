import { ExperimentConfig } from '../../shared/types/experiment.js';
import { ArgoWorkflow } from '../../shared/types/workflow.js';

export class WorkflowGenerator {
  
  generateWorkflow(config: ExperimentConfig): ArgoWorkflow {
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
        templates: [
          {
            name: 'run-experiment',
            container: {
              name: 'experiment',
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
          }
        ],
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

  generateParallelWorkflow(config: ExperimentConfig, parallelConfigs: ExperimentConfig[]): ArgoWorkflow {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    
    return {
      apiVersion: 'argoproj.io/v1alpha1',
      kind: 'Workflow',
      metadata: {
        generateName: `${config.name}-parallel-${timestamp}-`,
        namespace: 'argo',
        labels: {
          'app': 'research-experiment',
          'experiment': config.name,
          'type': 'parallel',
          'created-by': 'workflow-manager'
        }
      },
      spec: {
        entrypoint: 'parallel-experiments',
        templates: [
          {
            name: 'parallel-experiments',
            // DAG template for parallel execution
            script: {
              image: 'alpine:latest',
              source: `
                echo "Starting parallel experiments..."
                echo "Total experiments: ${parallelConfigs.length}"
              `
            }
          },
          ...parallelConfigs.map((parallelConfig, index) => ({
            name: `experiment-${index}`,
            container: {
              name: `experiment-${index}`,
              image: parallelConfig.image,
              command: ['/bin/bash', '-c'],
              args: [parallelConfig.command],
              env: this.generateEnvironmentVariables(parallelConfig.envVars),
              resources: {
                requests: {
                  'nvidia.com/gpu': parallelConfig.resources.gpuCount.toString(),
                  'cpu': parallelConfig.resources.cpuCores,
                  'memory': parallelConfig.resources.memory
                }
              },
              volumeMounts: [
                {
                  name: 'data-volume',
                  mountPath: parallelConfig.dataPath || '/data'
                },
                {
                  name: 'results-volume',
                  mountPath: `${parallelConfig.resultsPath || '/results'}/experiment-${index}`
                }
              ]
            }
          }))
        ],
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
          }
        ]
      }
    };
  }

  private generateEnvironmentVariables(envVars: Record<string, string>): Array<{ name: string; value: string }> {
    return Object.entries(envVars).map(([name, value]) => ({
      name,
      value: value.toString()
    }));
  }

  generateHyperparameterSweepWorkflow(
    baseConfig: ExperimentConfig, 
    parameterGrid: Record<string, any[]>
  ): ArgoWorkflow {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const combinations = this.generateParameterCombinations(parameterGrid);
    
    return {
      apiVersion: 'argoproj.io/v1alpha1',
      kind: 'Workflow',
      metadata: {
        generateName: `${baseConfig.name}-sweep-${timestamp}-`,
        namespace: 'argo',
        labels: {
          'app': 'research-experiment',
          'experiment': baseConfig.name,
          'type': 'hyperparameter-sweep',
          'created-by': 'workflow-manager'
        }
      },
      spec: {
        entrypoint: 'hyperparameter-sweep',
        templates: [
          {
            name: 'hyperparameter-sweep',
            script: {
              image: 'alpine:latest',
              source: `
                echo "Starting hyperparameter sweep..."
                echo "Total combinations: ${combinations.length}"
              `
            }
          },
          ...combinations.map((params, index) => {
            const modifiedEnvVars = { ...baseConfig.envVars };
            Object.entries(params).forEach(([key, value]) => {
              modifiedEnvVars[key] = value.toString();
            });

            return {
              name: `sweep-${index}`,
              container: {
                name: `sweep-${index}`,
                image: baseConfig.image,
                command: ['/bin/bash', '-c'],
                args: [baseConfig.command],
                env: this.generateEnvironmentVariables(modifiedEnvVars),
                resources: {
                  requests: {
                    'nvidia.com/gpu': baseConfig.resources.gpuCount.toString(),
                    'cpu': baseConfig.resources.cpuCores,
                    'memory': baseConfig.resources.memory
                  }
                },
                volumeMounts: [
                  {
                    name: 'data-volume',
                    mountPath: baseConfig.dataPath || '/data'
                  },
                  {
                    name: 'results-volume',
                    mountPath: `${baseConfig.resultsPath || '/results'}/sweep-${index}`
                  }
                ]
              }
            };
          })
        ],
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
          }
        ]
      }
    };
  }

  private generateParameterCombinations(parameterGrid: Record<string, any[]>): Record<string, any>[] {
    const keys = Object.keys(parameterGrid);
    const values = keys.map(key => parameterGrid[key]);
    
    const combinations: Record<string, any>[] = [];
    
    function generateCombinations(currentCombination: any[], depth: number) {
      if (depth === keys.length) {
        const combination: Record<string, any> = {};
        keys.forEach((key, index) => {
          combination[key] = currentCombination[index];
        });
        combinations.push(combination);
        return;
      }
      
      for (const value of values[depth]) {
        generateCombinations([...currentCombination, value], depth + 1);
      }
    }
    
    generateCombinations([], 0);
    return combinations;
  }
}
