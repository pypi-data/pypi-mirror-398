django-epfl-mail
================

[![Build Status][github-actions-image]][github-actions-url]
[![Coverage Status][codecov-image]][codecov-url]
[![PyPI version][pypi-image]][pypi-url]
[![PyPI Python version][pypi-python-image]][pypi-url]

A Django application with templates for emails.

Requirements
------------

- Python 3.7 or later
- Django 2.2, 3.2, 4.2 or 5.2

Installation
------------

Installing from PyPI is as easy as doing:

```bash
pip install django-epfl-mail
```

Documentation
-------------

### Setup

Add `'django_epflmail'` to your `INSTALLED_APPS` setting.

```python
INSTALLED_APPS = [
    ...
    'django_epflmail',
]
```

### Example template

```python
from django.core.mail.message import EmailMessage
from django.template.loader import render_to_string

html = render_to_string("example.html", {"APP_TITLE": "Example"})
email = EmailMessage(
    "Email Example", html, "from@example.com", ["to@example.com"]
)
email.send()
```

```htmldjango
{% extends "epflmail/default.html" %}
{% load i18n %}

{% block title %}
Email Example
{% endblock %}

{% block online %}
  {% with ONLINE_VERSION_LINK="https://example.com" %}
    {% include 'epflmail/includes/online.inc.html'%}
  {% endwith %}
{% endblock %}

{% block main %}
  <p>This is an example.</p>
{% endblock %}

{% block unsubscribe %}
  <a href="https://example.com">Unsubscribe link</a>
{% endblock %}
```

[github-actions-image]: https://github.com/epfl-si/django-epfl-mail/actions/workflows/build.yml/badge.svg?branch=main
[github-actions-url]: https://github.com/epfl-si/django-epfl-mail/actions

[codecov-image]:https://codecov.io/gh/epfl-si/django-epfl-mail/branch/main/graph/badge.svg
[codecov-url]:https://codecov.io/gh/epfl-si/django-epfl-mail

[pypi-python-image]: https://img.shields.io/pypi/pyversions/django-epfl-mail
[pypi-image]: https://img.shields.io/pypi/v/django-epfl-mail
[pypi-url]: https://pypi.org/project/django-epfl-mail/
