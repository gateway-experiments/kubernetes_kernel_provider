"""Provides support for launching and managing kernels within a Kubernetes cluster."""

import os

from jupyter_kernel_mgmt.discovery import KernelProviderBase, KernelSpec
from jupyter_kernel_mgmt.kernelspec import NoSuchKernel
from jupyter_core.paths import jupyter_path
from remote_kernel_provider import RemoteKernelProviderBase
from traitlets.log import get_logger as get_app_logger

try:
    from json import JSONDecodeError
except ImportError:
    # JSONDecodeError is new in Python 3.5, so while we support 3.4:
    JSONDecodeError = ValueError

log = get_app_logger()  # We should always be run within an application


class KubernetesKernelProvider(RemoteKernelProviderBase):
    id = 'k8s'
    kernels_dir = 'kubernetes_kernels'
    actual_process_class = 'kubernetes_kernel_provider.k8s.KubernetesProcessProxy'
    supported_process_classes = [
        'enterprise_gateway.services.processproxies.k8s.KubernetesProcessProxy',
        actual_process_class
    ]
