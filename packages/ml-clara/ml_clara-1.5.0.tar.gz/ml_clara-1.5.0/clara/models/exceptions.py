"""
Model loading exceptions.

Custom exceptions for model loading, adapter merging, and related operations.
"""


class ModelNotFoundError(Exception):
    """
    Raised when no model path is specified.

    Neither local_path nor hf_id was provided in the configuration.
    """

    def __init__(self, message: str = "No model path specified"):
        self.message = message
        super().__init__(self.message)


class ModelLoadError(Exception):
    """
    Raised when model loading fails.

    This can happen due to:
    - Invalid model path
    - Corrupted checkpoint
    - Network errors (HuggingFace download)
    - Incompatible model format
    - Out of memory
    """

    def __init__(self, message: str, cause: Exception | None = None):
        self.message = message
        self.cause = cause
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.cause:
            return f"{self.message}: {self.cause}"
        return self.message


class AdapterIncompatibleError(Exception):
    """
    Raised when an adapter is incompatible with the base model.

    This can happen due to:
    - Shape mismatch (different hidden dimensions)
    - Architecture mismatch
    - Missing target modules
    - Dtype incompatibility
    """

    def __init__(
        self,
        message: str,
        adapter_path: str | None = None,
        base_model: str | None = None,
    ):
        self.message = message
        self.adapter_path = adapter_path
        self.base_model = base_model
        super().__init__(self.message)

    def __str__(self) -> str:
        parts = [self.message]
        if self.adapter_path:
            parts.append(f"Adapter: {self.adapter_path}")
        if self.base_model:
            parts.append(f"Base model: {self.base_model}")
        return " | ".join(parts)


class TokenizerError(Exception):
    """
    Raised when tokenizer loading or operation fails.
    """

    def __init__(self, message: str, cause: Exception | None = None):
        self.message = message
        self.cause = cause
        super().__init__(self.message)


class ChecksumConfigError(ValueError):
    """Raised when checksum configuration is invalid or incomplete."""


class ChecksumMismatchError(Exception):
    """Raised when a file's SHA256 does not match the expected value."""

    def __init__(self, path: str, expected_sha256: str, actual_sha256: str):
        self.path = path
        self.expected_sha256 = expected_sha256
        self.actual_sha256 = actual_sha256
        super().__init__(self.__str__())

    def __str__(self) -> str:
        return (
            f"Checksum mismatch for {self.path}: "
            f"expected sha256={self.expected_sha256}, got sha256={self.actual_sha256}"
        )
