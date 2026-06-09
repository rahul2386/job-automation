import { useState } from "react";

import { ApplicationsPage } from "./pages/ApplicationsPage";
import { JobsPage } from "./pages/JobsPage";
import { ResumePage } from "./pages/ResumePage";
import "./styles.css";

export default function App() {
  const [page, setPage] = useState<"resume" | "jobs" | "applications">("jobs");

  return (
    <>
      <nav className="app-nav">
        <button className={page === "jobs" ? "nav-button active" : "nav-button"} type="button" onClick={() => setPage("jobs")}>
          Jobs
        </button>
        <button
          className={page === "applications" ? "nav-button active" : "nav-button"}
          type="button"
          onClick={() => setPage("applications")}
        >
          Applications
        </button>
        <button
          className={page === "resume" ? "nav-button active" : "nav-button"}
          type="button"
          onClick={() => setPage("resume")}
        >
          Resume
        </button>
      </nav>
      {page === "jobs" ? <JobsPage /> : null}
      {page === "applications" ? <ApplicationsPage /> : null}
      {page === "resume" ? <ResumePage /> : null}
    </>
  );
}
