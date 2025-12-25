from django.core.management import BaseCommand

from itoutils.django.commands import LoggedCommandMixin, dry_runnable
from testproject.testapp.models import Item


class Command(LoggedCommandMixin, BaseCommand):
    ATOMIC_HANDLE = True

    def add_arguments(self, parser):
        parser.add_argument("pk", type=int)
        parser.add_argument("--delete", dest="delete", action="store_true")
        parser.add_argument("--wet-run", dest="wet_run", action="store_true")

    @dry_runnable
    def handle(self, pk, delete=False, **options):
        item = Item.objects.get(pk=pk)
        if delete:
            self.logger.info("Deleting Item pk=%d", pk)
            item.delete()
        else:
            print(item)
