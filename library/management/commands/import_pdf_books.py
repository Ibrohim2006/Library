import logging
from django.core.management.base import BaseCommand

from library.models import BookModel        
from pathlib import Path


import os

class Command(BaseCommand):
    help = 'Generate 1 identical book entries for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--d',
            type=str,
            help='The path to the directory to process.',
            required=True  # Make the argument mandatory
        )


    def handle(self, *args, **kwargs):
        # cwd = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
        # files = os.listdir(cwd)  # Get all the files in that directory
        # print("Files in %r: %s" % (cwd, files))
        # print(kwargs.items())
        directory_path = Path(kwargs['d'])
        # directory_path = 'media/book/file/'  # Represents the current directory

        print(directory_path, "d")
        # print([a for a in os.walk(directory_path)])
        # # files_list = [p for p in os.scandir(directory_path) if p.endswith('.pdf')]
        files_list = [p for p in directory_path.iterdir() if p.suffix == '.pdf']
        # print(files_list, "files_list")
        books = []
        for file_path in files_list:
            books.append(
                BookModel(
                    file=str(file_path).replace(str(directory_path), ''),
                    title=str(file_path.name).replace('.pdf', ''),
                )
            )

        BookModel.objects.bulk_create(books)
        self.stdout.write(self.style.SUCCESS("✅ 1000 ta book muvaffaqiyatli yaratildi."))