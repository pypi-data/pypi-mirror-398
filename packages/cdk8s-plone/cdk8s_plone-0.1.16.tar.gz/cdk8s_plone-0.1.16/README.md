# CDK8S Plone

> TypeScript and Python library for deploying Plone CMS to Kubernetes using CDK8S

[![npm version](https://badge.fury.io/js/%40bluedynamics%2Fcdk8s-plone.svg)](https://www.npmjs.com/package/@bluedynamics/cdk8s-plone)
[![PyPI version](https://badge.fury.io/py/cdk8s-plone.svg)](https://pypi.org/project/cdk8s-plone/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

## Overview

cdk8s-plone provides CDK8S constructs for deploying [Plone CMS](https://plone.org/) on Kubernetes. Define your infrastructure using TypeScript or Python and generate Kubernetes manifests automatically.

**Key Features:**

* 🚀 Supports Volto (modern React frontend) and Classic UI
* 📦 High availability with configurable replicas
* ⚡ Optional Varnish HTTP caching layer
* 🔧 Fine-grained resource and probe configuration
* 🌍 Multi-language support (TypeScript/JavaScript and Python)
* ✅ Type-safe infrastructure as code

## Quick Start

### Installation

**TypeScript/JavaScript:**

```bash
npm install @bluedynamics/cdk8s-plone
```

**Python:**

```bash
pip install cdk8s-plone
```

### Basic Example

```python
import { App, Chart } from 'cdk8s';
import { Plone, PloneVariant } from '@bluedynamics/cdk8s-plone';

const app = new App();
const chart = new Chart(app, 'PloneDeployment');

new Plone(chart, 'my-plone', {
  variant: PloneVariant.VOLTO,
  backend: {
    image: 'plone/plone-backend:6.1.3',
    replicas: 3,
  },
  frontend: {
    image: 'plone/plone-frontend:16.0.0',
    replicas: 2,
  },
});

app.synth();
```

Generate Kubernetes manifests:

```bash
cdk8s synth
kubectl apply -f dist/
```

## Documentation

**📚 Full documentation:** https://bluedynamics.github.io/cdk8s-plone/

* [Quick Start Tutorial](https://bluedynamics.github.io/cdk8s-plone/tutorials/01-quick-start.html)
* [Configuration Reference](https://bluedynamics.github.io/cdk8s-plone/reference/configuration-options.html)
* [Architecture Overview](https://bluedynamics.github.io/cdk8s-plone/explanation/architecture.html)
* [Complete API Documentation](./API.md)

## Examples

Complete working examples are available in the [`examples/`](examples/) directory:

* **[Production Volto](examples/production-volto/)** - Production-ready Plone 6 deployment with modern UI:

  * Volto frontend (React) + REST API backend
  * PostgreSQL with RelStorage (CloudNativePG or Bitnami)
  * Varnish HTTP caching with kube-httpcache
  * Ingress support (Traefik/Kong) with TLS
* **[Classic UI](examples/classic-ui/)** - Traditional Plone deployment with server-side rendering:

  * Classic UI (traditional Plone interface)
  * PostgreSQL with RelStorage (CloudNativePG or Bitnami)
  * Varnish HTTP caching with kube-httpcache
  * Ingress support (Traefik/Kong) with TLS
  * Simpler architecture (no separate frontend)

### Prometheus Metrics

Enable Prometheus ServiceMonitor for metrics collection (requires Prometheus Operator):

```python
new Plone(chart, 'my-plone', {
  backend: {
    servicemonitor: true,
    metricsPath: '/metrics',  // optional, defaults to '/metrics'
  },
  frontend: {
    servicemonitor: true,
    metricsPort: 9090,  // optional, defaults to service port
  },
});
```

**Note:** You must instrument your Plone backend/frontend to expose metrics at the configured endpoint. For Volto/Node.js frontends, consider using [prom-client](https://www.npmjs.com/package/prom-client) or [express-prometheus-middleware](https://www.npmjs.com/package/express-prometheus-middleware).

## Requirements

* **kubectl** - [Install kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl)
* **Node.js 16+** (for TypeScript/JavaScript) - [Install Node.js](https://nodejs.org/)
* **Python 3.8+** (for Python) - [Install Python](https://www.python.org/)
* **Kubernetes cluster** (local or cloud)

For detailed setup instructions, see [Setup Prerequisites](https://bluedynamics.github.io/cdk8s-plone/how-to/setup-prerequisites.html).

## Development

This project uses [Projen](https://projen.io/) for project management.

```bash
# Install dependencies
npm install

# Run tests
npm test

# Build
npm run build

# Update project configuration
# Edit .projenrc.ts, then run:
npx projen
```

For detailed development instructions, see [CONTRIBUTING.md](./CONTRIBUTING.md) (if available).

## Resources

* [CDK8S Documentation](https://cdk8s.io/)
* [Plone CMS](https://plone.org/)
* [kube-httpcache](https://github.com/mittwald/kube-httpcache) (for HTTP caching)
* [CloudNativePG](https://cloudnative-pg.io/) (for PostgreSQL management)

## License

[Apache 2.0](LICENSE)

## Maintainers

Maintained by [Blue Dynamics Alliance](https://github.com/bluedynamics)

**Author:** Jens W. Klein (jk@kleinundpartner.at)
