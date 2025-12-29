from setuptools import setup
import os
import subprocess
import re


def read_requirements():
    here = os.path.dirname(os.path.abspath(__file__))
    req_path = os.path.join(here, 'requirements.txt')
    with open(req_path, 'r') as f:
        return f.read().splitlines()


def get_cuda_version():
    try:
        output = subprocess.check_output(['nvcc', '--version']).decode()
        match = re.search(r'release (\d+\.\d+)', output)
        if match:
            return float(match.group(1))
    except Exception:
        return None


def get_pytorch_version(cuda_version):
    if cuda_version is None:
        return 'torch>=2.4.0'
    elif 12.6 <= cuda_version < 12.8:
        return 'torch>=2.4.0+cu126'
    elif 12.8 <= cuda_version < 13.0:
        return 'torch>=2.4.0+cu128'
    elif cuda_version >= 13.0:
        return 'torch>=2.4.0+cu130'
    else:
        return 'torch>=2.4.0'


requirements = read_requirements()


try:
    # noinspection PyPackageRequirements
    import torch
    torch_installed = True
except ImportError:
    torch_installed = False

if not torch_installed:
    detected_cuda_version = get_cuda_version()
    requirements.append(get_pytorch_version(detected_cuda_version))


setup(
    name='pose-estimation-recognition-utils-rtmlib',
    version='0.1.2',
    packages=['pose_estimation_recognition_utils_rtmlib'],
    install_requires=requirements,
    url='https://github.com/cobtras/pose-estimation-recognition-utils-rtmlib',
    license='Apache 2.0',
    author='Jonas David Stephan, Sabine Dawletow, Nathalie Dollmann, Benjamin Otto Ernst Bruch',
    author_email='j.stephan@system-systeme.de',
    description='Classes for AI recognition on pose estimation data with rtmlib',
    long_description='Includes all general classes needed for AI movement recognition based on pose estimation data with rtmlib'
)
