from _typeshed import Incomplete
from bosa_core import ConfigService as ConfigService
from bosa_core.cache import CacheService as CacheService
from bosa_server_plugins.common.cache import serialize_cache_data as serialize_cache_data
from bosa_server_plugins.google.auth.auth import GoogleCredentials as GoogleCredentials
from bosa_server_plugins.google_mail.constants import GMAIL_LABEL_STATS_AUTH_KEY_FORMAT as GMAIL_LABEL_STATS_AUTH_KEY_FORMAT, GMAIL_LABEL_STATS_CACHE_KEY as GMAIL_LABEL_STATS_CACHE_KEY, GMAIL_LABEL_STATS_CACHE_TTL as GMAIL_LABEL_STATS_CACHE_TTL
from bosa_server_plugins.google_mail.services.labels import GoogleMailLabelsService as GoogleMailLabelsService

logger: Incomplete

def compute_label_stats_task(email: str) -> tuple[dict, str | None]:
    """Compute Gmail label statistics for a user and cache the results.

    Args:
        email (str): The user's email address used for cache scoping.

    Returns:
        tuple[dict, str | None]: A tuple containing the computed summary and an error message if any.
    """
def get_label_stats_cache_key(email: str) -> str:
    """Construct the cache key for label stats based on the email address.

    Args:
        email (str): The user's email address used for cache scoping.

    Returns:
        str: The cache key for label stats.
    """
def get_label_stats_auth_key(email: str) -> str:
    """Construct the auth key for label stats based on the email address.

    Args:
        email (str): The user's email address used for cache scoping.

    Returns:
        str: The auth key for label stats.
    """
