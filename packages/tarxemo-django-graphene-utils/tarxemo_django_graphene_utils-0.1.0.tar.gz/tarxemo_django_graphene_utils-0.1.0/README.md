# TarXemo Django Graphene Utils

A utility collection for building standardized GraphQL APIs with Django and Graphene.

## Installation

```bash
pip install tarxemo-django-graphene-utils
```

## Usage

### Standardized Responses

```python
from tarxemo_django_graphene_utils import build_success_response, build_error

def resolve_something(root, info):
    if success:
        return build_success_response("Operation successful")
    return build_error("Something went wrong")
```

### Pagination

```python
from tarxemo_django_graphene_utils import get_paginated_and_non_paginated_data

def resolve_items(root, info, **kwargs):
    return get_paginated_and_non_paginated_data(
        model=MyModel,
        filtering_object=kwargs,
        graphene_type=MyModelType
    )
```

## Building and Publishing

1. Build the package:
   ```bash
   python setup.py sdist bdist_wheel
   ```

2. Upload to PyPI (requires twine):
   ```bash
   twine upload dist/*
   ```
