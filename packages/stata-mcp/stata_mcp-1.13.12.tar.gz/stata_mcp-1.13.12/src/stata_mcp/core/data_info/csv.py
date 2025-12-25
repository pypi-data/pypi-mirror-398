#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : csv.py

from pathlib import Path
from typing import List

import pandas as pd

from ._base import DataInfoBase


class CsvDataInfo(DataInfoBase):
    def __init__(self,
                 data_path: str | Path,
                 vars_list: List[str] | str = None,
                 *,
                 encoding: str = "utf-8",
                 cache_info: bool = True,
                 cache_dir: str | Path = None,
                 **kwargs):
        """
        Initialize CSV data info handler.

        Args:
            data_path: Path to the CSV file
            vars_list: List of variables to analyze, or single variable name
            encoding: File encoding (default: utf-8)
            cache_info: Whether to cache data information (default: True)
            cache_dir: Directory for caching (default: None)
            **kwargs: Additional pandas.read_csv() arguments (sep, header, etc.)
        """
        # Initialize base class with kwargs
        super().__init__(
            data_path=data_path,
            vars_list=vars_list,
            encoding=encoding,
            cache_info=cache_info,
            cache_dir=cache_dir,
            **kwargs
        )

    def _read_data(self) -> pd.DataFrame:
        """
        Read CSV file into pandas DataFrame.

        Automatically detects header and handles various CSV formats.

        Returns:
            pd.DataFrame: The data from the CSV file

        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file is not a valid CSV file
        """
        # Convert to Path object if it's a string
        file_path = Path(self.data_path)

        # Check if file exists
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        # Check if it's a CSV file
        valid_extensions = {'.csv', '.txt', '.tsv'}
        if file_path.suffix.lower() not in valid_extensions:
            raise ValueError(f"File must have extension in {valid_extensions}, got: {file_path.suffix}")

        try:
            # Auto-detect header if not explicitly specified
            if 'header' not in self.kwargs:
                # Read first few lines to detect header
                sample_kwargs = {k: v for k, v in self.kwargs.items() if k not in ['header', 'names']}

                # Try reading with header=0 (assume first row is header)
                try:
                    df_with_header = pd.read_csv(file_path, nrows=10, header=0, **sample_kwargs)

                    # Simple heuristic: check if column names look like data values
                    # If column names are all numeric or look like data, probably no header
                    column_names = df_with_header.columns.tolist()

                    # Check if any column name looks like a data value (numeric)
                    looks_like_data = False
                    for col_name in column_names:
                        # Try to convert column name to float
                        try:
                            float(str(col_name))
                            looks_like_data = True
                            break
                        except (ValueError, TypeError):
                            continue

                    if looks_like_data:
                        # Column names look like data values, so no header
                        self.kwargs['header'] = None
                    else:
                        # Column names don't look like data, assume header exists
                        self.kwargs['header'] = 0

                except Exception:
                    # If detection fails, default to header=0
                    self.kwargs['header'] = 0

            # Handle no-header case by providing default column names
            if self.kwargs.get('header') is None:
                # First, read a sample to determine number of columns
                sample_kwargs = {k: v for k, v in self.kwargs.items() if k not in ['header', 'names']}
                sample_df = pd.read_csv(file_path, nrows=1, header=None, **sample_kwargs)
                num_cols = len(sample_df.columns)

                # Generate default column names
                self.kwargs['names'] = [f'V{i+1}' for i in range(num_cols)]

            # Read the CSV file with error handling for invalid parameters
            try:
                df = pd.read_csv(file_path, **self.kwargs)
            except TypeError as e:
                if "unexpected keyword argument" in str(e):
                    # Filter out problematic parameters and retry with basic ones
                    basic_kwargs = {k: v for k, v in self.kwargs.items()
                                    if k in {'sep', 'header', 'encoding', 'names'}}
                    print(f"Warning: Retrying CSV read with filtered parameters due to: {e}")
                    df = pd.read_csv(file_path, **basic_kwargs)
                else:
                    raise
            except Exception as e:
                raise ValueError(f"Error reading CSV file {file_path}: {str(e)}")

            return df

        except Exception as e:
            raise ValueError(f"Error reading CSV file {file_path}: {str(e)}")
