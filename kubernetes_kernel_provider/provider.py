"""Provides support for launching and managing kernels within a Kubernetes cluster."""
import asyncio
import os
from datetime import datetime
from kubernetes import config
from kubernetes.config.config_exception import ConfigException
from remote_kernel_provider import RemoteKernelProviderBase


LOGGED_WARNING_INTERVAL = int(os.getenv("K8SKP_LOGGED_WARNING_INTERVAL_SECS", "600"))  # log no more than every 10 min
last_logged_warning = datetime.min
first_time = True
in_cluster = False


class KubernetesKernelProvider(RemoteKernelProviderBase):
    id = 'k8skp'
    kernel_file = 'k8skp_kernel.json'
    lifecycle_manager_classes = ['kubernetes_kernel_provider.k8s.KubernetesKernelLifecycleManager']

    @asyncio.coroutine
    def find_kernels(self):
        """ Ensures the provider is running within a Kubernetes cluster.  If not, it will
            log a warning message and no kernelspecs will be returned.  Since find_kernels()
            is frequently called, it will only log the warning periodically (10 minutes by default).
        """
        global first_time, in_cluster, last_logged_warning

        # Only check the cluster config once since the results can't change unless restarted.
        if first_time:
            try:
                config.load_incluster_config()
                in_cluster = True
            except ConfigException as ce:
                # Check to see if we're in-cluster via env.  If in-cluster, periodically
                # log a warning
                if os.getenv('KUBERNETES_SERVICE_HOST') is not None:
                    raise ce  # Got an exception in-cluster - let it be known
            first_time = False

        if not in_cluster:
            current_time = datetime.now()
            delta = current_time - last_logged_warning
            if delta.days > 0 or delta.seconds > LOGGED_WARNING_INTERVAL:
                self.log.warning("KubernetesKernelProvider must be run from within a Kubernetes "
                                 "cluster.  No Kubernetes kernels will be available.")
                last_logged_warning = current_time
            return {}

        return super(KubernetesKernelProvider, self).find_kernels()
