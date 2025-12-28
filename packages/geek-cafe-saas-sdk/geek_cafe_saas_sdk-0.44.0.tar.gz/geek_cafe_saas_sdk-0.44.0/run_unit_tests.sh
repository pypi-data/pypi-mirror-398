#!/usr/bin/env bash
set -euo pipefail

# run_unit_tests.sh - Run unit tests for the project

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "Error: .venv directory not found. Please run pysetup.sh first." >&2
    exit 1
fi

# Activate the virtual environment
source .venv/bin/activate

# Create reports directory if it doesn't exist
mkdir -p reports

# Run the unit tests with coverage and HTML reports
echo "Running unit tests with coverage..."
python -m pytest tests/ -v --tb=short \
    --cov=geek_cafe_saas_sdk \
    --cov-report=term-missing \
    --cov-report=html:reports/coverage \
    --cov-report=json:reports/coverage.json \
    --html=reports/test-report.html \
    --self-contained-html \
    --cov-fail-under=0

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 COVERAGE SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Generate coverage summary from JSON
python3 << 'EOF'
import json
import sys

try:
    with open('reports/coverage.json', 'r') as f:
        data = json.load(f)
    
    total_pct = data['totals']['percent_covered']
    print(f"\n🎯 Overall Coverage: {total_pct:.1f}%\n")
    
    # Find files with low coverage
    files = []
    for file_path, stats in data['files'].items():
        pct = stats['summary']['percent_covered']
        missing = stats['summary']['missing_lines']
        files.append((pct, missing, file_path))
    
    files.sort()
    
    print("📉 Files with LOWEST coverage (< 80%):")
    print("-" * 80)
    low_count = 0
    for pct, missing, path in files:
        if pct < 80:
            # Shorten path for display
            short_path = path.replace('src/geek_cafe_saas_sdk/', '')
            print(f"  {pct:5.1f}% - {missing:3d} lines missing - {short_path}")
            low_count += 1
            if low_count >= 15:
                remaining = sum(1 for p, _, _ in files if p < 80) - 15
                if remaining > 0:
                    print(f"  ... and {remaining} more files with < 80% coverage")
                break
    
    if low_count == 0:
        print("  ✅ All files have >= 80% coverage!")
    
    print("\n📈 Files with HIGHEST coverage (>= 95%):")
    print("-" * 80)
    high_files = [(pct, path) for pct, _, path in files if pct >= 95]
    high_files.sort(reverse=True)
    
    for i, (pct, path) in enumerate(high_files[:10]):
        short_path = path.replace('src/geek_cafe_saas_sdk/', '')
        print(f"  {pct:5.1f}% - {short_path}")
    
    if len(high_files) > 10:
        print(f"  ... and {len(high_files) - 10} more files with >= 95% coverage")
    
    print()

except Exception as e:
    print(f"Error reading coverage data: {e}", file=sys.stderr)
    sys.exit(1)
EOF

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Test reports generated:"
echo "   📋 Test report:     reports/test-report.html"
echo "   📊 Coverage report: reports/coverage/index.html"
echo "   📈 Coverage JSON:   reports/coverage.json"
echo ""
echo "💡 Tip: Open coverage report to see line-by-line coverage details"
echo "   macOS:  open reports/coverage/index.html"
echo "   Linux:  xdg-open reports/coverage/index.html"
echo ""

# Update README.md with coverage badges
echo "📝 Updating README.md with coverage badges..."
python3 update_readme_badges.py
echo ""

# Deactivate the virtual environment
deactivate
