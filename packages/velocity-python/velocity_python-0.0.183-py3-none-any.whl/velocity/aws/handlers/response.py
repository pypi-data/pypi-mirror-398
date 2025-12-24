import sys
import time
import traceback
from typing import Any, Dict, List, Optional
from velocity.misc.format import to_json


class Response:
    """Class to manage and structure HTTP responses with various actions and custom headers."""

    VALID_VARIANTS = {"success", "error", "warning", "info"}

    def __init__(self):
        """Initialize the Response object with default status, headers, and an empty actions list."""
        self.actions: List[Dict[str, Any]] = []
        self.jobs = JobEnvelope(self)
        self.body: Dict[str, Any] = {}
        self.raw: Dict[str, Any] = {
            "statusCode": 200,
            "body": "{}",
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
            },
        }

    def render(self) -> Dict[str, Any]:
        """
        Finalize the response body as JSON and return the complete response dictionary.

        Returns:
            Dict[str, Any]: The complete HTTP response with headers, status code, and JSON body.
        """
        if self.actions:
            self.body["actions"] = self.actions
        if self.jobs.events:
            self.body["jobs"] = {"events": self.jobs.events}
        self.raw["body"] = to_json(self.body)
        return self.raw

    def alert(self, message: str, title: str = "Notification") -> "Response":
        """
        Add an alert action to the response.

        Args:
            message (str): The alert message.
            title (str): Title for the alert. Defaults to "Notification".

        Returns:
            Response: The current Response object, allowing method chaining.
        """
        self.actions.append(
            {
                "action": "alert",
                "payload": {"title": title, "message": message},
            }
        )
        return self

    def toast(self, message: str, variant: str = "success") -> "Response":
        """
        Add a toast notification action to the response with a specified variant.

        Args:
            message (str): The message to display in the toast.
            variant (str): The style variant of the toast (e.g., "success", "error"). Must be one of VALID_VARIANTS.

        Raises:
            ValueError: If the variant is not one of VALID_VARIANTS.

        Returns:
            Response: The current Response object, allowing method chaining.
        """
        variant = variant.lower()
        if variant not in self.VALID_VARIANTS:
            raise ValueError(
                f"Notistack variant '{variant}' not in {self.VALID_VARIANTS}"
            )
        self.actions.append(
            {
                "action": "toast",
                "payload": {"options": {"variant": variant}, "message": message},
            }
        )
        return self

    def load_object(self, payload: Dict[str, Any]) -> "Response":
        """
        Add a load-object action to the response with a specified payload.

        Args:
            payload (Dict[str, Any]): The data to load into the response.

        Returns:
            Response: The current Response object, allowing method chaining.
        """
        self.actions.append({"action": "load-object", "payload": payload})
        return self

    def update_store(self, payload: Dict[str, Any]) -> "Response":
        """
        Add an update-store action to the response with a specified payload.

        Args:
            payload (Dict[str, Any]): The data to update the store with.

        Returns:
            Response: The current Response object, allowing method chaining.
        """
        self.actions.append({"action": "update-store", "payload": payload})
        return self

    def file_download(self, payload: Dict[str, Any]) -> "Response":
        """
        Add a file-download action to the response with a specified payload.

        Args:
            payload (Dict[str, Any]): The data for file download details.

        Returns:
            Response: The current Response object, allowing method chaining.
        """
        self.actions.append({"action": "file-download", "payload": payload})
        return self

    def status(self, code: Optional[int] = None) -> int:
        """
        Get or set the status code of the response.

        Args:
            code (Optional[int]): The HTTP status code to set. If None, returns the current status code.

        Returns:
            int: The current status code.
        """
        if code is not None:
            self.raw["statusCode"] = int(code)
        return self.raw["statusCode"]

    def headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Get or update the headers of the response.

        Args:
            headers (Optional[Dict[str, str]]): A dictionary of headers to add or update.

        Returns:
            Dict[str, str]: The current headers after updates.
        """
        if headers:
            formatted_headers = {
                self._format_header_key(k): v for k, v in headers.items()
            }
            self.raw["headers"].update(formatted_headers)
        return self.raw["headers"]

    def set_status(self, code: int) -> "Response":
        """
        Set the HTTP status code of the response.

        Args:
            code (int): The status code to set.

        Returns:
            Response: The current Response object, allowing method chaining.
        """
        self.status(code)
        return self

    def set_headers(self, headers: Dict[str, str]) -> "Response":
        """
        Set custom headers for the response.

        Args:
            headers (Dict[str, str]): The headers to add or update.

        Returns:
            Response: The current Response object, allowing method chaining.
        """
        self.headers(headers)
        return self

    def set_body(self, body: Dict[str, Any]) -> "Response":
        """
        Update the body of the response with new data.

        Args:
            body (Dict[str, Any]): The body data to update.

        Returns:
            Response: The current Response object, allowing method chaining.
        """
        self.body.update(body)
        return self

    def exception(self) -> None:
        """
        Capture and format the current exception details and set a 500 status code.
        Includes traceback information if DEBUG mode is enabled.
        """
        exc_type, exc_value, tb = sys.exc_info()
        self.set_status(500)
        self.set_body(
            {
                "python_exception": {
                    "type": str(exc_type),
                    "value": str(exc_value),
                    "traceback": traceback.format_exc(),
                    "tb": traceback.format_tb(tb) if tb else [],
                }
            }
        )

    def console(self, message: str, title: str = "Notification") -> "Response":
        """
        Add a console log action to the response.

        Args:
            message (str): The console message.
            title (str): Title for the console message. Defaults to "Notification".

        Returns:
            Response: The current Response object, allowing method chaining.
        """
        self.actions.append(
            {
                "action": "console",
                "payload": {"title": title, "message": message},
            }
        )
        return self

    def redirect(self, location: str) -> "Response":
        """
        Add a redirect action to the response with the target location.

        Args:
            location (str): The URL to redirect to.

        Returns:
            Response: The current Response object, allowing method chaining.
        """
        self.actions.append({"action": "redirect", "payload": {"location": location}})
        return self

    def signout(self) -> "Response":
        """
        Add a signout action to the response.

        Returns:
            Response: The current Response object, allowing method chaining.
        """
        self.actions.append({"action": "signout"})
        return self

    def set_table(self, payload: Dict[str, Any]) -> "Response":
        """
        Add a set-table action to the response with the specified payload.

        Args:
            payload (Dict[str, Any]): The table data to set.

        Returns:
            Response: The current Response object, allowing method chaining.
        """
        self.actions.append({"action": "set-table", "payload": payload})
        return self

    def set_repo(self, payload: Dict[str, Any]) -> "Response":
        """
        Add a set-repo action to the response with the specified payload.

        Args:
            payload (Dict[str, Any]): The repository data to set.

        Returns:
            Response: The current Response object, allowing method chaining.
        """
        self.actions.append({"action": "set-repo", "payload": payload})
        return self

    @staticmethod
    def _format_header_key(key: str) -> str:
        """
        Format HTTP headers to be in a title-cased format.

        Args:
            key (str): The header key to format.

        Returns:
            str: The formatted header key.
        """
        return "-".join(word.capitalize() for word in key.split("-"))


class JobEnvelope:
    """Structured helper for emitting job lifecycle events in API responses."""

    def __init__(self, response: "Response") -> None:
        self._response = response
        self.events: List[Dict[str, Any]] = []

    def start(
        self,
        *,
        job_id: Any,
        label: Optional[str] = None,
        job_key: Optional[str] = None,
        status: Optional[str] = None,
        detail: Optional[str] = None,
        auto_download: Optional[bool] = True,
        poll_interval: Optional[int] = 3000,
        batch_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        cancellable: Optional[bool] = None,
        cancel_action: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record the starting state for a long-running job."""

        job = self._build_job(
            job_id,
            label=label,
            job_key=job_key,
            status=status or "Queued",
            detail=detail or "Queued",
            auto_download=auto_download,
            poll_interval=poll_interval,
            batch_id=batch_id,
            metadata=metadata,
            cancellable=cancellable,
            cancel_action=cancel_action,
        )
        return self._record_event("start", job)

    def progress(
        self,
        *,
        job_id: Any,
        percent: Optional[float] = None,
        detail: Optional[str] = None,
        status: Optional[str] = None,
        stage: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Report progress for an in-flight job."""

        job = self._build_job(
            job_id,
            percent=percent,
            detail=detail,
            status=status,
            stage=stage,
            metadata=metadata,
            partial=True,
        )
        return self._record_event("progress", job)

    def complete(
        self,
        *,
        job_id: Any,
        detail: Optional[str] = None,
        result: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_download: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Mark the job as completed."""

        job = self._build_job(
            job_id,
            status="Completed",
            detail=detail,
            result=result,
            metadata=metadata,
            auto_download=auto_download,
            partial=True,
        )
        return self._record_event("complete", job)

    def fail(
        self,
        *,
        job_id: Any,
        detail: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Mark the job as failed."""

        job = self._build_job(
            job_id,
            status="Failed",
            detail=detail or error,
            error=error,
            metadata=metadata,
            partial=True,
        )
        return self._record_event("failed", job)

    def cancel(
        self,
        *,
        job_id: Any,
        detail: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Mark the job as cancelled."""

        job = self._build_job(
            job_id,
            status="Cancelled",
            detail=detail,
            metadata=metadata,
            partial=True,
        )
        return self._record_event("cancelled", job)

    def _record_event(self, event_type: str, job: Dict[str, Any]) -> Dict[str, Any]:
        if not job.get("jobId"):
            raise ValueError("jobId is required for job events")
        self.events.append(
            {
                "type": event_type,
                "job": job,
                "timestamp": int(time.time() * 1000),
            }
        )
        return job

    def _build_job(
        self,
        job_id: Any,
        *,
        label: Optional[str] = None,
        job_key: Optional[str] = None,
        status: Optional[str] = None,
        detail: Optional[str] = None,
        auto_download: Optional[bool] = None,
        poll_interval: Optional[int] = None,
        batch_id: Optional[str] = None,
        percent: Optional[float] = None,
        stage: Optional[str] = None,
        result: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        cancellable: Optional[bool] = None,
        cancel_action: Optional[str] = None,
        error: Optional[str] = None,
        partial: bool = False,
    ) -> Dict[str, Any]:
        job: Dict[str, Any] = {"jobId": str(job_id)}

        def assign(key: str, value: Any) -> None:
            if value is not None:
                job[key] = value

        assign("jobKey", job_key)
        assign("label", label)
        assign("status", status)
        assign("detail", detail)
        assign("autoDownload", auto_download)
        assign("pollInterval", poll_interval)
        assign("batchId", batch_id)
        assign("percent", percent)
        assign("stage", stage)
        assign("result", result)
        assign("metadata", metadata)
        assign("cancellable", cancellable)
        assign("cancelAction", cancel_action)
        assign("error", error)

        if partial and "detail" not in job and status:
            job["detail"] = status

        return job
