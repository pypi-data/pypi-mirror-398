"""
IO utilities for loading experimental data files.

This module provides utilities for reading data from various file formats
commonly used in psychological experiments, including MATLAB .mat files.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import polars as pl
import scipy.io
from docx import Document


__all__ = [
    "MatFormatError",
    "load_mat_matrix",
    "load_excel",
    "load_csv",
    "load_docx",
]


class MatFormatError(RuntimeError):
    """Exception raised when a MATLAB .mat file has an unexpected format."""
    pass


def load_excel(path: Path, sheet: str | None = None) -> pd.DataFrame:
    """
    Load an Excel worksheet into a pandas DataFrame via polars.

    Parameters
    ----------
    path : Path
        Path to the Excel file.
    sheet : str or None, default None
        Sheet name to load. If None, the first sheet is read.
    """
    df = pl.read_excel(str(path), sheet_name=sheet)
    return df.to_pandas()


def load_csv(path: Path, **kwargs: Any) -> pd.DataFrame:
    """
    Load a CSV file into a pandas DataFrame via polars.

    Parameters
    ----------
    path : Path
        Path to the CSV file.
    **kwargs : Any
        Additional keyword arguments passed to polars.read_csv.
    """
    df = pl.read_csv(str(path), **kwargs)
    return df.to_pandas()


def load_docx(path: Path) -> str:
    """
    Load a .docx file and return its full text.

    Parameters
    ----------
    path : Path
        Path to the Word document.
    """
    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs)


def load_mat_matrix(file_path: Path, *, var_name: str = "results") -> np.ndarray:
    """
    Strictly load a 2D numeric matrix from a MATLAB .mat file.
    
    This function handles two common MATLAB data formats:
    1. **Cell array** (dtype object): Automatically vstacks multiple cells into a single matrix
    2. **Numeric matrix**: Returns the matrix directly
    
    The function performs strict validation to ensure data integrity:
    - All cells must have consistent column counts
    - All data must be numeric (no strings or objects)
    - No NaN or Inf values are allowed
    - Result must be a 2D matrix
    
    Parameters
    ----------
    file_path : Path
        Path to the .mat file.
    var_name : str, default "results"
        Name of the variable to load from the .mat file.
    
    Returns
    -------
    np.ndarray
        A 2D numeric matrix with shape (n_rows, n_cols).
    
    Raises
    ------
    MatFormatError
        If the file format is invalid, the variable is missing, or data validation fails.
    
    Examples
    --------
    >>> # Load a cell array from MATLAB
    >>> # mat["results"] = {[48x12 double], [48x12 double], [48x12 double]}
    >>> data = load_mat_matrix(Path("experiment.mat"))
    >>> print(data.shape)  # (144, 12) - all cells vstacked
    
    >>> # Load a direct numeric matrix
    >>> # mat["data"] = [100x6 double]
    >>> data = load_mat_matrix(Path("experiment.mat"), var_name="data")
    >>> print(data.shape)  # (100, 6)
    
    Notes
    -----
    This function was designed for loading trial data from psychological experiments
    where MATLAB cell arrays are commonly used to store trials across multiple blocks.
    """
    # Use squeeze_me to reduce weird singleton dimensions when possible
    mat = scipy.io.loadmat(str(file_path), squeeze_me=False, struct_as_record=False)

    keys = [k for k in mat.keys() if not k.startswith("__")]
    if var_name not in mat:
        raise MatFormatError(
            f"{file_path}: missing variable '{var_name}'. "
            f"Available keys: {keys}"
        )

    raw = mat[var_name]
    arr = np.asarray(raw)

    # Case 1: MATLAB cell array => dtype object
    if arr.dtype == object:
        cells = [np.asarray(x) for x in np.ravel(arr)]

        if len(cells) == 0:
            raise MatFormatError(f"{file_path}: '{var_name}' is an empty cell array.")

        mats: list[np.ndarray] = []
        for idx, c in enumerate(cells):
            c = np.asarray(c)
            if c.ndim == 1:
                c = c.reshape(1, -1)
            if c.ndim != 2:
                raise MatFormatError(
                    f"{file_path}: cell[{idx}] has ndim={c.ndim}, expected 2. shape={c.shape}"
                )
            if not np.issubdtype(c.dtype, np.number):
                raise MatFormatError(
                    f"{file_path}: cell[{idx}] dtype={c.dtype}, expected numeric matrix."
                )
            mats.append(c)

        ncols = {m.shape[1] for m in mats}
        if len(ncols) != 1:
            shapes = [m.shape for m in mats]
            raise MatFormatError(
                f"{file_path}: '{var_name}' cells have inconsistent column counts. shapes={shapes}"
            )

        out = np.vstack(mats)

    # Case 2: already numeric matrix
    else:
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        if arr.ndim != 2:
            raise MatFormatError(f"{file_path}: '{var_name}' ndim={arr.ndim}, expected 2.")
        if not np.issubdtype(arr.dtype, np.number):
            raise MatFormatError(f"{file_path}: '{var_name}' dtype={arr.dtype}, expected numeric.")
        out = arr

    if not np.isfinite(out).all():
        raise MatFormatError(f"{file_path}: '{var_name}' contains NaN/Inf.")

    return out
