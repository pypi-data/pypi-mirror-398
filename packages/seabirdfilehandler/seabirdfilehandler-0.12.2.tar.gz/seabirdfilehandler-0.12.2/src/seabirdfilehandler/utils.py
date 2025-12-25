import logging

logger = logging.getLogger(__name__)


def get_unique_sensor_data(
    sensor_data: list[list[dict]],
) -> list[tuple[list[dict]]]:
    """
    Returns all the unique sensors and their configuration used in the given
    collection of sensor data. These will typically be parsed from xml inside
    .cnv or .xmlcon files.
    If for example, the first oxygen sensor has been replaced after the 8 cast,
    then we will see that in the output structure by a seconde tuple, with the
    number 8 and the individual sensor information for that new oxygen sensor.

    Parameters
    ----------
    sensor_data:
        The structure of xml-parsed dicts inside two organizing lists.

    Returns
    -------
    The input structure stripped down to unique sensor data and appended by
    the index, at which this new sensor appeared the first time.

    """
    unique = []
    last_unique = None
    for index, individual_sensor_data in enumerate(
        [file for file in sensor_data]
    ):
        if last_unique is None:
            unique.append((index, individual_sensor_data))
        else:
            differing_dicts = [
                current_dict
                for last_dict, current_dict in zip(
                    last_unique, individual_sensor_data
                )
                if current_dict != last_dict
            ]
            if differing_dicts:
                unique.append((index, differing_dicts))
        last_unique = individual_sensor_data
    return unique


class UnexpectedFileFormat(Exception):
    def __init__(self, file_type: str, error: str) -> None:
        message = f"{file_type} is not formatted as expected: {error}"
        logger.error(message)
        super().__init__(message)
