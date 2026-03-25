# Contributing to AdaptiveSec

Thanks for contributing. Follow this guide before writing a single line of code — it keeps the repo clean and your work reviewable.

---

## Table of Contents

- [Branch Structure](#branch-structure)
- [First-Time Setup](#first-time-setup)
- [Starting a New Story](#starting-a-new-story)
- [Branch Naming](#branch-naming)
- [Doing the Work](#doing-the-work)
- [Opening a Pull Request](#opening-a-pull-request)
- [After Your PR is Merged](#after-your-pr-is-merged)
- [Commit Message Style](#commit-message-style)
- [Code Standards](#code-standards)
- [Golden Rules](#golden-rules)

---

## Branch Structure

The repo uses three levels of branches:

| Branch | Purpose |
| --- | --- |
| `main` | Production branch. Only merged into at the end of the week after everything is tested. **Never commit directly here.** |
| `straightoprod` | Shared working branch. All feature branches merge into here first. |
| `{issue}-{story-id}-{slug}` | Feature branches — one per user story. This is where you do your work. |

---

## First-Time Setup

### Clone the repo

```bash
cd Desktop
git clone https://github.com/ForhaadM/AdaptiveSec.git
cd AdaptiveSec
```

### Get the `.env` file

The `.env` file is **never committed to GitHub**. Place the file in the root `AdaptiveSec/` directory. Without it the backend will not run.

### Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
cd ..
```

### Install frontend dependencies

```bash
cd dashboard
npm install
cd ..
```

### Install all other dependencies using AdaptiveSec/requirements.txt

---

## Starting a New Story

Always do these steps before creating a branch. Never branch off `main` or another feature branch.

```bash
git checkout straightoprod
git pull origin straightoprod
git checkout -b {your-branch-name}
```

---

## Branch Naming

Use the exact names below — they match the GitHub issue numbers:

| Issue | Story ID | Branch Name |
| --- | --- | --- |
| #10 | W1-001 | `10-w1-001-repo-setup` |
| #11 | W1-002 | `11-w1-002-secrets-management` |
| #12 | W1-003 | `12-w1-003-jwt-auth` |
| #13 | W1-004 | `13-w1-004-chrome-extension-scaffold` |
| #14 | W1-005 | `14-w1-005-download-datasets` |
| #15 | W1-006 | `15-w1-006-redis-setup` |
| #16 | W1-007 | `16-w1-007-rabbitmq-setup` |
| #17 | W1-008 | `17-w1-008-dashboard-skeleton` |
| #18 | W1-009 | `18-w1-009-contributing-readme` |
| #19 | W1-010 | `19-w1-010-dataset-cleaning` |
| #20 | W1-011 | `20-w1-011-baseline-model` |

---

## Doing the Work

Work inside your feature branch. Commit often — don't wait until everything is done.

```bash
git add {specific-files}
git commit -m "W1-00X: describe what you did"
git push origin {your-branch-name}
```

Prefer staging specific files over `git add .` to avoid accidentally committing secrets or build artifacts.

---

## Opening a Pull Request

When your story is complete and tested:

1. Go to [github.com/ForhaadM/AdaptiveSec](https://github.com/ForhaadM/AdaptiveSec)
2. Click **Pull requests** → **New pull request**
3. Set **base** to: `straightoprod`
4. Set **compare** to: your feature branch
5. Title: use your story ID — e.g. `W1-003: Implement JWT auth layer`
6. Description: include `closes #[issue number]` to auto-close the issue on merge
7. Get at least one teammate to review before merging

---

## After Your PR is Merged

Clean up your local machine:

```bash
git checkout straightoprod
git pull origin straightoprod
git branch -d {your-branch-name}
```

You can also delete the branch on GitHub: go to the repo → **Branches** → click the trash icon next to your merged branch.

---

## Commit Message Style

Commit messages must include the story ID and a plain description of what changed.

```text
Good: W1-003: add JWT middleware to protected routes
Good: W1-005: download Kaggle phishing dataset and place in data/raw/
Bad:  fix stuff
Bad:  updates
Bad:  wip
```

If a commit closes a GitHub issue, include it in the message:

```text
W1-005: download and organize training datasets - closes #14
```

---

## Code Standards

### Python (backend / ML pipeline)

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints on all function signatures
- Keep functions focused — one responsibility per function
- Do not commit unused imports or debug `print()` statements
- All new backend modules go under `backend/ml_pipeline/` or `backend/`

### JavaScript / React (dashboard)

- Follow the existing ESLint config (`dashboard/eslint.config.js`)
- Use functional components and hooks — no class components
- Keep components small and single-purpose
- Do not commit `console.log` statements

### Chrome Extension

- All heavy computation (TensorFlow.js inference) goes in `offscreen.js` — never block the service worker
- Keep `background.js` as a thin event router only
- Stay within Manifest V3 constraints

### General

- Do not commit your `.env` file under any circumstances
- Do not commit `node_modules/`, `__pycache__/`, or build artifacts — these are in `.gitignore`
- Do not mix work from multiple stories in one branch

---

## Golden Rules

- **NEVER** commit directly to `main` or `straightoprod`
- **NEVER** branch off another feature branch — always branch off `straightoprod`
- **ALWAYS** pull from `straightoprod` before creating a new branch
- **ALWAYS** include `closes #[issue number]` in your PR description
- **NEVER** commit your `.env` file
- **One branch = one story** — do not mix work from multiple stories in one branch

---
