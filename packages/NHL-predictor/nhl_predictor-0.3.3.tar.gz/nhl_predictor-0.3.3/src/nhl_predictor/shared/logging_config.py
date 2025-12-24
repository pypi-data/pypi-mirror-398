import logging

from pythonjsonlogger import jsonlogger


class LoggingConfig:
    """Class to manage logging configuration.
    """

    @staticmethod
    def get_logger(name: str):
        """Get a logger with the provided name.

        Args:
            name (str): Logger name.

        Returns:
            _type_: A properly configured logging object.
        """
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)

        # If logger with name was already created, don't muck with the handlers
        if not logger.handlers:
            handler = logging.FileHandler("buildData.log", 'w+')
            formatter = jsonlogger.JsonFormatter("%(asctime)s %(name)s %(levelname)s %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger