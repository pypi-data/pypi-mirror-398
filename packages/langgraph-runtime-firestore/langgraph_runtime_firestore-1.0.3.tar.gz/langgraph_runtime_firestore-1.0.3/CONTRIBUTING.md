# Contributing to LangGraph Runtime Firestore

Thank you for your interest in contributing to LangGraph Runtime Firestore! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/MarcoFurrer/langgraph_runtime_firestore.git
   cd langgraph_runtime_firestore
   ```

2. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

3. **Set up Firestore credentials**
   
   You'll need a Google Cloud Firestore project:
   - Create a service account in your Google Cloud project
   - Download the credentials JSON file
   - Set environment variables:
     ```bash
     export FIRESTORE_CREDENTIALS_PATH=/path/to/credentials.json
     export FIRESTORE_PROJECT_ID=your-project-id
     ```

## Code Style

We use `ruff` for linting and formatting. Before submitting a PR:

```bash
# Check code style
make lint

# Auto-fix issues
make format
```

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clear, concise commit messages
   - Keep changes focused and atomic
   - Add or update documentation as needed

3. **Test your changes**
   - Ensure all existing functionality still works
   - Add tests for new features if applicable

4. **Run linting**
   ```bash
   make lint
   ```

5. **Submit a pull request**
   - Provide a clear description of the changes
   - Reference any related issues
   - Wait for review and address feedback

## Code Organization

- `checkpoint.py` - Checkpoint management for state persistence
- `database.py` - Firestore connection and initialization
- `ops.py` - Core operations (Threads, Runs, Assistants)
- `store.py` - Store implementation for LangGraph
- `queue.py` - Background task queue management
- `serialize.py` - Serialization/deserialization for Firestore
- `firestore_stream.py` - Stream management for real-time updates

## Reporting Issues

When reporting issues, please include:
- A clear description of the problem
- Steps to reproduce
- Expected vs. actual behavior
- Environment details (Python version, Firestore SDK version, etc.)

## Questions?

Feel free to open an issue for questions or discussions about the project.
