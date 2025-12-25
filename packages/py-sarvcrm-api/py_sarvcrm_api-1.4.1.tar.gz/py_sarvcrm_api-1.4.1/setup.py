from setuptools import find_packages, setup

setup(
    name='py-sarvcrm-api',
    version='1.4.1',
    license="MIT",
    description='simple sarvcrm api module',
    author='hmohammad',
    author_email='hmohammad2520@gmail.com',
    url='https://github.com/Radin-System/py-sarvcrm-api',
    install_requires=[
        'requests==2.32.4',
        'requests-cache==1.2.1',
        'classmods==1.2.1'
    ],
    packages=find_packages(exclude=['test', 'test.*']),
    include_package_data=True,
    zip_safe=False,
)