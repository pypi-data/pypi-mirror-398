# Sphinx Documentation - Quick Reference

## 📚 Documentation Location

**Web:** `docs/_build/html/index.html` (after building)

**Source:** `docs/source/` directory

## 🚀 Quick Start

### Build Documentation
```bash
cd docs
pip install -e ".[dev]"
make html                    # Linux/macOS
# OR
make.bat html                # Windows
```

### View Documentation
Open `docs/_build/html/index.html` in your browser

### Live Preview
```bash
pip install sphinx-autobuild
sphinx-autobuild docs/source docs/_build/html
# Then open http://localhost:8000
```

## 📖 Documentation Pages

### Getting Started
- **introduction.rst** - Project overview and architecture
- **installation.rst** - Installation guide with troubleshooting
- **quickstart.rst** - 5-minute quick start

### User Guides
- **guides/configuration.rst** - Complete configuration reference
- **guides/cli_simulator.rst** - CLI simulator usage (all options)
- **guides/mqtt_authentication.rst** - MQTT auth setup
- **guides/http_retry_logic.rst** - HTTP retry behavior

### API Reference
- **api/modules.rst** - Overview of all modules
- **api/config.rst** - Configuration management API
- **api/states.rst** - Beacon state tracking API
- **api/colors.rst** - Color calculations API
- **api/animation.rst** - Animation loop API
- **api/wled.rst** - WLED communication API
- **api/mqtt.rst** - MQTT listener API
- **api/simulator.rst** - Simulator API

## 🔧 Building & Deployment

### Local Build
```bash
cd docs
make clean html
```

### GitHub Pages Deployment
Automatic via `.github/workflows/docs.yml`:
- Builds on push to main/develop
- Deploys to gh-pages branch
- Access at: https://username.github.io/ble2wled

### Custom Domain (Optional)
1. Update `.github/workflows/docs.yml` line with `cname:`
2. Create `CNAME` file with your domain
3. Configure DNS records

## 📝 Content Statistics

| Section | Files | Pages | Code Examples |
|---------|-------|-------|----------------|
| Getting Started | 3 | 3 | 15+ |
| User Guides | 4 | ~30 | 50+ |
| API Reference | 8 | ~18 | 60+ |
| **Total** | **15** | **~51** | **125+** |

## ✨ Features

✅ Auto-generated API documentation from docstrings
✅ Professional Read the Docs theme
✅ Full-text search
✅ Cross-referenced documentation
✅ Mobile-responsive design
✅ Dark mode support
✅ GitHub Pages deployment
✅ Automated CI/CD builds

## 🔗 Key Sections

### Configuration
Everything about .env files, environment variables, properties, validation

### CLI Simulator
All options, usage examples, MQTT connection, performance tips

### MQTT Authentication
Setup, .env configuration, CLI usage, security best practices

### HTTP Retry Logic
How retries work, configuration, typical scenarios, optimization

### API Documentation
All modules, functions, classes, with examples and cross-references

## 📚 Files to Consolidate (Optional)

These can be deleted from root directory (content now in Sphinx docs):
- `README.md` (merge relevant parts)
- `SIMULATOR.md`
- `SIMULATOR_GUIDE.md`
- `MQTT_AUTHENTICATION.md`
- `HTTP_RETRY_LOGIC.md`
- All `*_SUMMARY.md` and `*_IMPLEMENTATION.md` files

## 🎯 Next Steps

1. Build locally: `make html`
2. Verify: Open `docs/_build/html/index.html`
3. Push to GitHub
4. Enable GitHub Pages (Settings → Pages → gh-pages branch)
5. Update root README.md to link to documentation

## 💡 Tips

- Edit `.rst` files in `docs/source/`
- Python docstrings auto-update API docs
- Run `make clean html` to rebuild everything
- Check for warnings in build output
- Use `sphinx-autobuild` for live preview

## 📞 Support

- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [Read the Docs Guide](https://docs.readthedocs.io/)
- [reStructuredText Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)

---

**Created:** December 20, 2025
**Status:** ✅ Complete and Ready for Deployment
