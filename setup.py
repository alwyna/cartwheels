from setuptools import setup

setup(
    name='cartwheels',
    version='0.0.0a1',
    description='Resolve version sets of python packages',
    author='Alwyn Aswin',
    author_email='aa2shop@hotmail.com',
    packages=['cartwheels'],  # same as name
    install_requires=['wheel', 'aiohttp==3.9.5', 'scipy==1.11.4', 'packaging==24.0', 'dill==0.3.8', 'matplotlib==3.9.0',
                      'numpy==1.26.4', 'pandas==2.2.2', 'networkx==3.3',
                      'jupyter==1.0.0', 'pydot==2.0.0', 'scikit-learn==1.4.2', 'pandas==2.2.2', 'tabulate==0.9.0']
    # external packages as dependencies
)
