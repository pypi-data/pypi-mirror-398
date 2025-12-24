"""
Test file to verify enhanced error messaging in the Arca SDK

Run with: python tests/test_error_handling.py
"""

import sys
sys.path.insert(0, '.')

from arca.exceptions import ArcaAPIError, ArcaAuthError


def test_arca_api_error_with_all_fields():
    """Test that ArcaAPIError captures and displays all error context"""
    print("=" * 60)
    print("Test 1: ArcaAPIError with all fields populated")
    print("=" * 60)
    
    error = ArcaAPIError(
        message="Type mismatch in comparison",
        status_code=400,
        details="Cannot compare VARCHAR column 'name' with TIMESTAMP value",
        suggestion="Use CAST to convert types: CAST(name AS TIMESTAMP) or compare with a string value",
        technical_details="operator does not exist: character varying >= timestamp",
        problematic_query="name >= CURRENT_DATE - INTERVAL 1 DAY"
    )
    
    print("\n--- Full error message (str(exception)) ---")
    print(str(error))
    
    print("\n--- Individual fields ---")
    print(f"e.message: {error.message}")
    print(f"e.status_code: {error.status_code}")
    print(f"e.details: {error.details}")
    print(f"e.suggestion: {error.suggestion}")
    print(f"e.technical_details: {error.technical_details}")
    print(f"e.problematic_query: {error.problematic_query}")
    
    assert error.message == "Type mismatch in comparison"
    assert error.status_code == 400
    assert error.details == "Cannot compare VARCHAR column 'name' with TIMESTAMP value"
    assert error.suggestion is not None
    assert "CAST" in error.suggestion
    assert error.problematic_query is not None
    
    print("\n✓ Test passed!")


def test_arca_api_error_partial_fields():
    """Test that ArcaAPIError works with only some fields populated"""
    print("\n" + "=" * 60)
    print("Test 2: ArcaAPIError with partial fields")
    print("=" * 60)
    
    error = ArcaAPIError(
        message="Table not found",
        status_code=404,
        details="The table 'nonexistent_table' does not exist in your account",
        suggestion="Check the table name or use list_tables() to see available tables"
    )
    
    print("\n--- Full error message ---")
    print(str(error))
    
    print("\n--- Individual fields ---")
    print(f"e.message: {error.message}")
    print(f"e.status_code: {error.status_code}")
    print(f"e.details: {error.details}")
    print(f"e.suggestion: {error.suggestion}")
    print(f"e.technical_details: {error.technical_details}")
    print(f"e.problematic_query: {error.problematic_query}")
    
    assert error.technical_details is None
    assert error.problematic_query is None
    
    print("\n✓ Test passed!")


def test_arca_api_error_minimal():
    """Test that ArcaAPIError works with minimal fields (backward compatibility)"""
    print("\n" + "=" * 60)
    print("Test 3: ArcaAPIError with minimal fields (backward compatible)")
    print("=" * 60)
    
    error = ArcaAPIError(message="Something went wrong", status_code=500)
    
    print("\n--- Full error message ---")
    print(str(error))
    
    assert error.message == "Something went wrong"
    assert error.status_code == 500
    assert error.details is None
    assert error.suggestion is None
    
    print("\n✓ Test passed!")


def test_exception_catching_pattern():
    """Test the recommended exception catching pattern for SDK users"""
    print("\n" + "=" * 60)
    print("Test 4: Recommended exception catching pattern")
    print("=" * 60)
    
    def simulate_api_call():
        raise ArcaAPIError(
            message="Invalid data type",
            status_code=400,
            details="Column 'calories' expects INTEGER but received STRING 'not-a-number'",
            suggestion="Ensure numeric values are passed as integers, not strings",
            technical_details="invalid input syntax for type integer: 'not-a-number'"
        )
    
    print("\n--- SDK user exception handling example ---")
    try:
        simulate_api_call()
    except ArcaAPIError as e:
        print(f"Error: {e.message}")
        print(f"What happened: {e.details}")
        print(f"How to fix: {e.suggestion}")
        if e.technical_details:
            print(f"Debug info: {e.technical_details}")
        if e.problematic_query:
            print(f"Failed query: {e.problematic_query}")
    
    print("\n✓ Test passed!")


def test_network_error():
    """Test network error format"""
    print("\n" + "=" * 60)
    print("Test 5: Network error (no status code)")
    print("=" * 60)
    
    error = ArcaAPIError(message="Network error: Connection refused")
    
    print("\n--- Full error message ---")
    print(str(error))
    
    assert error.status_code is None
    assert "Network error" in error.message
    
    print("\n✓ Test passed!")


if __name__ == "__main__":
    print("\n🧪 Running Arca SDK Error Handling Tests\n")
    
    test_arca_api_error_with_all_fields()
    test_arca_api_error_partial_fields()
    test_arca_api_error_minimal()
    test_exception_catching_pattern()
    test_network_error()
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
