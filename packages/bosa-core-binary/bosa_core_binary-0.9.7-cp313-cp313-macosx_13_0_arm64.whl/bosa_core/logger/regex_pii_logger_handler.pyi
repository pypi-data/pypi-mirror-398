import logging
from _typeshed import Incomplete

class RegexLoggerHandler(logging.Handler):
    """Handler for preprocessing log messages using regex."""
    REGEX_KTP: Incomplete
    REGEX_NPWP: Incomplete
    REGEX_PHONE_NUMBER: Incomplete
    REGEX_EMAIL_ADDRESS: Incomplete
    pii_regex_process_enabled: Incomplete
    def __init__(self, pii_regex_process_enabled: bool = False) -> None:
        """Initialize the handler.

        Args:
            pii_regex_process_enabled (bool): Flag to enable regex processing.
        """
    def process_message_using_regex(self, message: str) -> str:
        """Process message through regex and return modified message.

        Args:
            message (str): The log message to process.

        Returns:
         str: The processed message.
        """
    def mask_ktp_number(self, ktp_number: str) -> str:
        """Mask the KTP number to show only the first 2 and last 2 digits.

        Args:
            ktp_number (str): The KTP number to mask.

        Returns:
            str: The masked KTP number.
        """
    def mask_npwp_number(self, npwp_number: str) -> str:
        """Mask the NPWP number to show only the first 2 and last 2 digits.

        Args:
            npwp_number (str): The NPWP number to mask.

        Returns:
            str: The masked NPWP number.
        """
    def mask_phone_number(self, phone_number: str) -> str:
        """Mask the phone number to show only the first 4 and last 4 digits.

        Args:
            phone_number (str): The phone number to mask.

        Returns:
            str: The masked phone number.
        """
    def mask_email_address(self, email_address: str) -> str:
        """Mask the email address to show only the first 2 and last 2 characters.

        Args:
            email_address (str): The email address to mask.

        Returns:
            str: The masked email address.
        """
    def emit(self, record: logging.LogRecord):
        """Emit the log record.

        Args:
            record (LogRecord): The log record to emit.
        """

def init_regex_pii_logging_handler(logger_name: str, pii_regex_process_enabled: bool = False) -> None:
    """Initialize the NER PII logging handler.

    Args:
        logger_name (str): The name of the logger.
        pii_regex_process_enabled (bool): Flag to enable regex processing.

    Returns:
        NerLoggerHandler: The initialized NER PII logging handler.
    """
