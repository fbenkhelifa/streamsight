# Portfolio Repository Reorganization Plan

_Last updated: 2026-03-28_

This file defines the target structure for organizing repositories, fixing naming consistency, and deciding what to merge or split.

## 1) Target Naming Convention

Use lowercase kebab-case for all repositories:

- ✅ already good: `streamsight`, `telecom-customer-churn-ml`, `binary-prediction-with-a-rainfall-dataset`
- 🔁 rename recommended:
  - `Store_Management_webApp` → `store-management-webapp`
  - `Predicting_Road_Accident_Risk` → `predicting-road-accident-risk`
  - `AISCHOOL` → `ai-school-website`
  - `-_-` → `ml-notebooks-collection`

## 2) What to Merge

### Merge candidate group: ML notebook repos

Current repos:
- `-_-`
- `binary-prediction-with-a-rainfall-dataset`
- `Predicting_Road_Accident_Risk`
- `telecom-customer-churn-ml`

Recommended end-state:
- Keep **separate specialized repos** for strong portfolio clarity, OR
- Merge all into one umbrella repo: `ml-case-studies` with structure:
  - `projects/credit-scoring/`
  - `projects/twitter-sentiment/`
  - `projects/rainfall-binary-prediction/`
  - `projects/road-accident-risk/`
  - `projects/telecom-churn/`

## 3) What to Split ("Diffuse")

### `AISCHOOL`
- Current issue: source code stored as `AISCHOOL.zip`.
- Action: extract ZIP and commit actual source folders/files.
- Optional split:
  - `ai-school-website` (source code)
  - `ai-school-website-report` (report-only archive) if report evolves separately.

### `-_-`
- Contains mixed notebook themes and datasets.
- Action options:
  - Keep as one curated collection (`ml-notebooks-collection`), or
  - Diffuse notebooks into dedicated project repos for cleaner recruiter-facing narrative.

## 4) Recommended Final Portfolio Layout

### Option A (best for recruiters)
- `streamsight`
- `store-management-webapp`
- `ai-school-website`
- `telecom-customer-churn-ml`
- `predicting-road-accident-risk`
- `binary-prediction-with-a-rainfall-dataset`
- `ml-notebooks-collection` (optional, only for experiments)

### Option B (best for maintenance)
- `streamsight`
- `store-management-webapp`
- `ai-school-website`
- `ml-case-studies` (merged notebooks)

## 5) Safe Migration Sequence

1. Rename repos (GitHub Settings → General → Repository name).
2. Add redirects section in README for renamed repos.
3. If merging notebooks, migrate one project at a time with preserved commit references.
4. Archive superseded repos instead of deleting immediately.
5. After 2–4 weeks, delete only if no broken links remain.

## 6) Status

- [x] README standardization completed across portfolio
- [x] security and auth hardening applied to `Store_Management_webApp`
- [ ] repository renames pending (manual GitHub action)
- [ ] merge/split execution pending final choice between Option A and B
