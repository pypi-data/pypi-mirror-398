import logging

import numpy as np
from scipy.signal import savgol_filter

logger = logging.getLogger(__name__)


def get_cast_borders(
    pressure_array: np.ndarray,
    downcast_only: bool = True,
    window: int = 50,
    polyorder: int = 3,
) -> dict:
    """Gets the borders of a given cast."""

    out_dict = {}

    # smooth the pressure data to remove noise
    smoothed_pressure = savgol_filter(
        x=pressure_array,
        window_length=window,
        polyorder=polyorder,
    )

    # calculate downcast borders
    out_dict["down_start"] = get_downcast_start(smoothed_pressure)
    out_dict["down_end"] = get_downcast_end(
        smoothed_pressure, out_dict["down_start"]
    )

    if not downcast_only:
        out_dict["up_start"] = get_upcast_start(
            out_dict["down_end"], smoothed_pressure
        )
        out_dict["up_end"] = get_upcast_end(
            out_dict["down_end"], smoothed_pressure
        )

    return out_dict


def get_downcast_end(
    pressure: np.ndarray,
    down_cast_start: int,
    min_descent_rate: float = 0.01,
) -> int:
    """
    Gets the downcast end of a given cast, accounting for heave due to waves.
    Returns the index of the highest pressure where the descent rate is below min_descent_rate.

    Parameters:
    -----------
    pressure : np.ndarray
        The pressure array.
    down_cast_start : int
        The index where the downcast starts.
    window : int, optional
        The window size for the Savitzky-Golay filter.
    polyorder : int, optional
        The polynomial order for the Savitzky-Golay filter.
    min_descent_rate : float, optional
        The minimum descent rate to consider as still descending.

    Returns:
    --------
    The index of the end of the downcast.
    """
    smoothed = pressure[down_cast_start:]

    # compute the descent rate
    descent_rate = np.gradient(smoothed)

    # find all indices where descent rate is below the threshold
    candidates = np.where(descent_rate < min_descent_rate)[0]

    if len(candidates) == 0:
        logger.warning("No clear downcast end found. Returning last index.")
        return len(pressure) - 1

    # find the candidate with the highest pressure
    max_pressure_candidate = candidates[np.argmax(smoothed[candidates])]

    return down_cast_start + max_pressure_candidate


def get_downcast_start(
    pressure: np.ndarray,
    min_ascent_rate: float = 0.01,
    min_sustained_points: int = 5,
) -> int:
    """
    Gets the downcast start of a given cast, removing soaking/waiting time.
    Returns the index where the CTD begins to continuously move downward.

    Parameters:
    -----------
    pressure : np.ndarray
        The pressure array.
    window : int, optional
        The window size for the Savitzky-Golay filter.
    polyorder : int, optional
        The polynomial order for the Savitzky-Golay filter.
    min_ascent_rate : float, optional
        The minimum ascent rate to consider as the start of descent.
    min_sustained_points : int, optional
        The number of consecutive points with increasing pressure to confirm the start.

    Returns:
    --------
    The index of the start of the downcast.
    """
    # compute the descent rate (derivative)
    descent_rate = np.gradient(pressure)

    # find the first index where the descent rate is above the threshold
    # and is sustained for min_sustained_points
    for i in range(len(descent_rate) - min_sustained_points):
        if all(descent_rate[i : i + min_sustained_points] > min_ascent_rate):
            return i
    # if no such point found, return 0 or warn
    logger.warning("No clear downcast start found. Returning 0.")
    return 0


def get_upcast_start(ind_dc_end: int, smooth_velo: np.ndarray) -> int | None:
    upcast_velo_mean = np.mean(smooth_velo[ind_dc_end : len(smooth_velo)])
    for i in range(ind_dc_end, len(smooth_velo)):
        if smooth_velo[i] < upcast_velo_mean * 0.5:
            return i
    logger.warning("Could not find the upcast start.")
    return None


def get_upcast_end(ind_dc_end: int, smooth_velo: np.ndarray) -> int | None:
    upcast_velo_mean = np.mean(smooth_velo[ind_dc_end : len(smooth_velo)])
    for i in range(len(smooth_velo) - 1, ind_dc_end, -1):
        if smooth_velo[i] < upcast_velo_mean * 0.5:
            return i
    logger.warning("Could not find the upcast end.")
    return None
