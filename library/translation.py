from modeltranslation.translator import register, TranslationOptions
from .models import BookModel, GenreModel


@register(GenreModel)
class GenreTranslationOptions(TranslationOptions):
    fields = ("name",)

@register(BookModel)
class BookTranslationOptions(TranslationOptions):
    fields = ("title", "author", "description")
