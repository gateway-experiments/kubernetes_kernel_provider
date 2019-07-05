"""Provides support for launching and managing kernels within a Kubernetes cluster."""

from remote_kernel_provider import RemoteKernelProviderBase


class KubernetesKernelProvider(RemoteKernelProviderBase):
    id = 'k8s'
    kernel_file = 'k8s_kernel.json'
    lifecycle_manager_classes = ['kubernetes_kernel_provider.k8s.KubernetesKernelLifecycleManager']
