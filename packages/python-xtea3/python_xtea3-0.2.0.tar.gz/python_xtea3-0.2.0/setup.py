from setuptools import setup
from Cython.Build import cythonize

setup(
    name='python-xtea3',
    version='0.2.0',
    author='Sergei Pikhovkin',
    license='MIT',
    description='XTEA3 implementation',
    url='https://github.com/pikhovkin/python-xtea3',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    python_requires=">=3.12,<4.0",
    ext_modules=cythonize('xtea3/xtea3.pyx'),
    include_package_data=True,
    packages=['xtea3'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Programming Language :: Python :: 3.15',
    ],
    keywords=[
        'xtea3',
    ],
)
