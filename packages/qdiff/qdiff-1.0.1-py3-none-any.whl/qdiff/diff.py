from abc import ABC, abstractmethod


class Diff(ABC):
    @abstractmethod
    def diff(self, path1, path2, output_path):
        pass

