from __future__ import with_statement

try:
    from setuptools import setup
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

from okydoky.version import VERSION


with open('README.rst') as f:
    readme = f.read()

with open('requirements.txt') as f:
    requirements = list(line.strip() for line in f)


setup(
    name='Okydoky',
    packages=['okydoky'],
    package_data={
        'okydoky': ['templates/*.*'],
        '': ['README.rst', 'requirements.txt', 'distribute_setup.py']
    },
    version=VERSION,
    description='Automated docs builder using Sphinx/GitHub/Distribute for '
                'private use',
    long_description=readme,
    license='MIT License',
    author='Hong Minhee',
    author_email='dahlia' '@' 'crosspop.in',
    maintainer='Hong Minhee',
    maintainer_email='dahlia' '@' 'crosspop.in',
    url='https://github.com/crosspop/okydoky',
    install_requires=requirements,
    entry_points = {
        'console_scripts': [
            'okydoky = okydoky.run:main'
        ]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 2 :: Only',
        'Topic :: Documentation',
        'Topic :: Software Development :: Documentation'
    ]
)
