########################################################################################################################
# IMPORTS

import base64
import json
import logging
import tempfile
import time
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from openai import OpenAI
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_exponential

########################################################################################################################
# PARAMETERS

logger = logging.getLogger(__name__)

########################################################################################################################
# BASE CLASSES


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    """

    @abstractmethod
    def invoke_text(
        self,
        *,
        instructions: str,
        input_texts: List[str],
        model: str,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        **kwargs,
    ) -> Tuple[str, Dict[str, Any], Any]:
        """
        Generate text output from the LLM.
        Supports both local images (image_path) and image URLs (image_url).
        """
        pass

    @abstractmethod
    def invoke_structured(
        self,
        *,
        instructions: str,
        input_texts: List[str],
        model_schema: Type[BaseModel],
        model: str,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        **kwargs,
    ) -> Tuple[BaseModel, Dict[str, Any], Any]:
        """
        Generate structured output from the LLM using a Pydantic schema.
        Supports both local images (image_path) and image URLs (image_url).
        """
        pass


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI provider implementation using the 'client.responses' pattern.
    """

    def __init__(self, api_key: str, default_model: str = "gpt-4o-mini") -> None:
        self.client = OpenAI(api_key=api_key)
        self.default_model = default_model

    @staticmethod
    def _batch_to_dict(batch) -> Dict[str, Any]:
        """
        Convert an OpenAI Batch object to a dictionary.

        Uses model_dump() for robust serialization that adapts to SDK changes.

        Args:
            batch: OpenAI Batch object (Pydantic model)

        Returns:
            Dictionary representation of the batch
        """
        return batch.model_dump()

    @staticmethod
    def _encode_image(image_path: str) -> str:
        """Encodes a local image file to a base64 string."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    @staticmethod
    def _get_image_media_type(image_path: str) -> str:
        """
        Determine the media type based on file extension.

        Supported formats: PNG, JPEG, WEBP, non-animated GIF

        Args:
            image_path: Path to the image file

        Returns:
            Media type string (e.g., "image/jpeg", "image/png")
        """
        extension = Path(image_path).suffix.lower()
        media_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        return media_types.get(extension, "not_compatible")  # Return 'not_compatible' for unsupported extensions

    @staticmethod
    def _is_url(path: str) -> bool:
        """Check if the provided path is a URL."""
        return path.startswith(("http://", "https://"))

    def _build_vision_content(
        self,
        input_texts: List[str],
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        detail: str = "auto",
    ) -> List[Dict[str, Any]]:
        """
        Builds the content list for the user message following OpenAI Responses API pattern.
        Handles text and optional image (from local file or URL) for Vision capabilities.

        Args:
            input_texts: List of text strings to include
            image_path: Path to a local image file (will be base64 encoded)
            image_url: URL of an image (used directly)

        Returns:
            List of content dictionaries with proper OpenAI Responses API format
        """
        content = []

        # Add text inputs using input_text type
        for text in input_texts:
            content.append({"type": "input_text", "text": text})

        # Add image if provided (prioritize image_url over image_path)
        if image_url:
            # Use URL directly with input_image type (OpenAI Responses API format)
            content.append({"type": "input_image", "image_url": image_url})
        elif image_path:
            # Check if image_path is actually a URL
            if self._is_url(image_path):
                content.append({"type": "input_image", "image_url": image_path})
            else:
                # Local file: encode to base64 and use data URL with correct media type
                base64_image = self._encode_image(image_path)
                media_type = self._get_image_media_type(image_path)
                if media_type == "not_compatible":
                    raise ValueError(f"Unsupported image format for file: {image_path}")
                content.append(
                    {"type": "input_image", "image_url": f"data:{media_type};base64,{base64_image}", "detail": detail}
                )

        return content

    @staticmethod
    def _extract_usage_meta(resp) -> Dict[str, Any]:
        """
        Extract usage metadata.
        Note: The structure of 'resp' depends on the specific API version.
        We attempt to read standard usage fields.
        """
        usage = getattr(resp, "usage", None)
        return {
            "response_id": getattr(resp, "id", None),
            "model": getattr(resp, "model", None),
            "input_tokens": getattr(usage, "input_tokens", 0) if usage else 0,
            "output_tokens": getattr(usage, "output_tokens", 0) if usage else 0,
        }

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
        retry=retry_if_not_exception_type(ValidationError),
    )
    def invoke_text(
        self,
        *,
        instructions: str,
        input_texts: List[str],
        model: str,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        **kwargs,
    ) -> Tuple[str, Dict[str, Any], Any]:
        """
        Generate text output using 'client.responses.create'.

        Args:
            instructions: System instructions for the model
            input_texts: List of text inputs
            model: Model identifier
            image_path: Path to local image file OR image URL (auto-detected)
            image_url: Direct image URL (takes priority over image_path)
            **kwargs: Additional arguments

        Returns:
            Tuple of (output_text, usage_metadata, raw_response)

        Examples:
            # Text only
            >>> text, meta, _ = provider.invoke_text(
            ...     instructions="Summarize",
            ...     input_texts=["Long text here..."],
            ...     model="gpt-4o-mini"
            ... )

            # With image URL
            >>> text, meta, _ = provider.invoke_text(
            ...     instructions="Describe this image",
            ...     input_texts=["What's in this image?"],
            ...     model="gpt-4o-mini",
            ...     image_url="https://example.com/image.jpg"
            ... )
        """
        t0 = time.time()

        # Build content with optional image support
        user_content = self._build_vision_content(input_texts, image_path, image_url, detail="high")

        # Construct input list (System + User)
        input_payload = [
            {"role": "system", "content": instructions},
            {"role": "user", "content": user_content},
        ]

        logger.info(f"Prompting {model} (text via responses.create)...")

        # Using the requested syntax
        resp = self.client.responses.create(
            model=model,
            input=input_payload,
            **kwargs,
        )
        # Extract output text
        output_text = getattr(resp, "output_text", "")
        if not output_text and hasattr(resp, "choices"):
            output_text = resp.choices[0].message.content

        meta = self._extract_usage_meta(resp) | {"latency_sec": round(time.time() - t0, 3)}
        return output_text, meta, resp

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
        retry=retry_if_not_exception_type(ValidationError),
    )
    def invoke_structured(
        self,
        *,
        instructions: str,
        input_texts: List[str],
        model_schema: Type[BaseModel],
        model: str,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        detail: Optional[str] = None,
        **kwargs,
    ) -> Tuple[BaseModel, Dict[str, Any], Any]:
        """
        Generate structured output using 'client.responses.parse'.
        Strictly follows the syntax: client.responses.parse(model=..., input=..., text_format=...)

        Args:
            instructions: System instructions for the model
            input_texts: List of text inputs
            model_schema: Pydantic model class for structured output
            model: Model identifier
            image_path: Path to local image file OR image URL (auto-detected)
            image_url: Direct image URL (takes priority over image_path)
            **kwargs: Additional arguments

        Returns:
            Tuple of (pydantic_instance, usage_metadata, raw_response)
        """
        t0 = time.time()

        # Prepare content (handles text + optional image from path or URL)
        user_content_list = self._build_vision_content(input_texts, image_path, image_url, detail)

        # Construct input payload
        input_payload = [
            {"role": "system", "content": instructions},
            {"role": "user", "content": user_content_list},
        ]

        logger.info(f"Prompting {model} (structured via responses.parse)...")

        # EXACT SYNTAX REQUESTED
        resp = self.client.responses.parse(model=model, input=input_payload, text_format=model_schema, **kwargs)

        # Access parsed output as requested: response.output_parsed
        parsed_output = resp.output_parsed

        meta = self._extract_usage_meta(resp) | {"latency_sec": round(time.time() - t0, 3)}
        return parsed_output, meta, resp

    # invoke_chat implementation omitted or mapped to invoke_text depending on need
    def invoke_chat(self, **kwargs):
        raise NotImplementedError("Chat method not implemented for Responses API pattern.")

    # ==========================================================================================================
    # BATCH PROCESSING METHODS
    # ==========================================================================================================

    def _build_batch_request(
        self,
        custom_id: str,
        instructions: str,
        input_texts: List[str],
        model: str,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        endpoint: str = "/v1/responses",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Build a single batch request in the format required by OpenAI Batch API.

        Args:
            custom_id: Unique identifier for this request (used to match results)
            instructions: System instructions for the model
            input_texts: List of text inputs
            model: Model identifier
            image_path: Path to local image file OR image URL (auto-detected)
            image_url: Direct image URL (takes priority over image_path)
            endpoint: API endpoint ("/v1/responses" or "/v1/chat/completions")
            **kwargs: Additional arguments for the API call

        Returns:
            Dictionary representing a single batch request line
        """
        # Build content with optional image support
        user_content = self._build_vision_content(input_texts, image_path, image_url, detail="high")

        # Construct input payload
        input_payload = [
            {"role": "system", "content": instructions},
            {"role": "user", "content": user_content},
        ]

        return {
            "custom_id": custom_id,
            "method": "POST",
            "url": endpoint,
            "body": {
                "model": model,
                "input": input_payload,
                **kwargs,
            },
        }

    def create_batch_file(
        self,
        requests: List[Dict[str, Any]],
        output_path: Optional[str] = None,
    ) -> str:
        """
        Create a JSONL batch input file from a list of request configurations.

        Args:
            requests: List of request configurations. Each dict should have:
                - custom_id: Unique identifier
                - instructions: System instructions
                - input_texts: List of input texts
                - model: Model to use (optional, uses default)
                - image_url: Image URL (optional)
                - image_path: Local image path (optional)
                - Any additional kwargs for the API
            output_path: Path to save the JSONL file (optional, creates temp file if not provided)

        Returns:
            Path to the created JSONL file

        Example:
            >>> requests = [
            ...     {"custom_id": "req-1", "instructions": "Summarize", "input_texts": ["Text 1..."]},
            ...     {"custom_id": "req-2", "instructions": "Summarize", "input_texts": ["Text 2..."]},
            ... ]
            >>> filepath = provider.create_batch_file(requests)
        """
        if output_path is None:
            with tempfile.NamedTemporaryFile(suffix=".jsonl", prefix="batch_input_", delete=False) as temp_file:
                output_path = temp_file.name

        with open(output_path, "w", encoding="utf-8") as f:
            for req in requests:
                custom_id = req.get("custom_id", str(uuid.uuid4()))
                instructions = req.get("instructions", "")
                input_texts = req.get("input_texts", [])
                model = req.get("model", self.default_model)
                image_url = req.get("image_url")
                image_path = req.get("image_path")
                endpoint = req.get("endpoint", "/v1/responses")

                # Get additional kwargs (exclude known keys)
                known_keys = {
                    "custom_id",
                    "instructions",
                    "input_texts",
                    "model",
                    "image_url",
                    "image_path",
                    "endpoint",
                }
                extra_kwargs = {k: v for k, v in req.items() if k not in known_keys}

                batch_request = self._build_batch_request(
                    custom_id=custom_id,
                    instructions=instructions,
                    input_texts=input_texts,
                    model=model,
                    image_path=image_path,
                    image_url=image_url,
                    endpoint=endpoint,
                    **extra_kwargs,
                )

                f.write(json.dumps(batch_request, ensure_ascii=False) + "\n")

        logger.info(f"Created batch file with {len(requests)} requests: {output_path}")
        return output_path

    def upload_batch_file(self, filepath: str) -> str:
        """
        Upload a batch input file to OpenAI.

        Args:
            filepath: Path to the JSONL batch file

        Returns:
            File ID from OpenAI

        Example:
            >>> file_id = provider.upload_batch_file("batch_input.jsonl")
            >>> print(file_id)  # "file-abc123"
        """
        with open(filepath, "rb") as f:
            file_obj = self.client.files.create(file=f, purpose="batch")

        logger.info(f"Uploaded batch file: {file_obj.id}")
        return file_obj.id

    def create_batch(
        self,
        input_file_id: str,
        endpoint: str = "/v1/responses",
        completion_window: str = "24h",
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new batch processing job.

        Args:
            input_file_id: ID of the uploaded batch input file
            endpoint: API endpoint ("/v1/responses" or "/v1/chat/completions")
            completion_window: Time window for completion ("24h")
            metadata: Optional metadata dict for the batch

        Returns:
            Batch object with job details

        Example:
            >>> batch = provider.create_batch("file-abc123")
            >>> print(batch["id"])  # "batch_abc123"
            >>> print(batch["status"])  # "validating"
        """
        batch = self.client.batches.create(
            input_file_id=input_file_id,
            endpoint=endpoint,
            completion_window=completion_window,
            metadata=metadata,
        )

        batch_dict = self._batch_to_dict(batch)

        logger.info(f"Created batch: {batch.id} (status: {batch.status})")
        return batch_dict

    def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """
        Get the current status of a batch job.

        Args:
            batch_id: ID of the batch

        Returns:
            Batch object with current status

        Status values:
            - validating: Input file being validated
            - failed: Validation failed
            - in_progress: Batch is running
            - finalizing: Completing and preparing results
            - completed: Done, results ready
            - expired: Did not complete in time
            - cancelling: Being cancelled
            - cancelled: Was cancelled
        """
        batch = self.client.batches.retrieve(batch_id)

        return self._batch_to_dict(batch)

    def wait_for_batch(
        self,
        batch_id: str,
        poll_interval: float = 30.0,
        timeout: Optional[float] = None,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """
        Wait for a batch job to complete, polling periodically.

        Args:
            batch_id: ID of the batch
            poll_interval: Seconds between status checks (default: 30)
            timeout: Maximum seconds to wait (default: None = no timeout)
            callback: Optional function called with status on each poll

        Returns:
            Final batch status

        Raises:
            TimeoutError: If timeout is reached before completion
            RuntimeError: If batch fails or is cancelled

        Example:
            >>> def on_update(status):
            ...     print(f"Status: {status['status']}, Completed: {status['request_counts']['completed']}")
            >>> result = provider.wait_for_batch("batch_abc123", callback=on_update)
        """
        start_time = time.time()
        terminal_statuses = {"completed", "failed", "expired", "cancelled"}

        while True:
            status = self.get_batch_status(batch_id)

            if callback:
                callback(status)

            if status["status"] in terminal_statuses:
                if status["status"] == "completed":
                    logger.info(f"Batch {batch_id} completed successfully")
                elif status["status"] == "failed":
                    raise RuntimeError(f"Batch {batch_id} failed")
                elif status["status"] == "expired":
                    raise RuntimeError(f"Batch {batch_id} expired before completion")
                elif status["status"] == "cancelled":
                    raise RuntimeError(f"Batch {batch_id} was cancelled")

                return status

            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Timeout waiting for batch {batch_id}")

            logger.debug(
                f"Batch {batch_id} status: {status['status']} "
                f"({status['request_counts']['completed']}/{status['request_counts']['total']} completed)"
            )

            time.sleep(poll_interval)

    @staticmethod
    def _parse_jsonl_content(content: str) -> List[Dict[str, Any]]:
        """
        Parse JSONL (JSON Lines) content into a list of dictionaries.

        Args:
            content: Raw JSONL content string

        Returns:
            List of parsed JSON objects
        """
        results = []
        for line in content.strip().split("\n"):
            if line:
                results.append(json.loads(line))
        return results

    def _save_batch_results_to_file(self, content: str, output_path: str) -> None:
        """
        Save batch results content to a file.

        Args:
            content: Raw JSONL content to save
            output_path: Path where to save the file
        """
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Saved batch results to: {output_path}")

    def _fetch_and_parse_file(self, file_id: str) -> List[Dict[str, Any]]:
        """
        Fetch a file from OpenAI and parse its JSONL content.

        Args:
            file_id: ID of the file to fetch

        Returns:
            List of parsed JSON objects from the file
        """
        file_response = self.client.files.content(file_id)
        return self._parse_jsonl_content(file_response.text)

    def _process_output_file(
        self,
        batch_id: str,
        output_file_id: Optional[str],
        output_path: Optional[str],
    ) -> List[Dict[str, Any]]:
        """
        Process successful batch results from the output file.

        Args:
            batch_id: ID of the batch (for logging)
            output_file_id: ID of the output file (None if no successes)
            output_path: Path to optionally save results

        Returns:
            List of result dictionaries from successful requests
        """
        if not output_file_id:
            if output_path:
                logger.warning(f"No output file for batch {batch_id}, skipping save to {output_path}")
            return []

        file_response = self.client.files.content(output_file_id)
        content = file_response.text

        if output_path:
            self._save_batch_results_to_file(content, output_path)

        return self._parse_jsonl_content(content)

    def _process_error_file(self, batch_id: str, error_file_id: Optional[str]) -> List[Dict[str, Any]]:
        """
        Process error results from the error file.

        Args:
            batch_id: ID of the batch (for logging)
            error_file_id: ID of the error file (None if no errors)

        Returns:
            List of error dictionaries
        """
        if not error_file_id:
            return []

        logger.info(f"Batch {batch_id} has errors (file: {error_file_id}). Fetching...")
        try:
            return self._fetch_and_parse_file(error_file_id)
        except Exception as e:
            logger.error(f"Failed to retrieve error file {error_file_id}: {e}")
            return []

    def get_batch_results(
        self,
        batch_id: str,
        output_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve results from a completed batch.

        Args:
            batch_id: ID of the batch
            output_path: Optional path to save the raw JSONL output

        Returns:
            List of result dictionaries, each containing:
                - custom_id: The original request ID
                - response: Response data (if successful)
                - error: Error data (if failed)

        Example:
            >>> results = provider.get_batch_results("batch_abc123")
            >>> for r in results:
            ...     print(f"{r['custom_id']}: {r['response']['body']['output_text']}")
        """
        status = self.get_batch_status(batch_id)

        if status["status"] != "completed":
            raise RuntimeError(f"Batch {batch_id} is not completed (status: {status['status']})")

        # Process both output and error files
        output_results = self._process_output_file(
            batch_id,
            status.get("output_file_id"),
            output_path,
        )
        error_results = self._process_error_file(batch_id, status.get("error_file_id"))

        results = output_results + error_results

        # Log warning if batch has no results
        if not results and not status.get("output_file_id") and not status.get("error_file_id"):
            logger.warning(f"Batch {batch_id} completed but has no output or error file.")

        logger.info(f"Retrieved {len(results)} results from batch {batch_id}")
        return results

    def get_batch_errors(self, batch_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve errors from a batch (if any).

        Args:
            batch_id: ID of the batch

        Returns:
            List of error dictionaries
        """
        status = self.get_batch_status(batch_id)

        error_file_id = status["error_file_id"]
        if not error_file_id:
            return []

        file_response = self.client.files.content(error_file_id)
        content = file_response.text

        errors = []
        for line in content.strip().split("\n"):
            if line:
                errors.append(json.loads(line))

        return errors

    def cancel_batch(self, batch_id: str) -> Dict[str, Any]:
        """
        Cancel a running batch job.

        Args:
            batch_id: ID of the batch to cancel

        Returns:
            Updated batch status
        """
        batch = self.client.batches.cancel(batch_id)
        logger.info(f"Cancelling batch {batch_id}")

        return self._batch_to_dict(batch)

    def list_batches(self, limit: int = 20, after: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all batches.

        Args:
            limit: Maximum number of batches to return
            after: Cursor for pagination

        Returns:
            List of batch objects
        """
        batches = self.client.batches.list(limit=limit, after=after)

        return [self._batch_to_dict(b) for b in batches.data]

    def submit_batch(
        self,
        requests: List[Dict[str, Any]],
        endpoint: str = "/v1/responses",
        metadata: Optional[Dict[str, str]] = None,
        wait: bool = False,
        poll_interval: float = 30.0,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Tuple[str, Optional[List[Dict[str, Any]]]]:
        """
        High-level method to submit a batch job (create file, upload, and start batch).

        Args:
            requests: List of request configurations (see create_batch_file for format)
            endpoint: API endpoint ("/v1/responses" or "/v1/chat/completions")
            metadata: Optional metadata for the batch
            wait: If True, wait for completion and return results
            poll_interval: Seconds between status checks when waiting
            callback: Optional callback for status updates when waiting

        Returns:
            Tuple of (batch_id, results). Results is None if wait=False.

        Example:
            >>> requests = [
            ...     {"custom_id": "img-1", "instructions": "Describe", "input_texts": ["What is this?"], "image_url": "..."},
            ...     {"custom_id": "img-2", "instructions": "Describe", "input_texts": ["What is this?"], "image_url": "..."},
            ... ]
            >>> batch_id, results = provider.submit_batch(requests, wait=True)
            >>> for r in results:
            ...     print(f"{r['custom_id']}: {r['response']['body']['output_text']}")
        """
        # Step 1: Create the batch file
        filepath = self.create_batch_file(requests)

        try:
            # Step 2: Upload the file
            file_id = self.upload_batch_file(filepath)

            # Step 3: Create the batch
            batch = self.create_batch(
                input_file_id=file_id,
                endpoint=endpoint,
                metadata=metadata,
            )

            batch_id = batch["id"]

            if not wait:
                return batch_id, None

            # Step 4: Wait for completion
            self.wait_for_batch(batch_id, poll_interval=poll_interval, callback=callback)

            # Step 5: Get results
            results = self.get_batch_results(batch_id)

            return batch_id, results

        finally:
            # Clean up temp file
            Path(filepath).unlink(missing_ok=True)


########################################################################################################################
# MAIN INTERFACE


class LLMInterface:
    """
    Unified interface for working with Large Language Models.
    """

    SUPPORTED_PROVIDERS = {
        "openai": OpenAIProvider,
    }

    def __init__(self, config) -> None:
        if "llm" not in config:
            raise ValueError("Configuration must contain 'llm' section")

        llm_config = config["llm"]
        self.provider_name = llm_config.get("provider", "openai").lower()

        if self.provider_name not in self.SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider '{self.provider_name}'")

        api_key = llm_config.get("api_key")
        if not api_key:
            raise ValueError(f"API key required for provider '{self.provider_name}'")

        default_model = llm_config.get("model", "gpt-5-nano")

        provider_class = self.SUPPORTED_PROVIDERS[self.provider_name]
        self.provider: BaseLLMProvider = provider_class(api_key=api_key, default_model=default_model)
        self.default_model = default_model

        logger.info(f"Initialized LLM interface with provider: {self.provider_name}")

    def invoke_text(
        self,
        *,
        instructions: str,
        input_texts: List[str],
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> Tuple[str, Dict[str, Any], Any]:
        """
        Wrapper for text generation with optional Vision support.

        Args:
            instructions: System instructions for the model
            input_texts: List of text inputs
            image_path: Path to local image file OR image URL (auto-detected)
            image_url: Direct image URL (takes priority over image_path)
            model: Model identifier (uses default if not specified)
            **kwargs: Additional arguments

        Returns:
            Tuple of (output_text, usage_metadata, raw_response)

        Examples:
            # Text only
            >>> text, meta, _ = llm.invoke_text(
            ...     instructions="Translate to Spanish",
            ...     input_texts=["Hello world"]
            ... )

            # With image URL
            >>> text, meta, _ = llm.invoke_text(
            ...     instructions="Describe what you see",
            ...     input_texts=["What's in this image?"],
            ...     image_url="https://example.com/image.jpg"
            ... )

            # With local image
            >>> text, meta, _ = llm.invoke_text(
            ...     instructions="Read the text",
            ...     input_texts=["Extract text from this image"],
            ...     image_path="/path/to/document.jpg"
            ... )
        """
        model = model or self.default_model
        return self.provider.invoke_text(
            instructions=instructions,
            input_texts=input_texts,
            model=model,
            image_path=image_path,
            image_url=image_url,
            **kwargs,
        )

    def invoke_structured(
        self,
        *,
        instructions: str,
        input_texts: List[str],
        model_schema: Type[BaseModel],
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> Tuple[BaseModel, Dict[str, Any], Any]:
        """
        Wrapper for structured output generation with Vision support.

        Args:
            instructions: System instructions for the model
            input_texts: List of text inputs
            model_schema: Pydantic model class for structured output
            image_path: Path to local image file OR image URL (auto-detected)
            image_url: Direct image URL (takes priority over image_path)
            model: Model identifier (uses default if not specified)
            **kwargs: Additional arguments

        Returns:
            Tuple of (pydantic_instance, usage_metadata, raw_response)

        Examples:
            # Using image URL
            >>> result, meta, _ = llm.invoke_structured(
            ...     instructions="Describe this image",
            ...     input_texts=["What do you see?"],
            ...     model_schema=ImageDescription,
            ...     image_url="https://example.com/image.jpg"
            ... )

            # Using local image file
            >>> result, meta, _ = llm.invoke_structured(
            ...     instructions="Extract text from image",
            ...     input_texts=["Read the label"],
            ...     model_schema=LabelText,
            ...     image_path="/path/to/image.jpg"
            ... )

            # image_path also accepts URLs (auto-detected)
            >>> result, meta, _ = llm.invoke_structured(
            ...     instructions="Analyze",
            ...     input_texts=["What is this?"],
            ...     model_schema=Analysis,
            ...     image_path="https://example.com/photo.jpg"
            ... )
        """
        model = model or self.default_model
        return self.provider.invoke_structured(
            instructions=instructions,
            input_texts=input_texts,
            model_schema=model_schema,
            model=model,
            image_path=image_path,
            image_url=image_url,
            **kwargs,
        )

    def get_default_model(self) -> str:
        return self.default_model

    # ==========================================================================================================
    # BATCH PROCESSING METHODS
    # ==========================================================================================================

    def create_batch_file(
        self,
        requests: List[Dict[str, Any]],
        output_path: Optional[str] = None,
    ) -> str:
        """
        Create a JSONL batch input file from a list of request configurations.

        Args:
            requests: List of request configurations. Each dict should have:
                - custom_id: Unique identifier
                - instructions: System instructions
                - input_texts: List of input texts
                - model: Model to use (optional, uses default)
                - image_url: Image URL (optional)
                - image_path: Local image path (optional)
                - Any additional kwargs for the API
            output_path: Path to save the JSONL file (optional, creates temp file if not provided)

        Returns:
            Path to the created JSONL file
        """
        if not hasattr(self.provider, "create_batch_file"):
            raise NotImplementedError(f"Batch processing not supported by {self.provider_name} provider")
        return self.provider.create_batch_file(requests, output_path)

    def upload_batch_file(self, filepath: str) -> str:
        """
        Upload a batch input file to the provider.

        Args:
            filepath: Path to the JSONL batch file

        Returns:
            File ID from the provider
        """
        if not hasattr(self.provider, "upload_batch_file"):
            raise NotImplementedError(f"Batch processing not supported by {self.provider_name} provider")
        return self.provider.upload_batch_file(filepath)

    def create_batch(
        self,
        input_file_id: str,
        endpoint: str = "/v1/responses",
        completion_window: str = "24h",
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new batch processing job.

        Args:
            input_file_id: ID of the uploaded batch input file
            endpoint: API endpoint ("/v1/responses" or "/v1/chat/completions")
            completion_window: Time window for completion ("24h")
            metadata: Optional metadata dict for the batch

        Returns:
            Batch object with job details
        """
        if not hasattr(self.provider, "create_batch"):
            raise NotImplementedError(f"Batch processing not supported by {self.provider_name} provider")
        return self.provider.create_batch(input_file_id, endpoint, completion_window, metadata)

    def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """
        Get the current status of a batch job.

        Args:
            batch_id: ID of the batch

        Returns:
            Batch object with current status
        """
        if not hasattr(self.provider, "get_batch_status"):
            raise NotImplementedError(f"Batch processing not supported by {self.provider_name} provider")
        return self.provider.get_batch_status(batch_id)

    def wait_for_batch(
        self,
        batch_id: str,
        poll_interval: float = 30.0,
        timeout: Optional[float] = None,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """
        Wait for a batch job to complete, polling periodically.

        Args:
            batch_id: ID of the batch
            poll_interval: Seconds between status checks (default: 30)
            timeout: Maximum seconds to wait (default: None = no timeout)
            callback: Optional function called with status on each poll

        Returns:
            Final batch status

        Raises:
            TimeoutError: If timeout is reached before completion
            RuntimeError: If batch fails or is cancelled
        """
        if not hasattr(self.provider, "wait_for_batch"):
            raise NotImplementedError(f"Batch processing not supported by {self.provider_name} provider")
        return self.provider.wait_for_batch(batch_id, poll_interval, timeout, callback)

    def get_batch_results(
        self,
        batch_id: str,
        output_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve results from a completed batch.

        Args:
            batch_id: ID of the batch
            output_path: Optional path to save the raw JSONL output

        Returns:
            List of result dictionaries, each containing:
                - custom_id: The original request ID
                - response: Response data (if successful)
                - error: Error data (if failed)
        """
        if not hasattr(self.provider, "get_batch_results"):
            raise NotImplementedError(f"Batch processing not supported by {self.provider_name} provider")
        return self.provider.get_batch_results(batch_id, output_path)

    def get_batch_errors(self, batch_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve errors from a batch (if any).

        Args:
            batch_id: ID of the batch

        Returns:
            List of error dictionaries
        """
        if not hasattr(self.provider, "get_batch_errors"):
            raise NotImplementedError(f"Batch processing not supported by {self.provider_name} provider")
        return self.provider.get_batch_errors(batch_id)

    def cancel_batch(self, batch_id: str) -> Dict[str, Any]:
        """
        Cancel a running batch job.

        Args:
            batch_id: ID of the batch to cancel

        Returns:
            Updated batch status
        """
        if not hasattr(self.provider, "cancel_batch"):
            raise NotImplementedError(f"Batch processing not supported by {self.provider_name} provider")
        return self.provider.cancel_batch(batch_id)

    def list_batches(self, limit: int = 20, after: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all batches.

        Args:
            limit: Maximum number of batches to return
            after: Cursor for pagination

        Returns:
            List of batch objects
        """
        if not hasattr(self.provider, "list_batches"):
            raise NotImplementedError(f"Batch processing not supported by {self.provider_name} provider")
        return self.provider.list_batches(limit, after)

    def submit_batch(
        self,
        requests: List[Dict[str, Any]],
        endpoint: str = "/v1/responses",
        metadata: Optional[Dict[str, str]] = None,
        wait: bool = False,
        poll_interval: float = 30.0,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Tuple[str, Optional[List[Dict[str, Any]]]]:
        """
        High-level method to submit a batch job (create file, upload, and start batch).

        This is the recommended way to submit batch jobs - it handles file creation,
        upload, batch creation, and optionally waiting for results.

        Args:
            requests: List of request configurations. Each dict should have:
                - custom_id: Unique identifier
                - instructions: System instructions
                - input_texts: List of input texts
                - model: Model to use (optional, uses default)
                - image_url: Image URL (optional)
                - image_path: Local image path (optional)
            endpoint: API endpoint ("/v1/responses" or "/v1/chat/completions")
            metadata: Optional metadata for the batch
            wait: If True, wait for completion and return results
            poll_interval: Seconds between status checks when waiting
            callback: Optional callback for status updates when waiting

        Returns:
            Tuple of (batch_id, results). Results is None if wait=False.

        Example:
            >>> requests = [
            ...     {"custom_id": "img-1", "instructions": "Describe", "input_texts": ["What is this?"], "image_url": "..."},
            ...     {"custom_id": "img-2", "instructions": "Describe", "input_texts": ["What is this?"], "image_url": "..."},
            ... ]
            >>> batch_id, results = llm.submit_batch(requests, wait=True)
            >>> for r in results:
            ...     print(f"{r['custom_id']}: {r['response']['body']['output_text']}")
        """
        if not hasattr(self.provider, "submit_batch"):
            raise NotImplementedError(f"Batch processing not supported by {self.provider_name} provider")
        return self.provider.submit_batch(requests, endpoint, metadata, wait, poll_interval, callback)
