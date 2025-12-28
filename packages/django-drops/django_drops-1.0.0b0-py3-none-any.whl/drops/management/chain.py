import argparse
import os
import re
import subprocess
from traceback import format_exception_only
from typing import Any

from django.core import management
from django.core.management.base import BaseCommand


class AppendWithRelatedActions(argparse.Action):
    """
    Экшон для argparse, который позволяет привязать к аргументу подаргументы

    Он складывает неймспейсы со значениями связанных аргументов в список
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, default=[], **kwargs)
        self.related = []  # список связанных аргументов

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Any,
        option_string: str | None = None,
    ) -> None:
        dest = getattr(namespace, self.dest)
        dest.append(
            argparse.Namespace(
                type=option_string.lstrip(parser.prefix_chars).replace("-", "_"),  # не особо общий код
                value=values,
                **{action.dest: action.default for action in self.related if action.default is not None},
            )
        )


class LinkedStoreTrueAction(argparse._StoreTrueAction):
    """
    Наследоваться от приватных классов плохо, но они сами виноваты
    """

    def __init__(self, *args, linked_to: AppendWithRelatedActions, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.linked_to = linked_to
        linked_to.related.append(self)

    def get_namespace(self, namespace: argparse.Namespace) -> argparse.Namespace:
        """
        Нужен неймспейс последнего тега, с которым связан
        """
        namespaces = getattr(namespace, self.linked_to.dest)
        if not namespaces:
            raise argparse.ArgumentError(self, f"can't be used before {' or '.join(self.linked_to.option_strings)}")
        return namespaces[-1]

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Any,
        option_string: str | None = None,
    ) -> None:
        super().__call__(parser, self.get_namespace(namespace), values, option_string)


def expand_environment_variables(arg: str) -> str:
    return re.sub(r"\$(\w+)", lambda m: os.getenv(m.group(1), ""), arg)


class Command(BaseCommand):
    """
    Runs command chain.

    Команды должны быть целиком в строке, чтобы парсер не пытался обработать их агрументы:
    manage.py chain --shell 'ls -l' --manage 'collectstatic --noinput' и т.п.
    """

    help = "Chain commands execution"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        command = parser.add_argument("--manage", "--shell", action=AppendWithRelatedActions, dest="commands")
        parser.add_argument("--allow-failure", action=LinkedStoreTrueAction, linked_to=command)

    def handle(self, *args, **options) -> None:
        for command in options.get("commands", []):
            try:
                self.stdout.write(self.style.SUCCESS(f"> {command.value}"))
                if command.type == "shell":
                    subprocess.run(command.value, shell=True, check=True)
                else:
                    # а тут мы будем подставлять значения переменных окружения сами
                    argv = command.value.split()
                    expanded = (expand_environment_variables(arg) for arg in argv)
                    management.call_command(*expanded)
            except Exception as e:
                if not command.allow_failure:
                    raise

                self.stdout.write(self.style.WARNING("".join(format_exception_only(e))))
