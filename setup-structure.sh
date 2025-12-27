#!/bin/bash

echo "🚀 Creating project structure..."

# Create main directories
mkdir -p backend/{app/{api,agents,chemistry,models,db,tasks,core},tests/{unit,integration,e2e},alembic/versions,scripts,data/{exports,logs}}
mkdir -p frontend/{src/{assets/styles,components/{layout,runs,molecules,traces,forms,ui},pages,lib,types},public}
mkdir -p docker docs/{api,architecture,setup} .github/workflows

echo "📁 Creating backend files..."

# Backend __init__.py files
touch backend/app/__init__.py
touch backend/app/api/__init__.py
touch backend/app/agents/__init__.py
touch backend/app/chemistry/__init__.py
touch backend/app/models/__init__.py
touch backend/app/db/__init__.py
touch backend/app/tasks/__init__.py
touch backend/app/core/__init__.py
touch backend/tests/__init__.py

# Backend main files
touch backend/app/{main.py,celery_app.py,config.py}
touch backend/app/api/{deps.py,runs.py,molecules.py,traces.py}
touch backend/app/agents/{base.py,planner.py,generator.py,ranker.py}
touch backend/app/chemistry/{engine.py,properties.py,screening.py,transforms.py}
touch backend/app/models/{run.py,molecule.py,trace.py,user.py}
touch backend/app/db/{base.py,session.py,models.py}
touch backend/app/tasks/{orchestrator.py,agent_tasks.py,export_tasks.py}
touch backend/app/core/{security.py,logging.py,exceptions.py}

# Backend config files
touch backend/{requirements.txt,requirements-dev.txt,pytest.ini,alembic.ini,.env.example}
touch backend/tests/conftest.py
touch backend/scripts/{init_db.py,seed_data.py}

echo "📁 Creating frontend files..."

# Frontend main files
touch frontend/src/{App.tsx,main.tsx,vite-env.d.ts}
touch frontend/src/assets/styles/globals.css
touch frontend/src/components/layout/{Layout.tsx,Navbar.tsx}
touch frontend/src/components/runs/{RunCard.tsx,RunList.tsx,RunStatusBadge.tsx}
touch frontend/src/components/molecules/{MoleculeTable.tsx,PropertyChart.tsx}
touch frontend/src/components/traces/{TraceViewer.tsx,TraceTimeline.tsx}
touch frontend/src/components/forms/{RunConfigForm.tsx,SmilesInput.tsx}
touch frontend/src/pages/{StartRunPage.tsx,DashboardPage.tsx,ResultsPage.tsx}
touch frontend/src/lib/{api.ts,queries.ts,utils.ts}
touch frontend/src/types/{run.ts,molecule.ts,trace.ts}

# Frontend config files
touch frontend/{package.json,tsconfig.json,tsconfig.node.json,vite.config.ts,tailwind.config.js,postcss.config.js,components.json,.env.example,index.html}

echo "📁 Creating root files..."

# Docker files
touch docker/{backend.Dockerfile,frontend.Dockerfile,nginx.conf}
touch docker-compose.yml docker-compose.prod.yml

# CI/CD
touch .github/workflows/{backend-ci.yml,frontend-ci.yml,deploy.yml}

# Root files
touch {Makefile,.gitignore,README.md,LICENSE}

# Documentation
touch docs/setup/{backend-setup.md,frontend-setup.md}
touch docs/architecture/system-design.md
touch docs/user-guide.md

echo "✅ Project structure created successfully!"
echo ""
echo "Next steps:"
echo "1. Run: chmod +x setup-structure.sh"
echo "2. Run: ./setup-structure.sh"
echo "3. Continue with STEP 3 in the guide"
