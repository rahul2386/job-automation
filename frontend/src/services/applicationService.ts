import { apiRequest } from "./api";
import type { Application, ApplicationBatchResponse, ApplicationStats } from "../types/application";

export function getApplications() {
  return apiRequest<Application[]>("/applications");
}

export function getApplicationStats() {
  return apiRequest<ApplicationStats>("/applications/stats");
}

export function applyToJob(jobId: number) {
  return apiRequest<Application>(`/applications/apply/${jobId}`, {
    method: "POST",
  });
}

export function autoApply(limit = 10) {
  return apiRequest<ApplicationBatchResponse>(`/applications/auto-apply?limit=${limit}`, {
    method: "POST",
  });
}
