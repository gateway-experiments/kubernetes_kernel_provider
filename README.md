# Kubernetes Kernel Provider
The Kubernetes Kernel Provider package provides support necessary for launching and managing Jupyter kernels within Kuberenetes clusters.  This is accomplished via two classes:

1. [`KubenetesKernelProvider`](https://github.com/gateway-experiments/kubernetes_kernel_provider/blob/master/kubernetes_kernel_provider/provider.py) is invoked by the application to locate and identify specific kernel specificiations (kernelspecs) that manage kernel lifecycles within a Kubernetes cluster.
2. [`KubernetesProcessProxy`](https://github.com/gateway-experiments/kubernetes_kernel_provider/blob/master/kubernetes_kernel_provider/k8s.py) is instantiated by the [`RemoteKernelManager`](https://github.com/gateway-experiments/remote_kernel_provider/blob/master/remote_kernel_provider/manager.py) to peform the kernel lifecycle management.  It performs post-launch discovery of the kernel pod and handles its termination via the [kubenetes-client](https://github.com/kubernetes-client/python) python API.

## Installation
`KubernetesKernelProvider` is a pip-installable package:
```bash
pip install kubenetes_kernel_provider
```

## Kubernetes Kernel Specifications
Criteria for discovery of the kernel specification via the `KubernetesKernelProvider` is that a `kernel.json` file exist in a sub-directory of `kubernetes_kernels`.  
