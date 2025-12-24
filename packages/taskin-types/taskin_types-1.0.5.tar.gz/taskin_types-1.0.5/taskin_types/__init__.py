"""Taskin Python type definitions auto-generated from TypeScript schemas."""

from pathlib import Path
import sys

# Add generated directory to path
generated_dir = Path(__file__).parent.parent / "generated"
sys.path.insert(0, str(generated_dir))

# Import all generated models
try:
    from task import *  # noqa: F401, F403
    from user import *  # noqa: F401, F403
except ImportError:
    # If generated files don't exist, provide helpful error
    raise ImportError(
        "Generated Python models not found. "
        "Please run 'pnpm build' in the types-py package."
    )

__version__ = "1.0.5"
__all__ = ["Task", "User"]
