# Contributing to Titans-MIRAS

Thank you for your interest in contributing to Titans-MIRAS! This document provides guidelines for contributing to the project.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/jonlukewatts/titans-miras.git
cd titans-miras
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e ".[dev,test]"
```

## Code Style

- Use [Black](https://github.com/psf/black) for formatting (line length: 120)
- Follow PEP 8 guidelines
- Use type hints for function signatures
- Write docstrings for public functions and classes

Format your code before committing:
```bash
black titans_miras/
```

## Testing

Run tests with pytest:
```bash
pytest tests/
```

## Pull Request Process

1. Fork the repository and create a new branch for your feature/fix
2. Make your changes with clear, descriptive commit messages
3. Add tests for new functionality
4. Ensure all tests pass
5. Update documentation if needed
6. Submit a pull request with a clear description of changes

## Reporting Issues

When reporting issues, please include:
- Python version
- PyTorch version
- Operating system
- Minimal code example to reproduce the issue
- Full error traceback

## Einops Notation

When working with tensor operations, follow the established notation:

| Symbol | Meaning |
|--------|---------|
| `b` | batch |
| `h` | heads |
| `bh` | batch and heads |
| `n` | sequence |
| `d` | feature dimension |
| `c` | intra-chunk |
| `w` | memory network weights |
| `o` | momentum orders |
| `u` | key/value updates per token |

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

