# AI Job Application Automation MVP - Architecture

## 1. FOLDER STRUCTURE

```
job_automation/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── resume.py
│   │   │   │   ├── jobs.py
│   │   │   │   ├── applications.py
│   │   │   │   └── users.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── resume_parser.py
│   │   │   ├── job_search.py
│   │   │   ├── job_matcher.py
│   │   │   ├── job_ranker.py
│   │   │   ├── job_applicator.py
│   │   │   └── embeddings.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── database.py
│   │   │   ├── user.py
│   │   │   ├── resume.py
│   │   │   ├── job.py
│   │   │   ├── application.py
│   │   │   └── job_search_config.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── resume.py
│   │   │   ├── job.py
│   │   │   └── application.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── logger.py
│   │   │   ├── validators.py
│   │   │   └── helpers.py
│   │   ├── tasks/
│   │   │   ├── __init__.py
│   │   │   ├── scheduled_jobs.py
│   │   │   └── job_search_scheduler.py
│   │   └── integrations/
│   │       ├── __init__.py
│   │       ├── groq_client.py
│   │       └── browser_automation.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   ├── requirements.txt
│   ├── .env.example
│   └── docker/
│       ├── Dockerfile
│       └── docker-compose.yml
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ResumeUpload.tsx
│   │   │   ├── JobSearch.tsx
│   │   │   ├── JobMatches.tsx
│   │   │   ├── ApplicationTracker.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   └── common/
│   │   ├── pages/
│   │   │   ├── Home.tsx
│   │   │   ├── Settings.tsx
│   │   │   ├── Applications.tsx
│   │   │   └── Analytics.tsx
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   ├── resumeService.ts
│   │   │   ├── jobService.ts
│   │   │   └── applicationService.ts
│   │   ├── hooks/
│   │   ├── types/
│   │   ├── styles/
│   │   ├── utils/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── docs/
│   ├── API.md
│   ├── DATABASE.md
│   └── SETUP.md
└── .gitignore
```

---

## 2. ARCHITECTURE

### Layered Architecture

```
┌─────────────────────────────────────────┐
│         Frontend (React/TypeScript)      │
│       TailwindCSS + React Router         │
└──────────────┬──────────────────────────┘
               │ Axios HTTP Calls
┌──────────────▼──────────────────────────┐
│       API Gateway (FastAPI)              │
│   - Authentication                       │
│   - Request Validation                   │
│   - Rate Limiting                        │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│     Business Logic Layer (Services)      │
│   - Resume Parser                        │
│   - Job Matcher                          │
│   - Job Ranker                           │
│   - Job Applicator                       │
│   - Embeddings Generator                 │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│    Data Access Layer (SQLAlchemy ORM)   │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│    Database Layer (PostgreSQL)           │
│    + Vector Store (FAISS)                │
└──────────────────────────────────────────┘
```

### Async Processing Flow

```
User Resume Upload
    ↓
[API Endpoint] → Queue Resume Parsing Task
    ↓
[APScheduler] → Trigger Job Search (every X hours)
    ↓
[Job Search Service] → Search Multiple Sources
    ↓
[Embeddings Service] → Generate & Store Embeddings
    ↓
[Job Matcher + FAISS] → Match Jobs to Resume
    ↓
[Job Ranker] → Rank by Score + Context
    ↓
[Browser Automation] → Auto-Apply (Playwright)
    ↓
[Application Tracker] → Record Status
```

---

## 3. SERVICE RESPONSIBILITIES

| Service | Responsibility |
|---------|-----------------|
| **ResumeParser** | Extract text from PDF/DOCX, parse skills, experience, education, contact info |
| **JobSearch** | Query job APIs (LinkedIn, Indeed, etc.), fetch job listings |
| **Embeddings** | Generate vector embeddings using SentenceTransformers for resume & jobs |
| **JobMatcher** | Use FAISS to find similar jobs based on resume embeddings |
| **JobRanker** | Rank matched jobs by relevance score using Groq LLM contextual analysis |
| **JobApplicator** | Automate job applications using Playwright browser automation |
| **ApplicationTracker** | Store & track application status, responses, rejections |
| **UserService** | Manage user authentication, profiles, preferences |
| **SchedulerService** | Orchestrate periodic job searches and auto-applications |

---

## 4. API LIST

### Resume Endpoints
- `POST /api/v1/resume/upload` - Upload resume file
- `GET /api/v1/resume/{resume_id}` - Get parsed resume
- `PUT /api/v1/resume/{resume_id}` - Update resume
- `DELETE /api/v1/resume/{resume_id}` - Delete resume

### Job Search Endpoints
- `POST /api/v1/jobs/search` - Trigger job search
- `GET /api/v1/jobs` - Get all jobs
- `GET /api/v1/jobs/{job_id}` - Get job details
- `GET /api/v1/jobs/matched` - Get matched jobs for resume

### Matching & Ranking Endpoints
- `POST /api/v1/jobs/match` - Match jobs to resume
- `GET /api/v1/jobs/ranked` - Get ranked job list
- `POST /api/v1/jobs/analyze` - Analyze job compatibility (Groq)

### Application Endpoints
- `POST /api/v1/applications` - Create application
- `GET /api/v1/applications` - List applications
- `GET /api/v1/applications/{app_id}` - Get application details
- `PUT /api/v1/applications/{app_id}/status` - Update application status
- `DELETE /api/v1/applications/{app_id}` - Delete application
- `POST /api/v1/applications/auto-apply` - Trigger auto-apply

### User Endpoints
- `POST /api/v1/users/register` - Register user
- `POST /api/v1/users/login` - Login user
- `GET /api/v1/users/profile` - Get user profile
- `PUT /api/v1/users/profile` - Update user profile
- `POST /api/v1/users/preferences` - Set search preferences

### Analytics Endpoints
- `GET /api/v1/analytics/dashboard` - Get dashboard metrics
- `GET /api/v1/analytics/success-rate` - Application success rate
- `GET /api/v1/analytics/job-sources` - Top job sources

---

## 5. DATABASE TABLES

### Users Table
```sql
users:
  - id (PK)
  - email (UNIQUE)
  - password_hash
  - first_name
  - last_name
  - created_at
  - updated_at
```

### Resumes Table
```sql
resumes:
  - id (PK)
  - user_id (FK)
  - file_name
  - file_path
  - parsed_content (JSON)
  - skills (JSON[])
  - experience (JSON[])
  - education (JSON[])
  - embeddings (VECTOR)
  - created_at
  - updated_at
```

### Jobs Table
```sql
jobs:
  - id (PK)
  - title
  - company
  - location
  - job_url
  - description
  - requirements (JSON[])
  - salary_min
  - salary_max
  - job_source (LinkedIn, Indeed, etc.)
  - embeddings (VECTOR)
  - posted_date
  - scraped_at
  - created_at
```

### Job Search Configs Table
```sql
job_search_configs:
  - id (PK)
  - user_id (FK)
  - keywords (JSON[])
  - locations (JSON[])
  - salary_range (JSON)
  - job_types (JSON[])
  - experience_level (JSON[])
  - active (BOOLEAN)
  - search_interval (INTERVAL)
  - last_searched_at
  - created_at
  - updated_at
```

### Job Matches Table
```sql
job_matches:
  - id (PK)
  - resume_id (FK)
  - job_id (FK)
  - match_score (FLOAT)
  - match_reason (TEXT)
  - matched_at
  - created_at
```

### Job Ranks Table
```sql
job_ranks:
  - id (PK)
  - job_id (FK)
  - resume_id (FK)
  - rank (INT)
  - relevance_score (FLOAT)
  - groq_analysis (TEXT)
  - ranked_at
  - created_at
```

### Applications Table
```sql
applications:
  - id (PK)
  - user_id (FK)
  - job_id (FK)
  - resume_id (FK)
  - application_url
  - status (PENDING, SUBMITTED, VIEWED, REJECTED, OFFER)
  - applied_at
  - response_received_at
  - response_content (TEXT)
  - applied_via_automation (BOOLEAN)
  - created_at
  - updated_at
```

### Application Logs Table
```sql
application_logs:
  - id (PK)
  - application_id (FK)
  - event_type (SUBMITTED, VIEWED, RESPONDED, etc.)
  - details (JSON)
  - created_at
```

### Embeddings Cache Table
```sql
embeddings_cache:
  - id (PK)
  - entity_type (resume, job)
  - entity_id
  - embedding_vector (VECTOR)
  - model_name
  - created_at
```

---

**Ready for implementation specifications.**
