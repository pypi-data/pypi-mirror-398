import argparse
import importlib
import logging
from pprint import pformat

from crontask import scheduler
from django.apps import apps
from django.core.management import BaseCommand, CommandError
from django.tasks import Task, TaskResult, task_backends


class Command(BaseCommand):
    def add_arguments(self, parser: argparse.ArgumentParser):
        task = parser.add_argument_group("Task Options")
        task.add_argument("--queue")
        task.add_argument("--backend")
        task.add_argument("--priority")
        task.add_argument("task", nargs="?")

    def handle_task(self, task: Task, **options):
        ch = logging.StreamHandler()
        formatter = logging.Formatter(logging.BASIC_FORMAT)
        ch.setFormatter(formatter)
        logging.root.addHandler(ch)

        result: TaskResult = task.using(
            queue_name=options["queue"],
            priority=options["priority"],
            backend=options["backend"],
        ).enqueue()
        return pformat(result)

    def get_task(self, task: str) -> Task:
        try:
            module_name, task_name = task.rsplit(".", 1)
            module = importlib.import_module(module_name)
        except ImportError:
            raise CommandError(f"Unknown task: {task}")
        else:
            return getattr(module, task_name)

    def task_class(self, backend, **options) -> tuple[Task]:
        return tuple({backend.task_class for backend in task_backends.all()})

    def handle(self, task, **options):
        # If we're passed a task name, we'll send that off to be executed
        if task:
            try:
                task = self.get_task(task)
            except ImportError:
                raise CommandError(f"Unknown task: {task}")
            else:
                return self.handle_task(task, **options)

        # First we need to lookup all the tasks our app can see
        TASK_CLASS = self.task_class(**options)
        tasks: dict[str, Task] = {}
        for app in apps.get_app_configs():
            try:
                module = importlib.import_module(f"{app.name}.tasks")
            except ImportError:
                pass
            else:
                for key in dir(module):
                    obj = getattr(module, key)
                    if isinstance(obj, TASK_CLASS):
                        tasks[obj.module_path] = obj

        # Then we check the schedule
        scheduled = {}
        for job in scheduler.get_jobs():
            scheduled[job.func.__self__.module_path] = job.trigger

        # Then we format the output, showing an extra annotation
        # for scheduled tasks
        padding = max([len(k) for k in tasks])
        for task in sorted(tasks):
            if task in scheduled:
                print(
                    task.ljust(padding),
                    self.style.MIGRATE_HEADING(scheduled[task]),
                )
            else:
                print(task)
