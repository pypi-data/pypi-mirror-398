"""
Solvien Graph - Import Tests
============================
Tests both new import style and backward compatibility.
"""

import sys


def test_biograph_import():
    """Test: import solvien_graph.biograph as bg"""
    print("Test 1: New import style")
    print("=" * 50)
    try:
        import solvien_graph.biograph as bg
        print("✅ import solvien_graph.biograph as bg - SUCCESS")
        print(f"   Available functions: {bg.__all__}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_alternative_import():
    """Test: from solvien_graph import biograph as bg"""
    print("\nTest 2: Alternative import style")
    print("=" * 50)
    try:
        from solvien_graph import biograph as bg
        print("✅ from solvien_graph import biograph as bg - SUCCESS")
        print(f"   Available functions: {bg.__all__}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_direct_function_import():
    """Test: from solvien_graph.biograph import quick_heatmap, quick_volcano"""
    print("\nTest 3: Direct function import from biograph")
    print("=" * 50)
    try:
        from solvien_graph.biograph import quick_heatmap, quick_volcano
        print("✅ from solvien_graph.biograph import quick_heatmap, quick_volcano - SUCCESS")
        print(f"   quick_heatmap: {quick_heatmap}")
        print(f"   quick_volcano: {quick_volcano}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_backward_compatibility():
    """Test: from solvien_graph import quick_heatmap (old style)"""
    print("\nTest 4: Backward compatibility (old import style)")
    print("=" * 50)
    try:
        from solvien_graph import quick_heatmap
        print("✅ from solvien_graph import quick_heatmap - SUCCESS (backward compatible)")
        print(f"   quick_heatmap: {quick_heatmap}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_main_module():
    """Test: Check biograph in main module"""
    print("\nTest 5: Check biograph in main module")
    print("=" * 50)
    try:
        import solvien_graph as sg
        print("✅ solvien_graph imported")
        print(f"   Has biograph attribute: {hasattr(sg, 'biograph')}")
        if hasattr(sg, 'biograph'):
            print(f"   sg.biograph: {sg.biograph}")
            print(f"   sg.biograph.__all__: {sg.biograph.__all__}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def run_all_tests():
    """Run all import tests"""
    print("=" * 60)
    print("Solvien Graph - Import Tests")
    print("=" * 60)
    
    results = [
        test_biograph_import(),
        test_alternative_import(),
        test_direct_function_import(),
        test_backward_compatibility(),
        test_main_module()
    ]
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    return all(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
