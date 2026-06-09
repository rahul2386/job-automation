import { apiRequest } from "./api";
import type { Resume } from "../types/resume";

export function getResume() {
  return apiRequest<Resume>("/resume");
}

export function uploadResume(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("user_id", "1");

  return apiRequest<Resume>("/resume/upload", {
    method: "POST",
    body: formData,
  });
}
