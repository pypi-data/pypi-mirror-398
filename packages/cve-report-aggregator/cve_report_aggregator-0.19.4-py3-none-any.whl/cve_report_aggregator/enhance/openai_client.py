"""OpenAI Batch API client for CVE enrichment with security context analysis."""

import json
import tempfile
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from ..core.constants import BATCH_TIMEOUT_HOURS
from ..core.logging import get_logger
from .models import SimpleCVEEnrichment

logger = get_logger(__name__)


class OpenAIEnricher:
    """OpenAI Batch API-based CVE enrichment engine.

    Uses OpenAI Batch API to analyze CVEs asynchronously in the context of UDS Core
    security controls (NetworkPolicies and Pepr admission policies) to generate
    mitigation strategies.

    The Batch API provides 50% cost savings compared to synchronous API calls.

    Attributes:
        client: OpenAI client instance
        model: OpenAI model to use (e.g., "gpt-5-nano", "gpt-5-mini")
        temperature: Fixed at 1.0 (required by gpt-5 models)
        baseline_context: Baseline security context from UDS Core
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5-nano",
        reasoning_effort: str = "medium",
        verbosity: str = "medium",
        max_completion_tokens: int | None = None,
        seed: int | None = None,
        metadata: dict[str, str] | None = None,
        baseline_context_path: Path | None = None,
        poll_interval: int = 10,
    ):
        """Initialize OpenAI Batch API enricher.

        Args:
            api_key: OpenAI API key
            model: OpenAI model to use (default: gpt-5-nano)
            reasoning_effort: Reasoning effort level (minimal, low, medium, high) (default: medium)
            verbosity: Verbosity level for model responses (low, medium, high) (default: medium)
            max_completion_tokens: Optional upper bound for total tokens including reasoning tokens
            seed: Optional seed for reproducible results
            metadata: Optional metadata tags for OpenAI requests
            baseline_context_path: Path to baseline security context markdown file
                                   If None, uses default from package
            poll_interval: Batch API polling interval in seconds (default: 10)

        Note:
            Temperature is fixed at 1.0 as required by gpt-5 models.
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = 1.0
        self.reasoning_effort = reasoning_effort
        self.verbosity = verbosity
        self.max_completion_tokens = max_completion_tokens
        self.seed = seed
        self.metadata = metadata
        self.poll_interval = poll_interval

        # Validate model is available
        self._validate_model()

        self.baseline_context = self._load_baseline_context(baseline_context_path)
        self.system_prompt = self._build_system_prompt()
        logger.info(
            "OpenAI Batch API enricher initialized",
            model=model,
            temperature=self.temperature,
            reasoning_effort=self.reasoning_effort,
            verbosity=self.verbosity,
            max_completion_tokens=self.max_completion_tokens,
            seed=self.seed,
        )

    def _load_baseline_context(self, path: Path | None = None) -> str:
        """Load baseline security context from markdown file.

        Args:
            path: Optional custom path to baseline context file

        Returns:
            Baseline security context as string

        Raises:
            FileNotFoundError: If baseline context file not found
        """
        if path is None:
            # Use default baseline context from package
            path = Path(__file__).parent / "baseline_security_context.md"

        if not path.exists():
            raise FileNotFoundError(f"Baseline context file not found: {path}")

        logger.debug("Loading baseline security context", path=str(path))
        return path.read_text()

    def _validate_model(self) -> None:
        """Validate that the configured model is available via OpenAI API.

        Raises:
            ValueError: If model is not available or API call fails
        """
        try:
            logger.debug("Validating model availability", model=self.model)

            # List all available models from OpenAI
            models = self.client.models.list()

            # Extract model IDs
            available_model_ids = [model.id for model in models.data]

            # Check if configured model is in the list
            if self.model not in available_model_ids:
                logger.error(
                    "Model not available",
                    requested_model=self.model,
                    available_models=available_model_ids[:10],  # Show first 10 for brevity
                )
                raise ValueError(
                    f"Model '{self.model}' is not available. "
                    f"Available models include: {', '.join(available_model_ids[:10])}"
                )

            logger.debug("Model validation successful", model=self.model)

        except Exception as e:
            if isinstance(e, ValueError):
                raise
            logger.error("Failed to validate model", error=str(e), model=self.model)
            raise ValueError(f"Failed to validate model '{self.model}': {str(e)}") from e

    def _build_system_prompt(self) -> str:
        """Build system prompt with baseline security context.

        Returns:
            System prompt for OpenAI
        """
        return f"""You are a cybersecurity expert analyzing Common Vulnerabilities and Exposures (CVEs) \
in the context of a Kubernetes cluster running UDS Core.

UDS Core provides defense-in-depth security through:
- NetworkPolicies enforcing zero-trust networking
- Pepr admission policies preventing insecure configurations
- Istio service mesh providing mTLS and traffic control

Your task is to provide:
1. A 2 sentence explanation of how UDS Core helps mitigate the CVE
2. A 1 sentence impact analysis of what could happen WITHOUT UDS Core controls

Mitigation Format: "UDS helps to mitigate {{CVE_ID}} by {{explanation}}"

The mitigation explanation should:
- Be exactly ONE sentence
- Identify the most relevant security control(s)
- Focus on the primary mitigation mechanism

The impact analysis should:
- Be 1 sentences describing potential consequences without UDS Core
- Cover attack scenarios, data risks, and potential blast radius
- Be specific to this CVE's attack vector and severity

Baseline Security Context:
{self.baseline_context}

Respond ONLY with valid JSON matching the SimpleCVEEnrichment schema. Do not include markdown \
formatting, code blocks, or any text outside the JSON object."""

    def _build_user_prompt(self, cve_id: str, cve_data: dict[str, Any]) -> str:
        """Build user prompt for CVE analysis.

        Args:
            cve_id: CVE identifier (e.g., CVE-2025-8869)
            cve_data: Vulnerability data from unified report

        Returns:
            User prompt for OpenAI
        """
        severity = cve_data.get("severity", "UNKNOWN")
        description = cve_data.get("description", "No description available")

        # Extract CVSS 3.x scores if available (optimized with list comprehension)
        cvss_scores = []
        if "cvss" in cve_data:
            cvss_data = cve_data["cvss"]
            if isinstance(cvss_data, list):
                cvss_scores = [
                    f"CVSS 3.x Base Score: {entry.get('metrics', {}).get('baseScore')}"
                    for entry in cvss_data
                    if entry.get("version", "").startswith("3") and entry.get("metrics", {}).get("baseScore")
                ]
        cvss_info = "\n" + "\n".join(cvss_scores) if cvss_scores else ""

        # Extract fix information if available
        fix_info = ""
        if "fix" in cve_data and "versions" in cve_data["fix"]:
            versions = cve_data["fix"]["versions"]
            if versions:
                fix_info = f"\nFixed in versions: {', '.join(versions)}"

        timestamp = datetime.now(UTC).isoformat()

        prompt = f"""Analyze the following CVE in the context of UDS Core security controls:

CVE ID: {cve_id}
Severity: {severity}{cvss_info}
Description: {description}{fix_info}

Provide your analysis in JSON format with TWO key fields:

{{
  "cve_id": "{cve_id}",
  "mitigation_summary": "UDS helps to mitigate {cve_id} by [your single-sentence explanation here]",
  "impact_analysis": "[1 sentence explanation of potential impact without UDS Core controls]",
  "analysis_model": "{self.model}",
  "analysis_timestamp": "{timestamp}"
}}

Requirements for the mitigation_summary:
- MUST be exactly ONE sentence
- MUST start with "UDS helps to mitigate {cve_id} by"
- MUST identify the most relevant UDS Core security control(s)
- MUST be concise and specific
- Focus on NetworkPolicies, Pepr policies, or Istio service mesh controls

Requirements for the impact_analysis:
- MUST be 2 sentences in length
- Describe what could happen WITHOUT UDS Core controls in place
- Cover attack scenarios (e.g., remote code execution, privilege escalation)
- Describe potential data risks (e.g., exfiltration, tampering)
- Mention blast radius (e.g., lateral movement, cluster-wide compromise)
- Be specific to this CVE's severity and attack vector

Example:
{{
  "cve_id": "CVE-2024-12345",
  "mitigation_summary": "UDS helps to mitigate CVE-2024-12345 by enforcing non-root container execution \
through Pepr admission policies and blocking unauthorized external network access via default-deny NetworkPolicies.",
  "impact_analysis": "Without UDS Core controls, this critical vulnerability could allow an attacker to \
achieve remote code execution on the vulnerable container with root privileges. This could enable lateral \
movement across the cluster, exfiltration of sensitive data from connected services, and deployment of \
malicious workloads. The blast radius would extend beyond the compromised pod to potentially affect the entire \
cluster and connected infrastructure.",
  "analysis_model": "{self.model}",
  "analysis_timestamp": "{timestamp}"
}}
"""

        return prompt

    def _create_batch_request(self, cve_id: str, cve_data: dict[str, Any], custom_id: str) -> dict[str, Any]:
        """Create a single batch request for a CVE.

        Args:
            cve_id: CVE identifier (e.g., CVE-2025-8869)
            cve_data: Vulnerability data from unified report
            custom_id: Custom identifier for this request

        Returns:
            Batch request dictionary in JSONL format
        """
        # Build request body with required parameters
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self._build_user_prompt(cve_id, cve_data)},
            ],
            "temperature": self.temperature,
            "reasoning_effort": self.reasoning_effort,
            "verbosity": self.verbosity,
            "response_format": {"type": "json_object"},
        }

        # Add optional parameters if provided
        if self.max_completion_tokens is not None:
            body["max_completion_tokens"] = self.max_completion_tokens
        if self.seed is not None:
            body["seed"] = self.seed

        # Metadata requires store to be enabled
        if self.metadata is not None:
            body["metadata"] = self.metadata
            body["store"] = True  # Required for metadata parameter

        return {
            "custom_id": custom_id,
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": body,
        }

    def _filter_vulnerabilities(
        self,
        vulnerabilities: list[dict[str, Any]],
        max_cves: int | None,
        severity_filter: list[str],
    ) -> tuple[list[tuple[str, dict[str, Any]]], int]:
        """Filter vulnerabilities by severity and max count.

        Args:
            vulnerabilities: List of vulnerability dictionaries
            max_cves: Maximum number of CVEs to collect (None = all)
            severity_filter: List of severity levels to include

        Returns:
            Tuple of (filtered CVEs list, count skipped by severity)
        """
        cves_to_enrich: list[tuple[str, dict[str, Any]]] = []
        skipped_by_severity = 0

        for vuln in vulnerabilities:
            if max_cves and len(cves_to_enrich) >= max_cves:
                logger.info("Reached max CVE limit", max_cves=max_cves, collected=len(cves_to_enrich))
                break

            cve_id = vuln.get("vulnerability_id")
            if not cve_id:
                logger.warning("Skipping vulnerability without ID", vuln=vuln.get("count"))
                continue

            cve_data = vuln.get("vulnerability", {})
            severity = cve_data.get("severity", "Unknown")

            if severity_filter and severity not in severity_filter:
                logger.debug(
                    "Skipping CVE due to severity filter",
                    cve_id=cve_id,
                    severity=severity,
                    allowed_severities=severity_filter,
                )
                skipped_by_severity += 1
                continue

            cves_to_enrich.append((cve_id, cve_data))

        return cves_to_enrich, skipped_by_severity

    def _create_batch_file(
        self,
        cves_to_enrich: list[tuple[str, dict[str, Any]]],
    ) -> Path:
        """Create JSONL batch request file.

        Args:
            cves_to_enrich: List of (cve_id, cve_data) tuples

        Returns:
            Path to created batch file
        """
        batch_requests = []
        for idx, (cve_id, cve_data) in enumerate(cves_to_enrich):
            custom_id = f"cve-{idx}-{cve_id}"
            batch_requests.append(self._create_batch_request(cve_id, cve_data, custom_id))

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            batch_file_path = Path(f.name)
            for request in batch_requests:
                f.write(json.dumps(request) + "\n")

        logger.info("Created batch request file", path=str(batch_file_path), requests=len(batch_requests))

        if batch_requests:
            logger.debug("Sample batch request", request=batch_requests[0])

        return batch_file_path

    def _upload_and_create_batch(self, batch_file_path: Path) -> tuple[Any, Any]:
        """Upload batch file and create batch job.

        Args:
            batch_file_path: Path to JSONL batch file

        Returns:
            Tuple of (batch_input_file, batch)
        """
        logger.info("Uploading batch file to OpenAI")
        with open(batch_file_path, "rb") as f:
            batch_input_file = self.client.files.create(file=f, purpose="batch")

        logger.info("Batch file uploaded", file_id=batch_input_file.id)

        logger.info("Creating batch job")
        batch = self.client.batches.create(
            input_file_id=batch_input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={"description": "CVE enrichment batch"},
        )

        logger.info(
            "Batch job created",
            batch_id=batch.id,
            status=batch.status,
            request_counts=batch.request_counts,
        )

        return batch_input_file, batch

    def _poll_for_completion(self, batch: Any) -> Any:
        """Poll batch until completion or timeout.

        Args:
            batch: OpenAI batch object

        Returns:
            Updated batch object

        Raises:
            EnrichmentError: If batch times out
        """
        timeout = timedelta(hours=BATCH_TIMEOUT_HOURS)
        start_time = datetime.now()

        logger.info(
            "Waiting for batch completion",
            poll_interval_seconds=self.poll_interval,
            timeout_hours=BATCH_TIMEOUT_HOURS,
        )

        while batch.status in ["validating", "in_progress", "finalizing"]:
            elapsed = datetime.now() - start_time
            if elapsed > timeout:
                from ..core.exceptions import EnrichmentError

                raise EnrichmentError(
                    f"Batch processing timed out after {elapsed}. "
                    f"Batch ID: {batch.id}, Status: {batch.status}, "
                    f"Request counts: {batch.request_counts}"
                )

            time.sleep(self.poll_interval)
            batch = self.client.batches.retrieve(batch.id)
            logger.info(
                "Batch status update",
                batch_id=batch.id,
                status=batch.status,
                request_counts=batch.request_counts,
                elapsed_minutes=int(elapsed.total_seconds() / 60),
            )

        return batch

    def _log_batch_errors(self, batch: Any) -> None:
        """Download and log errors from batch error file.

        Args:
            batch: OpenAI batch object with error_file_id
        """
        if not batch.error_file_id:
            return

        logger.info("Downloading error file for details", error_file_id=batch.error_file_id)
        try:
            error_content = self.client.files.content(batch.error_file_id)
            error_data = error_content.read().decode("utf-8")

            error_lines = error_data.strip().split("\n")[:3]
            for line in error_lines:
                error_result = json.loads(line)
                logger.error(
                    "Batch request error",
                    custom_id=error_result.get("custom_id"),
                    error=error_result.get("error"),
                )
        except Exception as e:
            logger.error("Failed to download error file", error=str(e))

    def _parse_batch_results(self, batch: Any) -> dict[str, SimpleCVEEnrichment]:
        """Download and parse batch output results.

        Args:
            batch: Completed OpenAI batch object

        Returns:
            Dictionary mapping CVE IDs to enrichments
        """
        if not batch.output_file_id:
            logger.error("No output file ID in completed batch - all requests may have failed")
            self._log_batch_errors(batch)
            return {}

        logger.info("Batch completed, downloading results", output_file_id=batch.output_file_id)
        output_content = self.client.files.content(batch.output_file_id)
        output_data = output_content.read().decode("utf-8")

        enrichments: dict[str, SimpleCVEEnrichment] = {}
        for line in output_data.strip().split("\n"):
            result = json.loads(line)
            custom_id = result["custom_id"]

            if result.get("error"):
                logger.error("Request failed", custom_id=custom_id, error=result["error"])
                continue

            response = result["response"]
            content = response["body"]["choices"][0]["message"]["content"]

            try:
                enrichment_data = json.loads(content)
                enrichment = SimpleCVEEnrichment(**enrichment_data)
                enrichments[enrichment.cve_id] = enrichment
                logger.debug("CVE enrichment successful", cve_id=enrichment.cve_id)
            except (json.JSONDecodeError, ValidationError) as e:
                logger.error(
                    "Failed to parse enrichment response",
                    custom_id=custom_id,
                    error=str(e),
                    content=content[:200],
                )

        return enrichments

    def _cleanup_resources(
        self,
        batch_file_path: Path | None,
        batch_input_file: Any | None,
        batch: Any | None,
    ) -> None:
        """Clean up local and remote resources.

        Args:
            batch_file_path: Path to local batch file
            batch_input_file: OpenAI file object for input
            batch: OpenAI batch object
        """
        # Cleanup local temporary file
        if batch_file_path and batch_file_path.exists():
            batch_file_path.unlink()
            logger.debug("Cleaned up temporary batch file", path=str(batch_file_path))

        # Cleanup OpenAI remote files
        try:
            if batch_input_file is not None:
                self.client.files.delete(batch_input_file.id)
                logger.debug("Deleted input file from OpenAI", file_id=batch_input_file.id)

            if batch is not None and batch.status == "completed":
                if batch.output_file_id:
                    self.client.files.delete(batch.output_file_id)
                    logger.debug("Deleted output file from OpenAI", file_id=batch.output_file_id)

                if batch.error_file_id:
                    self.client.files.delete(batch.error_file_id)
                    logger.debug("Deleted error file from OpenAI", file_id=batch.error_file_id)
        except Exception as e:
            logger.warning(
                "Failed to cleanup OpenAI remote files",
                error=str(e),
                batch_id=batch.id if batch is not None else None,
            )

    def enrich_report(
        self,
        vulnerabilities: list[dict[str, Any]],
        max_cves: int | None = None,
        severity_filter: list[str] | None = None,
    ) -> dict[str, SimpleCVEEnrichment]:
        """Enrich multiple CVEs from a vulnerability report using OpenAI Batch API.

        This method coordinates the batch enrichment workflow:
        1. Filters vulnerabilities by severity
        2. Creates batch request file
        3. Uploads and creates batch job
        4. Polls for completion
        5. Parses results
        6. Cleans up resources

        Args:
            vulnerabilities: List of vulnerability dictionaries
            max_cves: Maximum number of CVEs to enrich (None = all)
            severity_filter: List of severity levels to enrich (e.g., ["Critical", "High"])
                           If None, enriches all severities. Default: ["Critical", "High"]

        Returns:
            Dictionary mapping CVE IDs to SimpleCVEEnrichment objects
        """
        if severity_filter is None:
            severity_filter = ["Critical", "High"]

        # Step 1: Filter vulnerabilities
        cves_to_enrich, skipped_by_severity = self._filter_vulnerabilities(vulnerabilities, max_cves, severity_filter)

        if not cves_to_enrich:
            logger.info("No CVEs to enrich after filtering")
            return {}

        logger.info(
            "Starting Batch API CVE enrichment",
            total_vulnerabilities=len(vulnerabilities),
            cves_to_enrich=len(cves_to_enrich),
            skipped_by_severity=skipped_by_severity,
            severity_filter=severity_filter,
        )

        batch_file_path: Path | None = None
        batch_input_file = None
        batch = None

        try:
            # Step 2: Create batch file
            batch_file_path = self._create_batch_file(cves_to_enrich)

            # Step 3: Upload and create batch
            batch_input_file, batch = self._upload_and_create_batch(batch_file_path)

            # Step 4: Poll for completion
            batch = self._poll_for_completion(batch)

            # Handle non-completed statuses
            if batch.status in ["failed", "expired", "cancelled"]:
                logger.error(f"Batch job {batch.status}", batch_id=batch.id, errors=getattr(batch, "errors", None))
                return {}

            # Step 5: Parse results
            enrichments = self._parse_batch_results(batch)

            logger.info(
                "CVE enrichment complete",
                total_vulnerabilities=len(vulnerabilities),
                cves_to_enrich=len(cves_to_enrich),
                successful_enrichments=len(enrichments),
                skipped_by_severity=skipped_by_severity,
                severity_filter=severity_filter,
            )

            return enrichments

        finally:
            # Step 6: Cleanup resources
            self._cleanup_resources(batch_file_path, batch_input_file, batch)
