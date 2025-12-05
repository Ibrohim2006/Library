from django.db import models

# Create your models here.
class Book(models.Model):
    title=models.CharField(max_length=200)
    author=models.CharField(max_length=200)
    cover=models.URLField()
    rating=models.FloatField()
    pages=models.IntegerField()
    language=models.CharField(max_length=200)
    description=models.TextField()

    def __str__(self):
        return self.title

class Review(models.Model):
    book=models.ForeignKey(Book, on_delete=models.CASCADE, related_name='review')
    username=models.CharField(max_length=200)
    stars=models.IntegerField()
    comment=models.TextField()

    def __str__(self):
        return f"{self.username}-{self.book}"

class Saved(models.Model):
    user_id=models.IntegerField()
    book=models.ForeignKey(Book, on_delete=models.CASCADE)

