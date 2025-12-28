"""Pytest configuration and fixtures for CVE Report Aggregator tests."""

import json

import pytest


@pytest.fixture
def sample_grype_report():
    """Sample Grype report for testing."""
    return {
        "_source_file": "test-report.json",
        "_scanner": "grype",
        "source": {"target": {"userInput": "nginx:1.21"}},
        "descriptor": {
            "version": "0.100.0",
            "db": {
                "built": "2024-01-01T00:00:00Z",
                "schemaVersion": 5,
            },
        },
        "matches": [
            {
                "vulnerability": {
                    "id": "CVE-2024-12345",
                    "severity": "High",
                    "description": "Test vulnerability",
                    "cvss": [
                        {
                            "version": "3.1",
                            "metrics": {"baseScore": 7.5},
                        }
                    ],
                },
                "relatedVulnerabilities": [],
                "matchDetails": [{"type": "exact-direct-match"}],
                "artifact": {
                    "name": "openssl",
                    "version": "1.1.1k",
                    "type": "deb",
                    "locations": [{"path": "/usr/lib/libssl.so"}],
                },
            }
        ],
    }


@pytest.fixture
def sample_grype_report_with_ghsa():
    """Sample Grype report with GHSA ID that has related CVE."""
    return {
        "_source_file": "test-ghsa-report.json",
        "_scanner": "grype",
        "source": {"target": {"userInput": "python:3.11"}},
        "descriptor": {
            "version": "0.100.0",
            "db": {
                "built": "2024-01-01T00:00:00Z",
                "schemaVersion": 5,
            },
        },
        "matches": [
            {
                "vulnerability": {
                    "id": "GHSA-xxxx-yyyy-zzzz",
                    "severity": "Medium",
                    "description": "Test GHSA vulnerability",
                    "cvss": [
                        {
                            "version": "3.1",
                            "metrics": {"baseScore": 6.5},
                        }
                    ],
                },
                "relatedVulnerabilities": [
                    {
                        "id": "CVE-2024-99999",
                        "namespace": "nvd:cpe",
                    }
                ],
                "matchDetails": [{"type": "exact-direct-match"}],
                "artifact": {
                    "name": "requests",
                    "version": "2.28.0",
                    "type": "python",
                    "locations": [{"path": "/usr/local/lib/python3.11/site-packages"}],
                },
            }
        ],
    }


@pytest.fixture
def sample_trivy_report():
    """Sample Trivy report for testing."""
    return {
        "_source_file": "test-trivy-report.json",
        "_scanner": "trivy",
        "ArtifactName": "nginx:1.21",
        "SchemaVersion": "2.0.0",
        "CreatedAt": "2024-01-01T00:00:00Z",
        "Results": [
            {
                "Type": "deb",
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2024-12345",
                        "PkgName": "openssl",
                        "InstalledVersion": "1.1.1k",
                        "Severity": "HIGH",
                        "Description": "Test vulnerability",
                        "CVSS": {
                            "nvd": {"V3Score": 7.5},
                        },
                        "References": ["https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-12345"],
                        "PublishedDate": "2024-01-01T00:00:00Z",
                        "LastModifiedDate": "2024-01-02T00:00:00Z",
                    }
                ],
            }
        ],
    }


@pytest.fixture
def sample_trivy_report_with_fix():
    """Sample Trivy report with fixed version."""
    return {
        "_source_file": "test-trivy-fix-report.json",
        "_scanner": "trivy",
        "ArtifactName": "alpine:3.18",
        "SchemaVersion": "2.0.0",
        "CreatedAt": "2024-01-01T00:00:00Z",
        "Results": [
            {
                "Type": "apk",
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2024-54321",
                        "PkgName": "libcrypto",
                        "InstalledVersion": "3.0.8-r0",
                        "FixedVersion": "3.0.9-r0",
                        "Severity": "CRITICAL",
                        "Description": "Critical vulnerability with fix",
                        "CVSS": {
                            "nvd": {"V3Score": 9.8},
                        },
                        "References": ["https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-54321"],
                        "PublishedDate": "2024-01-01T00:00:00Z",
                        "LastModifiedDate": "2024-01-02T00:00:00Z",
                    }
                ],
            }
        ],
    }


@pytest.fixture
def sample_sbom_report():
    """Sample Syft SBOM report for testing."""
    return {
        "descriptor": {
            "name": "syft",
            "version": "0.100.0",
        },
        "artifacts": [
            {
                "name": "nginx",
                "version": "1.21.0",
                "type": "deb",
            }
        ],
        "schema": {
            "version": "5.0.0",
        },
    }


@pytest.fixture
def temp_reports_dir(tmp_path, sample_grype_report):
    """Create a temporary directory with sample reports."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    report_file = reports_dir / "test-report.json"
    report_file.write_text(json.dumps(sample_grype_report))

    return reports_dir


@pytest.fixture
def temp_output_file(tmp_path):
    """Create a temporary output file path."""
    return tmp_path / "unified-report.json"


@pytest.fixture
def mock_subprocess_success(monkeypatch):
    """Mock subprocess.run to return successful results."""
    import subprocess

    class MockCompletedProcess:
        def __init__(self, stdout="", stderr="", returncode=0):
            self.stdout = stdout
            self.stderr = stderr
            self.returncode = returncode

    def mock_run(*args, **kwargs):
        command = args[0]
        if "which" in command:
            return MockCompletedProcess(stdout="/usr/local/bin/grype\n")
        elif "version" in command:
            return MockCompletedProcess(stdout="Version: 0.100.0\n")
        elif "grype" in command:
            scan_result = {
                "matches": [
                    {
                        "vulnerability": {
                            "id": "CVE-2024-12345",
                            "severity": "High",
                            "cvss": [{"version": "3.1", "metrics": {"baseScore": 7.5}}],
                        },
                        "relatedVulnerabilities": [],
                        "matchDetails": [],
                        "artifact": {
                            "name": "test",
                            "version": "1.0",
                            "type": "deb",
                            "locations": [],
                        },
                    }
                ]
            }
            return MockCompletedProcess(stdout=json.dumps(scan_result))
        elif "syft" in command and "convert" in command:
            cdx_result = {"bomFormat": "CycloneDX", "specVersion": "1.4"}
            return MockCompletedProcess(stdout=json.dumps(cdx_result))
        elif "trivy" in command:
            return MockCompletedProcess()
        return MockCompletedProcess()

    monkeypatch.setattr(subprocess, "run", mock_run)


@pytest.fixture
def mock_subprocess_failure(monkeypatch):
    """Mock subprocess.run to simulate command failures."""
    import subprocess

    def mock_run(*args, **kwargs):
        if kwargs.get("check"):
            raise subprocess.CalledProcessError(1, args[0], stderr="Command failed")
        return None

    monkeypatch.setattr(subprocess, "run", mock_run)


@pytest.fixture
def mock_subprocess_not_found(monkeypatch):
    """Mock subprocess.run to simulate command not found."""
    import subprocess

    def mock_run(*args, **kwargs):
        raise FileNotFoundError("Command not found")

    monkeypatch.setattr(subprocess, "run", mock_run)


@pytest.fixture
def vuln_map_sample():
    """Sample vulnerability map for testing report generation."""
    return {
        "CVE-2024-12345": {
            "count": 2,
            "selected_scanner": "grype",
            "scanner_sources": ["grype"],  # Added scanner_sources field
            "vulnerability_data": {
                "id": "CVE-2024-12345",
                "severity": "High",
                "description": "Test vulnerability",
                "cvss": [{"version": "3.1", "metrics": {"baseScore": 7.5}}],
            },
            "related_vulnerabilities": [],
            "affected_sources": [
                {
                    "source_file": "report1.json",
                    "image": "nginx:1.21",
                    "artifact": {
                        "name": "openssl",
                        "version": "1.1.1k",
                        "type": "deb",
                        "location": "/usr/lib/libssl.so",
                    },
                },
                {
                    "source_file": "report2.json",
                    "image": "alpine:3.18",
                    "artifact": {
                        "name": "openssl",
                        "version": "1.1.1k",
                        "type": "apk",
                        "location": "/lib/libssl.so",
                    },
                },
            ],
            "match_details": [{"type": "exact-direct-match"}],
        },
        "CVE-2024-54321": {
            "count": 1,
            "selected_scanner": "trivy",
            "scanner_sources": ["trivy"],  # Added scanner_sources field
            "vulnerability_data": {
                "id": "CVE-2024-54321",
                "severity": "Critical",
                "description": "Critical vulnerability",
                "cvss": {"nvd": {"V3Score": 9.8}},
            },
            "related_vulnerabilities": [],
            "affected_sources": [
                {
                    "source_file": "report1.json",
                    "image": "nginx:1.21",
                    "artifact": {
                        "name": "libcrypto",
                        "version": "3.0.8",
                        "type": "apk",
                        "location": None,
                    },
                }
            ],
            "match_details": [],
        },
    }
