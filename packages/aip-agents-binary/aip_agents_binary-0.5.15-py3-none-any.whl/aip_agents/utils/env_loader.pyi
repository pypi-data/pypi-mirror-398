from _typeshed import Incomplete

logger: Incomplete

def load_local_env(override: bool = True) -> None:
    """Load environment variables from a .env file if python-dotenv is available.

    Args:
        override (bool, optional): Whether to override existing environment variables. Defaults to True.
    """
