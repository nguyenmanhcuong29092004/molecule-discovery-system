/**
 * Type definitions for Molecule Discovery Runs
 */

export interface RunConstraints {
  max_mw: number;
  max_logp: number;
  max_hbd: number;
  max_hba: number;
  max_tpsa: number;
  max_violations: number;
}

export interface RunConfig {
  objective: string;
  seed_smiles: string[];
  rounds: number;
  candidates_per_round: number;
  top_k: number;
  constraints: RunConstraints;
}

export interface CreateRunRequest {
  config: RunConfig;
}

export interface RunProgress {
  total_generated: number;
  total_valid: number;
  total_passed: number;
}

export interface RunResponse {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  objective: string;
  config: RunConfig;
  progress: RunProgress;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
}

export interface TaskResponse {
  run_id: string;
  task_id: string;
  status: string;
  message: string;
}

// Form data type (before transformation to API format)
export interface RunFormData {
  objective: string;
  seed_smiles_text: string; // Text input (one per line)
  rounds: number;
  candidates_per_round: number;
  top_k: number;
  max_mw: number;
  max_logp: number;
  max_hbd: number;
  max_hba: number;
  max_tpsa: number;
  max_violations: number;
}

// Default values
export const DEFAULT_CONSTRAINTS: RunConstraints = {
  max_mw: 500,
  max_logp: 5,
  max_hbd: 5,
  max_hba: 10,
  max_tpsa: 140,
  max_violations: 1,
};

export const DEFAULT_FORM_VALUES: RunFormData = {
  objective: '',
  seed_smiles_text: '',
  rounds: 5,
  candidates_per_round: 50,
  top_k: 10,
  max_mw: 500,
  max_logp: 5,
  max_hbd: 5,
  max_hba: 10,
  max_tpsa: 140,
  max_violations: 1,
};