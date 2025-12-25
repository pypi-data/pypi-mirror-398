from abc import ABC


class BaseCronTask(ABC):
    name: str

    @staticmethod
    def run(*args, **kwargs):
        ...
