from setuptools import setup, find_packages

setup(
    name='nse-trading-calendar',  # Must be unique on PyPI
    version='0.1.4',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['pandas', 'openpyxl'],
    author='Naveen Gupta',
    author_email='naveeng1520@gmail.com',
    description='Check NSE trading days and type using historical data.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    license='MIT',
    url='https://github.com/yourusername/nse-trading-calendar',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
