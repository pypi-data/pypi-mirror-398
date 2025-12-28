import numpy as np
from numpy.typing import NDArray
from typing_extensions import TypeAlias

NDArrayStr: TypeAlias = NDArray[np.str_]
NDArrayBool: TypeAlias = NDArray[np.bool]

NDArrayInt8: TypeAlias = NDArray[np.int8]
NDArrayInt16: TypeAlias = NDArray[np.int16]
NDArrayInt32: TypeAlias = NDArray[np.int32]
NDArrayInt64: TypeAlias = NDArray[np.int64]
NDArrayInt: TypeAlias = NDArrayInt64

NDArrayFloat32: TypeAlias = NDArray[np.float32]
NDArrayFloat64: TypeAlias = NDArray[np.float64]
NDArrayFloat: TypeAlias = NDArrayFloat64


__all__ = [
    "NDArray",
    "NDArrayStr",
    "NDArrayBool",
    "NDArrayInt8",
    "NDArrayInt16",
    "NDArrayInt32",
    "NDArrayInt64",
    "NDArrayInt",
    "NDArrayFloat32",
    "NDArrayFloat64",
    "NDArrayFloat",
]
