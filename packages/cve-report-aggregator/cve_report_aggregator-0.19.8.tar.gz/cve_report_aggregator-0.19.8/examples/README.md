# CVE Report Aggregator Examples

This directory contains example configurations demonstrating how to use the CVE Report Aggregator.

## Configuration Files

- [.cve-aggregator.example.yaml](./.cve-aggregator.example.yaml): Full example configuration with all options
  documented, including mixed local/remote packages and CVE enrichment via OpenRouter.
- [.cve-aggregator.local-example.yaml](./.cve-aggregator.local-example.yaml): Simplified example for scanning local
  packages only.

## CVE Enrichment

The examples include configuration for AI-powered CVE enrichment using OpenRouter. To enable enrichment:

1. Set your API key: `export OPENROUTER_API_KEY=sk-or-...`
1. Set `enrich.enabled: true` in your configuration
1. Choose a model (default: `x-ai/grok-code-fast-1`)

See the main [README](../README.md#cve-enrichment) for full enrichment documentation.
