"""Synchronous wrapper for MiViA API client."""

import asyncio
from pathlib import Path
from uuid import UUID

from mivia.client import MiviaClient
from mivia.models import (
    CustomizationDto,
    ImageDto,
    JobDto,
    JobListResponse,
    ModelDto,
)


class SyncMiviaClient:
    """Synchronous wrapper for MiviaClient."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
    ):
        """
        Initialize sync MiViA client.

        Args:
            api_key: API key. If None, reads from MIVIA_API_KEY env var.
            base_url: Base URL. If None, reads from MIVIA_BASE_URL or uses default.
            timeout: Request timeout in seconds.
        """
        self._api_key = api_key
        self._base_url = base_url
        self._timeout = timeout

    def _run(self, coro):
        """Run coroutine in event loop."""
        return asyncio.run(coro)

    async def _execute(self, method_name: str, *args, **kwargs):
        """Execute async method within context."""
        async with MiviaClient(
            api_key=self._api_key,
            base_url=self._base_url,
            timeout=self._timeout,
        ) as client:
            method = getattr(client, method_name)
            return await method(*args, **kwargs)

    # --- Image Operations ---

    def upload_image(
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
        return self._run(self._execute("upload_image", file_path, forced))

    def upload_images(
        self,
        file_paths: list[Path | str],
        forced: list[bool] | None = None,
    ) -> list[ImageDto]:
        """
        Upload multiple images.

        Args:
            file_paths: List of paths to image files.
            forced: List of forced flags per image.

        Returns:
            List of uploaded image DTOs.
        """
        return self._run(self._execute("upload_images", file_paths, forced))

    def list_images(self) -> list[ImageDto]:
        """
        List user's uploaded images.

        Returns:
            List of image DTOs.
        """
        return self._run(self._execute("list_images"))

    def delete_image(self, image_id: UUID) -> None:
        """
        Delete an image.

        Args:
            image_id: Image UUID.
        """
        return self._run(self._execute("delete_image", image_id))

    # --- Model Operations ---

    def list_models(self) -> list[ModelDto]:
        """
        List available models.

        Returns:
            List of model DTOs.
        """
        return self._run(self._execute("list_models"))

    def get_model_customizations(self, model_id: UUID) -> list[CustomizationDto]:
        """
        Get customizations for a model.

        Args:
            model_id: Model UUID.

        Returns:
            List of customization DTOs.
        """
        return self._run(self._execute("get_model_customizations", model_id))

    # --- Job Operations ---

    def create_jobs(
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
        return self._run(
            self._execute("create_jobs", image_ids, model_id, customization_id)
        )

    def get_job(self, job_id: UUID) -> JobDto:
        """
        Get job details (v2 with results).

        Args:
            job_id: Job UUID.

        Returns:
            Job DTO with results.
        """
        return self._run(self._execute("get_job", job_id))

    def list_jobs(
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
        return self._run(
            self._execute("list_jobs", model_id, page, page_size, sort_by, sort_order)
        )

    def wait_for_job(
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
        return self._run(
            self._execute("wait_for_job", job_id, timeout, poll_interval)
        )

    def wait_for_jobs(
        self,
        job_ids: list[UUID],
        timeout: float = 300.0,
        poll_interval: float = 2.0,
    ) -> list[JobDto]:
        """
        Wait for multiple jobs.

        Args:
            job_ids: List of job UUIDs.
            timeout: Max wait time in seconds.
            poll_interval: Time between polls in seconds.

        Returns:
            List of completed job DTOs.
        """
        return self._run(
            self._execute("wait_for_jobs", job_ids, timeout, poll_interval)
        )

    # --- Report Operations ---

    def download_pdf(
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
        return self._run(
            self._execute("download_pdf", job_ids, output_path, tz_offset)
        )

    def download_csv(
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
        return self._run(
            self._execute("download_csv", job_ids, output_path, include_images)
        )

    # --- High-Level Convenience ---

    def analyze(
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
        return self._run(
            self._execute(
                "analyze", file_paths, model_id, customization_id, wait, timeout
            )
        )
