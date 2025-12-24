#!/usr/bin/env bash

set -e

# Parse command line arguments
JSON_MODE=false
ARGS=()

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --help|-h)
            echo "Usage: $0 [--json] [decision_topic]"
            echo "  --json    Output results in JSON format"
            echo "  --help    Show this help message"
            exit 0
            ;;
        *)
            ARGS+=("$arg")
            ;;
    esac
done

# Get script directory and load common functions
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get repository root
REPO_ROOT=$(get_repo_root)

# Create decisions directory
DECISIONS_DIR="$REPO_ROOT/docs/decisions"
mkdir -p "$DECISIONS_DIR"

# Path to template
TEMPLATE_PATH="$REPO_ROOT/.specify/templates/decide-template.md"

# Function to get next ADR number
get_next_adr_number() {
    local decisions_dir="$1"
    local highest=0

    if [[ -d "$decisions_dir" ]]; then
        for file in "$decisions_dir"/*.md; do
            [[ -f "$file" ]] || continue
            filename=$(basename "$file")
            # Match pattern: 0001-title.md, 0002-title.md, etc.
            if [[ "$filename" =~ ^([0-9]{4})- ]]; then
                number=$((10#${BASH_REMATCH[1]}))
                if [[ "$number" -gt "$highest" ]]; then
                    highest=$number
                fi
            fi
        done
    fi

    # Return next number in 4-digit format
    printf "%04d" $((highest + 1))
}

ADR_NUMBER=$(get_next_adr_number "$DECISIONS_DIR")

# Output results
if $JSON_MODE; then
    printf '{"REPO_ROOT":"%s","DECISIONS_DIR":"%s","ADR_NUMBER":"%s","TEMPLATE_PATH":"%s"}\n' \
        "$REPO_ROOT" "$DECISIONS_DIR" "$ADR_NUMBER" "$TEMPLATE_PATH"
else
    echo "REPO_ROOT: $REPO_ROOT"
    echo "DECISIONS_DIR: $DECISIONS_DIR"
    echo "ADR_NUMBER: $ADR_NUMBER"
    echo "TEMPLATE_PATH: $TEMPLATE_PATH"
fi
