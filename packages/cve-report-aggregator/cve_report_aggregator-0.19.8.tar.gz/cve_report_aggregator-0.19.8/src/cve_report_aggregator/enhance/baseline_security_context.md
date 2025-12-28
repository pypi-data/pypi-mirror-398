# Baseline Security Context for CVE Mitigation Analysis

## Overview

This document provides a comprehensive security baseline for analyzing how UDS Core's security controls help mitigate
Common Vulnerabilities and Exposures (CVEs). This context should be used when querying AI systems to understand the
effectiveness of security measures against specific vulnerabilities.

## Network Policy Enforcement

### Policy Engine: Kubernetes NetworkPolicies (Managed by UDS Operator)

UDS Core implements a defense-in-depth network security strategy using Kubernetes NetworkPolicies that enforce
zero-trust networking principles. All network traffic is denied by default, with explicit allow rules for legitimate
communication paths.

### Network Policy Architecture

**Key Principles:**

- **Default Deny**: All namespaces have default deny policies for both ingress and egress traffic
- **Explicit Allow**: Only explicitly defined communication paths are permitted
- **Namespace Isolation**: Strong isolation between namespaces with controlled cross-namespace communication
- **Metadata Protection**: Special protections against cloud provider metadata endpoints (169.254.169.254/32)
- **Service Mesh Integration**: Policies work in conjunction with Istio service mesh for enhanced security

### Network Policy Categories

#### 1. Intra-Namespace Communication

- **Purpose**: Enable communication between pods within the same namespace
- **Scope**: Pod-to-pod communication within namespace boundaries
- **Security Benefit**: Prevents lateral movement between namespaces while allowing necessary local communication

**Example Policies:**

- `allow-authservice-egress-all-pods-intranamespace`
- `allow-authservice-ingress-all-pods-intranamespace`
- `allow-keycloak-egress-waypoint-to-keycloak`

#### 2. DNS Resolution

- **Purpose**: Allow DNS lookups via CoreDNS
- **Target**: CoreDNS pods in kube-system namespace (port 53/UDP)
- **Security Benefit**: Restricts DNS queries to trusted internal DNS infrastructure only

**Example Policies:**

- `allow-authservice-egress-dns-lookup-via-coredns`
- `allow-keycloak-egress-dns-lookup-via-coredns`

#### 3. Service Mesh Communication (Istio)

- **Purpose**: Enable secure service-to-service communication via Istio service mesh
- **Components**: Gateway ingress, waypoint proxies, control plane communication
- **Security Benefit**: Enforces mTLS, traffic encryption, and policy-driven routing

**Example Policies:**

- `allow-authservice-egress-sso-provider` - Routes to tenant ingress gateway
- `allow-keycloak-egress-waypoint-to-istio-control-plane` - Control plane connectivity (port 15012)
- `allow-keycloak-ingress-8080-keycloak-istio-admin-gateway` - Admin gateway access
- `allow-keycloak-ingress-8080-keycloak-istio-tenant-gateway` - Tenant gateway access

#### 4. Health Probes and Monitoring

- **Purpose**: Allow health checks and metrics collection
- **Sources**: Ambient mesh health probes (169.254.7.127/32), Prometheus monitoring
- **Security Benefit**: Enables observability without compromising security

**Example Policies:**

- `allow-authservice-ingress-ambient-healthprobes`
- `allow-keycloak-ingress-9000-http-keycloak-metrics` - Prometheus metrics (port 9000)
- `allow-keycloak-ingress-waypoint-health` - Waypoint health monitoring (port 15020)

#### 5. External Access (Controlled)

- **Purpose**: Allow controlled external communication for specific use cases
- **Constraints**:
  - Excludes cloud metadata endpoint (169.254.169.254/32) to prevent SSRF attacks
  - Typically restricted to HTTPS (443), HTTP (80), and service mesh ports (15008)
- **Security Benefit**: Prevents unauthorized external data exfiltration while allowing necessary external services

**Example Policies:**

- `allow-authservice-egress-redis-session-store` - Anywhere access with metadata exclusion
- `allow-keycloak-egress-ocsp-lookup` - OCSP validation via 80/443/15008

#### 6. Application-Specific Access

- **Purpose**: Enable specific application features with minimal permissions
- **Examples**: Backchannel communication, protected apps
- **Security Benefit**: Granular access control based on application requirements

**Example Policies:**

- `allow-authservice-ingress-protected-apps` - Specific ports (10003, 15008)
- `allow-keycloak-ingress-keycloak-backchannel-access` - Port 8080 from any namespace

### Network Policy Summary

**Total Policies Analyzed**: 20+ policies across authservice and keycloak namespaces

**Security Coverage:**

- Default deny all traffic (ingress + egress)
- DNS limited to CoreDNS in kube-system
- Cloud metadata endpoint blocked (CVE-2020-8554 protection)
- Istio service mesh integration with mTLS
- Namespace isolation with explicit cross-namespace rules
- Port-level granularity for all allowed traffic
- Pod selector restrictions for targeted policies
- Health probe and monitoring integration

## Custom Policy Engine: Pepr Policies

### Policy Engine: Pepr (TypeScript-based Kubernetes Admission Controller)

UDS Core uses Pepr, a TypeScript-based admission controller, to enforce security policies at pod admission time. These
policies are based on Big Bang's Kyverno policies and provide both **mutation** (automatic security hardening) and
**validation** (enforcement of security requirements).

### Policy Capabilities

**Mutations** (Automatic Security Hardening):

- Policies can automatically modify pod specifications to ensure security
- Applied before pods are created, ensuring compliance without manual intervention
- Can be exempted via UDS Exemption Custom Resources

**Validations** (Enforcement):

- Policies validate pod configurations against security requirements
- Reject non-compliant pods at admission time
- Ensure consistent security posture across the cluster

### Implemented Pepr Policy Categories

#### 1. Privilege Escalation Prevention (Severity: HIGH)

**Policy: DisallowPrivileged**

- **Mutation**: Sets `allowPrivilegeEscalation: false` unless container is privileged or has CAP_SYS_ADMIN
- **Validation**: Ensures `allowPrivilegeEscalation: false` and `privileged: false|undefined`
- **Security Benefit**: Prevents containers from gaining additional privileges at runtime
- **CVE Mitigation**: Blocks privilege escalation exploits (e.g., container breakout vulnerabilities)

#### 2. Non-Root User Enforcement (Severity: HIGH)

**Policy: RequireNonRootUser**

- **Mutation**:
  - Sets `runAsNonRoot: true`
  - Defaults to `runAsUser: 1000`, `runAsGroup: 1000`
  - Supports custom UIDs via `uds/user`, `uds/group`, `uds/fsgroup` labels
- **Validation**: Ensures `runAsNonRoot: true` OR `runAsUser > 0`
- **Security Benefit**: Prevents root-based exploits and privilege escalation
- **CVE Mitigation**: Limits impact of container escape vulnerabilities

#### 3. Capability Restrictions (Severity: MEDIUM-HIGH)

**Policy: DropAllCapabilities (Mutation + Validation)**

- **Mutation**: Sets `capabilities.drop: ["ALL"]` for all containers
- **Validation**: Verifies all containers explicitly drop all capabilities
- **Security Benefit**: Removes unnecessary Linux capabilities

**Policy: RestrictCapabilities (Validation)**

- **Validation**: Prevents adding capabilities beyond allowed list
- **Security Benefit**: Limits attack surface by restricting privileged operations
- **CVE Mitigation**: Reduces impact of kernel exploits requiring specific capabilities

#### 4. Host Namespace Protection (Severity: HIGH)

**Policy: DisallowHostNamespaces**

- **Validation**: Ensures `hostPID`, `hostIPC`, `hostNetwork` are false
- **Security Benefit**: Prevents access to host-level resources
- **CVE Mitigation**: Blocks container escape attacks via shared namespaces

**Policy: RestrictHostPorts**

- **Validation**: Restricts container `hostPort` to approved list
- **Security Benefit**: Prevents unauthorized network access and port conflicts
- **CVE Mitigation**: Reduces network-based attack surface

#### 5. SELinux and Seccomp Hardening (Severity: HIGH)

**Policy: DisallowSELinuxOptions**

- **Validation**: Prevents use of custom SELinux options
- **Security Benefit**: Prevents SELinux-based privilege escalation

**Policy: RestrictSELinuxType**

- **Validation**: Restricts SELinux type to allowed list
- **Security Benefit**: Enforces mandatory access control

**Policy: RestrictSeccomp**

- **Validation**: Ensures seccomp profile is `RuntimeDefault` or `Localhost` (not `Unconfined`)
- **Security Benefit**: Limits syscall access to reduce kernel attack surface
- **CVE Mitigation**: Blocks exploits requiring dangerous syscalls

**Policy: RestrictProcMount**

- **Validation**: Ensures `/proc` mount type is restricted to "Default"
- **Security Benefit**: Prevents exposure of sensitive kernel information

#### 6. Network Security Policies (Severity: MEDIUM-HIGH)

**Policy: DisallowNodePortServices**

- **Validation**: Prevents creation of NodePort services
- **Security Benefit**: NodePort bypasses NetworkPolicy controls
- **CVE Mitigation**: Prevents CVE-2020-8554 (MITM via service misconfiguration)

**Policy: RestrictExternalNames**

- **Validation**: Restricts Service externalNames to approved list
- **Security Benefit**: Prevents MITM attacks via DNS manipulation
- **CVE Mitigation**: Directly addresses CVE-2020-8554

#### 7. Storage Security (Severity: MEDIUM)

**Policy: RestrictVolumeTypes**

- **Validation**: Limits volume types to approved list (excludes hostPath by default)
- **Security Benefit**: Reduces CSI driver vulnerability exposure

**Policy: RestrictHostPathWrite**

- **Validation**: Ensures hostPath volumes (if allowed) are mounted read-only
- **Security Benefit**: Prevents host file system modification
- **CVE Mitigation**: Limits container escape via file system manipulation

#### 8. Istio Service Mesh Security (Severity: HIGH)

**Policy: RestrictIstioUser**

- **Validation**: Only Istio components can run as UID/GID 1337
- **Security Benefit**: Prevents privilege escalation via Istio proxy identity
- **CVE Mitigation**: Blocks unauthorized bypass of service mesh controls

**Policy: RestrictIstioSidecarOverrides**

- **Validation**: Blocks dangerous Istio sidecar annotations:
  - `sidecar.istio.io/bootstrapOverride`
  - `sidecar.istio.io/proxyImage`
  - `proxy.istio.io/config`
  - Custom volumes and discovery addresses
- **Security Benefit**: Prevents sidecar configuration manipulation
- **CVE Mitigation**: Blocks service mesh bypass and proxy replacement attacks

**Policy: RestrictIstioTrafficOverrides**

- **Validation**: Blocks traffic interception annotations/labels:
  - `sidecar.istio.io/inject` (disable injection)
  - Traffic exclusion annotations (ports, IPs, interfaces)
  - Interception mode overrides
- **Security Benefit**: Prevents traffic bypass and unauthorized network access
- **CVE Mitigation**: Enforces zero-trust networking via Istio

**Policy: RestrictIstioAmbientOverrides**

- **Validation**: Blocks `ambient.istio.io/bypass-inbound-capture`
- **Security Benefit**: Prevents bypass of ambient mesh traffic capture

### Pepr Policy Summary

**Total Implemented Policies**: 19 validations, 3 mutations

**Security Coverage:**

- Privilege escalation prevention (HIGH)
- Non-root user enforcement (HIGH)
- Capability restrictions (HIGH)
- Host namespace protection (HIGH)
- SELinux/Seccomp hardening (HIGH)
- Network service restrictions (MEDIUM)
- Storage security controls (MEDIUM)
- Istio service mesh security (HIGH)

## Combined Security Posture

### Defense-in-Depth Strategy

UDS Core implements multiple layers of security controls:

1. **Network Layer (NetworkPolicies)**

   - Zero-trust networking with default deny
   - Explicit allow rules for legitimate traffic
   - Cloud metadata endpoint protection
   - Service mesh integration (mTLS, encryption)

1. **Admission Control Layer (Pepr Policies)**

   - Automatic security hardening (mutations)
   - Enforcement of security requirements (validations)
   - Prevention of dangerous configurations
   - Istio service mesh security

1. **Runtime Security Layer**

   - Non-root container execution
   - Capability dropping
   - Seccomp/SELinux enforcement
   - Read-only file systems where possible

### CVE Mitigation Framework

When analyzing CVEs, consider how UDS Core's security controls provide protection:

**Network-Based Vulnerabilities:**

- NetworkPolicies restrict attack surface by limiting network access
- Istio service mesh provides mTLS and traffic encryption
- External access controls prevent data exfiltration
- Metadata endpoint protection prevents SSRF attacks

**Privilege Escalation Vulnerabilities:**

- Non-root user enforcement limits initial compromise impact
- Capability restrictions prevent kernel exploits
- Seccomp profiles limit syscall access
- SELinux provides mandatory access control

**Container Escape Vulnerabilities:**

- Host namespace isolation prevents escape paths
- Read-only file systems limit persistence mechanisms
- Volume type restrictions prevent host file system access
- Pepr mutations automatically harden pod configurations

**Service Mesh Vulnerabilities:**

- Istio user restrictions prevent proxy impersonation
- Sidecar configuration locks prevent bypass attacks
- Traffic interception enforcement ensures all traffic is captured

### Example CVE Analysis Template

When enriching CVEs with UDS Core security context, analyze:

1. **Attack Vector**: How does the vulnerability get exploited?
1. **Required Permissions**: What capabilities/privileges does the exploit need?
1. **Network Requirements**: Does the exploit require network access?
1. **Runtime Context**: What container runtime features does it leverage?

Then map to security controls:

- **NetworkPolicies**: Does default deny block the attack path?
- **Pepr Policies**: Do mutations/validations prevent the attack?
- **Service Mesh**: Does Istio provide additional protection?
- **Runtime Security**: Do seccomp/SELinux/capabilities block exploitation?

### Limitations and Gaps

**Known Limitations:**

- NetworkPolicies don't control pod-level egress to same-node destinations
- HostPort bypasses NetworkPolicy controls (mitigated by RestrictHostPorts)
- Some Big Bang policies not yet implemented in Pepr
- Container runtime vulnerabilities may bypass some controls

**Recommended Additional Controls:**

- Image scanning and vulnerability management (Grype/Trivy)
- Runtime security monitoring (Falco)
- Image signature verification (Cosign)
- Regular security patching and updates

## Conclusion

UDS Core provides a robust security baseline through:

- **25+ NetworkPolicies** enforcing zero-trust networking
- **19 Pepr validation policies** preventing insecure configurations
- **3 Pepr mutation policies** automatically hardening workloads
- **Istio service mesh** providing mTLS and traffic control

This defense-in-depth approach significantly reduces the attack surface and limits the impact of vulnerabilities. When
analyzing CVEs, consider how these controls intersect with the vulnerability's attack vector to determine residual risk.
