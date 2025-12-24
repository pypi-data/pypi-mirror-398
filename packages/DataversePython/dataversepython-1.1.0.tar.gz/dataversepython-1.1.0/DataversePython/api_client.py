import time
import logging
from typing import Optional, Dict, Any, List
import requests
import uuid
import re
import json
from dataclasses import dataclass

@dataclass
class BatchOperation:
    """Represents a single operation in a batch request."""
    method: str  # POST, PATCH, DELETE
    path: str  # Relative path, e.g., "api/data/v9.2/accounts"
    json_body: Optional[Dict[str, Any]] = None
    content_id: int = 0
    headers: Optional[Dict[str, str]] = None


@dataclass
class BatchOperationResult:
    """Represents the result of a single operation in a batch response."""
    content_id: int
    status_code: int
    headers: Dict[str, str]
    body: Optional[str] = None
    error: Optional[Dict[str, Any]] = None


class ApiClient:
    """
    Lightweight HTTP client for Microsoft Dataverse Web API.
    Centralizes request building, retries, timeouts, pagination, and logging.
    """

    def __init__(
        self,
        session: requests.Session,
        base_uri: str,
        logger: logging.Logger,
        timeout: int = 120,
        retries: int = 3,
        backoff: float = 0.5,
    ) -> None:
        self.session = session
        self.base_uri = base_uri
        self.logger = logger
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff

    def set_timeout(self, timeout: int) -> None:
        """Set request timeout in seconds. Useful for batch operations."""
        self.timeout = timeout

    def _full_url(self, path: str, params: Optional[Dict[str, Any]] = None) -> str:
        url = f"{self.base_uri}{path}"
        if params:
            # Preserve OData parameter keys like $top, $select, $filter without URL-encoding
            components: List[str] = []
            for k, v in params.items():
                if v is None:
                    continue
                components.append(f"{k}={v}")
            if components:
                url += "?" + "&".join(components)
        return url

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json: Any = None,
        data: Any = None,
    ) -> requests.Response:
        url = self._full_url(path, params)
        attempt = 0
        start = time.perf_counter()
        while True:
            attempt += 1
            try:
                # Prefer raw body `data` when provided (e.g., multipart $batch); else JSON payload
                request_kwargs = {"headers": headers, "timeout": self.timeout}
                if data is not None:
                    request_kwargs["data"] = data
                else:
                    request_kwargs["json"] = json

                resp = self.session.request(
                    method=method.upper(),
                    url=url,
                    **request_kwargs
                )
            except requests.RequestException as ex:
                duration = int((time.perf_counter() - start) * 1000)
                self.logger.error(
                    f"HTTP error method={method} url={url} attempt={attempt} duration_ms={duration} error={ex}"
                )
                if attempt >= self.retries:
                    raise
                time.sleep(self.backoff * attempt)
                continue

            status = resp.status_code
            duration = int((time.perf_counter() - start) * 1000)
            req_id = resp.headers.get("x-ms-request-id") or resp.headers.get("request-id")
            self.logger.debug(
                f"HTTP {method.upper()} status={status} url={url} attempt={attempt} duration_ms={duration} request_id={req_id}"
            )

            if status in (429, 500, 502, 503, 504) and attempt < self.retries:
                retry_after = resp.headers.get("Retry-After")
                sleep_s = float(retry_after) if retry_after else self.backoff * attempt
                time.sleep(sleep_s)
                continue

            return resp

    def get_paginated(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        resp = self.request("GET", path, params=params, headers=headers)
        if resp.status_code != 200:
            content = resp.content.decode("utf-8", errors="ignore")
            self.logger.error(
                f"GET failed status={resp.status_code} url={resp.url} response={content}"
            )
            raise Exception(
                f"Request failed with status code {resp.status_code}. Response: {content}"
            )
        data = resp.json()
        rows.extend(data.get("value", []))
        next_link = data.get("@odata.nextLink")
        # Continue pagination using absolute nextLink; preserve headers
        while next_link:
            resp = self.session.get(next_link, headers=headers, timeout=self.timeout)
            if resp.status_code != 200:
                content = resp.content.decode("utf-8", errors="ignore")
                self.logger.error(
                    f"GET page failed status={resp.status_code} url={next_link} response={content}"
                )
                raise Exception(
                    f"Request failed with status code {resp.status_code}. Response: {content}"
                )
            data = resp.json()
            rows.extend(data.get("value", []))
            next_link = data.get("@odata.nextLink")
        return rows

    def post_json(
        self, path: str, json_payload: Any, headers: Optional[Dict[str, str]] = None
    ) -> requests.Response:
        return self.request("POST", path, headers=headers, json=json_payload)

    def patch_json(
        self, path: str, json_payload: Any, headers: Optional[Dict[str, str]] = None
    ) -> requests.Response:
        return self.request("PATCH", path, headers=headers, json=json_payload)

    def delete(
        self, path: str, headers: Optional[Dict[str, str]] = None
    ) -> requests.Response:
        """Convenience DELETE wrapper."""
        return self.request("DELETE", path, headers=headers)

    def _generate_batch_boundary(self) -> str:
        """Generate a unique batch boundary identifier."""
        return f"batch_{uuid.uuid4().hex}"

    def _generate_changeset_boundary(self) -> str:
        """Generate a unique changeset boundary identifier."""
        return f"changeset_{uuid.uuid4().hex}"

    def _build_batch_body(
        self,
        operations: List[BatchOperation],
        use_changeset: bool = False,
    ) -> tuple[str, str]:
        """
        Build a multipart/mixed batch request body.
        
        Args:
            operations: List of BatchOperation objects.
            use_changeset: If True, wrap all operations in a single changeset for atomicity.
        
        Returns:
            Tuple of (batch_body: str, content_type_header: str)
        """
        batch_boundary = self._generate_batch_boundary()
        lines: List[str] = []

        if use_changeset:
            # All operations in a single changeset (atomic transaction)
            changeset_boundary = self._generate_changeset_boundary()
            lines.append(f"--{batch_boundary}")
            lines.append(f'Content-Type: multipart/mixed; boundary="{changeset_boundary}"')
            lines.append("")

            for op in operations:
                lines.append(f"--{changeset_boundary}")
                lines.append("Content-Type: application/http")
                lines.append("Content-Transfer-Encoding: binary")
                lines.append(f"Content-ID: {op.content_id}")
                lines.append("")
                lines.append(f"{op.method} {op.path} HTTP/1.1")
                # Include custom headers if provided (e.g., If-Match for DELETE)
                if op.headers:
                    for hk, hv in op.headers.items():
                        lines.append(f"{hk}: {hv}")
                # Only include Content-Type header for requests with a body (POST, PATCH)
                if op.method in ("POST", "PATCH") and op.json_body:
                    lines.append("Content-Type: application/json")
                    lines.append("")
                    lines.append(json.dumps(op.json_body))
                elif op.method in ("POST", "PATCH"):
                    lines.append("Content-Type: application/json")
                    lines.append("")
                lines.append("")

            lines.append(f"--{changeset_boundary}--")
            lines.append("")
            lines.append(f"--{batch_boundary}--")
        else:
            # Individual operations (no atomic grouping)
            for op in operations:
                lines.append(f"--{batch_boundary}")
                lines.append("Content-Type: application/http")
                lines.append("Content-Transfer-Encoding: binary")
                lines.append(f"Content-ID: {op.content_id}")
                lines.append("")
                lines.append(f"{op.method} {op.path} HTTP/1.1")
                # Include custom headers if provided (e.g., If-Match for DELETE)
                if op.headers:
                    for hk, hv in op.headers.items():
                        lines.append(f"{hk}: {hv}")
                # Only include Content-Type header for requests with a body (POST, PATCH)
                if op.method in ("POST", "PATCH") and op.json_body:
                    lines.append("Content-Type: application/json")
                    lines.append("")
                    lines.append(json.dumps(op.json_body))
                elif op.method in ("POST", "PATCH"):
                    lines.append("Content-Type: application/json")
                    lines.append("")
                lines.append("")

            lines.append(f"--{batch_boundary}--")

        # Join with CRLF (required by Dataverse)
        batch_body = "\r\n".join(lines)
        content_type = f'multipart/mixed; boundary="{batch_boundary}"'

        return batch_body, content_type

    def _parse_batch_response(
        self, response_body: str
    ) -> List[BatchOperationResult]:
        """
        Parse a multipart batch response body into individual operation results.
        
        Args:
            response_body: Raw response body from $batch request.
        
        Returns:
            List of BatchOperationResult objects.
        """
        results: List[BatchOperationResult] = []

        # Find the top-level batch response boundary line, e.g. '--batchresponse_<guid>'
        boundary_line_match = re.search(r"--batchresponse_[^\r\n]+", response_body)
        if not boundary_line_match:
            self.logger.warning("Could not find batch boundary in response")
            return results

        batch_boundary = boundary_line_match.group(0)[2:]  # remove leading '--'

        # Helper to parse a single HTTP response part into a BatchOperationResult
        def parse_single_response(part_text: str) -> List[BatchOperationResult]:
            res_list: List[BatchOperationResult] = []
            lines = part_text.split("\r\n")

            # There may be multiple HTTP responses in a part; collect each block starting with 'HTTP/1.1'
            i = 0
            current_content_id: Optional[int] = None
            while i < len(lines):
                line = lines[i]
                # Capture Content-ID before the HTTP status line
                if line.startswith("Content-ID: "):
                    try:
                        current_content_id = int(line.split(": ", 1)[1].strip())
                    except ValueError:
                        current_content_id = None
                    i += 1
                    continue

                if line.startswith("HTTP/1.1 "):
                    # Parse status code
                    parts_http = line.split(" ", 2)
                    status_code = None
                    try:
                        status_code = int(parts_http[1])
                    except (IndexError, ValueError):
                        status_code = None

                    headers: Dict[str, str] = {}
                    body_lines: List[str] = []

                    # Scan subsequent lines: headers until blank line, then body until next boundary or end
                    i += 1
                    # Headers
                    while i < len(lines) and lines[i].strip() != "":
                        hline = lines[i]
                        if hline.startswith("OData-EntityId: "):
                            headers["OData-EntityId"] = hline.split(": ", 1)[1].strip()
                        elif hline.startswith("Location: "):
                            headers["Location"] = hline.split(": ", 1)[1].strip()
                        elif hline.startswith("Content-Type: "):
                            headers["Content-Type"] = hline.split(": ", 1)[1].strip()
                        i += 1

                    # Skip blank line between headers and body
                    if i < len(lines) and lines[i].strip() == "":
                        i += 1

                    # Body lines until next boundary marker or end
                    while i < len(lines):
                        # Stop if we hit another part boundary or an inner changeset boundary marker
                        if lines[i].startswith("--batchresponse_") or lines[i].startswith("--changesetresponse_"):
                            break
                        body_lines.append(lines[i])
                        i += 1

                    body = "\r\n".join(body_lines).strip() if body_lines else None
                    error = None
                    if body and status_code not in (200, 204):
                        try:
                            body_json = json.loads(body)
                            if isinstance(body_json, dict) and "error" in body_json:
                                error = body_json["error"]
                        except (json.JSONDecodeError, ValueError):
                            pass

                    if status_code is not None:
                        res_list.append(
                            BatchOperationResult(
                                content_id=current_content_id or 0,
                                status_code=status_code,
                                headers=headers,
                                body=body,
                                error=error,
                            )
                        )
                    # Continue scanning lines from where we stopped
                    continue

                i += 1

            return res_list

        # Split the whole response into top-level parts using the batch boundary
        parts = response_body.split(f"--{batch_boundary}")
        for part in parts:
            if not part or not part.strip():
                continue

            # If this part contains a changeset response, split further using the changeset boundary
            changeset_header_match = re.search(r'boundary\s*=\s*"?changesetresponse_[^"\r\n]+"?', part)
            if changeset_header_match:
                # Extract changeset boundary name, e.g. changesetresponse_<guid>
                boundary_value = changeset_header_match.group(0)
                # Get the value after '=' and strip quotes
                cs_boundary = boundary_value.split('=', 1)[1].strip().strip('"')
                cs_parts = part.split(f"--{cs_boundary}")
                for cs_part in cs_parts:
                    if not cs_part.strip():
                        continue
                    results.extend(parse_single_response(cs_part))
            else:
                # No changeset: parse directly
                results.extend(parse_single_response(part))

        return results

    def post_batch(
        self,
        operations: List[BatchOperation],
        use_changeset: bool = False,
        continue_on_error: bool = True,
    ) -> tuple[requests.Response, List[BatchOperationResult]]:
        """
        Send a batch request containing multiple operations.
        
        Args:
            operations: List of BatchOperation objects to include in the batch.
            use_changeset: If True, wrap operations in a changeset for atomic transaction.
            continue_on_error: If True, include Prefer: odata.continue-on-error header.
        
        Returns:
            Tuple of (response object, list of BatchOperationResult).
        """
        batch_body, content_type = self._build_batch_body(operations, use_changeset)

        headers: Dict[str, str] = {
            "Content-Type": content_type,
            "Accept": "application/json",
        }
        if continue_on_error:
            headers["Prefer"] = "odata.continue-on-error"

        self.logger.info(
            f"Batch request operations={len(operations)} use_changeset={use_changeset} continue_on_error={continue_on_error}"
        )

        resp = self.request(
            "POST",
            "api/data/v9.2/$batch",
            headers=headers,
            data=batch_body,
        )

        # Parse response
        results: List[BatchOperationResult] = []
        if resp.status_code in (200, 201):
            results = self._parse_batch_response(resp.text)
            self.logger.info(
                f"Batch response status={resp.status_code} parsed_operations={len(results)}"
            )
        else:
            self.logger.error(
                f"Batch request failed status={resp.status_code} response={resp.text[:500]}"
            )

        return resp, results
