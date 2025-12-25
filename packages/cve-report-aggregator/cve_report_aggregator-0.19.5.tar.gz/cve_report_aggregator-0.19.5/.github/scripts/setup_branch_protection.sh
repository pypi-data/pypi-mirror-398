#!/bin/bash

echo "Setting up branch protection rules for Git Flow..."

if ! command -v gh &> /dev/null; then
    echo "GitHub CLI (gh) is not installed. Please install it first."
    exit 1
fi

if ! gh auth status &> /dev/null; then
    echo "Not authenticated with GitHub. Run 'gh auth login' first."
    exit 1
fi

REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "Repository: $REPO"

set_branch_protection() {
    local BRANCH=$1
    local ALLOW_FORCE_PUSH=$2
    local REQUIRED_CHECKS=$3
    local REQUIRED_APPROVALS=${4:-1}

    echo "Setting protection for branch: $BRANCH"

    # Create the branch protection rule using JSON payload
    gh api \
        --method PUT \
        -H "Accept: application/vnd.github+json" \
        "/repos/$REPO/branches/$BRANCH/protection" \
        --input - <<EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["$REQUIRED_CHECKS"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": $REQUIRED_APPROVALS,
    "require_last_push_approval": false
  },
  "restrictions": null,
  "allow_force_pushes": $ALLOW_FORCE_PUSH,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": true,
  "lock_branch": false,
  "allow_fork_syncing": true
}
EOF
}

# Protect main branch (don't require approvals right now, but should in future)
echo "Configuring 'main' branch..."
set_branch_protection "main" "false" "all-tests-pass"

gh api \
    --method PATCH \
    -H "Accept: application/vnd.github+json" \
    "/repos/$REPO/branches/main/protection/required_pull_request_reviews" \
    --input - <<EOF
{
  "dismiss_stale_reviews": true,
  "require_code_owner_reviews": false,
  "required_approving_review_count": 2,
  "require_last_push_approval": true
}
EOF

# Protect develop branch
echo "Configuring 'develop' branch..."
set_branch_protection "develop" "false" "all-tests-pass"

echo "Branch protection rules configured successfully!"

cat <<EOF
Current Protection Rules:
- main branch:
  - Requires PR with 2 approvals
  - Requires all status checks to pass
  - Requires branches to be up to date
  - Requires conversation resolution
  - No force pushes allowed
  - No branch deletion allowed
- develop branch:
  - Requires PR with 1 approval
  - Requires all status checks to pass
  - Requires branches to be up to date
  - Requires conversation resolution
  - No force pushes allowed
  - No branch deletion allowed
EOF
