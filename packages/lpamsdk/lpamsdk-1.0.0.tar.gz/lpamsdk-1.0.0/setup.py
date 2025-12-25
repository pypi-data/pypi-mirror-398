from setuptools import setup, find_packages
import os

# Get the long description from the README file
with open(os.path.join(os.path.dirname(__file__), 'README.md'), 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='lpamsdk',
    version='1.0.0',
    description='Python wrapper for LPAMSDK',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Guannan Guo',
    author_email='ggntju@outlook.com',
    url='',
    packages=find_packages(),
    package_data={
        'lpamsdk': ['../dll/*', '../libs/*'],
    },
    include_package_data=True,
    # install_requires=[
    #     'pythonnet>=3.0.0',  # Required for .NET assembly interaction
    # ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development :: Libraries',
        'Topic :: System :: Hardware :: Hardware Drivers',
    ],
    python_requires='>=3.9',
)