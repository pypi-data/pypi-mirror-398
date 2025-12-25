# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['libtvdb', 'libtvdb.model']

package_data = \
{'': ['*']}

install_requires = \
['deserialize>=2.1.0,<3.0.0', 'requests>=2.32.3,<3.0.0']

setup_kwargs = {
    'name': 'libtvdb',
    'version': '0.12.1',
    'description': 'A wrapper around the TVDB API.',
    'long_description': '# libtvdb\n\n[![CI](https://github.com/dalemyers/libtvdb/workflows/CI/badge.svg)](https://github.com/dalemyers/libtvdb/actions)\n[![PyPI version](https://badge.fury.io/py/libtvdb.svg)](https://badge.fury.io/py/libtvdb)\n[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)\n\nA wrapper around the [TVDB API](https://api.thetvdb.com/swagger).\n\n## Installation\n\n```bash\npip install libtvdb\n```\n\n## Examples\n\nSearching for shows:\n\n```python\nimport libtvdb\n\nclient = libtvdb.TVDBClient(api_key="...", pin="...")\nshows = client.search_show("Doctor Who")\n\nfor show in shows:\n    print(show.name)\n```\n\n## Development\n\nThis project uses [Poetry](https://python-poetry.org/) for dependency management.\n\n```bash\n# Install dependencies\npoetry install\n\n# Run tests\npoetry run pytest\n\n# Run linters and type checkers\npoetry run ruff check libtvdb\npoetry run black --check libtvdb tests\npoetry run pylint libtvdb\npoetry run mypy libtvdb\npoetry run pyright libtvdb\n```\n\n## Advanced\n\nYou can set `libtvdb_api_key` and `libtvdb_pin` in your OS X keychain if you don\'t want to supply these every time. If any of the values supplied to the `TVDBClient` constructor are `None`, it will look into your keychain and load the appropriate value. If it can\'t find them, it will throw an exception.\n',
    'author': 'Dale Myers',
    'author_email': 'dale@myers.io',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'https://github.com/dalemyers/libtvdb',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.11,<4.0',
}


setup(**setup_kwargs)
