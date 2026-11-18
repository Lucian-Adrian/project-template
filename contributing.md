# Contributing

Thank you for your interest in contributing! Please follow these guidelines:

## How to Contribute

1. Fork the repository
2. Create a feature branch (git checkout -b feature/amazing-feature)
3. Commit your changes (git commit -m 'Add amazing feature')
4. Push to the branch (git push origin feature/amazing-feature)
5. Open a Pull Request

## Code Style

- Follow the existing code style
- Write clear, concise commit messages
- Add tests for new features
- Update documentation as needed

## Running tests

From the repository root, run:

```bash
python3 -m unittest discover -s tests -v
```

The tests require Python 3, Bash and Git, with no third-party Python packages. They run disposable copies of the Bash deploy script in temporary directories to check scaffolding, overwrite choices, symlink protection and generated ignore rules.

## Reporting Issues

Please use the GitHub issue tracker to report bugs or request features.
