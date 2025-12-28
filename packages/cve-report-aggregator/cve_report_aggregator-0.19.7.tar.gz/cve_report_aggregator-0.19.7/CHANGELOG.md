# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.19.7](https://github.com/mkm29/cve-report-aggregator/compare/v0.19.6...v0.19.7) (2025-12-25)


### Miscellaneous Chores

* **deps-dev:** bump ty from 0.0.5 to 0.0.6 in the development-dependencies group ([f760a8e](https://github.com/mkm29/cve-report-aggregator/commit/f760a8ebca294fa46484b1379c28c5136b01347f))
* **deps-dev:** bump ty in the development-dependencies group ([3e03f73](https://github.com/mkm29/cve-report-aggregator/commit/3e03f73a5ad1270103dbc1f081ae8022f4dbb99a))
* **deps:** bump anchore/sbom-action from 0.20.11 to 0.21.0 ([e5191e9](https://github.com/mkm29/cve-report-aggregator/commit/e5191e9c0b6913a8ec05f0f337a4a9c3cbcf4e27))
* **deps:** bump anchore/sbom-action from 0.20.11 to 0.21.0 ([a6b5eec](https://github.com/mkm29/cve-report-aggregator/commit/a6b5eec45c0283bddd0d14507997e6393ee269f2))

## [0.19.6](https://github.com/mkm29/cve-report-aggregator/compare/v0.19.5...v0.19.6) (2025-12-22)


### Bug Fixes

* refactor create executive summary function to reduce complexity ([fc7b3e9](https://github.com/mkm29/cve-report-aggregator/commit/fc7b3e9bc10f41d3c71bd670ae8af3d6291ec0ad))
* refactor scanner pipeline to reduct cyclomatic complexity ([9401606](https://github.com/mkm29/cve-report-aggregator/commit/94016061a395feab47bdff306c15037a1298dbb4))


### Code Refactoring

* Simplify CLI argument processing and enhance configuration handling ([bc73658](https://github.com/mkm29/cve-report-aggregator/commit/bc73658bcb44548c0bcb122481977d3208f54335))
* Simplify CLI argument processing and enhance configuration handling ([f4bfb87](https://github.com/mkm29/cve-report-aggregator/commit/f4bfb872bd00562b3b632e1f46d9d0ca8686226a))
* Simplify create_executive_summary function and enhance severity statistics handling ([16858e4](https://github.com/mkm29/cve-report-aggregator/commit/16858e426a33cf2cc106c9232d64a6feb6f6adf5))

## [0.19.5](https://github.com/mkm29/cve-report-aggregator/compare/v0.19.4...v0.19.5) (2025-12-22)


### Miscellaneous Chores

* **deps-dev:** bump the development-dependencies group with 3 updates ([583d842](https://github.com/mkm29/cve-report-aggregator/commit/583d8420975e4e500208da8368521332b750390a))

## [0.19.4](https://github.com/mkm29/cve-report-aggregator/compare/v0.19.3...v0.19.4) (2025-12-22)


### Miscellaneous Chores

* **deps:** bump the production-dependencies group with 2 updates ([18efa7e](https://github.com/mkm29/cve-report-aggregator/commit/18efa7e0e4faed40c2426d6a7f418cea151cad6a))

## [0.19.3](https://github.com/mkm29/cve-report-aggregator/compare/v0.19.2...v0.19.3) (2025-12-22)


### Miscellaneous Chores

* **deps:** bump actions/attest-build-provenance from 2.4.0 to 3.1.0 ([baceb69](https://github.com/mkm29/cve-report-aggregator/commit/baceb699ddc194ee1cf47c43ea585708fc07b036))

## [0.19.2](https://github.com/mkm29/cve-report-aggregator/compare/v0.19.1...v0.19.2) (2025-12-22)


### Miscellaneous Chores

* **deps:** bump actions/attest-sbom from 2.4.0 to 3.0.0 ([69cc57e](https://github.com/mkm29/cve-report-aggregator/commit/69cc57e922d8b5c4f78a36782dbea3869b146c31))
* **deps:** bump actions/attest-sbom from 2.4.0 to 3.0.0 ([8452013](https://github.com/mkm29/cve-report-aggregator/commit/84520132c6ea2082803575bbd20c4f8e9b60e0f1))

## [0.19.1](https://github.com/mkm29/cve-report-aggregator/compare/v0.19.0...v0.19.1) (2025-12-20)


### Bug Fixes

* auto use colors docker entrypoint ([d01483b](https://github.com/mkm29/cve-report-aggregator/commit/d01483b8976304665c381ce46ddc5073205a3a37))
* enable colored output in Docker entrypoint and add progress indicators for database updates ([2554851](https://github.com/mkm29/cve-report-aggregator/commit/2554851eec1107fef71b27f39554fba48c598b98))
* improve changelog formatting for better readability ([1ff572f](https://github.com/mkm29/cve-report-aggregator/commit/1ff572fd4bdc7796f14d318bdb1e9c2523b7a37e))
* improve Trivy error handling and update exit code handling in scans ([7a94d4f](https://github.com/mkm29/cve-report-aggregator/commit/7a94d4f7059eac20d2a15567039bcc07c947e7af))
* improve Trivy error handling and update exit code handling in scans ([8599ae4](https://github.com/mkm29/cve-report-aggregator/commit/8599ae4df103721bbd593d13932d801f23646482))
* improve Trivy error handling and update exit code handling in scans ([6aebbf8](https://github.com/mkm29/cve-report-aggregator/commit/6aebbf86741d8bc7445b46832041860e48a0c1d2))
* update documentation syntax for code blocks in error handling and package guides ([87b4587](https://github.com/mkm29/cve-report-aggregator/commit/87b458780ba3249f308d552f86f54e254cf7149b))
* update documentation syntax for code blocks in error handling and package guides ([0859c3a](https://github.com/mkm29/cve-report-aggregator/commit/0859c3a3084058d396f60533280d5d0ef528dfd2))
* update references from Zarf to UDS CLI for local package scanning ([057fd6d](https://github.com/mkm29/cve-report-aggregator/commit/057fd6ddbea9ed000a5879dc7cb38990128bca44))
* update references from Zarf to UDS CLI for local package scanning ([910af9c](https://github.com/mkm29/cve-report-aggregator/commit/910af9cfbb0360b22f9e6ffbb9c501016b207b45))

## [0.19.0](https://github.com/mkm29/cve-report-aggregator/compare/v0.18.0...v0.19.0) (2025-12-20)

### Features

- add code improvement analysis and recommendations for the CVE Report Aggregator
  ([452c27a](https://github.com/mkm29/cve-report-aggregator/commit/452c27a189bd3f99bb50eb1a1a0ff57101e762ab))
- add code improvement analysis and recommendations for the CVE Report Aggregator
  ([d63b2e8](https://github.com/mkm29/cve-report-aggregator/commit/d63b2e87ad8882f7f35aebd7f3df59cdb1587e47))
- add functionality to persist Trivy reports
  ([6520ddc](https://github.com/mkm29/cve-report-aggregator/commit/6520ddc77aa2a4f9081f01e55e3e54aeb9dcf958))
- add functionality to persist Trivy reports in CycloneDX format for inspection
  ([63ca5a6](https://github.com/mkm29/cve-report-aggregator/commit/63ca5a6384a226dca3aaa6ab143ba42142ced6dd))
- add poll interval configuration for batch API processing
  ([a5c2732](https://github.com/mkm29/cve-report-aggregator/commit/a5c273285d54ca55cee5c70ba19176512280537f))
- add poll interval configuration for batch API processing
  ([0c827d7](https://github.com/mkm29/cve-report-aggregator/commit/0c827d7c5d4a42a7a21e7a16d5f6c6eba9721b87))
- add tarball creation for output artifacts and enhance input directory handling
  ([0402623](https://github.com/mkm29/cve-report-aggregator/commit/04026235ef2202bd63a06eb47bd66fc968fce23c))
- add tests for acquiring SBOMs from local and remote packages, including mixed scenarios and error handling
  ([87e8f8f](https://github.com/mkm29/cve-report-aggregator/commit/87e8f8f31c51e3e888c08d646b7cda5ac764f776))
- add unit tests for \_save_trivy_reports and process_trivy_reports with persist_cyclonedx_dir functionality
  ([7bdfabf](https://github.com/mkm29/cve-report-aggregator/commit/7bdfabfbff15e1740939d270484bf9fb25b0786d))
- Add unit tests for archive creation and executor management, save Trivy reports using aiofiles
  ([2b991d6](https://github.com/mkm29/cve-report-aggregator/commit/2b991d69ec634bea9b19040e5db22514327ee312))
- archive artifacts, add unit tests, async IO operations
  ([747a855](https://github.com/mkm29/cve-report-aggregator/commit/747a85526407343852d79f1b56c06da71e591cb9))
- break complex functions to satisfy SRP
  ([c2eab16](https://github.com/mkm29/cve-report-aggregator/commit/c2eab16371a637d856bb369ec88639de030b92ae))
- enhance processing of vulnerability reports by adding classification and persistence functions for SBOMs and Trivy
  reports ([0462978](https://github.com/mkm29/cve-report-aggregator/commit/0462978f8ada64b1254fcc2e4b67b11f2225e810))

### Bug Fixes

- update target Python version to 3.14 in pyproject.toml
  ([d63b2e8](https://github.com/mkm29/cve-report-aggregator/commit/d63b2e87ad8882f7f35aebd7f3df59cdb1587e47))

### Performance Improvements

- implement caching for Grype report processing to reduce redundant I/O
  ([d63b2e8](https://github.com/mkm29/cve-report-aggregator/commit/d63b2e87ad8882f7f35aebd7f3df59cdb1587e47))

### Documentation

- add comments explaining constants in core/constants.py
  ([d63b2e8](https://github.com/mkm29/cve-report-aggregator/commit/d63b2e87ad8882f7f35aebd7f3df59cdb1587e47))

### Code Refactoring

- improve type hints for context parameters across multiple modules
  ([d63b2e8](https://github.com/mkm29/cve-report-aggregator/commit/d63b2e87ad8882f7f35aebd7f3df59cdb1587e47))
- remove unnecessary type hints in context manager functions
  ([d63b2e8](https://github.com/mkm29/cve-report-aggregator/commit/d63b2e87ad8882f7f35aebd7f3df59cdb1587e47))
- update README for clarity and adjust tarball utility docstring
  ([32c1b28](https://github.com/mkm29/cve-report-aggregator/commit/32c1b2803b2370a5fc88c5c5e8792ca6ec5c60f5))

### Tests

- add verbose logging tests for async save_trivy_reports functionality
  ([0210079](https://github.com/mkm29/cve-report-aggregator/commit/02100798a76d02ed8d61abfbb282dabf08082801))

### Miscellaneous Chores

- update version to 0.17.3 in changelog and uv.lock
  ([2be3028](https://github.com/mkm29/cve-report-aggregator/commit/2be302867ee0cd8365fe908bc9507d530ba45cf0))

## [0.18.0](https://github.com/mkm29/cve-report-aggregator/compare/v0.17.3...v0.18.0) (2025-12-20)

### Features

- enhance package validation and secure API key handling in models
  ([507d584](https://github.com/mkm29/cve-report-aggregator/commit/507d58455c48bafa46af973172a5449634385a18))
- pin action and redact api keys
  ([d26c122](https://github.com/mkm29/cve-report-aggregator/commit/d26c122fecb616e68ae59637f2186b0668dd63b7))

### Miscellaneous Chores

- update version to 0.17.2 in uv.lock and improve changelog formatting
  ([955ba18](https://github.com/mkm29/cve-report-aggregator/commit/955ba18ef7d96a0e704ee96a222ae389b8ac3163))

## [0.17.3](https://github.com/mkm29/cve-report-aggregator/compare/v0.17.2...v0.17.3) (2025-12-20)

### Miscellaneous Chores

- migrate to official GitHub attestation actions and update documentation
  ([80821ad](https://github.com/mkm29/cve-report-aggregator/commit/80821ad62f9e7fce23158937edf7dbd6919fb6bd))
- migrate to official GitHub attestation actions and update documentation
  ([471c9b2](https://github.com/mkm29/cve-report-aggregator/commit/471c9b2164f324766b61242c8bee0f9ba8c94996))
- migrate to official GitHub attestation actions and update documentation
  ([88d2460](https://github.com/mkm29/cve-report-aggregator/commit/88d2460551e17c6b36bf484a65106dd47c7f1d5a))

## [0.17.2](https://github.com/mkm29/cve-report-aggregator/compare/v0.17.1...v0.17.2) (2025-12-20)

### Bug Fixes

- update changelog formatting for clarity
  ([7e753d3](https://github.com/mkm29/cve-report-aggregator/commit/7e753d31d06217bdf3fbc474144a42b5cf4951ca))
- update invalid important syntax readme
  ([53a2ac0](https://github.com/mkm29/cve-report-aggregator/commit/53a2ac0f13f08e02ae38ea1986c5b166ade7b768))

### Documentation

- update notes formatting in packages.md to use \[!NOTE\] syntax
  ([20209a8](https://github.com/mkm29/cve-report-aggregator/commit/20209a81483a1db5146d130ff5e7bb037af5a155))

### Miscellaneous Chores

- **docker:** fixed issue with attaching SPDX attestation
  ([e035bbe](https://github.com/mkm29/cve-report-aggregator/commit/e035bbeec5a1bf1464fdf03f8f5eb57e125b02e1))
- update version to 0.17.0 in uv.lock
  ([8e84a83](https://github.com/mkm29/cve-report-aggregator/commit/8e84a83dfb8cd1d9e893ad3b0948d78ef12d5d36))

## [0.17.1](https://github.com/mkm29/cve-report-aggregator/compare/v0.17.0...v0.17.1) (2025-12-20)

### Documentation

- update installation instructions to replace pipx with uv
  ([79d7163](https://github.com/mkm29/cve-report-aggregator/commit/79d7163f455afba117b1fb526a41f874de648188))

## [0.17.0](https://github.com/mkm29/cve-report-aggregator/compare/v0.16.1...v0.17.0) (2025-12-20)

### Features

- replace mypy with ty and add more pre-commit hooks (mostly for GH Actions)
  ([06d28e8](https://github.com/mkm29/cve-report-aggregator/commit/06d28e891c0e38e7621bddda4f3f1bbf07282286))

### Bug Fixes

- replace mypy with ty
  ([4c2dbc0](https://github.com/mkm29/cve-report-aggregator/commit/4c2dbc06a0972b3e23d1c426d4e53f8bc8b3f960))

## [0.16.1](https://github.com/mkm29/cve-report-aggregator/compare/v0.16.0...v0.16.1) (2025-12-20)

### Bug Fixes

- **deps:** pin dependency versons
  ([c2e8fc2](https://github.com/mkm29/cve-report-aggregator/commit/c2e8fc2d2f6d2baa0d9228e9382a1adf6fe0c8de))

### Miscellaneous Chores

- added commitlint.config.js file
  ([ee34381](https://github.com/mkm29/cve-report-aggregator/commit/ee343810b7120f6bd9bde5c3f09787aa89f18c68))
- **deps-dev:** bump the development-dependencies group with 5 updates
  ([9d81d68](https://github.com/mkm29/cve-report-aggregator/commit/9d81d68974b9be8d42fb098f8d06a308b21aefd3))
- update GitHub Actions to use latest versions of upload-artifact and setup-uv
  ([69d5131](https://github.com/mkm29/cve-report-aggregator/commit/69d51310f3b09908851ecfdfa7ec73f7676bddd2))
- update GitHub Actions to use latest versions of upload-artifact and setup-uv
  ([c6597a9](https://github.com/mkm29/cve-report-aggregator/commit/c6597a9a846786a4e06ec96e13ec5492af17f95c))
- **workflow:** remove npm cache configuration from Node.js setup
  ([bc68f88](https://github.com/mkm29/cve-report-aggregator/commit/bc68f882330c153a5516306ea96bfbfeff2a775f))

## [0.16.0](https://github.com/mkm29/cve-report-aggregator/compare/v0.15.0...v0.16.0) (2025-12-20)

### Features

- **docker:** add function to update Grype vulnerability database
  ([2f27ae0](https://github.com/mkm29/cve-report-aggregator/commit/2f27ae0b53485ed6325dae5fe3c52db083c37639))
- **docker:** enhance logging and add Trivy database update functionality
  ([392762b](https://github.com/mkm29/cve-report-aggregator/commit/392762b8cd8d816ee99a5b9e4d9b217bdd2ab6e3))
- **grype:** update grype db in entrypoint.sh
  ([b90ab3e](https://github.com/mkm29/cve-report-aggregator/commit/b90ab3e82ced2ba661730585cd8bf86fe5ab1dde))
- **grype:** update grype db in entrypoint.sh
  ([8bdaaf8](https://github.com/mkm29/cve-report-aggregator/commit/8bdaaf819ebfde458a1a3eb953efc382c2c7efd9))
- update trivy db in entrypoint script
  ([923ed24](https://github.com/mkm29/cve-report-aggregator/commit/923ed240a6e50b50bcc429c9c3c9ddab107740fe))
- **workflow:** update Node.js version to 20.x in commitlint configuration
  ([30c53fc](https://github.com/mkm29/cve-report-aggregator/commit/30c53fcdb10c196378913ebe7957b2f9aebc4c3e))

## [0.15.0](https://github.com/mkm29/cve-report-aggregator/compare/v0.14.0...v0.15.0) (2025-12-19)

### Features

- **docs:** add comprehensive retry logic documentation and enhance error handling references
  ([592fb4b](https://github.com/mkm29/cve-report-aggregator/commit/592fb4b7aa62699c05d7418f7bedba494331a5c0))
- **docs:** refine retry logic documentation for clarity and consistency
  ([a2d5f80](https://github.com/mkm29/cve-report-aggregator/commit/a2d5f806f65ac11b54ef3abb9aca2be123e6edce))
- **executor:** implement exponential backoff retry logic for transient failures
  ([cea57cf](https://github.com/mkm29/cve-report-aggregator/commit/cea57cf93e373d360afd027ee04d153faaadf6b4))
- **scanner:** add support for "both" scanner option and enhance tracking of scanner sources
  ([e686d39](https://github.com/mkm29/cve-report-aggregator/commit/e686d393e5c047acd71f961d68fe3eee8f44991f))
- **scanner:** allow scanning with trivy and grype
  ([93bd20c](https://github.com/mkm29/cve-report-aggregator/commit/93bd20c8b34ae4b0a9b6cbe952bc9e1b84f6fff7))
- support using Grpye and Trivy scanners; added retry logic
  ([079327e](https://github.com/mkm29/cve-report-aggregator/commit/079327ef115bc1508807de13e68b7d6380d04c88))
- **tests:** add detailed test failure report and enhance CLI test coverage
  ([e3e4252](https://github.com/mkm29/cve-report-aggregator/commit/e3e42526dbcf2541c45be3d82d5a7e542872a86e))
- **tests:** add OpenAI API key parameter for CLI configuration tests
  ([5576d29](https://github.com/mkm29/cve-report-aggregator/commit/5576d2987af0082fd26b1d494738d28a6b293a08))

### Bug Fixes

- **cli:** update command description to improve readability
  ([a2d5f80](https://github.com/mkm29/cve-report-aggregator/commit/a2d5f806f65ac11b54ef3abb9aca2be123e6edce))

### Code Refactoring

- **tests:** streamline imports and remove redundant verbose mode tests
  ([a2d5f80](https://github.com/mkm29/cve-report-aggregator/commit/a2d5f806f65ac11b54ef3abb9aca2be123e6edce))

## [0.14.0](https://github.com/mkm29/cve-report-aggregator/compare/v0.13.0...v0.14.0) (2025-12-19)

### Features

- Add comprehensive package sources guide and mixed package support
  ([2e92d0b](https://github.com/mkm29/cve-report-aggregator/commit/2e92d0b125dfd6d3a1d96f798ac5555f2ffc1ee8))
- Implement a concurrent pipeline for vulnerability scanning
  ([85a2dd5](https://github.com/mkm29/cve-report-aggregator/commit/85a2dd5f840065d5824974c55e89f2ac1865af0d))
- implement multi-threading pipeline
  ([d307ca6](https://github.com/mkm29/cve-report-aggregator/commit/d307ca62ef48412019eb41e72b7db0ab6863a6a6))
- **scanner:** enhance Trivy report processing to handle CycloneDX files
  ([6817da7](https://github.com/mkm29/cve-report-aggregator/commit/6817da7f684c875ea4f5e8d371176b98b62a4610))

### Bug Fixes

- **changelog:** format entries for consistency and clarity
  ([75e07ce](https://github.com/mkm29/cve-report-aggregator/commit/75e07ced2bf919fe36844ea54ac516ed075f448b))
- convert Grype SBOM report to cyclonedx-json for Trivy scanning
  ([a92fdfa](https://github.com/mkm29/cve-report-aggregator/commit/a92fdfaf146227e620168d29a5740196a9a7447e))
- trivy scan convert report first
  ([ed95ed3](https://github.com/mkm29/cve-report-aggregator/commit/ed95ed376124563c91e2f4dacb09add1da58ff6d))

### Miscellaneous Chores

- backported from main to update deps
  ([235717b](https://github.com/mkm29/cve-report-aggregator/commit/235717b05d2cd5fc328f3d6adcb3e973060b398e))
- backported from main to update deps
  ([286edd4](https://github.com/mkm29/cve-report-aggregator/commit/286edd4a26223b7e390c17b250524744cef1333f))
- bump version to 0.13.0
  ([6817da7](https://github.com/mkm29/cve-report-aggregator/commit/6817da7f684c875ea4f5e8d371176b98b62a4610))

## [0.13.0](https://github.com/mkm29/cve-report-aggregator/compare/v0.12.1...v0.13.0) (2025-11-02)

### Features

- **branch-protection:** allow dependabot branches in validation
  ([2ce6559](https://github.com/mkm29/cve-report-aggregator/commit/2ce6559c9fc4c49fb0d82dc087f23d427ff34a0f))
- **branch-protection:** allow dependabot branches in validation
  ([41e408c](https://github.com/mkm29/cve-report-aggregator/commit/41e408c2776918c1c0e63ab91a5580a73ae5c728))

### Bug Fixes

- update Contributor Guide link in pull request template
  ([b3cfabc](https://github.com/mkm29/cve-report-aggregator/commit/b3cfabcdfcb983a61ddfe07a77a619e1cc1178a6))

## [0.12.1](https://github.com/mkm29/cve-report-aggregator/compare/v0.12.0...v0.12.1) (2025-11-02)

### Bug Fixes

- update gh workflow and create issue template
  ([7c588ae](https://github.com/mkm29/cve-report-aggregator/commit/7c588ae8652cb930ed405296d01fdd731cb948a2))

### Miscellaneous Chores

- **deps:** bump actions/checkout from 4 to 5
  ([5bc6a4f](https://github.com/mkm29/cve-report-aggregator/commit/5bc6a4ff54d2410a37e35e3eb93776774e2f24b5))
- **deps:** bump actions/checkout from 4 to 5
  ([ffdea08](https://github.com/mkm29/cve-report-aggregator/commit/ffdea08c1c44730e074f24c69cc77d2895a0311f))
- **deps:** bump actions/download-artifact from 4 to 6
  ([767f473](https://github.com/mkm29/cve-report-aggregator/commit/767f47396008e496fe30255cde8e82cf9f11d1bc))
- **deps:** bump actions/download-artifact from 4 to 6
  ([5fc119a](https://github.com/mkm29/cve-report-aggregator/commit/5fc119a90f824310db01b5d0be41a72ca51f3e58))
- **deps:** bump actions/github-script from 7 to 8
  ([2f87e4c](https://github.com/mkm29/cve-report-aggregator/commit/2f87e4cfb0e61b3e67f1f41a6cc2843c5fa07ac2))
- **deps:** bump actions/github-script from 7 to 8
  ([3cb7cde](https://github.com/mkm29/cve-report-aggregator/commit/3cb7cde5a16a7b9c567d180bc4e8c82dd5b6e53b))
- **deps:** bump actions/setup-python from 5 to 6
  ([1370563](https://github.com/mkm29/cve-report-aggregator/commit/1370563586399ca865cd9c60b28bc013873d4eb8))
- **deps:** bump actions/setup-python from 5 to 6
  ([7661309](https://github.com/mkm29/cve-report-aggregator/commit/766130959e80f6f1304ce9991a31423720ec013c))
- **deps:** bump docker/build-push-action from 5 to 6
  ([6a8a977](https://github.com/mkm29/cve-report-aggregator/commit/6a8a9776768e22fa3f036bc4f58fb796be930efa))
- **deps:** bump docker/build-push-action from 5 to 6
  ([e316b09](https://github.com/mkm29/cve-report-aggregator/commit/e316b09c5abcee54be50195cf16e8e4c51d36fbb))
- **deps:** bump the production-dependencies group with 4 updates
  ([1fb54b7](https://github.com/mkm29/cve-report-aggregator/commit/1fb54b734b54e06f9b08577f487f58c3af2331b2))
- **deps:** bump the production-dependencies group with 4 updates
  ([9c001cd](https://github.com/mkm29/cve-report-aggregator/commit/9c001cd6a411d8043074903e32eca0c7cac0680f))
- remove commitlint workflow
  ([f03e309](https://github.com/mkm29/cve-report-aggregator/commit/f03e309162b922e72926e92c5531d0ccdf067ee3))
- update issue and pull request templates for consistency and clarity
  ([a35e331](https://github.com/mkm29/cve-report-aggregator/commit/a35e331415984cf6a0ecad70dea5627f501867e7))
- update issue and pull request templates for consistency and clarity
  ([211418d](https://github.com/mkm29/cve-report-aggregator/commit/211418d5a5df39efa1619653a28e26cce08e887e))

## [0.12.0](https://github.com/mkm29/cve-report-aggregator/compare/v0.11.0...v0.12.0) (2025-11-02)

### Features

- add AppContext, enhance validation, increase test coverage
  ([6d1f193](https://github.com/mkm29/cve-report-aggregator/commit/6d1f193b03df47ea1ecbe8c36e5f8c5809678f41))
- Add comprehensive tests for json_utils and models modules
  ([1584314](https://github.com/mkm29/cve-report-aggregator/commit/1584314adee0058b24532ce8219ce6ebcef4a7ac))
- Enhance acquire_sboms test by checking command existence before scanning local packages
  ([707071c](https://github.com/mkm29/cve-report-aggregator/commit/707071c498545503d9249ea8ae9a9eaca1736451))
- Enhance error handling for package pulling in CVE Report Aggregator
  ([db65324](https://github.com/mkm29/cve-report-aggregator/commit/db6532497b99cf298fe28ed626fdc75204a00556))
- Enhance local package detection and filtering; add tests for edge cases and enrichment functionality
  ([7792b2c](https://github.com/mkm29/cve-report-aggregator/commit/7792b2cd0444856c78cdf689a6517b6612cc99ad))
- enhance package pulling error handling
  ([dd6d6e7](https://github.com/mkm29/cve-report-aggregator/commit/dd6d6e75d7f4b083958e1d86ffde01849b37cc71))
- Implement local Zarf package scanner for extracting SBOMs
  ([b945982](https://github.com/mkm29/cve-report-aggregator/commit/b9459828f143c78f86490f692f6c13bbf4e0f445))
- Implement local Zarf package scanner for extracting SBOMs
  ([d53bf3f](https://github.com/mkm29/cve-report-aggregator/commit/d53bf3f964655680fe7731026b54494fb04a8342))
- improve validation
  ([c0f4ce2](https://github.com/mkm29/cve-report-aggregator/commit/c0f4ce285daed5123a27271104126e9fd673ce4d))
- Introduce AppContext for dependency injection and refactor error handling
  ([9c5a157](https://github.com/mkm29/cve-report-aggregator/commit/9c5a1575995bc8c01006bd77ddba99474bd66196))
- Refactor validation error handling and introduce new EnrichmentError class
  ([d204308](https://github.com/mkm29/cve-report-aggregator/commit/d204308d4485ef3eeb6dde44e0abe5b5fbb1facb))
- Update README and remove error handling demo script; enhance JSON loading and validation across modules
  ([5123c2a](https://github.com/mkm29/cve-report-aggregator/commit/5123c2a8463586f62da94f3030d2bb9e696f24ad))

### Bug Fixes

- Update ErrorHandler instantiation in tests
  ([d53bf3f](https://github.com/mkm29/cve-report-aggregator/commit/d53bf3f964655680fe7731026b54494fb04a8342))

### Code Refactoring

- code structure for improved readability and maintainability
  ([e7ecdbd](https://github.com/mkm29/cve-report-aggregator/commit/e7ecdbd4ab03e09981f15858ba4fe7053ea38696))
- Remove unused import from test_models.py
  ([67b3780](https://github.com/mkm29/cve-report-aggregator/commit/67b3780c123e709bc8061bb56d89971c1b924470))
- Simplify error handling in load_json_report function
  ([16d97ea](https://github.com/mkm29/cve-report-aggregator/commit/16d97eab27245e159ec9e05a067c274a1209e976))

### Tests

- Add unit tests for local package scanning functionality
  ([d53bf3f](https://github.com/mkm29/cve-report-aggregator/commit/d53bf3f964655680fe7731026b54494fb04a8342))
- Add unit tests for orchestrator module
  ([d53bf3f](https://github.com/mkm29/cve-report-aggregator/commit/d53bf3f964655680fe7731026b54494fb04a8342))
- Add unit tests for validation module
  ([d53bf3f](https://github.com/mkm29/cve-report-aggregator/commit/d53bf3f964655680fe7731026b54494fb04a8342))

## [0.11.0](https://github.com/mkm29/cve-report-aggregator/compare/v0.10.1...v0.11.0) (2025-10-21)

### Features

- add OCI image labels and build-time metadata to Dockerfile and workflow
  ([1e656d4](https://github.com/mkm29/cve-report-aggregator/commit/1e656d4d36fa042ce082517dc722f9453abf061c))

### Bug Fixes

- add OCI image labels and build-time metadata to Dockerfile and workflow
  ([a3bff3f](https://github.com/mkm29/cve-report-aggregator/commit/a3bff3f19d6831c4f7f95870eacb76d33f81e411))

## [0.10.1](https://github.com/mkm29/cve-report-aggregator/compare/v0.10.0...v0.10.1) (2025-10-21)

### Documentation

- enhance README with detailed configuration and performance improvements
  ([3efed66](https://github.com/mkm29/cve-report-aggregator/commit/3efed6602aa19df6bf28df8223fac2357c3e934d))
- update README with new YAML structure
  ([660abd4](https://github.com/mkm29/cve-report-aggregator/commit/660abd48b0db65c0bf560ac653008156c940b860))

## [0.10.0](https://github.com/mkm29/cve-report-aggregator/compare/v0.9.0...v0.10.0) (2025-10-20)

### Features

- enchance CVEs using the OpenAI API
  ([ff78b4e](https://github.com/mkm29/cve-report-aggregator/commit/ff78b4e0da5109fd63ad0800ad5972a3db7fcc27))

### Bug Fixes

- import ConfigurationError in config.py for better error handling
  ([7dfcdfb](https://github.com/mkm29/cve-report-aggregator/commit/7dfcdfb47f6a28d0c966f3ca481c02cfc9478783))

### Code Refactoring

- clean up imports in models.py for improved readability
  ([7dfcdfb](https://github.com/mkm29/cve-report-aggregator/commit/7dfcdfb47f6a28d0c966f3ca481c02cfc9478783))

### Miscellaneous Chores

- update version to 0.9.0 in uv.lock and refine changelog entries
  ([7dfcdfb](https://github.com/mkm29/cve-report-aggregator/commit/7dfcdfb47f6a28d0c966f3ca481c02cfc9478783))

## [0.9.0](https://github.com/mkm29/cve-report-aggregator/compare/v0.8.0...v0.9.0) (2025-10-20)

### Features

- add executive summary, constants, improve logging
  ([fd3ce8c](https://github.com/mkm29/cve-report-aggregator/commit/fd3ce8c5a1be8cd140e3dd323b05ce3876703bc3))
- **cli:** Add executive summary generation and update report handling
  ([b4c9072](https://github.com/mkm29/cve-report-aggregator/commit/b4c907239c0dadb1fd784a851d82f1bd1fdfc781))
- **cli:** Add executive summary generation and update report handling
  ([ed8661a](https://github.com/mkm29/cve-report-aggregator/commit/ed8661ac24c23aad0c4615a9832c501b9afb0453))

### Bug Fixes

- parallel processing improvements
  ([a3cc574](https://github.com/mkm29/cve-report-aggregator/commit/a3cc5744daeea83024721886917f3aec861f483e))

### Miscellaneous Chores

- **docs:** remove mkdocs for now until GitHub Pages issue is resolved
  ([b22eaeb](https://github.com/mkm29/cve-report-aggregator/commit/b22eaeba0099c86687373186d60335272e6a94f7))
- update version to 0.7.2 and refine changelog entries
  ([0f2c1d9](https://github.com/mkm29/cve-report-aggregator/commit/0f2c1d94bb70efb3c87816f9ab785c99537d3bba))

## [0.8.0](https://github.com/mkm29/cve-report-aggregator/compare/v0.7.2...v0.8.0) (2025-10-20)

### Features

- Add CLAUDE.md for repository guidance and performance optimization plan
  ([9638798](https://github.com/mkm29/cve-report-aggregator/commit/9638798874fb34a29dd0ffc7794a1d603ffc5df9))
- **config:** Add support for downloading SBOM reports from remote registry and configure max concurrent workers
  ([407382a](https://github.com/mkm29/cve-report-aggregator/commit/407382a3654a6ff139e152578773021bb309bcee))
- **downloader:** Implement parallel downloading of SBOM reports with thread safety and error handling
  ([407382a](https://github.com/mkm29/cve-report-aggregator/commit/407382a3654a6ff139e152578773021bb309bcee))
- enhanced type checking in report.py
  ([df8ee38](https://github.com/mkm29/cve-report-aggregator/commit/df8ee3882448de3e5164704f05d21db4472bedc6))
- parallel download packages
  ([400649b](https://github.com/mkm29/cve-report-aggregator/commit/400649b51711c23a47bc6ffea10c742fa1826fbe))
- parallelelize package downloads; improve type checking
  ([4ed6b90](https://github.com/mkm29/cve-report-aggregator/commit/4ed6b90140cb829fb9c933d30354e2ba62aac033))

### Bug Fixes

- **docker:** Set PYTHON_GIL environment variable to 0 for improved concurrency in Dockerfile
  ([407382a](https://github.com/mkm29/cve-report-aggregator/commit/407382a3654a6ff139e152578773021bb309bcee))
- increase fail severity to high
  ([726a5f6](https://github.com/mkm29/cve-report-aggregator/commit/726a5f65ab2991fb9666497bb32eb261df07a34d))

### Documentation

- **changelog:** Update CHANGELOG with new features and improvements related to SBOM downloading and parallel processing
  ([407382a](https://github.com/mkm29/cve-report-aggregator/commit/407382a3654a6ff139e152578773021bb309bcee))

### Code Refactoring

- enhance Grype scan workflow with improved triggers and deta…
  ([22b279a](https://github.com/mkm29/cve-report-aggregator/commit/22b279a7f7fbf6d47082dd35d2c1d20353a56ba9))
- enhance Grype scan workflow with improved triggers and detailed logging
  ([0e92cc9](https://github.com/mkm29/cve-report-aggregator/commit/0e92cc9e4851cf20662677caea2befb5979ca4eb))
- Improve formatting and readability in CLAUDE.md and PERFORMANCE_OPTIMIZATION.md; add Dockerfile for Python 3.14 with
  Free-Threading
  ([7cf751b](https://github.com/mkm29/cve-report-aggregator/commit/7cf751bad960eb0dc975c84d70d9b1ebd00580fb))
- improve type casting in image name extraction and update tests for clarity
  ([799ca94](https://github.com/mkm29/cve-report-aggregator/commit/799ca944d6f3ac49078479aa0c96f8e31318e3f1))
- Remove CLAUDE.md and PERFORMANCE_OPTIMIZATION.md documentation files
  ([a5070fd](https://github.com/mkm29/cve-report-aggregator/commit/a5070fd62ddbebf06a1a077bd6bc9bbff4a306ff))
- remove emoji from scan summary for clarity
  ([76fab17](https://github.com/mkm29/cve-report-aggregator/commit/76fab1760e2bed7296e36685306312b662648992))
- update Grype scan workflow to use outputs for image handling and improve summary reporting
  ([0029221](https://github.com/mkm29/cve-report-aggregator/commit/0029221868e23e8168c27398714b35aa1aab748e))
- update Python version to 3.14.0 and enhance image name extraction logic in reports
  ([ff9dc31](https://github.com/mkm29/cve-report-aggregator/commit/ff9dc31dfea111989f4e599cffdc96e721c18843))

### Tests

- **downloader:** Add comprehensive tests for parallel downloading functionality, including max workers configuration
  and error handling
  ([407382a](https://github.com/mkm29/cve-report-aggregator/commit/407382a3654a6ff139e152578773021bb309bcee))

## [0.7.2](https://github.com/mkm29/cve-report-aggregator/compare/v0.7.1...v0.7.2) (2025-10-20)

### Code Refactoring

- replace Semgrep scan with Grype vulnerability scan in workflow
  ([c763b51](https://github.com/mkm29/cve-report-aggregator/commit/c763b515a6085a6b458abb483db7b671805f62a7))
- replace Semgrep scan with Grype vulnerability scan in workflow
  ([70fa600](https://github.com/mkm29/cve-report-aggregator/commit/70fa600e5cabd9ba0f8bca86e50538d507ab4ea1))
- replace semgrep workflow with Grype scan
  ([8f20a87](https://github.com/mkm29/cve-report-aggregator/commit/8f20a8772eb69578a7066c8089c59c83dfe908af))

## [0.7.1](https://github.com/mkm29/cve-report-aggregator/compare/v0.7.0...v0.7.1) (2025-10-19)

### Bug Fixes

- added conditions to check for valid Docker auth
  ([5193b2b](https://github.com/mkm29/cve-report-aggregator/commit/5193b2b0ad5026e919ed667e4876e0783939fb52))
- improve Docker config validation and clarify authentication requirements in entrypoint script
  ([e7bd2df](https://github.com/mkm29/cve-report-aggregator/commit/e7bd2dfaf45f5d387e1df3b8813de6e08ab9ff20))
- improve Docker config validation and clarify authentication requirements in entrypoint script
  ([537e589](https://github.com/mkm29/cve-report-aggregator/commit/537e5899300ea54f1bd847fa5700a9bc3afaa8f0))

## [0.7.0](https://github.com/mkm29/cve-report-aggregator/compare/v0.6.0...v0.7.0) (2025-10-19)

### Features

- add case-insensitive log level normalization and corresponding tests
  ([89e1f7b](https://github.com/mkm29/cve-report-aggregator/commit/89e1f7b5b7e33aca7d5802e9f689ef0455c0b635))
- enhance CLI logging by displaying configuration settings in DEBUG mode and local variables in CRITICAL mode
  ([9d05f62](https://github.com/mkm29/cve-report-aggregator/commit/9d05f628e8511fc1b601793f6a7504fc7b96dcf7))
- enhance SBOM handling by grouping reports by package and updating output file naming
  ([c69a2fe](https://github.com/mkm29/cve-report-aggregator/commit/c69a2fe37249c35115645871f9aa9b7b9e2fa45d))

### Bug Fixes

- correct severity breakdown count assignment in CLI
  ([7ac67d2](https://github.com/mkm29/cve-report-aggregator/commit/7ac67d2d62fb2bb41349116ac66e799e32c5e286))
- download package names
  ([4c422fe](https://github.com/mkm29/cve-report-aggregator/commit/4c422fefc022414c6789b99febdf8e4b200eb2d3))

### Code Refactoring

- remove unused command execution functions and update tests to use ExecutorManager
  ([3640af0](https://github.com/mkm29/cve-report-aggregator/commit/3640af00e0c46871c944c3de2f665c3a593004e8))

### Tests

- enhance case-insensitive log level tests with temporary input directory setup
  ([82300e6](https://github.com/mkm29/cve-report-aggregator/commit/82300e6087103c8c7bed2e0bd19e0f45cec2c93a))
- enhance output file validation in CLI tests to ensure correct naming patterns and existence
  ([15f5e7e](https://github.com/mkm29/cve-report-aggregator/commit/15f5e7e63015f5d914ae571663e5b19f51fbeca6))

## [0.6.0](https://github.com/mkm29/cve-report-aggregator/compare/v0.5.2...v0.6.0) (2025-10-19)

### Features

- **docs:** enhance README with supply chain security details and image verification instructions
  ([b0bf1cd](https://github.com/mkm29/cve-report-aggregator/commit/b0bf1cdd77f167beee639f50d8f57956cb769d1d))
- enhance command execution safety and add markdown linting functionality
  ([8f4347c](https://github.com/mkm29/cve-report-aggregator/commit/8f4347c16934b185c28396b9e5897ec58f73f880))
- **workflows:** add container image security scan workflow
  ([4240453](https://github.com/mkm29/cve-report-aggregator/commit/4240453af71b4ccb2175f7ec35ad4d6b72fe2587))
- **workflows:** enhance Docker build and scan workflows with version tagging and security scan trigger
  ([591674c](https://github.com/mkm29/cve-report-aggregator/commit/591674cce74238c2bdb69c8be8951945712038f7))
- **workflows:** enhance security scanning workflows and artifact handling
  ([60f5122](https://github.com/mkm29/cve-report-aggregator/commit/60f51228778fa50e45555f66886622f66424db4d))

### Bug Fixes

- add SAST (grype scan) workflow
  ([65b4884](https://github.com/mkm29/cve-report-aggregator/commit/65b4884cc7d1c2606add35927b711ba2ab928c4f))
- implement SLSA level 3 in docker build workflow
  ([ef73efd](https://github.com/mkm29/cve-report-aggregator/commit/ef73efdd81cf260e280fc0b71aa4668feea76ed2))
- increase CI with SAST
  ([0f2ac1a](https://github.com/mkm29/cve-report-aggregator/commit/0f2ac1a0c5e2fe556ae701b219e1f665b9c791c9))
- remove \*.sarif from .gitignore
  ([13d96be](https://github.com/mkm29/cve-report-aggregator/commit/13d96be1d8e613a14a5ec42359f4cd8db4a6acce))
- update .gitignore to exclude SARIF files and remove semgrep.sarif
  ([6cad191](https://github.com/mkm29/cve-report-aggregator/commit/6cad19162c918de32d27bc5d1a38057edd5155e8))
- **workflows:** clean up branch triggers and add permissions for test jobs
  ([bb036ac](https://github.com/mkm29/cve-report-aggregator/commit/bb036acf5188cf519240c267d59501c2347579f0))
- **workflows:** comment out push tags configuration in Docker build workflow
  ([bd93541](https://github.com/mkm29/cve-report-aggregator/commit/bd93541caedd18ad924f94d76ccee17a1c6b2a81))
- **workflows:** enhance Docker build and release workflows with improved error handling and summary generation
  ([224d848](https://github.com/mkm29/cve-report-aggregator/commit/224d848a2c53db74af700cf0452dbac385b655f0))
- **workflows:** enhance image tag determination logic for scans triggered by Docker build workflow
  ([ce3248a](https://github.com/mkm29/cve-report-aggregator/commit/ce3248ae05cc7b571bd4966de8b9b2296ebd4885))
- **workflows:** remove pull_request trigger from Semgrep security scan workflow
  ([e095612](https://github.com/mkm29/cve-report-aggregator/commit/e095612b7e3f6457da924f97afd2010fecd4a3f5))
- **workflows:** update push event handling for feature branch and improve image tag determination
  ([b69bd84](https://github.com/mkm29/cve-report-aggregator/commit/b69bd844951b8d41b0941738d608900528a3ee03))
- **workflows:** update Semgrep security scan workflow and remove container image scanning
  ([08869d0](https://github.com/mkm29/cve-report-aggregator/commit/08869d08530510421c4b58b2e57e1cd78aaceb33))

## [0.5.2](https://github.com/mkm29/cve-report-aggregator/compare/v0.5.1...v0.5.2) (2025-10-19)

### Bug Fixes

- add missing permission docker build flow
  ([5d1e0fa](https://github.com/mkm29/cve-report-aggregator/commit/5d1e0fa877eec0592380b6555d118af7bd4a6c49))
- add missing permissions to docker build workflow
  ([82efe9d](https://github.com/mkm29/cve-report-aggregator/commit/82efe9dba7fc8103b79d1122a62723147ef03668))
- **release:** update permissions for trigger-docker-build job
  ([4c39f21](https://github.com/mkm29/cve-report-aggregator/commit/4c39f211f393f866cb35631c34902255b9e50f6a))

## [0.5.1](https://github.com/mkm29/cve-report-aggregator/compare/v0.5.0...v0.5.1) (2025-10-19)

### Bug Fixes

- moved pypi publish job to trigger
  ([9794a32](https://github.com/mkm29/cve-report-aggregator/commit/9794a32a11afcd773ee8a8c8dbc0221df4236175))

### Code Refactoring

- Simplify PyPI publication steps and adjust permissions in release workflow
  ([f0dad86](https://github.com/mkm29/cve-report-aggregator/commit/f0dad86edc17f571e3204ca276db6eab223c2bb1))
- Simplify PyPI publication steps and adjust permissions in release workflow
  ([459b40a](https://github.com/mkm29/cve-report-aggregator/commit/459b40a4d331a0643690acda2e32b66b53463ce7))

## [0.5.0](https://github.com/mkm29/cve-report-aggregator/compare/v0.4.1...v0.5.0) (2025-10-19)

### Features

- centralized log manager with structlog
  ([3a27b4c](https://github.com/mkm29/cve-report-aggregator/commit/3a27b4cfe1accf9a8b17e594b51eb3d3a591e65e))
- **downloader:** Implement remote package downloading for SBOM reports
  ([9ab4bcb](https://github.com/mkm29/cve-report-aggregator/commit/9ab4bcb070727be18fe7e08d114cda0b9985c7d7))
- Enhance global configuration management and add usage examples
  ([c46d45b](https://github.com/mkm29/cve-report-aggregator/commit/c46d45bba7477c516e2fc391cb04f3513c35804b))
- implement command executor manager
  ([1682e1a](https://github.com/mkm29/cve-report-aggregator/commit/1682e1a237c19751a72dfbb4757aaf15fd59fb97))
- Implement CVE Report Aggregator processing modules
  ([6bd8081](https://github.com/mkm29/cve-report-aggregator/commit/6bd8081c3292ae2755baa450ebddcddfbdcfaf1a))
- **logging:** Implement centralized logging system using structlog
  ([24b1a4d](https://github.com/mkm29/cve-report-aggregator/commit/24b1a4d9c3e3408d72e161f3f0bd9699212869ba))
- Reorganize modules, add command executor module
  ([fca9045](https://github.com/mkm29/cve-report-aggregator/commit/fca90459734551b61255c0bfe5261ebf4cdaf01d))

### Bug Fixes

- Remove redundant import of Generator from typing
  ([bcf4aad](https://github.com/mkm29/cve-report-aggregator/commit/bcf4aad4fd927b30d38e8876fb7f15c5d39c393b))
- **tests:** Refactor sample and quiet configuration fixtures for improved path handling
  ([6902f2f](https://github.com/mkm29/cve-report-aggregator/commit/6902f2f7710086ee96a97a05a82b69f523f0e07e))

## [0.4.1](https://github.com/mkm29/cve-report-aggregator/compare/v0.4.0...v0.4.1) (2025-10-18)

### Code Refactoring

- Simplify Dockerfile by removing python-builder stage and optimizing package installation
  ([530aa73](https://github.com/mkm29/cve-report-aggregator/commit/530aa73e2d24f3936591813f94b6ad5ff8dd465e))
- Simplify Dockerfile by removing python-builder stage and optimizing package installation
  ([1f8f0d6](https://github.com/mkm29/cve-report-aggregator/commit/1f8f0d6cafc94427a4fd9082fecc1ba8c5df563a))

## [0.4.0](https://github.com/mkm29/cve-report-aggregator/compare/v0.3.0...v0.4.0) (2025-10-18)

### Features

- Add Docker build trigger after successful release
  ([dfcf8f2](https://github.com/mkm29/cve-report-aggregator/commit/dfcf8f21b801bc3d6d51b713acdd612adbb7a576))
- Add Docker build trigger after successful release
  ([c8bc662](https://github.com/mkm29/cve-report-aggregator/commit/c8bc66269dd7ae870633c212685bc1d05872dc6d))

## [0.3.0](https://github.com/mkm29/cve-report-aggregator/compare/v0.2.0...v0.3.0) (2025-10-18)

### Features

- Implement comprehensive configuration management using Pydantic Settings with YAML support
  ([4d62a3f](https://github.com/mkm29/cve-report-aggregator/commit/4d62a3fa19cb8713e17ddf37c6b8c0a59fcb50f7))
- implement pydantic app config and mkdocs site
  ([f699282](https://github.com/mkm29/cve-report-aggregator/commit/f6992826f79c91c5c424d1b8cef57cfb7ca65408))
- pydantic config and mkdocs site
  ([ff707ed](https://github.com/mkm29/cve-report-aggregator/commit/ff707eddf87de2612163dcc053e5a424f7af4974))

### Bug Fixes

- Update documentation links and improve .gitignore configuration
  ([ab0324e](https://github.com/mkm29/cve-report-aggregator/commit/ab0324e285d057376eeab69f2886dfc61934dc24))
- Update documentation links and improve .gitignore configuration
  ([a4c24a4](https://github.com/mkm29/cve-report-aggregator/commit/a4c24a4c698d623d8935a6b86680d98d86c1daf0))

### Code Refactoring

- Simplify Docker build workflow by removing unnecessary conditions and improving version handling
  ([6e8dc4f](https://github.com/mkm29/cve-report-aggregator/commit/6e8dc4f4785e6350529b379c1462736633a09efa))
- Simplify Docker build workflow by removing unnecessary conditions and improving version handling
  ([be41e7e](https://github.com/mkm29/cve-report-aggregator/commit/be41e7efb8b56cf563db262182440e8b3ec56af1))

## [0.2.0](https://github.com/mkm29/cve-report-aggregator/compare/v0.1.0...v0.2.0) (2025-10-18)

### Features

- Add branch protection and CI workflows for Git Flow
  ([5db7c5d](https://github.com/mkm29/cve-report-aggregator/commit/5db7c5d00712764959632d9105aaecc747977351))
- Add branch protection and CI workflows for Git Flow
  ([bc7ac6a](https://github.com/mkm29/cve-report-aggregator/commit/bc7ac6a67c81fcab33b7d1523d7578df33cb9583))
- Add Codecov token and slug for unit test coverage uploads
  ([8ed43cc](https://github.com/mkm29/cve-report-aggregator/commit/8ed43cc52a35f4c7ce987a00751ed4d1f2ec78b6))
- Add comprehensive unit tests
  ([29e44da](https://github.com/mkm29/cve-report-aggregator/commit/29e44dab24b1748166b14ba12836f1f4c534702b))
- add Dockerfile and update README with Docker usage instructions
  ([9b5208a](https://github.com/mkm29/cve-report-aggregator/commit/9b5208a54658f649f23d90bb9e0e888968be237b))
- add Dockerfile and update README with Docker usage instructions
  ([63a18f2](https://github.com/mkm29/cve-report-aggregator/commit/63a18f282333153a39d0528d4c16eb6d71b71ad4))
- add highest severity selection for vulnerability deduplication
  ([745c231](https://github.com/mkm29/cve-report-aggregator/commit/745c2313e26f18b30652095feb5cfeff29b27035))
- add highest severity selection for vulnerability deduplication
  ([896053c](https://github.com/mkm29/cve-report-aggregator/commit/896053ca88df1626108862a8012b438a84bb869f))
- add scanner source tracking and update CLI options for highest score selection
  ([276f96e](https://github.com/mkm29/cve-report-aggregator/commit/276f96eb45d2abbcd652b2ee9203aa3b29e8d4b8))
- add scanner source tracking and update CLI options for highest score selection
  ([8620258](https://github.com/mkm29/cve-report-aggregator/commit/862025857fd7a1601d09ff8ba6db0d0a5dc8836f))
- Add unit and integration tests for vulnerability deduplication and severity scoring
  ([7e2b3dc](https://github.com/mkm29/cve-report-aggregator/commit/7e2b3dcfdbdb569f9bf2088077f12c41dacf4de6))
- configured pyproject.toml to use utils module
  ([18ed577](https://github.com/mkm29/cve-report-aggregator/commit/18ed577617a5cb193b240ee2314ccfc2eeb4bd01))
- configured pyproject.toml to use utils module
  ([8041b2f](https://github.com/mkm29/cve-report-aggregator/commit/8041b2fb5604a3bbb7ec4ad5ad2deeadad2be4f9))
- implement Docker credentials management and SOPS encryption support
  ([93fb183](https://github.com/mkm29/cve-report-aggregator/commit/93fb1837526bb9637a70ad58843e65dad6a993e8))
- implement Docker credentials management and SOPS encryption support
  ([6c20a1c](https://github.com/mkm29/cve-report-aggregator/commit/6c20a1c6a5a6750bb19394af10479db83e87a4be))

### Bug Fixes

- add contributing doc
  ([ca44c02](https://github.com/mkm29/cve-report-aggregator/commit/ca44c026a818d610c78ba9fe36acc1c68264fa7f))
- Enhance Dockerfile credential handling with fallback for missing secrets
  ([e2b0858](https://github.com/mkm29/cve-report-aggregator/commit/e2b0858a9bf0323cc0d6f51ee9af57039ce48b33))
- Enhance Dockerfile credential handling with fallback for missing secrets
  ([4dfcc58](https://github.com/mkm29/cve-report-aggregator/commit/4dfcc588f376a76fb2d1a713d3577972829e8bbd))
- Remove commented environment section from release workflow
  ([3bdbef1](https://github.com/mkm29/cve-report-aggregator/commit/3bdbef14a28508129ec48ed27311bf4583dd404d))
- Remove push trigger from Docker build workflow and refine versio…
  ([d948616](https://github.com/mkm29/cve-report-aggregator/commit/d94861645929706f78b1fc3ac049ebfb3265be8c))
- Remove push trigger from Docker build workflow and refine versioning logic for merged PRs
  ([bbbd140](https://github.com/mkm29/cve-report-aggregator/commit/bbbd140f12312b1fbed1bf8877c0162cb9bc5d84))
- tighten docker build workflow
  ([08b2540](https://github.com/mkm29/cve-report-aggregator/commit/08b25403c77b059f833e8e6a7b146bcbcd1316bb))
- Update conditions for Docker build job execution
  ([e049adf](https://github.com/mkm29/cve-report-aggregator/commit/e049adf0879b44279d205229e199877e215d7bd2))
- Update Docker build context and file path for image build
  ([a5a9049](https://github.com/mkm29/cve-report-aggregator/commit/a5a9049ededff89b62a345fcebc03cf03ca600ce))
- Update Docker build context and file path for image build
  ([056c010](https://github.com/mkm29/cve-report-aggregator/commit/056c0108046b533b36ab3b26ba6df9b19e7e2c3f))
- update logo image in README and add new logo file
  ([1a42b79](https://github.com/mkm29/cve-report-aggregator/commit/1a42b796e5e988079340541cc58f7ace284b0c4b))
- update logo image in README and replace old logo file
  ([fc3f532](https://github.com/mkm29/cve-report-aggregator/commit/fc3f53266fa329d23c301bf1c250742161f3e598))

### Documentation

- Update README to include additional badges for Python version, PyPI, CI, and Docker
  ([8f414a6](https://github.com/mkm29/cve-report-aggregator/commit/8f414a623dbdcf36d655b0a83c2b100c7e93cb94))
- Update README to include badges
  ([6872952](https://github.com/mkm29/cve-report-aggregator/commit/6872952b98c0ea653ed7ac29c86e3c7023d7f9b6))

### Code Refactoring

- add type annotations for improved type safety and clarity
  ([8d95f87](https://github.com/mkm29/cve-report-aggregator/commit/8d95f8765a0dbdd556c9ce314363e148e92a4bec))
- add type annotations for improved type safety and clarity
  ([3fb6bf1](https://github.com/mkm29/cve-report-aggregator/commit/3fb6bf1ea0810fa70adc38d9058bcef73aea1953))
- Clean up test files by removing unused imports and improving docstrings
  ([de32773](https://github.com/mkm29/cve-report-aggregator/commit/de32773f41b8cebfc7f9ca0ab54e5dd379273506))
- modify code structure for improved readability and maintainability
  ([bd0a813](https://github.com/mkm29/cve-report-aggregator/commit/bd0a813e84d64e1303a2359a31e7d03f2f036607))
- Remove disk space checks and cleanup steps from Docker build workflow
  ([bf4aa6f](https://github.com/mkm29/cve-report-aggregator/commit/bf4aa6f3a707fb44e395b84d95102ad1ef60607e))
- Remove disk space checks and cleanup steps from Docker build workflow
  ([8eb4d3b](https://github.com/mkm29/cve-report-aggregator/commit/8eb4d3b422d998a9dd904b6001da9db77caedbaa))
- update CLI entry point to conditionally display logo based on version flag
  ([c99ad17](https://github.com/mkm29/cve-report-aggregator/commit/c99ad17bb838d95b7112f67b6bf295a8199f296c))

### Miscellaneous Chores

- merge develop branch into main
  ([2316963](https://github.com/mkm29/cve-report-aggregator/commit/2316963e204977416f33b0a367c336e7142aba1b))
- removed background from logo and filled in Doug
  ([781f3af](https://github.com/mkm29/cve-report-aggregator/commit/781f3afb889600602ab0f978a8a1544ee5b39e9f))

## [Unreleased]

### Added

- Docker credentials management with two methods: build-time secrets and environment variables
- SOPS encryption support for credentials file (`docker/config.json`)
- Docker BuildKit secret mount for secure credential injection during build
- Entrypoint script with dual authentication support (config.json or env vars)
- Security best practices documentation for credential management
- `.sops.yaml` configuration for encrypting credentials with age key
- Multi-stage Docker build with Alpine Linux base
- Non-root user (cve-aggregator, UID 1001) for container security
- Pre-installed scanning tools in Docker image: Grype, Syft, Trivy, UDS CLI
- Rich terminal output with color-coded tables and progress indicators
- Multi-scanner support (Grype and Trivy)
- SBOM auto-detection and scanning with Grype
- Automatic conversion of Grype reports to CycloneDX format for Trivy
- CVE deduplication across multiple scan reports
- Automatic null CVSS filtering (removes invalid scores)
- CVSS 3.x-based severity selection with `--mode highest-score`
- Scanner source tracking to identify which scanner provided vulnerability data
- Occurrence tracking to count CVE appearances across images
- Click-based CLI with rich-click styling
- Comprehensive test suite with pytest
- Type annotations throughout codebase
- Package installation via pip/pipx
- Docker Compose support

### Changed

- Consolidated Docker credentials documentation into main README.md
- Updated credentials file format to JSON with `username`, `password`, and `registry` fields
- Removed volume mount references from documentation (focus on credential management)
- Simplified credential methods from 4 to 2 (build-time secrets and environment variables)
- Registry is now configurable via credentials file instead of hardcoded

### Removed

- Separate `docker/README.md` file (merged into main README)
- Docker Secrets method (Docker Swarm/Compose secrets)
- Volume-mounted credentials file method
- Support for multiple credential file locations

### Security

- Credentials must be encrypted with SOPS before committing to version control
- Decrypted credential files (\*.dec) are automatically cleaned up after build
- Build-time secrets never appear in Docker image layers
- Container runs as non-root user (UID 1001)
- System pip removed from final image to reduce attack surface
- All dependencies pinned to specific versions in Dockerfile

## [0.1.0] - 2025-01-17

### Added

- Initial release of CVE Report Aggregator
- Basic Grype report aggregation and deduplication
- Command-line interface with Click
- JSON output format with metadata, summary, and vulnerabilities
- Docker support with Dockerfile and docker-compose.yml
- MIT License
- README with usage examples and installation instructions

[0.1.0]: https://github.com/mkm29/cve-report-aggregator/releases/tag/v0.1.0
[unreleased]: https://github.com/mkm29/cve-report-aggregator/compare/v0.1.0...HEAD
