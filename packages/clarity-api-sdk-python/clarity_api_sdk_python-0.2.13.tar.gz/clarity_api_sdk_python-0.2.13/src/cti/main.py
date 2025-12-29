"""Example"""

import logging

from cti.logger import initialize_logger, get_logger, ExternalLoggerConfig

initialize_logger(
    external_logger_configurations=[
        ExternalLoggerConfig(name="urllib3"),
        ExternalLoggerConfig(name="httpcore"),
        ExternalLoggerConfig(name="httpx"),
        ExternalLoggerConfig(name="httpx_auth"),
        ExternalLoggerConfig(name="httpx_retries"),
    ]
)

logger_a = get_logger("logger_a")
logger_b = get_logger("logger_b", "WARNING")

# root_logger = logging.getLogger()
# root_logger.setLevel("DEBUG")

logger_a.info("This is info message from logger_a")
logger_a.critical("This is critical message from logger_a")

# Dynamically change the log level of logger_a to WARNING
print("\nChanging logger_a level to WARNING...\n")
logging.getLogger("logger_a").setLevel(logging.WARNING)

logger_a.info("This info message from logger_a should NOT be visible.")
logger_a.warning("This is a new warning message from logger_a.")

logger_b.warning("This is warning message from logger_b")
