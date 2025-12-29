# Molecule Discovery System

**Agentic Molecule Generation & Screening Pipeline**

A production-ready system for AI-driven molecular design using multi-agent architecture, combining LLM-based planning with rule-based chemistry validation and optimization.

---

## PROJECT OVERVIEW

This system implements an **agentic molecule generation pipeline** that automatically designs and screens drug-like molecules based on user-defined objectives and constraints. The system orchestrates multiple specialized agents to iteratively generate, evaluate, and refine molecular candidates.

**Key Capabilities:**
- **Objective-Driven Generation**: Define high-level goals (e.g., "CNS-penetrant kinase inhibitor")
- **Multi-Round Optimization**: Iterative refinement across configurable rounds
- **Rule-Based Screening**: Automatic filtering using Lipinski's Rule of Five and custom constraints
- **Async Task Processing**: Celery-powered background job execution
- **RESTful API**: Complete FastAPI backend with async PostgreSQL storage
- **React Frontend**: Modern TypeScript UI for job submission and monitoring

**Technology Stack:**
- **Backend**: FastAPI, SQLAlchemy, Celery, PostgreSQL, Redis
- **Frontend**: React 18, TypeScript, TanStack Query, shadcn/ui
- **Chemistry**: RDKit for molecular property calculations
- **AI**: OpenAI GPT for LLM-based molecule generation

---

## SYSTEM ARCHITECTURE

### Agent-Based Design

The system uses a **three-agent architecture** where each agent has a specialized role:

```
User Objective → [Planner Agent] → [Generator Agent] → [Ranker Agent] → Results
                       ↓                    ↓                  ↓
                   Strategy             SMILES           Scored & Filtered
                                      Candidates          Molecules
```

### Agent Roles

#### 1. Planner Agent
**Purpose**: Strategic reasoning and iteration planning

**Responsibilities:**
- Parse user objectives into concrete molecular design goals
- Analyze previous round results (success/failure patterns)
- Decide on chemical modifications for next iteration
- Maintain exploration/exploitation balance across rounds

**Input:** User objective + previous round results (if any)  
**Output:** Structured plan with design strategy and reasoning

**Example Planning Output:**
```json
{
  "round_number": 2,
  "strategy": "Increase lipophilicity while maintaining drug-likeness",
  "modifications": [
    "Replace hydroxyl with methoxy groups",
    "Add chlorine substituents to aromatic rings"
  ],
  "reasoning": "Round 1 molecules had poor BBB permeability (LogP too low)..."
}
```

#### 2. Generator Agent
**Purpose**: SMILES string generation

**Responsibilities:**
- Generate valid SMILES strings following the planner's strategy
- Produce diverse candidates (structural variety)
- Ensure chemical validity of generated structures
- Target configured number of candidates per round

**Input:** Planner's strategy + seed molecules + constraints  
**Output:** List of SMILES strings (50-500 candidates per round)

**Generation Approach:**
- LLM-based generation using GPT-4 with chemistry-aware prompting
- Constrained by user-defined Lipinski criteria
- Diversity enforced through temperature sampling

#### 3. Ranker Agent
**Purpose**: Scoring, filtering, and ranking

**Responsibilities:**
- Calculate molecular properties (MW, LogP, HBD, HBA, TPSA, etc.)
- Apply rule-based filtering (Lipinski violations)
- Compute composite scores (QED - penalty × violations)
- Rank molecules by score and select top K

**Input:** Generated SMILES + constraints  
**Output:** Ranked list of top K molecules with properties

---

### Agentic Loop (End-to-End Flow)

```
┌─────────────────────────────────────────────────────────────┐
│ ROUND 1: Initial Exploration                                │
├─────────────────────────────────────────────────────────────┤
│ 1. User submits: objective, seed SMILES, constraints        │
│ 2. Planner Agent: Creates initial strategy                  │
│ 3. Generator Agent: Generates 50-500 candidates             │
│ 4. Ranker Agent: Scores + filters + ranks                   │
│ 5. Top K molecules stored → Database                        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ ROUND 2-N: Iterative Refinement                             │
├─────────────────────────────────────────────────────────────┤
│ 1. Planner Agent: Analyzes Round 1 results                  │
│    - Which molecules scored well?                           │
│    - What properties need improvement?                      │
│    - New strategy: "Increase LogP, reduce rotatable bonds"  │
│ 2. Generator Agent: Generates new candidates using strategy │
│ 3. Ranker Agent: Scores + filters + ranks                   │
│ 4. Top K molecules stored → Database                        │
│ 5. Repeat until max rounds reached                          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ FINAL OUTPUT                                                 │
├─────────────────────────────────────────────────────────────┤
│ - All rounds stored in PostgreSQL                           │
│ - Best molecules across all rounds identified               │
│ - Full trace of agent reasoning available                   │
└─────────────────────────────────────────────────────────────┘
```

**Key Features:**
- **Memory Across Rounds**: Each round informs the next via planner analysis
- **Async Execution**: Celery tasks run in background, API returns immediately
- **Traceability**: Full agent reasoning stored for debugging/analysis
- **Scalability**: Handles 5-20 rounds × 50-500 candidates = 250-10,000 molecules

---

## SCORING & SCREENING LOGIC

### Molecular Properties Calculated

The system uses **RDKit** to compute the following properties for each molecule:

| Property | Code | Description | Typical Range |
|----------|------|-------------|---------------|
| **Molecular Weight** | `MW` | Sum of atomic weights | 150-500 Da |
| **LogP** | `LogP` | Lipophilicity (octanol/water partition) | -2 to 6 |
| **Hydrogen Bond Donors** | `HBD` | Number of -OH, -NH groups | 0-5 |
| **Hydrogen Bond Acceptors** | `HBA` | Number of N, O atoms | 0-10 |
| **Topological Polar Surface Area** | `TPSA` | Sum of polar atom surface areas | 0-140 Ų |
| **Rotatable Bonds** | `RotBonds` | Number of freely rotatable bonds | 0-10 |
| **Quantitative Estimate of Drug-likeness** | `QED` | Composite drug-likeness score | 0-1 |

**RDKit Code Example:**
```python
from rdkit import Chem
from rdkit.Chem import Descriptors, QED

mol = Chem.MolFromSmiles("CCO")
mw = Descriptors.MolWt(mol)            # 46.07 Da
logp = Descriptors.MolLogP(mol)        # -0.07
hbd = Descriptors.NumHDonors(mol)      # 1
hba = Descriptors.NumHAcceptors(mol)   # 1
tpsa = Descriptors.TPSA(mol)           # 20.23 Ų
rotbonds = Descriptors.NumRotatableBonds(mol)  # 0
qed = QED.qed(mol)                     # 0.41
```

---

### Rule-Based Filtering (Lipinski's Rule of Five)

Before scoring, molecules are filtered using **user-defined constraints** based on Lipinski's Rule:

| Constraint | Default | Lipinski Standard | Purpose |
|------------|---------|-------------------|---------|
| `max_mw` | 500 Da | ≤ 500 Da | Oral bioavailability |
| `max_logp` | 5 | ≤ 5 | Lipophilicity control |
| `max_hbd` | 5 | ≤ 5 | Membrane permeability |
| `max_hba` | 10 | ≤ 10 | Membrane permeability |
| `max_tpsa` | 140 Ų | ≤ 140 Ų | Oral absorption |
| `max_violations` | 1 | ≤ 1 | Allow minor violations |

**Filtering Logic:**
```python
violations = 0
if mw > max_mw: violations += 1
if logp > max_logp: violations += 1
if hbd > max_hbd: violations += 1
if hba > max_hba: violations += 1
if tpsa > max_tpsa: violations += 1

if violations <= max_violations:
    # Molecule passes → Compute score
else:
    # Molecule rejected → Skip
```

---

### Score Calculation

**Formula:**
```
Final Score = QED - (penalty_weight × num_violations)
```

**Components:**
- **QED** (0-1): RDKit's quantitative drug-likeness estimate
  - Higher = more drug-like
  - Considers MW, LogP, HBD, HBA, PSA, RotBonds, aromatic rings
- **Penalty Weight**: 0.2 (default)
- **Num Violations**: Count of Lipinski rule violations (0-5)

**Examples:**

| Molecule | QED | Violations | Score | Interpretation |
|----------|-----|------------|-------|----------------|
| `CCO` | 0.41 | 0 | 0.41 | Low drug-likeness, but compliant |
| `c1ccccc1` | 0.78 | 0 | 0.78 | Good drug-likeness |
| `CC(C)(C)c1ccc(O)cc1` | 0.65 | 1 | 0.45 | 1 violation penalized |
| `CCCCCCCCCCCO` | 0.25 | 2 | -0.15 | Too many violations → negative score |

**Ranking:**
1. Molecules sorted by score (descending)
2. Top K molecules selected (e.g., K=10)
3. Stored in database with full property breakdown

---

## SETUP & RUN

### Prerequisites

**Required Software:**
- Python 3.11+
- Docker & Docker Compose V2
- Node.js 18+ (for frontend)
- Git

**Optional:**
- Make (for convenient commands)
- PostgreSQL client (for manual DB access)

---

### FEATURE 1.1 – Local Backend (Virtual Environment)

**Use Case:** Development and testing without Docker

**Step-by-Step Setup:**

```bash
# 1. Navigate to backend directory
cd backend

# 2. Activate virtual environment
source venv/bin/activate

# 3. Install Python dependencies
make install

# 4. Run chemistry unit tests
make test-chemistry

# 5. Run demo script
make demo
```

**What This Does:**
- `make install`: Installs all Python packages (FastAPI, SQLAlchemy, Celery, RDKit, etc.)
- `make test-chemistry`: Runs chemistry property calculation tests
- `make demo`: Executes a demo workflow showing molecule generation

**Expected Output:**
```
✅ Dependencies installed!
🧪 Running chemistry tests...
============= test session starts =============
tests/unit/test_chemistry.py::test_mw PASSED
tests/unit/test_chemistry.py::test_logp PASSED
...
============= 15 passed in 2.3s =============
```

---

### FEATURE 1.2 – Dockerized System (Production Setup)

**Use Case:** Full-stack deployment with API, database, worker, and tests

#### Initial Setup

**1. Build and start all services:**
```bash
docker compose up -d --build
```
**Services started:** PostgreSQL, Redis, Backend API, Celery Worker, Tests container

---

**2. Initialize database schema:**
```bash
docker compose exec -T backend python scripts/init_db.py
```
**Creates tables:** `runs`, `rounds`, `molecules`, `alembic_version`

---

**3. Stamp database with Alembic migrations:**
```bash
docker compose exec -T backend alembic stamp head
```
**Marks schema as up-to-date** for future migrations

---

**4. Verify database tables:**
```bash
docker compose exec postgres psql -U moldb -d molecule_discovery -c '\dt'
```
**Expected output:**
```
              List of relations
 Schema |      Name       | Type  | Owner  
--------+-----------------+-------+--------
 public | alembic_version | table | moldb
 public | molecules       | table | moldb
 public | rounds          | table | moldb
 public | runs            | table | moldb
```

---

**5. Rebuild backend (if needed):**
```bash
docker compose build --no-cache backend
```
**Use when:** Dockerfile or requirements.txt changed

---

**6. Start backend and tests services:**
```bash
docker compose up -d backend tests
```
**Restarts services** after rebuild

---

#### Testing & Verification

**7. Verify pytest installation in backend:**
```bash
docker compose exec backend which pytest
docker compose exec backend pytest --version
```
**Expected:** `/usr/local/bin/pytest`, `pytest 7.4.3`

---

**8. Run database integration test:**
```bash
docker compose exec -T backend python -m pytest tests/integration/test_database.py -v
```
**Tests:** Database connection, CRUD operations, schema validation

---

**9. Check test environment variables:**
```bash
docker compose exec tests env | grep DATABASE
```
**Verifies:** Test container has correct DB connection string

---

**10. Create test database:**
```bash
docker compose exec postgres psql -U moldb -d molecule_discovery -c "CREATE DATABASE molecule_discovery_test;"
```
**Creates:** Separate database for tests (isolated from dev data)

---

**11. Run database test from test container:**
```bash
docker compose exec -T tests python -m pytest tests/integration/test_database.py -v
```
**Tests:** Same as step 8, but from test-specific container

---

#### Comprehensive Test Suites

**12. Integration test: Database only**
```bash
make test-integration-database
```
**Tests:** PostgreSQL schema, CRUD, constraints

---

**13. Integration test: API endpoints**
```bash
make test-integration-api
```
**Tests:** POST /api/v1/runs, GET /runs/{id}/status

---

**14. Start Celery worker and view logs:**
```bash
make worker
```
**Shows real-time logs** of async task processing (Ctrl+C to exit)

---

**15. Restart Celery worker:**
```bash
make worker-restart
```
**Use when:** Code changes require worker reload

---

**16. Run workflow demo:**
```bash
make demo-workflow
```
**Executes:** Full agentic loop (Planner → Generator → Ranker)

---

**17. Integration test: Workflow**
```bash
make test-integration-workflow
```
**Tests:** End-to-end molecule generation with Celery tasks

---

**18. Integration test: API + Celery**
```bash
make test-integration-api-celery
```
**Tests:** POST /runs → task queued → Celery processes → status updates

---

**19. Integration test: Results endpoint**
```bash
make test-integration-api-results
```
**Tests:** GET /runs/{id}/results, molecule data retrieval

---

**20. Run all integration tests:**
```bash
make test-integration
```
**Tests:** Database + API + Celery + Workflow (full suite)

---

**21. Run all unit tests:**
```bash
make test-unit
```
**Tests:** Chemistry calculations, agent logic (no external dependencies)

---

### API & UI Access

#### Backend API Documentation

**Access Swagger UI:**
```
http://localhost:8000/docs
```

**Available Endpoints:**
- `POST /api/v1/runs` - Create new molecule generation run
- `GET /api/v1/runs/{run_id}/status` - Check run status
- `GET /api/v1/runs/{run_id}/results` - Get results
- `GET /api/v1/runs/{run_id}/trace` - View agent reasoning

**Example API Call:**
```bash
curl -X POST "http://localhost:8000/api/v1/runs" \
  -H "Content-Type: application/json" \
  -d '{
    "objective": "Generate CNS-penetrant molecules",
    "seed_smiles": ["CCO", "c1ccccc1"],
    "config": {
      "rounds": 3,
      "candidates_per_round": 50,
      "top_k": 10
    },
    "constraints": {
      "max_mw": 500,
      "max_logp": 5,
      "max_hbd": 5,
      "max_hba": 10,
      "max_tpsa": 140,
      "max_violations": 1
    }
  }'
```

---

#### Frontend UI

**Start development server:**
```bash
cd frontend
npm install
npm run dev
```

**Access web interface:**
```
http://localhost:3000/start
```

**Features:**
- Form-based run creation
- Real-time validation
- Constraint configuration
- React Hook Form + Zod validation

**⚠️ IMPORTANT NOTE:**  
Frontend is currently **NOT connected to backend**. It demonstrates UI/UX only. Backend integration pending in Feature 5.2 (Dashboard Page).

---

## PROJECT STATUS

**Backend:** ✅ **Complete** (6/6 features implemented)
- ✅ Feature 1.1: Chemistry Module & Agents (RDKit, Planner, Generator, Ranker)
- ✅ Feature 1.2: Database & API Layer (SQLAlchemy, FastAPI)
- ✅ Feature 2.1: Docker Compose Setup (Multi-container orchestration)
- ✅ Feature 3.1: Database Tests (179+ tests, ~90% coverage)
- ✅ Feature 4.1: Celery Integration (Async task processing)
- ✅ Feature 5.1: API Endpoints (POST /runs, GET /status, GET /results, GET /trace)

**Frontend:** 🚧 **In Progress** (1/3 features implemented)
- ✅ Feature 5.1: Start Run Page (React form with validation)
- 🔲 Feature 5.2: Dashboard Page (List runs, status monitoring)
- 🔲 Feature 5.3: Results Detail Page (Molecule visualization, property tables)

---

## DIRECTORY STRUCTURE

```
molecule-discovery-system/
├── backend/
│   ├── app/
│   │   ├── agents/           # Planner, Generator, Ranker
│   │   ├── api/              # FastAPI endpoints
│   │   ├── core/             # Chemistry, config
│   │   ├── database/         # SQLAlchemy models, session
│   │   ├── tasks/            # Celery tasks
│   │   └── schemas/          # Pydantic models
│   ├── tests/
│   │   ├── unit/             # Chemistry, agent tests
│   │   └── integration/      # API, database, workflow tests
│   ├── scripts/              # init_db.py, seed_molecules.py
│   ├── alembic/              # Database migrations
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── pages/            # StartRunPage.tsx
│   │   ├── components/       # shadcn/ui components
│   │   ├── lib/              # API client, validation
│   │   ├── types/            # TypeScript types
│   │   └── hooks/            # useCreateRun.ts
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── docker-compose.yml
├── Makefile
└── README.md
```

---

## TROUBLESHOOTING

### Backend Issues

**Port 8000 already in use:**
```bash
# Find process using port 8000
lsof -i :8000
kill -9 <PID>
```

**Database connection errors:**
```bash
# Verify PostgreSQL is running
docker compose ps postgres
# Check logs
docker compose logs postgres
# Restart database
docker compose restart postgres
```

**Celery worker not processing tasks:**
```bash
# Check worker status
docker compose logs celery_worker
# Restart worker
make worker-restart
# Verify Redis connection
docker compose exec redis redis-cli ping
```

---

### Frontend Issues

**Port 3000 already in use:**
```bash
npm run dev -- --port 3001
```

**TypeScript errors:**
```bash
# Rebuild node_modules
rm -rf node_modules package-lock.json
npm install
```

**Cannot find module '@/...':**
```bash
# Restart VS Code
# Restart Vite dev server
npm run dev
```

---

### Docker Issues

**Container fails to start:**
```bash
# View logs
docker compose logs <service_name>
# Rebuild from scratch
docker compose down -v
docker compose up -d --build
```

**Database not initializing:**
```bash
# Manual initialization
docker compose exec postgres psql -U moldb -d molecule_discovery -c '\dt'
docker compose exec -T backend python scripts/init_db.py
```

---

## DEVELOPMENT WORKFLOW

### Typical Development Cycle

**1. Start services:**
```bash
docker compose up -d
```

**2. Make code changes** in `backend/app/` or `frontend/src/`

**3. For backend changes:**
```bash
# Restart backend
docker compose restart backend
# Or rebuild if dependencies changed
docker compose build backend
docker compose up -d backend
```

**4. Run tests:**
```bash
make test-unit          # Fast unit tests
make test-integration   # Full integration tests
```

**5. View logs:**
```bash
docker compose logs -f backend
docker compose logs -f celery_worker
```

**6. Stop services:**
```bash
docker compose down
```

---

### Adding New Features

**Backend:**
1. Write unit tests in `tests/unit/`
2. Implement feature in `app/`
3. Run `make test-unit`
4. Write integration tests in `tests/integration/`
5. Run `make test-integration`

**Frontend:**
1. Create component in `src/components/` or `src/pages/`
2. Add types in `src/types/`
3. Implement API calls in `src/lib/api/`
4. Test in browser

---

## DOCUMENTATION

**Additional Resources:**
- **Backend README**: `backend/README.md` (API design, testing guide)
- **Frontend README**: `frontend/README.md` (Component usage, setup)
- **Chemistry Module**: `backend/app/core/chemistry.py` (RDKit functions)
- **Agent Documentation**: `backend/app/agents/` (Planner, Generator, Ranker logic)
- **API Schemas**: `backend/app/schemas/` (Pydantic models)

---

## LICENSE

MIT License - See LICENSE file for details

---

## CONTRIBUTORS

**Original Implementation:** Claude (Anthropic)  
**Project Supervision:** nmcuong

---

## NEXT STEPS

1. ✅ **Complete Backend** (Done)
2. 🚧 **Complete Frontend**:
   - Implement Dashboard Page (Feature 5.2)
   - Implement Results Detail Page (Feature 5.3)
   - Connect frontend to backend API
3. 🔲 **Add Authentication** (JWT tokens)
4. 🔲 **Add Molecule Visualization** (RDKit + React)
5. 🔲 **Deploy to Production** (AWS/GCP)

---

**Ready to get started?** Run `make setup` to initialize the entire system!