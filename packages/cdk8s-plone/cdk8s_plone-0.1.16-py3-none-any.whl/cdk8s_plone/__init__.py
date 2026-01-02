r'''
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
'''
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

import abc
import builtins
import datetime
import enum
import typing

import jsii
import publication
import typing_extensions

import typeguard
from importlib.metadata import version as _metadata_package_version
TYPEGUARD_MAJOR_VERSION = int(_metadata_package_version('typeguard').split('.')[0])

def check_type(argname: str, value: object, expected_type: typing.Any) -> typing.Any:
    if TYPEGUARD_MAJOR_VERSION <= 2:
        return typeguard.check_type(argname=argname, value=value, expected_type=expected_type) # type:ignore
    else:
        if isinstance(value, jsii._reference_map.InterfaceDynamicProxy): # pyright: ignore [reportAttributeAccessIssue]
           pass
        else:
            if TYPEGUARD_MAJOR_VERSION == 3:
                typeguard.config.collection_check_strategy = typeguard.CollectionCheckStrategy.ALL_ITEMS # type:ignore
                typeguard.check_type(value=value, expected_type=expected_type) # type:ignore
            else:
                typeguard.check_type(value=value, expected_type=expected_type, collection_check_strategy=typeguard.CollectionCheckStrategy.ALL_ITEMS) # type:ignore

from ._jsii import *

import cdk8s_plus_30 as _cdk8s_plus_30_fa3b8a6f
import constructs as _constructs_77d1e7e8


class Plone(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@bluedynamics/cdk8s-plone.Plone",
):
    '''Plone construct for deploying Plone CMS to Kubernetes.

    This construct creates all necessary Kubernetes resources for running Plone:

    - Deployment(s) for backend (and optionally frontend)
    - Service(s) for network access
    - Optional PodDisruptionBudget for high availability

    Supports two deployment variants:

    - VOLTO: Modern React frontend with REST API backend (default)
    - CLASSICUI: Traditional server-side rendered Plone

    Example::

        new Plone(chart, 'my-plone', {
          variant: PloneVariant.VOLTO,
          backend: {
            image: 'plone/plone-backend:6.0.10',
            replicas: 3,
          },
          frontend: {
            image: 'plone/plone-frontend:16.0.0',
          },
        });
    '''

    def __init__(
        self,
        scope: "_constructs_77d1e7e8.Construct",
        id: builtins.str,
        *,
        backend: typing.Optional[typing.Union["PloneBaseOptions", typing.Dict[builtins.str, typing.Any]]] = None,
        frontend: typing.Optional[typing.Union["PloneBaseOptions", typing.Dict[builtins.str, typing.Any]]] = None,
        image_pull_secrets: typing.Optional[typing.Sequence[builtins.str]] = None,
        site_id: typing.Optional[builtins.str] = None,
        variant: typing.Optional["PloneVariant"] = None,
        version: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param backend: Backend (Plone API) configuration. Default: {} (uses default values from PloneBaseOptions)
        :param frontend: Frontend (Volto) configuration. Only used when variant is PloneVariant.VOLTO. Default: {} (uses default values from PloneBaseOptions)
        :param image_pull_secrets: Names of Kubernetes secrets to use for pulling private container images. These secrets must exist in the same namespace as the deployment. Default: [] (no image pull secrets)
        :param site_id: Plone site ID in the ZODB. This is used to construct the internal API path for Volto frontend. Default: 'Plone'
        :param variant: Plone deployment variant to use. Default: PloneVariant.VOLTO
        :param version: Version string for labeling the deployment. This is used in Kubernetes labels and doesn't affect the actual image versions. Default: 'undefined'
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__543cbcb1139deb4ce75315c33bb5ebd6fd98851d9416a0f8e2c5cd960899e686)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        options = PloneOptions(
            backend=backend,
            frontend=frontend,
            image_pull_secrets=image_pull_secrets,
            site_id=site_id,
            variant=variant,
            version=version,
        )

        jsii.create(self.__class__, self, [scope, id, options])

    @builtins.property
    @jsii.member(jsii_name="backendServiceName")
    def backend_service_name(self) -> builtins.str:
        '''Name of the backend Kubernetes service.

        Use this to reference the backend service from other constructs.
        '''
        return typing.cast(builtins.str, jsii.get(self, "backendServiceName"))

    @builtins.property
    @jsii.member(jsii_name="siteId")
    def site_id(self) -> builtins.str:
        '''The Plone site ID in ZODB.'''
        return typing.cast(builtins.str, jsii.get(self, "siteId"))

    @builtins.property
    @jsii.member(jsii_name="variant")
    def variant(self) -> "PloneVariant":
        '''The deployment variant being used (VOLTO or CLASSICUI).'''
        return typing.cast("PloneVariant", jsii.get(self, "variant"))

    @builtins.property
    @jsii.member(jsii_name="frontendServiceName")
    def frontend_service_name(self) -> typing.Optional[builtins.str]:
        '''Name of the frontend Kubernetes service.

        Only set when variant is VOLTO, otherwise undefined.
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "frontendServiceName"))


@jsii.data_type(
    jsii_type="@bluedynamics/cdk8s-plone.PloneBaseOptions",
    jsii_struct_bases=[],
    name_mapping={
        "annotations": "annotations",
        "environment": "environment",
        "image": "image",
        "image_pull_policy": "imagePullPolicy",
        "limit_cpu": "limitCpu",
        "limit_memory": "limitMemory",
        "liveness_enabled": "livenessEnabled",
        "liveness_failure_threshold": "livenessFailureThreshold",
        "liveness_initial_delay_seconds": "livenessInitialDelaySeconds",
        "liveness_period_seconds": "livenessPeriodSeconds",
        "liveness_success_threshold": "livenessSuccessThreshold",
        "liveness_timeout_seconds": "livenessTimeoutSeconds",
        "max_unavailable": "maxUnavailable",
        "metrics_path": "metricsPath",
        "metrics_port": "metricsPort",
        "min_available": "minAvailable",
        "pod_annotations": "podAnnotations",
        "readiness_enabled": "readinessEnabled",
        "readiness_failure_threshold": "readinessFailureThreshold",
        "readiness_initial_delay_seconds": "readinessInitialDelaySeconds",
        "readiness_period_seconds": "readinessPeriodSeconds",
        "readiness_success_threshold": "readinessSuccessThreshold",
        "readiness_timeout_seconds": "readinessTimeoutSeconds",
        "replicas": "replicas",
        "request_cpu": "requestCpu",
        "request_memory": "requestMemory",
        "service_annotations": "serviceAnnotations",
        "servicemonitor": "servicemonitor",
    },
)
class PloneBaseOptions:
    def __init__(
        self,
        *,
        annotations: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        environment: typing.Optional["_cdk8s_plus_30_fa3b8a6f.Env"] = None,
        image: typing.Optional[builtins.str] = None,
        image_pull_policy: typing.Optional[builtins.str] = None,
        limit_cpu: typing.Optional[builtins.str] = None,
        limit_memory: typing.Optional[builtins.str] = None,
        liveness_enabled: typing.Optional[builtins.bool] = None,
        liveness_failure_threshold: typing.Optional[jsii.Number] = None,
        liveness_initial_delay_seconds: typing.Optional[jsii.Number] = None,
        liveness_period_seconds: typing.Optional[jsii.Number] = None,
        liveness_success_threshold: typing.Optional[jsii.Number] = None,
        liveness_timeout_seconds: typing.Optional[jsii.Number] = None,
        max_unavailable: typing.Optional[typing.Union[builtins.str, jsii.Number]] = None,
        metrics_path: typing.Optional[builtins.str] = None,
        metrics_port: typing.Optional[typing.Union[builtins.str, jsii.Number]] = None,
        min_available: typing.Optional[typing.Union[builtins.str, jsii.Number]] = None,
        pod_annotations: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        readiness_enabled: typing.Optional[builtins.bool] = None,
        readiness_failure_threshold: typing.Optional[jsii.Number] = None,
        readiness_initial_delay_seconds: typing.Optional[jsii.Number] = None,
        readiness_period_seconds: typing.Optional[jsii.Number] = None,
        readiness_success_threshold: typing.Optional[jsii.Number] = None,
        readiness_timeout_seconds: typing.Optional[jsii.Number] = None,
        replicas: typing.Optional[jsii.Number] = None,
        request_cpu: typing.Optional[builtins.str] = None,
        request_memory: typing.Optional[builtins.str] = None,
        service_annotations: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        servicemonitor: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Base options for Plone backend or frontend configuration.

        These options control container image, replica count, resource limits,
        environment variables, and health probes.

        :param annotations: Annotations to add to the Deployment metadata. Default: - no additional annotations
        :param environment: Environment variables to set in the container. Use cdk8s-plus-30 Env class to define variables and sources. Default: - undefined (no additional environment variables)
        :param image: Container image to use for the deployment. Default: - 'plone/plone-backend:latest' for backend, 'plone/plone-frontend:latest' for frontend
        :param image_pull_policy: Image pull policy for the container. Default: 'IfNotPresent'
        :param limit_cpu: CPU limit for the container. Default: '500m' for both backend and frontend
        :param limit_memory: Memory limit for the container. Default: '512Mi' for backend, '1Gi' for frontend
        :param liveness_enabled: Enable liveness probe for the container. Liveness probes determine when to restart a container. Recommended: true for frontend, false for backend (Zope has its own recovery). Default: false
        :param liveness_failure_threshold: Minimum consecutive failures for the liveness probe to be considered failed. Default: 3
        :param liveness_initial_delay_seconds: Number of seconds after container start before liveness probe is initiated. Default: 30
        :param liveness_period_seconds: How often (in seconds) to perform the liveness probe. Default: 10
        :param liveness_success_threshold: Minimum consecutive successes for the liveness probe to be considered successful. Default: 1
        :param liveness_timeout_seconds: Number of seconds after which the liveness probe times out. Default: 5
        :param max_unavailable: Maximum number of pods that can be unavailable during updates. Can be an absolute number (e.g., 1) or a percentage (e.g., '50%'). Used in PodDisruptionBudget if specified. Default: - undefined (not set)
        :param metrics_path: Path to scrape metrics from. Only used when servicemonitor is enabled. Default: '/metrics'
        :param metrics_port: Port name or number to scrape metrics from. Only used when servicemonitor is enabled. Default: - uses the main service port
        :param min_available: Minimum number of pods that must be available during updates. Can be an absolute number (e.g., 1) or a percentage (e.g., '50%'). Used in PodDisruptionBudget if specified. Default: - undefined (not set)
        :param pod_annotations: Annotations to add to the Pod template metadata. Common for Prometheus, Istio, backup policies, etc. Default: - no additional annotations
        :param readiness_enabled: Enable readiness probe for the container. Readiness probes determine when a container is ready to accept traffic. Default: true
        :param readiness_failure_threshold: Minimum consecutive failures for the readiness probe to be considered failed. Default: 3
        :param readiness_initial_delay_seconds: Number of seconds after container start before readiness probe is initiated. Default: 10
        :param readiness_period_seconds: How often (in seconds) to perform the readiness probe. Default: 10
        :param readiness_success_threshold: Minimum consecutive successes for the readiness probe to be considered successful. Default: 1
        :param readiness_timeout_seconds: Number of seconds after which the readiness probe times out. Default: 15
        :param replicas: Number of pod replicas to run. Default: 2
        :param request_cpu: CPU request for the container. Default: '200m'
        :param request_memory: Memory request for the container. Default: '256Mi'
        :param service_annotations: Annotations to add to the Service metadata. Common for external-dns, load balancers, service mesh, etc. Default: - no additional annotations
        :param servicemonitor: Enable Prometheus ServiceMonitor for metrics collection. Requires Prometheus Operator to be installed in the cluster. When enabled, a ServiceMonitor resource will be created to scrape metrics. Default: false
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cd9cf17a63ac3f69f433db3caa859d98a750929386f09ada26dd0fd212b3ec78)
            check_type(argname="argument annotations", value=annotations, expected_type=type_hints["annotations"])
            check_type(argname="argument environment", value=environment, expected_type=type_hints["environment"])
            check_type(argname="argument image", value=image, expected_type=type_hints["image"])
            check_type(argname="argument image_pull_policy", value=image_pull_policy, expected_type=type_hints["image_pull_policy"])
            check_type(argname="argument limit_cpu", value=limit_cpu, expected_type=type_hints["limit_cpu"])
            check_type(argname="argument limit_memory", value=limit_memory, expected_type=type_hints["limit_memory"])
            check_type(argname="argument liveness_enabled", value=liveness_enabled, expected_type=type_hints["liveness_enabled"])
            check_type(argname="argument liveness_failure_threshold", value=liveness_failure_threshold, expected_type=type_hints["liveness_failure_threshold"])
            check_type(argname="argument liveness_initial_delay_seconds", value=liveness_initial_delay_seconds, expected_type=type_hints["liveness_initial_delay_seconds"])
            check_type(argname="argument liveness_period_seconds", value=liveness_period_seconds, expected_type=type_hints["liveness_period_seconds"])
            check_type(argname="argument liveness_success_threshold", value=liveness_success_threshold, expected_type=type_hints["liveness_success_threshold"])
            check_type(argname="argument liveness_timeout_seconds", value=liveness_timeout_seconds, expected_type=type_hints["liveness_timeout_seconds"])
            check_type(argname="argument max_unavailable", value=max_unavailable, expected_type=type_hints["max_unavailable"])
            check_type(argname="argument metrics_path", value=metrics_path, expected_type=type_hints["metrics_path"])
            check_type(argname="argument metrics_port", value=metrics_port, expected_type=type_hints["metrics_port"])
            check_type(argname="argument min_available", value=min_available, expected_type=type_hints["min_available"])
            check_type(argname="argument pod_annotations", value=pod_annotations, expected_type=type_hints["pod_annotations"])
            check_type(argname="argument readiness_enabled", value=readiness_enabled, expected_type=type_hints["readiness_enabled"])
            check_type(argname="argument readiness_failure_threshold", value=readiness_failure_threshold, expected_type=type_hints["readiness_failure_threshold"])
            check_type(argname="argument readiness_initial_delay_seconds", value=readiness_initial_delay_seconds, expected_type=type_hints["readiness_initial_delay_seconds"])
            check_type(argname="argument readiness_period_seconds", value=readiness_period_seconds, expected_type=type_hints["readiness_period_seconds"])
            check_type(argname="argument readiness_success_threshold", value=readiness_success_threshold, expected_type=type_hints["readiness_success_threshold"])
            check_type(argname="argument readiness_timeout_seconds", value=readiness_timeout_seconds, expected_type=type_hints["readiness_timeout_seconds"])
            check_type(argname="argument replicas", value=replicas, expected_type=type_hints["replicas"])
            check_type(argname="argument request_cpu", value=request_cpu, expected_type=type_hints["request_cpu"])
            check_type(argname="argument request_memory", value=request_memory, expected_type=type_hints["request_memory"])
            check_type(argname="argument service_annotations", value=service_annotations, expected_type=type_hints["service_annotations"])
            check_type(argname="argument servicemonitor", value=servicemonitor, expected_type=type_hints["servicemonitor"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if annotations is not None:
            self._values["annotations"] = annotations
        if environment is not None:
            self._values["environment"] = environment
        if image is not None:
            self._values["image"] = image
        if image_pull_policy is not None:
            self._values["image_pull_policy"] = image_pull_policy
        if limit_cpu is not None:
            self._values["limit_cpu"] = limit_cpu
        if limit_memory is not None:
            self._values["limit_memory"] = limit_memory
        if liveness_enabled is not None:
            self._values["liveness_enabled"] = liveness_enabled
        if liveness_failure_threshold is not None:
            self._values["liveness_failure_threshold"] = liveness_failure_threshold
        if liveness_initial_delay_seconds is not None:
            self._values["liveness_initial_delay_seconds"] = liveness_initial_delay_seconds
        if liveness_period_seconds is not None:
            self._values["liveness_period_seconds"] = liveness_period_seconds
        if liveness_success_threshold is not None:
            self._values["liveness_success_threshold"] = liveness_success_threshold
        if liveness_timeout_seconds is not None:
            self._values["liveness_timeout_seconds"] = liveness_timeout_seconds
        if max_unavailable is not None:
            self._values["max_unavailable"] = max_unavailable
        if metrics_path is not None:
            self._values["metrics_path"] = metrics_path
        if metrics_port is not None:
            self._values["metrics_port"] = metrics_port
        if min_available is not None:
            self._values["min_available"] = min_available
        if pod_annotations is not None:
            self._values["pod_annotations"] = pod_annotations
        if readiness_enabled is not None:
            self._values["readiness_enabled"] = readiness_enabled
        if readiness_failure_threshold is not None:
            self._values["readiness_failure_threshold"] = readiness_failure_threshold
        if readiness_initial_delay_seconds is not None:
            self._values["readiness_initial_delay_seconds"] = readiness_initial_delay_seconds
        if readiness_period_seconds is not None:
            self._values["readiness_period_seconds"] = readiness_period_seconds
        if readiness_success_threshold is not None:
            self._values["readiness_success_threshold"] = readiness_success_threshold
        if readiness_timeout_seconds is not None:
            self._values["readiness_timeout_seconds"] = readiness_timeout_seconds
        if replicas is not None:
            self._values["replicas"] = replicas
        if request_cpu is not None:
            self._values["request_cpu"] = request_cpu
        if request_memory is not None:
            self._values["request_memory"] = request_memory
        if service_annotations is not None:
            self._values["service_annotations"] = service_annotations
        if servicemonitor is not None:
            self._values["servicemonitor"] = servicemonitor

    @builtins.property
    def annotations(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Annotations to add to the Deployment metadata.

        :default: - no additional annotations

        Example::

            { 'deployment.kubernetes.io/revision': '1' }
        '''
        result = self._values.get("annotations")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def environment(self) -> typing.Optional["_cdk8s_plus_30_fa3b8a6f.Env"]:
        '''Environment variables to set in the container.

        Use cdk8s-plus-30 Env class to define variables and sources.

        :default: - undefined (no additional environment variables)
        '''
        result = self._values.get("environment")
        return typing.cast(typing.Optional["_cdk8s_plus_30_fa3b8a6f.Env"], result)

    @builtins.property
    def image(self) -> typing.Optional[builtins.str]:
        '''Container image to use for the deployment.

        :default: - 'plone/plone-backend:latest' for backend, 'plone/plone-frontend:latest' for frontend

        Example::

            'plone/plone-backend:6.0.10' or 'plone/plone-frontend:16.0.0'
        '''
        result = self._values.get("image")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def image_pull_policy(self) -> typing.Optional[builtins.str]:
        '''Image pull policy for the container.

        :default: 'IfNotPresent'
        '''
        result = self._values.get("image_pull_policy")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def limit_cpu(self) -> typing.Optional[builtins.str]:
        '''CPU limit for the container.

        :default: '500m' for both backend and frontend

        Example::

            '500m' or '1' or '2000m'
        '''
        result = self._values.get("limit_cpu")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def limit_memory(self) -> typing.Optional[builtins.str]:
        '''Memory limit for the container.

        :default: '512Mi' for backend, '1Gi' for frontend

        Example::

            '512Mi' or '1Gi'
        '''
        result = self._values.get("limit_memory")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def liveness_enabled(self) -> typing.Optional[builtins.bool]:
        '''Enable liveness probe for the container.

        Liveness probes determine when to restart a container.
        Recommended: true for frontend, false for backend (Zope has its own recovery).

        :default: false
        '''
        result = self._values.get("liveness_enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def liveness_failure_threshold(self) -> typing.Optional[jsii.Number]:
        '''Minimum consecutive failures for the liveness probe to be considered failed.

        :default: 3
        '''
        result = self._values.get("liveness_failure_threshold")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def liveness_initial_delay_seconds(self) -> typing.Optional[jsii.Number]:
        '''Number of seconds after container start before liveness probe is initiated.

        :default: 30
        '''
        result = self._values.get("liveness_initial_delay_seconds")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def liveness_period_seconds(self) -> typing.Optional[jsii.Number]:
        '''How often (in seconds) to perform the liveness probe.

        :default: 10
        '''
        result = self._values.get("liveness_period_seconds")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def liveness_success_threshold(self) -> typing.Optional[jsii.Number]:
        '''Minimum consecutive successes for the liveness probe to be considered successful.

        :default: 1
        '''
        result = self._values.get("liveness_success_threshold")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def liveness_timeout_seconds(self) -> typing.Optional[jsii.Number]:
        '''Number of seconds after which the liveness probe times out.

        :default: 5
        '''
        result = self._values.get("liveness_timeout_seconds")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def max_unavailable(
        self,
    ) -> typing.Optional[typing.Union[builtins.str, jsii.Number]]:
        '''Maximum number of pods that can be unavailable during updates.

        Can be an absolute number (e.g., 1) or a percentage (e.g., '50%').
        Used in PodDisruptionBudget if specified.

        :default: - undefined (not set)
        '''
        result = self._values.get("max_unavailable")
        return typing.cast(typing.Optional[typing.Union[builtins.str, jsii.Number]], result)

    @builtins.property
    def metrics_path(self) -> typing.Optional[builtins.str]:
        '''Path to scrape metrics from.

        Only used when servicemonitor is enabled.

        :default: '/metrics'
        '''
        result = self._values.get("metrics_path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def metrics_port(self) -> typing.Optional[typing.Union[builtins.str, jsii.Number]]:
        '''Port name or number to scrape metrics from.

        Only used when servicemonitor is enabled.

        :default: - uses the main service port
        '''
        result = self._values.get("metrics_port")
        return typing.cast(typing.Optional[typing.Union[builtins.str, jsii.Number]], result)

    @builtins.property
    def min_available(self) -> typing.Optional[typing.Union[builtins.str, jsii.Number]]:
        '''Minimum number of pods that must be available during updates.

        Can be an absolute number (e.g., 1) or a percentage (e.g., '50%').
        Used in PodDisruptionBudget if specified.

        :default: - undefined (not set)
        '''
        result = self._values.get("min_available")
        return typing.cast(typing.Optional[typing.Union[builtins.str, jsii.Number]], result)

    @builtins.property
    def pod_annotations(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Annotations to add to the Pod template metadata.

        Common for Prometheus, Istio, backup policies, etc.

        :default: - no additional annotations

        Example::

            { 'prometheus.io/scrape': 'true', 'prometheus.io/port': '8080' }
        '''
        result = self._values.get("pod_annotations")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def readiness_enabled(self) -> typing.Optional[builtins.bool]:
        '''Enable readiness probe for the container.

        Readiness probes determine when a container is ready to accept traffic.

        :default: true
        '''
        result = self._values.get("readiness_enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def readiness_failure_threshold(self) -> typing.Optional[jsii.Number]:
        '''Minimum consecutive failures for the readiness probe to be considered failed.

        :default: 3
        '''
        result = self._values.get("readiness_failure_threshold")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def readiness_initial_delay_seconds(self) -> typing.Optional[jsii.Number]:
        '''Number of seconds after container start before readiness probe is initiated.

        :default: 10
        '''
        result = self._values.get("readiness_initial_delay_seconds")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def readiness_period_seconds(self) -> typing.Optional[jsii.Number]:
        '''How often (in seconds) to perform the readiness probe.

        :default: 10
        '''
        result = self._values.get("readiness_period_seconds")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def readiness_success_threshold(self) -> typing.Optional[jsii.Number]:
        '''Minimum consecutive successes for the readiness probe to be considered successful.

        :default: 1
        '''
        result = self._values.get("readiness_success_threshold")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def readiness_timeout_seconds(self) -> typing.Optional[jsii.Number]:
        '''Number of seconds after which the readiness probe times out.

        :default: 15
        '''
        result = self._values.get("readiness_timeout_seconds")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def replicas(self) -> typing.Optional[jsii.Number]:
        '''Number of pod replicas to run.

        :default: 2
        '''
        result = self._values.get("replicas")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def request_cpu(self) -> typing.Optional[builtins.str]:
        '''CPU request for the container.

        :default: '200m'

        Example::

            '200m' or '0.5'
        '''
        result = self._values.get("request_cpu")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def request_memory(self) -> typing.Optional[builtins.str]:
        '''Memory request for the container.

        :default: '256Mi'

        Example::

            '256Mi' or '512Mi'
        '''
        result = self._values.get("request_memory")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def service_annotations(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Annotations to add to the Service metadata.

        Common for external-dns, load balancers, service mesh, etc.

        :default: - no additional annotations

        Example::

            { 'external-dns.alpha.kubernetes.io/hostname': 'plone.example.com' }
        '''
        result = self._values.get("service_annotations")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def servicemonitor(self) -> typing.Optional[builtins.bool]:
        '''Enable Prometheus ServiceMonitor for metrics collection.

        Requires Prometheus Operator to be installed in the cluster.
        When enabled, a ServiceMonitor resource will be created to scrape metrics.

        :default: false
        '''
        result = self._values.get("servicemonitor")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PloneBaseOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class PloneHttpcache(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@bluedynamics/cdk8s-plone.PloneHttpcache",
):
    '''PloneHttpcache construct for deploying Varnish HTTP caching layer.

    Uses the mittwald/kube-httpcache Helm chart to deploy Varnish as a
    caching proxy in front of Plone backend and/or frontend services.

    The cache automatically connects to the Plone services and provides
    HTTP cache invalidation capabilities.

    Example::

        const plone = new Plone(chart, 'plone');
        const cache = new PloneHttpcache(chart, 'cache', {
          plone: plone,
          existingSecret: 'varnish-secret',
        });
    '''

    def __init__(
        self,
        scope: "_constructs_77d1e7e8.Construct",
        id: builtins.str,
        *,
        plone: "Plone",
        app_version: typing.Optional[builtins.str] = None,
        chart_version: typing.Optional[builtins.str] = None,
        existing_secret: typing.Optional[builtins.str] = None,
        exporter_enabled: typing.Optional[builtins.bool] = None,
        limit_cpu: typing.Optional[builtins.str] = None,
        limit_memory: typing.Optional[builtins.str] = None,
        replicas: typing.Optional[jsii.Number] = None,
        request_cpu: typing.Optional[builtins.str] = None,
        request_memory: typing.Optional[builtins.str] = None,
        servicemonitor: typing.Optional[builtins.bool] = None,
        varnish_vcl: typing.Optional[builtins.str] = None,
        varnish_vcl_file: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param plone: The Plone construct to attach the HTTP cache to. The cache will automatically connect to the backend and frontend services.
        :param app_version: Version of the kube-httpcache Container Image to use. If not specified, the latest version from the repository will be used. Default: undefined (chartVersion = with each chart release there is an image release too )
        :param chart_version: Version of the kube-httpcache Helm chart to use. If not specified, the latest version from the repository will be used. Default: undefined (latest)
        :param existing_secret: Name of an existing Kubernetes secret containing Varnish admin credentials. The secret should be created separately in the same namespace. Default: - undefined (no existing secret)
        :param exporter_enabled: Enable the Prometheus exporter for Varnish metrics. When enabled, the exporter sidecar container will be deployed alongside Varnish. Default: true
        :param limit_cpu: CPU limit for Varnish pods. Default: '500m'
        :param limit_memory: Memory limit for Varnish pods. Default: '500Mi'
        :param replicas: Number of Varnish pod replicas to run. Default: 2
        :param request_cpu: CPU request for Varnish pods. Default: '100m'
        :param request_memory: Memory request for Varnish pods. Default: '100Mi'
        :param servicemonitor: Enable Prometheus ServiceMonitor for metrics collection. Requires Prometheus Operator to be installed in the cluster. Default: false
        :param varnish_vcl: Varnish VCL configuration as a string. If provided, this takes precedence over varnishVclFile. Default: - loaded from varnishVclFile or default config file
        :param varnish_vcl_file: Path to a Varnish VCL configuration file. If not provided, uses the default VCL file included in the library. Default: - uses default config/varnish.tpl.vcl
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f7f85fe682616b18a7851bccc28d7021f541060ebc9eba02965066fd28589e69)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        options = PloneHttpcacheOptions(
            plone=plone,
            app_version=app_version,
            chart_version=chart_version,
            existing_secret=existing_secret,
            exporter_enabled=exporter_enabled,
            limit_cpu=limit_cpu,
            limit_memory=limit_memory,
            replicas=replicas,
            request_cpu=request_cpu,
            request_memory=request_memory,
            servicemonitor=servicemonitor,
            varnish_vcl=varnish_vcl,
            varnish_vcl_file=varnish_vcl_file,
        )

        jsii.create(self.__class__, self, [scope, id, options])

    @builtins.property
    @jsii.member(jsii_name="httpcacheServiceName")
    def httpcache_service_name(self) -> builtins.str:
        '''Name of the Varnish service created by the Helm chart.

        Use this to reference the cache service from ingress or other constructs.
        '''
        return typing.cast(builtins.str, jsii.get(self, "httpcacheServiceName"))


@jsii.data_type(
    jsii_type="@bluedynamics/cdk8s-plone.PloneHttpcacheOptions",
    jsii_struct_bases=[],
    name_mapping={
        "plone": "plone",
        "app_version": "appVersion",
        "chart_version": "chartVersion",
        "existing_secret": "existingSecret",
        "exporter_enabled": "exporterEnabled",
        "limit_cpu": "limitCpu",
        "limit_memory": "limitMemory",
        "replicas": "replicas",
        "request_cpu": "requestCpu",
        "request_memory": "requestMemory",
        "servicemonitor": "servicemonitor",
        "varnish_vcl": "varnishVcl",
        "varnish_vcl_file": "varnishVclFile",
    },
)
class PloneHttpcacheOptions:
    def __init__(
        self,
        *,
        plone: "Plone",
        app_version: typing.Optional[builtins.str] = None,
        chart_version: typing.Optional[builtins.str] = None,
        existing_secret: typing.Optional[builtins.str] = None,
        exporter_enabled: typing.Optional[builtins.bool] = None,
        limit_cpu: typing.Optional[builtins.str] = None,
        limit_memory: typing.Optional[builtins.str] = None,
        replicas: typing.Optional[jsii.Number] = None,
        request_cpu: typing.Optional[builtins.str] = None,
        request_memory: typing.Optional[builtins.str] = None,
        servicemonitor: typing.Optional[builtins.bool] = None,
        varnish_vcl: typing.Optional[builtins.str] = None,
        varnish_vcl_file: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Configuration options for PloneHttpcache (Varnish caching layer).

        :param plone: The Plone construct to attach the HTTP cache to. The cache will automatically connect to the backend and frontend services.
        :param app_version: Version of the kube-httpcache Container Image to use. If not specified, the latest version from the repository will be used. Default: undefined (chartVersion = with each chart release there is an image release too )
        :param chart_version: Version of the kube-httpcache Helm chart to use. If not specified, the latest version from the repository will be used. Default: undefined (latest)
        :param existing_secret: Name of an existing Kubernetes secret containing Varnish admin credentials. The secret should be created separately in the same namespace. Default: - undefined (no existing secret)
        :param exporter_enabled: Enable the Prometheus exporter for Varnish metrics. When enabled, the exporter sidecar container will be deployed alongside Varnish. Default: true
        :param limit_cpu: CPU limit for Varnish pods. Default: '500m'
        :param limit_memory: Memory limit for Varnish pods. Default: '500Mi'
        :param replicas: Number of Varnish pod replicas to run. Default: 2
        :param request_cpu: CPU request for Varnish pods. Default: '100m'
        :param request_memory: Memory request for Varnish pods. Default: '100Mi'
        :param servicemonitor: Enable Prometheus ServiceMonitor for metrics collection. Requires Prometheus Operator to be installed in the cluster. Default: false
        :param varnish_vcl: Varnish VCL configuration as a string. If provided, this takes precedence over varnishVclFile. Default: - loaded from varnishVclFile or default config file
        :param varnish_vcl_file: Path to a Varnish VCL configuration file. If not provided, uses the default VCL file included in the library. Default: - uses default config/varnish.tpl.vcl
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0f974bf721e34d8993ba90020605bc5e09424793236af8b8c5a9bb9a63f1974a)
            check_type(argname="argument plone", value=plone, expected_type=type_hints["plone"])
            check_type(argname="argument app_version", value=app_version, expected_type=type_hints["app_version"])
            check_type(argname="argument chart_version", value=chart_version, expected_type=type_hints["chart_version"])
            check_type(argname="argument existing_secret", value=existing_secret, expected_type=type_hints["existing_secret"])
            check_type(argname="argument exporter_enabled", value=exporter_enabled, expected_type=type_hints["exporter_enabled"])
            check_type(argname="argument limit_cpu", value=limit_cpu, expected_type=type_hints["limit_cpu"])
            check_type(argname="argument limit_memory", value=limit_memory, expected_type=type_hints["limit_memory"])
            check_type(argname="argument replicas", value=replicas, expected_type=type_hints["replicas"])
            check_type(argname="argument request_cpu", value=request_cpu, expected_type=type_hints["request_cpu"])
            check_type(argname="argument request_memory", value=request_memory, expected_type=type_hints["request_memory"])
            check_type(argname="argument servicemonitor", value=servicemonitor, expected_type=type_hints["servicemonitor"])
            check_type(argname="argument varnish_vcl", value=varnish_vcl, expected_type=type_hints["varnish_vcl"])
            check_type(argname="argument varnish_vcl_file", value=varnish_vcl_file, expected_type=type_hints["varnish_vcl_file"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "plone": plone,
        }
        if app_version is not None:
            self._values["app_version"] = app_version
        if chart_version is not None:
            self._values["chart_version"] = chart_version
        if existing_secret is not None:
            self._values["existing_secret"] = existing_secret
        if exporter_enabled is not None:
            self._values["exporter_enabled"] = exporter_enabled
        if limit_cpu is not None:
            self._values["limit_cpu"] = limit_cpu
        if limit_memory is not None:
            self._values["limit_memory"] = limit_memory
        if replicas is not None:
            self._values["replicas"] = replicas
        if request_cpu is not None:
            self._values["request_cpu"] = request_cpu
        if request_memory is not None:
            self._values["request_memory"] = request_memory
        if servicemonitor is not None:
            self._values["servicemonitor"] = servicemonitor
        if varnish_vcl is not None:
            self._values["varnish_vcl"] = varnish_vcl
        if varnish_vcl_file is not None:
            self._values["varnish_vcl_file"] = varnish_vcl_file

    @builtins.property
    def plone(self) -> "Plone":
        '''The Plone construct to attach the HTTP cache to.

        The cache will automatically connect to the backend and frontend services.
        '''
        result = self._values.get("plone")
        assert result is not None, "Required property 'plone' is missing"
        return typing.cast("Plone", result)

    @builtins.property
    def app_version(self) -> typing.Optional[builtins.str]:
        '''Version of the kube-httpcache Container Image to use.

        If not specified, the latest version from the repository will be used.

        :default: undefined (chartVersion = with each chart release there is an image release too )
        '''
        result = self._values.get("app_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def chart_version(self) -> typing.Optional[builtins.str]:
        '''Version of the kube-httpcache Helm chart to use.

        If not specified, the latest version from the repository will be used.

        :default: undefined (latest)
        '''
        result = self._values.get("chart_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def existing_secret(self) -> typing.Optional[builtins.str]:
        '''Name of an existing Kubernetes secret containing Varnish admin credentials.

        The secret should be created separately in the same namespace.

        :default: - undefined (no existing secret)
        '''
        result = self._values.get("existing_secret")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def exporter_enabled(self) -> typing.Optional[builtins.bool]:
        '''Enable the Prometheus exporter for Varnish metrics.

        When enabled, the exporter sidecar container will be deployed alongside Varnish.

        :default: true
        '''
        result = self._values.get("exporter_enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def limit_cpu(self) -> typing.Optional[builtins.str]:
        '''CPU limit for Varnish pods.

        :default: '500m'
        '''
        result = self._values.get("limit_cpu")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def limit_memory(self) -> typing.Optional[builtins.str]:
        '''Memory limit for Varnish pods.

        :default: '500Mi'
        '''
        result = self._values.get("limit_memory")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def replicas(self) -> typing.Optional[jsii.Number]:
        '''Number of Varnish pod replicas to run.

        :default: 2
        '''
        result = self._values.get("replicas")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def request_cpu(self) -> typing.Optional[builtins.str]:
        '''CPU request for Varnish pods.

        :default: '100m'
        '''
        result = self._values.get("request_cpu")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def request_memory(self) -> typing.Optional[builtins.str]:
        '''Memory request for Varnish pods.

        :default: '100Mi'
        '''
        result = self._values.get("request_memory")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def servicemonitor(self) -> typing.Optional[builtins.bool]:
        '''Enable Prometheus ServiceMonitor for metrics collection.

        Requires Prometheus Operator to be installed in the cluster.

        :default: false
        '''
        result = self._values.get("servicemonitor")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def varnish_vcl(self) -> typing.Optional[builtins.str]:
        '''Varnish VCL configuration as a string.

        If provided, this takes precedence over varnishVclFile.

        :default: - loaded from varnishVclFile or default config file
        '''
        result = self._values.get("varnish_vcl")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def varnish_vcl_file(self) -> typing.Optional[builtins.str]:
        '''Path to a Varnish VCL configuration file.

        If not provided, uses the default VCL file included in the library.

        :default: - uses default config/varnish.tpl.vcl
        '''
        result = self._values.get("varnish_vcl_file")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PloneHttpcacheOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@bluedynamics/cdk8s-plone.PloneOptions",
    jsii_struct_bases=[],
    name_mapping={
        "backend": "backend",
        "frontend": "frontend",
        "image_pull_secrets": "imagePullSecrets",
        "site_id": "siteId",
        "variant": "variant",
        "version": "version",
    },
)
class PloneOptions:
    def __init__(
        self,
        *,
        backend: typing.Optional[typing.Union["PloneBaseOptions", typing.Dict[builtins.str, typing.Any]]] = None,
        frontend: typing.Optional[typing.Union["PloneBaseOptions", typing.Dict[builtins.str, typing.Any]]] = None,
        image_pull_secrets: typing.Optional[typing.Sequence[builtins.str]] = None,
        site_id: typing.Optional[builtins.str] = None,
        variant: typing.Optional["PloneVariant"] = None,
        version: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Main configuration options for Plone deployment.

        :param backend: Backend (Plone API) configuration. Default: {} (uses default values from PloneBaseOptions)
        :param frontend: Frontend (Volto) configuration. Only used when variant is PloneVariant.VOLTO. Default: {} (uses default values from PloneBaseOptions)
        :param image_pull_secrets: Names of Kubernetes secrets to use for pulling private container images. These secrets must exist in the same namespace as the deployment. Default: [] (no image pull secrets)
        :param site_id: Plone site ID in the ZODB. This is used to construct the internal API path for Volto frontend. Default: 'Plone'
        :param variant: Plone deployment variant to use. Default: PloneVariant.VOLTO
        :param version: Version string for labeling the deployment. This is used in Kubernetes labels and doesn't affect the actual image versions. Default: 'undefined'
        '''
        if isinstance(backend, dict):
            backend = PloneBaseOptions(**backend)
        if isinstance(frontend, dict):
            frontend = PloneBaseOptions(**frontend)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d92a415ce6a72ab45cd3d3e169acc7fc8156c275bc6268fa1eed4110e990c22a)
            check_type(argname="argument backend", value=backend, expected_type=type_hints["backend"])
            check_type(argname="argument frontend", value=frontend, expected_type=type_hints["frontend"])
            check_type(argname="argument image_pull_secrets", value=image_pull_secrets, expected_type=type_hints["image_pull_secrets"])
            check_type(argname="argument site_id", value=site_id, expected_type=type_hints["site_id"])
            check_type(argname="argument variant", value=variant, expected_type=type_hints["variant"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if backend is not None:
            self._values["backend"] = backend
        if frontend is not None:
            self._values["frontend"] = frontend
        if image_pull_secrets is not None:
            self._values["image_pull_secrets"] = image_pull_secrets
        if site_id is not None:
            self._values["site_id"] = site_id
        if variant is not None:
            self._values["variant"] = variant
        if version is not None:
            self._values["version"] = version

    @builtins.property
    def backend(self) -> typing.Optional["PloneBaseOptions"]:
        '''Backend (Plone API) configuration.

        :default: {} (uses default values from PloneBaseOptions)
        '''
        result = self._values.get("backend")
        return typing.cast(typing.Optional["PloneBaseOptions"], result)

    @builtins.property
    def frontend(self) -> typing.Optional["PloneBaseOptions"]:
        '''Frontend (Volto) configuration.

        Only used when variant is PloneVariant.VOLTO.

        :default: {} (uses default values from PloneBaseOptions)
        '''
        result = self._values.get("frontend")
        return typing.cast(typing.Optional["PloneBaseOptions"], result)

    @builtins.property
    def image_pull_secrets(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Names of Kubernetes secrets to use for pulling private container images.

        These secrets must exist in the same namespace as the deployment.

        :default: [] (no image pull secrets)

        Example::

            ['my-registry-secret']
        '''
        result = self._values.get("image_pull_secrets")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def site_id(self) -> typing.Optional[builtins.str]:
        '''Plone site ID in the ZODB.

        This is used to construct the internal API path for Volto frontend.

        :default: 'Plone'
        '''
        result = self._values.get("site_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def variant(self) -> typing.Optional["PloneVariant"]:
        '''Plone deployment variant to use.

        :default: PloneVariant.VOLTO
        '''
        result = self._values.get("variant")
        return typing.cast(typing.Optional["PloneVariant"], result)

    @builtins.property
    def version(self) -> typing.Optional[builtins.str]:
        '''Version string for labeling the deployment.

        This is used in Kubernetes labels and doesn't affect the actual image versions.

        :default: 'undefined'
        '''
        result = self._values.get("version")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PloneOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.enum(jsii_type="@bluedynamics/cdk8s-plone.PloneVariant")
class PloneVariant(enum.Enum):
    '''Plone deployment variants.'''

    VOLTO = "VOLTO"
    '''Volto variant: ReactJS frontend (Volto) with REST API backend.

    Deploys both frontend and backend services.
    '''
    CLASSICUI = "CLASSICUI"
    '''Classic UI variant: Traditional Plone with server-side rendering.

    Deploys only the backend service.
    '''


__all__ = [
    "Plone",
    "PloneBaseOptions",
    "PloneHttpcache",
    "PloneHttpcacheOptions",
    "PloneOptions",
    "PloneVariant",
]

publication.publish()

def _typecheckingstub__543cbcb1139deb4ce75315c33bb5ebd6fd98851d9416a0f8e2c5cd960899e686(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    backend: typing.Optional[typing.Union[PloneBaseOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    frontend: typing.Optional[typing.Union[PloneBaseOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    image_pull_secrets: typing.Optional[typing.Sequence[builtins.str]] = None,
    site_id: typing.Optional[builtins.str] = None,
    variant: typing.Optional[PloneVariant] = None,
    version: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cd9cf17a63ac3f69f433db3caa859d98a750929386f09ada26dd0fd212b3ec78(
    *,
    annotations: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    environment: typing.Optional[_cdk8s_plus_30_fa3b8a6f.Env] = None,
    image: typing.Optional[builtins.str] = None,
    image_pull_policy: typing.Optional[builtins.str] = None,
    limit_cpu: typing.Optional[builtins.str] = None,
    limit_memory: typing.Optional[builtins.str] = None,
    liveness_enabled: typing.Optional[builtins.bool] = None,
    liveness_failure_threshold: typing.Optional[jsii.Number] = None,
    liveness_initial_delay_seconds: typing.Optional[jsii.Number] = None,
    liveness_period_seconds: typing.Optional[jsii.Number] = None,
    liveness_success_threshold: typing.Optional[jsii.Number] = None,
    liveness_timeout_seconds: typing.Optional[jsii.Number] = None,
    max_unavailable: typing.Optional[typing.Union[builtins.str, jsii.Number]] = None,
    metrics_path: typing.Optional[builtins.str] = None,
    metrics_port: typing.Optional[typing.Union[builtins.str, jsii.Number]] = None,
    min_available: typing.Optional[typing.Union[builtins.str, jsii.Number]] = None,
    pod_annotations: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    readiness_enabled: typing.Optional[builtins.bool] = None,
    readiness_failure_threshold: typing.Optional[jsii.Number] = None,
    readiness_initial_delay_seconds: typing.Optional[jsii.Number] = None,
    readiness_period_seconds: typing.Optional[jsii.Number] = None,
    readiness_success_threshold: typing.Optional[jsii.Number] = None,
    readiness_timeout_seconds: typing.Optional[jsii.Number] = None,
    replicas: typing.Optional[jsii.Number] = None,
    request_cpu: typing.Optional[builtins.str] = None,
    request_memory: typing.Optional[builtins.str] = None,
    service_annotations: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    servicemonitor: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f7f85fe682616b18a7851bccc28d7021f541060ebc9eba02965066fd28589e69(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    plone: Plone,
    app_version: typing.Optional[builtins.str] = None,
    chart_version: typing.Optional[builtins.str] = None,
    existing_secret: typing.Optional[builtins.str] = None,
    exporter_enabled: typing.Optional[builtins.bool] = None,
    limit_cpu: typing.Optional[builtins.str] = None,
    limit_memory: typing.Optional[builtins.str] = None,
    replicas: typing.Optional[jsii.Number] = None,
    request_cpu: typing.Optional[builtins.str] = None,
    request_memory: typing.Optional[builtins.str] = None,
    servicemonitor: typing.Optional[builtins.bool] = None,
    varnish_vcl: typing.Optional[builtins.str] = None,
    varnish_vcl_file: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0f974bf721e34d8993ba90020605bc5e09424793236af8b8c5a9bb9a63f1974a(
    *,
    plone: Plone,
    app_version: typing.Optional[builtins.str] = None,
    chart_version: typing.Optional[builtins.str] = None,
    existing_secret: typing.Optional[builtins.str] = None,
    exporter_enabled: typing.Optional[builtins.bool] = None,
    limit_cpu: typing.Optional[builtins.str] = None,
    limit_memory: typing.Optional[builtins.str] = None,
    replicas: typing.Optional[jsii.Number] = None,
    request_cpu: typing.Optional[builtins.str] = None,
    request_memory: typing.Optional[builtins.str] = None,
    servicemonitor: typing.Optional[builtins.bool] = None,
    varnish_vcl: typing.Optional[builtins.str] = None,
    varnish_vcl_file: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d92a415ce6a72ab45cd3d3e169acc7fc8156c275bc6268fa1eed4110e990c22a(
    *,
    backend: typing.Optional[typing.Union[PloneBaseOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    frontend: typing.Optional[typing.Union[PloneBaseOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    image_pull_secrets: typing.Optional[typing.Sequence[builtins.str]] = None,
    site_id: typing.Optional[builtins.str] = None,
    variant: typing.Optional[PloneVariant] = None,
    version: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
