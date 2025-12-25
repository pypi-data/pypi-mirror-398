#!/bin/bash

# Script to compare Mist API documentation files between two git tags.
# Usage: api-doc-diff.sh <path> <from_tag> <to_tag>

set -e  # Exit on error

# Color codes for output.
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print error messages.
error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
}

# Function to print warning messages.
warn() {
    echo -e "${YELLOW}WARNING: $1${NC}" >&2
}

# Function to print success messages.
success() {
    echo -e "${GREEN}$1${NC}"
}

# Function to print usage.
usage() {
    echo "Usage: $0 <path> <from_tag> <to_tag>"
    echo ""
    echo "Arguments:"
    echo "  path      Path to the Mist API repository"
    echo "  from_tag  Git tag to compare from"
    echo "  to_tag    Git tag to compare to"
    echo ""
    echo "Example:"
    echo "  $0 /path/to/api v1.0.0 v1.1.0"
    exit 1
}

# ============================================================================
# VALIDATION SECTION - All checks before performing operations.
# ============================================================================

# Check if all parameters are provided.
if [ $# -ne 3 ]; then
    error "Missing required parameters"
    usage
fi

API_PATH="$1"
FROM_TAG="$2"
TO_TAG="$3"

# Store original directory.
ORIGINAL_DIR=$(pwd)

# Check if VS Code (code command) is available.
if ! command -v code &> /dev/null; then
    error "VS Code 'code' command not found in PATH"
    echo ""
    echo "Please install VS Code and ensure the 'code' command is available."
    echo "On macOS, open VS Code and run: Shell Command: Install 'code' command in PATH"
    echo ""
    exit 1
fi

# Validate that path exists.
if [ ! -d "$API_PATH" ]; then
    error "Path does not exist: $API_PATH"
    exit 1
fi

# Change to the API repository.
cd "$API_PATH" || {
    error "Failed to change directory to: $API_PATH"
    exit 1
}

# Validate that it's a git repository.
if [ ! -d .git ]; then
    error "Not a git repository: $API_PATH"
    cd "$ORIGINAL_DIR"
    exit 1
fi

# Fetch the requested tags from remote if they don't exist locally.
echo "Checking and fetching required tags..."
for tag in "$FROM_TAG" "$TO_TAG"; do
    if ! git rev-parse "$tag" >/dev/null 2>&1; then
        echo "Fetching tag: $tag"
        if ! git fetch origin "refs/tags/${tag}:refs/tags/${tag}" 2>/dev/null; then
            error "Tag does not exist on remote: $tag"
            echo ""
            echo "Please verify that the tag exists in the remote repository."
            cd "$ORIGINAL_DIR"
            exit 1
        fi
        success "Fetched tag: $tag"
    else
        echo "  ✓ Tag already exists locally: $tag"
    fi
done

echo ""

# ============================================================================
# MAIN OPERATIONS - All validations passed, proceed with work.
# ============================================================================

# Create secure temporary directory with random naming.
TEMP_BASE=$(mktemp -d) || {
    error "Failed to create temporary directory"
    cd "$ORIGINAL_DIR"
    exit 1
}

FROM_DIR="${TEMP_BASE}/${FROM_TAG}"
TO_DIR="${TEMP_BASE}/${TO_TAG}"

echo "Creating temporary directories..."
mkdir -p "$FROM_DIR" "$TO_DIR" || {
    error "Failed to create directories $FROM_DIR or $TO_DIR"
    cd "$ORIGINAL_DIR"
    exit 1
}

# List of files to extract.
FILES=(
    "docs/src/Home.md"
    "docs/src/Overview.md"
    "docs/src/Auth.md"
    "docs/src/Site.md"
    "docs/src/Org.md"
    "docs/src/MSP.md"
)

# Function to extract file from a tag.
extract_file() {
    local tag=$1
    local filepath=$2
    local dest_dir=$3
    local filename=$(basename "$filepath")
    
    # Validate filename to prevent path traversal attacks.
    # basename should already strip path components, but verify for safety.
    case "$filename" in
        */*|*\\*|..|.|"")
            error "Invalid filename detected: $filename"
            return 1
            ;;
    esac
    
    # Validate destination directory exists and is writable.
    if [ ! -d "$dest_dir" ] || [ ! -w "$dest_dir" ]; then
        error "Destination directory not writable: $dest_dir"
        return 1
    fi

    # Attempt to extract the file. Capture stderr to distinguish between
    # "file doesn't exist in tag" vs "write failure" errors.
    local git_error
    if git_error=$(git show "${tag}:${filepath}" 2>&1 > "${dest_dir}/${filename}"); then
        echo "  ✓ Extracted: $filename"
    else
        # Check if it's a "file doesn't exist" error or something else.
        if echo "$git_error" | grep -q "does not exist\|exists on disk, but not in"; then
            warn "File does not exist in tag $tag: $filepath"
            # Create empty placeholder file.
            touch "${dest_dir}/${filename}.missing"
        else
            error "Failed to extract $filepath: $git_error"
            return 1
        fi
    fi
}

# Extract all files from a tag.
extract_all_files() {
    local tag=$1
    local dest_dir=$2

    success "Extracting files from tag: $tag"
    for file in "${FILES[@]}"; do
        extract_file "$tag" "$file" "$dest_dir"
    done
}

# Extract files from both tags in parallel for better performance.
# Capture output to prevent interleaved messages.
echo ""
FROM_OUTPUT=$(mktemp)
TO_OUTPUT=$(mktemp)

extract_all_files "$FROM_TAG" "$FROM_DIR" > "$FROM_OUTPUT" 2>&1 &
FROM_PID=$!

extract_all_files "$TO_TAG" "$TO_DIR" > "$TO_OUTPUT" 2>&1 &
TO_PID=$!

# Wait for both extraction processes to complete.
wait $FROM_PID
FROM_EXIT=$?

wait $TO_PID
TO_EXIT=$?

# Display output sequentially to avoid garbled messages.
cat "$FROM_OUTPUT"
cat "$TO_OUTPUT"

# Clean up temporary output files.
rm -f "$FROM_OUTPUT" "$TO_OUTPUT"

# Check if either extraction failed.
if [ $FROM_EXIT -ne 0 ] || [ $TO_EXIT -ne 0 ]; then
    error "File extraction failed"
    cd "$ORIGINAL_DIR"
    exit 1
fi

echo ""

# Print location of extracted files.
echo ""
success "Files extracted successfully!"
echo ""
echo "Location: $TEMP_BASE"
echo "  - $FROM_TAG files: $FROM_DIR"
echo "  - $TO_TAG files: $TO_DIR"
echo ""

# Open VS Code with the temp directory.
echo "Opening VS Code..."
code "$TEMP_BASE"

# Return to original directory.
cd "$ORIGINAL_DIR" || {
    error "Failed to return to original directory"
    exit 1
}

success "Done!"
