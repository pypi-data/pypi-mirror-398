"""Custom logging filters to reduce log noise."""
import logging

class HealthCheckFilter(logging.Filter):
    """A custom log filter to suppress successful health check endpoint logs."""

    def __init__(self, path: str):
        """Initialize the filter with the path of the health check endpoint."""
        super().__init__()
        self.path = path

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter out successful log records for the health check endpoint.

        Args:
            record: The log record to be processed.

        Returns:
            False if the record should be suppressed, True otherwise.
        """
        # --- CORRECTED FILTER LOGIC ---
        # The args tuple from uvicorn.access is:
        # (client_addr, method, path, protocol, status_code)
        # We need to check if the tuple has enough elements to avoid an IndexError.
        if record.name == "uvicorn.access" and isinstance(record.args, tuple) and len(record.args) >= 5:
            # Extract the path (at index 2) and status_code (at index 4)
            path = record.args[2]
            status_code = record.args[4]

            # Check for the specific health check path and a 200 status code
            if path == self.path and status_code == 200:
                return False

        # Allow all other log records to pass
        return True