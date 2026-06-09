# Database Schema - Job Automation MVP

## 1. ENTITY RELATIONSHIP DIAGRAM

```
┌─────────────────────┐
│       USERS         │
├─────────────────────┤
│ id (PK)             │
│ email (UNIQUE)      │
│ password_hash       │
│ first_name          │
│ last_name           │
│ created_at          │
│ updated_at          │
└──────────┬──────────┘
           │ 1
           │ (one-to-one)
           │
           ▼
┌─────────────────────┐
│     RESUMES         │
├─────────────────────┤
│ id (PK)             │
│ user_id (FK,UQ)     │◄──┐ One user = One resume
│ file_name           │   │
│ file_path           │   │
│ parsed_content      │   │
│ skills (ARRAY)      │   │
│ experience (JSON)   │   │
│ education (JSON)    │   │
│ contact_info (JSON) │   │
│ embeddings (JSON)   │   │
│ created_at          │   │
│ updated_at          │   │
└─────────────────────┘   │


┌──────────────────────────┐
│        SKILLS            │
├──────────────────────────┤
│ id (PK)                  │
│ name (UNIQUE)            │
│ category                 │
│ created_at               │
└──────────────────────────┘


┌──────────────────────────┐         ┌──────────────────────────┐
│       JOBS               │         │   APPLICATIONS           │
├──────────────────────────┤         ├──────────────────────────┤
│ id (PK)                  │◄────────│ job_id (FK)              │
│ title                    │ 1    N  │ user_id (FK)             │
│ company                  │         │ resume_id (FK)           │
│ location                 │         │ status                   │
│ salary                   │         │ applied_at               │
│ salary_min               │         │ response_received_at     │
│ salary_max               │         │ response_content         │
│ source                   │         │ applied_via_automation   │
│ apply_url (UNIQUE)       │         │ created_at               │
│ description              │         │ updated_at               │
│ requirements (ARRAY)     │         │                          │
│ posted_date              │         │ (UQ: user_id + job_id)   │
│ match_score              │         │                          │
│ embeddings (JSON)        │         └──────────────────────────┘
│ scraped_at               │                    │
│ created_at               │                    │
│ updated_at               │                    │ (FK)
└──────────────────────────┘                    │
                                                ▼
                                         ┌──────────────────┐
                                         │      USERS       │
                                         │   (resume_id)    │
                                         └──────────────────┘
```

---

## 2. TABLE SCHEMAS

### USERS
- **Purpose**: Store user account information
- **Primary Key**: id
- **Unique Constraints**: email
- **Indexes**:
  - `idx_user_email` on email
  - `idx_user_created_at` on created_at

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | INTEGER | PK | Auto-increment |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Login identifier |
| password_hash | VARCHAR(255) | NOT NULL | Hashed password |
| first_name | VARCHAR(100) | | User's first name |
| last_name | VARCHAR(100) | | User's last name |
| created_at | DATETIME | NOT NULL | Timestamp |
| updated_at | DATETIME | NOT NULL | Timestamp |

---

### RESUMES
- **Purpose**: Store user resume data and metadata
- **Primary Key**: id
- **Foreign Keys**: user_id → users.id (UNIQUE - one resume per user)
- **Indexes**:
  - `idx_resume_user_id` on user_id
  - `idx_resume_created_at` on created_at

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | INTEGER | PK | Auto-increment |
| user_id | INTEGER | FK(users), UNIQUE, NOT NULL | Link to user (1-to-1) |
| file_name | VARCHAR(255) | NOT NULL | Original filename |
| file_path | VARCHAR(500) | NOT NULL | Storage location |
| parsed_content | TEXT | | Full text extracted from PDF/DOCX |
| skills | ARRAY(VARCHAR) | DEFAULT [] | Extracted skills list |
| experience | JSON | | Work experience details |
| education | JSON | | Education details |
| contact_info | JSON | | Phone, address, links |
| embeddings | JSON | | Vector embeddings from SentenceTransformers |
| created_at | DATETIME | NOT NULL | Timestamp |
| updated_at | DATETIME | NOT NULL | Timestamp |

---

### SKILLS
- **Purpose**: Reference table for all skills
- **Primary Key**: id
- **Unique Constraints**: name
- **Indexes**:
  - `idx_skill_name` on name
  - `idx_skill_category` on category

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | INTEGER | PK | Auto-increment |
| name | VARCHAR(100) | UNIQUE, NOT NULL | Skill name (Python, React, etc.) |
| category | VARCHAR(50) | | Category (Language, Framework, Tool) |
| created_at | DATETIME | NOT NULL | Timestamp |

---

### JOBS
- **Purpose**: Store job listings from various sources
- **Primary Key**: id
- **Unique Constraints**: apply_url
- **Indexes**:
  - `idx_job_title` on title
  - `idx_job_company` on company
  - `idx_job_location` on location
  - `idx_job_source` on source
  - `idx_job_posted_date` on posted_date
  - `idx_job_created_at` on created_at
  - `idx_job_match_score` on match_score

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | INTEGER | PK | Auto-increment |
| title | VARCHAR(255) | NOT NULL, INDEX | Job title |
| company | VARCHAR(255) | NOT NULL, INDEX | Company name |
| location | VARCHAR(255) | NOT NULL | Job location |
| salary | VARCHAR(100) | | Display salary range (e.g., "$80k-$120k") |
| salary_min | FLOAT | | Minimum salary parsed |
| salary_max | FLOAT | | Maximum salary parsed |
| source | VARCHAR(50) | NOT NULL, INDEX | LinkedIn, Indeed, Glassdoor, etc. |
| apply_url | VARCHAR(500) | UNIQUE, NOT NULL | Direct apply link |
| description | TEXT | NOT NULL | Full job description |
| requirements | ARRAY(VARCHAR) | DEFAULT [] | Required skills/qualifications |
| posted_date | DATETIME | INDEX | When job was posted |
| match_score | FLOAT | DEFAULT 0.0, INDEX | Relevance score vs. resume (0-100) |
| embeddings | JSON | | Vector embeddings for matching |
| scraped_at | DATETIME | NOT NULL | When job was scraped |
| created_at | DATETIME | NOT NULL, INDEX | Timestamp |
| updated_at | DATETIME | NOT NULL | Timestamp |

---

### APPLICATIONS
- **Purpose**: Track user applications to jobs
- **Primary Key**: id
- **Foreign Keys**: 
  - user_id → users.id
  - job_id → jobs.id
  - resume_id → resumes.id
- **Unique Constraints**: (user_id, job_id) - prevent duplicate applications
- **Indexes**:
  - `idx_application_user_id` on user_id
  - `idx_application_job_id` on job_id
  - `idx_application_resume_id` on resume_id
  - `idx_application_status` on status
  - `idx_application_created_at` on created_at

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | INTEGER | PK | Auto-increment |
| user_id | INTEGER | FK(users), NOT NULL, INDEX | Application owner |
| job_id | INTEGER | FK(jobs), NOT NULL, INDEX | Applied job |
| resume_id | INTEGER | FK(resumes), NOT NULL, INDEX | Resume used |
| status | VARCHAR(50) | NOT NULL, DEFAULT 'PENDING', INDEX | PENDING, SUBMITTED, VIEWED, REJECTED, OFFER |
| applied_at | DATETIME | NOT NULL | When application was sent |
| response_received_at | DATETIME | | When response was received |
| response_content | TEXT | | Rejection/feedback message |
| applied_via_automation | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether auto-applied by system |
| created_at | DATETIME | NOT NULL, INDEX | Timestamp |
| updated_at | DATETIME | NOT NULL | Timestamp |

---

## 3. RELATIONSHIPS

### User → Resume (1:1)
- One user has exactly one resume
- Cascade delete: If user deleted, resume is deleted
- Foreign key constraint ensures referential integrity

### User → Applications (1:N)
- One user can have many applications
- Cascade delete: If user deleted, applications are deleted

### Job → Applications (1:N)
- One job can have many applications from different users
- Cascade delete: If job deleted, applications are deleted

### Resume → Applications (1:N)
- One resume can be used for multiple applications
- Links which resume was used for each application

---

## 4. KEY INDEXES FOR QUERY PERFORMANCE

**User Queries:**
- `idx_user_email` - Fast login lookups
- `idx_user_created_at` - Recent user analysis

**Resume Queries:**
- `idx_resume_user_id` - Quick resume lookup by user
- `idx_resume_created_at` - Track resume updates

**Skill Queries:**
- `idx_skill_name` - Quick skill lookup
- `idx_skill_category` - Filter by category

**Job Queries:**
- `idx_job_title` - Search by title
- `idx_job_company` - Company-based searches
- `idx_job_location` - Location-based searches
- `idx_job_source` - Filter by source
- `idx_job_posted_date` - Recent jobs first
- `idx_job_match_score` - Sort by relevance
- `idx_job_created_at` - Time-series analysis

**Application Queries:**
- `idx_application_user_id` - User's applications
- `idx_application_status` - Status-based reporting
- `idx_application_created_at` - Application timeline

---

## 5. CREATE TABLE SQL GENERATION

To create tables from SQLAlchemy models:

```python
from app.models import Base, engine

# Create all tables
Base.metadata.create_all(bind=engine)
```

Or use Alembic for migrations:

```bash
alembic init alembic
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

---

## 6. CONSTRAINTS & INTEGRITY

| Constraint | Type | Purpose |
|-----------|------|---------|
| `email` (users) | UNIQUE | Prevent duplicate accounts |
| `user_id` (resumes) | UNIQUE | One resume per user |
| `apply_url` (jobs) | UNIQUE | Prevent duplicate job postings |
| `(user_id, job_id)` (applications) | UNIQUE | Prevent duplicate applications |
| Foreign keys | Referential | Maintain data integrity |
| NOT NULL constraints | Data validity | Ensure required fields exist |
