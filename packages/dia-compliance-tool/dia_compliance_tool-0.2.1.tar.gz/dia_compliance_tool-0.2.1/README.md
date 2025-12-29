# Digital-India-Act-Compliance-Checker-Tool

## Setup

This package requires API keys to be set as environment variables.

#### For MAC and Linux
```bash
export GROQ_API_KEY=your_groq_key
```

#### For Windows
```bash
$env:GROQ_API_KEY=your_groq_key
```

#### Commands for creating PyPI package

```bash
Remove-Item -Recurse -Force dist
```

```bash
python -m build
```

```bash
twine upload dist/*
```

#### PyPI installable package

```bash
pip install dia-compliance-tool==0.2.0
```