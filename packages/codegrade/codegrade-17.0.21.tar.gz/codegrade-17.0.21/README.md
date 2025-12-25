# CodeGrade API

This library makes it easier to use the CodeGrade API. Its API allows you to
automate your usage of CodeGrade. We are currently still busy documenting the
entire API, but everything that is possible in the UI of CodeGrade is also
possible through the API.
## Installation
You can install the library through [pypi](https://pypi.org/), simply run
`python3 -m pip install codegrade`. If you want to get a dev version with support
for the latest features, simply email [support@codegrade.com](mailto:support@codegrade.com)
and we'll provide you with a dev version.
## Usage
First, create a client:

```python
import codegrade

# Don't store your password in your code!
with codegrade.login(
    username='my-username',
    password=os.getenv('CG_PASSWORD'),
    tenant='My University',
) as client:
    pass

# Or supply information interactively.
with codegrade.login_from_cli() as client:
    pass
```

Now call your endpoint and use your models:

```python
from codegrade.models import PatchCourseData

courses = client.course.get_all()
for course in courses:
    client.course.patch(
        PatchCourseData(name=course.name + ' (NEW)'),
        course_id=course.id,
    )

# Or, simply use dictionaries.
for course in courses:
    client.course.patch(
        {"name": course.name + ' (NEW)'},
        course_id=course.id,
    )
```

For the complete documentation go to
https://python.api.codegrade.com.
## Backwards compatibility
CodeGrade is constantly upgrading its API, but we try to minimize backwards
incompatible changes. We'll announce every backwards incompatible change in the
[changelog](http://codegrade.com/changelog). A new version of the API
client is released with every release of CodeGrade, which is approximately every
month. To upgrade simply run `pip install --upgrade codegrade`.
## Supported python versions
We support python 3.6 and above, `pypy` is currently not tested but should work
just fine.
## License
The library is licensed under AGPL-3.0-only or BSD-3-Clause-Clear.