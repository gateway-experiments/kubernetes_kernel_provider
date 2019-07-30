# Kubernetes Kernel Provider

__NOTE: This repository is experimental and undergoing frequent changes!__

The Kubernetes Kernel Provider package provides support necessary for launching and managing Jupyter kernels within Kuberenetes clusters.  This is accomplished via two classes:

1. [`KubenetesKernelProvider`](https://github.com/gateway-experiments/kubernetes_kernel_provider/blob/master/kubernetes_kernel_provider/provider.py) is invoked by the application to locate and identify specific kernel specificiations (kernelspecs) that manage kernel lifecycles within a Kubernetes cluster.
2. [`KubernetesKernelLifecycleManager`](https://github.com/gateway-experiments/kubernetes_kernel_provider/blob/master/kubernetes_kernel_provider/k8s.py) is instantiated by the [`RemoteKernelManager`](https://github.com/gateway-experiments/remote_kernel_provider/blob/master/remote_kernel_provider/manager.py) to peform the kernel lifecycle management.  It performs post-launch discovery of the kernel pod and handles its termination via the [kubenetes-client](https://github.com/kubernetes-client/python) python API.

## Installation
`KubernetesKernelProvider` is a pip-installable package:
```bash
pip install kubenetes_kernel_provider
```

##Usage
Because this version of Jupyter kernel management is still in its experimental stages, a [special branch of Notebook](https://github.com/takluyver/notebook/tree/jupyter-kernel-mgmt) is required, which includes the machinery to leverage the new framework.  An installable build of this branch is available as an asset on the [interim-dev release](https://github.com/gateway-experiments/remote_kernel_provider/releases/tag/v0.1-interim-dev) of the Remote Kernel Provider on which Kubernetes Kernel Provider depends.

### Kubernetes Kernel Specifications
Criteria for discovery of the kernel specification via the `KubernetesKernelProvider` is that a `k8skp_kernel.json` file exist in a sub-directory named `kernels` in the Jupyter path hierarchy. 

Such kernel specifications should be initially created using the included Jupyter application`jupyter-k8s-kernelspec` to insure the minimally viable requirements exist.  This application can be used to create kernel specifications for use in Kubernetes, including Spark on Kubernetes for three languages: Python, Scala and R.

To create kernel specifications for use by KubernetesKernelProvider use `juptyer k8s-kernelspec install`.  Here are it's parameter options, produced using `jupyter k8s-kernelspec install --help`.  All parameters are optional with no parameters yielding a Python-based kernelspec for a Kuberenetes cluster.

```
A Jupyter kernel for use within a Kubernetes cluster

Options
-------

Arguments that take values are actually convenience aliases to full
Configurables, whose aliases are listed on the help line. For more information
on full configurables, see '--help-all'.

--user
    Install to the per-user kernel registry
--sys-prefix
    Install to Python's sys.prefix. Useful in conda/virtual environments.
--spark
    Install kernelspec for Spark on Kubernetes.
--tensorflow
    Install kernelspec with tensorflow support.
--debug
    set log level to logging.DEBUG (maximize logging output)
--prefix=<Unicode> (K8SKP_SpecInstaller.prefix)
    Default: ''
    Specify a prefix to install to, e.g. an env. The kernelspec will be
    installed in PREFIX/share/jupyter/kernels/
--kernel_name=<Unicode> (K8SKP_SpecInstaller.kernel_name)
    Default: 'k8skp_python'
    Install the kernel spec into a directory with this name.
--display_name=<Unicode> (K8SKP_SpecInstaller.display_name)
    Default: 'Kubernetes Python'
    The display name of the kernel - used by user-facing applications.
--image_name=<Unicode> (K8SKP_SpecInstaller.image_name)
    Default: None
    The kernel image to use for this kernel specification. If this specification
    is enabled for Spark usage, this image will be the driver image.
    (K8SKP_IMAGE_NAME env var)
--executor_image_name=<Unicode> (K8SKP_SpecInstaller.executor_image_name)
    Default: None
    The executor image to use for this kernel specification.  Only applies to
    Spark-enabled kernel specifications.  (K8SKP_EXECUTOR_IMAGE_NAME env var)
--language=<Unicode> (K8SKP_SpecInstaller.language)
    Default: 'Python'
    The language of the underlying kernel.  Must be one of 'Python', 'R', or
    'Scala'.  Default = 'Python'.
--spark_home=<Unicode> (K8SKP_SpecInstaller.spark_home)
    Default: '/opt/spark-2.1.0-bin-hadoop2.7'
    Specify where the spark files can be found.
--spark_init_mode=<Unicode> (K8SKP_SpecInstaller.spark_init_mode)
    Default: 'lazy'
    Spark context initialization mode.  Must be one of 'lazy', 'eager', or
    'none'.  Default = 'lazy'.
--extra_spark_opts=<Unicode> (K8SKP_SpecInstaller.extra_spark_opts)
    Default: ''
    Specify additional Spark options.
--log-level=<Enum> (Application.log_level)
    Default: 30
    Choices: (0, 10, 20, 30, 40, 50, 'DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL')
    Set the log level by value or name.
--config=<Unicode> (JupyterApp.config_file)
    Default: ''
    Full path of a config file.

To see all available configurables, use `--help-all`

Examples
--------

    jupyter-k8s-kernelspec install --language=R --image_name=foo/my_r_kernel_image:v4_0
    jupyter-k8s-kernelspec install --language=Scala --spark --kernel_name=Scala_on_k8s_spark
            --display_name='Scala on Kubernetes with Spark'
``` 
