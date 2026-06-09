export type ResumeItem = {
  text: string;
};

export type Resume = {
  id: number;
  user_id: number;
  file_name: string;
  file_path: string;
  parsed_content: string | null;
  skills: string[];
  experience: ResumeItem[] | null;
  education: ResumeItem[] | null;
  projects: ResumeItem[] | null;
  created_at: string;
  updated_at: string;
};
