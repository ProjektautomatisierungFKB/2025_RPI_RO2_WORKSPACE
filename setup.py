from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'my_gpio_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='pi',
    maintainer_email='pi@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    # Ausschnitt aus setup.py
	entry_points={
    		'console_scripts': [
        		'control_node = my_gpio_pkg.gpio_control_node:main',
    		],
	},
)
