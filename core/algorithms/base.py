# core/algorithms/base.py
from abc import ABC, abstractmethod

class AlgorithmBase(ABC):
    name = "Base"

    @abstractmethod
    def run(self, records, output_folder=None, dark_enabled=False):
        """
        records: List[dict]，每条 dict 包含 wavelength, data, filename 等
        output_folder: str
        dark_enabled: bool
        return:
            dict:
                curves: List[tuple] -> [(x, y, label), ...]
                log: str
        """
        raise NotImplementedError
