# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module for processing qBraid quantum devices and jobs data into
formats that can be more easily served to and received by clients.

"""
import datetime
from typing import Any, Optional, Union

from .exceptions import QuantumServiceRuntimeError


def _device_status_msg(num_devices: int, lag: Union[int, float]) -> str:
    """Helper function to return a status message based on the
    number of devices and the lag time."""
    if num_devices == 0:
        return "No results matching given criteria"
    hours, minutes = divmod(lag, 60)
    min_10, _ = divmod(minutes, 10)
    min_display = min_10 * 10
    if hours > 0:
        if minutes > 30:
            return f"Device status updated {hours}.5 hours ago"
        hour_s = "hour" if hours == 1 else "hours"
        return f"Device status updated {hours} {hour_s} ago"
    if minutes < 10:
        min_display = minutes
    return f"Device status updated {min_display} minutes ago"


def _job_status_msg(num_jobs: int, query: dict[str, Any]) -> str:
    """Helper function to return a status message based on the
    the number of of query parameters and number of jobs returned."""
    max_results = query.get("resultsPerPage", query.get("maxResults", query.get("numResults", 10)))
    num_query_params = len(query)
    if num_jobs == 0:
        if num_query_params == 0:
            return "No jobs found submitted by user"
        return "No jobs found matching given criteria"
    if num_jobs < max_results:
        return f"Displaying {num_jobs}/{num_jobs} jobs matching query"
    if num_query_params > 0:
        plural = "s" if num_jobs > 1 else ""
        return f"Displaying {num_jobs} most recent job{plural} matching query"
    return f"Displaying {num_jobs} most recent jobs"


# pylint: disable-next=too-many-locals
def _process_device_data(devices: list[dict[str, Any]]) -> tuple[list[list[str]], str]:
    """Processes raw job data and returns list"""
    device_data = []
    tot_dev = 0
    min_lag = 1e7
    for document in devices:
        qbraid_id = document["qbraid_id"]
        name = document["name"]
        provider = document["provider"]
        status_refresh = document["statusRefresh"]
        # pending_jobs = document.get("pendingJobs", 0)
        # timestamp = datetime.datetime.now(datetime.UTC)
        timestamp = datetime.datetime.utcnow()
        if status_refresh is not None:
            refresh = str(status_refresh)
            format_datetime_part1 = refresh[:10].split("-")
            format_datetime_part2 = refresh[11:19].split(":")
            format_datetime = format_datetime_part1 + format_datetime_part2
            format_datetime_int = [int(x) for x in format_datetime]
            year, month, day, hour, minute, second = format_datetime_int
            mk_datime = datetime.datetime(year, month, day, hour, minute, second)
            sec_lag = (timestamp - mk_datime).seconds
            min_lag = min(sec_lag, min_lag)
        status = document["status"]
        tot_dev += 1
        device_data.append([provider, name, qbraid_id, status])

    device_data.sort()
    lag, _ = divmod(min_lag, 60)

    return device_data, _device_status_msg(tot_dev, lag)


def _process_job_data(
    jobs: list[dict[str, Any]], query: dict[str, Any]
) -> tuple[list[list[str]], str]:
    """Processes raw job data and returns list"""
    num_jobs = 0
    job_data = []
    for document in jobs:
        job_id = document.get("qbraidJobId", document.get("_id"))
        if job_id is None:
            continue
        created_at = document.get("createdAt")
        if created_at is None:
            timestamps = document.get("timestamps", {})
            created_at = timestamps.get("createdAt", timestamps.get("jobStarted"))
        status = document.get("qbraidStatus", document.get("status", "UNKNOWN"))
        num_jobs += 1
        job_data.append([job_id, created_at, status])

    return job_data, _job_status_msg(num_jobs, query)


def process_device_data(devices: list[dict[str, Any]]) -> tuple[list[list[str]], str]:
    """Processes raw device data and returns list of provider, name, qbraid_id, and status."""
    try:
        return _process_device_data(devices)
    except Exception as err:  # pylint: disable=broad-exception-caught
        raise QuantumServiceRuntimeError("Failed to process device data") from err


def process_job_data(
    jobs: list[dict[str, Any]], params: Optional[dict[str, Any]] = None
) -> tuple[list[list[str]], str]:
    """Processes raw job data and returns list of jobs and a status message."""
    params = params or {}

    try:
        return _process_job_data(jobs, params)
    except Exception as err:  # pylint: disable=broad-exception-caught
        raise QuantumServiceRuntimeError("Failed to process job data") from err


def transform_device_data(device_data: dict[str, Any]) -> dict[str, Any]:
    """
    Transforms the device data to be compatible with the qBraid API.

    Args:
        device_data (dict): The original device data dictionary.

    Returns:
        dict: The transformed device data dictionary.
    """
    # Create a copy of the input dictionary to avoid modifying the original data
    transformed_data = device_data.copy()

    # Normalize device type to upper case if it is a simulator
    if transformed_data.get("type") == "Simulator":
        transformed_data["type"] = "SIMULATOR"

    # Update device status based on availability
    if transformed_data.get("status") == "ONLINE" and not transformed_data.get("isAvailable", True):
        transformed_data["status"] = "UNAVAILABLE"

    return transformed_data
