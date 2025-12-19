const { exec } = require('child_process');
const { promisify } = require('util');
const fs = require('fs/promises');
const path = require('path');

const execAsync = promisify(exec);

class DockerService {
  constructor() {
    this.dockerfilesDir = path.join(process.cwd(), 'dockerfiles');
    this.ensureDockerfilesDirectory();
  }

  async ensureDockerfilesDirectory() {
    try {
      await fs.access(this.dockerfilesDir);
    } catch {
      await fs.mkdir(this.dockerfilesDir, { recursive: true });
    }
  }

  async buildImage(config) {
    const imageName = `${config.name}:latest`;
    const dockerfile = config.dockerfile || this.generateDockerfile(config);
    
    // Save Dockerfile
    const dockerfilePath = await this.saveDockerfile(config.name, dockerfile);
    
    try {
      // Build Docker image with detailed output
      const buildCommand = `docker build -t ${imageName} -f ${dockerfilePath} ../proto-gcn`;
      console.log('Executing:', buildCommand);
      
      // Execute with real-time output capture
      const { stdout, stderr } = await execAsync(buildCommand, { 
        maxBuffer: 1024 * 1024 * 10 // 10MB buffer for large build logs
      });
      
      let buildLog = `Building Docker image: ${imageName}\n`;
      buildLog += `Using Dockerfile: ${dockerfilePath}\n\n`;
      buildLog += `--- Docker Build Output ---\n`;
      buildLog += stdout;
      
      if (stderr && !stderr.includes('WARNING')) {
        buildLog += `\n--- Build Errors ---\n`;
        buildLog += stderr;
        throw new Error(stderr);
      }
      
      if (stderr && stderr.includes('WARNING')) {
        buildLog += `\n--- Build Warnings ---\n`;
        buildLog += stderr;
      }
      
      buildLog += `\n✅ Successfully built: ${imageName}`;
      
      return {
        imageName,
        buildLog,
        dockerfile,
        dockerfilePath
      };
    } catch (error) {
      const errorLog = `❌ Docker build failed for: ${imageName}\n`;
      const fullError = errorLog + `Error: ${error.message}\n`;
      
      throw new Error(fullError);
    }
  }

  async listImages() {
    try {
      const { stdout } = await execAsync('docker images --format "{{.Repository}}:{{.Tag}}"');
      return stdout.trim().split('\n').filter(line => line && !line.includes('<none>'));
    } catch (error) {
      throw new Error(`Failed to list Docker images: ${error.message}`);
    }
  }

  async searchImages(query = '') {
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
      throw new Error(`Failed to search images: ${error.message}`);
    }
  }

  generateDockerfile(config) {
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

    // Workspace setup
    dockerfile += `WORKDIR /workspace\n`;
    dockerfile += `COPY . /workspace/\n\n`;

    // Install project dependencies
    dockerfile += `# Install project dependencies\n`;
    dockerfile += `RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; fi\n`;
    dockerfile += `RUN if [ -f setup.py ]; then pip install -e .; fi\n\n`;

    // Entry point
    dockerfile += `# Flexible entry point\n`;
    dockerfile += `ENTRYPOINT ["/bin/bash", "-c"]\n`;
    dockerfile += `CMD ["python auto_protogcn.py"]\n`;

    return dockerfile;
  }

  async saveDockerfile(name, content) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const filename = `Dockerfile.${name}.${timestamp}`;
    const filepath = path.join(this.dockerfilesDir, filename);
    
    await fs.writeFile(filepath, content, 'utf8');
    return filepath;
  }
}

module.exports = DockerService;
