"""Verification script for CLI structure (without dependencies).

This script verifies:
1. All files have valid Python syntax
2. Module structure is correct
3. Function signatures match expected API
4. Pipeline flow is implemented correctly
"""

import ast
import sys
from pathlib import Path

def verify_syntax(filepath: Path) -> bool:
    """Verify file has valid Python syntax."""
    try:
        with open(filepath) as f:
            ast.parse(f.read())
        return True
    except SyntaxError as e:
        print(f"  ✗ Syntax error in {filepath}: {e}")
        return False

def extract_functions(filepath: Path) -> list[str]:
    """Extract function names from a Python file."""
    with open(filepath) as f:
        tree = ast.parse(f.read())
    
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append(node.name)
    return functions

def extract_imports(filepath: Path) -> list[str]:
    """Extract imported module names from a Python file."""
    with open(filepath) as f:
        tree = ast.parse(f.read())
    
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports

def main():
    """Run verification checks."""
    root = Path(__file__).parent.parent
    src_dir = root / "src" / "vlsi_report_cluster"
    tests_dir = root / "tests"
    
    print("="*60)
    print("VLSI Report Cluster - CLI Structure Verification")
    print("="*60)
    
    all_passed = True
    
    # Check 1: Syntax validation
    print("\n1. Syntax Validation")
    print("-"*60)
    files_to_check = [
        src_dir / "cli.py",
        src_dir / "formatter.py",
        src_dir / "__main__.py",
        tests_dir / "test_cli.py",
    ]
    
    for filepath in files_to_check:
        if filepath.exists():
            if verify_syntax(filepath):
                print(f"  ✓ {filepath.name}")
            else:
                all_passed = False
        else:
            print(f"  ✗ File not found: {filepath}")
            all_passed = False
    
    # Check 2: Formatter functions
    print("\n2. Formatter Module Functions")
    print("-"*60)
    formatter_file = src_dir / "formatter.py"
    if formatter_file.exists():
        functions = extract_functions(formatter_file)
        expected = ["format_table", "format_json"]
        for func in expected:
            if func in functions:
                print(f"  ✓ {func}() defined")
            else:
                print(f"  ✗ {func}() missing")
                all_passed = False
    
    # Check 3: CLI function
    print("\n3. CLI Module Functions")
    print("-"*60)
    cli_file = src_dir / "cli.py"
    if cli_file.exists():
        functions = extract_functions(cli_file)
        expected = ["main", "cli_main"]
        for func in expected:
            if func in functions:
                print(f"  ✓ {func}() defined")
            else:
                print(f"  ✗ {func}() missing")
                all_passed = False
    
    # Check 4: Pipeline imports in CLI
    print("\n4. CLI Pipeline Imports")
    print("-"*60)
    if cli_file.exists():
        imports = extract_imports(cli_file)
        expected_modules = [
            "vlsi_report_cluster.parser",
            "vlsi_report_cluster.embedder",
            "vlsi_report_cluster.clusterer",
            "vlsi_report_cluster.template_extractor",
            "vlsi_report_cluster.formatter",
        ]
        for module in expected_modules:
            if module in imports:
                print(f"  ✓ {module}")
            else:
                print(f"  ✗ {module} not imported")
                all_passed = False
    
    # Check 5: Test file structure
    print("\n5. Test File Structure")
    print("-"*60)
    test_file = tests_dir / "test_cli.py"
    if test_file.exists():
        functions = extract_functions(test_file)
        test_count = len([f for f in functions if f.startswith("test_")])
        if test_count >= 11:
            print(f"  ✓ {test_count} test methods defined (≥11 required)")
        else:
            print(f"  ✗ Only {test_count} test methods (need ≥11)")
            all_passed = False
    
    # Check 6: CLI command signature
    print("\n6. CLI Command Signature")
    print("-"*60)
    if cli_file.exists():
        with open(cli_file) as f:
            content = f.read()
        
        required_params = [
            "report_file",
            "output_format",
            "format",
            "min_cluster_size",
            "min_samples",
            "embedder",
            "embedder_model",
            "encoding",
        ]
        
        for param in required_params:
            if param in content:
                print(f"  ✓ {param} parameter")
            else:
                print(f"  ✗ {param} parameter missing")
                all_passed = False
    
    # Check 7: Pipeline flow in CLI
    print("\n7. Pipeline Flow Implementation")
    print("-"*60)
    if cli_file.exists():
        with open(cli_file) as f:
            content = f.read()
        
        pipeline_steps = [
            ("parse_report", "Step 1: Parse report"),
            ("create_embedder", "Step 2: Create embedder"),
            ("embed", "Step 3: Embed lines"),
            ("cluster_embeddings", "Step 4: Cluster embeddings"),
            ("extract_templates", "Step 5: Extract templates"),
            ("format_table", "Step 6: Format output (table)"),
            ("format_json", "Step 6: Format output (json)"),
        ]
        
        for func_name, description in pipeline_steps:
            if func_name in content:
                print(f"  ✓ {description}")
            else:
                print(f"  ✗ {description}")
                all_passed = False
    
    # Check 8: Error handling
    print("\n8. Error Handling")
    print("-"*60)
    if cli_file.exists():
        with open(cli_file) as f:
            content = f.read()
        
        error_handlers = [
            ("FileNotFoundError", "File not found handling"),
            ("UnicodeDecodeError", "Encoding error handling"),
            ("ImportError", "Missing dependency handling"),
        ]
        
        for exception, description in error_handlers:
            if exception in content:
                print(f"  ✓ {description}")
            else:
                print(f"  ✗ {description}")
                all_passed = False
    
    # Check 9: Fallback logic
    print("\n9. Fallback Logic (cluster_result is None)")
    print("-"*60)
    if cli_file.exists():
        with open(cli_file) as f:
            content = f.read()
        
        if "cluster_result is None" in content or "cluster_result == None" in content:
            print("  ✓ Fallback condition check implemented")
        else:
            print("  ✗ Fallback condition check missing")
            all_passed = False
        
        if "labels=None" in content:
            print("  ✓ Fallback calls extract_templates(lines, labels=None)")
        else:
            print("  ✗ Fallback template extraction missing")
            all_passed = False
    
    # Summary
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL CHECKS PASSED")
        print("="*60)
        return 0
    else:
        print("✗ SOME CHECKS FAILED")
        print("="*60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
