import logging

from fluidattacks_core.logging.sources.utils import get_environment


class NoProductionFilter(logging.Filter):
    def filter(self, _record: logging.LogRecord) -> bool:
        return get_environment() != "production"


class ProductionOnlyFilter(logging.Filter):
    def filter(self, _record: logging.LogRecord) -> bool:
        return get_environment() == "production"
