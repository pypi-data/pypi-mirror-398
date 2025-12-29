#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : _base.py

import json
from abc import ABC, abstractmethod
from os import PathLike
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

import numpy as np
import pandas as pd


class DataInfoBase(ABC):
    def __init__(self,
                 data_path: str | Path,
                 vars_list: List[str] | str = None,
                 *,
                 encoding: str = "utf-8",
                 cache_info: bool = True,
                 cache_dir: str | Path = None,
                 **kwargs):
        self.data_path = data_path
        self.encoding = encoding
        self._pre_vars_list = vars_list
        self.cache_info = cache_info
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.kwargs = kwargs  # Store additional keyword arguments for subclasses to use

    # Properties
    @property
    def df(self) -> pd.DataFrame:
        """Get the data as a pandas DataFrame."""
        return self._read_data()

    @property
    def vars_list(self) -> List[str]:
        """Get the list of selected variables."""
        return self._get_selected_vars(self._pre_vars_list)

    @property
    def info(self) -> Dict[str, Any]:
        """Get comprehensive information about the data."""
        return {
            "summary": self.summary(),
        }

    @property
    def is_url(self) -> bool:
        try:
            result = urlparse(str(self.data_path))
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    # Abstract methods (must be implemented by subclasses)
    @abstractmethod
    def _read_data(self) -> pd.DataFrame:
        """Read data from the source file. Must be implemented by subclasses."""
        ...

    # Public methods
    def summary(self,
                saved_path: str | PathLike = None) -> Dict[str, Any]:
        """
        Provide a summary of the data.

        Args:
            saved_path (str): If you want to save the result into a json, config this arg with absloute path.

        Returns:
            Dict[str, Any]: the summary of provided data (vars)

        Examples:
            >>> from stata_mcp.core.data_info import DtaDataInfo
            >>> data_info = DtaDataInfo(...)
            >>> summary_data = data_info.summary()
            >>> print(summary_data)
            {
                "overview": {
                    "obs": 1314,  # Observed numbers
                    "var_numbers": 10  # equal to the length of `vars_detail`.
                },
                "vars_detail": {
                    "name": {
                        "type": "str",
                        "obs": 1314,
                        "value_list": ["Jack", "Rose", ...]  # list 10 random unique value
                    },
                    "age": {
                        "type": "float",  # it signed as float no matter the value type is int or float
                        "obs": 1314,
                        "summary": {
                            "mean": 52.1,
                            "se": 10.3386,
                            "min": 18,
                            "max": 100
                        }
                    },
                    "male": {
                        "type": "float",  # Note: no bool type! It is signed with 0 and 1.
                        "obs": 1111,  # Note: maybe some obs do not have value (NA), this is not be counted.
                        "summary": {
                            "mean": 0.49955,
                            "se": 0.500225,
                            "min": 0,
                            "max": 1
                        }
                    }
                    "var_name": {}
                }
            }
        """
        df = self.df
        selected_vars = self.vars_list

        # 基本概览信息
        overview = {
            "obs": len(df),
            "var_numbers": len(selected_vars)
        }

        # 详细变量信息
        vars_detail = {}

        for var_name in selected_vars:
            var_series = df[var_name]
            var_info = DataInfoBase._get_variable_info(var_series)
            vars_detail[var_name] = var_info

        summary_result = {
            "overview": overview,
            "vars_detail": vars_detail
        }

        if saved_path:
            # If there is `saved_path`, save the summary into that file with json format.
            summary_result["saved_path"] = str(saved_path)
            self.save_to_json(summary_result, saved_path)

        return summary_result

    @staticmethod
    def save_to_json(summary_result: Dict[str, Any],
                     save_path: str) -> bool:
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(summary_result, ensure_ascii=False, indent=4))
            return True
        except Exception:
            return False

    # Private helper methods
    def _get_selected_vars(self, vars: List[str] | str = None) -> List[str]:
        """
        Get the list of selected variables.

        If vars is None, return all variables from self.data.
        If vars is a string, convert it to a list.
        Check if all variables exist in self.data, if not raise an error and return all available variables.

        Args:
            vars: List of variable names, single variable name, or None.

        Returns:
            List[str]: List of selected variable names.

        Raises:
            ValueError: If specified variables don't exist in the dataset.
        """
        # Get all available variables from the data
        all_vars = list(self.df.columns)

        if vars is None:
            return all_vars

        # Convert string to list if needed
        if isinstance(vars, str):
            vars = [vars]

        # Check if all specified variables exist in the dataset
        missing_vars = [var for var in vars if var not in all_vars]

        if missing_vars:
            raise ValueError(f"Variables {missing_vars} not found in dataset. "
                             f"Available variables are: {all_vars}")

        return vars

    # Helper methods for summary
    @staticmethod
    def _get_variable_info(var_series: pd.Series) -> Dict[str, Any]:
        """
        Get detailed information for a single variable.

        Args:
            var_series: pandas Series containing the variable data

        Returns:
            Dict[str, Any]: Variable information including type, observations, and summary statistics
        """
        # Remove NA values for analysis
        non_na_series = var_series.dropna()
        non_na_count = len(non_na_series)

        # Determine variable type
        var_type = DataInfoBase._determine_variable_type(non_na_series)

        # Basic variable info
        var_info = {
            "type": var_type,
            "obs": non_na_count
        }

        # Add type-specific information
        if var_type == "str":
            var_info["value_list"] = DataInfoBase._get_string_value_list(non_na_series)
        else:  # float type
            var_info["summary"] = DataInfoBase._get_numeric_summary(non_na_series)

        return var_info

    @staticmethod
    def _determine_variable_type(series: pd.Series) -> str:
        """
        Determine the type of a variable.

        Args:
            series: pandas Series with NA values removed

        Returns:
            str: "str" for string variables, "float" for numeric variables
        """
        if len(series) == 0:
            return "float"  # Default to float for empty series

        # Check if all non-null values are numeric
        try:
            # Try to convert to numeric
            pd.to_numeric(series, errors='raise')
            return "float"
        except (ValueError, TypeError):
            return "str"

    @staticmethod
    def _get_string_value_list(series: pd.Series) -> List[str]:
        """
        Get a list of unique string values (up to 10 random values).

        Args:
            series: pandas Series with NA values removed

        Returns:
            List[str]: List of up to 10 unique string values
        """
        unique_values = series.unique()

        if len(unique_values) <= 10:
            return sorted(unique_values.tolist())
        else:
            # Randomly sample 10 values if there are more than 10
            import random
            sampled_values = random.sample(unique_values.tolist(), 10)
            return sorted(sampled_values)

    @staticmethod
    def _get_numeric_summary(series: pd.Series) -> Dict[str, float]:
        """
        Calculate summary statistics for numeric variables.

        Args:
            series: pandas Series with NA values removed

        Returns:
            Dict[str, float]: Summary statistics including mean, se, min, max
        """
        if len(series) == 0:
            return {
                "mean": np.nan,
                "se": np.nan,
                "min": np.nan,
                "max": np.nan
            }

        # Convert to numeric to handle any remaining type issues
        numeric_series = pd.to_numeric(series, errors='coerce').dropna()

        if len(numeric_series) == 0:
            return {
                "mean": np.nan,
                "se": np.nan,
                "min": np.nan,
                "max": np.nan
            }

        mean_val = float(numeric_series.mean())
        std_val = float(numeric_series.std())
        n = len(numeric_series)
        se_val = std_val / np.sqrt(n) if n > 0 else np.nan

        return {
            "mean": mean_val,
            "se": se_val,
            "min": float(numeric_series.min()),
            "max": float(numeric_series.max())
        }
