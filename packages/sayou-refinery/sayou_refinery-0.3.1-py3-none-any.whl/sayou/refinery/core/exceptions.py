from sayou.core.exceptions import SayouCoreError


class RefineryError(SayouCoreError):
    """
    Base exception for all errors within the sayou-refinery toolkit.
    """

    pass


class NormalizationError(RefineryError):
    """
    Raised when raw data cannot be converted to SayouBlocks.
    (e.g., Malformed JSON, Unsupported format)
    """

    pass


class ProcessingError(RefineryError):
    """
    Raised when a processor fails to clean or transform blocks.
    (e.g., PII masking failure, Imputation rule error)
    """

    pass
