import { exec } from 'child_process';
import { promisify } from 'util';
import fs from 'fs/promises';
import path from 'path';
import { DockerBuildConfig } from '../../shared/types/experiment.js';

const execAsync = promisify(exec);

export class DockerService {
  private dockerfilesDir: string;

  constructor() {
    this.dockerfilesDir = path.join(process.cwd(), 'dockerfiles');
    this.ensureDockerfilesDirectory();
  }

  private async ensureDockerfilesDirectory(): Promise<void> {
    try {
      await fs.access(this.dockerfilesDir);
    } catch {
      await fs.mkdir(this.dockerfilesDir, { recursive: true });
    }
  }

  async buildImage(config: DockerBuildConfig): Promise<string> {
    const imageName = `${config.name}:latest`;
    const dockerfile = config.dockerfile || this.generateDockerfile(config);
    
    // Save Dockerfile
    const dockerfilePath = await this.saveDockerfile(config.name, dockerfile);
    
    try {
      // Build Docker image
      const buildCommand = `docker build -t ${imageName} -f ${dockerfilePath} ../proto-gcn`;
      const { stdout, stderr } = await execAsync(buildCommand);
      
      if (stderr && !stderr.includes('WARNING')) {
        throw new Error(stderr);
      }
      
      return imageName;
    } catch (error) {
      throw new Error(`Docker build failed: ${error}`);
    }
  }

  async listImages(): Promise<string[]> {
    try {
      const { stdout } = await execAsync('docker images --format "{{.Repository}}:{{.Tag}}"');
      return stdout.trim().split('\n').filter(line => line && !line.includes('<none>'));
    } catch (error) {
      throw new Error(`Failed to list Docker images: ${error}`);
    }
  }

  async removeImage(imageName: string): Promise<void> {
    try {
      await execAsync(`docker rmi ${imageName}`);
    } catch (error) {
      throw new Error(`Failed to remove Docker image: ${error}`);
    }
  }

  async pushImage(imageName: string, registry?: string): Promise<void> {
    try {
      const fullImageName = registry ? `${registry}/${imageName}` : imageName;
      
      if (registry) {
        await execAsync(`docker tag ${imageName} ${fullImageName}`);
      }
      
      await execAsync(`docker push ${fullImageName}`);
    } catch (error) {
      throw new Error(`Failed to push Docker image: ${error}`);
    }
  }

  async getImageInfo(imageName: string): Promise<any> {
    try {
      const { stdout } = await execAsync(`docker inspect ${imageName}`);
      return JSON.parse(stdout)[0];
    } catch (error) {
      throw new Error(`Failed to get image info: ${error}`);
    }
  }

  async searchImages(query: string = ''): Promise<string[]> {
    try {
      // Get local images
      const { stdout: localImages } = await execAsync('docker images --format "{{.Repository}}:{{.Tag}}"');
      const local = localImages.trim().split('\n').filter(line => line && !line.includes('<none>'));
      
      // Common base images for research
      const commonImages = [
        'python:3.8',
        'python:3.9',
        'python:3.10',
        'python:3.11',
        'nvidia/cuda:11.3.1-cudnn8-runtime-ubuntu20.04',
        'nvidia/cuda:11.8-cudnn8-runtime-ubuntu22.04',
        'nvidia/cuda:12.0-cudnn8-runtime-ubuntu22.04',
        'pytorch/pytorch:1.11.0-cuda11.3-cudnn8-runtime',
        'pytorch/pytorch:1.13.0-cuda11.6-cudnn8-runtime',
        'pytorch/pytorch:2.0.0-cuda11.7-cudnn8-runtime',
        'tensorflow/tensorflow:2.8.0-gpu',
        'tensorflow/tensorflow:2.10.0-gpu',
        'tensorflow/tensorflow:2.12.0-gpu',
        'jupyter/tensorflow-notebook',
        'jupyter/pytorch-notebook',
        'jupyter/datascience-notebook',
        'ubuntu:20.04',
        'ubuntu:22.04',
        'debian:11',
        'alpine:latest'
      ];

      // Combine and filter
      const allImages = [...new Set([...local, ...commonImages])];
      
      if (query) {
        return allImages.filter(img => 
          img.toLowerCase().includes(query.toLowerCase())
        );
      }
      
      return allImages;
    } catch (error) {
      throw new Error(`Failed to search images: ${error}`);
    }
  }

  private generateDockerfile(config: DockerBuildConfig): string {
    let dockerfile = `FROM ${config.baseImage}\n\n`;
    
    // Environment setup
    dockerfile += `ENV DEBIAN_FRONTEND=noninteractive\n\n`;

    // System dependencies based on base image
    if (config.baseImage.includes('ubuntu') || config.baseImage.includes('debian')) {
      dockerfile += `RUN apt-get update && apt-get install -y \\\n`;
      dockerfile += `    python3-pip python3-dev \\\n`;
      dockerfile += `    git curl wget unzip nano vim \\\n`;
      dockerfile += `    build-essential \\\n`;
      dockerfile += `    && apt-get clean \\\n`;
      dockerfile += `    && rm -rf /var/lib/apt/lists/*\n\n`;
    }

    // Python setup
    if (!config.baseImage.includes('python') && !config.baseImage.includes('pytorch') && !config.baseImage.includes('tensorflow')) {
      dockerfile += `RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1\n`;
      dockerfile += `RUN pip3 install --upgrade pip setuptools wheel\n\n`;
    }

    // CUDA/GPU specific setup
    if (config.baseImage.includes('cuda')) {
      dockerfile += `# CUDA environment setup\n`;
      dockerfile += `ENV CUDA_HOME=/usr/local/cuda\n`;
      dockerfile += `ENV PATH=$CUDA_HOME/bin:$PATH\n`;
      dockerfile += `ENV LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH\n\n`;
    }

    // Install Python requirements
    if (config.requirements && config.requirements.length > 0) {
      dockerfile += `# Install Python packages\n`;
      dockerfile += `RUN pip install --no-cache-dir \\\n`;
      config.requirements.forEach((req, index) => {
        const isLast = index === config.requirements.length - 1;
        dockerfile += `    ${req}${isLast ? '\n\n' : ' \\\n'}`;
      });
    }

    // PyTorch specific setup
    if (config.baseImage.includes('pytorch') || config.requirements.some(req => req.includes('torch'))) {
      dockerfile += `# PyTorch specific setup\n`;
      dockerfile += `ENV TORCH_CUDA_ARCH_LIST="6.0 6.1 7.0 7.5 8.0 8.6+PTX"\n`;
      dockerfile += `ENV TORCH_NVCC_FLAGS="-Xfatbin -compress-all"\n\n`;
    }

    // Workspace setup
    dockerfile += `WORKDIR /workspace\n`;
    dockerfile += `COPY . /workspace/\n\n`;

    // Install project dependencies
    dockerfile += `# Install project dependencies\n`;
    dockerfile += `RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; fi\n`;
    dockerfile += `RUN if [ -f setup.py ]; then pip install -e .; fi\n\n`;

    // GPU runtime setup
    if (config.baseImage.includes('cuda')) {
      dockerfile += `# GPU runtime setup\n`;
      dockerfile += `RUN rm -f /usr/lib/x86_64-linux-gnu/libGLX_indirect.so.0 \\\n`;
      dockerfile += `    && rm -f /usr/lib/x86_64-linux-gnu/libGLX.so.0\n\n`;
    }

    // Entry point
    dockerfile += `# Flexible entry point\n`;
    dockerfile += `ENTRYPOINT ["/bin/bash", "-c"]\n`;
    dockerfile += `CMD ["python auto_protogcn.py"]\n`;

    return dockerfile;
  }

  private async saveDockerfile(name: string, content: string): Promise<string> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const filename = `Dockerfile.${name}.${timestamp}`;
    const filepath = path.join(this.dockerfilesDir, filename);
    
    await fs.writeFile(filepath, content, 'utf8');
    return filepath;
  }

  async getDockerfileHistory(imageName: string): Promise<string[]> {
    try {
      const files = await fs.readdir(this.dockerfilesDir);
      return files.filter(file => file.includes(imageName));
    } catch {
      return [];
    }
  }

  async cleanupUnusedImages(): Promise<number> {
    try {
      const { stdout } = await execAsync('docker image prune -f');
      const match = stdout.match(/Total reclaimed space: (.+)/);
      return match ? parseInt(match[1]) : 0;
    } catch (error) {
      throw new Error(`Failed to cleanup unused images: ${error}`);
    }
  }

  async getDockerSystemInfo(): Promise<any> {
    try {
      const { stdout } = await execAsync('docker system df --format "table {{.Type}}\\t{{.Total}}\\t{{.Active}}\\t{{.Size}}\\t{{.Reclaimable}}"');
      return stdout;
    } catch (error) {
      throw new Error(`Failed to get Docker system info: ${error}`);
    }
  }
}
