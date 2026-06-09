export type Job = {
  id: number;
  title: string;
  company: string;
  description: string;
  source: string;
  apply_url: string;
  posted_date: string | null;
  match_score: number | null;
  missing_skills: string[];
  match_reason: string | null;
  scraped_at: string;
};

export type JobSearchResponse = {
  total: number;
  jobs: Job[];
};
