"""
This module contains the objects needed to perform
a multi-criteria analysis for fish passage
on spatially distributed hydrodynamic data.

The module tests are located in the folder:
tests/test_MulticriteriAnalysis.py file,
in HECEPython repository.

Authors: Utashi Ciraane,
HECE, University of Liège, Belgium.
"""
# **************************************************************
# Libraries used throughout the module
# **************************************************************

# To stay inside the HECEPython repository
# ----------------------------------------

# Standard libraries
# -------------------
import logging
import numpy as np
import os

# Cherry-picked objects from standard libraries
# ---------------------------------------------
from enum import Enum
from pathlib import Path
from tqdm import tqdm
from typing import Literal, Union

# Cherry-picked objects from wolfhece
# ------------------------------------
from wolfhece.wolf_array import WolfArray, header_wolf

## **************************************************************
# Constants Used
# **************************************************************
class Operator(Enum):
    """
    Mathematical operators used
    in the module.
    """
    AVERAGE = "average"
    BETWEEN = "between" # Between two limits. The limits are included.
    BETWEEN_STRICT = "strictly between" # Between two limits. The limits are not included.
    EQUAL = "equal"  # Equal to a value.
    INFERIOR = "inferior" # Less than a limit. The limit is not included.
    INFERIOR_OR_EQUAL = "inferior or equal" # Less than or equal to a limit. The limit is included.
    OUTSIDE = "outside" # Outside two limits. The limits are included.
    OUTSIDE_STRICT = "strictly outside" # Outside two limits. The limits are not included.
    PERCENTAGE = "percentage"
    PRODUCT = "product"
    SUM = "sum"
    SUPERIOR = "superior" # Greater than a limit. The limit is not included.
    SUPERIOR_OR_EQUAL = "superior or equal" # Greater than or equal to a limit. The limit is included.
    THRESHOLD = "threshold"
    WEIGHTED_SUM = "weighted sum"

class Format(Enum):
    """
    Types of data formats used in the module.
    """
    FLOAT32 = np.float32  # The float32 data type used in the module.
    FLOAT64 = np.float64  # The float64 data type used in the module.
    INT32 = np.int32  # The int32 data type used in the module.
    INT64 = np.int64  # The int64 data type used in the module.

class Status(Enum):
    """
    Status of objects in the module
    """
    PROGRESS_BAR_DISABLE = False    # Enable or disable the tqdm  progress bars.


class Constant(Enum):
    """
    This class contains the constants used throughout the module.
    """
    EPSG = 31370
    ONE = 1
    ZERO = 0
    CONDITION = "condition"


## **************************************************************
# Classes or Objects used to perform the multi-criteria analysis
## **************************************************************
class Variable:
    """
    This class is used to store variable (data: array)
    that will be used  in the multi-criteria analysis.

    The types of variable allowed are:
        - np.ma.MaskedArray: A numpy masked array.
        - np.ndarray: A numpy array.
        - WolfArray: A WolfArray object from the wolfhece library.
    """
    def __init__(self,
                 variable: np.ma.MaskedArray| np.ndarray| WolfArray,
                 dtype : Union[np.dtype, str] = Format.FLOAT32.value) :
        """
        Initialize the variable with a WolfArray or a numpy array.
        if a type dtype is not provided, it defaults to np.float32.

        :param variable: A WolfArray or a numpy array.
        ::type variable: np.ma.MaskedArray | np.ndarray | WolfArray
        :param dtype: The data type of the variable, defaults to np.float32.
        ::type dtype: Union[np.dtype, str]

        """
        self._variable: np.ma.MaskedArray = None
        self._dtype = dtype
        self.variable = variable



    @property
    def variable(self) -> np.ma.MaskedArray:
        """
        Return the variable.

        :return: The variable as a numpy masked array.
        """
        return self._variable

    @variable.setter
    def variable(self, value: np.ma.MaskedArray| np.ndarray| WolfArray) :
        """
        Set the variable and converts it to a numpy masked array.

        :param value: A WolfArray or a numpy masked array.
        """
        assert isinstance(value, (np.ma.MaskedArray, np.ndarray, WolfArray)), \
            "The variable must be a numpy masked array, a numpy array or a WolfArray."
        if isinstance(value, WolfArray):
            if np.ma.is_masked(value.array):
                value = value.array
            else:
                # If the WolfArray is not masked, create a masked array with no mask.
                mask = np.zeros(value.array.shape, dtype=bool)
                value = np.ma.masked_array(value.array, mask=mask)

        elif isinstance(value, np.ndarray):
            mask =np.zeros(value.shape, dtype=bool)
            value = np.ma.masked_array(value, mask=mask)
        self._variable = value.astype(self._dtype, copy=True)

    @property
    def dtype(self) -> type:
        """
        Return the data type of the variable.

        :return: The data type of the variable.
        """
        return self._variable.dtype

    @dtype.setter
    def dtype(self, value: Union[type, str]) -> None:
        """
        Set the data type of the variable.

        :param value: The data type to set.
        """
        assert isinstance(value, (type, str)), \
            "The data type must be a numpy dtype or a string representing a numpy dtype."
        # if isinstance(value, str):
        #     # value = type(value)

        self._variable = self._variable.astype(value, copy=True)
        self._dtype = value

class Criteria:
    """
    This class is used to define a criteria included in the multi-criteria analysis

    It contains a threshold and a condition:.
        - superior,
        - inferior,
        - equal,
        - superior or equal,
        - inferior or equal,
        - between,
        - strictly between,
        - outside,
        - strictly outside.

    The condition defines how the threshold is applied to select
    values in the variable true (1) or False (0).
    """
    def __init__(self,
                 threshold: Union[float, int, tuple],
                 condition: Literal[Operator.SUPERIOR.value,
                                   Operator.INFERIOR.value,
                                   Operator.SUPERIOR_OR_EQUAL.value,
                                   Operator.INFERIOR_OR_EQUAL.value,
                                   Operator.BETWEEN.value,
                                   Operator.BETWEEN_STRICT.value,
                                   Operator.OUTSIDE.value,
                                   Operator.OUTSIDE_STRICT.value
                                   ] = Operator.SUPERIOR_OR_EQUAL.value) -> dict:
        """
        Return a criteria with a threshold and a condition.

        :param threshold: The threshold value for the criteria.
        :type threshold: float| int|tuple
        :param condition: The condition to select the data around the threshold.
        :type condition: str
        :return: a dictionary containing 2 elements, the threshold and the condition.
        :rtype: dict
        """

        self._available_conditions = [Operator.SUPERIOR.value,
                                   Operator.INFERIOR.value,
                                   Operator.EQUAL.value,
                                   Operator.SUPERIOR_OR_EQUAL.value,
                                   Operator.INFERIOR_OR_EQUAL.value,
                                   Operator.BETWEEN.value,
                                   Operator.BETWEEN_STRICT.value,
                                   Operator.OUTSIDE.value,
                                   Operator.OUTSIDE_STRICT.value
                                   ] # add NOT in method too.
        self._needs_tuple = (Operator.BETWEEN.value,
                        Operator.BETWEEN_STRICT.value,
                        Operator.OUTSIDE.value,
                        Operator.OUTSIDE_STRICT.value)
        self._criteria: dict = {}

        self.threshold = threshold
        self.condition = condition

    @property
    def criteria(self) -> dict:
        """
        Return the criteria.

        :return: The criteria as a dictionary.
        """
        return self._criteria

    @criteria.setter
    def criteria(self,
                 criteria : dict) -> None:
        """
        Set the criteria.

        :param value: The criteria as a dictionary.
        """
        assert isinstance(criteria, dict), f"The criteria must be a dictionary, not {type(criteria)}."
        assert Operator.THRESHOLD.value in criteria,\
            f"The threshold key must be {Operator.THRESHOLD.value } in the criteria dictionary."
        assert Constant.CONDITION.value in criteria,\
            f"The condition key must be {Constant.CONDITION.value} in the criteria dictionary."
        self.threshold = criteria[Operator.THRESHOLD.value]
        self.condition = criteria[Constant.CONDITION.value]

    @property
    def threshold(self) -> float:
        """
        Get the threshold of the criteria.

        :return: The threshold as a float.
        """
        return self._criteria[Operator.THRESHOLD.value]

    @threshold.setter
    def threshold(self, value: float) -> None:
        """
        Set the threshold of the criteria.

        :param value: The threshold to set.
        """
        assert isinstance(value, (float, int, tuple)),\
              f"The threshold must be a float or an int or a tuple of length equals to Two, not a {type(value)} ."
        if isinstance(value, tuple):
            assert len(value) == 2, "The threshold tuple must have exactly two elements."
            assert value[0] <= value[1], "The first element of the threshold tuple must be less than the second element."
            if Constant.CONDITION.value in self._criteria:
                if self.condition not in (self._needs_tuple):
                    value = self._tuple_to_number(value)
                    logging.warning(f"The condition '{self.condition}' does not require a tuple for the threshold. "
                                    f"The threshold will be set to : {value} which i the first value of the tuple.")

        elif isinstance(value, (float, int)):
            if Constant.CONDITION.value in self._criteria:
                if self.condition in self._needs_tuple:
                    logging.warning(f"The condition '{self.condition}' requires a tuple for the threshold. "
                                    f"The threshold will be set to a tuple with the value {value} as both elements.")
                    # Convert single number to tuple
                    value = self._number_to_tuple(value)
        assert isinstance(self._criteria, dict), f"The criteria type must be a dictionary, not {type(self._criteria)}."
        self._criteria[Operator.THRESHOLD.value] = value

    @property
    def condition(self) -> str:
        """
        Get the condition.

        :return: The condition as a string.
        """
        return self._criteria[Constant.CONDITION.value]

    @condition.setter
    def condition(self, value: Literal[Operator.SUPERIOR.value,
                                        Operator.INFERIOR.value,
                                        Operator.EQUAL.value,
                                        Operator.SUPERIOR_OR_EQUAL.value,
                                        Operator.INFERIOR_OR_EQUAL.value,
                                        Operator.BETWEEN.value,
                                        Operator.BETWEEN_STRICT.value
                                        ]) -> None:
        """
        Set the condition.

        :param value: The condition to set.
        """
        assert isinstance(value, str), f"The condition must be a string, not a {type(value)}."
        assert value in self._available_conditions,\
            f"The criteria must be one of the following: {self._available_conditions}."
        self._criteria[Constant.CONDITION.value] = value
        # If the condition is a range condition (between, strictly between, outside, strictly outside),
        # we need to convert the threshold to a tuple if it is not already.
        if value in self._needs_tuple:
            if isinstance(self.threshold, (int, float)):
                # If the threshold is a single number, convert it to a tuple
                self.threshold = self._number_to_tuple(self.threshold)
        else:
            # If the condition does not require a tuple, ensure the threshold is a single number
            if isinstance(self.threshold, tuple):
                self.threshold = self._tuple_to_number(self.threshold)

    def _number_to_tuple(self, value: Union[float, int]) -> tuple:
        """
        Convert a number to a tuple of two elements.

        :param value: The number to convert.
        :return: A tuple with the number as both elements.
        """
        assert isinstance(value, (float, int)), f"The value must be a float or an int, not {type(value)}."
        return (value, value)

    def _tuple_to_number(self, value: tuple) -> float:
        """
        Convert a tuple of two elements to a number.

        :param value: The tuple to convert.
        :return: The first element of the tuple as a float.
        """
        assert isinstance(value, tuple), f"The value must be a tuple, not {type(value)}."
        assert len(value) == 2, "The tuple must have exactly two elements."
        return value[0]

class Score:
    """
    This class  scores a Variable based on the given criteria (threshold & condition).

    The score is a np.MaskedArray with the same shape as the given variable.

    The score contains boolean values indicating whether the variable meets the criteria (1) or (0).
    If the variable is masked, the score is also masked.

    Binary notation was selected to allow mathematical operations.
    """
    def __init__(self,
                 variable: Variable,
                 criteria: Criteria,
                 dtype = Format.INT32.value
                 ) -> None:
        """
        Initialize the score with a variable and a criteria.

        :param variable: The variable (array) to score.
        :type variable: Variable
        :param criteria: The criteria to use for scoring (threshold and condition).
        :type criteria: Criteria
        :param dtype: The data type of the score, defaults to np.int32.
        :type dtype: Union[np.dtype, str]
        """
        assert isinstance(variable, Variable), f"The variable must be an instance of Variable, not {type(variable)}."
        assert isinstance(criteria, Criteria), f"The criteria must be an instance of Criteria, not {type(criteria)}."
        self._variable = None
        self.variable = variable
        self._criteria = None
        self.criteria = criteria
        self._score: np.ma.MaskedArray = None
        self._dtype = None
        self.dtype = dtype

    @property
    def variable(self) -> Variable:
        """
        Get the variable.

        :return: The variable as a Variable object.
        """
        return self._variable

    @variable.setter
    def variable(self, value: Variable) -> None:
        """
        Set the variable.

        :param value: The variable to set.
        """
        assert isinstance(value, Variable), f"The variable must be an instance of Variable, not {type(value)}."
        self._variable = value

    @property
    def criteria(self) -> Criteria:
        """
        Get the criteria.

        :return: The criteria as a Criteria object.
        """
        return self._criteria

    @criteria.setter
    def criteria(self, value: Criteria) -> None:
        """
        Set the criteria.

        :param value: The criteria to set.
        """
        assert isinstance(value, Criteria), f"The criteria must be an instance of Criteria, not {type(value)}."
        self._criteria = value

    @property
    def score(self) -> np.ma.MaskedArray:
        """
        Get the score.

        :return: The score as a numpy masked array.
        """
        self.score = self._compute_score()
        return self._score

    @score.setter
    def score(self, value: np.ma.MaskedArray) -> None:
        """
        Set the score.

        :param value: The score to set.
        """
        assert isinstance(value, np.ma.MaskedArray), f"The score must be a numpy masked array, not {type(value)}."
        assert value.shape == self.variable.variable.shape, \
            f"The score must have the same shape as the variable, not {value.shape}."
        self._score = value.astype(self._dtype, copy=True)

    @property
    def dtype(self) -> type:
        """
        Get the data type of the score.

        :return: The data type of the score.
        """
        return self._dtype

    @dtype.setter
    def dtype(self, value: Union[type, str]) -> None:
        """
        Set the data type of the score.

        :param value: The data type to set.
        """
        assert isinstance(value, (type, str)), f"The data type must be a numpy dtype or a string representing a numpy dtype, not {type(value)}."
        assert np.issubdtype(value, np.integer), \
            f"The data type must be an integer type, not {value}."
        self._dtype = value
        if self._score is not None:
            self._score = self._score.astype(value, copy=True)

    def _compute_score(self):
        """
        Compute the score based on the variable and criteria.

        :return: The score as a numpy masked array.
        """
        assert self._variable is not None, "Variable is not set."
        assert self._criteria is not None, "Criteria is not set."
        assert isinstance(self._variable.variable, np.ma.MaskedArray), \
            f"The variable must be a numpy masked array, not {type(self._variable.variable)}"
        score:np.ma.MaskedArray = self.variable.variable.copy()
        score = score.astype(Format.INT32.value, copy=True)  # Convert to int32 for scoring

        if self.criteria.condition == Operator.SUPERIOR.value:
            score[self.variable.variable <= self.criteria.threshold] = Constant.ZERO.value
            score[self.variable.variable > self.criteria.threshold] = Constant.ONE.value

        elif self.criteria.condition == Operator.INFERIOR.value:
            score[self.variable.variable >= self.criteria.threshold] = Constant.ZERO.value
            score[self.variable.variable < self.criteria.threshold] = Constant.ONE.value

        elif self.criteria.condition == Operator.EQUAL.value:
            score[self.variable.variable != self.criteria.threshold] = Constant.ZERO.value
            score[self.variable.variable == self.criteria.threshold] = Constant.ONE.value

        elif self.criteria.condition == Operator.SUPERIOR_OR_EQUAL.value:
            score[self.variable.variable < self.criteria.threshold] = Constant.ZERO.value
            score[self.variable.variable >= self.criteria.threshold] = Constant.ONE.value

        elif self.criteria.condition == Operator.INFERIOR_OR_EQUAL.value:
            score[self.variable.variable > self.criteria.threshold] = Constant.ZERO.value
            score[self.variable.variable <= self.criteria.threshold] = Constant.ONE.value

        elif self.criteria.condition == Operator.BETWEEN.value:
            assert isinstance(self.criteria.threshold, tuple), \
                "The threshold for the 'between' condition must be a tuple of two elements."
            score[(self.variable.variable < self.criteria.threshold[0]) | \
                  (self.variable.variable > self.criteria.threshold[1])] = Constant.ZERO.value
            score[(self.variable.variable >= self.criteria.threshold[0]) & \
                  (self.variable.variable <= self.criteria.threshold[1])] = Constant.ONE.value

        elif self.criteria.condition == Operator.BETWEEN_STRICT.value:
            assert isinstance(self.criteria.threshold, tuple), \
                "The threshold for the 'strictly between' condition must be a tuple of two elements."
            score[(self.variable.variable <= self.criteria.threshold[0]) | \
                  (self.variable.variable >= self.criteria.threshold[1])] = Constant.ZERO.value
            score[(self.variable.variable > self.criteria.threshold[0]) & \
                  (self.variable.variable < self.criteria.threshold[1])] = Constant.ONE.value

        elif self.criteria.condition == Operator.OUTSIDE.value:
            assert isinstance(self.criteria.threshold, tuple), \
                "The threshold for the 'outside' condition must be a tuple of two elements."
            score[(self.variable.variable > self.criteria.threshold[0]) & \
                  (self.variable.variable < self.criteria.threshold[1])] = Constant.ZERO.value
            score[(self.variable.variable <= self.criteria.threshold[0]) | \
                  (self.variable.variable >= self.criteria.threshold[1])] = Constant.ONE.value

        elif self.criteria.condition == Operator.OUTSIDE_STRICT.value:
            assert isinstance(self.criteria.threshold, tuple), \
                "The threshold for the 'strictly outside' condition must be a tuple of two elements."
            score[(self.variable.variable >= self.criteria.threshold[0]) | \
                  (self.variable.variable <= self.criteria.threshold[1])] = Constant.ZERO.value
            score[(self.variable.variable < self.criteria.threshold[0]) | \
                  (self.variable.variable > self.criteria.threshold[1])] = Constant.ONE.value

        else:
            raise ValueError(f"Unknown condition: {self._criteria.condition}. "
                             f"Available conditions are: {self._criteria._available_conditions}")

        return score.astype(self.dtype, copy=True)

class Scores:
    """
    This class is used to store multiple scores from different criteria as dictionary.

    It contains a dictionary of scores,
    where the keys are the score names and the values are the Score objects.
    """
    def __init__(self, scores:dict[str, Score]) -> None:
        """
        Initialize the Scores object.
        """
        self._scores: dict[str, Score] = None
        self.scores = scores

    @property
    def scores(self) -> dict[str, Score]:
        """
        Get the scores.

        :return: The scores as a dictionary of Score objects.
        """
        return self._scores

    @scores.setter
    def scores(self, value: dict[str, Score]) -> None:
        """
        Set the scores.

        :param value: The scores to set.
        """
        assert isinstance(value, dict), f"The scores must be a dictionary, not {type(value)}."
        assert all(isinstance(key, str) for key in value.keys()), \
            "All keys in the scores dictionary must be strings."
        assert all(isinstance(score, Score) for score in value.values()), \
            "All values in the scores dictionary must be Score objects."
        assert all(score.variable.variable.shape == next(iter(value.values())).variable.variable.shape \
                    for score in value.values()), "All scores must have the same shape."
        self._scores = value

    @property
    def number(self) -> int:
        """
        Get the number of scores.

        :return: The number of scores in the dictionary.
        """
        return len(self._scores) if self._scores is not None else 0

    def add_score(self, name: str, score: Score) -> None:
        """
        Add a score to the scores dictionary.

        :param name: The name of the score.
        :param score: The Score object to add.
        """
        assert isinstance(name, str), f"The name must be a string, not {type(name)}."
        assert isinstance(score, Score), f"The score must be an instance of Score, not {type(score)}."
        if self._scores is None:
            self._scores = {}
        self._scores[name] = score

    def get_score(self, name: str) -> Score:
        """
        Get a score by its name.

        :param name: The name of the score to get.
        :return: The Score object with the given name.
        """
        try:
            return self._scores[name]
        except KeyError:
            logging.error(f"The score with name: '{name}' does not exist.")
            raise KeyError(f"The score with name '{name}' does not exist.")

    def remove_score(self, name: str) -> None:
        """
        Remove a score by its name.

        :param name: The name of the score to remove.
        """
        try:
            del self._scores[name]
        except KeyError:
            logging.error(f"The score with name:'{name}' does not exist.")
            raise KeyError(f"The score with name '{name}' does not exist.")

class Operations:
    """
    This class is used to perform mathematical operations on scores.

    N.B.: if needed operations from other libraries can be added here.
    for instance **pymcdm, scikit-mcda, etc.**
    """

    def __init__(self,
                 scores: Scores,
                 int_type:str = Format.INT32.value,
                 float_type:str = Format.FLOAT32.value,
                 weight: dict = None
                ) -> None:
        """
        Initialize the Operations object with a Scores object.

        :param scores: The Scores object to perform operations on.
        :type scores: Scores
        :param int_type: The integer data type to use in the operations if integers are expected,
        defaults to np.int32.
        :type int_type: str
        :param float_type: The float data type to use in the operations if floats are expected
        , defaults to np.float32.
        :type float_type: str
        :param weight: A dictionary of weights for scores, defaults to None.
        :type weight: dict

        :raises AssertionError: If the scores is not an instance of Scores.
        """
        assert isinstance(scores, Scores),\
            f"The scores must be an instance of Scores, not {type(scores)}."
        self._scores = None
        self._int_type = None
        self._float_type = None
        self._weight = None
        self.scores = scores
        self.int_type = int_type
        self.float_type = float_type
        self.weight = weight
        self._available_operations = [Operator.SUM.value,
                                      Operator.PRODUCT.value,
                                      Operator.WEIGHTED_SUM.value,
                                      Operator.AVERAGE.value]

    @property
    def scores(self) -> Scores:
        """
        Get the Scores object.

        :return: The Scores object.
        """
        return self._scores

    @scores.setter
    def scores(self, value: Scores) -> None:
        """
        Set the Scores object.

        :param value: The Scores object to set.
        """
        assert isinstance(value, Scores),\
            f"The scores must be an instance of Scores, not {type(value)}."
        self._scores = value

    @property
    def int_type(self) -> str:
        """
        Get the integer data type used in the operations.

        :return: The integer data type as a string.
        """
        return self._int_type
    @int_type.setter
    def int_type(self, value: Union[str,type]) -> None:
        """
        Set the integer data type used in the operations.

        :param value: The integer data type to set.
        """
        assert isinstance(value, (str,type)), f"The integer type must be a string, not {type(value)}."
        self._int_type = value

    @property
    def float_type(self) -> str:
        """
        Get the float data type used in the operations.

        :return: The float data type as a string.
        """
        return self._float_type

    @float_type.setter
    def float_type(self, value: Union[str,type]) -> None:
        """
        Set the float data type used in the operations.

        :param value: The float data type to set.
        """
        assert isinstance(value, (str,type)), f"The float type must be a string, not {type(value)}."
        self._float_type = value

    @property
    def weight(self) -> dict:
        """
        Get the weight dictionary.

        :return: The weight dictionary.
        """
        return self._weight

    @weight.setter
    def weight(self, value: dict) -> None:
        """
        Set the weight dictionary.

        :param value: The weight dictionary to set.
        """
        if value is None:
            if self.scores.number == 0:
                logging.warning("No scores to set weight for. Setting weight to None.")
                self._weight = None
                return
            elif self.scores.number > 0:
                logging.warning("No weight provided. Setting weight to equal distribution.")
                value = {key: 1  for key in self.scores.scores.keys()}
        else:
            assert isinstance(value, dict), f"The weight must be a dictionary, not {type(value)}."
            assert len(value) == self.scores.number,\
                "The weight dictionary must have the same number of keys as the scores dictionary."
            assert all(key in self.scores.scores.keys() for key in value.keys()),\
                "All keys in the weight dictionary must be present in the scores dictionary."
        self._weight = value

    def sum(self) -> np.ma.MaskedArray:
        """
        Sum all scores in the Scores object.

        :return: The sum of all scores as a numpy masked array.
        """
        if self.scores.number == 0:
            logging.warning("No scores to sum.")
            return np.ma.masked_array([], mask=True)
        score_sum = np.ma.masked_array(np.zeros_like(next(iter(self.scores.scores.values())).score),
                                       dtype=Format.INT32.value)

        for score in self.scores.scores.values():
            score_sum += score.score

        return score_sum

    def product(self) -> np.ma.MaskedArray:
        """
        Calculate the product of all scores in the Scores object.

        :return: The product of all scores as a numpy masked array.
        """
        if self.scores.number == 0:
            logging.warning("No scores to multiply.")
            return np.ma.masked_array([], mask=True)

        score_product = np.ma.masked_array(np.ones_like(next(iter(self.scores.scores.values())).score),
                                           dtype=Format.INT32.value)

        for score in self.scores.scores.values():
            score_product *= score.score

        return score_product


    def weighted_sum(self) -> np.ma.MaskedArray:
        """
        Calculate the weighted sum of all scores in the Scores object.

        :return: The weighted sum of all scores as a numpy masked array.
        """
        if self.scores.number == 0:
            logging.warning("No scores to calculate weighted sum.")
            return np.ma.masked_array([], mask=True)

        score_sum = np.ma.masked_array(np.zeros_like(next(iter(self.scores.scores.values())).score),
                                       dtype=self.float_type) # FIXME Find a better method to apply this

        for key, score in self.scores.scores.items():
            if key in self.weight:
                array = (score.score * self.weight[key]).astype(self.float_type, copy=True)
                score_sum = score_sum.astype(self.float_type, copy=True)
                score_sum += array

            else:
                raise KeyError(f"No weight provided for score '{key}'. Using default weight of 1.")

        return score_sum

    def average(self) -> np.ma.MaskedArray:
        """
        Calculate the average of all scores in the Scores object.

        :return: The average of all scores as a numpy masked array.
        """
        if self.scores.number == 0:
            logging.warning("No scores to average.")
            return np.ma.masked_array([], mask=True)

        score_sum = self.sum()
        average: np.ma.MaskedArray = (score_sum / self.scores.number)
        average = average.astype(self.float_type)

        return average

    def percentage(self) -> np.ma.MaskedArray:
        """
        Calculate the percentage of each score in the Scores object.

        :return: The percentage of each score as a numpy masked array.
        """
        return self.average() * 100

    def apply_operation(self,
                        operation: Literal[Operator.SUM.value,
                                           Operator.PRODUCT.value,
                                           Operator.WEIGHTED_SUM.value,
                                           Operator.AVERAGE.value,
                                           Operator.PERCENTAGE.value
                                           ]) -> np.ma.MaskedArray:
        """
        Select an operation to perform on the scores.

        :param operation: The operation to perform.
        :return: The result of the operation as a numpy masked array.
        """
        # if operation.lower() not in self._available_operations():
        if operation == Operator.SUM.value:
            return self.sum()
        elif operation == Operator.PRODUCT.value:
            return self.product()
        elif operation == Operator.WEIGHTED_SUM.value:
            return self.weighted_sum()
        elif operation == Operator.AVERAGE.value:
            return self.average()
        elif operation == Operator.PERCENTAGE.value:
            return self.percentage()
        else:
            raise ValueError(f"Unknown operation: {operation}. "
                             f"Available operations are: {self._available_operations()}")

class Results:
    """
    This class is used to collect results of the Operations module.

    It allows:
        - to define the mold (a WolfArray) which serve as the geo-spatial extent computed results,
        - to define the method used to compute scores,
        - to get and write the results.
    """
    def __init__(self,
                 operations: Operations,
                 mold: WolfArray = None,
                 method: Literal[Operator.SUM.value,
                                 Operator.PRODUCT.value,
                                    Operator.WEIGHTED_SUM.value,
                                    Operator.AVERAGE.value,
                                    Operator.PERCENTAGE.value
                                    ] = Operator.SUM.value
                ) -> None:

        """
        Initialize the Results object.

        :param operations: The Operations object to perform operations on.
        :type operations: Operations
        :param mold: The mold used for the results, defaults to None.
        :type mold: WolfArray
        :param method: The method used to compute the scores, defaults sum.
        :type method: str,

        """
        self._operations = None
        self._mold = None
        self._method = None
        self.operations = operations
        self.mold = mold
        self.method = method

    @property
    def operations(self) -> Operations:
        """
        Get the Operations object.

        :return: The Operations object.
        """
        return self._operations

    @operations.setter
    def operations(self, value: Operations) -> None:
        """
        Set the Operations object.

        :param value: The Operations object to set.
        """
        assert isinstance(value, Operations),\
            f"The operations must be an instance of Operations, not {type(value)}."
        self._operations = value

    @property
    def mold(self) -> WolfArray:
        """
        Get the mold used for the results.

        :return: The mold as a WolfArray.
        """

        return self._mold

    @mold.setter
    def mold(self, value: WolfArray) -> None:
        """
        Set the mold used for the results.
        :param value: The mold to set.
        """
        if value is not None:
            assert isinstance(value, WolfArray), f"The mold must be a WolfArray, not {type(value)}."
            for key in self.operations.scores.scores.keys():
                if value.shape != self.operations.scores.get_score(key).score.shape:
                    raise ValueError(f"The mold shape {value.shape} does not match the score shape {self.operations.scores.get_score(key).score.shape}.")
        self._mold = value

    @property
    def header(self) -> header_wolf:
        """
        Get the header of the mold.

        :return: The header of the mold as a header_wolf object.
        """
        if self.mold is None:
            if self.operations is not None:
                    sample = self.operations.scores.get_score(next(iter(self.operations.scores.scores.keys()))).score
                    nbx = sample.shape[0]
                    nby = sample.shape[1]
                    return self.create_header_wolf(nbx=nbx,
                                                        nby=nby,
                                                        dx= Constant.ONE.value,
                                                        dy= Constant.ONE.value)
        else:
            return self.mold.get_header()

    @property
    def method(self) -> str:
        """
        Get the method used for the results.

        :return: The method as a string.
        """
        return self._method

    @method.setter
    def method(self, value: Literal[Operator.SUM.value,
                                      Operator.PRODUCT.value,
                                      Operator.WEIGHTED_SUM.value,
                                      Operator.AVERAGE.value,
                                      Operator.PERCENTAGE.value
                                      ]) -> None:
        """
        Set the method used for the results.
        :param value: The method to set.

        """
        assert value in self.operations._available_operations,\
            f"The method must be one of the following: {self.operations._available_operations}."
        self._method = value

    @property
    def as_numpy_array(self) -> np.ma.MaskedArray:
        return self.operations.apply_operation(self.method)

    @property
    def as_WolfArray(self) -> WolfArray:
        """
        Get the results as a WolfArray.

        :return: The results as a WolfArray.
        """
        return self.as_results(self.as_numpy_array)

    #------------
    # Methods
    #------------

    def create_header_wolf(self,
                       origx:float = None,
                       origy: float =None ,
                       origz: float = None,
                       dx: float = None,
                       dy: float = None,
                       dz: float = None,
                       nbx: int = None,
                       nby: int = None,
                            nbz: int = None):
        """
        Create a header_wolf object.
        The header_wolf object is used to describe the spatial
        characteristics of the array.


        :param origx: The x-coordinate of the origin (in 2D - lower left corner),
        defaults to None.
        :type origx: float, optional
        :param origy: The y-coordinate of the origin (in 2D - lower left corner),
        defaults to None.
        :type origy: float, optional
        :param origz: The z-coordinate of the origin, defaults to None.
        :type origz: float, optional
        :param dx: The x-spacing (discretization in the x direction), defaults to None.
        :type dx: float, optional
        :param dy: The y-spacing (discretization in the x direction), defaults to None.
        :type dy: float, optional
        :param dz: The z-spacing, defaults to None.
        :type dz: float, optional
        :param nbx: The number of columns, defaults to None.
        :type nbx: int, optional
        :param nby: The number of rows, defaults to None.
        :type nby: int, optional
        :param nbz: The number of layers, defaults to None.
        :type nbz: int, optional
        :return: A header_wolf object with the given parameters.
        :rtype: header_wolf
        """
        header = header_wolf()
        if origx is not None:
            header.origx = origx
        if origy is not None:
            header.origy = origy
        if origz is not None:
            header.origz = origz
        if dx is not None:
            header.dx = dx
        if dy is not None:
            header.dy = dy
        if dz is not None:
            header.dz = dz
        if nbx is not None:
            header.nbx = nbx
        if nby is not None:
            header.nby = nby
        if nbz is not None:
            header.nbz = nbz
        return header

    def create_WolfArray(self,
                        dtype = None) -> WolfArray:
        """
        Create an empty WolfArray with the given name, and header.

        :param dtype: The data type of the WolfArray, defaults to np.float32.
        :type dtype: Union[type, str]
        :return: An empty WolfArray with the given name and header.
        :rtype: WolfArray
        """
        array = WolfArray()
        array.init_from_header(self.header, dtype=dtype)
        return array

    def as_results(self,
                      results: np.ma.MaskedArray,
                      EPSG: int = 31370,
                      dtype: Union[type, str] =None,
                      write_to: Union [Path,str] = None
                      ) -> WolfArray:
        """
        Write the results to a WolfArray file.

        :param output_path: The path to write the results to.
        :param name: The name of the results file.
        :param header: The header for the WolfArray.
        :param dtype: The data type of the WolfArray.
        """
        if dtype is None:
            dtype = results.dtype
        array = self.create_WolfArray(dtype=dtype)
        array.array = results
        array.array.mask = results.mask
        array.nullvalue = -99999
        if write_to is not None:
            assert isinstance(write_to, (str, Path)), \
                f"The output path must be a string or a Path object, not {type(write_to)}."
            # if not os.path.exists(write_to):
            #     os.makedirs(write_to)
            array.write_all(write_to, EPSG=EPSG)
        return array

class Input:
    """
    This class stores the inputs of the MultiCriteriaAnalysis.

    Also, it ensures that the inputs are valid and consistent
    to feed the MulticriteriAnalysis tool.
    """
    def __init__(self,
                 name: str,
                 array: np.ma.MaskedArray| np.ndarray| WolfArray,
                 condition: Literal[Operator.SUPERIOR.value,
                                    Operator.INFERIOR.value,
                                    Operator.EQUAL.value,
                                    Operator.SUPERIOR_OR_EQUAL.value,
                                    Operator.INFERIOR_OR_EQUAL.value] = Operator.SUPERIOR_OR_EQUAL.value,
                threshold: Union[float, int] = 0.0,
                ) -> None:
        """
        Initialize the Input object.

        :param name: The name of the variable.
        :type name: str
        :param array: The array (matrix) containing the variable (observations).
        :type array: np.ma.MaskedArray, np.ndarray, or WolfArray
        :param condition: The condition (criteria) used to discriminate values inside the variable,
        defaults to 'superior or equal'.
        :type condition: str, optional
        :param threshold: The threshold used to select values inside the variable,
        defaults to 0.0.
        :type threshold: Union[float, int], optional
        """
        self._name = None
        self._array = None
        self._condition = None
        self._threshold = None
        self._score = None
        self.name = name
        self.array = array
        self.condition = condition
        self.threshold = threshold

    @property
    def name(self) -> str:
        """
        Get the name of the input.

        :return: The name of the input.
        """
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """
        Set the name of the input.

        :param value: The name to set.
        """
        assert isinstance(value, str), f"The name must be a string, not {type(value)}."
        self._name = value

    @property
    def array(self) -> Union[np.ma.MaskedArray, np.ndarray, WolfArray]:
        """
        Get the array of the input.

        :return: The array as a numpy masked array.
        """
        return self._array

    @array.setter
    def array(self, value: Union[np.ma.MaskedArray, np.ndarray, WolfArray
                    ]) -> None:
        """
        Set the array of the input.

        :param value: The array to set.
        """
        assert isinstance(value, (np.ma.MaskedArray, np.ndarray, WolfArray)), \
            f"The array must be a numpy masked array, a numpy array or a WolfArray, not {type(value)}."
        self._array = value

    @property
    def condition(self) -> Literal[Operator.SUPERIOR.value,
                                    Operator.INFERIOR.value,
                                    Operator.EQUAL.value,
                                    Operator.SUPERIOR_OR_EQUAL.value,
                                    Operator.INFERIOR_OR_EQUAL.value]:
        """
        Get the condition of the input.

        :return: The condition as a string.
        """
        return self._condition

    @condition.setter
    def condition(self, value: Literal[Operator.SUPERIOR.value,
                                        Operator.INFERIOR.value,
                                        Operator.EQUAL.value,
                                        Operator.SUPERIOR_OR_EQUAL.value,
                                        Operator.INFERIOR_OR_EQUAL.value]) -> None:
        """
        Set the condition of the input.

        :param value: The condition to set.
        """
        assert isinstance(value, str), f"The condition must be a string, not {type(value)}."
        self._condition = value

    @property
    def threshold(self) -> Union[float, int]:
        """
        Get the threshold of the input.

        :return: The threshold as a float or an int.
        """
        return self._threshold

    @threshold.setter
    def threshold(self, value: Union[float, int, tuple, list, np.ndarray]) -> None:
        """
        Set the threshold of the input.

        :param value: The threshold to set.
        FIXME make it fair for list as well.
        """
        assert isinstance(value, (float, int, tuple, list, np.ndarray)),\
            f"The threshold must be a float or an int or a tuple, not {type(value)}."
        if isinstance(value, (tuple, list)):
            assert len(value) == 2, "The threshold must be a tuple or a list with exactly two elements."
            assert all(isinstance(item, (float, int)) for item in value), \
                f"All elements in the threshold tuple or list must be floats or ints.\
                    not {[type(item) for item in value]}."
            value = tuple(value)  # Ensure it's a tuple
        elif isinstance(value, np.ndarray):
            assert value.ndim == 1, "The threshold must be a 1D numpy"
            assert len(value) == 2, "The threshold must be a 1D numpy array with exactly two elements."
            # val1 = value[0]
            if np.issubdtype(value.dtype, np.integer):
                value = (int(value[0]), int(value[1]))
            elif np.issubdtype(value.dtype,np.floating):
                value = (float(value[0]), float(value[1]))
            # value = (float(value[0]), float(value[1]))  # Convert to tuple
        self._threshold = value

    @property
    def score(self) -> Score:
        """
        Get the score of the input.

        :return: The score as a Score object.
        """
        if self._score is None:
            self._score = Score(variable= Variable(variable = self.array),
                                criteria= Criteria(threshold=self.threshold, condition=self.condition, ))
        return self._score


    @score.setter
    def score(self, value: Score) -> None:
        """
        Set the score of the input.

        :param value: The score to set.
        """
        assert isinstance(value, Score), f"The score must be an instance of Score, not {type(value)}."
        self._score = value

class MulticriteriAnalysis:
    """
    This class performs a multi-criteria analysis based
    on a set of inputs (variables and criteria).

    The inputs are:
        - name: The name of the variable (observations).
        - array: The array (matrix) containing the variable (observations).
        - condition: The condition (criteria) used to distinguish between good and bad variables.
        Basically, the condition is used to obtain a binary score (0 or 1) for each value in the array.
        - Threshold: The value(s) used as limits for the condition.
    """
    def __init__(self,
                 inputs: Union[list[Input],tuple[Input],Input],
                 method:Literal[Operator.SUM.value,
                                Operator.AVERAGE.value,
                                Operator.PERCENTAGE.value] = Operator.PERCENTAGE.value,
                 dtype: Union[type, str] = Format.FLOAT32.value,
                 mold: WolfArray = None,
                 write_to: Union[Path, str] = None,
                 EPSG: int = None
                 ) -> None:
        """
        Initialize the MultiCriteriaAnalysis

        :param inputs: The inputs to the MultiCriteriaAnalysis.
        :type inputs: Union[list[Input], tuple[Input], Input]
        :param method: The method used for the MultiCriteriaAnalysis,
        defaults to 'percentage'.
        :type method: Literal[constant_value(Constant.SUM),
                        constant_value(Constant.AVERAGE),
                        constant_value(Constant.PERCENTAGE)], optional
        :param dtype: The data type used for the MultiCriteriaAnalysis,
        defaults to np.float32.
        :type dtype: Union[type, str], optional
        :param mold: The mold used for the MultiCriteriaAnalysis,
        defaults to None.
        :type mold: WolfArray, optional
        :param write_to: The path where the results will be written,
        defaults to None.
        :type write_to: Union[Path, str], optional
        :param EPSG: The EPSG code for the coordinate reference system,
        defaults to None.
        :type EPSG: int, optional
        """
        self._inputs: list[Input] = None
        self._method: str = None
        self._dtype: Union[type, str] = None
        self._mold: WolfArray = None
        self._path: Union[Path, str] = None
        self._EPSG: int = None
        self.inputs = inputs
        self.method = method
        self.dtype = dtype
        self.mold = mold
        self.path = write_to
        self.EPSG = EPSG

    # ************************
    # Preprocessing the inputs
    # ************************

    @property
    def inputs(self) -> list[Input]:
        """
        Get the inputs of the MultiCriteriaAnalysis.

        :return: The inputs as a list of Input objects.
        """
        return self._inputs

    @inputs.setter
    def inputs(self, value: Union[list[Input],tuple[Input],Input]) -> None:
        """
        Set the inputs of the MultiCriteriaAnalysis.

        :param value: The inputs to set.
        """
        assert isinstance(value, (list, tuple, Input)), \
            f"The inputs must be a list or a tuple of Input objects, not {type(value)}."
        if isinstance(value, (list, tuple)):
            assert len(value) > 0, "The inputs list must not be empty."
            assert all(isinstance(item, Input) for item in value), \
                "All items in the inputs list must be Input objects."
            if isinstance(value, tuple):
                value = list(value)
        elif isinstance(value, Input):
            value = [value]

        self._inputs = value

    @property
    def number_of_inputs(self) -> int:
        """
        Get the number of inputs.

        :return: The number of inputs.
        """
        return len(self.inputs) if self.inputs is not None else 0

    @property
    def method(self) -> Literal[Operator.SUM.value,
                                Operator.AVERAGE.value,
                                Operator.PERCENTAGE.value]:
        """
        Get the method used for the MultiCriteriaAnalysis.

        :return: The method as a string.
        """
        return self._method

    @method.setter
    def method(self, value: Literal[Operator.SUM.value,
                                      Operator.AVERAGE.value,
                                      Operator.PERCENTAGE.value]) -> None:
        """
        Set the method used for the MultiCriteriaAnalysis.

        :param value: The method to set.
        """
        assert isinstance(value, str), f"The method must be a string, not {type(value)}."
        self._method = value

    @property
    def dtype(self) -> Union[type, str]:
        """
        Get the data type used for the MultiCriteriaAnalysis.

        :return: The data type as a string or a numpy dtype.
        """
        return self._dtype

    @dtype.setter
    def dtype(self, value: Union[type, str]) -> None:
        """
        Set the data type used for the MultiCriteriaAnalysis.

        :param value: The data type to set.
        """
        if value is None:
            value = Format.FLOAT32.value  # Default data type
        else:
            assert isinstance(value, (type, str)),\
                f"The data type must be a numpy dtype or a string representing a numpy dtype, not {type(value)}."
            self._dtype = value

    @property
    def mold(self) -> WolfArray:
        """
        Get the mold used for the MultiCriteriaAnalysis.

        :return: The mold as a WolfArray.
        """
        return self._mold

    @mold.setter
    def mold(self, value: WolfArray) -> None:
        """
        Set the mold used for the MultiCriteriaAnalysis.

        :param value: The mold to set.

        FIXME: add update mold from inputs.
        """
        if value is not None:
            assert isinstance(value, WolfArray), f"The mold must be a WolfArray, not {type(value)}."
            for input_ in self.inputs:
                if value.shape != input_.array.shape:
                    raise ValueError(f"The mold shape {value.shape} does not match the input shape {input_.array.shape}.")
        self._mold = value

    @property
    def path(self) -> Union[Path, str]:
        """
        Get the path where the results will be written.

        :return: The path as a string or a Path object.
        """
        return self._path

    @path.setter
    def path(self, value: Union[Path, str]) -> None:
        """
        Set the path where the results will be written.

        :param value: The path to set.
        """
        if value is None:
            self._path = None
        else:
            assert isinstance(value, (Path, str)),\
                f"The path must be a string or a Path object, not {type(value)}."
            self._path = value

    @property
    def scores(self) -> Scores:
        """
        Get the scores for each input.

        :return: The scores as a Scores object.
        """
        scores = {}
        for input_ in self.inputs:
            scores[input_.name] = input_.score

        return Scores(scores)

    @property
    def operations(self) -> Operations:
        """
        Get the operations to be performed on the scores.

        :return: The Operations object.
        """
        return Operations(scores=self.scores, int_type=self.dtype, float_type=self.dtype)

    @property
    def EPSG(self) -> int:
        """
        Get the EPSG code for the results.

        :return: The EPSG code as an integer.
        """
        return self._EPSG

    @EPSG.setter
    def EPSG(self, value: int) -> None:
        """
        Set the EPSG code for the results.

        :param value: The EPSG code to set.
        """
        if value is None:
            self._EPSG = Constant.EPSG.value  # Default EPSG code
        else:
            assert isinstance(value, int), f"The EPSG code must be an integer, not {type(value)}."
            self._EPSG = value

    # *************************************
    # Performing the MultiCriteria Analysis
    # *************************************

    @property
    def results(self) -> WolfArray:
        """
        Perform the MultiCriteria Analysis on the inputs.

        :return: The results of the analysis as a Results object.
        """
        if self.number_of_inputs == 0:
            raise ValueError("No inputs provided for the MultiCriteria Analysis.")
        assert self.number_of_inputs >= 2, "At least two inputs are required for the MultiCriteria Analysis."
        assert self.method in self.operations._available_operations,\
            f"The method '{self.method}' is not available.\
                Available methods are: {self.operations._available_operations}"
        # Create results object
        results = Results(operations=self.operations, mold=self.mold, method=self.method)
        return  results.as_WolfArray

    def write_result(self) -> WolfArray:
        """
        Write the results to a WolfArray file.

        :return: The results as a WolfArray.
        """
        if self.path is None:
            raise ValueError("No path provided for writing the results.")
        return self.results.write_all(self.path, self.EPSG)

























