"""Provides support for launching and managing kernels within a Kubernetes cluster."""

from remote_kernel_provider import RemoteKernelProviderBase

class KubernetesKernelProvider(RemoteKernelProviderBase):
    id = 'k8s'
    kernels_file = 'k8s_kernel.json'
    actual_process_class = 'kubernetes_kernel_provider.k8s.KubernetesProcessProxy'
    supported_process_classes = [
        'enterprise_gateway.services.processproxies.k8s.KubernetesProcessProxy',
        actual_process_class
    ]
