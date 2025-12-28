import logging

from rich.logging import RichHandler

logging.getLogger("httpx").setLevel(logging.ERROR)

_logger_name = 'pantoqa.automations'


def setup_logger():
  formatter = logging.Formatter('%(levelname)s: %(asctime)s %(filename)s:%(lineno)d %(message)s')
  loghandler = logging.StreamHandler()

  logger = logging.getLogger(_logger_name)
  logger.setLevel(logging.INFO)
  loghandler.setFormatter(formatter)
  logger.addHandler(loghandler)
  logger.propagate = False
  return logger


def setup_logger_cli():
  formatter = logging.Formatter("%(message)s")
  loghandler = RichHandler(
    markup=True,
    rich_tracebacks=False,
    show_time=False,
    show_path=False,
  )

  logger = logging.getLogger(_logger_name)
  logger.setLevel(logging.INFO)
  loghandler.setFormatter(formatter)
  logger.addHandler(loghandler)
  logger.propagate = False
  return logger


logger = setup_logger_cli()
