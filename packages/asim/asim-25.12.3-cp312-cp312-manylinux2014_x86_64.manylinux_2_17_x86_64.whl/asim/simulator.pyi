from io import BytesIO
from typing import Dict, Union, List

import numpy as np
import onnxruntime as ort
import pandas as pd

from .dataset import PhysicalDataManage

class PhysicalSimulator:

    _sess: ort.InferenceSession
    _dm: PhysicalDataManage

    def __init__(self, fh: Union[str, BytesIO], dm: PhysicalDataManage):
        """
        init
        """
        ...

    def step(self, x1: Dict[str, np.ndarray], y0: Dict[str, np.ndarray]) -> Dict[str, list]:
        """
        sim.step({"load": 150.0}, {"power1": 60.0, "power2": 80.0})
        """
        ...

    def steps(self, df: pd.DataFrame, x0: Dict[str, float]) -> pd.DataFrame:
        """
        steps
        """
        ...

    def plots(self, df: pd.DataFrame, figsize: tuple[int, int] = (15, 3)) -> None:
        """
        plots
        """
        ...
