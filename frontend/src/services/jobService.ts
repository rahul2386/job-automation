import { apiRequest } from "./api";
import type { Job, JobSearchResponse } from "../types/job";

export function getRecentJobs() {
  return apiRequest<Job[]>("/jobs");
}

export function searchJobs() {
  return apiRequest<JobSearchResponse>("/jobs/search", {
    method: "POST",
  });
}

export function matchJobs() {
  return apiRequest<JobSearchResponse>("/jobs/match", {
    method: "POST",
  });
}
