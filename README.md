# AI-Assisted Smart Compiler

An interactive AI-powered compiler with machine learning for statement classification, semantic analysis, and intelligent error feedback via Gemini LLM. Features a web UI for pipeline visualization and phase-by-phase outputs.

## Features

- **Lexical Analysis**: Tokenizes source code into identifiers, keywords, operators, etc.
- **Syntax Analysis**: Parses tokens into an Abstract Syntax Tree (AST).
- **ML Classification**: Uses TF-IDF + RandomForest to classify statement types (96% accuracy).
- **Semantic Analysis**: Checks symbol tables, scopes, and types for errors.
- **LLM Feedback**: Provides concise error explanations and fix suggestions using Google Gemini.
- **Web UI**: React-based interface to run pipelines, view outputs, and learn about phases.
- **Latency Comparison**: Compares ML-assisted vs. traditional compilation times.

## Project Structure

- `run_compiler.py`: Main pipeline script (CLI).
- `backend/`: FastAPI server for API endpoints.
- `frontend/`: React + Vite web UI.
- `src/`: Core compiler (lexer, parser, semantic analyzer).
- `ml/`: ML models, data, and scripts.
- `examples/`: Sample source files for testing.
- `tests/`: Unit tests.
- `requirements.txt`: Python dependencies.
- `frontend/package.json`: Node.js dependencies.

## Prerequisites

- Python 3.10+
- Node.js 18+
- Virtual environment (recommended)

## Installation & Setup

1. **Clone the repository** (if not already):
   ```sh
   git clone <repo-url>
   cd AI_Assisted_Smart_Compiler
   ```

2. **Backend Setup**:
   ```sh
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. **Frontend Setup**:
   ```sh
   cd frontend
   npm install
   cd ..
   ```

4. **Environment Variables**:
   - Copy `.env.example` to `.env` (if exists) or create `.env`.
   - Add your Gemini API key: `GEMINI_API_KEYS=your_key_here`
   - Set model: `GEMINI_MODEL=gemini-2.5-flash`

## How to Run

### CLI Mode
```sh
python run_compiler.py examples/simple_test.txt
```
Generates `output.json` with predictions and logs.

### Web UI Mode
1. **Start Backend**:
   ```sh
   python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
   ```

2. **Start Frontend** (in another terminal):
   ```sh
   cd frontend
   npm run dev -- --host 127.0.0.1 --port 5173
   ```

3. Open `http://127.0.0.1:5173` in your browser.

Select a file, run the pipeline, and view outputs for each phase, including LLM feedback on errors.

## API Endpoints

- `GET /api/files`: List example files.
- `POST /api/run`: Run pipeline on a file, returns outputs.

## Current Progress

- [X] Lexical Analysis
- [X] Syntax Analysis (Parser and AST)
- [X] ML Statement Classification (TF-IDF + RandomForest, 96% accuracy)
- [X] Semantic Analysis (symbol table, scope, type checks)
- [X] LLM Integration (Gemini for error feedback)
- [X] Web UI (React, phase guides, latency comparison)
- [ ] Code Generation (Future)

## Contributing

- Run tests: `python -m pytest`
- Train ML model: See `ml/scripts/train_model.py`
- Add examples in `examples/`

## License

MIT License.
