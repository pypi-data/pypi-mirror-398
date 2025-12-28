#!/usr/bin/env python3
"""
Batch migration script to update tests for auto-extraction pattern.

This script automatically removes tenant_id and user_id parameters from service method calls
in test files and updates assertions to expect test_user instead of user_123.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


def migrate_service_calls(content: str) -> Tuple[str, int]:
    """
    Remove tenant_id and user_id parameters from service method calls.
    
    Returns:
        Tuple of (modified_content, number_of_changes)
    """
    changes = 0
    
    # Pattern 1: service.method(tenant_id="...", user_id="...", other_params)
    # Replace with: service.method(other_params)
    pattern1 = r'(\w+\.(?:create|get_by_id|update|delete|list_\w+|add_member|remove_member|archive|unarchive|tally_\w+))\(\s*tenant_id\s*=\s*["\'][^"\']+["\']\s*,\s*user_id\s*=\s*["\'][^"\']+["\']\s*,\s*'
    content, count1 = re.subn(pattern1, r'\1(', content)
    changes += count1
    
    # Pattern 2: service.method(tenant_id="...", user_id="...", ) with trailing comma but no other params
    pattern2 = r'(\w+\.(?:create|get_by_id|update|delete|list_\w+|add_member|remove_member|archive|unarchive|tally_\w+))\(\s*tenant_id\s*=\s*["\'][^"\']+["\']\s*,\s*user_id\s*=\s*["\'][^"\']+["\']\s*\)'
    content, count2 = re.subn(pattern2, r'\1()', content)
    changes += count2
    
    # Pattern 3: service.method(resource_id, tenant_id="...", user_id="...")
    pattern3 = r'(\w+\.(?:get_by_id|update|delete))\((["\'][^"\']+["\'])\s*,\s*tenant_id\s*=\s*["\'][^"\']+["\']\s*,\s*user_id\s*=\s*["\'][^"\']+["\']\s*\)'
    content, count3 = re.subn(pattern3, r'\1(\2)', content)
    changes += count3
    
    # Pattern 4: service.method(resource_id, tenant_id, user_id, other) - positional args
    pattern4 = r'(\w+\.(?:get_by_id|update|delete))\((["\'][^"\']+["\'])\s*,\s*["\'][^"\']+["\']\s*,\s*["\'][^"\']+["\']\s*,\s*'
    content, count4 = re.subn(pattern4, r'\1(\2, ', content)
    changes += count4
    
    # Pattern 5: service.method(resource_id, tenant_id, user_id) - only those 3 args
    pattern5 = r'(\w+\.(?:get_by_id|update|delete))\((["\'][^"\']+["\'])\s*,\s*["\'][^"\']+["\']\s*,\s*["\'][^"\']+["\']\s*\)'
    content, count5 = re.subn(pattern5, r'\1(\2)', content)
    changes += count5
    
    # Pattern 6: Just tenant_id/user_id in any order
    pattern6 = r',\s*(?:tenant_id|user_id)\s*=\s*["\'][^"\']+["\']\s*,\s*(?:tenant_id|user_id)\s*=\s*["\'][^"\']+["\']\s*,'
    content, count6 = re.subn(pattern6, ',', content)
    changes += count6
    
    # Pattern 7: tenant_id or user_id at end of parameter list
    pattern7 = r',\s*(?:tenant_id|user_id)\s*=\s*["\'][^"\']+["\']\s*\)'
    content, count7 = re.subn(pattern7, ')', content)
    changes += count7
    
    return content, changes


def migrate_assertions(content: str) -> Tuple[str, int]:
    """
    Update assertions to expect test_user instead of user_123.
    
    Returns:
        Tuple of (modified_content, number_of_changes)
    """
    changes = 0
    
    # Pattern: assert result.data.created_by_id == "user_123"
    # Replace with: assert result.data.created_by_id == "test_user"
    pattern1 = r'(assert\s+\w+\.(?:created_by_id|updated_by_id|user_id)\s*==\s*)["\']user_123["\']'
    content, count1 = re.subn(pattern1, r'\1"test_user"', content)
    changes += count1
    
    # Pattern: assert vote.user_id == "user_123"
    pattern2 = r'(assert\s+\w+\.user_id\s*==\s*)["\']user_123["\']'
    content, count2 = re.subn(pattern2, r'\1"test_user"', content)
    changes += count2
    
    return content, changes


def migrate_helper_defaults(content: str) -> Tuple[str, int]:
    """
    Update helper method default values.
    
    Returns:
        Tuple of (modified_content, number_of_changes)
    """
    changes = 0
    
    # Pattern: user_id: str = "user_123"
    # Replace with: user_id: str = "test_user"
    pattern = r'(user_id:\s*str\s*=\s*)["\']user_123["\']'
    content, count = re.subn(pattern, r'\1"test_user"', content)
    changes += count
    
    return content, changes


def migrate_test_file(filepath: Path) -> bool:
    """
    Migrate a single test file.
    
    Returns:
        True if file was modified, False otherwise
    """
    try:
        content = filepath.read_text()
        original_content = content
        
        # Apply migrations
        content, call_changes = migrate_service_calls(content)
        content, assert_changes = migrate_assertions(content)
        content, helper_changes = migrate_helper_defaults(content)
        
        total_changes = call_changes + assert_changes + helper_changes
        
        if total_changes > 0:
            filepath.write_text(content)
            print(f"✅ {filepath.name}: {total_changes} changes")
            print(f"   - Service calls: {call_changes}")
            print(f"   - Assertions: {assert_changes}")
            print(f"   - Helper defaults: {helper_changes}")
            return True
        else:
            print(f"⏭️  {filepath.name}: No changes needed")
            return False
            
    except Exception as e:
        print(f"❌ {filepath.name}: Error - {e}")
        return False


def find_test_files(test_dir: Path, exclude_patterns: List[str] = None) -> List[Path]:
    """Find all test files in directory."""
    exclude_patterns = exclude_patterns or []
    test_files = []
    
    for test_file in test_dir.glob("test_*.py"):
        # Skip files that match exclude patterns
        if any(pattern in test_file.name for pattern in exclude_patterns):
            continue
        test_files.append(test_file)
    
    return sorted(test_files)


def main():
    """Main migration script."""
    print("=" * 70)
    print("🔧 Test Migration Script - Auto-Extraction Pattern")
    print("=" * 70)
    print()
    
    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    test_dir = project_root / "tests"
    
    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        return 1
    
    # Files to exclude (already migrated or special cases)
    exclude_patterns = [
        "test_chat_channel_service.py",  # Already migrated
        "test_vote_service.py",  # Already migrated
        "test_cognito",  # Cognito tests have different structure
        "test_password_handlers.py",  # Handler tests
        "test_tenant_service_cognito",  # Cognito integration
    ]
    
    print(f"📁 Scanning: {test_dir}")
    print(f"🚫 Excluding: {', '.join(exclude_patterns)}")
    print()
    
    test_files = find_test_files(test_dir, exclude_patterns)
    
    if not test_files:
        print("❌ No test files found to migrate")
        return 1
    
    print(f"📊 Found {len(test_files)} test files to process")
    print()
    
    modified_count = 0
    
    for test_file in test_files:
        if migrate_test_file(test_file):
            modified_count += 1
    
    print()
    print("=" * 70)
    print(f"✅ Migration complete!")
    print(f"   Modified: {modified_count}/{len(test_files)} files")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Run: python -m pytest tests/ -v --tb=no -q")
    print("2. Review changes: git diff tests/")
    print("3. If issues, rollback: git checkout tests/")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
