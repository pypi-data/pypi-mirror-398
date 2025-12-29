from numpy import typing
import numpy as np
from typing import Any, Union

def _u8_array_to_rgba(arr: typing.NDArray[np.uint8]) -> typing.NDArray[np.uint32]:
    """Convert an array with inner dimension [R,G,B,A] into packed uint32 values.

    Args:
        arr (typing.NDArray[np.uint8]): Nx3 or Nx4 array of uint8 values, shape (N, 3) or (N, 4), where each row is [r, g, b, a].

    Returns:
        typing.NDArray[np.uint32]: Array of uint32 values as 0xRRGGBBAA.
    """
    r = arr[:, 0]
    g = arr[:, 1]
    b = arr[:, 2]
    a = arr[:, 3] if arr.shape[1] == 4 else np.repeat(0xFF, len(arr))
    # Reverse the byte order because this is how we encode into uint32
    arr = np.vstack([a, b, g, r]).T
    # Make contiguous and then reinterpret
    arr = np.ascontiguousarray(arr, dtype=np.uint8)
    arr = arr.view(np.uint32)
    arr = np.squeeze(arr, axis=1)
    return arr  # type: ignore[return-value]


def _numpy_array_to_u32(data: typing.NDArray[Union[np.uint8, np.float32, np.float64]]) -> typing.NDArray[np.uint32]:
    """Convert a numpy array of uint8, float32, or float64 to a uint32 array.

    Args:
        data (typing.NDArray[Union[np.uint8, np.float32, np.float64]]): Input numpy array of type uint8, float32, or float64.

    Returns:
        typing.NDArray[np.uint32]: Converted numpy array of type uint32.
    """
    if data.size == 0:
        return np.array([], dtype=np.uint32)

    if data.dtype.type in [np.float32, np.float64]:
        array = _u8_array_to_rgba(np.asarray(np.round(np.asarray(data) * 255.0), np.uint8))
    else:
        array = _u8_array_to_rgba(np.asarray(data, dtype=np.uint8))
    return array


def _rgba_u32_to_u8_array(
    values: typing.NDArray[np.uint32] | int,
    num_channels: int = 4,
    dtype: np.dtype = np.uint8,
) -> typing.NDArray[Any]:
    """
    Convert packed uint32 RGBA values (0xRRGGBBAA) back into an array of
    uint8 channels [R, G, B] or [R, G, B, A].

    Args:
        values: scalar or array of uint32 values, each 0xRRGGBBAA.
        num_channels: 3 for RGB, 4 for RGBA.
        dtype: output dtype, usually np.uint8.

    Returns:
        Array of shape (N, num_channels), dtype=dtype.
    """
    vals = np.asarray(values, dtype=np.uint32).reshape(-1)  # (N,)

    # 0xRRGGBBAA → extract channels by bit shifts
    r = ((vals >> 24) & 0xFF).astype(dtype)
    g = ((vals >> 16) & 0xFF).astype(dtype)
    b = ((vals >> 8)  & 0xFF).astype(dtype)
    a = (vals & 0xFF).astype(dtype)

    if num_channels == 4:
        out = np.stack([r, g, b, a], axis=1)  # (N, 4)
    elif num_channels == 3:
        out = np.stack([r, g, b], axis=1)     # (N, 3)
    else:
        raise ValueError(f"num_channels must be 3 or 4, got {num_channels}")

    return out
