from setuptools import setup, find_packages

setup(
    name='unmeshed-sdk',
    version='1.2.7',
    author='Unmeshed',
    author_email='pippython@unmeshed.com',
    description='Python SDK for Unmeshed Orchestration platform',
    zip_safe = False,
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/stablequark/unmeshed-python-sdk',
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        'requests',
        'setuptools',
        'pytest',
        'numpy'
    ],
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires='>=3.5',
)
