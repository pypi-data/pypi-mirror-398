from enum import Enum

class ArchitectureFlags(Enum):
    """
    Architecture configuration flags for optional components.

    :param SKIP_DATABASE: Skip database creation
    :param SKIP_DOMAIN: Skip domain and DNS configuration
    :param SKIP_DEFAULT_POST_APPLY_SCRIPTS: Skip default post-apply scripts
    :param SKIP_SSL_CERT: Skip SSL certificate creation
    """

    SKIP_DATABASE = "skip_database"
    SKIP_DOMAIN = "skip_domain"
    SKIP_DEFAULT_POST_APPLY_SCRIPTS = "skip_default_post_apply_scripts"
    SKIP_SSL_CERT = "skip_ssl_cert"