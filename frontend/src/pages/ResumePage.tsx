import { useEffect, useState } from "react";
import { FileText, RefreshCcw } from "lucide-react";

import { ResumeUpload } from "../components/ResumeUpload";
import { API_BASE_URL } from "../services/api";
import { getResume, uploadResume } from "../services/resumeService";
import type { Resume } from "../types/resume";

export function ResumePage() {
  const [resume, setResume] = useState<Resume | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadResume() {
    setIsLoading(true);
    setError(null);
    try {
      setResume(await getResume());
    } catch (err) {
      setResume(null);
      if (err instanceof Error && !err.message.includes("No resume")) {
        setError(err.message);
      }
    } finally {
      setIsLoading(false);
    }
  }

  async function handleUpload(file: File) {
    setIsUploading(true);
    setError(null);
    try {
      setResume(await uploadResume(file));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to upload resume");
    } finally {
      setIsUploading(false);
    }
  }

  useEffect(() => {
    void loadResume();
  }, []);

  return (
    <main className="resume-page">
      <section className="top-bar">
        <div>
          <p className="eyebrow">Resume Module</p>
          <h1>Resume</h1>
        </div>
        <button className="icon-button" type="button" aria-label="Refresh resume" onClick={loadResume}>
          <RefreshCcw size={18} />
        </button>
      </section>

      <ResumeUpload isUploading={isUploading} onUpload={handleUpload} />

      {error ? <p className="error">{error}</p> : null}

      <section className="resume-layout">
        <div className="resume-summary">
          <div className="section-heading">
            <FileText size={20} />
            <h2>Uploaded Resume</h2>
          </div>
          {isLoading ? (
            <p className="muted">Loading resume...</p>
          ) : resume ? (
            <>
              <p className="file-name">{resume.file_name}</p>
              <p className="muted">Updated {new Date(resume.updated_at).toLocaleString()}</p>
              <a
                className="view-link"
                href={`${API_BASE_URL}/${resume.file_path.replace(/\\/g, "/")}`}
                target="_blank"
                rel="noreferrer"
              >
                View uploaded resume
              </a>
            </>
          ) : (
            <p className="muted">No resume uploaded yet.</p>
          )}
        </div>

        <div className="skills-panel">
          <h2>Extracted Skills</h2>
          {resume?.skills.length ? (
            <div className="skill-list">
              {resume.skills.map((skill) => (
                <span className="skill-chip" key={skill}>
                  {skill}
                </span>
              ))}
            </div>
          ) : (
            <p className="muted">Skills will appear after a PDF resume is parsed.</p>
          )}
        </div>
      </section>
    </main>
  );
}
