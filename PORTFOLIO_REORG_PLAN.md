# Portfolio Repository Reorganization Plan

_Last updated: 2026-03-28_

This file defines the target structure for organizing repositories, fixing naming consistency, and deciding what to merge or split.

## 1) Naming Convention (Current State)

All repositories now follow lowercase kebab-case where applicable.

Current portfolio repositories:

- `streamsight`
- `store-management-webapp`
- `ai-school-website`
- `predicting-road-accident-risk`
- `binary-prediction-with-a-rainfall-dataset`
- `telecom-customer-churn-ml`
- `ml-notebooks-collection`

Rename history (completed):

- `Store_Management_webApp` → `store-management-webapp`
- `Predicting_Road_Accident_Risk` → `predicting-road-accident-risk`
- `AISCHOOL` → `ai-school-website`
- `-_-` → `ml-notebooks-collection`

## 2) What to Merge (Optional)

### Merge candidate group: ML notebook repos

Current repos:
- `ml-notebooks-collection`
- `binary-prediction-with-a-rainfall-dataset`
- `predicting-road-accident-risk`
- `telecom-customer-churn-ml`

Recommended end-state options:
- Keep **separate specialized repos** for stronger portfolio clarity, OR
- Merge all into one umbrella repo: `ml-case-studies` with structure:
  - `projects/credit-scoring/`
  - `projects/twitter-sentiment/`
  - `projects/rainfall-binary-prediction/`
  - `projects/road-accident-risk/`
  - `projects/telecom-churn/`

## 3) What to Split ("Diffuse")

### `ai-school-website`
- Current issue: source code is still stored as `AISCHOOL.zip`.
- Action: extract ZIP and commit actual source folders/files.
- Optional split:
  - `ai-school-website` (source code)
  - `ai-school-website-report` (report-only archive) if report evolves separately.

### `ml-notebooks-collection`
- Contains mixed notebook themes and datasets.
- Action options:
  - Keep as one curated collection, or
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

## 5) Safe Migration Sequence (Remaining)

1. Add redirects section in README for renamed repos (optional but useful).
2. If merging notebooks, migrate one project at a time with preserved commit references.
3. Archive superseded repos instead of deleting immediately.
4. After 2–4 weeks, delete only if no broken links remain.

## 6) Status

- [x] README standardization completed across portfolio
- [x] security and auth hardening applied to `store-management-webapp`
- [x] repository renames completed
- [ ] merge/split execution pending final choice between Option A and Option B
