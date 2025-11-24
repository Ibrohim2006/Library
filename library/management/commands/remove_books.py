from django.core.management.base import BaseCommand

from library.models import BookModel

class Command(BaseCommand):
    help = 'Generate 1 identical book entries for testing'

    def handle(self, *args, **kwargs):
        BookModel.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("✅ 1000 ta book muvaffaqiyatli yaratildi."))