# Package Sources Guide

Complete guide for using local and remote packages with CVE Report Aggregator.

## Overview

CVE Report Aggregator supports three package source strategies:

1. **Local Packages**: Process Zarf archives from `./packages/` directory (auto-detected, no config needed)
1. **Remote Packages**: Download from OCI registry using UDS CLI (requires authentication)
1. **Mixed Packages** (v0.14.0+): Combine both with per-package `source` field

### Feature Comparison

| Feature        | Local         | Remote   | Mixed (v0.14.0+) |
| -------------- | ------------- | -------- | ---------------- |
| **Network**    | No            | Yes      | Partial          |
| **Config**     | Auto-detected | Required | Per-package      |
| **Speed**      | Fast          | Slower   | Optimized        |
| **Air-Gapped** | ✅            | ❌       | ✅ Partial       |
| **Auth**       | None          | Required | Remote only      |

## Quick Start

### Local Packages

```bash
# Place packages and run (auto-detected)
mkdir -p packages && cp /path/to/*.tar.zst packages/
cve-report-aggregator --log-level DEBUG
```

### Remote Packages

```yaml
# .cve-aggregator.yaml
registry: registry.defenseunicorns.com
organization: sld-45
packages:
  - name: gitlab
    version: 18.4.2-uds.0-unicorn
```

```bash
docker login registry.defenseunicorns.com
cve-report-aggregator --log-level DEBUG
```

### Mixed Packages (v0.14.0+)

```yaml
# .cve-aggregator.yaml
registry: registry.defenseunicorns.com
organization: sld-45
packages:
  - name: core-base
    version: 0.55.0-unicorn
    source: local      # From ./packages/
  - name: gitlab
    version: 18.4.2-uds.0-unicorn
    source: remote     # From registry
```

## Configuration Modes

### Auto-Detect (No Config)

Priority order: Local packages → Remote (if enabled) → Existing reports

### Local-Only

```yaml
localOnly: true
```

Or: `cve-report-aggregator --local-only`

### Mixed (v0.14.0+)

Per-package `source: local` or `source: remote` (defaults to `remote`)

## Local Packages

### Setup

```bash
./packages/
└── zarf-package-<name>-<arch>-<version>.tar.zst
```

**Example**: `zarf-package-gitlab-amd64-18.4.2-uds.0-unicorn.tar.zst`

### How It Works

1. Auto-detect `.tar.zst` files in `./packages/`
1. Extract metadata: `zarf package inspect definition <archive>`
1. Extract SBOMs: `zarf package inspect <archive> --sbom-out ./reports/`
1. Scan with Grype or Trivy

> [!NOTE]
> Init packages (`zarf-init-*.tar.zst`) are excluded.

## Remote Packages

### Prerequisites

```bash
# Install UDS CLI
brew install defenseunicorns/tap/uds

# Authenticate
docker login registry.defenseunicorns.com
# OR
uds auth login registry.defenseunicorns.com
```

### Configuration

```yaml
registry: registry.defenseunicorns.com
organization: sld-45
maxWorkers: 14  # Parallel downloads (optional)
packages:
  - name: gitlab
    version: 18.4.2-uds.0-unicorn
```

## Mixed Packages (v0.14.0+)

### Per-Package Source Control

Each package specifies its source independently:

```yaml
packages:
  # Local (fast, cached)
  - name: core-base
    version: 0.55.0-unicorn
    source: local

  # Remote (always latest)
  - name: gitlab
    version: 18.4.2-uds.0-unicorn
    source: remote
```

### Benefits

- **Flexibility**: Mix sources based on availability
- **Performance**: Use local for frequently scanned packages
- **Cost**: Reduce bandwidth and registry rate limits
- **Deployment**: Support air-gapped, hybrid, and CI/CD scenarios

## Common Scenarios

### Air-Gapped Development

```yaml
localOnly: true
packages:
  - name: core-base
    version: 0.55.0-unicorn
    source: local
```

### Hybrid Environment

```yaml
registry: registry.defenseunicorns.com
organization: sld-45
packages:
  - name: core-base      # Cached local
    version: 0.55.0-unicorn
    source: local
  - name: gitlab         # Latest remote
    version: 18.4.2-uds.0-unicorn
    source: remote
```

### CI/CD Pipeline

```yaml
registry: registry.defenseunicorns.com
organization: sld-45
maxWorkers: 14
packages:
  - name: gitlab
    version: 18.4.2-uds.0-unicorn
    source: remote       # Always fresh
```

## Troubleshooting

### "Local package archive not found"

```bash
# Verify filename pattern
ls -lh packages/zarf-package-<name>-<arch>-<version>.tar.zst
```

### "Failed to download remote packages"

```bash
# Re-authenticate
docker login registry.defenseunicorns.com
# Test download
uds zarf package inspect sbom registry.defenseunicorns.com/sld-45/gitlab-18.4.2-uds.0-unicorn:amd64
```

### "No local packages found"

```bash
# Check directory
ls -lh packages/*.tar.zst | grep -v "zarf-init-"
```

### "Failed to extract package metadata"

```bash
# Install Zarf CLI
brew install defenseunicorns/tap/zarf
# Verify
zarf version
# Test package
zarf package inspect packages/zarf-package-*.tar.zst
```

## Migration Guide

### v0.13.0 → v0.14.0

**No Breaking Changes** - Existing configs work unchanged.

#### Before (v0.13.0)

```yaml
# Either local OR remote (not both)
packages:
  - name: gitlab
    version: 18.4.2-uds.0-unicorn
```

#### After (v0.14.0)

```yaml
# Mix local AND remote
packages:
  - name: gitlab
    version: 18.4.2-uds.0-unicorn
    source: local    # NEW: per-package source
  - name: headlamp
    version: 0.35.0-uds.0-registry1
    source: remote   # NEW: per-package source
```

> [!NOTE]
> `source: remote` is default if omitted.

## Docker Usage

### Local Packages

```bash
docker run -it --rm \
  -v $(pwd)/packages:/home/cve-aggregator/packages:ro \
  -v $(pwd)/output:/home/cve-aggregator/output \
  ghcr.io/mkm29/cve-report-aggregator:latest \
  --local-only --log-level DEBUG
```

### Remote Packages

```bash
docker run -it --rm \
  -v $(pwd)/.cve-aggregator.yaml:/home/cve-aggregator/.cve-aggregator.yaml \
  -v $(pwd)/output:/home/cve-aggregator/output \
  -v ~/.docker/config.json:/home/cve-aggregator/.docker/config.json:ro \
  ghcr.io/mkm29/cve-report-aggregator:latest
```

### Mixed Packages

```bash
docker run -it --rm \
  -v $(pwd)/.cve-aggregator.yaml:/home/cve-aggregator/.cve-aggregator.yaml \
  -v $(pwd)/packages:/home/cve-aggregator/packages:ro \
  -v $(pwd)/output:/home/cve-aggregator/output \
  -v ~/.docker/config.json:/home/cve-aggregator/.docker/config.json:ro \
  ghcr.io/mkm29/cve-report-aggregator:latest
```

## Best Practices

1. **Keep `./packages/` organized** - Only relevant packages
1. **Preserve filenames** - Use original Zarf naming convention
1. **Clean old versions** - Remove outdated packages to save space
1. **Exclude from Git** - Add `packages/` to `.gitignore`
1. **Use `--local-only` for air-gapped** - Prevent network calls
1. **Debug with `--log-level DEBUG`** - See detailed processing
1. **Mixed strategy** - Local for stable, remote for frequently updated
1. **Secure credentials** - Never commit registry auth to Git

## Quick Reference

### CLI Commands

```bash
# Auto-detect local packages
cve-report-aggregator

# Local-only (air-gapped)
cve-report-aggregator --local-only

# With debug logging
cve-report-aggregator --log-level DEBUG

# Specific scanner
cve-report-aggregator --scanner trivy

# With CVE enrichment
export OPENAI_API_KEY=sk-...
cve-report-aggregator --enrich-cves
```

### Configuration Templates

**Minimal (Local):**

```yaml
localOnly: true
```

**Basic Remote:**

```yaml
registry: registry.defenseunicorns.com
organization: sld-45
packages:
  - name: gitlab
    version: 18.4.2-uds.0-unicorn
```

**Mixed (v0.14.0+):**

```yaml
registry: registry.defenseunicorns.com
organization: sld-45
packages:
  - {name: core-base, version: 0.55.0-unicorn, source: local}
  - {name: gitlab, version: 18.4.2-uds.0-unicorn, source: remote}
```

## Summary

### Key Features

- **v0.14.0+**: Per-package source specification (`source: local|remote`)
- **Local**: Auto-detected, fast, air-gapped friendly
- **Remote**: Registry-based, always latest, requires auth
- **Mixed**: Combine for optimal performance and flexibility
- **Backward Compatible**: No breaking changes from v0.13.0

### Output

All reports saved to `$HOME/output/` with format: `<package>-<version>.json`

### Next Steps

- Review [.cve-aggregator.example.yaml](./examples/.cve-aggregator.example.yaml) for complete examples
- Try [.cve-aggregator.local-example.yaml](./examples/.cve-aggregator.local-example.yaml) with your local packages
- See [README.md](../README.md) for general usage and features
