import os
import time
from enum import Enum
from typing import List, Optional
from datetime import datetime

from .api_client import APIException, APIClientBase, InvalidInputException


class JobWaitTimeout(APIException):
    def __init__(self, message: str = None):
        super().__init__(
            url=None,
            status_code=0,
            message=message or "Timed-out while waiting for job to complete",
        )


class JobStatus(str, Enum):
    running = "RUNNING"
    pending = "PENDING"
    succeeded = "SUCCEEDED"
    failed = "FAILED"
    canceled = "CANCELED"


class Jobs(APIClientBase):
    def __init__(self, url_base=None, **kwargs):
        super().__init__(url_base or os.environ.get("PROTECTION_SERVICE", ""), **kwargs)

    def get_jobs(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        types: Optional[List[str]] = None,
        free_text: Optional[str] = None,
        categories: Optional[List[str]] = None,
        statuses: Optional[List[str]] = None,
        created_after: Optional[datetime] = None,
        updated_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        sort_by: Optional[str] = None,
        sort_direction: Optional[str] = None,
        hide_acknowledged: Optional[bool] = None,
        hide_nested_jobs: Optional[bool] = None,
        object_id: Optional[str] = None,
        username: Optional[str] = None,
    ):
        query_params = {
            "limit": limit,
            "offset": offset,
            "types": types,
            "free_text": free_text,
            "categories": categories,
            "statuses": statuses,
            "created_after": created_after.isoformat() if created_after else None,
            "updated_after": updated_after.isoformat() if updated_after else None,
            "created_before": created_before.isoformat() if created_before else None,
            "sort_by": sort_by,
            "sort_direction": sort_direction,
            "hide_acknowledged": hide_acknowledged,
            "hide_nested_jobs": hide_nested_jobs,
            "object_id": object_id,
            "username": username,
        }

        query_params = {k: v for k, v in query_params.items() if v is not None}

        query_list = []
        for key, value in query_params.items():
            if isinstance(value, list):
                query_list.extend((key, v) for v in value)
            else:
                query_list.append((key, value))

        return self.get_request("/jobs", query_args=query_list)

    def get_job(self, id: str):
        if not id:
            raise InvalidInputException(f"Expected a valid job id, received: `{id}`")
        return self.get_request("/jobs/{id}", id=id)

    def create_job(self, body: dict):
        return self.post_request("/jobs", body=body)

    def patch_job(self, id: str, body: dict):
        if not id:
            raise InvalidInputException(f"Expected a valid job id, received: `{id}`")
        return self.patch_request("/jobs/{id}", id=id, body=body)

    def delete_job(self, id: str):
        if not id:
            raise InvalidInputException(f"Expected a valid job id, received: `{id}`")
        return self.delete_request("/jobs/{id}", id=id)

    def wait_for_job_completion(self, id: str, timeout: float, waiting_func=None):
        def sync_get_job(id):
            try:
                return self.get_job(str(id))
            except APIException as e:
                if e.status_code == 404:
                    return None
                else:
                    raise e

        async def async_get_job(id):
            try:
                return await self.get_job(str(id))
            except APIException as e:
                if e.status_code == 404:
                    return None
                else:
                    raise e

        if self._use_asyncio:
            return _async_wait_for_job_completion(id, timeout, async_get_job, waiting_func)
        else:
            return _sync_wait_for_job_completion(id, timeout, sync_get_job, waiting_func)


def _default_sync_waiting_func(timeout: float):
    time.sleep(timeout)
    return False


def _has_ended(job):
    if not job:
        return False
    return job.get("status") in [JobStatus.succeeded.value, JobStatus.failed.value, JobStatus.canceled.value]


def _sync_wait_for_job_completion(id: str, timeout: float, job_getter, waiting_func=None):
    start_time = time.monotonic()
    job = job_getter(id)
    waiting_func = waiting_func if waiting_func else _default_sync_waiting_func
    while not _has_ended(job):
        wait_cancelled = waiting_func(timeout=0.8)
        wait_time = time.monotonic() - start_time

        job = job_getter(id)
        if wait_cancelled:
            return job

        if wait_time >= timeout and not _has_ended(job):
            raise JobWaitTimeout()
    return job


async def _async_wait_for_job_completion(id: str, timeout: float):
    raise NotImplementedError("The asyncio client does not support waiting for job completion at this time")


class V1Jobs(Jobs):
    def __init__(self, url_base=None, **kwargs):
        url_base_v1 = f"{url_base or os.environ.get('PROTECTION_SERVICE', '')}/v1/"
        super().__init__(url_base_v1, **kwargs)

    def get_jobs(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        types: Optional[List[str]] = None,
        freeText: Optional[str] = None,
        categories: Optional[List[str]] = None,
        statuses: Optional[List[str]] = None,
        createdAfter: Optional[datetime] = None,
        updatedAfter: Optional[datetime] = None,
        createdBefore: Optional[datetime] = None,
        sortBy: Optional[str] = None,
        sortDirection: Optional[str] = None,
        hideAcknowledged: Optional[bool] = None,
        hideNestedJobs: Optional[bool] = None,
        objectId: Optional[str] = None,
        username: Optional[str] = None,
    ):
        query_params = {
            "limit": limit,
            "offset": offset,
            "types": types,
            "freeText": freeText,
            "categories": categories,
            "statuses": statuses,
            "createdAfter": createdAfter.isoformat() if createdAfter else None,
            "updatedAfter": updatedAfter.isoformat() if updatedAfter else None,
            "createdBefore": createdBefore.isoformat() if createdBefore else None,
            "sortBy": sortBy,
            "sortDirection": sortDirection,
            "hideAcknowledged": hideAcknowledged,
            "hideNestedJobs": hideNestedJobs,
            "objectId": objectId,
            "username": username,
        }

        query_params = {k: v for k, v in query_params.items() if v is not None}

        query_list = []
        for key, value in query_params.items():
            if isinstance(value, list):
                query_list.extend((key, v) for v in value)
            else:
                query_list.append((key, value))

        return self.get_request("/jobs", query_args=query_list)
