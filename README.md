# AI Interview Prep Platform

An AI-powered coaching platform for personalized interview preparation with structured practice sessions and real-time feedback.

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Next.js (TypeScript)
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Authentication**: Clerk
- **LLM**: OpenAI / Anthropic (configurable)

## Project Structure

```
interview-prep-ai/
├── backend/          # FastAPI backend
├── frontend/         # Next.js frontend
├── docs/             # Documentation
└── docker-compose.yml # Local PostgreSQL
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Clerk account (for authentication)

### Setup

1. **Clone and navigate to the project**

   ```bash
   cd interview-prep-ai
   ```

2. **Set up backend**

   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up frontend**

   ```bash
   cd frontend
   npm install
   ```

4. **Configure environment variables**

   Environment files have been created from `.env.example`:
   - `backend/.env` - Backend environment variables
   - `frontend/.env.local` - Frontend environment variables

   Update these files with your actual values:
   - Database URL (defaults to `postgresql://postgres:postgres@localhost:5432/interview_prep`)
   - Clerk keys (get from [Clerk Dashboard](https://dashboard.clerk.com)):
     - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` for frontend
     - `CLERK_SECRET_KEY` for backend
   - LLM API keys:
     - `OPENAI_API_KEY` if using OpenAI
     - `ANTHROPIC_API_KEY` if using Anthropic

5. **Start PostgreSQL**

   ```bash
   docker compose up -d
   ```

   Verify it's running:

   ```bash
   docker compose ps
   ```

6. **Run database migrations**

   ```bash
   cd backend
   source venv/bin/activate  # Activate virtual environment if not already active
   alembic upgrade head
   ```

   This will create all database tables. The initial migration (`001_initial_migration.py`) has been created.

7. **Start the development servers**

   Backend (from `backend/` directory):

   ```bash
   source venv/bin/activate  # Activate virtual environment
   uvicorn app.main:app --reload
   ```

   Frontend (from `frontend/` directory):

   ```bash
   npm run dev
   ```

8. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## Development

### Backend

- FastAPI automatically reloads on code changes
- API documentation available at `/docs` (Swagger UI)
- Alternative docs at `/redoc`

### Frontend

- Next.js hot reloads on code changes
- TypeScript for type safety
- Tailwind CSS for styling

### Database Migrations

Create a new migration:

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Environment Variables

See `.env.example` files in `backend/` and `frontend/` directories for required variables.

## License

MIT
