import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OneHotEncoder  # One hot encoding for model binary creation of my array when passing it in
from collections.abc import Callable
from typing import Any, TypeVar, List, Dict

generic_type = TypeVar("T")

class Model_Evaluator:
    """Runs predictions over rows and computes metrics."""
    def __init__(
        self,
        predict: List[generic_type],
        metrics: Dict[str, generic_type],
    ) -> None:  # Not sure of inputs or returns yet
        self.predict = predict
        self.metrics = metrics
    def rating_check(self):
        pass
