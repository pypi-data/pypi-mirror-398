"""
Solvien Graph - Annotation Tests
================================
Tests publication quality annotations on various chart types.
"""

import sys
import numpy as np


def test_volcano_annotations():
    """Test volcano plot with statistical annotations"""
    print("1. Volcano Plot with statistical annotations...")
    try:
        import solvien_graph.biograph as bg
        
        np.random.seed(42)
        n_genes = 200
        log2fc = np.random.randn(n_genes) * 2
        pvalues = np.random.exponential(0.1, n_genes)
        pvalues = np.clip(pvalues, 1e-10, 1)
        
        bg.quick_volcano(
            log2fc=log2fc,
            pvalue=pvalues,
            title="Volcano Plot - Publication Quality",
            fc_threshold=1.0,
            pvalue_threshold=0.05,
            publication_quality=True,
            show=True
        )
        print("✅ Volcano plot annotations test passed")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_violin_annotations():
    """Test violin plot with mean value annotations"""
    print("\n2. Violin Plot with mean value annotations...")
    try:
        import solvien_graph.biograph as bg
        
        np.random.seed(42)
        data_dict = {
            "Control": np.random.normal(5, 1, 100),
            "Treatment A": np.random.normal(6.5, 1.2, 100),
            "Treatment B": np.random.normal(4.5, 0.8, 100)
        }
        
        bg.quick_violin(
            data_dict=data_dict,
            title="Violin Plot - Publication Quality",
            publication_quality=True,
            show=True
        )
        print("✅ Violin plot annotations test passed")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_boxplot_annotations():
    """Test box plot with median value annotations"""
    print("\n3. Box Plot with median value annotations...")
    try:
        import solvien_graph.biograph as bg
        
        np.random.seed(42)
        data_dict = {
            "Control": np.random.normal(5, 1, 100),
            "Treatment A": np.random.normal(6.5, 1.2, 100),
            "Treatment B": np.random.normal(4.5, 0.8, 100)
        }
        
        bg.quick_boxplot(
            data_dict=data_dict,
            title="Box Plot - Publication Quality",
            publication_quality=True,
            show=True
        )
        print("✅ Box plot annotations test passed")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def run_all_tests():
    """Run all annotation tests"""
    print("=" * 70)
    print("Solvien Graph - Publication Quality Annotation Tests")
    print("=" * 70)
    print()
    
    results = [
        test_volcano_annotations(),
        test_violin_annotations(),
        test_boxplot_annotations()
    ]
    
    print()
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("Check the PNG/PDF files to verify annotations are visible.")
    print("=" * 70)
    
    return all(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
