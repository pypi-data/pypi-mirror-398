"""
Request timeout in seconds for Looker API
"""

LOOKER_ENV_PREFIX = "CASTOR_LOOKER_"

DEFAULT_LOOKER_TIMEOUT_SECOND = 120
"""
Number of items per page when requesting Looker API
"""
DEFAULT_LOOKER_PAGE_SIZE = 500
"""
Maximum concurrent threads to run when fetching
"""
DEFAULT_LOOKER_THREAD_POOL_SIZE = 20
MIN_THREAD_POOL_SIZE = 1
MAX_THREAD_POOL_SIZE = 200
