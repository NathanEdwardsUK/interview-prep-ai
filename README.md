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

4. **Start PostgreSQL**

   ```bash
   docker-compose up -d
   ```

5. **Configure environment variables**

   Copy `.env.example` files and fill in your values:
   - `backend/.env.example` → `backend/.env`
   - `frontend/.env.example` → `frontend/.env.local`

   Required variables:
   - Database URL
   - Clerk keys (publishable key for frontend, secret key for backend)
   - LLM API keys (OpenAI or Anthropic)

6. **Run database migrations**

   ```bash
   cd backend
   alembic upgrade head
   ```

7. **Start the development servers**

   Backend (from `backend/` directory):

   ```bash
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
