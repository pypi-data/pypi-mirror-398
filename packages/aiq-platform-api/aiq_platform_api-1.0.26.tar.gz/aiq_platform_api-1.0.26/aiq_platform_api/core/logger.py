import logging

from IPython import get_ipython


class AttackIQLogger:
    """Logger for AttackIQ platform.

    This class provides a logger for the AttackIQ platform.
    It handles logging to the console and Jupyter notebooks.
    """

    _instances = {}

    @classmethod
    def get_logger(cls, name: str = None) -> logging.Logger:
        if name not in cls._instances:
            logger = logging.getLogger(name)
            logger.setLevel(logging.INFO)
            logger.propagate = False

            for handler in logger.handlers[:]:
                logger.removeHandler(handler)

            if cls.is_jupyter():
                handler = cls.NotebookHandler()
            else:
                handler = logging.StreamHandler()

            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)

            cls._instances[name] = logger

        return cls._instances[name]

    @staticmethod
    def is_jupyter():
        try:
            shell = get_ipython().__class__.__name__
            return shell == "ZMQInteractiveShell"
        except NameError:
            return False

    class NotebookHandler(logging.Handler):
        def emit(self, record):
            from IPython.display import display, HTML

            log_entry = self.format(record)
            color = "white"
            if record.levelno >= logging.ERROR:
                color = "red"
            elif record.levelno >= logging.WARNING:
                color = "orange"
            display(HTML(f'<pre style="color: {color}">{log_entry}</pre>'))


logger = AttackIQLogger.get_logger(__name__)
