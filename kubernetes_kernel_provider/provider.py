"""Provides support for launching and managing kernels within a Kubernetes cluster."""

from remote_kernel_provider import RemoteKernelProviderBase


class KubernetesKernelProvider(RemoteKernelProviderBase):
    id = 'k8skp'
    kernel_file = 'k8skp_kernel.json'
    lifecycle_manager_classes = ['kubernetes_kernel_provider.k8s.KubernetesKernelLifecycleManager']
