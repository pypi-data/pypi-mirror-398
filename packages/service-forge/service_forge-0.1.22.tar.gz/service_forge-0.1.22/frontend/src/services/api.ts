// API service for communicating with the backend
const API_BASE_URL = 'http://localhost:8001/api/v1';

export interface WorkflowNode {
  id: string;
  type: string;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle: string;
  targetHandle: string;
}

export interface Workflow {
  id: string;
  name: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export class ApiService {
  static async getWorkflows(): Promise<Workflow[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/workflow/`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching workflows:', error);
      throw error;
    }
  }

  static async getWorkflow(id: string): Promise<Workflow> {
    try {
      const response = await fetch(`${API_BASE_URL}/workflow/${id}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Error fetching workflow ${id}:`, error);
      throw error;
    }
  }

  static async runWorkflow(id: string): Promise<string> {
    try {
      const response = await fetch(`${API_BASE_URL}/workflow/${id}`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Error running workflow ${id}:`, error);
      throw error;
    }
  }
}
