"""
Django signals for automatic counter updates.

Usage: Bu faylni library/apps.py ga import qiling:

# library/apps.py
from django.apps import AppConfig

class LibraryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'library'

    def ready(self):
        import library.signals  # Import signals
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db.models import Avg, Count
from .models import RatingModel, CommentModel, SavedBookModel, CommentLikeModel


# ============================================================================
# RATING SIGNALS - Automatic average rating updates
# ============================================================================
@receiver(post_save, sender=RatingModel)
@receiver(post_delete, sender=RatingModel)
def update_book_rating_stats(sender, instance, **kwargs):
    """
    Automatically update book's avg_rating and total_ratings
    when a rating is created, updated, or deleted.
    """
    book = instance.book

    # Calculate stats
    stats = RatingModel.objects.filter(
        book=book,
        is_active=True
    ).aggregate(
        avg=Avg('stars'),
        count=Count('id')
    )

    # Update book
    book.avg_rating = round(stats['avg'], 2) if stats['avg'] else None
    book.total_ratings = stats['count']
    book.save(update_fields=['avg_rating', 'total_ratings'])


# ============================================================================
# COMMENT SIGNALS - Automatic comment count updates
# ============================================================================
@receiver(post_save, sender=CommentModel)
@receiver(post_delete, sender=CommentModel)
def update_book_comment_count(sender, instance, **kwargs):
    """
    Automatically update book's total_comments
    when a comment is created, updated, or deleted.
    """
    book = instance.book

    # Count approved and active comments
    count = CommentModel.objects.filter(
        book=book,
        is_active=True,
        status='approved'
    ).count()

    book.total_comments = count
    book.save(update_fields=['total_comments'])


# ============================================================================
# SAVED BOOK SIGNALS - Automatic save count updates
# ============================================================================
@receiver(post_save, sender=SavedBookModel)
@receiver(post_delete, sender=SavedBookModel)
def update_book_save_count(sender, instance, **kwargs):
    """
    Automatically update book's total_saves
    when a book is saved or unsaved by a user.
    """
    book = instance.book

    # Count active saves
    count = SavedBookModel.objects.filter(
        book=book,
        is_active=True
    ).count()

    book.total_saves = count
    book.save(update_fields=['total_saves'])


# ============================================================================
# COMMENT LIKE SIGNALS - Automatic like count updates
# ============================================================================
@receiver(post_save, sender=CommentLikeModel)
@receiver(post_delete, sender=CommentLikeModel)
def update_comment_like_count(sender, instance, **kwargs):
    """
    Automatically update comment's likes_count
    when a like/dislike is created or deleted.
    """
    comment = instance.comment

    # Count only likes (is_like=True)
    count = CommentLikeModel.objects.filter(
        comment=comment,
        is_like=True
    ).count()

    comment.likes_count = count
    comment.save(update_fields=['likes_count'])

# ============================================================================
# OPTIMIZATION: Prevent recursive saves
# ============================================================================
# Yuqoridagi signallar book.save() chaqiradi, lekin bu BookModel uchun
# signal yaratmaydi chunki biz faqat specific fieldlarni update qilyapmiz
# (update_fields parametri bilan)