# Building Documentation

This directory contains the Sphinx documentation for BLE2WLED.

## Prerequisites

Install documentation dependencies:

```bash
pip install -e ".[dev]"
```

This installs:
- sphinx
- sphinx-rtd-theme
- myst-parser

## Building HTML

### On Linux/macOS:

```bash
make html
```

### On Windows:

```bash
make.bat html
```

Output: `_build/html/index.html`

## Building PDF

Requires LaTeX/pdflatex:

### On Linux/macOS:

```bash
make latexpdf
```

### On Windows:

```bash
make.bat latexpdf
```

Output: `_build/latex/BLE2WLED.pdf`

## Building Other Formats

**Text:**
```bash
make text
```

**Man pages:**
```bash
make man
```

## Live Preview

Use sphinx-autobuild for live preview during editing:

```bash
pip install sphinx-autobuild
sphinx-autobuild source _build/html
```

Then open http://localhost:8000 in your browser.

## Structure

```
docs/
├── source/
│   ├── conf.py              # Sphinx configuration
│   ├── index.rst            # Main index
│   ├── introduction.rst      # Project introduction
│   ├── installation.rst      # Installation guide
│   ├── quickstart.rst        # Quick start guide
│   ├── license.rst           # License
│   ├── guides/
│   │   ├── configuration.rst         # Configuration guide
│   │   ├── cli_simulator.rst         # CLI simulator guide
│   │   ├── mqtt_authentication.rst   # MQTT auth guide
│   │   └── http_retry_logic.rst      # HTTP retry guide
│   └── api/
│       ├── modules.rst              # API overview
│       ├── config.rst               # Config module
│       ├── states.rst               # States module
│       ├── colors.rst               # Colors module
│       ├── animation.rst            # Animation module
│       ├── wled.rst                 # WLED module
│       ├── mqtt.rst                 # MQTT module
│       └── simulator.rst            # Simulator module
├── Makefile                 # Build script (Linux/macOS)
├── make.bat                 # Build script (Windows)
└── _build/                  # Build output (generated)
```

## Deploying to GitHub Pages

### Automatic (via GitHub Actions)

See `.github/workflows/docs.yml` for automatic deployment on each push.

### Manual

Build HTML and push to `gh-pages` branch:

```bash
make clean html
git checkout gh-pages
cp -r _build/html/* .
git add .
git commit -m "Update documentation"
git push origin gh-pages
```

## Troubleshooting

**Module not found errors:**

Ensure BLE2WLED is installed:

```bash
pip install -e ..
```

**autodoc not finding modules:**

The `conf.py` adds `src/` to path. Verify it's correct for your setup.

**ANSI color issues in terminal blocks:**

These are intentional (showing terminal output). Update `conf.py` if needed.

## Resources

- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [Read the Docs Theme](https://sphinx-rtd-theme.readthedocs.io/)
- [MyST Parser](https://myst-parser.readthedocs.io/)
