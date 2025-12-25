from setuptools import setup, find_packages

setup(
    name='toughanimator',  # Package name on PyPI
    version='0.1.10',
    description='A tool for visualizing TOUGH simulation outputs.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='scarletref',
    author_email='scarletreflection@gmail.com',
    url='https://github.com/scarletref/toughanimator',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'numpy',
        'pandas',
        'vtk',
    ],
    python_requires='>=3.11,<3.14',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
