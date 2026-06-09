import { useEffect, useState } from "react";
import { RefreshCcw } from "lucide-react";

import { getApplications, getApplicationStats } from "../services/applicationService";
import type { Application, ApplicationStats } from "../types/application";

function formatDate(value: string) {
  return new Date(value).toLocaleString();
}

const emptyStats: ApplicationStats = {
  total_jobs_found: 0,
  total_applied: 0,
  success_rate: 0,
  failed_applications: 0,
};

export function ApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [stats, setStats] = useState<ApplicationStats>(emptyStats);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadTracker() {
    setIsLoading(true);
    setError(null);
    try {
      const [applicationRows, statRows] = await Promise.all([getApplications(), getApplicationStats()]);
      setApplications(applicationRows);
      setStats(statRows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load application tracker");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadTracker();
  }, []);

  return (
    <main className="page-shell">
      <section className="top-bar">
        <div>
          <p className="eyebrow">Application Tracker</p>
          <h1>Applications</h1>
        </div>
        <button className="icon-button" type="button" aria-label="Refresh applications" onClick={loadTracker}>
          <RefreshCcw size={18} />
        </button>
      </section>

      <section className="dashboard-grid">
        <div className="metric-card">
          <span>Total Jobs Found</span>
          <strong>{stats.total_jobs_found}</strong>
        </div>
        <div className="metric-card">
          <span>Total Applied</span>
          <strong>{stats.total_applied}</strong>
        </div>
        <div className="metric-card">
          <span>Success Rate</span>
          <strong>{stats.success_rate}%</strong>
        </div>
        <div className="metric-card">
          <span>Failed Applications</span>
          <strong>{stats.failed_applications}</strong>
        </div>
      </section>

      {error ? <p className="error">{error}</p> : null}

      <section className="table-panel">
        <table className="applications-table">
          <thead>
            <tr>
              <th>Company</th>
              <th>Job Title</th>
              <th>Status</th>
              <th>Applied Date</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={4}>Loading applications...</td>
              </tr>
            ) : applications.length ? (
              applications.map((application) => (
                <tr key={application.id}>
                  <td>{application.company ?? "Unknown"}</td>
                  <td>{application.job_title ?? `Job #${application.job_id}`}</td>
                  <td>
                    <span className={application.status === "Applied" ? "status-applied" : "status-failed"}>
                      {application.status}
                    </span>
                  </td>
                  <td>{formatDate(application.applied_at)}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={4}>No applications tracked yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </main>
  );
}
