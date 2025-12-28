import sys
from importlib.metadata import version as v

# This ternary allows us to run pytest without installing the module.
__version__ = v(__package__) if "pytest" not in sys.modules else "0.0.0"


_user_agent = f"WallarooSDK/{__version__}"
