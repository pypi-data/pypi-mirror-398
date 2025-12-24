"""
IPython/Jupyter extension for opkit

Usage in Jupyter:
    %load_ext opkit
"""

try:
    from IPython.core.inputtransformer2 import StatelessInputTransformer
    IPYTHON_AVAILABLE = True
except ImportError:
    IPYTHON_AVAILABLE = False
    class StatelessInputTransformer: 
        @staticmethod
        def wrap(func):
            return func

from .transform import transform_operators

@StatelessInputTransformer.wrap
def opkit_transformer(lines):
    """Transform opkit syntax in Jupyter cells"""
    source = '\n'.join(lines)
    transformed = transform_operators(source)
    return transformed.split('\n')


def load_ipython_extension(ipython):
    """Load the extension in IPython/Jupyter"""
    if not IPYTHON_AVAILABLE:
        raise ImportError(
            "IPython is not installed. Install with: pip install opkit[jupyter]"
        )
    
    ipython.input_transformers_cleanup.append(opkit_transformer)
    print("✓ opkit operators enabled in Jupyter!")


def unload_ipython_extension(ipython):
    """Unload the extension"""
    if IPYTHON_AVAILABLE:
        ipython.input_transformers_cleanup.remove(opkit_transformer)
        print("✓ opkit operators disabled")