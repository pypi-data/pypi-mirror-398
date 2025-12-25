# Inspect Tasks in your Django App

![PyPI - Version](https://img.shields.io/pypi/v/django-inspect-tasks)
![PyPI - License](https://img.shields.io/pypi/l/django-inspect-tasks)

# Instalation

Install using `pip` or `uv` (or your favorite tool)

```shell
uv add django-inspect-tasks
```

Then add to your projects `settings.py` under `INSTALLED_APPS`

```python
INSTALLED_APPS = [
    "myapp",
    # Third Party
    "crontask",
    "django_inspect_tasks",
    # Default Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]
```

Adds a `tasks` subcommand to your app

```shell
python manage.py tasks
crontask.tasks.heartbeat cron[month='*', day='*', day_of_week='*', hour='*', minute='*']
myapp.tasks.example_regular_task
myapp.tasks.example_scheduled_task interval[0:01:00]
```
