# Release Guide

Follow these steps each time you release a new version of `amsdal-ml`.

---

## Step 0: Check Working Directory

Before starting, ensure you have a clean working directory:

```bash
git status
```

**If you have uncommitted changes:**
1. Review the changes: `git diff`
2. Decide what to do:
   - **Commit them now** if they should be part of this release:
     ```bash
     git add .
     git commit -m "Your commit message"
     git push origin main
     ```
   - **Stash them** if they're unrelated to this release:
     ```bash
     git stash
     # After release, restore with: git stash pop
     ```
   - **Discard them** if they're not needed:
     ```bash
     git restore .  # Be careful - this cannot be undone!
     ```

---

## Step 1: Update Version Number

Edit `amsdal_ml/__about__.py`:

```python
__version__ = '0.1.4'  # Change to your new version
```

**Version format**: `MAJOR.MINOR.PATCH`
- PATCH: Bug fixes (e.g., `0.1.3` → `0.1.4`)
- MINOR: New features (e.g., `0.1.4` → `0.2.0`)
- MAJOR: Breaking changes (e.g., `0.2.0` → `1.0.0`)

---

## Step 2: Update Changelogs

### 2a. Update `latest-changelogs.md`

Replace entire content with your new release notes:

```markdown
## [v0.1.4](https://pypi.org/project/amsdal_ml/0.1.4/) - 2025-10-15

### Description of changes

- First change
- Second change
- Third change
```

### 2b. Update `change-logs.md`

Prepend the same content to the top of the file (keep existing entries below).

---

## Step 3: Run Quality Checks

```bash
hatch run all
hatch run cov
```

All checks must pass before continuing.

---

## Step 4: Create Release Branch

```bash
git checkout -b release/v0.1.4
```

---

## Step 5: Commit and Push

```bash
git add amsdal_ml/__about__.py latest-changelogs.md change-logs.md
git commit -m "Release v0.1.4"
git push origin release/v0.1.4
```

---

## Step 6: Create Pull Request

1. Go to: https://github.com/amsdal/amsdal_ml/pulls
2. Click "New pull request"
3. Set base: `main` ← compare: `release/v0.1.4`
4. Title: `Release v0.1.4`
5. Add description with changelog content
6. Create and merge the PR

---

## Step 7: Checkout Main and Pull

```bash
git checkout main
git pull origin main
```

---

## Step 8: Create and Push Tag

```bash
git tag -a v0.1.4 -m "Release v0.1.4"
git push origin v0.1.4
```

**Important**: Tag must start with `v` (e.g., `v0.1.4`)

---

## Step 9: Monitor CI/CD

Go to: https://github.com/amsdal/amsdal_ml/actions

Wait for all jobs to complete:
1. ✅ License check
2. ✅ Build
3. ✅ Publish to PyPI
4. ✅ Create GitHub release

---

## Step 10: Verify Release

### Check PyPI
https://pypi.org/project/amsdal-ml/

### Check GitHub Releases
https://github.com/amsdal/amsdal_ml/releases

### Test Installation
```bash
pip install --upgrade amsdal-ml
python -c "import amsdal_ml; print(amsdal_ml.__version__)"
```

---

## Done! ✅

---

## Troubleshooting

**If CI fails:**
1. Check logs at https://github.com/amsdal/amsdal_ml/actions
2. Fix the issue
3. Delete and recreate the tag:
   ```bash
   git tag -d v0.1.4
   git push origin :refs/tags/v0.1.4
   git tag -a v0.1.4 -m "Release v0.1.4"
   git push origin v0.1.4
   ```

**If you need to rollback:**
- Release a new patch version with the fix (recommended)
- Or yank the release from PyPI using `twine`
