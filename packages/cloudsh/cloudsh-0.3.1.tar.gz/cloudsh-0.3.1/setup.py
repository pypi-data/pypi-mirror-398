# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['cloudsh', 'cloudsh.commands']

package_data = \
{'': ['*'], 'cloudsh': ['args/*']}

install_requires = \
['aiofiles>=23.0.0,<24.0.0',
 'argcomplete>=3.5.3,<4.0.0',
 'argx>=0.3,<0.4',
 'panpath>=0.4,<0.5',
 'python-dateutil>=2.9.0.post0,<3.0.0',
 'python-simpleconf[toml]>=0.7,<0.8']

extras_require = \
{'all': ['azure-storage-blob>=12,<13',
         'aioboto3>=11.0.0',
         'gcloud-aio-storage>=8.0.0'],
 'aws': ['aioboto3>=11.0.0'],
 'azure': ['azure-storage-blob>=12,<13'],
 'gcs': ['gcloud-aio-storage>=8.0.0'],
 'gs': ['gcloud-aio-storage>=8.0.0'],
 's3': ['aioboto3>=11.0.0']}

entry_points = \
{'console_scripts': ['cloudsh = cloudsh.main:main']}

setup_kwargs = {
    'name': 'cloudsh',
    'version': '0.3.1',
    'description': 'A Python CLI wrapping common Linux commands for local/cloud files.',
    'long_description': 'None',
    'author': 'Your Name',
    'author_email': 'you@example.com',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'None',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'extras_require': extras_require,
    'entry_points': entry_points,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
