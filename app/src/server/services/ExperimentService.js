const fs = require('fs/promises');
const path = require('path');
const yaml = require('js-yaml');

class ExperimentService {
  constructor() {
    this.workflowsDir = path.join(process.cwd(), 'workflows');
    this.ensureWorkflowsDirectory();
  }

  async ensureWorkflowsDirectory() {
    try {
      await fs.access(this.workflowsDir);
    } catch {
      await fs.mkdir(this.workflowsDir, { recursive: true });
    }
  }

  async saveWorkflow(workflow, experimentName) {
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

  async loadWorkflow(filename) {
    const filepath = path.join(this.workflowsDir, filename);
    const content = await fs.readFile(filepath, 'utf8');
    return yaml.load(content);
  }

  async listWorkflowFiles() {
    try {
      const files = await fs.readdir(this.workflowsDir);
      return files.filter(file => file.endsWith('.yaml') || file.endsWith('.yml'));
    } catch {
      return [];
    }
  }
}

module.exports = ExperimentService;
