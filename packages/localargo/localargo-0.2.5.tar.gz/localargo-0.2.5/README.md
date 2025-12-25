# localargo

[![PyPI - Version](https://img.shields.io/pypi/v/localargo.svg)](https://pypi.org/project/localargo)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/localargo.svg)](https://pypi.org/project/localargo)

**Convenient ArgoCD local development tool**

Localargo is a command-line tool that makes ArgoCD development workflows faster and more convenient. It provides streamlined commands for managing local clusters, applications, secrets, port forwarding, and debugging - all designed specifically for ArgoCD development.

## Features

- **Cluster Management**: Initialize, manage, and switch between Kubernetes clusters
- **Application Management**: Create, sync, and manage ArgoCD applications
- **Port Forwarding**: Easily access services running in your applications
- **Secrets Management**: Create and manage secrets for local development
- **Sync Operations**: Sync applications with watch mode for continuous development
- **Templates**: Quick-start applications from common templates
- **Debug Tools**: Comprehensive debugging and troubleshooting utilities
- **Validation**: Validate configurations before deployment

## Quick Start

```bash
# Install localargo
pip install localargo

# Initialize a local cluster with ArgoCD (uses KinD by default)
localargo cluster init

# Bring up cluster, configure ArgoCD, apply secrets, deploy apps
localargo up

# Create an application from a template
localargo template create my-app --repo https://github.com/myorg/myrepo

# Port forward services for easy access
localargo port-forward start my-service

# Sync and watch for changes
localargo sync --app my-app --watch
```

## Available Commands

Localargo provides the following main commands:

- **`cluster`**: Manage Kubernetes clusters for ArgoCD development
  - `init`: Initialize a local cluster with ArgoCD
  - `status`: Show cluster and ArgoCD status
  - `list`: List available clusters
  - `switch`: Switch Kubernetes contexts
  - `delete`: Delete clusters
  - `password`: Get ArgoCD admin password

- **`up`**: Bring up cluster, configure ArgoCD, apply secrets, deploy apps

- **`app`**: Manage ArgoCD applications
  - `deploy`: Create/update and sync applications
  - `sync`: Sync applications
  - `status`: Show application status
  - `logs`: Tail application logs
  - `list`: List applications
  - `delete`: Delete applications

- **`sync`**: Sync ArgoCD applications or local directories (with watch mode)

- **`template`**: Create ArgoCD applications from templates
  - `create`: Create application from template
  - `list-templates`: List available templates
  - `show`: Show template details

- **`port-forward`**: Manage port forwarding for applications
  - `start`: Start port forwarding for a service
  - `app`: Port forward all services in an application
  - `list-forwards`: List active forwards
  - `stop`: Stop port forwarding

- **`secrets`**: Manage secrets for local development

- **`debug`**: Debugging and troubleshooting tools
  - `validate`: Validate application configuration
  - `logs`: Show ArgoCD application logs
  - `events`: Show Kubernetes events

- **`validate`**: Validate manifest and show execution plan

- **`down`**: Tear down cluster

- **`ca`**: Manage CA certificates and TLS infrastructure
  - `status`: Show CA infrastructure status

## Table of Contents

- [Installation](#installation)
- [Manifest Configuration](#manifest-configuration)
- [Documentation](#documentation)
- [License](#license)

## Installation

```console
pip install localargo
```

### Development Setup

For contributors and development, we recommend using [Mise](https://mise.jdx.dev/) to set up the complete development environment:

```bash
# Install Mise (macOS with Homebrew)
brew install mise

# Install all development tools
mise install

# Create Hatch environment
hatch env create

# All tools will be automatically available
```

### Git Hook Setup

To ensure code quality before every commit, enable the mise-managed pre-commit hook:

```bash
mise generate git-pre-commit --write --task=precommit
```

This creates `.git/hooks/pre-commit`, which automatically runs:

- `hatch fmt`
- `hatch run typecheck`
- `hatch run test`

If any step fails, the commit will be blocked until fixed.

You can also run it manually at any time:

```bash
mise run precommit
```

### Optional Dependencies

For file watching functionality:
```console
pip install localargo[watch]
```

## Manifest Configuration

Localargo uses a `localargo.yaml` manifest file to declaratively configure your local development environment.

### Basic Structure

```yaml
cluster:
  - name: my-cluster
    provider: kind  # or k3s

ingress:
  namespace: ingress-nginx
  secretName: localargo-ca-cert
  secretKey: crt
  coreDnsRewrite:
    enabled: true          # default: true
    domains:
      - localtest.me       # default: ["localtest.me"]

apps:
  - my-app:
      namespace: my-namespace
      app_file: app.yaml

repo_creds:
  - github:
      repoURL: https://github.com/myorg
      username: git
      password: ${GITHUB_TOKEN}

secrets:
  - db_password:
      namespace: my-namespace
      secretName: my-secrets
      secretKey: db-password
      secretValue:
        - fromEnv: DATABASE_PASSWORD
```

### Ingress Configuration

The `ingress` section configures the nginx ingress controller and related settings:

- **`coreDnsRewrite`**: Automatically configures CoreDNS to rewrite `*.localtest.me` queries to the ingress-nginx service. This allows pods inside the cluster to resolve ingress hostnames (which normally resolve to `127.0.0.1` externally). Enabled by default—no `hostAliases` hacks needed!

### Automatic CA Certificate Distribution

Localargo automatically distributes the CA certificate secret to all app namespaces during `localargo up`. This enables applications to trust the local dev CA for TLS connections (e.g., OIDC callbacks to identity providers like Keycloak).

For each app defined in your manifest:

```yaml
apps:
  - bookstack:
      namespace: bookstack
      app_file: apps/bookstack.yaml
  - keycloak:
      namespace: keycloak
      app_file: apps/keycloak.yaml
```

Localargo will automatically copy the `localargo-ca-cert` secret from the `ingress-nginx` namespace to each app's namespace (`bookstack`, `keycloak`, etc.). This means:

- **Zero manual steps**: No need to manually copy secrets between namespaces
- **Declarative**: CA distribution is automatic based on your apps configuration
- **Survives cluster recreation**: Works every time you run `localargo up`
- **Idempotent**: Skips namespaces that already have the secret

Applications can then mount the CA certificate to trust the local TLS certificates:

```yaml
volumes:
  - name: localargo-ca
    secret:
      secretName: localargo-ca-cert
volumeMounts:
  - name: localargo-ca
    mountPath: /etc/ssl/certs/localargo-ca.crt
    subPath: crt
```

### Secrets Configuration

The `secrets` section allows you to declaratively define Kubernetes secrets. Each secret entry specifies where the secret value comes from.

#### From Environment Variables

Source secret values from environment variables:

```yaml
secrets:
  - api_key:
      namespace: core
      secretName: app-secrets
      secretKey: api-key
      secretValue:
        - fromEnv: API_KEY
```

#### Random Base64 Values

Generate cryptographically secure random bytes encoded as base64. The number specifies the byte count (not the output string length):

```yaml
secrets:
  - encryption_key:
      namespace: core
      secretName: crypto-secrets
      secretKey: encryption-key
      secretValue:
        - randomBase64: 32  # 32 bytes -> 44 character base64 string
```

#### Random Hex Values

Generate cryptographically secure random bytes encoded as lowercase hexadecimal. The number specifies the byte count:

```yaml
secrets:
  - session_id:
      namespace: core
      secretName: session-secrets
      secretKey: session-id
      secretValue:
        - randomHex: 16  # 16 bytes -> 32 character hex string
```

#### Static Values

Use a literal string value directly:

```yaml
secrets:
  - api_endpoint:
      namespace: core
      secretName: config
      secretKey: endpoint
      secretValue:
        - staticValue: "https://api.example.com"
```

#### Copy from Another Secret (sameAs)

Copy a value from an existing Kubernetes secret. This is useful for sharing secrets between namespaces or reusing values:

```yaml
secrets:
  - copied_password:
      namespace: app-namespace
      secretName: app-secrets
      secretKey: db-password
      secretValue:
        - sameAs:
            namespace: source-namespace
            secretName: source-secret
            secretKey: password
```

> **Note:** `sameAs` secrets are processed after all other secrets, ensuring the source secret exists before copying. The source secret can be one created earlier in the same `localargo up` run or a pre-existing secret in the cluster.

#### Multiple Keys in One Secret

You can define multiple keys for the same secret by using separate entries with the same `secretName`. Localargo automatically merges them:

```yaml
secrets:
  - db_user:
      namespace: backend
      secretName: database-credentials
      secretKey: username
      secretValue:
        - staticValue: "admin"
  - db_pass:
      namespace: backend
      secretName: database-credentials
      secretKey: password
      secretValue:
        - fromEnv: DB_PASSWORD
  - db_host:
      namespace: backend
      secretName: database-credentials
      secretKey: host
      secretValue:
        - staticValue: "postgres.backend.svc"
```

This creates a single `database-credentials` secret with three keys: `username`, `password`, and `host`.

#### Complete Example

```yaml
secrets:
  # From environment variable
  - db_password:
      namespace: backend
      secretName: database-credentials
      secretKey: password
      secretValue:
        - fromEnv: DATABASE_PASSWORD

  # Random 256-bit encryption key (base64 encoded)
  - encryption_key:
      namespace: backend
      secretName: crypto-config
      secretKey: aes-key
      secretValue:
        - randomBase64: 32

  # Random session secret (hex encoded)
  - session_secret:
      namespace: backend
      secretName: session-config
      secretKey: secret
      secretValue:
        - randomHex: 64

  # Multiple keys in the same secret (separate entries, same secretName)
  - jwt_secret:
      namespace: backend
      secretName: auth-config
      secretKey: jwt-secret
      secretValue:
        - randomBase64: 64

  - refresh_token_secret:
      namespace: backend
      secretName: auth-config
      secretKey: refresh-secret
      secretValue:
        - randomBase64: 64
```

## Documentation

Full documentation is available at [docs/](docs/) and can be built locally using mdBook.

To build the documentation:

```console
# Install mdBook (if not already installed)
cargo install mdbook

# Build the docs
cd docs && mdbook build

# Or using Hatch
hatch run docs:build
```

## License

`localargo` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
