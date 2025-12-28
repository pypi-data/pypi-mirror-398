from abc import ABC, abstractmethod
from enum import Enum


class RenderFormat(Enum):
    SHORT = "short"
    LONG = "long"


class Summarization(Enum):
    MAX = "max"
    MIN = "min"
    AVERAGE = "average"
    MEDIAN = "median"


class VyomDataType(ABC):
    data_type = None

    @staticmethod
    @abstractmethod
    def render(format=RenderFormat.SHORT):
        """
        Abstract static method to render the data.
        Must be implemented by subclasses.
        """
        pass

    @staticmethod
    @abstractmethod
    def form_widget():
        """
        Abstract static method to return a react-widget.
        Must be implemented by subclasses.
        """
        pass

    @staticmethod
    @abstractmethod
    def summarize(summarization):
        """
        Abstract static method to summarize the data.
        Must be implemented by subclasses.
        """
        pass
