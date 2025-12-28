# better_coverage

**better_coverage** is a pytest plugin that displays pytest-cov coverage results in Jest/Istanbul's console format with a directory tree structure.

##### Why?

Using better_coverage lets you see coverage in Jest's familiar table format right in your terminal. The reporter organizes files into a directory tree, shows uncovered line ranges (e.g., `5-12,18`), and applies the same color coding as Jest so your Python coverage reports look exactly like your JavaScript ones.

## Usage

Add the package to your project:

```bash
pip install better-coverage
```

Then run your tests with coverage:

```bash
pytest --cov=your_package --cov-report=xml
```

The Jest-style coverage table will automatically appear at the end of your test run.

#### Options

The plugin automatically detects terminal width and formats output accordingly. Coverage data is read from pytest-cov, so use standard pytest-cov options:

```bash
pytest --cov=your_package --cov-report=xml --cov-branch
```

Use `--cov-branch` to enable branch coverage reporting.

## Contributing

Contributions are welcome! If you find a bug or have suggestions for improvement, please open an issue or submit a pull request.

## License

Apache License 2.0 © 2025 Mridang Agarwalla
