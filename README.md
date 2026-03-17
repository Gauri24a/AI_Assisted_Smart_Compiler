# AI-Assisted Smart Compiler

This project is an AI-assisted compiler that uses machine learning to understand programmer intent and provide smarter error messages.

## Project Structure

- `run_compiler.py`: The main entry point to run the compiler.
- `output.json`: The default output file for predictions.
- `src/`: Contains the core compiler components (lexer, parser, AST nodes).
- `tests/`: Contains tests for the compiler components.
- `ml/`: Contains all machine learning related files.
  - `scripts/`: Scripts for training the model and making predictions.
  - `data/`: The datasets used for training.
- `examples/`: Contains example source code files.
- `requirements.txt`: The Python dependencies for this project.
- `README.md`: This file.

## How to Run

1.  **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

2.  **Activate the virtual environment:**
    ```sh
    d:\AI_Assisted_Smart_Compiler\.venv\Scripts\Activate.ps1
    ```

3.  **Run the compiler:**
    ```sh
    python run_compiler.py examples/simple_test.txt
    ```

    This will generate an `output.json` file with the statement predictions.

## Current Progress

- [X] Lexical Analysis
- [X] Syntax Analysis (Parser and AST)
- [X] AI Statement Classification
- [ ] Semantic Analysis (In Progress)
- [ ] Code Generation (Planned)
