from django.core.management.base import BaseCommand

from library.models import BookModel

class Command(BaseCommand):
    help = 'Generate 1 identical book entries for testing'

    def handle(self, *args, **kwargs):
        books = []
        for i in range(1000):
            books.append(
                BookModel(
                    file="Ch Aytmatov O tar qush nolasi (1).pdf",
                )
            )

        BookModel.objects.bulk_create(books)
        self.stdout.write(self.style.SUCCESS("✅ 1000 ta book muvaffaqiyatli yaratildi."))