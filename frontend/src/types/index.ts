export interface Report {
  id: number;
  title: string;
  filename: string;
  file_path: string;
  content_text: string | null;
  status: "UPLOADED" | "PROCESSING" | "READY" | "ERROR";
  created_at: string;
}

export interface Criterion {
  id: string;
  label: string;
  weight: number;
  description?: string;
}

export interface AgentConfiguration {
  id: number;
  name: string;
  description: string | null;
  criteria: {
    checkItems: Criterion[];
    scoringRubric?: string;
  };
  max_score: number;
  created_at: string;
}

export interface AgentResult {
  id: number;
  agent_config_id: number;
  agent_name: string;
  score: number | null;
  max_score: number | null;
  feedback: string | null;
  details: Array<{
    criterion: string;
    passed: boolean;
    comment: string;
  }> | null;
  status: "PENDING" | "RUNNING" | "COMPLETED" | "ERROR";
}

export interface Evaluation {
  id: number;
  report_id: number;
  status: "PENDING" | "RUNNING" | "COMPLETED" | "ERROR";
  total_score: number | null;
  max_possible_score: number | null;
  summary: string | null;
  agent_results: AgentResult[];
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}
