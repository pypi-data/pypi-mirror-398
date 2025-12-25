import logging, sys

LEVELS = {"CRITICAL":50,"ERROR":40,"WARNING":30,"INFO":20,"DEBUG":10}

def setup_logging(level: str = "INFO") -> None:
  root = logging.getLogger()
  if root.handlers:
    root.setLevel(LEVELS.get(level.upper(), 20))
    return
  h = logging.StreamHandler(sys.stdout)
  h.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-5s | %(name)s | %(message)s"))
  root.addHandler(h)
  root.setLevel(LEVELS.get(level.upper(), 20))

def get_logger(name: str) -> logging.Logger:
  return logging.getLogger(name)
