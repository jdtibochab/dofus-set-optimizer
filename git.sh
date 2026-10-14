
function pull_pr(){
    local PR="$1"
    # Fetch the PR and create a worktree for it
    git fetch origin "pull/$PR/head:pr-$PR"
    git worktree add "../pr-$PR" "pr-$PR"
}

function push_pr(){
    local PR="$1"
    gh pr checkout "$PR" # e.g., gh pr checkout 123
    git push
}

function clean_branch() {
    local BRANCH="$1"
    git worktree remove "../$BRANCH" --force
    git branch -D "$BRANCH"
}

function create_branch() {
    local BRANCH="$1"
    git branch "$BRANCH"
    git worktree add "../$BRANCH" "$BRANCH"
    cd "../$BRANCH"
    ln -s "../main/data" "./data"
    conda run -n py312 python -m venv .venv
    source ".venv/bin/activate"
    pip install -e .
}