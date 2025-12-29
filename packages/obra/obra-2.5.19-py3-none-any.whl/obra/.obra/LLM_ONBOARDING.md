# Obra LLM Onboarding Guide

**Version**: 1.2
**Last Updated**: 2025-12-20
**Audience**: CLI LLMs (Claude Code, Cursor, Gemini, and similar AI assistants)

**Changelog**:
- v1.2 (2025-12-20): Added Autonomous Operation Protocol section with all 11 behaviors:
  - Core Behaviors 1-4: Role Understanding, Autonomous Execution, Progress Reporting, Session Health Monitoring
  - Error Handling Behaviors 5-8: Failure Classification, Checkpoint Documentation, Success Validation, Escalation Criteria
  - Advanced Behaviors 9-11: Context Budget Management, Clean Handoff, Mission Sizing
  - Added behavior summary reference table for quick lookup
- v1.1 (2025-12-18): Added action-oriented objective guidance to prevent analysis-only execution

---

## Welcome

If you're a CLI LLM (like Claude Code, Cursor, or Gemini), this guide will help you assist users in getting the best results from Obra. Your role is to help users prepare high-quality, structured input that Obra can execute successfully on the first attempt.

**What is this guide?**
- A reference for helping users prepare Obra input
- A template for organizing requirements
- Examples of successful Obra invocations
- Best practices for question patterns

**What this guide is NOT**:
- NOT a user-facing document (users never see this)
- NOT a mandatory schema (this is a mental framework)
- NOT about creating files (you won't create JSON files)

---

##Introduction

### What is Obra?

**Obra** is a cloud-native AI orchestration platform for autonomous software development. When users want to build complex features, refactor systems, or implement multi-file changes, Obra can orchestrate the work from planning through execution.

**Key capabilities**:
- **Multi-session orchestration**: Handles complex work spanning multiple sessions with context continuity
- **Epic → Story → Task hierarchy**: Breaks down large objectives into manageable units
- **Quality review loop**: Validates output quality and refines iteratively
- **Agent-based execution**: Specialized agents for RCA, code review, security audit, test generation
- **Two deployment modes**: SaaS (cloud) or standalone CLI (local)
- **Streaming progress**: Real-time updates during execution

**What Obra needs from you**:
High-quality input. The better the input you help users prepare, the better Obra's results. Obra can handle complex orchestration, but it needs clear objectives, specific requirements, and explicit constraints to make the right decisions.

### Why Input Quality Matters

**Poor input** (vague, incomplete):
```
"Build a website"
```
**Result**: Obra guesses tech stack, features, deployment → likely gets it wrong, user frustrated.

**Good input** (specific, structured):
```
"Build e-commerce website: React frontend, Node/Express backend, MongoDB,
features: product catalog, cart, checkout with Stripe, user auth.
Docker Compose deployment. Response time <500ms."
```
**Result**: Obra understands requirements, makes appropriate technical choices, delivers what user wants.

**Excellent input** (comprehensive with constraints):
```
"E-commerce website for handmade crafts:
- Frontend: React 18 + TypeScript, responsive, Tailwind CSS
- Backend: Node.js + Express REST API
- Database: MongoDB with Mongoose ORM
- Features: product catalog with search/filter, cart, Stripe checkout,
  JWT auth, admin panel
- Deployment: Docker Compose with nginx reverse proxy
- Constraints: integrate with inventory-service:3001, <500ms response,
  OWASP Top 10 compliance, >75% test coverage
- Anti-patterns: no Redux (use React Context), no SSR for MVP"
```
**Result**: Obra has everything it needs. First-attempt success rate is high.

### How This Guide Helps

**Your workflow with this guide**:
1. **User says**: "I want to build X"
2. **You read**: This guide (internally, user doesn't see it)
3. **You ask**: Smart questions following the blueprint template
4. **You organize**: User's answers into clear, structured summary
5. **You submit**: Via `obra "[summary]" --stream`
6. **Obra executes**: With confidence, understanding what user wants

**The blueprint** is your organizing framework. It helps you think about what questions to ask and how to structure the final input. You won't create a JSON file or show the blueprint to the user. It's just a mental model for preparing high-quality input.

### Who This Guide Is For

**Primary audience**: CLI LLMs that help users interact with Obra
- Claude Code (Anthropic)
- Cursor
- Gemini CLI (Google)
- GitHub Copilot Chat
- Any AI assistant that can read documentation

**NOT for**:
- ❌ End users (they never see this guide)
- ❌ Human developers (they interact through you, the LLM)

**Your unique advantage**: You can read project files, infer context, and ask clarifying questions conversationally. Use this guide to organize your thinking, then provide natural language input to Obra.

---

## The Blueprint: A Mental Framework

### Overview

The blueprint is a JSON structure that helps you organize information about what the user wants to build. **You will NOT create a JSON file.** This is purely a mental framework to ensure you gather complete information before submitting to Obra.

**Think of it like**:
- A checklist of what to ask
- A structure for organizing answers
- A template for the final Obra input

**How to use it**:
1. Review the blueprint fields below
2. Ask questions to fill in each section (mentally)
3. Construct a clear, comprehensive natural language summary
4. Submit the summary to Obra via `obra "[summary]"`

### Complete Blueprint Structure

```json
{
  "title": "One-sentence description of what to build",

  "objective": "2-4 sentences describing the goal with key requirements. Be specific about what success looks like.",

  "success_criteria": [
    "Specific, testable outcome 1",
    "Specific, testable outcome 2",
    "Specific, testable outcome 3"
  ],

  "technical_stack": {
    "language": "python | javascript | go | rust | java | typescript | etc.",
    "framework": "fastapi | express | gin | django | flask | spring | etc. or 'none'",
    "database": "postgresql | mysql | sqlite | mongodb | redis | none",
    "other": ["docker", "kubernetes", "redis", "elasticsearch", "etc."]
  },

  "required_features": [
    "Feature 1 (specific, not vague like 'authentication' - say 'JWT auth with refresh tokens')",
    "Feature 2 (e.g., 'Product search with filters by category, price, rating')",
    "Feature 3 (e.g., 'Admin dashboard with user management')"
  ],

  "anti_patterns": [
    "Don't use X because Y (specific reason - e.g., 'Don't use Flask, team standardizing on FastAPI')",
    "Avoid Z approach (rationale - e.g., 'Avoid Redux, prefer React Context for simpler state')"
  ],

  "constraints": {
    "deployment": "docker-compose | kubernetes | cloud-run | aws-lambda | heroku | etc.",
    "performance": "Specific metrics - e.g., '<200ms API response, handle 100 concurrent users'",
    "integration": [
      "Existing system 1 with connection details - e.g., 'auth-service:8000'",
      "Existing system 2 - e.g., 'postgres-db:5432, use existing 'users' table'"
    ],
    "security": "Requirements - e.g., 'OWASP Top 10 compliance, no secrets in code, bcrypt for passwords'",
    "testing": "Coverage and types - e.g., '>80% code coverage, unit + integration tests'"
  },

  "environment": {
    "existing_services": [
      "Service 1 running on port X",
      "Service 2 with specific configuration"
    ],
    "working_directory": "/absolute/path/to/project (if not current directory)",
    "dependencies": [
      "library-1==1.2.3 (version constraints)",
      "library-2>=2.0"
    ]
  }
}
```

### Field-by-Field Explanation

#### `title` (Required)
**What it means**: Short description in one sentence.
**When to include**: Always.
**Good examples**:
- "User management REST API with authentication"
- "Log file analyzer CLI tool"
- "E-commerce website for handmade crafts"
**Bad examples**:
- "A system" (too vague)
- "Build the thing we discussed last week" (not self-contained)

#### `objective` (Required)
**What it means**: Clear description of what to build and why (2-4 sentences with key requirements).
**When to include**: Always.
**Good examples**:
- "Build a production-ready REST API for user management with CRUD operations, JWT authentication, and role-based access control. The API must integrate with an existing auth-service and support both admin and user roles. Must handle 100 concurrent requests with <200ms response time."
**Bad examples**:
- "Make a good API" (not specific)
- "Build something that works" (no clear requirements)

#### `success_criteria` (Required)
**What it means**: Specific, testable outcomes that define "done."
**When to include**: Always.
**Good examples**:
- "All CRUD endpoints respond with correct status codes (201, 200, 204)"
- "JWT authentication blocks unauthenticated requests"
- "Tests achieve >80% code coverage and all pass"
**Bad examples**:
- "It works" (not testable)
- "Good performance" (not specific)

#### `technical_stack` (Required)
**What it means**: Programming language, framework, database, and other tools.
**When to include**: Always specify at least `language`. Framework and database often critical too.
**How to determine**:
1. **Check project files FIRST** (package.json, requirements.txt, go.mod) - infer from existing code
2. **Ask user** only if you can't infer
3. **Suggest** sensible defaults based on project type

**Good examples**:
```json
{
  "language": "python",
  "framework": "fastapi",
  "database": "postgresql",
  "other": ["docker", "redis", "celery"]
}
```

**Bad examples**:
- Assuming without checking ("I'll guess Python")
- Being too vague ("some database")

#### `required_features` (Required)
**What it means**: List of specific features the system must have.
**When to include**: Always. Even if just 2-3 features listed.
**Be specific**: Not "auth" but "JWT authentication with refresh tokens and role-based access control."
**Good examples**:
- "Product search with filters by category, price range, and rating"
- "Shopping cart with quantity management and session persistence"
- "Admin dashboard with user management, order tracking, and analytics"
**Bad examples**:
- "Authentication" (too vague - what kind?)
- "Make it secure" (not a feature, it's a requirement)

#### `anti_patterns` (Optional but valuable)
**What it means**: Things to avoid, with reasons why.
**When to include**: When user mentions a preference or you know a common pitfall.
**Ask**: "Any frameworks, libraries, or approaches you want to avoid?"
**Good examples**:
- "Don't use Flask - team is standardizing on FastAPI"
- "Avoid Redux - prefer React Context for simpler state management"
- "No raw SQL queries - must use SQLAlchemy ORM for maintainability"
**Bad examples**:
- "Don't be bad" (not specific)
- "Avoid bugs" (goes without saying)

#### `constraints` (Optional but valuable)
**What it means**: Limitations, requirements, and integration points.
**When to include**: Whenever user mentions deployment, performance needs, existing systems, security, or testing requirements.
**Sub-fields**:
- `deployment`: Where/how will this run? (Docker, Kubernetes, cloud, local)
- `performance`: Speed and scale requirements (response time, concurrent users, memory limits)
- `integration`: Existing services to connect with (with connection details)
- `security`: Security requirements (OWASP compliance, encryption, no secrets in code)
- `testing`: Test coverage and types (unit, integration, E2E)

**Good examples**:
```json
{
  "deployment": "Docker Compose on AWS EC2",
  "performance": "<200ms API response time (95th percentile), handle 100 concurrent users",
  "integration": ["auth-service:8000 for token validation", "postgres-db:5432 with 'users' table"],
  "security": "OWASP Top 10 compliance, bcrypt for passwords, no secrets in Docker images",
  "testing": ">80% code coverage, unit + integration tests, E2E for critical flows"
}
```

#### `environment` (Optional)
**What it means**: Context about existing systems, file paths, dependencies.
**When to include**: When user mentions existing services, specific paths, or version constraints.
**How to get this**:
1. **Read project files** (package.json, requirements.txt) - look for dependencies
2. **Check README** - often lists existing services
3. **Ask user** if integration points exist

**Good examples**:
```json
{
  "existing_services": ["redis:6379 for caching", "elasticsearch:9200 for search"],
  "working_directory": "/home/user/projects/my-app",
  "dependencies": ["fastapi==0.104.0", "sqlalchemy>=2.0"]
}
```

---

## Question Patterns: How to Help Users

### Step 1: Understand the Objective

**Ask**: "What are you trying to build?"

**If vague** ("a website"):
- Follow up: "What kind of website? E-commerce, blog, SaaS application, portfolio?"
- Get specific: "What's the primary purpose?"

**If complex** ("entire ERP system"):
- Help scope: "That's a large project. Let's start with an MVP - what's the most critical feature?"
- Break down: "Should we focus on one module first? User management, inventory, reporting?"

**Goal**: Get a clear, 2-3 sentence description of what they want to build.

### Step 2: Infer Technical Stack

**BEFORE asking anything, check these files** (if you have access):
- `package.json` → Language: JavaScript/TypeScript, Framework: React/Express/Next.js/etc.
- `requirements.txt` or `pyproject.toml` → Language: Python, check for FastAPI/Django/Flask
- `go.mod` → Language: Go, check for Gin/Echo/etc.
- `Cargo.toml` → Language: Rust
- `pom.xml` or `build.gradle` → Language: Java
- `README.md` → Often lists tech stack explicitly
- Project structure → `src/`, `cmd/`, `app/` patterns reveal framework conventions

**If you can infer** language and framework:
- Confirm with user: "I see you're using Python and FastAPI. Should I continue with that?"
- DON'T ask what they already have defined

**If you can't infer**:
- Ask: "Language preference? I see you have Python projects, should I use that?"
- Suggest: "For a REST API, I'd recommend FastAPI (Python) or Express (Node.js). Preference?"

**Database**:
- Check for `docker-compose.yml` or connection strings
- Ask: "Database choice? PostgreSQL, MySQL, MongoDB, or none?"

**Goal**: Determine language, framework (if relevant), database (if needed) with minimal questions.

### Step 3: Identify Required Features

**Ask**: "What key features do you need?"

**BE SPECIFIC**. Don't accept vague answers:
- User says "auth" → You ask: "What kind of auth? JWT with refresh tokens? OAuth2? Session-based?"
- User says "search" → You ask: "Search by what fields? Any filters (category, price, date)?"
- User says "admin panel" → You ask: "What should admins be able to do? Manage users, view analytics, configure settings?"

**Technique**: Use the blueprint's `required_features` list as a checklist in your mind:
- User management? → What operations? (CRUD, bulk import, role assignment)
- Data processing? → What transformations? (CSV → DB, API → JSON, image resize)
- API endpoints? → Which resources and HTTP methods? (GET /users, POST /products)

**Goal**: List 3-5 specific features (not just "works").

### Step 4: Clarify Constraints

**Ask**: "Any requirements or limitations I should know about?"

**Probe for**:
- **Deployment**: "Where will this run? Docker? Kubernetes? Cloud provider?"
- **Performance**: "Any speed or scale requirements? (e.g., must handle X requests/second)"
- **Integration**: "Does this need to connect to any existing services or databases?"
- **Security**: "Any security requirements? (OWASP compliance, encryption, audit logs)"
- **Testing**: "Test coverage expectations? (e.g., >80%, integration tests required)"

**Technique - Ask Once, Get Multiple**:
Instead of 5 separate questions, ask:
"Are there any constraints I should know about?  Deployment target, performance needs, existing services to integrate with, security requirements, or testing expectations?"

**Goal**: Gather constraints without interrogating. 1-2 questions should cover this.

### Step 5: Identify Anti-Patterns

**Ask**: "Any frameworks, libraries, or approaches you want to avoid?"

**Why this matters**: Helps Obra make better technical choices aligned with team standards.

**Common scenarios**:
- Team standardizing: "Don't use Flask, we're moving to FastAPI"
- Performance: "Avoid synchronous I/O, must be async"
- Complexity: "No Redux, prefer simpler state management"
- Legacy: "Avoid Python 2 patterns, target Python 3.11+"

**If user doesn't mention any**:
- That's fine! Anti-patterns are optional.
- DON'T invent constraints. Only include what user explicitly states.

**Goal**: Capture any explicit "don't do X" instructions (if any).

### Step 6: Organize and Summarize

**Internally** (you don't show this to the user):
- Map answers to blueprint structure
- Check completeness: Do I have objective, tech stack, features, success criteria?
- Fill gaps: If anything critical is missing, ask ONE more clarifying question

**Construct natural language summary**:
- Start with objective (what to build)
- List tech stack (language, framework, database)
- Describe features (what it must do)
- State constraints (deployment, performance, integration)
- Mention anti-patterns (if any)

**Example mental process**:
```
User wants: User management API
Tech stack: Python + FastAPI + PostgreSQL (inferred from project files)
Features: CRUD for users, JWT auth, role-based access
Constraints: Docker Compose deployment, <200ms response, integrate with auth-service:8000
Anti-patterns: No Flask (team uses FastAPI)

Final summary:
"Build user management REST API with Python/FastAPI and PostgreSQL.
Features: CRUD operations for users, JWT authentication with refresh tokens,
role-based access control (admin/user roles). Docker Compose deployment.
Must integrate with existing auth-service:8000 for token validation.
Performance requirement: <200ms API response time. Avoid Flask (standardize on FastAPI)."
```

### Step 7: Submit to Obra

**Command format**:
```bash
obra "[your clear, structured summary]" --stream
```

**Flags to use**:
- `--stream`: Show real-time progress (recommended for UX)
- `-v`, `-vv`, `-vvv`: Verbosity levels (use `-v` for most cases)
- `--model opus`: Specify implementation model (if user requests)
- `--dir /path`: Specify working directory (if not current dir)

**Example submission**:
```bash
obra "User management REST API with Python/FastAPI and PostgreSQL.
CRUD operations for users, JWT authentication with refresh tokens, role-based
access control (admin/user roles). Docker Compose deployment. Integrate with
existing auth-service:8000. Performance: <200ms API response time. Tests >80%
coverage. Avoid Flask (standardizing on FastAPI)." --stream
```

**CRITICAL**: The summary is natural language, NOT JSON. Don't try to create JSON for Obra. Just provide a clear, complete paragraph (or bullets) with all the information.

---

## Complete Examples

### Example 1: REST API (Python/FastAPI)

**User's initial request**:
"I want to build a user management API"

**Your internal reasoning** (using blueprint):
- Title: User Management REST API
- Objective: CRUD for users with auth
- Tech stack: Check project files first...
  - `requirements.txt` shows `fastapi==0.104.0` → Python + FastAPI ✓
  - `docker-compose.yml` shows `postgres:14` → PostgreSQL ✓
- Features: CRUD, authentication (need specifics)
- Constraints: Deployment? Performance? Integration?

**Questions you ask**:
```
"I see you're using Python and FastAPI with PostgreSQL. Should I continue with that stack?"
[User: Yes]

"What authentication approach? JWT, OAuth2, or session-based?"
[User: JWT]

"Any specific features beyond basic CRUD? Role-based access, user profiles, etc.?"
[User: Yes, admin and regular user roles]

"Deployment target?"
[User: Docker Compose]

"Any existing services to integrate with?"
[User: Yes, auth-service on port 8000 for validation]

"Performance requirements?"
[User: Should handle 100 concurrent users, response time under 200ms]

"Test coverage expectations?"
[User: At least 80%]

"Any frameworks to avoid?"
[User: Don't use Flask, we're standardizing on FastAPI]
```

**Final Obra input**:
```bash
obra "User management REST API:
- Tech stack: Python 3.11, FastAPI 0.104, PostgreSQL 14
- Features:
  * CRUD operations for users (create, read, update, delete)
  * JWT authentication with refresh tokens
  * Role-based access control (admin and user roles)
  * Admin endpoints for user management
- Deployment: Docker Compose
- Integration: Must connect to existing auth-service:8000 for token validation
- Performance: Handle 100 concurrent requests, <200ms response time (95th percentile)
- Testing: >80% code coverage with unit and integration tests
- Anti-patterns: Don't use Flask (team standard is FastAPI)
- Success criteria: All CRUD endpoints work, JWT auth blocks unauthorized requests,
  role permissions enforced, tests pass with >80% coverage" --stream
```

**Why this works**:
- ✅ Clear tech stack (inferred from project files)
- ✅ Specific features (not just "CRUD" but details about auth and roles)
- ✅ Explicit constraints (deployment, integration, performance)
- ✅ Anti-patterns included (team standards)
- ✅ Success criteria stated (testable outcomes)

---

### Example 2: REST API (Node/Express)

**User's initial request**:
"Build a product catalog API"

**Your internal reasoning**:
- Check project files: `package.json` shows Express.js → Node.js + Express ✓
- Database: Not obvious, need to ask
- Features: Product catalog implies CRUD for products, search/filter
- Constraints: Unknown, ask

**Questions you ask**:
```
"I see you're using Node.js with Express. Database preference? MongoDB, PostgreSQL, MySQL?"
[User: MongoDB with Mongoose]

"What operations on products? Just CRUD or also search, filter, categories?"
[User: CRUD plus search by name and filter by category and price]

"User authentication needed?"
[User: No, public API for now]

"Deployment?"
[User: Docker with nginx reverse proxy]

"Any performance requirements?"
[User: Not critical for MVP, just reasonably fast]
```

**Final Obra input**:
```bash
obra "Product catalog REST API:
- Tech stack: Node.js 18, Express.js, MongoDB with Mongoose ORM
- Features:
  * CRUD operations for products (name, description, price, category, image URL)
  * Search products by name (partial match, case-insensitive)
  * Filter products by category and price range
  * Pagination support (limit/offset)
- Deployment: Docker Compose with nginx reverse proxy
- API design: RESTful endpoints (GET /products, POST /products, PUT /products/:id, DELETE /products/:id)
- No authentication required (public API for MVP)
- Success criteria: All CRUD endpoints work, search returns relevant results, filters work correctly,
  pagination handles large datasets" --stream
```

**Why this works**:
- ✅ Tech stack specified (Node + Express + MongoDB)
- ✅ Features detailed (CRUD + search + filter + pagination)
- ✅ Deployment clear (Docker with nginx)
- ✅ API design specified (RESTful)
- ✅ Success criteria stated

---

### Example 3: CLI Tool (Python)

**User's initial request**:
"Make a CLI tool to analyze log files"

**Your internal reasoning**:
- Type: CLI tool, not web service
- Language: Check project... no existing Python files. Ask preference.
- Features: Log analysis (what kind? parsing? metrics extraction?)
- Constraints: Performance (log files can be huge)

**Questions you ask**:
```
"Language preference? Python or Go are common for CLI tools."
[User: Python, I'm familiar with it]

"What log formats? Apache, Nginx, JSON, custom?"
[User: Support common formats - Apache, Nginx, and JSON]

"What analysis? Error counting, performance metrics, custom queries?"
[User: Extract error rates, response times, status code distribution]

"Output format?"
[User: CSV and JSON, user's choice via flag]

"Performance constraints? Some log files are huge."
[User: Should handle 10GB files without eating all memory]
```

**Final Obra input**:
```bash
obra "CLI tool for log file analysis:
- Tech stack: Python 3.11, Click or Typer for CLI framework
- Features:
  * Parse common log formats: Apache Combined, Nginx, JSON logs
  * Extract metrics: error rate, average response time, status code distribution
  * Output formats: CSV and JSON (user selectable via --output flag)
  * Progress indicator for large files
- Performance: Handle 10GB files with <1GB memory usage (stream processing, not load entire file)
- CLI interface:
  * Main command: analyze <logfile> --format [apache|nginx|json] --output [csv|json]
  * Optional: --filter flag for date range or status codes
- No external service dependencies (pure CLI tool)
- Success criteria: Parse 10GB Apache log in <5 minutes, memory usage <1GB, accurate metric extraction" --stream
```

**Why this works**:
- ✅ CLI tool context clear (not web service)
- ✅ Supported formats explicit
- ✅ Output options specified
- ✅ Performance constraint critical for log files
- ✅ CLI interface designed upfront

---

### Example 4: CLI Tool (Go)

**User's initial request**:
"Create a deployment automation tool"

**Your internal reasoning**:
- Type: CLI tool for DevOps automation
- Language: User mentioned Go (or should I ask?)
- Features: Deployment (to where? K8s? Docker? Cloud?)
- Constraints: Likely needs to interact with APIs (kubectl, docker, etc.)

**Questions you ask**:
```
"Language preference? Go is popular for DevOps tools."
[User: Yes, Go]

"Deploy to what? Kubernetes, Docker Swarm, cloud providers?"
[User: Kubernetes clusters]

"What should it automate? Build, push images, apply manifests, all of it?"
[User: Full flow - build Docker image, push to registry, apply K8s manifests, verify deployment]

"Configuration? YAML config file or CLI flags?"
[User: YAML config file with CLI flag overrides]

"Which container registry?"
[User: Support Docker Hub and private registries]
```

**Final Obra input**:
```bash
obra "Kubernetes deployment automation CLI tool:
- Tech stack: Go 1.21, Cobra for CLI framework
- Features:
  * Read deployment config from YAML file (build settings, image name, K8s manifests path)
  * Build Docker image from Dockerfile
  * Push image to registry (Docker Hub or private registry via config)
  * Apply Kubernetes manifests using kubectl or K8s Go client
  * Verify deployment (wait for pods to be ready, check status)
  * Rollback command if deployment fails
- Configuration: YAML config file with CLI flag overrides (--config, --registry, --namespace)
- Dependencies: docker CLI and kubectl must be installed (check in pre-flight)
- Output: Progress logs, final status (success/failure), resource URLs
- Success criteria: Full deploy flow works end-to-end, rollback restores previous state,
  clear error messages on failure" --stream
```

**Why this works**:
- ✅ Go + Cobra for CLI (standard for DevOps tools)
- ✅ Full automation flow defined (build → push → deploy → verify)
- ✅ Configuration approach specified (YAML + CLI flags)
- ✅ Rollback feature included (critical for deployment tools)
- ✅ Dependencies stated (docker, kubectl)

---

### Example 5: Web App (React + Backend)

**User's initial request**:
"Build a task management web app"

**Your internal reasoning**:
- Type: Full-stack web app (frontend + backend)
- Tech stack: Need both frontend and backend choices
- Features: Task management (CRUD tasks, likely users, maybe teams)
- Constraints: Real-time updates? Auth? Deployment?

**Questions you ask**:
```
"Frontend framework preference? React, Vue, Angular?"
[User: React]

"Backend language and framework?"
[User: FastAPI (Python)]

"Database?"
[User: PostgreSQL]

"Task features needed? Just CRUD or also due dates, priorities, assignments?"
[User: CRUD, due dates, priorities, and user assignments]

"User authentication?"
[User: Yes, JWT auth]

"Real-time updates when tasks change?"
[User: Yes, use WebSockets]

"Mobile-responsive?"
[User: Yes, mobile and desktop]

"Deployment?"
[User: Docker Compose for now]
```

**Final Obra input**:
```bash
obra "Task management web application:
- Frontend:
  * React 18 with TypeScript
  * Responsive design (mobile and desktop) using Tailwind CSS
  * Real-time updates via WebSocket connection
  * Forms for task creation/editing with validation
- Backend:
  * Python 3.11 with FastAPI
  * REST API for tasks (CRUD operations)
  * WebSocket endpoint for real-time task updates
  * JWT authentication with refresh tokens
  * PostgreSQL 14 database with SQLAlchemy ORM
- Features:
  * User registration and login (JWT auth)
  * Create, read, update, delete tasks
  * Task fields: title, description, due date, priority (low/medium/high), assigned user
  * Task list with filters (by priority, status, assigned user)
  * Real-time sync when any user updates tasks
- Deployment: Docker Compose with separate containers for frontend (nginx), backend (FastAPI), database (PostgreSQL)
- State management: React Context API (avoid Redux for simplicity)
- Success criteria: Users can register/login, all task operations work, real-time updates appear instantly,
  responsive on mobile and desktop, tests >70% coverage" --stream
```

**Why this works**:
- ✅ Full-stack architecture specified (React + FastAPI + PostgreSQL)
- ✅ Real-time feature explicit (WebSockets)
- ✅ Responsive design stated
- ✅ Authentication approach defined (JWT)
- ✅ State management choice made (React Context, not Redux)
- ✅ Deployment stack clear (Docker Compose)

---

### Example 6: Data Pipeline (Python)

**User's initial request**:
"I need to process CSV files and load them into a database"

**Your internal reasoning**:
- Type: ETL/data pipeline
- Tech stack: Python is common for data processing
- Features: CSV parsing, validation, transformation, database load
- Constraints: File size? Frequency? Error handling?

**Questions you ask**:
```
"What database? PostgreSQL, MySQL, something else?"
[User: PostgreSQL]

"CSV file size and frequency? One-off or recurring?"
[User: Recurring daily, files can be up to 1GB]

"Any data validation or transformation needed?"
[User: Validate required fields, convert date formats, deduplicate records]

"Error handling? Skip bad rows, stop on error, or log and continue?"
[User: Log errors to file, skip bad rows, continue processing]

"Should this run on a schedule or trigger manually?"
[User: Run via cron job daily]
```

**Final Obra input**:
```bash
obra "CSV to PostgreSQL ETL pipeline:
- Tech stack: Python 3.11, pandas for CSV processing, SQLAlchemy for DB
- Input: CSV files up to 1GB, recurring daily
- Processing steps:
  * Read CSV in chunks (handle large files without memory issues)
  * Validate: check required fields (id, name, email, date), reject rows with missing data
  * Transform: parse dates to ISO format, deduplicate by id (keep latest)
  * Load: Insert into PostgreSQL using SQLAlchemy ORM
- Error handling:
  * Log validation errors to error.log (row number, reason)
  * Skip invalid rows, continue processing
  * Report summary at end (total rows, inserted, skipped)
- Database: PostgreSQL 14, table schema: id, name, email, date, created_at
- Execution: CLI script that can be run via cron: python pipeline.py --input data.csv
- Performance: Process 1GB CSV in <10 minutes, memory usage <500MB
- Success criteria: Pipeline processes large files without crashing, invalid rows logged,
  all valid data in database, idempotent (re-running same file doesn't duplicate)" --stream
```

**Why this works**:
- ✅ ETL steps clear (read → validate → transform → load)
- ✅ Chunked processing for large files (memory efficiency)
- ✅ Error handling strategy defined
- ✅ Idempotent design (important for data pipelines)
- ✅ Performance constraints stated

---

### Example 7: Microservice (Go)

**User's initial request**:
"Create a payment processing microservice"

**Your internal reasoning**:
- Type: Microservice (part of larger system)
- Language: Go is popular for microservices
- Features: Payment processing (via which provider? Stripe? PayPal?)
- Constraints: Security critical, integration with existing systems

**Questions you ask**:
```
"Payment provider? Stripe, PayPal, or multiple?"
[User: Stripe]

"What operations? Process payments, refunds, webhooks?"
[User: All three - charge customers, process refunds, handle Stripe webhooks]

"Integration with existing services?"
[User: Yes, user-service for customer info, order-service for order details]

"Database needed or just API wrapper?"
[User: Need to store transaction records for audit]

"Security requirements?"
[User: PCI DSS compliance considerations, no storing full card details, Stripe tokens only]

"Deployment?"
[User: Kubernetes]
```

**Final Obra input**:
```bash
obra "Payment processing microservice:
- Tech stack: Go 1.21, Gin web framework, PostgreSQL for transaction logs
- Stripe integration using stripe-go SDK
- Features:
  * POST /payments - Create payment intent with Stripe
  * POST /payments/:id/confirm - Confirm payment
  * POST /refunds - Process refund for order
  * POST /webhooks/stripe - Handle Stripe webhooks (payment succeeded, failed, refunded)
- Integration:
  * Call user-service:8001 to fetch customer details
  * Call order-service:8002 to fetch order amounts
- Database: Store transaction records (transaction_id, stripe_payment_id, amount, status, timestamp)
- Security:
  * Use Stripe tokens only (never store card details)
  * HTTPS only (TLS 1.2+)
  * Validate webhook signatures from Stripe
  * API key authentication for internal services
- Deployment: Kubernetes with Horizontal Pod Autoscaler
- Error handling: Retry failed Stripe API calls with exponential backoff, idempotent webhook processing
- Success criteria: Payments process successfully, refunds work, webhooks handle all events, no duplicate processing,
  all transactions logged" --stream
```

**Why this works**:
- ✅ Stripe integration explicit (specific SDK)
- ✅ API endpoints defined (create, confirm, refund, webhooks)
- ✅ Integration points stated (user-service, order-service)
- ✅ Security considerations front and center
- ✅ Idempotent webhook handling (critical for payments)
- ✅ Kubernetes deployment specified

---

### Example 8: Authentication System

**User's initial request**:
"Implement OAuth2 with JWT for our platform"

**Your internal reasoning**:
- Type: Authentication system (critical infrastructure)
- Approach: OAuth2 + JWT (complex, need specifics)
- Features: Login, token generation, refresh, validation
- Constraints: Security is paramount

**Questions you ask**:
```
"OAuth2 provider or implementing the auth server yourself?"
[User: Implementing our own auth server]

"Grant types needed? Authorization code, client credentials, password?"
[User: Authorization code for web apps, refresh tokens for mobile]

"JWT configuration? Access token expiry, refresh token rotation?"
[User: Access tokens expire in 15 minutes, refresh tokens in 7 days with rotation]

"User storage?"
[User: PostgreSQL with user credentials table]

"Password hashing?"
[User: bcrypt]

"Social login? (Google, GitHub, etc.)"
[User: Not in MVP, just email/password]
```

**Final Obra input**:
```bash
obra "OAuth2 authentication server with JWT:
- Tech stack: Python 3.11, FastAPI, PostgreSQL for user storage
- OAuth2 implementation:
  * Authorization code grant flow (for web apps)
  * Refresh token flow (for mobile apps)
  * Token endpoint: POST /oauth/token (grant_type, code/refresh_token)
  * Introspection endpoint: POST /oauth/introspect (validate tokens)
- JWT configuration:
  * Access tokens: 15-minute expiry, signed with RS256 (private key)
  * Refresh tokens: 7-day expiry with rotation (new refresh token on each use)
  * Claims: user_id, email, roles, issued_at, expires_at
- Features:
  * User registration: POST /users/register (email, password)
  * User login: POST /auth/login (returns authorization code)
  * Token exchange: POST /oauth/token (code for access/refresh tokens)
  * Token refresh: POST /oauth/token (refresh token for new access token with rotation)
  * Logout: POST /auth/logout (invalidate refresh token)
- Security:
  * bcrypt for password hashing (cost factor 12)
  * HTTPS only (TLS 1.2+)
  * CSRF protection for auth flows
  * Rate limiting on login/registration (10 requests/minute per IP)
  * Refresh token stored hashed in database
- Database schema: users (id, email, password_hash), refresh_tokens (token_hash, user_id, expires_at, revoked)
- Success criteria: OAuth2 flows work per spec (RFC 6749), JWT tokens validate correctly, refresh rotation works,
  brute force protection active, all passwords hashed" --stream
```

**Why this works**:
- ✅ OAuth2 flows specified (authorization code + refresh)
- ✅ JWT config detailed (expiry, algorithm, claims)
- ✅ Security measures comprehensive (bcrypt, HTTPS, rate limiting, token rotation)
- ✅ Database schema defined
- ✅ All critical endpoints listed

---

### Example 9: Database Migration

**User's initial request**:
"Migrate from SQLite to PostgreSQL with zero downtime"

**Your internal reasoning**:
- Type: Migration (not new development)
- Challenge: Zero downtime (need strategy)
- Features: Data migration, schema migration, validation
- Constraints: Must not interrupt service

**Questions you ask**:
```
"Current SQLite database size and table count?"
[User: 500MB, 10 tables, about 1 million rows total]

"Application stack? Need to update connection strings."
[User: Python/Flask app]

"Can you afford read-only mode briefly or need full availability?"
[User: Brief read-only acceptable (< 5 minutes)]

"PostgreSQL instance ready or need to set up?"
[User: PostgreSQL 14 already running in Docker]

"Any schema changes during migration or 1:1 copy?"
[User: 1:1 copy for now, schema changes later]
```

**Final Obra input**:
```bash
obra "SQLite to PostgreSQL migration with minimal downtime:
- Current state: SQLite database (500MB, 10 tables, 1M rows), Python/Flask app
- Target: PostgreSQL 14 in Docker container
- Migration strategy:
  * Phase 1: Dual-write mode - write to both SQLite and PostgreSQL, read from SQLite
  * Phase 2: Backfill - copy existing SQLite data to PostgreSQL while dual-write active
  * Phase 3: Validation - verify row counts, sample data integrity checks
  * Phase 4: Cutover - switch reads to PostgreSQL (< 5 min read-only mode)
  * Phase 5: Monitor - watch for issues, rollback plan ready
- Implementation:
  * Create PostgreSQL schema matching SQLite (use Alembic for migrations)
  * Script to copy data: read from SQLite in batches (10k rows), insert into PostgreSQL
  * Update Flask app config to use PostgreSQL connection string
  * Add feature flag for dual-write mode (config toggle)
- Data validation:
  * Compare row counts per table (SQLite vs PostgreSQL)
  * Sample 1000 random rows per table, verify content matches
  * Check foreign key relationships intact
- Rollback plan:
  * If issues in first hour, switch back to SQLite reads
  * Keep SQLite file for 7 days before deletion
- Success criteria: All data migrated, row counts match, sample data validates,
  app runs on PostgreSQL without errors, <5 min downtime" --stream
```

**Why this works**:
- ✅ Migration strategy phased (dual-write → backfill → validation → cutover)
- ✅ Zero downtime approach (brief read-only only)
- ✅ Validation steps explicit
- ✅ Rollback plan included (critical for migrations)
- ✅ Timeline realistic (phases can be executed safely)

---

### Example 10: Testing Infrastructure

**User's initial request**:
"Add pytest and coverage to existing project"

**Your internal reasoning**:
- Type: Testing setup (infrastructure, not new features)
- Context: Existing project (need to see what's there)
- Features: Test framework, coverage reporting, CI integration
- Constraints: Existing code might not be testable (refactoring needed?)

**Questions you ask**:
```
"What's the project? (Check files to see Python app structure)"
[Finds: FastAPI REST API project, no tests exist yet]

"Coverage target? (80% is common)"
[User: 80% minimum]

"Test types? Unit only or also integration tests?"
[User: Both unit and integration tests]

"CI/CD? GitHub Actions, GitLab CI, Jenkins?"
[User: GitHub Actions]

"Any mocking requirements? (e.g., external API calls, database)"
[User: Yes, mock external API calls and database for unit tests]
```

**Final Obra input**:
```bash
obra "Add pytest testing infrastructure to FastAPI project:
- Setup:
  * Install pytest, pytest-cov, pytest-asyncio, pytest-mock
  * Create tests/ directory structure (tests/unit/, tests/integration/)
  * Configure pytest.ini (test discovery, coverage settings)
- Unit tests:
  * Test all API endpoints with mocked database (use pytest fixtures)
  * Mock external API calls using pytest-mock
  * Test business logic functions in isolation
  * Target: >80% code coverage for src/ directory
- Integration tests:
  * Test full API flows with test database (PostgreSQL in Docker)
  * Use pytest fixtures for test database setup/teardown
  * Test authentication, authorization, and data persistence
- Configuration:
  * pytest.ini: configure coverage reporting (HTML + terminal)
  * Separate test config (test_config.py) for test database connection
  * Fixtures in conftest.py for reusable test setup
- GitHub Actions CI:
  * Run tests on every PR and push to main
  * Fail build if coverage drops below 80%
  * Upload coverage report to Codecov or similar
- Documentation:
  * README section on running tests: pytest --cov=src --cov-report=html
  * Mark slow integration tests with @pytest.mark.integration
- Success criteria: All tests pass, >80% coverage achieved, CI pipeline runs tests automatically,
  test documentation clear for contributors" --stream
```

**Why this works**:
- ✅ Testing strategy clear (unit + integration)
- ✅ Mocking approach defined (pytest-mock, test DB)
- ✅ Coverage target explicit (>80%)
- ✅ CI integration specified (GitHub Actions)
- ✅ Project structure defined (tests/unit/, tests/integration/)
- ✅ Documentation included (README, test markers)

---

## Anti-Patterns: What NOT to Do

### Vague Objectives

❌ **Bad**:
```
"Build a good website"
```
**Problem**: What kind of website? For what purpose? What makes it "good"?

✅ **Good**:
```
"Build an e-commerce website for selling handmade crafts with product catalog,
shopping cart, checkout via Stripe, and user accounts. React frontend, Node/Express
backend, MongoDB database."
```

---

❌ **Bad**:
```
"Make something that works"
```
**Problem**: Works for what? No features, no tech stack, no constraints.

✅ **Good**:
```
"Create a log file analyzer CLI tool (Python) that parses Apache and Nginx logs,
extracts error rates and response times, outputs to CSV. Must handle 10GB files
with <1GB memory usage."
```

### Missing Constraints

❌ **Bad**:
```
"Just make it fast"
```
**Problem**: How fast? What are the performance criteria?

✅ **Good**:
```
"API response time <200ms (95th percentile), handle 100 concurrent requests,
database queries <50ms."
```

---

❌ **Bad**:
```
"It needs to be secure"
```
**Problem**: Too vague. What security measures?

✅ **Good**:
```
"Security requirements: OWASP Top 10 compliance, bcrypt for passwords (cost 12),
HTTPS only, no secrets in code, JWT tokens with 15-min expiry."
```

### Assumed Tech Stack

❌ **Bad** (you assume without checking):
```
"I'll guess Python"
```
**Problem**: User might be using Node.js or Go. Always check project files first.

✅ **Good**:
```
[Check package.json first]
"I see you're using Node.js with Express. Should I continue with that stack?"
```

---

❌ **Bad** (you don't ask about framework):
```
"Build a REST API with Python"
```
**Problem**: Which framework? FastAPI, Django, Flask?

✅ **Good**:
```
"Build a REST API with Python/FastAPI [inferred from requirements.txt]"
```

### Non-Specific Features

❌ **Bad**:
```
"Add authentication"
```
**Problem**: What kind? JWT, OAuth, session-based, API keys?

✅ **Good**:
```
"Add JWT authentication with refresh tokens, 15-minute access token expiry,
7-day refresh token expiry with rotation."
```

### Analysis Objectives (No Code Delivered)

❌ **Bad**:
```
"Investigate performance issues"
```
**Problem**: Analysis objective. May produce a report instead of fixing code.

✅ **Good**:
```
"Optimize API response time to <200ms by adding Redis caching for frequently
accessed user data and database connection pooling."
```

---

❌ **Bad**:
```
"Review error handling in the application"
```
**Problem**: Vague review request. Likely produces analysis document.

✅ **Good**:
```
"Add try-catch blocks with structured logging (logger.error with context) to
7 exception handlers in client.py and server.py."
```

---

❌ **Bad**:
```
"Validate security compliance"
```
**Problem**: Audit/validation objective, not implementation.

✅ **Good**:
```
"Fix SQL injection vulnerabilities in user search and admin panel endpoints
using parameterized queries. Add input sanitization for all user-provided fields."
```

**Key principle**: Replace "investigate/review/audit/validate" with specific code changes.

---

❌ **Bad**:
```
"Implement search"
```
**Problem**: Search by what? Any filters? Full-text or basic matching?

✅ **Good**:
```
"Implement product search by name (partial match, case-insensitive) with filters
for category (dropdown) and price range (min/max sliders)."
```

### Interrogating Users

❌ **Bad** (asking too many questions):
```
1. What language?
2. What framework?
3. What database?
4. What version?
5. What deployment?
6. What testing framework?
7. What CI/CD?
8. What logging?
9. What monitoring?
10. What... [continues]
```
**Problem**: Feels like an interrogation. Users will abandon.

✅ **Good** (ask 3-5 key questions):
```
1. "I see you're using Python/FastAPI. Continue with that?"
2. "Key features needed? (e.g., CRUD, auth, search)"
3. "Any constraints? (deployment, performance, integration, testing)"
```

### Missing Success Criteria

❌ **Bad**:
```
"Build an API"
```
**Problem**: How do we know when it's done?

✅ **Good**:
```
"Build an API.
Success criteria:
- All endpoints respond with correct status codes
- Authentication blocks unauthorized requests
- Tests achieve >80% coverage and pass
- API documentation generated (OpenAPI)"
```

### Overly Specific (Too Prescriptive)

❌ **Bad**:
```
"Use pandas version 1.5.3, import data using pd.read_csv with chunksize=10000,
use dtype={'id': 'int64', 'name': 'str'}, then call df.drop_duplicates(subset=['id'])..."
```
**Problem**: You're writing the code, not describing what to build. Let Obra decide implementation details.

✅ **Good**:
```
"ETL pipeline to load CSV into PostgreSQL. Read in chunks for large files (>1GB),
validate required fields, deduplicate by ID."
```

### Ignoring Existing Context

❌ **Bad** (you don't check project files):
```
"What language are you using?"
```
**Problem**: `package.json` or `requirements.txt` would tell you.

✅ **Good**:
```
[Check files first]
"I see you have package.json with Express. Continuing with Node.js/Express?"
```

---

## Tips for Success

### 1. Ask 3-5 Questions Maximum

**Why**: Users want help, not an interview.

**How**:
- Check project files first (infer what you can)
- Ask only for what's missing or ambiguous
- Combine related questions ("Any constraints? Deployment, performance, integration?")

**Example**:
Instead of 10 separate questions:
```
1. Language?
2. Framework?
3. Database?
4. Deployment?
5. Performance needs?
6. Integration?
7. Testing?
8. Security?
9. Auth approach?
10. CI/CD?
```

Ask 3 combined questions:
```
1. "I see Python/FastAPI. Continue with that? Database preference?"
2. "Key features? (CRUD, auth, search, admin panel?)"
3. "Any constraints? (deployment, performance, existing services, testing expectations)"
```

### 2. Infer Before Asking

**Check these files** (if accessible):
- `package.json` → Language (JS/TS), framework (React, Express, Next.js)
- `requirements.txt` / `pyproject.toml` → Language (Python), framework clues
- `go.mod` → Language (Go)
- `Cargo.toml` → Language (Rust)
- `README.md` → Often lists tech stack and setup instructions
- `docker-compose.yml` → Reveals services (database, Redis, etc.)
- Project structure → Conventions reveal framework (Django has `manage.py`, Flask has `app.py`)

**Only ask** if you can't infer.

### 3. Be Specific, Not Vague

**Vague**: "Authentication"
**Specific**: "JWT authentication with refresh tokens"

**Vague**: "Make it fast"
**Specific**: "<200ms API response time, 100 concurrent users"

**Vague**: "Add search"
**Specific**: "Search by product name with filters for category and price range"

**Why**: Specificity helps Obra make the right technical choices.

### 3a. Use Action-Oriented Objectives (Not Analysis)

**CRITICAL**: Frame objectives as implementation goals, not investigation tasks.

**Analysis triggers** (may cause research/validation instead of code):
- ❌ "Validate the authentication system"
- ❌ "Investigate performance issues in the API"
- ❌ "Review error handling in the codebase"
- ❌ "Audit security vulnerabilities"

**Implementation triggers** (clear code changes):
- ✅ "Add JWT authentication with refresh tokens to the REST API"
- ✅ "Optimize API response time to <200ms by adding Redis caching"
- ✅ "Add structured logging with error context to all exception handlers"
- ✅ "Fix SQL injection vulnerability in user search endpoint using parameterized queries"

**Why this matters**: Generic action words like "validate", "investigate", "review", "audit" without specific implementation targets may trigger analysis-only execution. Implementation agents might create reports instead of writing code.

**How to fix vague objectives**:
1. **Replace analysis verbs** with implementation verbs:
   - "Validate X" → "Add validation for X using Y library"
   - "Investigate Y" → "Fix Y by implementing Z approach"
   - "Review Z" → "Improve Z by adding A, B, C features"

2. **Add concrete deliverables**:
   - Not: "Handle exceptions better"
   - Better: "Add try-catch blocks with logger.error() to 7 exception handlers in client.py"

3. **Specify files/locations when known**:
   - Not: "Improve logging"
   - Better: "Add structured logging to obra/api/client.py and obra/api/server.py using Python logging module"

**Action verb guide**:
- **Good** (implementation): Add, Create, Modify, Fix, Build, Implement [with specifics], Delete, Rename, Refactor [with target]
- **Risky** (may trigger analysis): Validate, Investigate, Review, Audit, Analyze, Check, Examine [without implementation goal]

**If user uses analysis language**, help them reframe:
```
User: "I need to validate our error handling"
You: "Got it. Do you want me to:
  A) Add validation checks to error handlers, or
  B) Improve error handling by adding structured logging?"
```

### 4. Include Anti-Patterns When Mentioned

If user says "Don't use Flask" → Include it.
If user doesn't mention anti-patterns → Don't invent them.

**Useful anti-patterns**:
- "Don't use Framework X (team standard is Y)"
- "Avoid synchronous code (must be async)"
- "No Redux (use simpler state management)"

**Don't make up** generic anti-patterns like "Don't write bad code" or "Avoid bugs."

### 5. Test Your Summary Mentally

**Before submitting**, ask yourself:
- ✅ Does this have enough detail?
- ✅ Is the tech stack clear?
- ✅ Are features specific (not vague)?
- ✅ Are constraints stated (deployment, performance, integration)?
- ✅ Can Obra execute this without guessing?

**If any answer is NO** → Ask one more clarifying question.

### 6. Use Natural Language, Not JSON

**DON'T** try to create JSON:
```json
{
  "title": "REST API",
  "objective": "Build API",
  ...
}
```

**DO** write natural language:
```
"Build user management REST API with Python/FastAPI, PostgreSQL, JWT auth,
CRUD operations, Docker Compose deployment. Integrate with auth-service:8000.
Performance: <200ms response time. Tests >80% coverage."
```

**Why**: Obra accepts natural language input. The blueprint is just your internal organizing framework.

### 7. Confirm Inferences

**When you infer tech stack** from project files:
- Confirm with user: "I see you're using X. Should I continue with that?"
- Gives user chance to correct if your inference is wrong

**Example**:
```
"I see package.json with Express and MongoDB. Should I use Node.js/Express/MongoDB,
or do you want to try a different stack?"
```

### 8. Handle Uncertainty Gracefully

**If user is unsure** ("I don't know what database to use"):
- Suggest sensible defaults: "PostgreSQL is a good default for production. Should I use that?"
- Explain briefly: "PostgreSQL handles complex queries well and is widely supported."

**If you're unsure** what user means:
- Ask for clarification: "When you say 'authentication', do you mean JWT, OAuth, or session-based?"

### 9. Track Constraints Explicitly

**Constraints often forgotten**:
- Deployment target (Docker, K8s, cloud provider)
- Performance requirements (response time, concurrent users)
- Integration with existing services (URLs, ports, APIs)
- Security requirements (OWASP, encryption, audit logs)
- Testing expectations (coverage %, types of tests)

**Probe for these** if not mentioned:
"Any constraints I should know about? Deployment, performance needs, existing services to integrate with?"

### 10. Provide Context About Environment

**If user mentions existing services**:
- Get connection details: "You mentioned auth-service. What's the connection info? (e.g., auth-service:8000)"

**If working directory matters**:
- Specify it: "Working directory is /home/user/projects/myapp (not current directory)"

**If version constraints exist**:
- Include them: "Python 3.11 (team standard), FastAPI >=0.104"

---

## Obra Command Reference

### Primary Command: Direct Objective

**Purpose**: Start AI-orchestrated work with Obra.

**Basic usage**:
```bash
obra "your objective"
```

**With streaming (recommended)**:
```bash
obra "your objective" --stream
```

**Verbosity levels**:
```bash
obra "objective" -v      # Progress with timestamps
obra "objective" -vv     # Detailed output with summaries
obra "objective" -vvv    # Debug mode (full protocol info)
```

**Specify model**:
```bash
obra "objective" --model opus            # Use Claude Opus for implementation
obra "objective" --impl-provider openai  # Use OpenAI for implementation
```

**Working directory**:
```bash
obra "objective" --dir /path/to/project
```

**Plan-only mode** (create plan without executing):
```bash
obra --plan-only "objective"
```

### Session Management

**Check status**:
```bash
obra status                    # Most recent session
obra status <id>               # Specific session
obra status -v                 # Verbose with quality metrics
```

**Resume session**:
```bash
obra resume <session_id>
obra resume <session_id> --stream
```

### Configuration

**Interactive TUI**:
```bash
obra config
```

**Show configuration**:
```bash
obra config --show
```

**Validate configuration**:
```bash
obra config --validate
```

**Reset to defaults**:
```bash
obra config --reset
```

### Authentication

**Login** (browser OAuth):
```bash
obra login
obra login --no-browser  # Print URL without opening browser
```

**Check auth status**:
```bash
obra whoami
```

**Logout**:
```bash
obra logout
```

### Plan Management (SaaS only)

**Validate plan file** (JSON recommended):
```bash
obra validate-plan plan.json
```

**Upload plan** (JSON recommended):
```bash
obra upload-plan plan.json
obra upload-plan --validate-only plan.json  # Validate without uploading
```

**List uploaded plans**:
```bash
obra plans list
obra plans list --limit 10
```

**Delete plan**:
```bash
obra plans delete <plan_id>
obra plans delete <plan_id> --force  # Skip confirmation
```

**Use plan with execution**:
```bash
obra --plan-id <id> "objective"
obra --plan-file plan.json "objective"
```

### Version and Health

**Check version**:
```bash
obra version
obra version --check  # Check for updates
```

### When to Use Each Command

**`obra "objective"`**: Start new work (primary command, use most often)
**`obra "objective" --stream`**: Start work with real-time progress (recommended for UX)
**`obra --plan-only "objective"`**: Create execution plan without implementing
**`obra status`**: Check if work is complete or still running
**`obra resume`**: Continue paused or interrupted work
**`obra config`**: First-time setup or change settings
**`obra validate-plan`**: Check plan file before using it
**`obra upload-plan`**: Save plan to cloud for reuse across devices

### Common Workflows

**New user onboarding**:
```bash
1. obra login
2. obra config  # Set up preferences
3. obra "your first objective" --stream
```

**Typical session**:
```bash
1. obra "build feature X" --stream
2. [Obra executes, streams progress]
3. obra status  # Check completion
```

**Interrupted session**:
```bash
1. obra status  # Find session ID
2. obra resume <session_id> --stream
```

**Using plan files** (JSON recommended):
```bash
1. obra validate-plan my-plan.json
2. obra upload-plan my-plan.json
3. obra --plan-id abc123 "implement plan"
```

---

## Advanced Invocation: Model & Provider Flags

### Overview

Obra allows per-task overrides of LLM model, provider, and reasoning depth. These flags override your config settings for a single invocation without changing your configuration file.

**When to use**:
- User requests specific model: "Use GPT-5 for this"
- Task requires high reasoning: Complex refactoring, architectural decisions
- Provider-specific features needed: Extended thinking, specialized models
- Testing different providers without changing config

**Flags available**:
- `--model` / `-m`: Specify implementation model
- `--impl-provider` / `-p`: Specify implementation provider
- `--thinking-level` / `-t`: Set reasoning/thinking depth

### Flag Reference

#### `--model` (Implementation Model)

**Purpose**: Choose which LLM model executes the implementation work.

**Valid values** (varies by provider):

**Anthropic** (requires `claude` CLI):
- `default` - Uses provider's recommended model
- `sonnet` - Claude Sonnet (balanced speed/quality)
- `opus` - Claude Opus (highest quality, slower)
- `haiku` - Claude Haiku (fastest, lighter tasks)

**Google** (requires `gemini` CLI):
- `default` - Uses provider's recommended model
- `auto` - Automatic model selection
- `gemini-2.5-pro` - Gemini 2.5 Pro (high quality)
- `gemini-2.5-flash` - Gemini 2.5 Flash (fast)
- `gemini-2.5-flash-lite` - Gemini 2.5 Flash Lite (lightweight)
- `gemini-3-pro-preview` - Gemini 3 Pro (preview)
- `gemini-3-flash-preview` - Gemini 3 Flash (preview)

**OpenAI** (requires `codex` CLI):
- `default` - Uses provider's recommended model
- `codex` - OpenAI Codex
- `gpt-5.2` - GPT-5.2
- `gpt-5.2-codex` - GPT-5.2 Codex variant
- `gpt-5.1-codex-max` - GPT-5.1 Codex Max
- `gpt-5.1-codex-mini` - GPT-5.1 Codex Mini
- `gpt-5.1` - GPT-5.1

**Format**:
```bash
obra "objective" --model <model_name>
obra "objective" -m <model_name>
```

#### `--impl-provider` (Implementation Provider)

**Purpose**: Choose which LLM provider executes the implementation work.

**Valid values**:
- `anthropic` (default) - Claude models (requires `claude` CLI installed)
- `google` - Gemini models (requires `gemini` CLI installed)
- `openai` - GPT/Codex models (requires `codex` CLI installed)

**Format**:
```bash
obra "objective" --impl-provider <provider>
obra "objective" -p <provider>
```

**Requirements**: The provider's CLI must be installed and configured:
- Anthropic: Install `claude` CLI
- Google: Install `gemini` CLI
- OpenAI: Install `codex` CLI

#### `--thinking-level` (Reasoning Depth)

**Purpose**: Control how much extended thinking/reasoning the LLM uses during execution.

**Valid values**:
- `off` - No extended thinking (fastest)
- `low` - Minimal reasoning
- `medium` (default) - Balanced reasoning
- `high` - Extended reasoning (complex tasks)
- `maximum` - Maximum reasoning depth (very complex tasks)

**When to use each level**:
- `off` / `low`: Simple tasks (typo fixes, straightforward implementations)
- `medium`: Most tasks (default, good balance)
- `high`: Complex refactoring, architectural decisions, multi-file changes
- `maximum`: Very complex systems, security-critical code, performance optimization

**Format**:
```bash
obra "objective" --thinking-level <level>
obra "objective" -t <level>
```

### Complete Examples

**Specify model only** (provider stays as configured):
```bash
obra "Fix authentication bug" --model opus
obra "Add API endpoint" -m gemini-2.5-flash
```

**Specify provider** (uses provider's default model):
```bash
obra "Refactor payment module" --impl-provider google
obra "Optimize database queries" -p openai
```

**Specify thinking level** (model/provider stay as configured):
```bash
obra "Add login form" --thinking-level low
obra "Design microservices architecture" -t high
```

**Combine multiple flags**:
```bash
# Use Claude Opus with high reasoning for complex refactoring
obra "Refactor authentication system" --model opus --thinking-level high

# Use Google Gemini 2.5 Pro with maximum reasoning for architecture
obra "Design API gateway architecture" \
  --impl-provider google \
  --model gemini-2.5-pro \
  --thinking-level maximum

# Use OpenAI GPT-5.2 with medium reasoning and streaming
obra "Implement user registration" \
  --impl-provider openai \
  --model gpt-5.2 \
  -t medium \
  --stream

# Combine with verbosity and working directory
obra "Add unit tests to payment module" \
  --model opus \
  --thinking-level high \
  --dir ~/projects/ecommerce \
  -vv \
  --stream
```

### Shorthand Aliases

You can use short flags for brevity:
```bash
obra "objective" -m opus -p anthropic -t high -vv -s
# Equivalent to:
obra "objective" --model opus --impl-provider anthropic --thinking-level high -vv --stream
```

### Common Patterns

**High-quality architectural work**:
```bash
obra "Design database schema for multi-tenant SaaS" \
  --model opus \
  --thinking-level maximum \
  --stream
```

**Fast iteration on simple tasks**:
```bash
obra "Fix typo in documentation" --model haiku --thinking-level off
```

**Testing different providers**:
```bash
# Try with Anthropic
obra "Implement feature X" --impl-provider anthropic --model opus -v

# Compare with Google
obra "Implement feature X" --impl-provider google --model gemini-2.5-pro -v

# Compare with OpenAI
obra "Implement feature X" --impl-provider openai --model gpt-5.2 -v
```

**User-requested model override**:
```
User: "Use Claude Opus to refactor this module"
You: [invoke obra]
  obra "Refactor authentication module for better testability. \
  Extract interfaces, add dependency injection, improve error handling." \
  --model opus --thinking-level high --stream
```

### Discovery

**For complete flag reference**:
```bash
obra run --help  # Shows all available flags with descriptions
```

**For provider/model compatibility**: See `docs/reference/cli-command-reference.md` in the Obra repository for the complete compatibility matrix.

---

## Autonomous Operation Protocol

### Purpose

This section defines behavioral specifications for LLMs operating Obra **autonomously**—that is, executing complex missions without human intervention for extended periods. While the previous sections assume interactive operation with a human available, autonomous operation requires explicit protocols for:

- Continuing execution without stopping for approval
- Reporting progress to an absent human
- Handling errors and recovering independently
- Knowing when to escalate vs. continue
- Managing context across session boundaries

### When to Use Autonomous Operation

**Use autonomous operation when:**
- Human will be away for hours while Obra works
- Mission is well-defined with clear success criteria
- No security-sensitive decisions required during execution
- Human wants status updates without active monitoring

**Use interactive operation when:**
- Requirements are unclear or evolving
- Security-sensitive operations need approval
- Human wants real-time control over decisions

### The 11 Core Behaviors

Autonomous operation requires mastering 11 behaviors, organized into three categories:

| Category | Behaviors | Purpose |
|----------|-----------|---------|
| **Core Operations** | 1-4 | Foundation for autonomous execution |
| **Error Handling** | 5-8 | Resilient operation and safe escalation |
| **Advanced** | 9-11 | Long-running sessions and handoffs |

**Core Operations (Behaviors 1-4):**
1. **Role Understanding** - Read guides, internalize Task Architect role
2. **Autonomous Execution** - Operate without stopping for approval
3. **Progress Reporting** - Write status updates to log file
4. **Session Health Monitoring** - Detect stalls and loops

**Error Handling (Behaviors 5-8):**
5. **Failure Classification** - Categorize errors, choose appropriate response
6. **Checkpoint Documentation** - Write recovery points after milestones
7. **Success Validation** - Verify deliverables and run smoke tests
8. **Escalation Criteria** - Know when to stop vs. continue

**Advanced (Behaviors 9-11):**
9. **Context Budget Management** - Checkpoint before context exhaustion
10. **Clean Handoff** - Produce summary on session end
11. **Mission Sizing** - Assess scope, plan appropriately

The following sections specify each behavior in detail.

### Core Operations (Behaviors 1-4)

#### Behavior 1: Role Understanding

```yaml
behavior: role_understanding
trigger: "Session start"
action:
  - Read obra/.obra/LLM_ONBOARDING.md
  - Read docs/reference/cli-command-reference.md (obra section)
  - Internalize Task Architect role (delegate, don't implement)
verification: "Can articulate role before first obra command"
```

**Purpose**: Before operating Obra autonomously, ensure you understand your role as Task Architect. You orchestrate work through Obra—you do NOT implement code directly.

**Required Reading**:
1. This guide (LLM_ONBOARDING.md) - especially the Blueprint and Question Patterns sections
2. CLI command reference - understand `obra`, `obra status`, `obra resume`

**Role Verification Checklist**:
- [ ] I understand I am the Task Architect, not the Implementer
- [ ] I know how to prepare high-quality objectives for Obra
- [ ] I can distinguish between interactive and autonomous operation modes
- [ ] I understand the `obra` command syntax and flags

**Anti-Pattern**: Starting execution without reading the guides. This leads to misunderstanding your role and improper use of Obra commands.

#### Behavior 2: Autonomous Execution

```yaml
behavior: autonomous_execution
trigger: "Mission received"
action:
  - Parse objective into Obra-compatible format
  - Execute `obra "<objective>" --stream`
  - Continue without human approval stops
exception: "Stop only for critical bugs (see Behavior 8: Escalation Criteria)"
anti_pattern: "Never use AskUserQuestion or EnterPlanMode"
note: "Uses simplified CLI syntax (no 'derive' verb required)"
```

**Purpose**: In autonomous mode, you must execute continuously without pausing for human approval. The human has delegated authority to you for the duration of the session.

**Execution Flow**:
1. Receive mission/objective from human
2. Assess mission size (see Behavior 11)
3. Format objective clearly (use Blueprint patterns from earlier sections)
4. Execute: `obra "<objective>" --stream`
5. Monitor progress with `obra status`
6. Continue to next objective or report completion

**What to NEVER Do in Autonomous Mode**:

| Prohibited Action | Why |
|-------------------|-----|
| `AskUserQuestion` tool | Human is away; this will hang the session |
| `EnterPlanMode` tool | Blocks on human approval; breaks autonomy |
| Stopping for "Is this okay?" | Human delegated authority; continue unless critical |
| Waiting for human input | Use defaults and document decisions instead |

**When Stopping IS Appropriate** (see Behavior 8 for full list):
- Critical bug or data corruption
- Security-sensitive operation (credentials, prod deploy)
- Obra explicitly requests human input (breakpoint triggered)
- Same error repeated 3+ times

**Decision Authority in Autonomous Mode**:
- **You decide**: Technical approach, file organization, naming conventions
- **Document**: Decisions made and rationale (in progress log)
- **Escalate**: Security decisions, breaking changes, ambiguous requirements

#### Behavior 3: Progress Reporting

```yaml
behavior: progress_reporting
trigger: "Every 5 minutes during active session"
output_file: ".obra/autonomous-session.log"
format: |
  ---
  timestamp: "2025-12-20T14:35:00Z"
  session_id: "abc123"
  phase: "Story 2/4 - Add authentication"
  current_task: "Task 3/5 - Implement JWT refresh"
  health: "ALIVE"
  last_activity: "45s ago"
  blockers: []
  notes: "JWT implementation in progress, tests passing"
  ---
action:
  - Append structured YAML block to log file
  - Include session_id for correlation
  - Classify health status honestly
```

**Purpose**: Since the human is away, you must leave a trail of progress reports they can review. This log enables monitoring and debugging of autonomous sessions.

**Health Status Values**:

| Status | Meaning |
|--------|---------|
| `ALIVE` | Active work in progress, recent activity |
| `INVESTIGATING` | Encountered issue, analyzing solution |
| `STALLED` | No progress for extended period |
| `COMPLETED` | Mission finished successfully |
| `FAILED` | Mission ended with unrecoverable error |
| `ESCALATED` | Stopped due to escalation criteria |

**Log Entry Fields**:

| Field | Required | Description |
|-------|----------|-------------|
| `timestamp` | Yes | ISO 8601 timestamp |
| `session_id` | Yes | Obra session ID for correlation |
| `phase` | Yes | Current story/phase (e.g., "Story 2/4 - Add authentication") |
| `current_task` | Yes | Current task within phase |
| `health` | Yes | One of the status values above |
| `last_activity` | Yes | Time since last meaningful action |
| `blockers` | No | List of current blockers (empty if none) |
| `notes` | No | Brief description of current work |

**Example Log File** (`.obra/autonomous-session.log`):

```yaml
---
timestamp: "2025-12-20T14:00:00Z"
session_id: "abc123"
phase: "Story 1/4 - Setup project structure"
current_task: "Task 2/3 - Create directory layout"
health: "ALIVE"
last_activity: "30s ago"
blockers: []
notes: "Creating src/ and tests/ directories"
---
---
timestamp: "2025-12-20T14:05:00Z"
session_id: "abc123"
phase: "Story 1/4 - Setup project structure"
current_task: "Task 3/3 - Initialize dependencies"
health: "ALIVE"
last_activity: "15s ago"
blockers: []
notes: "Running pip install, all dependencies resolving"
---
---
timestamp: "2025-12-20T14:10:00Z"
session_id: "abc123"
phase: "Story 2/4 - Add authentication"
current_task: "Task 1/5 - Create auth module"
health: "ALIVE"
last_activity: "10s ago"
blockers: []
notes: "Story 1 complete. Starting authentication module."
---
```

**Logging Best Practices**:
- Write entry at least every 5 minutes during active work
- Write immediately on phase/story transitions
- Write immediately when health status changes
- Keep notes brief but informative
- Include blockers when relevant (helps human understand delays)

#### Behavior 4: Session Health Monitoring

```yaml
behavior: session_health_monitoring
trigger: "After each obra command"
action:
  - Run `obra status` to verify session state
  - Track objective history (detect loops)
  - Monitor time since last progress
thresholds:
  stall_warning: "Same state for 10 minutes"
  stall_critical: "Same state for 20 minutes"
  loop_detection: "Same objective submitted 3x without progress"
response:
  stall_warning: "Log warning, continue monitoring"
  stall_critical: "Escalate (see Behavior 8)"
  loop_detection: "Stop and report loop details"
```

**Purpose**: Detect when sessions are stuck and take appropriate action. This prevents wasted time on stalled operations and catches infinite loops early.

**Monitoring Checklist** (run after each obra command):
1. Check `obra status` output for session state
2. Compare current state to previous check
3. Track how long state has been unchanged
4. Check if current objective matches previous objectives (loop detection)
5. Update progress log with health status

**Threshold Details**:

| Threshold | Trigger | Response |
|-----------|---------|----------|
| `stall_warning` | Same state for 10 minutes | Log warning in progress file, set health to `INVESTIGATING`, continue monitoring |
| `stall_critical` | Same state for 20 minutes | Log error, set health to `STALLED`, trigger escalation (see Behavior 8) |
| `loop_detection` | Same objective 3x without progress | Stop immediately, log loop details, set health to `FAILED` |

**Loop Detection Logic**:

```
Track last 5 objectives:
  objectives = ["obj1", "obj2", "obj3", "obj4", "obj5"]

If objectives[-1] == objectives[-2] == objectives[-3]:
  AND no progress between submissions:
    → Loop detected → Stop and report
```

**Example Loop Detection**:
```yaml
# Loop detected - same objective 3x with no progress
---
timestamp: "2025-12-20T15:30:00Z"
session_id: "abc123"
phase: "Story 2/4 - Add authentication"
current_task: "Task 2/5 - Configure JWT"
health: "FAILED"
last_activity: "5s ago"
blockers:
  - "Loop detected: 'Configure JWT module' submitted 3x without progress"
notes: "STOPPING: Repeated same objective without advancement. Human review required."
---
```

**Stall Detection Example**:
```yaml
# Stall warning at 10 minutes
---
timestamp: "2025-12-20T15:40:00Z"
session_id: "abc123"
phase: "Story 2/4 - Add authentication"
current_task: "Task 3/5 - Implement token refresh"
health: "INVESTIGATING"
last_activity: "10m ago"
blockers:
  - "Stall warning: No progress for 10 minutes"
notes: "obra status shows 'in_progress' but no file changes detected. Investigating."
---

# Stall critical at 20 minutes - escalating
---
timestamp: "2025-12-20T15:50:00Z"
session_id: "abc123"
phase: "Story 2/4 - Add authentication"
current_task: "Task 3/5 - Implement token refresh"
health: "STALLED"
last_activity: "20m ago"
blockers:
  - "Stall critical: No progress for 20 minutes"
notes: "ESCALATING: Session appears stuck. Triggering escalation per Behavior 8."
---
```

**What Counts as "Progress"**:
- File created or modified
- Test run (pass or fail counts as activity)
- Obra phase/task changed
- Build/compile completed
- Explicit "continuing..." message from Obra

**What Does NOT Count as "Progress"**:
- Same status message repeated
- Waiting without action
- Internal processing without output

### Error Handling (Behaviors 5-8)

#### Behavior 5: Failure Classification

```yaml
behavior: failure_classification
trigger: "Error encountered during Obra execution"
action:
  - Identify error category from list below
  - Apply category-specific response
  - Track retry attempts
  - Escalate when threshold exceeded
categories:
  transient:
    examples:
      - "Network timeout"
      - "Rate limit exceeded (429)"
      - "503 Service Unavailable"
      - "Connection reset by peer"
      - "DNS resolution failure"
    response: "Retry 2x with exponential backoff (10s, 30s)"
    escalate_after: "3 consecutive failures"

  validation:
    examples:
      - "Invalid input format"
      - "Missing required field"
      - "Schema validation error"
      - "Malformed YAML/JSON"
      - "Type mismatch in API call"
    response: "Fix input based on error message, retry once"
    escalate_after: "Fix attempt fails"

  auth:
    examples:
      - "Token expired"
      - "Not authorized (401)"
      - "Forbidden (403)"
      - "Session invalidated"
      - "API key invalid"
    response: "Run `obra login`, retry once"
    escalate_after: "Re-authentication fails"

  implementation:
    examples:
      - "Tests fail"
      - "Build error"
      - "Lint failure"
      - "Type check failure"
      - "Integration test timeout"
    response: "Let Obra iterate (it has quality loops)"
    escalate_after: "5 iterations without progress"

  critical:
    examples:
      - "Data corruption detected"
      - "Unhandled exception/crash"
      - "Security breach indicator"
      - "Infinite loop detected"
      - "Resource exhaustion (OOM, disk full)"
    response: "STOP IMMEDIATELY, report full context"
    escalate_after: "Never retry critical failures"
```

**Purpose**: Not all errors are equal. Autonomous operators must classify errors correctly to avoid both premature escalation (stopping on recoverable issues) and dangerous continuation (ignoring critical failures).

**Category Decision Tree**:

```
Error occurred
    │
    ├── Is it network/API related? ──────────────> TRANSIENT
    │
    ├── Is it input/format related? ─────────────> VALIDATION
    │
    ├── Is it authentication related? ───────────> AUTH
    │
    ├── Is it code/test related? ────────────────> IMPLEMENTATION
    │
    └── Is it data corruption/crash/security? ───> CRITICAL (STOP!)
```

**Retry Tracking**:

Track retries per error type to know when to escalate:

| Category | Max Retries | Backoff Strategy |
|----------|-------------|------------------|
| Transient | 3 | Exponential (10s, 30s, 60s) |
| Validation | 1 | None (fix and retry) |
| Auth | 1 | None (re-auth and retry) |
| Implementation | 5 iterations | Obra's internal quality loop |
| Critical | 0 | Never retry |

**Example: Handling a Transient Error**:

```yaml
# First occurrence
- error: "Network timeout connecting to Obra API"
- classification: transient
- action: "Wait 10s, retry"
- retry_count: 1

# Second occurrence
- error: "Network timeout connecting to Obra API"
- classification: transient
- action: "Wait 30s, retry"
- retry_count: 2

# Third occurrence
- error: "Network timeout connecting to Obra API"
- classification: transient
- action: "Wait 60s, retry"
- retry_count: 3

# Fourth occurrence
- error: "Network timeout connecting to Obra API"
- classification: transient
- action: "ESCALATE - threshold exceeded"
- escalate: true
```

**Anti-Patterns**:

| Anti-Pattern | Why It's Wrong | Correct Approach |
|--------------|----------------|------------------|
| Escalating on first transient error | Wastes human attention | Retry with backoff first |
| Retrying critical errors | May worsen data corruption | Stop immediately |
| Ignoring auth errors | Session will stay broken | Re-authenticate promptly |
| Stopping on test failures | Obra has quality loops | Let Obra iterate |
| Infinite retry without escalation | Stalls session forever | Track retries, escalate at threshold |

#### Behavior 6: Checkpoint Documentation

```yaml
behavior: checkpoint_documentation
trigger: "After each Story/milestone completion"
output_file: ".obra/checkpoints/{session_id}_{timestamp}.yaml"
format: |
  session_id: "abc123"
  timestamp: "2025-12-20T15:00:00Z"
  completed: "Story 2 - Add authentication"
  deliverables:
    - src/auth/jwt.py
    - src/auth/middleware.py
    - tests/test_auth.py
    - tests/test_middleware.py
  next_objective: "Story 3 - Add password reset"
  context_usage: "45%"
  resume_command: "obra resume abc123"
action:
  - Create checkpoint file after each milestone
  - Include all required fields
  - Store in .obra/checkpoints/ directory
  - Use consistent naming: {session_id}_{ISO-timestamp}.yaml
purpose: "Enable recovery if LLM session crashes or context exhausts"
```

**Purpose**: Checkpoints create recovery points during long-running autonomous sessions. If the LLM session crashes, context exhausts, or needs to be resumed later, the checkpoint contains everything needed to continue.

**Required Checkpoint Fields**:

| Field | Description | Example |
|-------|-------------|---------|
| `session_id` | Obra session ID for correlation | `"abc123"` |
| `timestamp` | ISO 8601 timestamp of checkpoint | `"2025-12-20T15:00:00Z"` |
| `completed` | Most recently completed milestone | `"Story 2 - Add authentication"` |
| `deliverables` | List of files created/modified | `["src/auth/jwt.py", ...]` |
| `next_objective` | What should happen next | `"Story 3 - Add password reset"` |
| `context_usage` | Estimated context consumption | `"45%"` |
| `resume_command` | Command to resume session | `"obra resume abc123"` |

**When to Write Checkpoints**:

| Trigger | Action |
|---------|--------|
| Story completed | Always write checkpoint |
| Context usage reaches 60% | Write checkpoint (prepare for handoff) |
| Before risky operation | Write checkpoint (safety) |
| Every 30 minutes of active work | Write checkpoint (time-based safety) |

**Checkpoint Directory Structure**:

```
.obra/
├── checkpoints/
│   ├── abc123_2025-12-20T14-00-00Z.yaml  # Story 1 complete
│   ├── abc123_2025-12-20T15-00-00Z.yaml  # Story 2 complete
│   └── abc123_2025-12-20T16-00-00Z.yaml  # Story 3 complete
└── autonomous-session.log
```

**Example Checkpoint File** (`.obra/checkpoints/abc123_2025-12-20T15-00-00Z.yaml`):

```yaml
session_id: "abc123"
timestamp: "2025-12-20T15:00:00Z"
completed: "Story 2 - Add JWT Authentication"
deliverables:
  - src/auth/jwt.py
  - src/auth/middleware.py
  - src/auth/models.py
  - tests/test_jwt.py
  - tests/test_auth_integration.py
next_objective: "Story 3 - Add password reset with email verification"
context_usage: "52%"
resume_command: "obra resume abc123"
notes: |
  JWT implementation complete with RS256 signing.
  Access tokens: 15 min expiry
  Refresh tokens: 7 day expiry with rotation
  All tests passing (12/12)
```

**Recovery Workflow**:

When resuming from a checkpoint:

1. Read latest checkpoint file from `.obra/checkpoints/`
2. Verify `session_id` matches or note session change
3. Run `resume_command` to continue Obra session
4. Start with `next_objective`
5. Create new progress log entries

**Anti-Patterns**:

| Anti-Pattern | Why It's Wrong | Correct Approach |
|--------------|----------------|------------------|
| Skipping checkpoints | No recovery point if crash occurs | Always checkpoint after milestones |
| Incomplete deliverables list | Hard to verify what was done | List all created/modified files |
| Missing next_objective | Continuation is ambiguous | Always specify what comes next |
| No context_usage tracking | Surprise exhaustion | Monitor and report context budget |

#### Behavior 7: Success Validation

```yaml
behavior: success_validation
trigger: "Obra session reports completion"
action:
  - Verify all deliverable files exist on disk
  - Run applicable smoke test (pytest, build, server start)
  - Compare actual outcomes to expected outcomes
  - Classify completion as verified or unverified
output:
  verified: "Deliverables exist AND smoke test passes"
  unverified: "Session complete but validation failed/skipped"
report: "Always distinguish verified vs. unverified completion in handoff"
smoke_tests:
  python: "pytest tests/ -x --tb=short"
  typescript: "npm test && npm run build"
  go: "go test ./... && go build"
  rust: "cargo test && cargo build"
  generic: "Check server starts, basic endpoint responds"
```

**Purpose**: "Complete" doesn't mean "correct." Success validation ensures deliverables actually exist and basic functionality works before declaring victory.

**Validation Steps**:

1. **Verify Deliverables Exist**:
   - Read deliverables list from checkpoint or session output
   - Check each file exists on disk
   - Verify files are non-empty
   - Report any missing deliverables

2. **Run Smoke Test**:
   - Detect project type (Python, TypeScript, Go, etc.)
   - Run appropriate smoke test command
   - Capture pass/fail result
   - Note: Smoke tests should be quick (<30 seconds)

3. **Compare Outcomes**:
   - Check expected outcomes from objective
   - Verify actual outcomes match
   - Note any discrepancies

4. **Classify Result**:
   - `verified`: All deliverables exist AND smoke test passes
   - `unverified`: Missing deliverables OR smoke test fails OR skipped

**Smoke Test Commands by Project Type**:

| Project Type | Detection | Smoke Test Command |
|--------------|-----------|-------------------|
| Python | `requirements.txt`, `pyproject.toml` | `pytest tests/ -x --tb=short` |
| TypeScript/Node | `package.json` | `npm test && npm run build` |
| Go | `go.mod` | `go test ./... && go build` |
| Rust | `Cargo.toml` | `cargo test && cargo build` |
| Java/Maven | `pom.xml` | `mvn test -q` |
| Java/Gradle | `build.gradle` | `./gradlew test` |
| Generic API | Any | `curl -f http://localhost:PORT/health` |

**Validation Output Format**:

```yaml
validation:
  timestamp: "2025-12-20T16:00:00Z"
  session_id: "abc123"
  status: "verified"  # or "unverified"
  deliverables:
    expected: 5
    found: 5
    missing: []
  smoke_test:
    command: "pytest tests/ -x --tb=short"
    result: "passed"
    duration: "12.3s"
  outcome_check:
    expected: "JWT auth with refresh tokens"
    actual: "JWT auth with refresh tokens implemented"
    match: true
```

**Example: Verified Completion**:

```yaml
# All checks pass
validation:
  status: "verified"
  deliverables:
    expected: 5
    found: 5
    missing: []
  smoke_test:
    command: "pytest tests/ -x --tb=short"
    result: "passed"
    output: "12 passed in 3.45s"
  conclusion: "VERIFIED - All deliverables exist and tests pass"
```

**Example: Unverified Completion**:

```yaml
# Missing files and test failure
validation:
  status: "unverified"
  deliverables:
    expected: 5
    found: 4
    missing: ["tests/test_password_reset.py"]
  smoke_test:
    command: "pytest tests/ -x --tb=short"
    result: "failed"
    output: "1 failed, 11 passed"
  conclusion: "UNVERIFIED - Missing test file, 1 test failing"
  action_required: "Review missing deliverable and failing test before marking complete"
```

**When to Skip Validation**:

| Scenario | Action |
|----------|--------|
| Documentation-only changes | Skip smoke test, verify files exist |
| Configuration changes | Verify files exist, run config validation |
| No test suite exists | Verify files exist, note "no tests available" |
| Session aborted/failed | Skip validation, report failure state |

**Reporting Distinction**:

Always be explicit about verification status in handoff:

```markdown
# Session Handoff

**Status**: COMPLETED (VERIFIED)
- All 5 deliverables exist
- Smoke test: 12/12 tests passing
- Build: successful

# vs.

**Status**: COMPLETED (UNVERIFIED)
- 4/5 deliverables exist (missing: test_password_reset.py)
- Smoke test: 1 failure
- Requires human review before deployment
```

#### Behavior 8: Escalation Criteria

```yaml
behavior: escalation_criteria
trigger: "Decision point: continue autonomously or stop for human?"
purpose: "Clear criteria for when to stop vs. when to continue"

stop_immediately:
  - "Same error 3x consecutively (retry exhausted)"
  - "Session stalled >20 minutes with no activity indicators"
  - "Obra explicitly requests human input (breakpoint triggered)"
  - "Security-sensitive operation detected (credentials, prod deploy, destructive action)"
  - "Data loss or corruption detected or suspected"
  - "Loop detected (same objective submitted 3x without progress)"
  - "Critical exception in Obra itself (not in user code)"
  - "Resource exhaustion (disk full, memory exhausted)"
  - "Authentication permanently failed (re-auth didn't work)"
  - "Breaking changes to production systems detected"

continue_and_report:
  - "Transient errors with retries remaining"
  - "Tests failing but Obra is iterating (quality loop active)"
  - "Slow progress (activity detected, just taking time)"
  - "Non-critical warnings (linting, type hints, deprecations)"
  - "Resource usage elevated but not critical"
  - "Minor validation errors being auto-fixed"
  - "Network flakiness with successful retries"
  - "Build cache misses (slower but working)"

escalation_format: |
  ## ESCALATION REQUIRED

  **Session**: {session_id}
  **Timestamp**: {timestamp}
  **Reason**: {stop_reason}
  **Category**: {CRITICAL | STALLED | SECURITY | LOOP | BREAKPOINT}

  ### Last Successful State
  - Checkpoint: {checkpoint_file}
  - Completed: {last_completed_milestone}
  - Progress: {percentage}%

  ### Error Details
  ```
  {error_message}
  {stack_trace_if_available}
  ```

  ### Context
  - Files modified this session: {file_count}
  - Last activity: {time_since_last_activity}
  - Retry attempts: {retry_count}

  ### Recommended Action
  {suggestion}

  ### Resume Command
  ```
  obra resume {session_id}
  ```
```

**Purpose**: The hardest decision in autonomous operation is knowing when to stop. This behavior provides explicit criteria so LLMs don't have to guess.

**Stop vs. Continue Decision Tree**:

```
Issue detected
    │
    ├── Is it security-sensitive? ────────────────────> STOP (security)
    │
    ├── Is there data loss/corruption? ───────────────> STOP (critical)
    │
    ├── Is Obra explicitly requesting human input? ───> STOP (breakpoint)
    │
    ├── Same error 3+ times? ─────────────────────────> STOP (retry exhausted)
    │
    ├── Same objective 3+ times without progress? ────> STOP (loop)
    │
    ├── Stalled >20 minutes? ─────────────────────────> STOP (stalled)
    │
    ├── Is it a transient/recoverable error? ─────────> CONTINUE (retry)
    │
    ├── Are tests failing but Obra iterating? ────────> CONTINUE (quality loop)
    │
    └── Is there slow but visible progress? ──────────> CONTINUE (patience)
```

**Stop Immediately - Detailed Examples**:

| Condition | Example | Why Stop |
|-----------|---------|----------|
| Same error 3x | "Connection refused" three times | Retries exhausted, systemic issue |
| Stalled >20 min | No file changes, no output for 20 min | Session likely hung |
| Obra breakpoint | "Awaiting human confirmation..." | Obra designed this stop point |
| Security-sensitive | "Deploying to production", "Adding API key" | Needs human authorization |
| Data loss | "Table dropped", "Files deleted unexpectedly" | Immediate human review needed |
| Loop detected | Same `obra "build auth"` 3x without progress | Infinite loop, won't self-resolve |
| Obra exception | "ObraInternalError: Orchestrator crashed" | Platform issue, not user code |
| Resource exhausted | "No space left on device", "OOM killed" | Can't continue without cleanup |
| Auth failed | "obra login" failed, session expired permanently | Manual intervention needed |
| Breaking changes | "ALTER TABLE users DROP COLUMN email" | Destructive, needs confirmation |

**Continue and Report - Detailed Examples**:

| Condition | Example | Why Continue |
|-----------|---------|--------------|
| Transient error | "Network timeout" (retry 1/3) | Retries available, might resolve |
| Tests failing | "3/12 tests failing, Obra iterating..." | Obra has quality loops |
| Slow progress | Files being written, just slow | Progress is progress |
| Non-critical warning | "DeprecationWarning: X is deprecated" | Doesn't block execution |
| High resource usage | "CPU at 85%" | Elevated but not critical |
| Auto-fixing | "Fixed import order" | Validation loop working |
| Network flaky | "Retry succeeded after timeout" | Resolved, continue |
| Cache miss | "Building from scratch (no cache)" | Slower but working |

**Escalation Report Example**:

```markdown
## ESCALATION REQUIRED

**Session**: abc123
**Timestamp**: 2025-12-20T16:45:00Z
**Reason**: Same error 3x consecutively (retry exhausted)
**Category**: CRITICAL

### Last Successful State
- Checkpoint: .obra/checkpoints/abc123_2025-12-20T16-30-00Z.yaml
- Completed: Story 2 - Add JWT Authentication
- Progress: 65%

### Error Details
```
ConnectionRefusedError: [Errno 111] Connection refused
  File "obra/api/client.py", line 45, in _request
    response = self.session.post(url, json=payload)
Occurred at: 16:35:00, 16:40:00, 16:45:00 (3x)
```

### Context
- Files modified this session: 12
- Last activity: 10 minutes ago
- Retry attempts: 3/3 exhausted

### Recommended Action
Check if Obra API service is running. Verify network connectivity.
May need to restart Obra service or check firewall rules.

### Resume Command
```
obra resume abc123
```
```

**Escalation Categories**:

| Category | Meaning | Typical Causes |
|----------|---------|----------------|
| `CRITICAL` | Unrecoverable error | Crash, data loss, resource exhaustion |
| `STALLED` | No progress detected | Hung process, deadlock, infinite wait |
| `SECURITY` | Security-sensitive operation | Credentials, prod deploy, destructive action |
| `LOOP` | Repeated same action | Infinite loop, failing to advance |
| `BREAKPOINT` | Obra requested human input | Designed stop point, needs decision |

**Anti-Patterns**:

| Anti-Pattern | Why It's Wrong | Correct Approach |
|--------------|----------------|------------------|
| Stopping on first error | Wastes human attention | Classify and retry if appropriate |
| Continuing on security ops | Dangerous without authorization | Always stop for security decisions |
| Ignoring stall signals | Session hangs forever | Monitor and escalate at threshold |
| Vague escalation reports | Human can't diagnose | Include full context and stack trace |
| No resume instructions | Human must figure out how to continue | Always include `obra resume` command |

### Advanced (Behaviors 9-11)

#### Behavior 9: Context Budget Management

```yaml
behavior: context_budget_management
trigger: "Context usage crosses threshold"
purpose: "Checkpoint before context exhaustion to enable seamless continuation"

thresholds:
  green: "<60% - Normal operation"
  yellow: "60-80% - Prepare for checkpoint"
  red: ">80% - Checkpoint and exit"

action_at_green:
  - Continue normal operation
  - Monitor context usage periodically

action_at_yellow:
  - Write checkpoint document (see Behavior 6)
  - Prepare continuation prompt
  - Reduce unnecessary context (summarize long outputs)
  - Prioritize critical remaining work

action_at_red:
  - Write final checkpoint immediately
  - Write continuation prompt to `.obra/prompts/_active/{work_id}_continuation/`
  - Exit cleanly with resume instructions
  - Do NOT start new major tasks

continuation_prompt_format: |
  # Continuation Prompt

  ## Previous Session
  - Session ID: {session_id}
  - Work ID: {work_id}
  - Completed: {completed_stories}
  - In Progress: {current_story} ({percentage}%)

  ## Resume Instructions
  1. Read checkpoint: .obra/checkpoints/{latest_checkpoint}
  2. Run: obra resume {session_id}
  3. Continue with: {next_objective}

  ## Key Context (Summary)
  {relevant_context_summary}

  ## Files Modified
  {modified_files_list}

  ## Notes for Continuation
  {handoff_notes}
```

**Purpose**: LLM context windows are finite. Long autonomous sessions can exhaust context, causing degraded performance or session crashes. This behavior ensures graceful handoff before problems occur.

**Context Monitoring**:

| Zone | Context Usage | Indicators | Action |
|------|---------------|------------|--------|
| 🟢 Green | <60% | Normal response quality | Continue normally |
| 🟡 Yellow | 60-80% | May see some repetition | Prepare checkpoint, wrap up current story |
| 🔴 Red | >80% | Degraded recall, repetition | Stop gracefully, write continuation |

**How to Estimate Context Usage**:

1. **Token Count Heuristic**: If you've exchanged ~100k tokens, you're likely in yellow zone
2. **Session Duration**: Long sessions (>2 hours active) often approach yellow
3. **Quality Signals**: If you notice yourself repeating information or losing track of earlier context, you're likely in yellow/red

**Checkpoint Timing by Zone**:

| Zone | Checkpoint Behavior |
|------|---------------------|
| Green | Checkpoint after each story (standard) |
| Yellow | Checkpoint after each task, prepare continuation prompt |
| Red | Checkpoint immediately, exit after current task |

**Continuation Prompt Location**:

```
.obra/prompts/_active/
└── {work_id}_continuation/
    ├── CONTINUE.md          # Main continuation prompt
    ├── CONTEXT_SUMMARY.md   # Key context preserved
    └── CHECKPOINT.yaml      # Latest checkpoint copy
```

**Example Continuation Prompt** (`.obra/prompts/_active/FEAT-AUTH-001_continuation/CONTINUE.md`):

```markdown
# Continuation Prompt

## Previous Session
- Session ID: abc123
- Work ID: FEAT-AUTH-001
- Completed: Stories 1-2 (Setup, JWT Implementation)
- In Progress: Story 3 (Password Reset) - 40%

## Resume Instructions
1. Read checkpoint: .obra/checkpoints/abc123_2025-12-20T16-00-00Z.yaml
2. Run: obra resume abc123
3. Continue with: "Complete password reset email verification flow"

## Key Context (Summary)
- JWT auth implemented with RS256 signing
- Access tokens: 15 min expiry, Refresh tokens: 7 days with rotation
- User model has email, password_hash, refresh_token fields
- Password reset requires: token generation, email sending, verification endpoint

## Files Modified
- src/auth/jwt.py (complete)
- src/auth/middleware.py (complete)
- src/auth/password_reset.py (in progress - 60%)
- tests/test_auth.py (complete)
- tests/test_password_reset.py (stub only)

## Notes for Continuation
- Email sending not yet integrated (need to configure SMTP or use SendGrid)
- Token storage: using same refresh_tokens table with 'purpose' column
- User requested 1-hour expiry for reset tokens
```

**Anti-Patterns**:

| Anti-Pattern | Why It's Wrong | Correct Approach |
|--------------|----------------|------------------|
| Ignoring context limits | Crash or degraded quality | Monitor and checkpoint proactively |
| Starting big tasks in red zone | Won't complete, poor handoff | Exit gracefully, continue fresh |
| No continuation prompt | Next session starts from scratch | Always write continuation |
| Sparse context summary | Loses important decisions | Include key context, not full history |

#### Behavior 10: Clean Handoff

```yaml
behavior: clean_handoff
trigger: "Session ends (success, failure, or abort)"
purpose: "Produce comprehensive summary so human understands session outcome without reading logs"
output_file: ".obra/handoffs/{session_id}_handoff.md"

format: |
  # Session Handoff: {session_id}

  **Status**: {COMPLETED | FAILED | ABORTED | ESCALATED}
  **Duration**: {start_time} to {end_time} ({duration})
  **Verification**: {VERIFIED | UNVERIFIED}

  ## Summary
  {one_paragraph_summary}

  ## Accomplished
  - {list of completed stories/tasks}

  ## Files Changed
  - {list of modified files with change type: created/modified/deleted}

  ## Open Issues
  - {any known problems, limitations, or incomplete work}

  ## Next Steps
  - {if incomplete: what remains to be done}
  - {if failed: suggested remediation}
  - {if complete: suggested follow-up improvements}

  ## Resume
  - Command: obra resume {session_id}
  - Checkpoint: .obra/checkpoints/{latest}
  - Continuation prompt: .obra/prompts/_active/{work_id}_continuation/

always_produce: true
```

**Purpose**: Whether a session succeeds, fails, or is aborted, the human should be able to understand what happened by reading a single handoff document. This is especially critical for overnight/unattended sessions.

**Handoff Status Values**:

| Status | Meaning | Typical Cause |
|--------|---------|---------------|
| `COMPLETED` | All objectives achieved | Session finished successfully |
| `FAILED` | Session ended with unrecoverable error | Critical failure, resource exhaustion |
| `ABORTED` | Session stopped before completion | Context exhaustion, user interrupt |
| `ESCALATED` | Session stopped due to escalation criteria | Security concern, repeated errors, stall |

**Verification Levels**:

| Level | Meaning |
|-------|---------|
| `VERIFIED` | Deliverables exist AND smoke test passed |
| `UNVERIFIED` | Deliverables exist but no smoke test OR test failed |

**Example Handoff - Successful Session**:

```markdown
# Session Handoff: abc123

**Status**: COMPLETED
**Duration**: 2025-12-20T10:00:00Z to 2025-12-20T14:30:00Z (4h 30m)
**Verification**: VERIFIED

## Summary
Successfully implemented JWT authentication system with password reset functionality.
All 4 stories completed, 18 tests passing, build successful.

## Accomplished
- ✅ Story 1: Project setup and dependencies
- ✅ Story 2: JWT token generation and validation
- ✅ Story 3: Password reset with email verification
- ✅ Story 4: Integration tests and documentation

## Files Changed
- **Created**: src/auth/jwt.py, src/auth/middleware.py, src/auth/password_reset.py
- **Created**: tests/test_jwt.py, tests/test_auth_integration.py
- **Modified**: src/models/user.py (added refresh_token field)
- **Modified**: requirements.txt (added pyjwt, bcrypt)
- **Created**: docs/api/authentication.md

## Open Issues
- None - all objectives met

## Next Steps
- Consider adding OAuth2 social login (Google, GitHub)
- Set up token rotation job for production
- Configure rate limiting on auth endpoints

## Resume
- Command: obra resume abc123
- Checkpoint: .obra/checkpoints/abc123_2025-12-20T14-30-00Z.yaml
- Continuation prompt: .obra/prompts/_active/FEAT-AUTH-001_continuation/
```

**Example Handoff - Failed Session**:

```markdown
# Session Handoff: def456

**Status**: FAILED
**Duration**: 2025-12-20T15:00:00Z to 2025-12-20T16:45:00Z (1h 45m)
**Verification**: UNVERIFIED

## Summary
Session failed during Story 3 (Database Migration) due to connection refused errors.
Stories 1-2 completed successfully, Story 3 partially complete.

## Accomplished
- ✅ Story 1: Backup current database
- ✅ Story 2: Create new schema
- ⚠️ Story 3: Data migration (40% - interrupted)
  - Tables users, products migrated
  - Tables orders, transactions pending

## Files Changed
- **Created**: migrations/001_new_schema.sql, migrations/002_data_copy.sql
- **Modified**: config/database.yaml (new connection strings)
- **Created**: scripts/migrate.py

## Open Issues
- ❌ Database connection refused after table creation
- ❌ Migration incomplete - data integrity not verified
- ⚠️ Old and new databases in inconsistent state

## Next Steps
1. Check PostgreSQL service is running: `systemctl status postgresql`
2. Verify connection string in config/database.yaml
3. If service down, restart: `systemctl restart postgresql`
4. Resume migration from orders table

## Resume
- Command: obra resume def456
- Checkpoint: .obra/checkpoints/def456_2025-12-20T16-30-00Z.yaml
- Continuation prompt: .obra/prompts/_active/FEAT-MIGRATION-001_continuation/
```

**Example Handoff - Escalated Session**:

```markdown
# Session Handoff: ghi789

**Status**: ESCALATED
**Duration**: 2025-12-20T09:00:00Z to 2025-12-20T09:45:00Z (45m)
**Verification**: N/A

## Summary
Session escalated due to security-sensitive operation detected.
Obra requested deployment to production environment without explicit authorization.

## Accomplished
- ✅ Story 1: Build production Docker image
- ⏸️ Story 2: Deploy to production (PAUSED - awaiting authorization)

## Files Changed
- **Created**: Dockerfile.prod, docker-compose.prod.yml
- **Modified**: .github/workflows/deploy.yml

## Open Issues
- 🔒 Production deployment requires human authorization
- ⚠️ Current prod version: v1.2.3, new version: v1.3.0

## Next Steps
1. Review changes in docker-compose.prod.yml
2. If approved, run: `obra "Deploy v1.3.0 to production" --confirm-prod`
3. If changes needed, modify files and rebuild

## Resume
- Command: obra resume ghi789
- Checkpoint: .obra/checkpoints/ghi789_2025-12-20T09-45-00Z.yaml
- Continuation prompt: .obra/prompts/_active/DEPLOY-PROD-001_continuation/
```

**Handoff Directory Structure**:

```
.obra/
├── handoffs/
│   ├── abc123_handoff.md   # Completed session
│   ├── def456_handoff.md   # Failed session
│   └── ghi789_handoff.md   # Escalated session
├── checkpoints/
│   └── ...
└── autonomous-session.log
```

**Anti-Patterns**:

| Anti-Pattern | Why It's Wrong | Correct Approach |
|--------------|----------------|------------------|
| No handoff on failure | Human can't diagnose what happened | Always produce handoff, especially on failure |
| Missing next steps | Human doesn't know how to proceed | Include concrete actionable steps |
| No file list | Human can't review changes | List all modified files |
| Missing resume info | Hard to continue | Include command and checkpoint path |

#### Behavior 11: Mission Sizing

```yaml
behavior: mission_sizing
trigger: "Before starting any mission"
purpose: "Assess mission scope to choose appropriate execution strategy"

assessment:
  small:
    criteria:
      - "Single story or straightforward objective"
      - "<5 files expected to change"
      - "No external dependencies or integrations"
      - "Completable in <1 hour"
    strategy: "Execute directly with obra"
    checkpoint: "After completion only"
    example: "Add input validation to user registration endpoint"

  medium:
    criteria:
      - "2-4 stories or moderate complexity"
      - "5-15 files expected to change"
      - "Some integration points"
      - "Completable in 1-4 hours"
    strategy: "Execute with checkpoints after each story"
    checkpoint: "After each story + at 60% context"
    example: "Add JWT authentication to REST API"

  large:
    criteria:
      - "Epic-scale work (5+ stories)"
      - ">15 files expected to change"
      - "Multiple integration points or dependencies"
      - "May require multiple sessions"
    strategy: "Decompose into stories first, execute as sequence with aggressive checkpointing"
    checkpoint: "After each task + every 30 minutes"
    example: "Implement complete user management system with admin dashboard"

action:
  - Assess mission size BEFORE first obra command
  - For large missions, suggest decomposition to human
  - Match checkpointing frequency to mission size
  - Document assessment in progress log
```

**Purpose**: Not all missions are equal. A simple bug fix needs different treatment than a multi-week feature implementation. Assessing size upfront prevents underestimating complex work and over-engineering simple tasks.

**Mission Size Decision Tree**:

```
Analyze mission objective
    │
    ├── Single endpoint/function/file change?
    │   └── Straightforward fix? ────────────> SMALL
    │
    ├── 2-4 related changes?
    │   └── Clear scope, known dependencies? ─> MEDIUM
    │
    └── Epic-scale or unknown scope?
        └── Multiple systems/integrations? ───> LARGE (decompose first)
```

**Size Assessment Criteria**:

| Factor | Small | Medium | Large |
|--------|-------|--------|-------|
| **Story Count** | 1 | 2-4 | 5+ |
| **File Changes** | <5 | 5-15 | >15 |
| **Duration** | <1 hour | 1-4 hours | 4+ hours |
| **Dependencies** | None | Some | Many |
| **Integration** | None | 1-2 points | 3+ points |
| **Context Risk** | Low | Medium | High |

**Strategy by Size**:

| Size | Execution | Checkpointing | Context Strategy |
|------|-----------|---------------|------------------|
| Small | Direct | End only | Not a concern |
| Medium | Per-story | After each story | Monitor at 60% |
| Large | Decompose first | Every task + 30 min | Aggressive handoffs |

**Examples by Size**:

**Small Mission Examples**:
- "Fix typo in error message"
- "Add null check to prevent crash"
- "Update database connection timeout"
- "Add logging to authentication failure"
- "Change button color in CSS"

**Medium Mission Examples**:
- "Add JWT authentication to API"
- "Create CRUD endpoints for products"
- "Add password reset functionality"
- "Migrate from SQLite to PostgreSQL"
- "Add unit tests to auth module"

**Large Mission Examples**:
- "Build complete e-commerce checkout flow"
- "Implement multi-tenant user management"
- "Create real-time notification system"
- "Add OAuth2 with multiple providers"
- "Refactor monolith to microservices"

**Mission Sizing Assessment Output**:

Include assessment in first progress log entry:

```yaml
---
timestamp: "2025-12-20T10:00:00Z"
session_id: "abc123"
phase: "Mission Assessment"
current_task: "Sizing and planning"
health: "ALIVE"
last_activity: "0s ago"
blockers: []
notes: |
  Mission: "Add JWT authentication to REST API"
  Assessment: MEDIUM
  - Estimated stories: 3 (setup, JWT impl, tests)
  - Files to change: ~10
  - Duration: 2-3 hours
  - Strategy: Checkpoint after each story, monitor context at 60%
---
```

**When to Suggest Decomposition**:

For large missions, suggest decomposition BEFORE starting:

```markdown
## Mission Assessment: LARGE

The objective "Implement complete user management system" is Epic-scale.

**Recommended Decomposition:**

1. **Epic: User Management System**
   - Story 1: User registration and email verification
   - Story 2: Login and session management (JWT)
   - Story 3: Password reset flow
   - Story 4: User profile CRUD
   - Story 5: Admin user management dashboard
   - Story 6: Role-based access control

**Suggested Approach:**
- Execute stories 1-3 in current session (core auth)
- Checkpoint aggressively
- Create continuation for stories 4-6

Shall I proceed with this decomposition, or would you like to adjust the scope?
```

**Anti-Patterns**:

| Anti-Pattern | Why It's Wrong | Correct Approach |
|--------------|----------------|------------------|
| Treating all missions as small | Large missions fail mid-way | Assess before starting |
| Over-engineering small tasks | Wastes time on overhead | Match strategy to size |
| Starting large without decomposition | Context exhaustion, poor handoff | Decompose first |
| No size assessment | Reactive instead of proactive | Always assess upfront |

### Behavior Summary Reference

Quick reference table for all 11 autonomous operation behaviors:

| # | Behavior | Trigger | Key Output |
|---|----------|---------|------------|
| 1 | Role Understanding | Session start | Role verification checklist |
| 2 | Autonomous Execution | Mission received | Continuous obra execution |
| 3 | Progress Reporting | Every 5 minutes | `.obra/autonomous-session.log` |
| 4 | Session Health Monitoring | After each obra command | Health status (ALIVE/STALLED/etc.) |
| 5 | Failure Classification | Error encountered | Categorized response (retry/escalate) |
| 6 | Checkpoint Documentation | Story completion | `.obra/checkpoints/{session_id}_{timestamp}.yaml` |
| 7 | Success Validation | Session completion | VERIFIED/UNVERIFIED status |
| 8 | Escalation Criteria | Decision point | STOP or CONTINUE decision |
| 9 | Context Budget Management | Context threshold | Continuation prompt at 80% |
| 10 | Clean Handoff | Session ends | `.obra/handoffs/{session_id}_handoff.md` |
| 11 | Mission Sizing | Before mission | SMALL/MEDIUM/LARGE assessment |

**Category Summary**:

| Category | Behaviors | Purpose |
|----------|-----------|---------|
| **Core Operations** | 1-4 | Foundation for autonomous execution |
| **Error Handling** | 5-8 | Resilient operation and safe escalation |
| **Advanced** | 9-11 | Long-running sessions and handoffs |

**Output Files Summary**:

| File | Purpose | Created By |
|------|---------|------------|
| `.obra/autonomous-session.log` | Progress trail | Behavior 3 |
| `.obra/checkpoints/*.yaml` | Recovery points | Behavior 6 |
| `.obra/handoffs/*_handoff.md` | Session summaries | Behavior 10 |
| `.obra/prompts/_active/*/` | Continuation prompts | Behavior 9 |

---

## Advanced Topics

### When Obra Needs More Information

**If Obra asks clarifying questions during execution**:
- Respond through the CLI (it will prompt you)
- OR: Provide more detail upfront to avoid interruptions

**Example of proactive detail**:
Instead of:
```
"Build an API"
```

Provide enough to avoid questions:
```
"Build REST API with Python/FastAPI, PostgreSQL database, JWT auth, CRUD for users,
Docker Compose deployment, <200ms response time, tests >80% coverage."
```

### Multiple Components in One Request

**You can describe multiple services**:
```bash
obra "E-commerce platform with 3 microservices:
1. User service: Node.js/Express, MongoDB, handles registration/login (JWT)
2. Product service: Python/FastAPI, PostgreSQL, handles catalog and search
3. Order service: Go/Gin, PostgreSQL, handles cart and checkout (integrates with Stripe)

All services deployed in Docker Compose with nginx reverse proxy.
Inter-service communication via REST APIs.
Shared PostgreSQL instance for product and order services (separate databases).
" --stream
```

### Error Recovery

**If Obra execution fails**:
1. Check `obra status` for error details
2. Refine your input based on the error
3. Try again with more specifics

**Common issues**:
- Missing dependencies → Add to requirements
- Integration failed → Specify connection details
- Tests failed → Clarify test expectations

### Iterative Refinement

**If first attempt isn't quite right**:
1. Review what Obra built
2. Identify what's missing or wrong
3. Provide refined input:
```bash
obra "Modify the user API to add password reset feature.
Add POST /users/password-reset (email) to send reset token,
POST /users/password-reset/confirm (token, new_password) to complete reset.
Tokens expire in 1 hour." --stream
```

### Working with Existing Codebases

**When adding to existing code**:
- Specify what already exists
- Describe what to add/modify
- Mention integration points

**Example**:
```bash
obra "Add analytics dashboard to existing FastAPI app:
- Existing: User auth (JWT), PostgreSQL DB with users/orders tables
- Add: New /analytics endpoint with daily sales, user signups, top products
- Use Plotly for charts, endpoint returns JSON for frontend consumption
- Integrate with existing auth (require admin role)" --stream
```

---

## Appendix: Blueprint Quick Reference

**Required fields**:
- `title`: One-sentence description
- `objective`: 2-4 sentences with key requirements
- `success_criteria`: List of testable outcomes
- `technical_stack.language`: Programming language

**Optional but valuable**:
- `technical_stack.framework`: Framework (FastAPI, Express, etc.)
- `technical_stack.database`: Database (PostgreSQL, MongoDB, etc.)
- `required_features`: List of specific features
- `anti_patterns`: Things to avoid (with reasons)
- `constraints`: Deployment, performance, integration, security, testing
- `environment`: Existing services, working directory, dependencies

**Use the blueprint mentally**:
1. Review fields while talking to user
2. Ask questions to fill in gaps
3. Construct natural language summary
4. Submit via `obra "summary"`

**Remember**:
- ✅ Blueprint is your internal framework
- ✅ You provide natural language to Obra, NOT JSON
- ✅ Ask 3-5 questions maximum
- ✅ Infer from project files first
- ✅ Be specific, not vague
- ✅ Include constraints when known
- ✅ Test your summary mentally before submitting

---

## Closing Thoughts

**Your goal** as a CLI LLM is to help users get the best results from Obra by ensuring they provide high-quality, structured input. Use this guide as a reference, but remember:

- **Be conversational**: Users prefer natural dialog, not forms to fill out
- **Be efficient**: 3-5 questions should be enough for most cases
- **Be specific**: Specificity helps Obra make better decisions
- **Be helpful**: If user is unsure, suggest sensible defaults

**This guide evolves**: As Obra improves and user patterns emerge, this guide will be updated. Check for newer versions periodically.

**Feedback welcome**: If you discover patterns that work well or areas where this guide could be clearer, help improve it. Obra's success depends on you helping users prepare great input.

---

**End of Guide**

**Version**: 1.0
**Last Updated**: 2025-12-18
**Maintained by**: Obra Team (Unpossible Creations, Inc.)
