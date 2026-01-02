# Contributing to AgentBill CrewAI Integration

Thank you for considering contributing to the AgentBill CrewAI integration! 🎉

## Development Setup

### Prerequisites
- Python 3.9 or higher
- pip and virtualenv
- Git
- GitHub account
- CrewAI installed

### Getting Started

1. **Fork the repository**
   ```bash
   # Click "Fork" on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/agentbill-crewai.git
   cd agentbill-crewai
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   pip install crewai
   ```

4. **Run tests**
   ```bash
   pytest
   ```

## Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clear, maintainable code
   - Follow PEP 8 style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Run quality checks**
   ```bash
   # Run tests
   pytest
   
   # Run with coverage
   pytest --cov=agentbill_crewai --cov-report=term
   
   # Run linting
   pylint agentbill_crewai
   
   # Format code
   black agentbill_crewai
   isort agentbill_crewai
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```
   
   Use conventional commit messages:
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `test:` Test additions/changes
   - `refactor:` Code refactoring
   - `perf:` Performance improvements
   - `chore:` Maintenance tasks

5. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Standards

### Python Style Guide
- Follow [PEP 8](https://pep8.org/)
- Use type hints for function signatures
- Write docstrings for all public functions and classes
- Keep functions focused and concise
- Use meaningful variable names

### Testing
- Write unit tests for all new functionality
- Aim for >90% code coverage
- Use pytest fixtures for common test setup
- Mock CrewAI dependencies appropriately
- Test edge cases and error conditions

### Documentation
- Add docstrings to all public APIs
- Include usage examples in documentation
- Update README.md for user-facing changes
- Add inline comments for complex logic

## Pull Request Process

1. **Before submitting**
   - [ ] All tests pass locally
   - [ ] Code coverage meets requirements (>90%)
   - [ ] Code follows style guidelines (pylint passes)
   - [ ] Documentation is updated
   - [ ] CHANGELOG.md is updated

2. **PR Description**
   - Clearly describe what changes you made
   - Reference any related issues
   - Include usage examples with CrewAI
   - List any breaking changes

3. **Review Process**
   - Maintainers will review your PR
   - Address any requested changes
   - Once approved, your PR will be merged

## Testing with CrewAI

```python
# Example test with actual CrewAI usage
from crewai import Agent, Task, Crew
from agentbill_crewai import track_crew

def test_with_crewai():
    # Create agents and tasks
    researcher = Agent(role="Researcher", goal="Research topics")
    task = Task(description="Research AI", agent=researcher)
    crew = Crew(agents=[researcher], tasks=[task])
    
    # Track crew
    tracked_crew = track_crew(crew, api_key="test")
    
    # Test your changes
    result = tracked_crew.kickoff()
```

## Adding New Tracking Features

To add new tracking capabilities:

1. **Modify tracker.py**
   ```python
   def track_new_feature(crew, ...):
       """Track new CrewAI feature."""
       # Implementation
   ```

2. **Add tests**
   ```python
   # tests/test_tracker.py
   def test_new_feature():
       # Test implementation
       pass
   ```

3. **Update documentation**
   - Add to README.md
   - Update CHANGELOG.md
   - Add usage examples

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions
- Email: support@agentbill.io

Thank you for contributing! 🚀
