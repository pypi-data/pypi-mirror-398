"""Task operations client."""

from __future__ import annotations

import json
import mimetypes
import os
import re
import warnings
from collections.abc import AsyncIterator, Iterable, Iterator
from typing import Any, BinaryIO, Mapping, Sequence

from ..core.pagination import Page
from ..models import (
    Task,
    TaskEditorial,
    TaskExamples,
    TaskIO,
    TaskLimits,
    TaskStatement,
    TaskStatementListEntry,
    TaskStatementSummary,
    TaskStatements,
    TestCase,
    TestSetDetail,
    TestSetShort,
    TestSetUploadEvent,
)
from .base import AsyncBaseClient, BaseClient

FileSource = os.PathLike[str] | str | bytes | bytearray | BinaryIO


class TasksClient(BaseClient):
    def list(
        self,
        hub: str,
        *,
        page: int = 1,
        page_size: int = 20,
        filters: Mapping[str, Any] | None = None,
    ) -> Page[Task]:
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if filters:
            params.update(filters)
        data = self._request("GET", f"/api/hubs/{hub}/tasks", params=params)
        return _build_task_page(data)

    def create(
        self, 
        hub: str, 
        *,
        name: str,
        time_limit: int,
        memory_limit: int,
        type: str = "batch",
        slug: str | None = None,
        visibility: str = "private",
    ) -> Task:
        """Create a new task in the hub."""
        payload = {
            "name": name,
            "time_limit": time_limit,
            "memory_limit": memory_limit,
            "type": type,
            "visibility": visibility,
        }
        if slug:
            payload["slug"] = slug
            
        data = self._request("POST", f"/api/hubs/{hub}/task/add/", json=payload)
        return Task.model_validate(data)

    def delete(self, hub: str, task_id: int) -> None:
        self._request("DELETE", f"/api/hubs/{hub}/task/{task_id}/delete")

    def bulk_delete(
        self,
        hub: str,
        *,
        task_ids: list[int] | None = None,
        task_names: list[str] | None = None,
    ) -> dict[str, Any]:
        payload = {}
        if task_ids:
            payload["ids"] = task_ids
        if task_names:
            payload["names"] = task_names
        return self._request("DELETE", f"/api/hubs/{hub}/tasks/bulk-delete", json=payload)

    def get_name(self, hub: str, task_id: int) -> dict[str, Any]:
        return self._request("GET", f"/api/hubs/{hub}/task/{task_id}/name/")

    def rename(self, hub: str, task_id: int, new_name: str) -> dict[str, Any]:
        return self._request(
            "PUT",
            f"/api/hubs/{hub}/task/{task_id}/name/update",
            json={"name": new_name},
        )

    def toggle_visibility(self, hub: str, task_id: int) -> dict[str, Any]:
        return self._request("PUT", f"/api/hubs/{hub}/task/{task_id}/visibility")

    def get_settings(self, hub: str, task_id: int) -> dict[str, Any]:
        return self._request("GET", f"/api/hubs/{hub}/task/{task_id}/settings")

    # Limits ----------------------------------------------------------------------

    def get_limits(self, hub: str, task_id: int) -> TaskLimits:
        data = self._request("GET", f"/api/hubs/{hub}/task/{task_id}/limits/update")
        return TaskLimits.model_validate(data)

    def update_limits(
        self,
        hub: str,
        task_id: int,
        *,
        time_limit: int,
        memory_limit: int,
    ) -> TaskLimits:
        payload = {"time_limit": time_limit, "memory_limit": memory_limit}
        data = self._request(
            "PUT",
            f"/api/hubs/{hub}/task/{task_id}/limits/update",
            json=payload,
        )
        return TaskLimits.model_validate(data)

    # Statement / editorial helpers -------------------------------------------------

    def get_statement(self, hub: str, task_id: int) -> TaskStatement:
        data = self._request("GET", f"/api/hubs/{hub}/task/{task_id}/statement")
        return TaskStatement.model_validate(data)

    def list_statements(self, hub: str, task_id: int) -> list[TaskStatementSummary]:
        data = self._request("GET", f"/api/hubs/{hub}/task/{task_id}/statements/list")
        if isinstance(data, list):
            return _statement_summaries_from_payload(data)
        if isinstance(data, Mapping):
            return _statement_summaries_from_payload([data])
        raise ValueError("Unexpected payload for statement list.")

    def list_statement_entries(self, hub: str, task_id: int) -> list[TaskStatementListEntry]:
        data = self._request("GET", f"/api/hubs/{hub}/task/{task_id}/statements/list")
        return _statement_entries_from_payload(data)

    def update_statement(
        self,
        hub: str,
        task_id: int,
        statement_id: int | None,
        body: dict[str, Any],
        *,
        language: str | None = None,
    ) -> TaskStatement:
        if statement_id is not None:
            warnings.warn(
                "Statement IDs are no longer used by the backend; `statement_id` is ignored.",
                DeprecationWarning,
                stacklevel=2,
            )
        lang_value = language or body.get("lang")
        if not isinstance(lang_value, str):
            raise ValueError("language is required when updating statement content.")
        payload = _ensure_lang_payload(body, lang_value)
        data = self._request(
            "PUT",
            f"/api/hubs/{hub}/task/{task_id}/statement/update",
            json=payload,
        )
        return TaskStatement.model_validate(data)

    def get_statements(self, hub: str, task_id: int, *, language: str | None = None) -> TaskStatements:
        params = {"lang": language} if language else None
        data = self._request(
            "GET",
            f"/api/hubs/{hub}/task/{task_id}/statement",
            params=params,
        )
        return TaskStatements.model_validate(data)

    def create_statement_language(
        self,
        hub: str,
        task_id: int,
        language: str,
        content: Mapping[str, Any],
    ) -> None:
        body = _ensure_lang_payload(content, language)
        self._request(
            "POST",
            f"/api/hubs/{hub}/task/{task_id}/statement/update",
            json=body,
        )

    def upsert_statement_language(
        self,
        hub: str,
        task_id: int,
        language: str,
        content: Mapping[str, Any],
    ) -> None:
        body = _ensure_lang_payload(content, language)
        self._request(
            "PUT",
            f"/api/hubs/{hub}/task/{task_id}/statement/update",
            json=body,
        )

    def delete_statement_language(self, hub: str, task_id: int, language: str) -> None:
        if not language:
            raise ValueError("language is required to delete statement content.")
        self._request(
            "DELETE",
            f"/api/hubs/{hub}/task/{task_id}/statement/update",
            json={"lang": language},
        )

    def get_editorial(self, hub: str, task_id: int) -> TaskEditorial:
        data = self._request("GET", f"/api/hubs/{hub}/task/{task_id}/editorial")
        return TaskEditorial.model_validate(data)

    def upload_statement_image(
        self,
        hub: str,
        task_id: int,
        file: os.PathLike[str] | str | bytes | BinaryIO | None = None,
        *,
        filename: str | None = None,
        content_type: str | None = None,
        files: Mapping[str, Any] | None = None,
    ) -> str | Mapping[str, Any]:
        """Upload an inline image for task statements.

        Legacy callers may continue passing an explicit ``files`` mapping; in that case the
        original response payload is returned unchanged. New callers can provide ``file`` and
        receive the uploaded image URL directly.
        """

        if files is not None:
            if file is not None:
                raise ValueError("Provide either 'file' or 'files', not both.")
            return self._request(
                "POST",
                f"/api/hubs/{hub}/task/{task_id}/statement/image",
                files=files,
            )

        if file is None:
            raise ValueError("file must be provided when 'files' is not supplied.")

        prepared = _prepare_file_field(
            "image",
            file,
            filename=filename,
            content_type=content_type,
        )
        response = self._request(
            "POST",
            f"/api/hubs/{hub}/task/{task_id}/statement/upload_image",
            files=prepared,
        )
        if isinstance(response, Mapping) and "image_url" in response:
            return str(response["image_url"])
        raise ValueError("Unexpected response payload for statement image upload.")

    # Testsets --------------------------------------------------------------------

    def list_testsets(
        self,
        hub: str,
        task_id: int,
        *,
        page: int = 1,
        page_size: int = 10,
    ) -> Page[TestSetShort]:
        params = {"page": page, "page_size": page_size}
        data = self._request("GET", f"/api/hubs/{hub}/task/{task_id}/testsets", params=params)
        return _build_testset_page(data)

    def get_testset(self, hub: str, task_id: int, testset_id: int) -> TestSetDetail:
        data = self._request(
            "GET",
            f"/api/hubs/{hub}/task/{task_id}/testset/{testset_id}",
        )
        return TestSetDetail.model_validate(data)

    def get_testcase(self, hub: str, task_id: int, testset_id: int, index: int) -> TestCase:
        data = self._request(
            "GET",
            f"/api/hubs/{hub}/task/{task_id}/testset/{testset_id}/test/{index}",
        )
        return TestCase.model_validate(data)

    def create_testset(
        self,
        hub: str,
        task_id: int,
        *,
        index: int | None = None,
    ) -> TestSetShort:
        payload = {"index": index} if index is not None else {}
        data = self._request(
            "POST",
            f"/api/hubs/{hub}/task/{task_id}/testset/create",
            json=payload or None,
        )
        return TestSetShort.model_validate(data)

    def delete_testset(self, hub: str, task_id: int, testset_id: int) -> None:
        self._request(
            "DELETE",
            f"/api/hubs/{hub}/task/{task_id}/testset/{testset_id}/delete",
        )

    def update_testset(
        self,
        hub: str,
        task_id: int,
        testset_id: int,
        **kwargs: Any,
    ) -> TestSetShort:
        if not kwargs:
            raise ValueError("At least one field must be provided to update the testset.")
        data = self._request(
            "PATCH",
            f"/api/hubs/{hub}/task/{task_id}/testset/{testset_id}/update",
            json=kwargs,
        )
        return TestSetShort.model_validate(data)

    def upload_testset_zip(
        self,
        hub: str,
        task_id: int,
        testset_id: int,
        zip_path: os.PathLike[str] | str | bytes | BinaryIO,
        *,
        stream: bool = True,
    ) -> Iterator[TestSetUploadEvent] | TestSetUploadEvent:
        files = _prepare_file_field(
            "testset_zip",
            zip_path,
            content_type="application/zip",
        )
        chunk_iter = self.transport.stream(
            "POST",
            f"/api/hubs/{hub}/task/{task_id}/testset/{testset_id}/upload",
            files=files,
        )
        events = _stream_upload_events(chunk_iter)
        if stream:
            return events
        terminal: TestSetUploadEvent | None = None
        for event in events:
            terminal = event
        if terminal is None:
            raise ValueError("No events were produced by the testset upload.")
        return terminal

    def upload_single_test(
        self,
        hub: str,
        task_id: int,
        testset_id: int,
        input_path: os.PathLike[str] | str | bytes | BinaryIO,
        answer_path: os.PathLike[str] | str | bytes | BinaryIO,
        *,
        pos: int = -1,
    ) -> None:
        files = {}
        files.update(
            _prepare_file_field("input_file", input_path),
        )
        files.update(
            _prepare_file_field("answer_file", answer_path),
        )
        data: dict[str, Any] | None = None
        if pos is not None:
            data = {"pos": str(pos)}
        self._request(
            "POST",
            f"/api/hubs/{hub}/task/{task_id}/testset/{testset_id}/upload-single",
            data=data,
            files=files,
        )

    def delete_testcase(self, hub: str, task_id: int, testset_id: int, index: int) -> None:
        params = {"test_index": index}
        self._request(
            "DELETE",
            f"/api/hubs/{hub}/task/{task_id}/testset/{testset_id}/delete-test",
            params=params,
        )

    def delete_testcases(
        self,
        hub: str,
        task_id: int,
        testset_id: int,
        indexes: Sequence[int],
    ) -> int:
        if not indexes:
            raise ValueError("indexes must contain at least one test index.")
        data = self._request(
            "DELETE",
            f"/api/hubs/{hub}/task/{task_id}/testset/{testset_id}/delete-multiple-tests",
            json={"test_indexes": list(indexes)},
        )
        return _extract_deleted_count(data, len(indexes))

    # Examples --------------------------------------------------------------------

    def get_examples(self, hub: str, task_id: int) -> TaskExamples:
        data = self._request("GET", f"/api/hubs/{hub}/task/{task_id}/examples")
        return TaskExamples.model_validate(data)

    def set_examples(
        self,
        hub: str,
        task_id: int,
        *,
        inputs: Sequence[str] | None = None,
        outputs: Sequence[str] | None = None,
    ) -> TaskExamples:
        if inputs is None and outputs is None:
            raise ValueError("At least one of 'inputs' or 'outputs' must be provided.")
        payload: dict[str, Any] = {}
        if inputs is not None:
            payload["example_inputs"] = list(inputs)
        if outputs is not None:
            payload["example_outputs"] = list(outputs)
        data = self._request(
            "PUT",
            f"/api/hubs/{hub}/task/{task_id}/examples/update",
            json=payload,
        )
        return TaskExamples.model_validate(data)

    def add_example(
        self,
        hub: str,
        task_id: int,
        *,
        input: str,
        output: str,
    ) -> TaskExamples:
        payload = {"example_input": input, "example_output": output}
        data = self._request(
            "POST",
            f"/api/hubs/{hub}/task/{task_id}/examples/update",
            json=payload,
        )
        return TaskExamples.model_validate(data)

    def get_io(self, hub: str, task_id: int) -> TaskIO:
        data = self._request("GET", f"/api/hubs/{hub}/task/{task_id}/io")
        return TaskIO.model_validate(data)

    def update_io(self, hub: str, task_id: int, payload: dict[str, Any]) -> TaskIO:
        data = self._request(
            "PUT",
            f"/api/hubs/{hub}/task/{task_id}/io",
            json=payload,
        )
        return TaskIO.model_validate(data)

    # Type / interactor / graders -------------------------------------------------

    def get_type(self, hub: str, task_id: int) -> dict[str, Any]:
        data = self._request("GET", f"/api/hubs/{hub}/task/{task_id}/type")
        if not isinstance(data, Mapping):
            raise ValueError("Unexpected payload for task type.")
        return dict(data)

    def update_type(self, hub: str, task_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        if "type" not in payload:
            raise ValueError("Payload must include the new task 'type'.")
        data = self._request(
            "PATCH",
            f"/api/hubs/{hub}/task/{task_id}/type/update",
            json=payload,
        )
        if not isinstance(data, Mapping):
            raise ValueError("Unexpected payload for task type update.")
        return dict(data)

    def get_interactor(self, hub: str, task_id: int) -> dict[str, Any]:
        data = self._request("GET", f"/api/hubs/{hub}/task/{task_id}/interactor/update")
        if not isinstance(data, Mapping):
            raise ValueError("Unexpected payload for task interactor.")
        return dict(data)

    def update_interactor(self, hub: str, task_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        data = self._request(
            "PUT",
            f"/api/hubs/{hub}/task/{task_id}/interactor/update",
            json=payload,
        )
        if not isinstance(data, Mapping):
            raise ValueError("Unexpected payload for task interactor update.")
        return dict(data)

    def get_checker(self, hub: str, task_id: int) -> dict[str, Any]:
        data = self._request("GET", f"/api/hubs/{hub}/task/{task_id}/checker/update")
        if not isinstance(data, Mapping):
            raise ValueError("Unexpected payload for task checker.")
        return dict(data)

    def update_checker(self, hub: str, task_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        if "checker_type" not in payload:
            raise ValueError("checker_type must be provided when updating the checker.")
        data = self._request(
            "PUT",
            f"/api/hubs/{hub}/task/{task_id}/checker/update",
            json=payload,
        )
        if not isinstance(data, Mapping):
            raise ValueError("Unexpected payload for task checker update.")
        return dict(data)

    def list_graders(self, hub: str, task_id: int) -> list[dict[str, Any]]:
        data = self._request("GET", f"/api/hubs/{hub}/task/{task_id}/graders")
        if isinstance(data, list):
            return [dict(item) for item in data if isinstance(item, Mapping)]
        raise ValueError("Unexpected payload for graders list.")

    def upsert_grader(self, hub: str, task_id: int, payload: dict[str, Any]) -> list[dict[str, Any]]:
        data = self._request(
            "PUT",
            f"/api/hubs/{hub}/task/{task_id}/graders",
            json=payload,
        )
        if isinstance(data, list):
            return [dict(item) for item in data if isinstance(item, Mapping)]
        raise ValueError("Unexpected payload for grader update.")

    def add_grader(self, hub: str, task_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        data = self._request(
            "POST",
            f"/api/hubs/{hub}/task/{task_id}/graders",
            json=payload,
        )
        if not isinstance(data, Mapping):
            raise ValueError("Unexpected payload for grader create.")
        return dict(data)

    def delete_grader(self, hub: str, task_id: int, programming_language: str) -> None:
        if not programming_language:
            raise ValueError("programming_language is required to delete a grader.")
        self._request(
            "DELETE",
            f"/api/hubs/{hub}/task/{task_id}/graders",
            json={"programming_language": programming_language},
        )


class AsyncTasksClient(AsyncBaseClient):
    async def list(
        self,
        hub: str,
        *,
        page: int = 1,
        page_size: int = 20,
        filters: Mapping[str, Any] | None = None,
    ) -> Page[Task]:
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if filters:
            params.update(filters)
        data = await self._request("GET", f"/api/hubs/{hub}/tasks", params=params)
        return _build_task_page(data)

    async def create(self, hub: str, payload: dict[str, Any]) -> Task:
        data = await self._request("POST", f"/api/hubs/{hub}/task/add/", json=payload)
        return Task.model_validate(data)

    async def delete(self, hub: str, task_id: int) -> None:
        await self._request("DELETE", f"/api/hubs/{hub}/task/{task_id}/delete")

    async def bulk_delete(
        self,
        hub: str,
        *,
        task_ids: list[int] | None = None,
        task_names: list[str] | None = None,
    ) -> dict[str, Any]:
        payload = {}
        if task_ids:
            payload["ids"] = task_ids
        if task_names:
            payload["names"] = task_names
        return await self._request("DELETE", f"/api/hubs/{hub}/tasks/bulk-delete", json=payload)

    async def get_name(self, hub: str, task_id: int) -> dict[str, Any]:
        return await self._request("GET", f"/api/hubs/{hub}/task/{task_id}/name/")

    async def rename(self, hub: str, task_id: int, new_name: str) -> dict[str, Any]:
        return await self._request(
            "PUT",
            f"/api/hubs/{hub}/task/{task_id}/name/update",
            json={"name": new_name},
        )

    async def toggle_visibility(self, hub: str, task_id: int) -> dict[str, Any]:
        return await self._request("PUT", f"/api/hubs/{hub}/task/{task_id}/visibility")

    async def get_settings(self, hub: str, task_id: int) -> dict[str, Any]:
        return await self._request("GET", f"/api/hubs/{hub}/task/{task_id}/settings")

    async def get_limits(self, hub: str, task_id: int) -> TaskLimits:
        data = await self._request("GET", f"/api/hubs/{hub}/task/{task_id}/limits/update")
        return TaskLimits.model_validate(data)

    async def update_limits(
        self,
        hub: str,
        task_id: int,
        *,
        time_limit: int,
        memory_limit: int,
    ) -> TaskLimits:
        payload = {"time_limit": time_limit, "memory_limit": memory_limit}
        data = await self._request(
            "PUT",
            f"/api/hubs/{hub}/task/{task_id}/limits/update",
            json=payload,
        )
        return TaskLimits.model_validate(data)

    async def get_statement(self, hub: str, task_id: int) -> TaskStatement:
        data = await self._request("GET", f"/api/hubs/{hub}/task/{task_id}/statement")
        return TaskStatement.model_validate(data)

    async def list_statements(self, hub: str, task_id: int) -> list[TaskStatementSummary]:
        data = await self._request("GET", f"/api/hubs/{hub}/task/{task_id}/statements/list")
        if isinstance(data, list):
            return _statement_summaries_from_payload(data)
        if isinstance(data, Mapping):
            return _statement_summaries_from_payload([data])
        raise ValueError("Unexpected payload for statement list.")

    async def list_statement_entries(self, hub: str, task_id: int) -> list[TaskStatementListEntry]:
        data = await self._request("GET", f"/api/hubs/{hub}/task/{task_id}/statements/list")
        return _statement_entries_from_payload(data)

    async def update_statement(
        self,
        hub: str,
        task_id: int,
        statement_id: int | None,
        payload: dict[str, Any],
        *,
        lang: str | None = None,
    ) -> TaskStatement:
        if statement_id is not None:
            warnings.warn(
                "Statement IDs are no longer used by the backend; `statement_id` is ignored.",
                DeprecationWarning,
                stacklevel=2,
            )
        lang_value = lang or payload.get("lang")
        if not isinstance(lang_value, str):
            raise ValueError("lang is required when updating statement content.")
        body = _ensure_lang_payload(payload, lang_value)
        data = await self._request(
            "PUT",
            f"/api/hubs/{hub}/task/{task_id}/statement/update",
            json=body,
        )
        return TaskStatement.model_validate(data)

    async def get_statements(
        self,
        hub: str,
        task_id: int,
        *,
        lang: str | None = None,
    ) -> TaskStatements:
        params = {"lang": lang} if lang else None
        data = await self._request(
            "GET",
            f"/api/hubs/{hub}/task/{task_id}/statement",
            params=params,
        )
        return TaskStatements.model_validate(data)

    async def create_statement_lang(
        self,
        hub: str,
        task_id: int,
        lang: str,
        payload: Mapping[str, Any],
    ) -> None:
        body = _ensure_lang_payload(payload, lang)
        await self._request(
            "POST",
            f"/api/hubs/{hub}/task/{task_id}/statement/update",
            json=body,
        )

    async def upsert_statement_lang(
        self,
        hub: str,
        task_id: int,
        lang: str,
        payload: Mapping[str, Any],
    ) -> None:
        body = _ensure_lang_payload(payload, lang)
        await self._request(
            "PUT",
            f"/api/hubs/{hub}/task/{task_id}/statement/update",
            json=body,
        )

    async def delete_statement_lang(self, hub: str, task_id: int, lang: str) -> None:
        if not lang:
            raise ValueError("lang is required to delete statement content.")
        await self._request(
            "DELETE",
            f"/api/hubs/{hub}/task/{task_id}/statement/update",
            json={"lang": lang},
        )

    async def get_editorial(self, hub: str, task_id: int) -> TaskEditorial:
        data = await self._request("GET", f"/api/hubs/{hub}/task/{task_id}/editorial")
        return TaskEditorial.model_validate(data)

    async def upload_statement_image(
        self,
        hub: str,
        task_id: int,
        file: os.PathLike[str] | str | bytes | BinaryIO | None = None,
        *,
        filename: str | None = None,
        content_type: str | None = None,
        files: Mapping[str, Any] | None = None,
    ) -> str | Mapping[str, Any]:
        if files is not None:
            if file is not None:
                raise ValueError("Provide either 'file' or 'files', not both.")
            return await self._request(
                "POST",
                f"/api/hubs/{hub}/task/{task_id}/statement/image",
                files=files,
            )

        if file is None:
            raise ValueError("file must be provided when 'files' is not supplied.")

        prepared = _prepare_file_field(
            "image",
            file,
            filename=filename,
            content_type=content_type,
        )
        response = await self._request(
            "POST",
            f"/api/hubs/{hub}/task/{task_id}/statement/upload_image",
            files=prepared,
        )
        if isinstance(response, Mapping) and "image_url" in response:
            return str(response["image_url"])
        raise ValueError("Unexpected response payload for statement image upload.")

    async def list_testsets(
        self,
        hub: str,
        task_id: int,
        *,
        page: int = 1,
        page_size: int = 10,
    ) -> Page[TestSetShort]:
        params = {"page": page, "page_size": page_size}
        data = await self._request("GET", f"/api/hubs/{hub}/task/{task_id}/testsets", params=params)
        return _build_testset_page(data)

    async def get_testset(self, hub: str, task_id: int, testset_id: int) -> TestSetDetail:
        data = await self._request(
            "GET",
            f"/api/hubs/{hub}/task/{task_id}/testset/{testset_id}",
        )
        return TestSetDetail.model_validate(data)

    async def get_testcase(
        self,
        hub: str,
        task_id: int,
        testset_id: int,
        index: int,
    ) -> TestCase:
        data = await self._request(
            "GET",
            f"/api/hubs/{hub}/task/{task_id}/testset/{testset_id}/test/{index}",
        )
        return TestCase.model_validate(data)

    async def create_testset(
        self,
        hub: str,
        task_id: int,
        *,
        index: int | None = None,
    ) -> TestSetShort:
        payload = {"index": index} if index is not None else {}
        data = await self._request(
            "POST",
            f"/api/hubs/{hub}/task/{task_id}/testset/create",
            json=payload or None,
        )
        return TestSetShort.model_validate(data)

    async def delete_testset(self, hub: str, task_id: int, testset_id: int) -> None:
        await self._request(
            "DELETE",
            f"/api/hubs/{hub}/task/{task_id}/testset/{testset_id}/delete",
        )

    async def update_testset(
        self,
        hub: str,
        task_id: int,
        testset_id: int,
        **kwargs: Any,
    ) -> TestSetShort:
        if not kwargs:
            raise ValueError("At least one field must be provided to update the testset.")
        data = await self._request(
            "PATCH",
            f"/api/hubs/{hub}/task/{task_id}/testset/{testset_id}/update",
            json=kwargs,
        )
        return TestSetShort.model_validate(data)

    async def upload_testset_zip(
        self,
        hub: str,
        task_id: int,
        testset_id: int,
        zip_path: os.PathLike[str] | str | bytes | BinaryIO,
        *,
        stream: bool = True,
    ) -> AsyncIterator[TestSetUploadEvent] | TestSetUploadEvent:
        files = _prepare_file_field(
            "testset_zip",
            zip_path,
            content_type="application/zip",
        )
        chunk_iter = await self.transport.stream(
            "POST",
            f"/api/hubs/{hub}/task/{task_id}/testset/{testset_id}/upload",
            files=files,
        )
        events = _async_stream_upload_events(chunk_iter)
        if stream:
            return events
        terminal: TestSetUploadEvent | None = None
        async for event in events:
            terminal = event
        if terminal is None:
            raise ValueError("No events were produced by the testset upload.")
        return terminal

    async def upload_single_test(
        self,
        hub: str,
        task_id: int,
        testset_id: int,
        input_path: os.PathLike[str] | str | bytes | BinaryIO,
        answer_path: os.PathLike[str] | str | bytes | BinaryIO,
        *,
        pos: int = -1,
    ) -> None:
        files = {}
        files.update(_prepare_file_field("input_file", input_path))
        files.update(_prepare_file_field("answer_file", answer_path))
        data: dict[str, Any] | None = None
        if pos is not None:
            data = {"pos": str(pos)}
        await self._request(
            "POST",
            f"/api/hubs/{hub}/task/{task_id}/testset/{testset_id}/upload-single",
            data=data,
            files=files,
        )

    async def delete_testcase(self, hub: str, task_id: int, testset_id: int, index: int) -> None:
        params = {"test_index": index}
        await self._request(
            "DELETE",
            f"/api/hubs/{hub}/task/{task_id}/testset/{testset_id}/delete-test",
            params=params,
        )

    async def delete_testcases(
        self,
        hub: str,
        task_id: int,
        testset_id: int,
        indexes: Sequence[int],
    ) -> int:
        if not indexes:
            raise ValueError("indexes must contain at least one test index.")
        data = await self._request(
            "DELETE",
            f"/api/hubs/{hub}/task/{task_id}/testset/{testset_id}/delete-multiple-tests",
            json={"test_indexes": list(indexes)},
        )
        return _extract_deleted_count(data, len(indexes))

    async def get_examples(self, hub: str, task_id: int) -> TaskExamples:
        data = await self._request("GET", f"/api/hubs/{hub}/task/{task_id}/examples")
        return TaskExamples.model_validate(data)

    async def set_examples(
        self,
        hub: str,
        task_id: int,
        *,
        inputs: Sequence[str] | None = None,
        outputs: Sequence[str] | None = None,
    ) -> TaskExamples:
        if inputs is None and outputs is None:
            raise ValueError("At least one of 'inputs' or 'outputs' must be provided.")
        payload: dict[str, Any] = {}
        if inputs is not None:
            payload["example_inputs"] = list(inputs)
        if outputs is not None:
            payload["example_outputs"] = list(outputs)
        data = await self._request(
            "PUT",
            f"/api/hubs/{hub}/task/{task_id}/examples/update",
            json=payload,
        )
        return TaskExamples.model_validate(data)

    async def add_example(
        self,
        hub: str,
        task_id: int,
        *,
        input: str,
        output: str,
    ) -> TaskExamples:
        payload = {"example_input": input, "example_output": output}
        data = await self._request(
            "POST",
            f"/api/hubs/{hub}/task/{task_id}/examples/update",
            json=payload,
        )
        return TaskExamples.model_validate(data)

    async def get_io(self, hub: str, task_id: int) -> TaskIO:
        data = await self._request("GET", f"/api/hubs/{hub}/task/{task_id}/io")
        return TaskIO.model_validate(data)

    async def update_io(self, hub: str, task_id: int, payload: dict[str, Any]) -> TaskIO:
        data = await self._request(
            "PUT",
            f"/api/hubs/{hub}/task/{task_id}/io",
            json=payload,
        )
        return TaskIO.model_validate(data)

    # Type / interactor / graders -------------------------------------------------

    async def get_type(self, hub: str, task_id: int) -> dict[str, Any]:
        data = await self._request("GET", f"/api/hubs/{hub}/task/{task_id}/type")
        if not isinstance(data, Mapping):
            raise ValueError("Unexpected payload for task type.")
        return dict(data)

    async def update_type(self, hub: str, task_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        if "type" not in payload:
            raise ValueError("Payload must include the new task 'type'.")
        data = await self._request(
            "PATCH",
            f"/api/hubs/{hub}/task/{task_id}/type/update",
            json=payload,
        )
        if not isinstance(data, Mapping):
            raise ValueError("Unexpected payload for task type update.")
        return dict(data)

    async def get_interactor(self, hub: str, task_id: int) -> dict[str, Any]:
        data = await self._request("GET", f"/api/hubs/{hub}/task/{task_id}/interactor/update")
        if not isinstance(data, Mapping):
            raise ValueError("Unexpected payload for task interactor.")
        return dict(data)

    async def update_interactor(self, hub: str, task_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        data = await self._request(
            "PUT",
            f"/api/hubs/{hub}/task/{task_id}/interactor/update",
            json=payload,
        )
        if not isinstance(data, Mapping):
            raise ValueError("Unexpected payload for task interactor update.")
        return dict(data)

    async def get_checker(self, hub: str, task_id: int) -> dict[str, Any]:
        data = await self._request("GET", f"/api/hubs/{hub}/task/{task_id}/checker/update")
        if not isinstance(data, Mapping):
            raise ValueError("Unexpected payload for task checker.")
        return dict(data)

    async def update_checker(self, hub: str, task_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        if "checker_type" not in payload:
            raise ValueError("checker_type must be provided when updating the checker.")
        data = await self._request(
            "PUT",
            f"/api/hubs/{hub}/task/{task_id}/checker/update",
            json=payload,
        )
        if not isinstance(data, Mapping):
            raise ValueError("Unexpected payload for task checker update.")
        return dict(data)

    async def list_graders(self, hub: str, task_id: int) -> list[dict[str, Any]]:
        data = await self._request("GET", f"/api/hubs/{hub}/task/{task_id}/graders")
        if isinstance(data, list):
            return [dict(item) for item in data if isinstance(item, Mapping)]
        raise ValueError("Unexpected payload for graders list.")

    async def upsert_grader(self, hub: str, task_id: int, payload: dict[str, Any]) -> list[dict[str, Any]]:
        data = await self._request(
            "PUT",
            f"/api/hubs/{hub}/task/{task_id}/graders",
            json=payload,
        )
        if isinstance(data, list):
            return [dict(item) for item in data if isinstance(item, Mapping)]
        raise ValueError("Unexpected payload for grader update.")

    async def add_grader(self, hub: str, task_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        data = await self._request(
            "POST",
            f"/api/hubs/{hub}/task/{task_id}/graders",
            json=payload,
        )
        if not isinstance(data, Mapping):
            raise ValueError("Unexpected payload for grader create.")
        return dict(data)

    async def delete_grader(self, hub: str, task_id: int, programming_language: str) -> None:
        if not programming_language:
            raise ValueError("programming_language is required to delete a grader.")
        await self._request(
            "DELETE",
            f"/api/hubs/{hub}/task/{task_id}/graders",
            json={"programming_language": programming_language},
        )


def _prepare_file_field(
    field: str,
    source: FileSource,
    *,
    filename: str | None = None,
    content_type: str | None = None,
) -> dict[str, Any]:
    if isinstance(source, (bytes, bytearray)):
        data = bytes(source)
        name = filename or field
        return {
            field: (
                name,
                data,
                content_type or _guess_content_type(name),
            )
        }

    if isinstance(source, (str, os.PathLike)):
        path = os.fspath(source)
        name = filename or os.path.basename(path) or field
        with open(path, "rb") as fh:
            data = fh.read()
        return {
            field: (
                name,
                data,
                content_type or _guess_content_type(name),
            )
        }

    if hasattr(source, "read"):
        name = filename or getattr(source, "name", field)
        file_obj = source
        if hasattr(file_obj, "seek"):
            try:
                file_obj.seek(0)
            except Exception:
                pass
        return {
            field: (
                name,
                file_obj,
                content_type or _guess_content_type(name),
            )
        }

    raise TypeError(f"Unsupported file source for field '{field}'.")


def _guess_content_type(filename: str | None) -> str:
    if filename:
        guessed, _ = mimetypes.guess_type(filename)
        if guessed:
            return guessed
    return "application/octet-stream"


def _statement_entries_from_payload(payload: Any) -> list[TaskStatementListEntry]:
    if isinstance(payload, list):
        return [TaskStatementListEntry.model_validate(item) for item in payload if isinstance(item, Mapping)]
    if isinstance(payload, Mapping):
        return [TaskStatementListEntry.model_validate(payload)]
    raise ValueError("Unexpected payload for statement entries.")


def _statement_summaries_from_payload(items: Iterable[Any]) -> list[TaskStatementSummary]:
    summaries: list[TaskStatementSummary] = []
    for item in items:
        if not isinstance(item, Mapping):
            raise ValueError("Statement summary payload must be a mapping.")
        if "language" in item:
            summaries.append(TaskStatementSummary.model_validate(item))
            continue
        title_map = item.get("title")
        if isinstance(title_map, Mapping):
            for lang, title in title_map.items():
                if isinstance(lang, str) and isinstance(title, str):
                    identifier = item.get("id")
                    if identifier is None:
                        continue
                    summaries.append(
                        TaskStatementSummary.model_validate(
                            {
                                "id": identifier,
                                "language": lang,
                                "title": title,
                            }
                        )
                    )
    return summaries


def _ensure_lang_payload(payload: Mapping[str, Any], lang: str) -> dict[str, Any]:
    if not lang:
        raise ValueError("lang must be provided.")
    body = dict(payload)
    existing_lang = body.get("lang")
    if existing_lang is None:
        body["lang"] = lang
    elif existing_lang != lang:
        raise ValueError("payload lang does not match provided lang argument.")
    return body


def _build_task_page(data: Any) -> Page[Task]:
    if not isinstance(data, Mapping):
        raise ValueError("Expected mapping payload for paginated tasks.")
    raw_results = data.get("results", [])
    if not isinstance(raw_results, list):
        raise ValueError("Expected list of results in paginated payload.")
    results = [Task.model_validate(item) for item in raw_results if isinstance(item, Mapping)]
    return Page(
        count=data.get("count"),
        next=data.get("next"),
        previous=data.get("previous"),
        results=results,
    )


def _build_testset_page(data: Any) -> Page[TestSetShort]:
    if not isinstance(data, Mapping):
        raise ValueError("Expected mapping payload for paginated testsets.")
    raw_results = data.get("results", [])
    if not isinstance(raw_results, list):
        raise ValueError("Expected list of results in paginated payload.")
    results = [TestSetShort.model_validate(item) for item in raw_results if isinstance(item, Mapping)]
    return Page(
        count=data.get("count"),
        next=data.get("next"),
        previous=data.get("previous"),
        results=results,
    )


def _extract_deleted_count(response: Any, fallback: int) -> int:
    if isinstance(response, Mapping):
        detail = response.get("detail")
        if isinstance(detail, str):
            match = re.search(r"(\\d+)", detail)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    pass
    return fallback


class _SSEDecoder:
    def __init__(self) -> None:
        self._buffer = ""

    def feed(self, chunk: str) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        self._buffer += chunk
        while "\n\n" in self._buffer:
            block, self._buffer = self._buffer.split("\n\n", 1)
            event = _parse_sse_block(block)
            if event is not None:
                events.append(event)
        return events

    def finalize(self) -> list[dict[str, Any]]:
        if not self._buffer:
            return []
        events = []
        event = _parse_sse_block(self._buffer)
        if event is not None:
            events.append(event)
        self._buffer = ""
        return events


def _parse_sse_block(block: str) -> dict[str, Any] | None:
    data_lines: list[str] = []
    for line in block.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
    if not data_lines:
        return None
    payload_text = "\n".join(data_lines).strip()
    if not payload_text:
        return None
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to decode SSE payload: {payload_text}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("SSE payload must be a JSON object.")
    return dict(payload)


def _stream_upload_events(chunks: Iterable[str]) -> Iterator[TestSetUploadEvent]:
    decoder = _SSEDecoder()
    for chunk in chunks:
        for payload in decoder.feed(chunk):
            yield TestSetUploadEvent.model_validate(payload)
    for payload in decoder.finalize():
        yield TestSetUploadEvent.model_validate(payload)


def _async_stream_upload_events(chunks: AsyncIterator[str]) -> AsyncIterator[TestSetUploadEvent]:
    async def _agen() -> AsyncIterator[TestSetUploadEvent]:
        decoder = _SSEDecoder()
        async for chunk in chunks:
            for payload in decoder.feed(chunk):
                yield TestSetUploadEvent.model_validate(payload)
        for payload in decoder.finalize():
            yield TestSetUploadEvent.model_validate(payload)

    return _agen()
