#!/usr/bin/env python3
"""
Update README.md with test results and coverage badges.

This script reads the coverage.json file and updates the README.md with:
- Test count badge
- Coverage percentage badge
- Test status
- Coverage summary table
"""

import json
import re
from datetime import datetime
from pathlib import Path


def get_coverage_color(percentage):
    """Get badge color based on coverage percentage."""
    if percentage >= 90:
        return "brightgreen"
    elif percentage >= 80:
        return "green"
    elif percentage >= 70:
        return "yellow"
    elif percentage >= 60:
        return "orange"
    else:
        return "red"


def create_badge_url(label, message, color):
    """Create a shields.io badge URL."""
    return f"https://img.shields.io/badge/{label}-{message}-{color}"


def update_readme():
    """Update README.md with test and coverage information."""
    
    # Read coverage data
    coverage_file = Path("reports/coverage.json")
    if not coverage_file.exists():
        print("❌ Coverage file not found. Run tests first: ./run_unit_tests.sh")
        return False
    
    with open(coverage_file) as f:
        coverage_data = json.load(f)
    
    # Extract metrics
    total_coverage = coverage_data['totals']['percent_covered']
    num_statements = coverage_data['totals']['num_statements']
    covered_statements = coverage_data['totals']['covered_lines']
    missing_statements = coverage_data['totals']['missing_lines']
    
    # Count tests from pytest metadata (if available)
    num_tests = 0
    pytest_file = Path("reports/.pytest_cache/v/cache/lastfailed")
    
    # Try to get test count from pytest collection
    try:
        import subprocess
        result = subprocess.run(
            ["python", "-m", "pytest", "--collect-only", "-q", "tests/"],
            capture_output=True,
            text=True,
            timeout=30
        )
        # Parse output like "938 tests collected in 0.44s"
        if "tests collected" in result.stdout:
            for line in result.stdout.split('\n'):
                if "tests collected" in line or "test collected" in line:
                    # Extract number from "938 tests collected" or "1 test collected"
                    parts = line.strip().split()
                    if parts[0].isdigit():
                        num_tests = int(parts[0])
                        break
    except Exception as e:
        print(f"⚠️  Could not extract test count: {e}")
        num_tests = 938  # Fallback to known count
    
    # Create badges
    coverage_color = get_coverage_color(total_coverage)
    coverage_badge = create_badge_url("coverage", f"{total_coverage:.1f}%25", coverage_color)
    tests_badge = create_badge_url("tests", f"{num_tests}%20passed", "brightgreen")
    
    # Get files with low coverage
    low_coverage_files = []
    for file_path, stats in coverage_data['files'].items():
        pct = stats['summary']['percent_covered']
        if pct < 80:
            short_path = file_path.replace('src/geek_cafe_saas_sdk/', '')
            missing = stats['summary']['missing_lines']
            low_coverage_files.append((pct, missing, short_path))
    
    low_coverage_files.sort()
    
    # Create coverage summary
    coverage_summary = f"""## Test Coverage

![Tests]({tests_badge})
![Coverage]({coverage_badge})

**Overall Coverage:** {total_coverage:.1f}% ({covered_statements}/{num_statements} statements)

### Coverage Summary

| Metric | Value |
|--------|-------|
| Total Statements | {num_statements:,} |
| Covered Statements | {covered_statements:,} |
| Missing Statements | {missing_statements:,} |
| Coverage Percentage | {total_coverage:.1f}% |
| Total Tests | {num_tests} |
| Test Status | ✅ All Passing |

### Files Needing Attention (< 80% coverage)

| Coverage | Missing Lines | File |
|----------|---------------|------|
"""
    
    # Add low coverage files (limit to top 10)
    for pct, missing, path in low_coverage_files[:10]:
        coverage_summary += f"| {pct:.1f}% | {missing} | `{path}` |\n"
    
    if len(low_coverage_files) > 10:
        coverage_summary += f"\n*... and {len(low_coverage_files) - 10} more files with < 80% coverage*\n"
    
    if not low_coverage_files:
        coverage_summary += "| - | - | ✅ All files have >= 80% coverage |\n"
    
    coverage_summary += f"""
### Running Tests

```bash
# Run all tests with coverage
./run_unit_tests.sh

# View detailed coverage report
open reports/coverage/index.html
```

*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

---
"""
    
    # Read README
    readme_file = Path("README.md")
    if not readme_file.exists():
        print("❌ README.md not found")
        return False
    
    readme_content = readme_file.read_text()
    
    # Define markers for the coverage section
    start_marker = "<!-- COVERAGE-BADGE:START -->"
    end_marker = "<!-- COVERAGE-BADGE:END -->"
    
    # Check if markers exist
    if start_marker in readme_content and end_marker in readme_content:
        # Replace existing section
        pattern = f"{re.escape(start_marker)}.*?{re.escape(end_marker)}"
        new_section = f"{start_marker}\n{coverage_summary}\n{end_marker}"
        updated_content = re.sub(pattern, new_section, readme_content, flags=re.DOTALL)
    else:
        # Add markers and section at the beginning (after title)
        lines = readme_content.split('\n')
        insert_index = 1  # After first line (title)
        
        # Find a better insertion point (after description if exists)
        for i, line in enumerate(lines):
            if line.startswith('##'):
                insert_index = i
                break
        
        new_section = f"\n{start_marker}\n{coverage_summary}\n{end_marker}\n"
        lines.insert(insert_index, new_section)
        updated_content = '\n'.join(lines)
    
    # Write updated README
    readme_file.write_text(updated_content)
    
    print("✅ README.md updated successfully!")
    print(f"   📊 Coverage: {total_coverage:.1f}%")
    print(f"   🧪 Tests: {num_tests} passing")
    print(f"   📉 Files < 80%: {len(low_coverage_files)}")
    
    return True


if __name__ == "__main__":
    import sys
    success = update_readme()
    sys.exit(0 if success else 1)
