# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module providing client for interacting with qBraid quantum services.

"""
import base64
import sys
import time
from json.decoder import JSONDecodeError
from typing import Any, Optional, Union

from requests.exceptions import JSONDecodeError as RequestsJSONDecodeError

from qbraid_core.client import QbraidClient
from qbraid_core.exceptions import RequestsApiError, ResourceNotFoundError
from qbraid_core.registry import register_client
from qbraid_core.system.executables import get_active_python_path, python_paths_equivalent

from .adapter import transform_device_data
from .exceptions import QuantumServiceRequestError
from .proxy import SUPPORTED_QJOB_LIBS, quantum_lib_proxy_state


@register_client()
class QuantumClient(QbraidClient):
    """Client for interacting with qBraid quantum services."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def search_devices(self, query: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        """Returns a list of quantum devices that match the given query filters."""
        query = query or {}

        # forward compatibility for casing transition
        if query.get("type") == "SIMULATOR":
            query["type"] = "Simulator"

        try:
            devices = self.session.get("/quantum-devices", params=query).json()
        except RequestsApiError as err:
            raise QuantumServiceRequestError(f"Failed to retrieve device data: {err}") from err

        return [transform_device_data(device) for device in devices]

    def search_jobs(self, query: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        """Returns a list of quantum jobs run by the user that match the given query filters."""
        query = query or {}

        max_results = query.pop("maxResults", None)
        if max_results is not None:
            query["resultsPerPage"] = max_results

        try:
            jobs_data = self.session.get("/quantum-jobs", params=query).json()
            if "jobsArray" in jobs_data:
                jobs_data = jobs_data["jobsArray"]
            return jobs_data
        except RequestsApiError as err:
            raise QuantumServiceRequestError(f"Failed to retrieve job data: {err}") from err

    def get_device(
        self,
        qbraid_id: Optional[str] = None,
        vendor_id: Optional[str] = None,
        object_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Returns the metadata corresponding to the specified quantum device."""
        query = {}
        if qbraid_id is not None:
            query["qbraid_id"] = qbraid_id
        if vendor_id is not None:
            query["objArg"] = vendor_id
        if object_id is not None:
            if not self._is_valid_object_id(object_id):
                raise ValueError(
                    "Invalid object_id format: expected a 24-character hexadecimal string"
                )
            query["_id"] = object_id
        if len(query) == 0:
            raise ValueError("Must provide either qbraid_id, vendor_id, or object_id")

        devices = self.search_devices(query=query)

        if len(devices) == 0:
            raise QuantumServiceRequestError("No devices found matching given criteria")

        device = devices[0]
        return transform_device_data(device)

    def get_job(
        self,
        qbraid_id: Optional[str] = None,
        vendor_id: Optional[str] = None,
        object_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Returns the metadata corresponding to the specified quantum job."""
        query = {}
        if qbraid_id is not None:
            query["qbraidJobId"] = qbraid_id
        if vendor_id is not None:
            query["vendorJobId"] = vendor_id
        if object_id is not None:
            if not self._is_valid_object_id(object_id):
                raise ValueError(
                    "Invalid object_id format: expected a 24-character hexadecimal string"
                )
            query["_id"] = object_id
        if len(query) == 0:
            raise ValueError("Must provide either qbraid_id, vendor_id, or object_id")

        jobs = self.search_jobs(query=query)

        if not jobs:
            raise QuantumServiceRequestError("No jobs found matching given criteria")

        job_data = jobs[0]

        return job_data

    def create_job(self, data: dict[str, Any]) -> dict[str, Any]:
        """Creates a new quantum job with the given data."""
        bitcode = data.get("bitcode")

        if bitcode is not None:
            data["bitcode"] = base64.b64encode(bitcode).decode("utf-8")

        try:
            return self.session.post("/quantum-jobs", json=data).json()
        except RequestsApiError as err:
            raise QuantumServiceRequestError(f"Failed to create job: {err}") from err

    def cancel_job(
        self,
        qbraid_id: Optional[str] = None,
        object_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Cancels the quantum job with the given qBraid ID."""
        if not qbraid_id and not object_id:
            raise ValueError("Must provide either qbraid_id or object_id")

        if qbraid_id and object_id:
            raise ValueError("Must provide either qbraid_id or object_id, not both")

        if qbraid_id:
            job_data = self.get_job(qbraid_id=qbraid_id)
            object_id = job_data.get("_id")

        if object_id is None or not self._is_valid_object_id(object_id):
            raise ValueError("Invalid object_id format: expected a 24-character hexadecimal string")

        try:
            return self.session.put(f"/quantum-jobs/cancel/{object_id}").json()
        except RequestsApiError as err:
            raise QuantumServiceRequestError(f"Failed to cancel job: {err}") from err

    def get_job_results(
        self, qbraid_id: str, max_retries: int = 5, wait_time: int = 2, backoff_factor: float = 2.0
    ) -> dict[str, Any]:
        """Returns the results of the quantum job with the given qBraid ID.

        Args:
            qbraid_id (str): The ID of the quantum job.
            max_retries (int, optional): The maximum number of retry attempts. Defaults to 3.
            wait_time (int, optional): The number of seconds to wait between retries. Defaults to 2.
            backoff_factor (float, optional): The factor by which to increase the wait time after
                each retry. Defaults to 2.0.

        Returns:
            dict[str, Any]: The data containing job results.

        Raises:
            QuantumServiceRequestError: If the request fails after multiple attempts or
                if there's an error in the response.
            ResourceNotFoundError: If no data is found for the specified job.
            RuntimeError: If an unexpected failure occurs after multiple retries.
        """
        for attempt in range(max_retries):
            try:
                response = self.session.get(f"/quantum-jobs/result/{qbraid_id}")
                resp_data: dict[str, Any] = response.json()

                error = resp_data.get("error")
                if error:
                    raise RequestsApiError(error)

                data = resp_data.get("data")
                if not data:
                    raise ResourceNotFoundError("No results found for job")

                return data

            except (RequestsApiError, JSONDecodeError, RequestsJSONDecodeError) as err:
                if attempt < max_retries - 1:
                    sleep_time = wait_time * (backoff_factor**attempt)
                    time.sleep(sleep_time)
                else:
                    raise QuantumServiceRequestError(
                        f"Failed to retrieve job results: {err}"
                    ) from err

        raise RuntimeError(  # pragma: no cover
            f"Unexpected failure after {max_retries} retries for job ID {qbraid_id}. "
            "This should not occur under normal operation. Please investigate or report "
            "at https://github.com/qBraid/qBraid/issues."
        )

    @staticmethod
    def qbraid_jobs_state(device_lib: Optional[str] = None) -> dict[str, Any]:
        """
        Checks if qBraid Quantum Jobs are enabled in the current environment for the
        specified device library.

        Args:
            device_lib (Optional[str]): The name of the quantum device library. If None,
                                        checks all supported libraries.

        Returns:
            dict[str, Any]: A dictionary containing the system's executable path and the states
                            of libraries relevant to qBraid Quantum Jobs. The libraries' states
                            include whether they are supported and enabled.
        """
        python_exe = get_active_python_path()
        environment_state: dict = {"exe": str(python_exe)}
        is_default_python = python_paths_equivalent(sys.executable, str(python_exe))

        check_libs = [device_lib] if device_lib else list(SUPPORTED_QJOB_LIBS.keys())

        libs_state = {
            lib: quantum_lib_proxy_state(lib, is_default_python=is_default_python)
            for lib in check_libs
        }

        environment_state["libs"] = libs_state

        return environment_state

    def estimate_cost(
        self,
        device_id: str,
        shots: Optional[int] = None,
        exec_min: Optional[Union[float, int]] = None,
    ) -> dict[str, float]:
        """
        Estimate the cost of running a quantum job on a specified device in qBraid credits,
        where 1 credit equals $0.01 USD.

        The estimated cost is based on the device's pricing model, which may include charges per
        task, per shot, and/or per minute. *Note*: The actual price charged may differ from this
        calculation. Visit https://docs.qbraid.com/home/pricing for the latest pricing information
        and details about qBraid credits.

        Args:
            device_id (str): Identifier for the quantum device.
            shots (Optional[int]): Number of repetitions (shots) of the quantum job.
            exec_min (Optional[Union[float, int]]): Estimated execution time in minutes.

        Returns:
            dict[str, float]: A dictionary with key 'estimatedCredits' giving float cost estimate.
        """
        if not shots and not exec_min:
            raise ValueError("Must provide either shots or exec_min")

        try:
            job_data = {"qbraidDeviceId": device_id, "shots": shots, "minutes": exec_min}
            return self.session.get("/quantum-jobs/cost-estimate", params=job_data).json()
        except RequestsApiError as err:
            raise QuantumServiceRequestError(f"Failed to estimate cost: {err}") from err
