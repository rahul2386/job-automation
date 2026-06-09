import { useEffect, useState } from "react";
import { RefreshCcw, Search, Send, Sparkles } from "lucide-react";

import { applyToJob, autoApply, getApplications } from "../services/applicationService";
import { getRecentJobs, matchJobs, searchJobs } from "../services/jobService";
import type { Application } from "../types/application";
import type { Job } from "../types/job";

function formatDate(value: string | null) {
  if (!value) {
    return "Unknown";
  }
  return new Date(value).toLocaleDateString();
}

export function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [isMatching, setIsMatching] = useState(false);
  const [isAutoApplyEnabled, setIsAutoApplyEnabled] = useState(false);
  const [isAutoApplying, setIsAutoApplying] = useState(false);
  const [applyingJobId, setApplyingJobId] = useState<number | null>(null);
  const [applicationsByJobId, setApplicationsByJobId] = useState<Record<number, Application>>({});
  const [error, setError] = useState<string | null>(null);

  async function loadJobs() {
    setIsLoading(true);
    setError(null);
    try {
      const [recentJobs, applications] = await Promise.all([getRecentJobs(), getApplications()]);
      setJobs(recentJobs);
      rememberApplications(applications);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to fetch jobs");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSearch() {
    setIsSearching(true);
    setError(null);
    try {
      const result = await searchJobs();
      setJobs(result.jobs);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to search jobs");
    } finally {
      setIsSearching(false);
    }
  }

  function rememberApplications(applications: Application[]) {
    setApplicationsByJobId((current) => {
      const next = { ...current };
      for (const application of applications) {
        next[application.job_id] = application;
      }
      return next;
    });
  }

  async function handleApply(jobId: number) {
    setApplyingJobId(jobId);
    setError(null);
    try {
      rememberApplications([await applyToJob(jobId)]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to apply to job");
    } finally {
      setApplyingJobId(null);
    }
  }

  async function handleAutoApply() {
    setIsAutoApplying(true);
    setError(null);
    try {
      const result = await autoApply();
      rememberApplications(result.applications);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to auto apply");
    } finally {
      setIsAutoApplying(false);
    }
  }

  async function handleMatch() {
    setIsMatching(true);
    setError(null);
    try {
      const result = await matchJobs();
      setJobs(result.jobs);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to match jobs");
    } finally {
      setIsMatching(false);
    }
  }

  useEffect(() => {
    void loadJobs();
  }, []);

  return (
    <main className="page-shell">
      <section className="top-bar">
        <div>
          <p className="eyebrow">Job Search Module</p>
          <h1>Recent Jobs</h1>
        </div>
        <button className="icon-button" type="button" aria-label="Refresh jobs" onClick={loadJobs}>
          <RefreshCcw size={18} />
        </button>
      </section>

      <section className="toolbar-panel">
        <div className="toolbar-actions">
          <button className="primary-button" type="button" disabled={isSearching} onClick={handleSearch}>
            <Search size={18} />
            {isSearching ? "Searching..." : "Search Jobs"}
          </button>
          <button className="secondary-button" type="button" disabled={isMatching} onClick={handleMatch}>
            <Sparkles size={18} />
            {isMatching ? "Matching..." : "Match Jobs"}
          </button>
          <button
            className="secondary-button"
            type="button"
            disabled={!isAutoApplyEnabled || isAutoApplying}
            onClick={handleAutoApply}
          >
            <Send size={18} />
            {isAutoApplying ? "Applying..." : "Auto Apply"}
          </button>
          <label className="toggle-control">
            <input
              type="checkbox"
              checked={isAutoApplyEnabled}
              onChange={(event) => setIsAutoApplyEnabled(event.target.checked)}
            />
            <span>Auto Apply</span>
          </label>
        </div>
        <span className="muted">{jobs.length} recent jobs</span>
      </section>

      {error ? <p className="error">{error}</p> : null}

      <section className="table-panel">
        <table className="jobs-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Company</th>
              <th>Match Score</th>
              <th>Missing Skills</th>
              <th>Match Reason</th>
              <th>Posted Date</th>
              <th>Application</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={7}>Loading jobs...</td>
              </tr>
            ) : jobs.length ? (
              jobs.map((job) => (
                <tr key={job.id}>
                  <td>
                    <a href={job.apply_url} target="_blank" rel="noreferrer">
                      {job.title}
                    </a>
                  </td>
                  <td>{job.company}</td>
                  <td>{Math.round(job.match_score ?? 0)}%</td>
                  <td>
                    {job.missing_skills?.length ? (
                      <div className="mini-chip-list">
                        {job.missing_skills.map((skill) => (
                          <span className="mini-chip" key={`${job.id}-${skill}`}>
                            {skill}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="muted">None</span>
                    )}
                  </td>
                  <td className="reason-cell">{job.match_reason || "Not matched yet."}</td>
                  <td>{formatDate(job.posted_date)}</td>
                  <td>
                    {applicationsByJobId[job.id] ? (
                      <span className={applicationsByJobId[job.id].status === "Applied" ? "status-applied" : "status-failed"}>
                        {applicationsByJobId[job.id].status}
                      </span>
                    ) : (
                      <button
                        className="table-action"
                        type="button"
                        disabled={applyingJobId === job.id}
                        onClick={() => void handleApply(job.id)}
                      >
                        {applyingJobId === job.id ? "Applying..." : "Apply"}
                      </button>
                    )}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={7}>No recent jobs found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </main>
  );
}
