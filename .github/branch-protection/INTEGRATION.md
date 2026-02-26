# 🔗 Integration: Workflows + Branch Protection Rules

This document explains how **CI/CD workflows** are integrated with **Branch Protection Rules** to create a secure and automated pipeline.

## 🏗️ General Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  GitHub Pull Request / Push                                     │
│  (Created on feature branch or merge to develop/master)         │
└────────────┬────────────────────────────────┬──────────────────┘
             │                                │
             ▼                                ▼
    ┌──────────────────┐          ┌─────────────────────┐
    │ Branch Validation│          │  Branch Protection  │
    │  Workflow        │          │  Rules              │
    │                  │          │                     │
    │ • Names Check    │          │ • Validates refs    │
    │ • Git Flow Rules │          │ • Blocks invalid    │
    └────────┬─────────┘          │   branch patterns   │
             │                    └──────────┬──────────┘
             ▼                               │
    ┌──────────────────┐                    │
    │ CI Workflow      │                    │
    │                  │                    │
    │ • Lint           │                    │
    │ • Type-Check     │ ◄──────────────────┘
    │ • Test           │  (Requires all)
    │ • Build          │
    └────────┬─────────┘
             │
             ▼
    PR Status ✅ PASSED
             │
             ▼
    ┌──────────────────┐
    │ Merge Button     │
    │ Enabled          │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ If master:       │
    │ Deploy Workflow  │
    │ Runs (validate + │
    │ deploy)          │
    └──────────────────┘
```

---

## 📊 Flow by Branch

### 👉 Creating PR to `develop`

```
feature/* branch
    ▼
git push origin feature/new-feature
    ▼
GitHub detects PR trigger
    ▼
Branch Validation runs:
  ✓ check-source-branch-develop (passes if valid types)
    
CI Workflow runs (parallel):
  ✓ lint (ESLint + Prettier)
  ✓ type-check (TypeScript -- NEW)
  ✓ test (Jest)
  ✓ build (Compilation)
    ▼
Branch Protection Rules verify:
  ✓ All status checks passed?
  ✓ Branch naming is valid?
    ▼
IF PASSED:
  ✅ "Merge pull request" button enabled
  
IF FAILED:
  ❌ Merge blocked
  ❌ Must fix and push again
```

### 👉 Creating PR to `master`

```
develop or hotfix/* branch
    ▼
git push to create PR on master
    ▼
Branch Validation runs:
  ✓ check-source-branch-master (rejects if not develop/hotfix/*)
    
CI Workflow runs (on develop before the PR):
  ✓ lint
  ✓ type-check
  ✓ test
  ✓ build
    ▼
Branch Protection Rules verify:
  ✓ All status checks passed?
  ✓ Require 1 approval? ✅ YES (master has requirement)
  ✓ Rebase up-to-date? (strict mode)
  ✓ All discussions resolved?
    ▼
IF PASSED:
  ✅ Merge enabled (after approval)
  
IF FAILED:
  ❌ Merge blocked until fixed
```

### 👉 Merge to `master` → Deploy

```
PR Merged to master
    ▼
git push origin master (automatic)
    ▼
Deploy Workflow triggers:
  
  Job: validate
    ✓ Runs COMPLETE CI pipeline
    ✓ lint, type-check, test, build
    ▼
    
    IF PASSED:
      output: should-deploy=true
    
    IF FAILED:
      ❌ Deploy blocked
      ❌ Validates code integrity
    
  Job: deploy (conditional to validate passing)
    ✓ Prepares credentials
    ✓ Deploy to Firebase
    ✓ Validates post-deploy
```

---

## 🔄 Mapping: Workflows ↔ Status Checks ↔ Rules

| Workflow | Job | Status Check | Reference in Rules |
|----------|-----|--------------|--------------|
| **branch-enforcer.yml** | check-source-branch-develop | "Branch Validation / check-source-branch-develop" | develop.json |
| **branch-enforcer.yml** | check-source-branch-master | "Branch Validation / check-source-branch-master" | master.json |
| **ci.yml** | lint | "CI / lint" | develop.json, master.json |
| **ci.yml** | type-check | "CI / type-check" | develop.json, master.json |
| **ci.yml** | test | "CI / test" | develop.json, master.json |
| **ci.yml** | build | "CI / build" | develop.json, master.json |

### ⚠️ Important
**The job name in the YAML MUST match the `context` in the JSON!**

Example:
```yaml
# ci.yml
jobs:
  type-check:    # ← Job name
    run: npx tsc --noEmit
```

```json
// develop.json
"required_status_checks": [
  {
    "context": "CI / type-check"  # ← Status Check name
  }
]
```

---

## 🔐 Protection in Layers

### Layer 1: Branch Naming (workflow)
```
Branch Validation Workflow
├─ Validates names: feat/*, fix/*, etc
└─ Blocks invalids: blah, wip/stuff, etc
```

### Layer 2: Quality Checks (workflow)
```
CI Workflow
├─ Lint: Code follows standards
├─ Type-Check: No TypeScript errors
├─ Test: Logic works
└─ Build: Compiles correctly
```

### Layer 3: Branch Rules (GitHub)
```
Branch Protection Rules
├─ Blocks merge if checks fail
├─ Requires approvals (master)
├─ Requires rebase (strict mode master)
└─ Blocks deletes/force-push
```

### Layer 4: Deploy (workflow)
```
Deploy Workflow (master only)
├─ Validates code completely
├─ Tests credentials
└─ Does secure deployment
```

---

## 📝 Configuration Checklist

- [ ] **Workflows created** (ci.yml, branch-enforcer.yml, deploy.yml)
- [ ] **Branch Rules applied**
  - [ ] develop.json via script or GitHub interface
  - [ ] master.json via script or GitHub interface
- [ ] **Secrets configured**
  - [ ] FIREBASE_SERVICE_ACCOUNT
  - [ ] FIREBASE_CI_TOKEN
  - [ ] FIREBASE_ENV_PROD
- [ ] **Variables configured**
  - [ ] FIREBASE_PROJECT_ID
- [ ] **Tests**
  - [ ] Create PR to develop → validations pass
  - [ ] Break a test → build fails
  - [ ] Try merge with PR open → blocked
  - [ ] Merge to develop passing → success
  - [ ] Merge to master → deploy initiates

---

## 🧪 Test Scenarios

### Test 1: Branch Naming Validation
```bash
# Create branch with invalid name
git checkout -b wip-test develop
git push origin wip-test

# Create PR to develop
# Expected result: ❌ check-source-branch-develop FAILS

# Expected message:
# ERROR: Invalid branch type for 'develop'
# Your branch: wip-test
# Allowed branch types: feat/*, feature/*, fix/*, etc
```

### Test 2: Lint Check
```bash
# Break formatting
echo "var x=1" >> src/main.ts  # ❌ ESLint error

git add .
git commit -m "test: lint error"
git push origin feat/lint-test

# Expected result: ❌ CI / lint FAILS
```

### Test 3: Type Check (NEW)
```bash
# Add TypeScript error
echo "const x: string = 123;" >> src/utils.ts  # ❌ Type error

git push

# Expected result: ❌ CI / type-check FAILS
```

### Test 4: Branch Protection Block
```bash
# Try to merge with failing checks
# In GitHub PR interface:

PR Status: ❌ Some checks failed
Merge button: DISABLED (grayed out)
Message: "All required status checks must pass before merging"
```

### Test 5: Strict Mode (master)
```bash
# Merge to develop while master diverged
git checkout -b feat/test develop
git push && Create PR to develop && Merge

# Now master is behind develop
# Some commits in develop are not in master

git checkout feat/release develop
# Create PR to master

# On GitHub:
# Branch status: "This branch is behind the base branch"
# Reason: Strict mode requires rebase for new CI pass

# Solution:
git fetch origin
git rebase origin/master
git push --force-with-lease
# CI runs again
# Now merge is allowed
```

---

## 📊 Visualizing Status

### On GitHub UI
```
Pull Request → Checks tab
├─ All checks: ✅ / ❌
├─ Details of each check
└─ Requires 1 approval (master)
```

### Via GitHub CLI
```bash
gh pr view <PR_NUMBER>

# Output shows:
# - Status of each check
# - Reviews
# - Merge eligibility
```

### Via API
```bash
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/pulls/PR_NUMBER | \
  jq '.statuses'
```

---

## 🔄 Workflow for Updating Rules

If you need to update the Branch Protection Rules:

1. **Edit JSON** in `.github/branch-protection/`
2. **Commit and push** to develop (NO approval required)
3. **Push to master** (triggers `setup-branch-rules.yml` workflow)
4. **Workflow automatically applies** the updated rules

```yaml
# setup-branch-rules.yml triggers automatically when:
on:
  push:
    paths:
      - '.github/branch-protection/*.json'
    branches:
      - master
```

---

## 🚨 Common Error: Status Check Not Found

### Problem
```
"Required status check not found"

Solution:
1. Verify the job exists in the workflow YAML
2. Verify the context name is exactly equal
3. Run the workflow at least 1x successfully
```

### Example
```yaml
# ✅ CORRECT - Job created and ran
jobs:
  type-check:
    run: npx tsc --noEmit
```

```json
// ✅ CORRECT - Context matches job
{
  "context": "CI / type-check"
}
```

---

## 📞 Quick References

| What | File | Link |
|------|------|------|
| Workflows | `.github/workflows/*.yml` | [workflows/](../workflows/) |
| Branch Rules | `.github/branch-protection/*.json` | [branch-protection/](.) |
| Apply Rules | `.github/branch-protection/apply_branch_rules.py` | [apply_branch_rules.py](apply_branch_rules.py) |
| Rules Documentation | `.github/branch-protection/README.md` | [README.md](README.md) |

---

## ✅ Summary

```
┌────────────────────────────────────────────────────────────┐
│  Push to Feature Branch                                    │
└────────────┬───────────────────────────────────────────────┘
             │
             ▼
        ┌───────────────────┐
        │ Validations       │
        │ (Workflows)       │
        │ - Branch names ✓  │
        │ - Lint ✓          │
        │ - Type-check ✓    │
        │ - Tests ✓         │
        │ - Build ✓         │
        └──────────┬────────┘
                   │
                   ▼
        ┌───────────────────┐
        │ Branch Rules      │
        │ (GitHub)          │
        │ - Blocks invalid  │
        │ - Blocks failures │
        │ - Requires reviews│
        └──────────┬────────┘
                   │
                   ▼
        ┌───────────────────┐
        │ ✅ Merge Enabled  │
        │ (Safe & Secure)   │
        └───────────────────┘
```

---

## 📚 Next Steps

1. ✅ Review this document
2. ✅ Apply branch rules (via script or GitHub UI)
3. ✅ Test complete workflow in feature branch
4. ✅ Merge to develop
5. ✅ Verify deploy to master

All 5 steps should result in ✅ to confirm complete integration!
