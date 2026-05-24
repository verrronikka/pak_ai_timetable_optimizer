# Release runbook

## Purpose

Use this checklist when preparing a release or when validating a candidate branch before merge into `main`.

## Build and verify locally

1. Install dependencies for backend and frontend.
2. Run the backend API and solver checks:

```bash
cd backend
python -m pytest tests/test_api.py tests/test_config.py -q
python -m pytest tests/test_performance_regression.py -q
```

3. Run the frontend smoke checks:

```bash
cd frontend
npm ci
npx playwright test --config=playwright.config.js --reporter=list
```

4. Run the solver from the repository root if you need to reproduce output artifacts:

```bash
cd dev_alg
python test.py
```

## Reproduce the environment

- Backend server: `python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000`
- Frontend static server: `python -m http.server 5500`
- Playwright smoke config: `frontend/playwright.config.js`
- CI workflow: `.github/workflows/ci-smoke.yml`
- Scheduled benchmark workflow: `.github/workflows/performance-benchmarks.yml`

## Required artifacts

- `reports/generated/performance_regression_latest.json`
- Playwright report under `frontend/playwright-report/`
- Solver outputs in `dev_alg/artifacts/`

## Rollback

If the release candidate is incorrect, revert the release commit or the smallest commit group that introduced the issue.

Recommended order:

1. Revert the last frontend or CI commit if the failure is limited to smoke coverage or workflow behavior.
2. Revert the backend durability commit group if job execution or API status handling regressed.
3. Re-run the backend and frontend checks above after the revert.

## Release gates

Do not merge until the following are true:

- Backend API and config tests pass.
- Performance regression report is generated and uploaded by CI.
- Frontend opens without browser console errors.
- Playwright smoke passes on the current branch.
- The release checklist in `docs/release-checklist.md` is fully green.
