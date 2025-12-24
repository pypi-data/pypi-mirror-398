# Releasing py-mcp-installer-service

This document describes the release process for the py-mcp-installer-service library.

## Version Scheme

We use [Semantic Versioning](https://semver.org/):
- **Major** (x.0.0): Breaking API changes
- **Minor** (0.x.0): New features, backward compatible
- **Patch** (0.0.x): Bug fixes, backward compatible

## Release Types

### GitHub Release Only
This library only creates GitHub releases (no PyPI). It's designed to be used as a git submodule.

## Release Process

### Manual Release (Standalone)

1. Update CHANGELOG.md with changes
2. Run release script:
   ```bash
   # Patch release (0.0.x)
   make release-patch

   # Minor release (0.x.0)
   make release-minor

   # Major release (x.0.0)
   make release-major
   ```

### Automatic Release (Parent Repo)

When released as part of mcp-ticketer:

1. Parent detects submodule changes
2. Automatically releases submodule first
3. Updates parent's submodule pointer
4. Continues with parent release

## What Happens

1. Version bumped in VERSION and __init__.py
2. Changes committed
3. Git tag created (v0.0.x)
4. Tag pushed to GitHub
5. GitHub release created

## Version Management

```bash
# Check current version
make version

# Bump version manually
python scripts/manage_version.py bump patch  # or minor/major
```

## Pre-Release Checklist

- [ ] All tests passing (`make test`)
- [ ] Type checks passing (`make type-check`)
- [ ] Linter passing (`make lint`)
- [ ] CHANGELOG.md updated with changes
- [ ] All changes committed
- [ ] Working directory clean (`git status`)

## Post-Release

1. Push changes: `git push origin main`
2. Push tag: `git push origin vX.Y.Z`
3. Verify GitHub release created
4. Update parent repo if needed
