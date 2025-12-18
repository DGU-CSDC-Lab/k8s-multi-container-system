export interface EnvironmentVariable {
  name: string;
  value: string;
}

export interface ResourceConfig {
  gpuCount: number;
  cpuCores: string;
  memory: string;
  parallelJobs: number;
}

export interface ExperimentConfig {
  name: string;
  image: string;
  command: string;
  envVars: Record<string, string>;
  resources: ResourceConfig;
  dataPath?: string;
  resultsPath?: string;
}

export interface WorkflowStatus {
  name: string;
  status: 'Pending' | 'Running' | 'Succeeded' | 'Failed' | 'Error';
  createdAt: string;
  finishedAt?: string;
  duration?: string;
}

export interface DockerBuildConfig {
  name: string;
  baseImage: string;
  requirements: string[];
  dockerfile?: string;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface ExperimentTemplate {
  id: string;
  name: string;
  description: string;
  config: Partial<ExperimentConfig>;
  tags: string[];
}
