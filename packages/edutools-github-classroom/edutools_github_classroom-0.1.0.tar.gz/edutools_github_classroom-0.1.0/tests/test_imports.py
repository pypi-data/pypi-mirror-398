"""
Test script for edutools-github-classroom package.
This script verifies that all modules can be imported correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path to test local package
package_dir = Path(__file__).parent.parent
sys.path.insert(0, str(package_dir))

print("Testing edutools-github-classroom package imports...")
print("=" * 60)

try:
    # Test main imports
    print("\n1. Testing main package import...")
    from edutools_github_classroom import ClassroomAPI
    print("   ✓ ClassroomAPI imported successfully")
    
    # Test exception imports
    print("\n2. Testing exception imports...")
    from edutools_github_classroom import (
        ClassroomAPIError,
        ClassroomAuthenticationError,
        ClassroomResourceNotFoundError
    )
    print("   ✓ All exceptions imported successfully")
    
    # Test version
    print("\n3. Testing version...")
    from edutools_github_classroom import __version__
    print(f"   ✓ Version: {__version__}")
    
    # Test individual modules
    print("\n4. Testing individual modules...")
    from edutools_github_classroom.base import ClassroomBase
    print("   ✓ ClassroomBase imported")
    
    from edutools_github_classroom.classrooms import Classrooms
    print("   ✓ Classrooms imported")
    
    from edutools_github_classroom.assignments import Assignments
    print("   ✓ Assignments imported")
    
    from edutools_github_classroom.submissions import Submissions
    print("   ✓ Submissions imported")
    
    from edutools_github_classroom.grades import Grades
    print("   ✓ Grades imported")
    
    # Test ClassroomAPI initialization (without token)
    print("\n5. Testing ClassroomAPI initialization...")
    try:
        api = ClassroomAPI("")
        print("   ✗ Should have raised ValueError for empty token")
    except ValueError as e:
        print(f"   ✓ Correctly raised ValueError: {e}")
    
    # Test with mock token
    print("\n6. Testing ClassroomAPI with mock token...")
    api = ClassroomAPI("ghp_test_token")
    print("   ✓ ClassroomAPI initialized with mock token")
    
    # Verify all properties exist
    print("\n7. Verifying API properties...")
    assert hasattr(api, 'classrooms'), "Missing classrooms property"
    print("   ✓ classrooms property exists")
    
    assert hasattr(api, 'assignments'), "Missing assignments property"
    print("   ✓ assignments property exists")
    
    assert hasattr(api, 'submissions'), "Missing submissions property"
    print("   ✓ submissions property exists")
    
    assert hasattr(api, 'grades'), "Missing grades property"
    print("   ✓ grades property exists")
    
    # Test context manager
    print("\n8. Testing context manager...")
    with ClassroomAPI("ghp_test_token") as api:
        assert api is not None
    print("   ✓ Context manager works correctly")
    
    # Test method availability
    print("\n9. Testing method availability...")
    api = ClassroomAPI("ghp_test_token")
    
    # Classrooms methods
    assert hasattr(api.classrooms, 'list')
    assert hasattr(api.classrooms, 'get')
    assert hasattr(api.classrooms, 'get_all')
    assert hasattr(api.classrooms, 'filter_by_name')
    assert hasattr(api.classrooms, 'filter_active')
    print("   ✓ All classrooms methods available")
    
    # Assignments methods
    assert hasattr(api.assignments, 'list')
    assert hasattr(api.assignments, 'get')
    assert hasattr(api.assignments, 'get_all')
    assert hasattr(api.assignments, 'filter_by_title')
    assert hasattr(api.assignments, 'get_statistics')
    assert hasattr(api.assignments, 'filter_by_type')
    print("   ✓ All assignments methods available")
    
    # Submissions methods
    assert hasattr(api.submissions, 'list')
    assert hasattr(api.submissions, 'get_all')
    assert hasattr(api.submissions, 'get_by_student')
    assert hasattr(api.submissions, 'filter_by_status')
    assert hasattr(api.submissions, 'get_repository_urls')
    assert hasattr(api.submissions, 'get_statistics')
    print("   ✓ All submissions methods available")
    
    # Grades methods
    assert hasattr(api.grades, 'get')
    assert hasattr(api.grades, 'export_to_csv')
    assert hasattr(api.grades, 'get_by_student')
    assert hasattr(api.grades, 'get_statistics')
    assert hasattr(api.grades, 'filter_by_status')
    assert hasattr(api.grades, 'get_by_roster_identifier')
    print("   ✓ All grades methods available")
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nThe package is ready to be installed and used.")
    print("\nNext steps:")
    print("1. Install locally: pip install -e .")
    print("2. Test with real GitHub token")
    print("3. Build package: python -m build")
    print("4. Upload to PyPI: twine upload dist/*")
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
