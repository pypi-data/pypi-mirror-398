class ConfigurationKeyNotFoundError(Exception):
    """Key not found in configuration exception."""

    def __init__(
        self: "ConfigurationKeyNotFoundError",
        message: str = "Key not found in configuration.",
    ) -> None:
        super().__init__(message)
