export type Application = {
  id: number;
  user_id: number;
  job_id: number;
  resume_id: number;
  status: "Applied" | "Failed" | string;
  applied_at: string;
  response_content: string | null;
  applied_via_automation: boolean;
  company: string | null;
  job_title: string | null;
  created_at: string;
  updated_at: string;
};

export type ApplicationBatchResponse = {
  total: number;
  applications: Application[];
};

export type ApplicationStats = {
  total_jobs_found: number;
  total_applied: number;
  success_rate: number;
  failed_applications: number;
};
