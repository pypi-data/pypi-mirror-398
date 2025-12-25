import logging
from _typeshed import Incomplete

class NerLoggerHandler(logging.Handler):
    """Handler for preprocessing log messages using NER."""
    api_url: Incomplete
    api_field: Incomplete
    pii_ner_process_enabled: Incomplete
    def __init__(self, api_url: str, api_field: str, pii_ner_process_enabled: bool = False) -> None:
        """Initialize the handler.

        Args:
            api_url (str): The URL of the NER API.
            api_field (str): The field name for the NER API.
            pii_ner_process_enabled (bool): Flag to enable NER processing.
        """
    def process_message_using_ner(self, message: str) -> str:
        """Process message through NER API and return modified message.

        Args:
            message (str): The log message to process.

        Returns:
            str: The processed message.
        """
    def emit(self, record: logging.LogRecord):
        """Emit the log record.

        Args:
            record (LogRecord): The log record to emit.
        """

def init_ner_pii_logging_handler(logger_name: str, api_url: str, api_field: str, pii_ner_process_enabled: bool = False) -> None:
    """Initialize the NER PII logging handler.

    Args:
        logger_name (str): The name of the logger.
        api_url (str): The URL of the NER API.
        api_field (str): The field name for the NER API.
        pii_ner_process_enabled (bool): Flag to enable NER processing.

    Returns:
        NerLoggerHandler: The initialized NER PII logging handler.
    """
