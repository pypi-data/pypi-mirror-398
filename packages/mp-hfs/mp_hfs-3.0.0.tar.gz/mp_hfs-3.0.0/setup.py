"""Setup script for mp-hfs (standard Python packaging)"""
from setuptools import setup, find_packages
import os

# 读取 README
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

# 读取版本号
version = '0.1.0'
if os.path.exists('VERSION'):
    with open('VERSION', 'r') as f:
        version = f.read().strip()

setup(
    name='mp-hfs',
    version=version,
    author='Rally82',
    author_email='rally82@example.com',
    description='HuggingFace Space Worker 分布式调度系统',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/rally82-2/ai-dev',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    python_requires='>=3.8',
    install_requires=[
        'redis>=4.0.0',
        'requests>=2.25.0',
        'click>=8.0.0',
        'pyyaml>=5.4.0',
        'tabulate>=0.8.9',
    ],
    entry_points={
        'console_scripts': [
            'hfs-worker=hfs.__main__:main',
            'hfs-admin=hfs.cli:cli',
        ],
    },
    include_package_data=True,
    package_data={
        'hfs': ['*.lua'],
    },
)
