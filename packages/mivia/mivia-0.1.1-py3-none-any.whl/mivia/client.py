"""Async MiViA API client."""

import asyncio
import os
from pathlib import Path
from typing import Self
from uuid import UUID

import httpx

from mivia.exceptions import (
    AuthenticationError,
    JobTimeoutError,
    MiviaError,
    NotFoundError,
    ServerError,
    ValidationError,
)
from mivia.models import (
    CreateJobsRequest,
    CreateReportRequest,
    CustomizationDto,
    ImageDto,
    JobDto,
    JobListResponse,
    JobStatus,
    ModelDto,
)


class MiviaClient:
    """Async HTTP client for MiViA API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
    ):
        """
        Initialize MiViA client.

        Args:
            api_key: API key. If None, reads from MIVIA_API_KEY env var.
            base_url: Base URL. If None, reads from MIVIA_BASE_URL or uses default.
            timeout: Request timeout in seconds.
        """
        self._api_key = api_key or os.environ.get("MIVIA_API_KEY")
        if not self._api_key:
            raise AuthenticationError("API key required. Set MIVIA_API_KEY env var.")

        self._base_url = (
            base_url
            or os.environ.get("MIVIA_BASE_URL")
            or "https://app.mivia.ai/api"
        )
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> Self:
        """Enter async context."""
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={"Authorization": self._api_key},
            timeout=self._timeout,
        )
        return self

    async def __aexit__(self, *args) -> None:
        """Exit async context."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure client is initialized."""
        if self._client is None:
            raise MiviaError("Client not initialized. Use 'async with' context.")
        return self._client

    def _handle_response(self, response: httpx.Response) -> None:
        """Handle HTTP response errors."""
        if response.status_code == 401:
            raise AuthenticationError()
        if response.status_code == 404:
            raise NotFoundError()
        if response.status_code == 400:
            try:
                detail = response.json().get("message", "Validation error")
            except Exception:
                detail = response.text
            raise ValidationError(str(detail))
        if response.status_code >= 500:
            raise ServerError(f"Server error: {response.status_code}")
        response.raise_for_status()

    # --- Image Operations ---

    async def upload_image(
        self,
        file_path: Path | str,
        forced: bool = False,
    ) -> ImageDto:
        """
        Upload single image.

        Args:
            file_path: Path to image file.
            forced: Bypass quality requirements.

        Returns:
            Uploaded image DTO.
        """
        images = await self.upload_images([file_path], [forced] if forced else None)
        return images[0]

    async def upload_images(
        self,
        file_paths: list[Path | str],
        forced: list[bool] | None = None,
        reuse_existing: bool = True,
    ) -> list[ImageDto]:
        """
        Upload multiple images.

        Args:
            file_paths: List of paths to image files.
            forced: List of forced flags per image.
            reuse_existing: If upload returns empty (duplicate), find existing image.

        Returns:
            List of uploaded image DTOs.
        """
        client = self._ensure_client()

        paths = [Path(p) for p in file_paths]
        files = [("files", (p.name, p.read_bytes())) for p in paths]

        # Server requires forced array (one per file)
        forced_flags = forced if forced else [False] * len(file_paths)
        data = {"forced": [str(f).lower() for f in forced_flags]}

        response = await client.post("/image", files=files, data=data)
        self._handle_response(response)
        uploaded = [ImageDto.model_validate(img) for img in response.json()]

        # If some images weren't uploaded (duplicates), find existing by filename
        if reuse_existing and len(uploaded) < len(paths):
            uploaded_names = {img.original_filename for img in uploaded}
            missing_names = {p.name for p in paths} - uploaded_names

            if missing_names:
                existing = await self.list_images()
                for img in existing:
                    if img.original_filename in missing_names:
                        uploaded.append(img)
                        missing_names.discard(img.original_filename)

        return uploaded

    async def list_images(self) -> list[ImageDto]:
        """
        List user's uploaded images.

        Returns:
            List of image DTOs.
        """
        client = self._ensure_client()
        response = await client.get("/image")
        self._handle_response(response)
        return [ImageDto.model_validate(img) for img in response.json()]

    async def delete_image(self, image_id: UUID) -> None:
        """
        Delete an image.

        Args:
            image_id: Image UUID.
        """
        client = self._ensure_client()
        response = await client.delete(f"/image/{image_id}")
        self._handle_response(response)

    # --- Model Operations ---

    async def list_models(self) -> list[ModelDto]:
        """
        List available models.

        Returns:
            List of model DTOs.
        """
        client = self._ensure_client()
        response = await client.get("/models")
        self._handle_response(response)
        return [ModelDto.model_validate(m) for m in response.json()]

    async def get_model_customizations(
        self, model_id: UUID
    ) -> list[CustomizationDto]:
        """
        Get customizations for a model.

        Args:
            model_id: Model UUID.

        Returns:
            List of customization DTOs.
        """
        client = self._ensure_client()
        response = await client.get(f"/models/{model_id}/customizations")
        self._handle_response(response)
        return [CustomizationDto.model_validate(c) for c in response.json()]

    # --- Job Operations ---

    async def create_jobs(
        self,
        image_ids: list[UUID],
        model_id: UUID,
        customization_id: UUID | None = None,
    ) -> list[JobDto]:
        """
        Create computation jobs.

        Args:
            image_ids: List of image UUIDs.
            model_id: Model UUID.
            customization_id: Optional customization UUID.

        Returns:
            List of created job DTOs.
        """
        client = self._ensure_client()

        request = CreateJobsRequest(
            image_ids=image_ids,
            model_id=model_id,
            customization_id=customization_id,
        )

        response = await client.post(
            "/jobs",
            json=request.model_dump(mode="json", by_alias=True, exclude_none=True),
        )
        self._handle_response(response)
        return [JobDto.model_validate(j) for j in response.json()]

    async def get_job(self, job_id: UUID) -> JobDto:
        """
        Get job details (v2 with results).

        Args:
            job_id: Job UUID.

        Returns:
            Job DTO with results.
        """
        client = self._ensure_client()
        response = await client.get(f"/v2/jobs/{job_id}")
        self._handle_response(response)
        return JobDto.model_validate(response.json())

    async def list_jobs(
        self,
        model_id: UUID | None = None,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "createdAt",
        sort_order: str = "desc",
    ) -> JobListResponse:
        """
        List jobs with pagination.

        Args:
            model_id: Optional filter by model.
            page: Page number (1-indexed).
            page_size: Items per page.
            sort_by: Sort field.
            sort_order: Sort order (asc/desc).

        Returns:
            Job list response with pagination.
        """
        client = self._ensure_client()

        params = {
            "page": page,
            "pageSize": page_size,
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }
        if model_id:
            params["modelId"] = str(model_id)

        response = await client.get("/v2/jobs", params=params)
        self._handle_response(response)
        return JobListResponse.model_validate(response.json())

    async def wait_for_job(
        self,
        job_id: UUID,
        timeout: float = 300.0,
        poll_interval: float = 2.0,
    ) -> JobDto:
        """
        Poll until job completes or times out.

        Args:
            job_id: Job UUID.
            timeout: Max wait time in seconds.
            poll_interval: Time between polls in seconds.

        Returns:
            Completed job DTO.

        Raises:
            JobTimeoutError: If timeout exceeded.
        """
        elapsed = 0.0
        while elapsed < timeout:
            job = await self.get_job(job_id)
            if job.status in (JobStatus.CACHED, JobStatus.NEW, JobStatus.FAILED):
                return job
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise JobTimeoutError(f"Job {job_id} did not complete within {timeout}s")

    async def wait_for_jobs(
        self,
        job_ids: list[UUID],
        timeout: float = 300.0,
        poll_interval: float = 2.0,
    ) -> list[JobDto]:
        """
        Wait for multiple jobs concurrently.

        Args:
            job_ids: List of job UUIDs.
            timeout: Max wait time in seconds.
            poll_interval: Time between polls in seconds.

        Returns:
            List of completed job DTOs.
        """
        tasks = [
            self.wait_for_job(jid, timeout, poll_interval)
            for jid in job_ids
        ]
        return await asyncio.gather(*tasks)

    # --- Report Operations ---

    async def download_pdf(
        self,
        job_ids: list[UUID],
        output_path: Path | str,
        tz_offset: int | None = None,
    ) -> Path:
        """
        Download PDF report.

        Args:
            job_ids: List of job UUIDs.
            output_path: Path to save PDF.
            tz_offset: Client timezone offset in minutes.

        Returns:
            Path to saved file.
        """
        client = self._ensure_client()

        request = CreateReportRequest(
            jobs_ids=job_ids,
            tz_offset=tz_offset,
        )

        response = await client.post(
            "/reports/pdf",
            json=request.model_dump(mode="json", by_alias=True, exclude_none=True),
        )
        self._handle_response(response)

        out = Path(output_path)
        out.write_bytes(response.content)
        return out

    async def download_csv(
        self,
        job_ids: list[UUID],
        output_path: Path | str,
        include_images: bool = True,
    ) -> Path:
        """
        Download CSV report (as zip).

        Args:
            job_ids: List of job UUIDs.
            output_path: Path to save ZIP.
            include_images: Include images in ZIP.

        Returns:
            Path to saved file.
        """
        client = self._ensure_client()

        request = CreateReportRequest(
            jobs_ids=job_ids,
            include_images=include_images,
        )

        response = await client.post(
            "/reports/csv",
            json=request.model_dump(mode="json", by_alias=True, exclude_none=True),
        )
        self._handle_response(response)

        out = Path(output_path)
        out.write_bytes(response.content)
        return out

    # --- High-Level Convenience ---

    async def analyze(
        self,
        file_paths: list[Path | str],
        model_id: UUID,
        customization_id: UUID | None = None,
        wait: bool = True,
        timeout: float = 300.0,
    ) -> list[JobDto]:
        """
        Upload images, create jobs, optionally wait for completion.

        Args:
            file_paths: List of image paths.
            model_id: Model UUID.
            customization_id: Optional customization UUID.
            wait: Wait for completion.
            timeout: Max wait time in seconds.

        Returns:
            List of job DTOs.
        """
        images = await self.upload_images(file_paths)
        jobs = await self.create_jobs(
            image_ids=[img.id for img in images],
            model_id=model_id,
            customization_id=customization_id,
        )

        if wait:
            jobs = await self.wait_for_jobs(
                [j.id for j in jobs],
                timeout=timeout,
            )

        return jobs
