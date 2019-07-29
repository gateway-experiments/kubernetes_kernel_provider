"""Tests kernel spec installation for use by KubernetesKernelProvider"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import json
import os
import pytest
import shutil
from tempfile import mkdtemp


@pytest.fixture(scope="module")
def mock_kernels_dir():
    kernels_dir = mkdtemp(prefix="kernels_")
    orig_data_dir = os.environ.get("JUPYTER_DATA_DIR")
    os.environ["JUPYTER_DATA_DIR"] = kernels_dir
    yield kernels_dir  # provide the fixture value
    shutil.rmtree(kernels_dir)
    if orig_data_dir:
        os.environ["JUPYTER_DATA_DIR"] = orig_data_dir
    else:
        os.environ.pop("JUPYTER_DATA_DIR")


@pytest.mark.script_launch_mode('subprocess')
def test_no_opts(script_runner):
    ret = script_runner.run('jupyter-k8s-kernelspec')
    assert ret.success is False
    assert ret.stdout.startswith("No subcommand specified.")
    assert ret.stderr == ''


@pytest.mark.script_launch_mode('subprocess')
def test_bad_subcommand(script_runner):
    ret = script_runner.run('jupyter', 'k8s-kernelspec', 'bogus-subcommand')
    assert ret.success is False
    assert ret.stdout.startswith("No subcommand specified.")
    assert ret.stderr == ''


@pytest.mark.script_launch_mode('subprocess')
def test_help_all(script_runner):
    ret = script_runner.run('jupyter-k8s-kernelspec', 'install', '--help-all')
    assert ret.success
    assert ret.stdout.startswith("A Jupyter kernel for use within a Kubernetes cluster")
    assert ret.stderr == ''


@pytest.mark.script_launch_mode('subprocess')
def test_bad_argument(script_runner):
    ret = script_runner.run('jupyter-k8s-kernelspec', 'install', '--bogus-argument')
    assert ret.success is False
    assert ret.stdout.startswith("A Jupyter kernel for use within a Kubernetes cluster")
    assert "[K8SKP_SpecInstaller] CRITICAL | Unrecognized flag: \'--bogus-argument\'" in ret.stderr


@pytest.mark.script_launch_mode('subprocess')
def test_mutually_exclusive(script_runner):
    ret = script_runner.run('jupyter-k8s-kernelspec', 'install', '--spark', '--tensorflow')
    assert ret.success is False
    assert ret.stdout == ''
    assert "[K8SKP_SpecInstaller] ERROR | Tensorflow support is mutually exclusive with Spark support." in ret.stderr


@pytest.mark.script_launch_mode('subprocess')
def test_bad_language(script_runner):
    ret = script_runner.run('jupyter-k8s-kernelspec', 'install', '--language=R', '--tensorflow')
    assert ret.success is False
    assert ret.stdout == ''
    assert "[K8SKP_SpecInstaller] ERROR | Tensorflow support is only available for use by Python kernels." in ret.stderr


@pytest.mark.script_launch_mode('subprocess')
def test_create_kernelspec(script_runner, mock_kernels_dir):
    my_env = os.environ.copy()
    my_env.update({"JUPYTER_DATA_DIR": mock_kernels_dir})
    ret = script_runner.run('jupyter-k8s-kernelspec', 'install', '--spark_home=/foo/bar',
                            '--spark', '--user', env=my_env)
    assert ret.success
    assert ret.stderr.startswith("[K8SKP_SpecInstaller] Installing Kubernetes Kernel Provider")
    assert ret.stdout == ''

    assert os.path.isdir(os.path.join(mock_kernels_dir, 'kernels', 'k8skp_python_spark'))
    assert os.path.isfile(os.path.join(mock_kernels_dir, 'kernels', 'k8skp_python_spark', 'k8skp_kernel.json'))

    with open(os.path.join(mock_kernels_dir, 'kernels', 'k8skp_python_spark', 'k8skp_kernel.json'), "r") as fd:
        kernel_json = json.load(fd)
        assert kernel_json["display_name"].endswith('(with Spark)')
        assert kernel_json["env"]["SPARK_HOME"] == '/foo/bar'
        assert kernel_json["metadata"]["lifecycle_manager"]["config"]["image_name"] == 'elyra/kernel-spark-py:dev'
        assert kernel_json["metadata"]["lifecycle_manager"]["config"]["executor_image_name"] == \
            'elyra/kernel-spark-py:dev'


@pytest.mark.script_launch_mode('subprocess')
def test_create_python_kernelspec(script_runner, mock_kernels_dir):
    my_env = os.environ.copy()
    my_env.update({"JUPYTER_DATA_DIR": mock_kernels_dir})
    my_env.update({"SPARK_HOME": "/bar/foo"})
    ret = script_runner.run('jupyter-k8s-kernelspec', 'install', '--display_name="My Python Kernel"',
                            '--kernel_name=my_python_kernel', '--user', '--image_name=foo/bar:zed', env=my_env)
    assert ret.success
    assert ret.stderr.startswith("[K8SKP_SpecInstaller] Installing Kubernetes Kernel Provider")
    assert ret.stdout == ''

    assert os.path.isdir(os.path.join(mock_kernels_dir, 'kernels', 'my_python_kernel'))
    assert os.path.isfile(os.path.join(mock_kernels_dir, 'kernels', 'my_python_kernel', 'k8skp_kernel.json'))

    with open(os.path.join(mock_kernels_dir, 'kernels', 'my_python_kernel', 'k8skp_kernel.json'), "r") as fd:
        kernel_json = json.load(fd)
        assert kernel_json["display_name"] == 'My Python Kernel'
        assert 'SPARK_HOME' not in kernel_json["env"]
        assert kernel_json["metadata"]["lifecycle_manager"]["config"]["image_name"] == 'foo/bar:zed'


@pytest.mark.script_launch_mode('subprocess')
def test_create_r_kernelspec(script_runner, mock_kernels_dir):
    my_env = os.environ.copy()
    my_env.update({"JUPYTER_DATA_DIR": mock_kernels_dir})
    my_env.update({"SPARK_HOME": "/bar/foo"})
    ret = script_runner.run('jupyter-k8s-kernelspec', 'install', '--language=R', '--display_name="My R Kernel"',
                            '--kernel_name=my_r_kernel', '--user', '--spark', env=my_env)
    assert ret.success
    assert ret.stderr.startswith("[K8SKP_SpecInstaller] Installing Kubernetes Kernel Provider")
    assert ret.stdout == ''

    assert os.path.isdir(os.path.join(mock_kernels_dir, 'kernels', 'my_r_kernel'))
    assert os.path.isfile(os.path.join(mock_kernels_dir, 'kernels', 'my_r_kernel', 'k8skp_kernel.json'))

    with open(os.path.join(mock_kernels_dir, 'kernels', 'my_r_kernel', 'k8skp_kernel.json'), "r") as fd:
        kernel_json = json.load(fd)
        assert kernel_json["display_name"] == 'My R Kernel'
        assert kernel_json["env"]["SPARK_HOME"] == '/bar/foo'
        argv = kernel_json["argv"]
        assert argv[len(argv) - 1] == 'lazy'


@pytest.mark.script_launch_mode('subprocess')
def test_create_scala_kernelspec(script_runner, mock_kernels_dir):
    my_env = os.environ.copy()
    my_env.update({"JUPYTER_DATA_DIR": mock_kernels_dir})
    my_env.update({"SPARK_HOME": "/bar/foo"})
    ret = script_runner.run('jupyter-k8s-kernelspec', 'install', '--language=Scala',
                            '--display_name="My Scala Kernel"', '--kernel_name=my_scala_kernel',
                            '--extra_spark_opts=--MyExtraSparkOpts', '--user', '--spark', env=my_env)
    assert ret.success
    assert ret.stderr.startswith("[K8SKP_SpecInstaller] Installing Kubernetes Kernel Provider")
    assert ret.stdout == ''

    assert os.path.isdir(os.path.join(mock_kernels_dir, 'kernels', 'my_scala_kernel'))
    assert os.path.isfile(os.path.join(mock_kernels_dir, 'kernels', 'my_scala_kernel', 'k8skp_kernel.json'))

    with open(os.path.join(mock_kernels_dir, 'kernels', 'my_scala_kernel', 'k8skp_kernel.json'), "r") as fd:
        kernel_json = json.load(fd)
        assert kernel_json["display_name"] == 'My Scala Kernel'
        assert '--MyExtraSparkOpts' in kernel_json["env"]["__TOREE_SPARK_OPTS__"]


@pytest.mark.script_launch_mode('subprocess')
def test_create_tensorflow_kernelspec(script_runner, mock_kernels_dir):
    my_env = os.environ.copy()
    my_env.update({"JUPYTER_DATA_DIR": mock_kernels_dir})
    ret = script_runner.run('jupyter', 'k8s-kernelspec', 'install', '--tensorflow',
                            '--display_name="My TF Kernel"', '--kernel_name=my_tf_kernel',
                            '--user', env=my_env)
    assert ret.success
    assert "[K8SKP_SpecInstaller] Installing Kubernetes Kernel Provider" in ret.stderr
    assert ret.stderr.startswith("[K8SKP_SpecInstaller] Installing Kubernetes Kernel Provider")
    assert ret.stdout == ''

    assert os.path.isdir(os.path.join(mock_kernels_dir, 'kernels', 'my_tf_kernel'))
    assert os.path.isfile(os.path.join(mock_kernels_dir, 'kernels', 'my_tf_kernel', 'k8skp_kernel.json'))

    with open(os.path.join(mock_kernels_dir, 'kernels', 'my_tf_kernel', 'k8skp_kernel.json'), "r") as fd:
        kernel_json = json.load(fd)
        assert kernel_json["language"] == 'python'
        assert kernel_json["display_name"] == 'My TF Kernel'
        assert 'SPARK_HOME' not in kernel_json["env"]
        argv = kernel_json["argv"]
        assert argv[len(argv) - 1] == '{response_address}'
