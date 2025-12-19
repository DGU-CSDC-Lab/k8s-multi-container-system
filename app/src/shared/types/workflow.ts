export interface WorkflowMetadata {
  generateName?: string;
  name?: string;
  namespace: string;
  labels?: Record<string, string>;
  annotations?: Record<string, string>;
}

export interface ContainerSpec {
  name: string;
  image: string;
  command?: string[];
  args?: string[];
  env?: Array<{ name: string; value: string }>;
  resources?: {
    requests?: Record<string, string>;
    limits?: Record<string, string>;
  };
  volumeMounts?: Array<{
    name: string;
    mountPath: string;
  }>;
}

export interface VolumeSpec {
  name: string;
  persistentVolumeClaim?: {
    claimName: string;
  };
  configMap?: {
    name: string;
  };
  emptyDir?: {};
}

export interface WorkflowTemplate {
  name: string;
  container?: ContainerSpec;
  script?: {
    image: string;
    source: string;
    volumeMounts?: Array<{
      name: string;
      mountPath: string;
    }>;
  };
}

export interface WorkflowSpec {
  entrypoint: string;
  arguments?: {
    parameters?: Array<{
      name: string;
      value?: string;
    }>;
  };
  templates: WorkflowTemplate[];
  volumes?: VolumeSpec[];
  parallelism?: number;
}

export interface ArgoWorkflow {
  apiVersion: string;
  kind: string;
  metadata: WorkflowMetadata;
  spec: WorkflowSpec;
}
