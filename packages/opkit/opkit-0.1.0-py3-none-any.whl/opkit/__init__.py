"""
opkit: Custom operators for NumPy and Pandas

After installation, all Python code in this environment supports custom operators. 
No special headers needed! 

Installation:
    pip install opkit
    python -m opkit install

For Jupyter: 
    pip install opkit[jupyter]
    %load_ext opkit
"""

__version__ = '0.1.0'
__all__ = ['activate', 'transform_operators', 'install', 'uninstall']

from .transform import transform_operators
from .ast_hook import install, uninstall

# Auto-activate when imported
_activated = False

def activate():
    """Activate opkit AST transformation globally"""
    global _activated
    if _activated:
        return
    
    import sys
    import os
    import builtins
    from .ast_hook import OpkitImportHook
    
    # Check for opt-out
    if os.environ.get('OPKIT_DISABLE_SITECUSTOMIZE') == '1':
        return
    
    # Install import hook for imported modules
    hook = OpkitImportHook()
    sys.meta_path.insert(0, hook)
    
    # Register operators in builtins
    from . import numpy_ops, pandas_ops, runtime_ops
    
    # Hook compile() for REPL and dynamic code
    _original_compile = builtins.compile
    
    def opkit_compile(source, filename, mode, flags=0, dont_inherit=False, optimize=-1, *, _feature_version=-1):
        """Compile with opkit syntax transformation"""
        if isinstance(source, str):
            try:
                transformed = transform_operators(source)
                return _original_compile(transformed, filename, mode, flags, dont_inherit, optimize, _feature_version=_feature_version)
            except Exception:
                pass
        return _original_compile(source, filename, mode, flags, dont_inherit, optimize, _feature_version=_feature_version)
    
    builtins.compile = opkit_compile
    
    # Hook eval() to work with compile hook
    _original_eval = builtins.eval
    
    def opkit_eval(source, globals=None, locals=None):
        """eval() with opkit syntax transformation"""
        if isinstance(source, str):
            try:
                # Compile will use our hooked compile function
                code = compile(source, '<string>', 'eval')
                return _original_eval(code, globals, locals)
            except Exception:
                pass
        return _original_eval(source, globals, locals)
    
    builtins.eval = opkit_eval
    
    # Hook sys.excepthook to catch syntax errors in scripts AND REPL
    _original_excepthook = sys.excepthook
    
    def opkit_excepthook(exc_type, exc_value, tb):
        """Catch syntax errors in scripts/REPL and retry with transformation"""
        if exc_type is SyntaxError:
            # Handle script files
            if exc_value.filename and not exc_value.filename.startswith('<') and os.path.isfile(exc_value.filename):
                try:
                    with open(exc_value.filename, 'r') as f:
                        source = f.read()
                    transformed = transform_operators(source)
                    code = compile(transformed, exc_value.filename, 'exec')
                    namespace = {
                        '__name__': '__main__',
                        '__file__': exc_value.filename,
                        '__cached__': None,
                        '__doc__': None,
                        '__loader__': None,
                        '__package__': None,
                        '__spec__': None,
                    }
                    exec(code, namespace)
                    sys.exit(0)
                except Exception:
                    pass
            
            # Handle REPL input (stdin/console)
            elif exc_value.filename in ('<stdin>', '<console>') and exc_value.text:
                try:
                    transformed = transform_operators(exc_value.text)
                    code = compile(transformed, exc_value.filename, 'single')
                    exec(code)
                    return  # Don't show the error if transformation succeeded
                except Exception:
                    pass
        
        # Fall back to original handler
        _original_excepthook(exc_type, exc_value, tb)
    
    sys.excepthook = opkit_excepthook
    
    # Setup REPL transformation if starting in interactive mode
    if not hasattr(sys, '_opkit_repl_installed'):
        sys._opkit_repl_installed = True
        _install_repl_hook()
    
    _activated = True


def _install_repl_hook():
    """Install REPL hook that will activate when interactive mode starts"""
    import sys
    
    # Register to check when interpreter is ready
    if hasattr(sys, '__interactivehook__'):
        _original_interactive_hook = sys.__interactivehook__
        def opkit_interactive_hook():
            if _original_interactive_hook:
                try:
                    _original_interactive_hook()
                except Exception:
                    pass
            _setup_interactive_console()
        sys.__interactivehook__ = opkit_interactive_hook


def _setup_interactive_console():
    """Replace the interactive console with one that transforms input"""
    import sys
    import code
    
    # Only do this once
    if hasattr(sys, '_opkit_console_replaced'):
        return
    sys._opkit_console_replaced = True
    
    class OpkitConsole(code.InteractiveConsole):
        """Interactive console that transforms opkit syntax"""
        
        def runsource(self, source, filename="<console>", symbol="single"):
            """Override to transform source before compilation"""
            try:
                # Try to transform the source
                transformed = transform_operators(source)
                return super().runsource(transformed, filename, symbol)
            except Exception:
                # If transformation fails, try original source
                return super().runsource(source, filename, symbol)
    
    # Start the custom console
    import __main__
    console = OpkitConsole(__main__.__dict__)
    
    try:
        console.interact(banner="")
    except SystemExit:
        pass
    
    # Exit after custom console exits
    sys.exit(0)


# Activate automatically when imported
activate()