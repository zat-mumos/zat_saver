import os

from setuptools import find_packages, setup

package_name = 'zat_saver'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), ['launch/saver.py'])
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Behrouz Ghamkar',
    maintainer_email='behrouz.ghamkhar@smail.inf.h-brs.de',
    description='Package for saving the data stream from the ZAT sensor case pipeline.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'saver=zat_saver.data_saver:main'
        ],
    },
)
