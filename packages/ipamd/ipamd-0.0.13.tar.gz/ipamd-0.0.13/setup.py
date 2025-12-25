from setuptools import setup, find_packages
import os
home_dir = os.path.expanduser('~')
config_dir = os.path.join(home_dir, '.config/ipamd')

setup(
    name='ipamd',
    python_requires='>=3.12',
    license='LGPL-3.0',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    description='A Python package for MD simulations and analysis of biomolecules',
    version='0.0.13',
    include_package_data=True,
    package_data={
        'ipamd': [
            "data/forcefield/*", 
            "app/lib/*",
            "plugins/analysis/data_process/*",
            "plugins/analysis/operator/*",
            "plugins/builder/converter/*",
            "plugins/builder/genbox/*",
            "plugins/builder/generator/*",
            "plugins/simulation/force/*",
            "plugins/simulation/integrator/*",
            "plugins/sakuanna/*",
        ]
    },
    data_files=[
    ],
    install_requires=[
        'tabulate',
        'rich',
        'numba',
        'matplotlib',
        'biopython',
        'requests',
        'pandas',
        'numpy',
        'pybioseq'
    ],
    packages=find_packages(),
    author='Xiaoyang Liu',
    author_email='liuxiaoyang_Q@outlook.com'
)
