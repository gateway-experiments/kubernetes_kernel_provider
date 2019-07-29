"""Installs kernel specs for use by KubernetesKernelProvider"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import os.path
import json
import sys

from distutils import dir_util
from string import Template
from traitlets.config.application import Application
from jupyter_core.application import (
    JupyterApp, base_flags, base_aliases
)
from traitlets import Instance, Dict, Unicode, Bool, default
from jupyter_kernel_mgmt.kernelspec import KernelSpec, KernelSpecManager
from remote_kernel_provider import spec_utils

from .provider import KubernetesKernelProvider
from . import __version__

KERNEL_JSON = "k8skp_kernel.json"
PYTHON = 'python'
TENSORFLOW = 'tensorflow'
DEFAULT_LANGUAGE = PYTHON
SUPPORTED_LANGUAGES = [PYTHON, 'scala', 'r']
DEFAULT_KERNEL_NAMES = {
    DEFAULT_LANGUAGE: 'k8skp_python',
    'scala': 'k8skp_scala',
    'r': 'k8skp_r'}
DEFAULT_DISPLAY_NAMES = {
    DEFAULT_LANGUAGE: 'Kubernetes Python',
    'scala': 'Kubernetes Scala',
    'r': 'Kubernetes R'}
DEFAULT_IMAGE_NAMES = {
    DEFAULT_LANGUAGE: 'elyra/kernel-py:dev',
    'scala': 'elyra/kernel-scala:dev',
    'r': 'elyra/kernel-r:dev',
    'tensorflow': 'elyra/kernel-tf-py:dev'}
DEFAULT_SPARK_IMAGE_NAMES = {
    DEFAULT_LANGUAGE: 'elyra/kernel-spark-py:dev',
    'scala': 'elyra/kernel-scala:dev',
    'r': 'elyra/kernel-spark-r:dev'}

SPARK_SUFFIX = '_spark'
SPARK_DISPLAY_NAME_SUFFIX = ' (with Spark)'
TENSORFLOW_SUFFIX = '_tf'
TENSORFLOW_DISPLAY_NAME_SUFFIX = ' (with Tensorflow)'
DEFAULT_INIT_MODE = 'lazy'
SPARK_INIT_MODES = [DEFAULT_INIT_MODE, 'eager', 'none']


class K8SKP_SpecInstaller(JupyterApp):
    """CLI for extension management."""
    name = u'jupyter-k8s-kernelspec'
    description = u'A Jupyter kernel for use within a Kubernetes cluster'
    examples = '''
    jupyter-k8s-kernelspec install --language=R --image_name=foo/my_r_kernel_image:v4_0
    jupyter-k8s-kernelspec install --language=Scala --spark --kernel_name=Scala_on_k8s_spark
            --display_name='Scala on Kubernetes with Spark'
    '''
    kernel_spec_manager = Instance(KernelSpecManager)

    def _kernel_spec_manager_default(self):
        return KernelSpecManager(kernel_file=KubernetesKernelProvider.kernel_file)

    source_dir = Unicode()
    staging_dir = Unicode()
    template_dir = Unicode()

    kernel_name = Unicode(DEFAULT_KERNEL_NAMES[DEFAULT_LANGUAGE], config=True,
                          help='Install the kernel spec into a directory with this name.')

    display_name = Unicode(DEFAULT_DISPLAY_NAMES[DEFAULT_LANGUAGE], config=True,
                           help='The display name of the kernel - used by user-facing applications.')

    # Image name
    image_name_env = 'K8SKP_IMAGE_NAME'
    image_name = Unicode(None, config=True, allow_none=True,
                         help="""The kernel image to use for this kernel specification. If this specification is
                         enabled for Spark usage, this image will be the driver image. (K8SKP_IMAGE_NAME env var)""")

    @default('image_name')
    def image_name_default(self):
        return os.getenv(self.image_name_env)

    executor_image_name_env = 'K8SKP_EXECUTOR_IMAGE_NAME'
    executor_image_name = Unicode(None, config=True, allow_none=True,
                                  help="""The executor image to use for this kernel specification.  Only applies to
                                  Spark-enabled kernel specifications.  (K8SKP_EXECUTOR_IMAGE_NAME env var)""")

    @default('executor_image_name')
    def executor_image_name_default(self):
        return os.getenv(self.executor_image_name_env)

    language = Unicode('Python', config=True,
                       help="The language of the underlying kernel.  Must be one of 'Python', 'R', or "
                            "'Scala'.  Default = 'Python'.")

    spark_home = Unicode(os.getenv("SPARK_HOME", '/opt/spark'), config=True,
                         help="Specify where the spark files can be found.")

    spark_init_mode = Unicode(DEFAULT_INIT_MODE, config=True,
                              help="Spark context initialization mode.  Must be one of 'lazy', 'eager', "
                                   "or 'none'.  Default = 'lazy'.")

    extra_spark_opts = Unicode('', config=True, help="Specify additional Spark options.")

    # Flags
    user = Bool(False, config=True,
                help="Try to install the kernel spec to the per-user directory instead of the system "
                     "or environment directory.")

    prefix = Unicode('', config=True,
                     help="Specify a prefix to install to, e.g. an env. The kernelspec will be "
                          "installed in PREFIX/share/jupyter/kernels/")

    spark = Bool(False, config=True, help="Install kernel for use with Spark.")

    tensorflow = Bool(False, config=True, help="Install kernel for use with Tensorflow.")

    aliases = {
        'prefix': 'K8SKP_SpecInstaller.prefix',
        'kernel_name': 'K8SKP_SpecInstaller.kernel_name',
        'display_name': 'K8SKP_SpecInstaller.display_name',
        'image_name': 'K8SKP_SpecInstaller.image_name',
        'executor_image_name': 'K8SKP_SpecInstaller.executor_image_name',
        'language': 'K8SKP_SpecInstaller.language',
        'spark_home': 'K8SKP_SpecInstaller.spark_home',
        'spark_init_mode': 'K8SKP_SpecInstaller.spark_init_mode',
        'extra_spark_opts': 'K8SKP_SpecInstaller.extra_spark_opts',
    }
    aliases.update(base_aliases)

    flags = {'user': ({'K8SKP_SpecInstaller': {'user': True}},
                      "Install to the per-user kernel registry"),
             'sys-prefix': ({'K8SKP_SpecInstaller': {'prefix': sys.prefix}},
                            "Install to Python's sys.prefix. Useful in conda/virtual environments."),
             'spark': ({'K8SKP_SpecInstaller': {'spark': True}},
                       "Install kernelspec for Spark on Kubernetes."),
             'tensorflow': ({'K8SKP_SpecInstaller': {'tensorflow': True}},
                            "Install kernelspec with tensorflow support."),
             'debug': base_flags['debug'], }

    def parse_command_line(self, argv=None):
        super(K8SKP_SpecInstaller, self).parse_command_line(argv=argv)

    def start(self):
        # validate parameters, ensure values are present
        self._validate_parameters()

        # create staging dir
        self.staging_dir = spec_utils.create_staging_directory()

        # copy files from installed area to staging dir
        self.source_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'kernelspecs', self.template_dir))
        dir_util.copy_tree(src=self.source_dir, dst=self.staging_dir)
        spec_utils.copy_kernelspec_files(self.staging_dir, launcher_type='kubernetes',
                                         resource_type=TENSORFLOW if self.tensorflow else self.language)
        # install to destination
        self.log.info("Installing Kubernetes Kernel Provider kernel specification for '{}'".format(self.display_name))
        install_dir = self.kernel_spec_manager.install_kernel_spec(self.staging_dir,
                                                                   kernel_name=self.kernel_name,
                                                                   user=self.user,
                                                                   prefix=self.prefix)

        # apply template values at destination (since one of the values is the destination directory)
        self._finalize_kernel_json(install_dir)

    def _finalize_kernel_json(self, location):
        """Apply substitutions to the kernel.json string, update a kernel spec using these values,
           then write to the target kernel.json file.
        """
        subs = self._get_substitutions(location)
        kernel_json_str = ''
        with open(os.path.join(location, KERNEL_JSON)) as f:
            for line in f:
                line = line.split('#', 1)[0]
                kernel_json_str = kernel_json_str + line
            f.close()
        post_subs = Template(kernel_json_str).safe_substitute(subs)
        kernel_json = json.loads(post_subs)

        # Instantiate default KernelSpec, then update with the substitutions.  This allows for new fields
        # to be added that we might not yet know about.
        kernel_spec = KernelSpec().to_dict()
        kernel_spec.update(kernel_json)

        kernel_json_file = os.path.join(location, KERNEL_JSON)
        self.log.debug("Finalizing kernel json file for kernel: '{}'".format(self.display_name))
        with open(kernel_json_file, 'w+') as f:
            json.dump(kernel_spec, f, indent=2)

    def _validate_parameters(self):
        if self.user and self.prefix:
            self._log_and_exit("Can't specify both user and prefix. Please choose one or the other.")

        entered_language = self.language
        self.language = self.language.lower()
        if self.language not in SUPPORTED_LANGUAGES:
            self._log_and_exit("Language '{}' is not in the set of supported languages: {}".
                               format(entered_language, SUPPORTED_LANGUAGES))

        if self.tensorflow:
            if self.language != PYTHON:
                self._log_and_exit("Tensorflow support is only available for use by Python kernels.")
            elif self.spark:
                self._log_and_exit("Tensorflow support is mutually exclusive with Spark support.")

        if self.spark is True:
            self.spark_init_mode = self.spark_init_mode.lower()
            if self.spark_init_mode not in SPARK_INIT_MODES:
                self._log_and_exit("Spark initialization mode '{}' is not in the set of supported "
                                   "initialization modes: {}".format(self.spark_init_mode, SPARK_INIT_MODES))

            # if kernel and display names are still defaulted, silently convert to lang default and append spark suffix
            if self.kernel_name == DEFAULT_KERNEL_NAMES[DEFAULT_LANGUAGE]:
                self.kernel_name = DEFAULT_KERNEL_NAMES[self.language] + SPARK_SUFFIX
            if self.display_name == DEFAULT_DISPLAY_NAMES[DEFAULT_LANGUAGE]:
                self.display_name = DEFAULT_DISPLAY_NAMES[self.language] + SPARK_DISPLAY_NAME_SUFFIX

            self.template_dir = DEFAULT_KERNEL_NAMES[self.language] + SPARK_SUFFIX

            if self.image_name is None:
                self.image_name = DEFAULT_SPARK_IMAGE_NAMES[self.language]
            if self.executor_image_name is None:
                self.executor_image_name = self.image_name
        else:
            # if kernel and display names are still defaulted, silently change to language defaults
            if self.tensorflow:
                if self.kernel_name == DEFAULT_KERNEL_NAMES[DEFAULT_LANGUAGE]:
                    self.kernel_name = DEFAULT_KERNEL_NAMES[self.language] + TENSORFLOW_SUFFIX
                if self.display_name == DEFAULT_DISPLAY_NAMES[DEFAULT_LANGUAGE]:
                    self.display_name = DEFAULT_DISPLAY_NAMES[self.language] + TENSORFLOW_DISPLAY_NAME_SUFFIX
                self.template_dir = DEFAULT_KERNEL_NAMES[self.language] + TENSORFLOW_SUFFIX
                if self.image_name is None:
                    self.image_name = DEFAULT_IMAGE_NAMES[TENSORFLOW]
            else:
                if self.kernel_name == DEFAULT_KERNEL_NAMES[DEFAULT_LANGUAGE]:
                    self.kernel_name = DEFAULT_KERNEL_NAMES[self.language]
                if self.display_name == DEFAULT_DISPLAY_NAMES[DEFAULT_LANGUAGE]:
                    self.display_name = DEFAULT_DISPLAY_NAMES[self.language]
                self.template_dir = DEFAULT_KERNEL_NAMES[self.language]
                if self.image_name is None:
                    self.image_name = DEFAULT_IMAGE_NAMES[self.language]

            self.spark_init_mode = 'none'
            if len(self.extra_spark_opts) > 0:
                self.log.warning("--extra_spark_opts will be ignored since --spark has not been specified.")
                self.extra_spark_opts = ''

        # sanitize kernel_name
        self.kernel_name = self.kernel_name.replace(' ', '_')

    def _get_substitutions(self, install_dir):

        substitutions = dict()
        substitutions['spark_home'] = self.spark_home
        substitutions['image_name'] = self.image_name
        substitutions['executor_image_name'] = self.executor_image_name
        substitutions['extra_spark_opts'] = self.extra_spark_opts
        substitutions['spark_init_mode'] = self.spark_init_mode
        substitutions['display_name'] = self.display_name
        substitutions['install_dir'] = install_dir

        return substitutions

    def _log_and_exit(self, msg, exit_status=1):
        self.log.error(msg)
        self.exit(exit_status)


class KubernetesKernelProviderApp(Application):
    version = __version__
    name = 'jupyter k8s-kernelspec'
    description = '''Application used to create kernelspecs for use on Kubernetes clusters

    \tKubernetes Kernel Provider Version: {}
    '''.format(__version__)
    examples = '''
    jupyter k8s-kernelspec install - Installs the kernel as a Jupyter Kernel.
    '''

    subcommands = Dict({
        'install': (K8SKP_SpecInstaller, K8SKP_SpecInstaller.description.splitlines()[0]),
    })

    aliases = {}
    flags = {}

    def start(self):
        if self.subapp is None:
            print('No subcommand specified. Must specify one of: {}'.format(list(self.subcommands)))
            print()
            self.print_description()
            self.print_subcommands()
            self.exit(1)
        else:
            return self.subapp.start()


if __name__ == '__main__':
    KubernetesKernelProviderApp.launch_instance()
