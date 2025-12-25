from django.core.management import BaseCommand

from itoutils.django.commands import LoggedCommandMixin


class Command(LoggedCommandMixin, BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("value", type=str)

    def handle(self, value, **options):
        print(value)
