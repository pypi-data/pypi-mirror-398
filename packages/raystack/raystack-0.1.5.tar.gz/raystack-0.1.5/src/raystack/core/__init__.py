try:
    from . import database
except ImportError as e:
    # Log the error but don't fail completely
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Failed to import database module: {e}")

from . import security
# Dependencies are now project-specific, not part of framework core
# Projects should define their own dependencies (e.g., in apps/admin/deps.py)
try:
    from . import dependencies
except ImportError:
    # Dependencies module is optional
    pass