#!/bin/bash
# VALLUM — Repository Security Scanner
# Run before every commit or CI/CD pipeline

set -e

echo "VALLUM Security Scan"
echo "============================================================"
echo ""

ERRORS=0
WARNINGS=0

# Check for .env in staging
echo "[1/7] Checking for .env files..."
if git diff --cached --name-only | grep -E '^\.env$' > /dev/null 2>&1; then
    echo "  CRITICAL: .env file detected!"
    ERRORS=$((ERRORS + 1))
else
    echo "  OK"
fi

# Scan for Google API keys
echo "[2/7] Scanning for Google API keys..."
if git diff --cached | grep -E 'AIzaSy[0-9A-Za-z_-]{35}' > /dev/null 2>&1; then
    echo "  CRITICAL: Google API key found!"
    ERRORS=$((ERRORS + 1))
else
    echo "  OK"
fi

# Scan for OpenAI keys
echo "[3/7] Scanning for OpenAI API keys..."
if git diff --cached | grep -E 'sk-[a-zA-Z0-9]{20,}' > /dev/null 2>&1; then
    echo "  CRITICAL: OpenAI API key found!"
    ERRORS=$((ERRORS + 1))
else
    echo "  OK"
fi

# Scan for private keys
echo "[4/7] Scanning for private keys..."
if git diff --cached | grep -E 'BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY' > /dev/null 2>&1; then
    echo "  CRITICAL: Private key detected!"
    ERRORS=$((ERRORS + 1))
else
    echo "  OK"
fi

# Check for passwords
echo "[5/7] Scanning for hardcoded passwords..."
if git diff --cached | grep -iE '(password|passwd|pwd)\s*=\s*["\047][^"\047]{4,}' > /dev/null 2>&1; then
    echo "  WARNING: Potential hardcoded password"
    WARNINGS=$((WARNINGS + 1))
else
    echo "  OK"
fi

# Check file sizes
echo "[6/7] Checking for large files..."
LARGE_FILES=$(git diff --cached --name-only | while read file; do
    if [ -f "$file" ]; then
        SIZE=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
        if [ "$SIZE" -gt 1048576 ]; then echo "$file ($((SIZE / 1024))KB)"; fi
    fi
done)
if [ -n "$LARGE_FILES" ]; then
    echo "  WARNING: Large files:"
    echo "$LARGE_FILES"
    WARNINGS=$((WARNINGS + 1))
else
    echo "  OK"
fi

# Dependency scan
echo "[7/7] Scanning dependencies..."
if command -v safety &> /dev/null; then
    if ! safety check --json > /dev/null 2>&1; then
        echo "  WARNING: Vulnerabilities found"
        WARNINGS=$((WARNINGS + 1))
    else
        echo "  OK"
    fi
else
    echo "  INFO: Install 'safety' for dependency scanning"
fi

echo ""
echo "============================================================"
if [ $ERRORS -gt 0 ]; then
    echo "SCAN FAILED: $ERRORS error(s), $WARNINGS warning(s)"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo "SCAN PASSED WITH WARNINGS: $WARNINGS warning(s)"
    exit 0
else
    echo "SCAN PASSED: Repository is clean"
    exit 0
fi
