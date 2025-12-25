"""Data models for CVE enrichment with security context analysis."""

from enum import Enum

from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    """Severity levels for security policies and mitigations."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class NetworkPolicyAnalysis(BaseModel):
    """Analysis of how NetworkPolicies mitigate a CVE.

    Attributes:
        blocks_attack_path: Whether network policies completely block the attack path
        relevant_policies: List of NetworkPolicy names that provide protection
        protection_summary: Summary of network-level protections
        limitations: Any limitations or gaps in network policy protection
        effectiveness: Overall effectiveness rating (HIGH/MEDIUM/LOW)
    """

    blocks_attack_path: bool = Field(description="Whether NetworkPolicies completely block the attack vector")
    relevant_policies: list[str] = Field(
        default_factory=list, description="Names of relevant NetworkPolicies providing protection"
    )
    protection_summary: str = Field(description="Summary of network-level protections")
    limitations: str | None = Field(default=None, description="Limitations or gaps in network policy coverage")
    effectiveness: SeverityLevel = Field(description="Effectiveness rating of network policy protection")


class PeprPolicyAnalysis(BaseModel):
    """Analysis of how Pepr admission policies mitigate a CVE.

    Attributes:
        prevents_exploitation: Whether Pepr policies prevent exploitation
        relevant_policies: List of Pepr policy names that provide protection
        protection_summary: Summary of admission control protections
        mutations_applied: List of automatic mutations that help mitigate the vulnerability
        validations_enforced: List of validations that prevent vulnerable configurations
        limitations: Any limitations or gaps in Pepr policy protection
        effectiveness: Overall effectiveness rating (HIGH/MEDIUM/LOW)
    """

    prevents_exploitation: bool = Field(description="Whether Pepr policies prevent exploitation of the vulnerability")
    relevant_policies: list[str] = Field(
        default_factory=list, description="Names of relevant Pepr policies providing protection"
    )
    protection_summary: str = Field(description="Summary of admission control protections")
    mutations_applied: list[str] = Field(
        default_factory=list,
        description="List of automatic mutations that help mitigate the vulnerability",
    )
    validations_enforced: list[str] = Field(
        default_factory=list,
        description="List of validations that prevent vulnerable configurations",
    )
    limitations: str | None = Field(default=None, description="Limitations or gaps in Pepr policy coverage")
    effectiveness: SeverityLevel = Field(description="Effectiveness rating of Pepr policy protection")


class SecurityContextAnalysis(BaseModel):
    """Comprehensive security context analysis for a CVE.

    Attributes:
        attack_vector: Description of how the vulnerability is exploited
        required_permissions: Capabilities/privileges needed for exploitation
        network_requirements: Network access requirements for exploitation
        runtime_context: Container runtime features leveraged by the exploit
        network_policy_analysis: Analysis of NetworkPolicy protections
        pepr_policy_analysis: Analysis of Pepr admission policy protections
        service_mesh_protection: How Istio service mesh provides protection
        residual_risk: Remaining risk after all security controls
        overall_effectiveness: Combined effectiveness of all security controls
    """

    attack_vector: str = Field(description="Description of how the vulnerability is exploited")
    required_permissions: list[str] = Field(
        default_factory=list,
        description="Capabilities, privileges, or permissions required for exploitation",
    )
    network_requirements: str | None = Field(default=None, description="Network access requirements for exploitation")
    runtime_context: str | None = Field(default=None, description="Container runtime features leveraged by the exploit")
    network_policy_analysis: NetworkPolicyAnalysis = Field(description="Analysis of NetworkPolicy protections")
    pepr_policy_analysis: PeprPolicyAnalysis = Field(description="Analysis of Pepr admission policy protections")
    service_mesh_protection: str | None = Field(
        default=None, description="How Istio service mesh provides additional protection"
    )
    residual_risk: str = Field(description="Remaining risk after applying all UDS Core security controls")
    overall_effectiveness: SeverityLevel = Field(description="Combined effectiveness of all security controls")


class MitigationStrategy(BaseModel):
    """Mitigation strategy for a CVE.

    Attributes:
        short_term: Immediate actions to reduce risk
        long_term: Permanent fixes or workarounds
        uds_core_controls: How UDS Core security controls help mitigate the vulnerability
        additional_recommendations: Additional security measures beyond UDS Core
        priority: Priority level for implementing mitigation (HIGH/MEDIUM/LOW)
    """

    short_term: list[str] = Field(default_factory=list, description="Immediate actions to reduce risk")
    long_term: list[str] = Field(default_factory=list, description="Permanent fixes or workarounds")
    uds_core_controls: list[str] = Field(
        default_factory=list,
        description="How UDS Core security controls help mitigate the vulnerability",
    )
    additional_recommendations: list[str] = Field(
        default_factory=list, description="Additional security measures beyond UDS Core"
    )
    priority: SeverityLevel = Field(description="Priority level for implementing mitigation")


class CVEEnrichment(BaseModel):
    """Complete CVE enrichment data from OpenAI analysis.

    Attributes:
        cve_id: CVE identifier
        security_context: Security context analysis
        mitigation_strategy: Recommended mitigation strategies
        analysis_model: OpenAI model used for analysis
        analysis_timestamp: ISO 8601 timestamp of when the analysis was performed
    """

    cve_id: str = Field(description="CVE identifier (e.g., CVE-2024-12345)")
    security_context: SecurityContextAnalysis = Field(description="Comprehensive security context analysis")
    mitigation_strategy: MitigationStrategy = Field(description="Recommended mitigation strategies")
    analysis_model: str = Field(description="OpenAI model used for analysis (e.g., gpt-5-nano)")
    analysis_timestamp: str = Field(description="ISO 8601 timestamp of when the analysis was performed")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "cve_id": "CVE-2024-12345",
                "security_context": {
                    "attack_vector": "Remote code execution via malicious HTTP request",
                    "required_permissions": ["CAP_NET_BIND_SERVICE"],
                    "network_requirements": "External network access to vulnerable service",
                    "runtime_context": "Requires container running as root",
                    "network_policy_analysis": {
                        "blocks_attack_path": True,
                        "relevant_policies": [
                            "deny-default",
                            "allow-ingress-istio-gateway-only",
                        ],
                        "protection_summary": "Default deny blocks external access",
                        "limitations": None,
                        "effectiveness": "high",
                    },
                    "pepr_policy_analysis": {
                        "prevents_exploitation": True,
                        "relevant_policies": ["RequireNonRootUser", "DropAllCapabilities"],
                        "protection_summary": "Non-root execution prevents exploitation",
                        "mutations_applied": ["runAsNonRoot: true", "drop: [ALL]"],
                        "validations_enforced": ["runAsUser > 0"],
                        "limitations": None,
                        "effectiveness": "high",
                    },
                    "service_mesh_protection": "mTLS prevents MITM attacks",
                    "residual_risk": "Minimal - requires multiple security control bypasses",
                    "overall_effectiveness": "high",
                },
                "mitigation_strategy": {
                    "short_term": ["Verify NetworkPolicies are applied"],
                    "long_term": ["Update vulnerable package to patched version"],
                    "uds_core_controls": [
                        "NetworkPolicies block external access",
                        "Pepr policies enforce non-root execution",
                    ],
                    "additional_recommendations": ["Enable runtime security monitoring"],
                    "priority": "medium",
                },
                "analysis_model": "gpt-4",
                "analysis_timestamp": "2025-10-20T15:30:00Z",
            }
        }


class SimpleCVEEnrichment(BaseModel):
    """Simplified CVE enrichment with single-sentence mitigation explanation.

    This model provides a concise, single-sentence explanation of how UDS Core
    security controls help mitigate a specific CVE, plus an impact analysis.

    Attributes:
        cve_id: CVE identifier
        mitigation_summary: Single-sentence explanation in format:
                           "UDS helps to mitigate {CVE_ID} by {explanation}"
        impact_analysis: 2-3 sentence explanation of the potential impact this CVE could have
                        on the deployed system if UDS Core controls were not in place
        analysis_model: OpenAI model used for analysis
        analysis_timestamp: ISO 8601 timestamp of when the analysis was performed
    """

    cve_id: str = Field(description="CVE identifier (e.g., CVE-2024-12345)")
    mitigation_summary: str = Field(
        description='Single-sentence mitigation explanation starting with "UDS helps to mitigate {CVE_ID} by"'
    )
    impact_analysis: str = Field(
        description="2-3 sentence explanation of the potential impact on the deployed system without UDS Core controls"
    )
    analysis_model: str = Field(description="OpenAI model used for analysis (e.g., gpt-5-nano)")
    analysis_timestamp: str = Field(description="ISO 8601 timestamp of when the analysis was performed")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "cve_id": "CVE-2024-12345",
                "mitigation_summary": "UDS helps to mitigate CVE-2024-12345 by enforcing non-root "
                "container execution through Pepr policies and blocking external network "
                "access via default-deny NetworkPolicies, preventing remote code execution.",
                "impact_analysis": "Without UDS Core controls, this CVE could allow an attacker to achieve "
                "remote code execution on the vulnerable container with root privileges. This could lead to "
                "lateral movement across the cluster, data exfiltration, and compromise of other services.",
                "analysis_model": "gpt-5-nano",
                "analysis_timestamp": "2025-10-20T15:30:00Z",
            }
        }
