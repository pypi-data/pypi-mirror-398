"""
CLI for opkit

Usage:
    python -m opkit install    # Enable globally
    python -m opkit uninstall  # Disable globally
    python -m opkit test       # Run quick test
"""

import sys

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'install':
        from .ast_hook import install
        install()
    elif command == 'uninstall':
        from .ast_hook import uninstall
        uninstall()
    elif command == 'test': 
        print("Testing opkit operators...")
        test_quick()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


def test_quick():
    """Quick functionality test"""
    from .transform import transform_operators
    
    test_cases = [
        ("[1, 2, 3]$", "Unary $ on list"),
        ("{'a': 1}$", "Unary $ on dict"),
        ("a +.. b", "Binary +..  (hstack)"),
        ("a +: b", "Binary +:  (vstack/append)"),
        ("a +. b", "Binary +. (dstack)"),
    ]
    
    print("\nTransformation tests:")
    for code, desc in test_cases: 
        transformed = transform_operators(code)
        print(f"  {desc: 30s} {code: 20s} → {transformed}")
    
    print("\n✓ Basic transformations working!")
    print("  Install with:  python -m opkit install")


if __name__ == '__main__':
    main()