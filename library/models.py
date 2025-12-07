from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from authentication.models import UserModel
from core.base import BaseModel

LANGUAGE_CHOICES = (
    ("en", "English"),
    ("ru", "Russian"),
    ("uz", "Uzbek"),
)


# ============================================================================
# GENRE MODEL
# ============================================================================
class GenreModel(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "genre"
        verbose_name_plural = "Genres"
        verbose_name = "Genre"


# ============================================================================
# BOOK MODEL
# ============================================================================
class BookModel(BaseModel):
    author = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    description = models.TextField()
    genre = models.ForeignKey(
        GenreModel,
        on_delete=models.CASCADE,
        related_name="book_genre"
    )
    year = models.PositiveIntegerField()
    language = models.CharField(
        max_length=20,
        choices=LANGUAGE_CHOICES,
        default="en"
    )
    image = models.ImageField(upload_to="book/image")
    youtube_url = models.URLField(blank=True, null=True)
    library_url = models.URLField(blank=True, null=True)
    store_url = models.URLField(blank=True, null=True)

    # Cached denormalized fields - performance uchun
    avg_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("Average Rating")
    )
    total_ratings = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Total Ratings")
    )
    total_saves = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Total Saves")
    )
    total_comments = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Total Comments")
    )

    def __str__(self):
        return f"{self.title} ({self.author})"

    class Meta:
        db_table = "book"
        verbose_name_plural = "Books"
        verbose_name = "Book"
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['author']),
            models.Index(fields=['genre']),
            models.Index(fields=['avg_rating']),
            models.Index(fields=['-created_at']),
        ]


# ============================================================================
# SAVED BOOKS MODEL
# ============================================================================
class SavedBookManager(models.Manager):
    """Custom manager for SavedBookModel"""

    def active(self):
        return self.filter(is_active=True)

    def for_user(self, user):
        return self.active().filter(user=user)

    def reading_now(self, user):
        return self.for_user(user).filter(status='currently_reading')

    def want_to_read(self, user):
        return self.for_user(user).filter(status='want_to_read')

    def finished(self, user):
        return self.for_user(user).filter(status='finished')


class SavedBookModel(BaseModel):
    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name="saved_books",
        verbose_name=_("User"),
        db_index=True
    )
    book = models.ForeignKey(
        BookModel,
        on_delete=models.CASCADE,
        related_name="saved_by_users",
        verbose_name=_("Book"),
        db_index=True
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes"),
        help_text=_("Personal notes about this book")
    )

    READING_STATUS = (
        ('want_to_read', _('Want To Read')),
        ('currently_reading', _('Currently Reading')),
        ('finished', _('Finished')),
    )
    status = models.CharField(
        choices=READING_STATUS,
        max_length=20,
        default='want_to_read',
        verbose_name=_('Reading Status'),
        db_index=True
    )
    is_active = models.BooleanField(default=True, db_index=True)

    # Custom manager
    objects = SavedBookManager()

    class Meta:
        db_table = "saved_books"
        verbose_name = _("Saved Book")
        verbose_name_plural = _("Saved Books")
        unique_together = ('user', 'book')
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['book', 'is_active']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['-created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} saved {self.book.title}"

    def save(self, *args, **kwargs):
        self.full_clean()
        is_new = not self.pk
        super().save(*args, **kwargs)

        # Update book's total_saves counter
        if is_new:
            self.book.total_saves = SavedBookModel.objects.filter(
                book=self.book,
                is_active=True
            ).count()
            self.book.save(update_fields=['total_saves'])

    def clean(self):
        # Check if book is already saved by user
        if not self.pk:
            if SavedBookModel.objects.filter(
                    user=self.user,
                    book=self.book,
                    is_active=True
            ).exists():
                raise ValidationError(
                    _("You have already saved this book.")
                )


# ============================================================================
# COMMENT MODEL
# ============================================================================
class CommentManager(models.Manager):
    """Custom manager for CommentModel"""

    def active(self):
        return self.filter(is_active=True)

    def approved(self):
        return self.active().filter(status='approved')

    def for_book(self, book):
        return self.approved().filter(book=book, parent=None)

    def pending_moderation(self):
        return self.active().filter(status='pending')


class CommentModel(BaseModel):
    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("User"),
        db_index=True
    )
    book = models.ForeignKey(
        BookModel,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("Book"),
        db_index=True
    )
    text = models.TextField(
        verbose_name=_("Comment text"),
        help_text=_("Maximum 1000 characters")
    )

    # Reply functionality (nested comments)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name=_("Parent comment")
    )

    # Moderation
    MODERATION_STATUS = (
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('spam', _('Spam')),
    )
    status = models.CharField(
        max_length=20,
        choices=MODERATION_STATUS,
        default='approved',
        db_index=True,
        verbose_name=_("Status")
    )

    # Engagement metrics
    likes_count = models.PositiveIntegerField(default=0)

    # Soft delete
    is_active = models.BooleanField(default=True, db_index=True)

    # Edited tracking
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)

    # Custom manager
    objects = CommentManager()

    class Meta:
        db_table = "comments"
        verbose_name = _("Comment")
        verbose_name_plural = _("Comments")
        indexes = [
            models.Index(fields=['book', 'is_active', 'status']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['parent']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} on {self.book.title}: {self.text[:50]}"

    def clean(self):
        # Text length check
        if len(self.text) > 1000:
            raise ValidationError(
                _("Comment must be less than 1000 characters")
            )

        # Prevent deeply nested comments (max 2 levels)
        if self.parent and self.parent.parent:
            raise ValidationError(
                _("Comments can only be nested 2 levels deep")
            )

        # Simple spam check
        spam_words = ['spam', 'casino', 'viagra']
        if any(word in self.text.lower() for word in spam_words):
            self.status = 'spam'

    def save(self, *args, **kwargs):
        from django.utils import timezone

        # Track edits
        if self.pk:
            old_instance = CommentModel.objects.get(pk=self.pk)
            if old_instance.text != self.text:
                self.is_edited = True
                self.edited_at = timezone.now()

        self.full_clean()
        is_new = not self.pk
        super().save(*args, **kwargs)

        # Update book's total_comments counter
        if is_new:
            self.book.total_comments = CommentModel.objects.filter(
                book=self.book,
                is_active=True,
                status='approved'
            ).count()
            self.book.save(update_fields=['total_comments'])

    @property
    def replies_count(self):
        return self.replies.filter(
            is_active=True,
            status='approved'
        ).count()


# ============================================================================
# RATING MODEL
# ============================================================================
class RatingManager(models.Manager):
    """Custom manager for RatingModel"""

    def active(self):
        return self.filter(is_active=True)

    def for_book(self, book):
        return self.active().filter(book=book)

    def by_user(self, user):
        return self.active().filter(user=user)


class RatingModel(BaseModel):
    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name="ratings",
        verbose_name=_("User"),
        db_index=True
    )
    book = models.ForeignKey(
        BookModel,
        on_delete=models.CASCADE,
        related_name="ratings",
        verbose_name=_("Book"),
        db_index=True
    )
    stars = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1, message=_("Minimum rating is 1")),
            MaxValueValidator(5, message=_("Maximum rating is 5"))
        ],
        verbose_name=_("Rating (1-5 stars)")
    )
    review_text = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Review"),
        help_text=_("Optional detailed review")
    )
    previous_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Previous rating")
    )
    is_active = models.BooleanField(default=True, db_index=True)

    # Custom manager
    objects = RatingManager()

    class Meta:
        db_table = "ratings"
        verbose_name = _("Rating")
        verbose_name_plural = _("Ratings")
        unique_together = ("user", "book")
        indexes = [
            models.Index(fields=['book', 'is_active']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['stars']),
            models.Index(fields=['-created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} rated {self.book.title}: {self.stars}★"

    def clean(self):
        if self.stars < 1 or self.stars > 5:
            raise ValidationError(_("Rating must be between 1 and 5"))

    def save(self, *args, **kwargs):
        # Track rating changes
        if self.pk:
            old_instance = RatingModel.objects.get(pk=self.pk)
            if old_instance.stars != self.stars:
                self.previous_rating = old_instance.stars

        self.full_clean()
        super().save(*args, **kwargs)

        # Update book's average rating
        self.update_book_average()

    def update_book_average(self):
        """Update book's average rating and count"""
        from django.db.models import Avg, Count

        stats = RatingModel.objects.filter(
            book=self.book,
            is_active=True
        ).aggregate(
            avg=Avg('stars'),
            count=Count('id')
        )

        self.book.avg_rating = round(stats['avg'], 2) if stats['avg'] else None
        self.book.total_ratings = stats['count']
        self.book.save(update_fields=['avg_rating', 'total_ratings'])


# ============================================================================
# COMMENT LIKE MODEL
# ============================================================================
class CommentLikeModel(BaseModel):
    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name="comment_likes",
        db_index=True
    )
    comment = models.ForeignKey(
        CommentModel,
        on_delete=models.CASCADE,
        related_name="likes",
        db_index=True
    )
    is_like = models.BooleanField(
        default=True,
        help_text=_("True=Like, False=Dislike")
    )

    class Meta:
        db_table = "comment_likes"
        verbose_name = _("Comment Like")
        verbose_name_plural = _("Comment Likes")
        unique_together = ("user", "comment")
        indexes = [
            models.Index(fields=['comment', 'is_like']),
        ]

    def __str__(self):
        action = "liked" if self.is_like else "disliked"
        return f"{self.user.email} {action} comment"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update comment's likes_count
        self.comment.likes_count = self.comment.likes.filter(
            is_like=True
        ).count()
        self.comment.save(update_fields=['likes_count'])


# ============================================================================
# SEARCH HISTORY
# ============================================================================
class SearchHistory(BaseModel):
    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name="search_histories"
    )
    query = models.CharField(max_length=255)

    class Meta:
        db_table = "search_history"
        verbose_name = "Search history"
        verbose_name_plural = "Search histories"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user} – {self.query[:10]}"


# ============================================================================
# SEARCH REQUEST MODEL
# ============================================================================
class SearchRequestModel(BaseModel):
    query = models.CharField(max_length=255)
    language = models.CharField(
        max_length=15,
        choices=LANGUAGE_CHOICES,
        default="uz"
    )

    class Meta:
        db_table = "search_request"
        verbose_name = "Search request"
        verbose_name_plural = "Search requests"

    def __str__(self):
        return f"{self.query} ({self.language})"


# ============================================================================
# FILTER REQUEST MODEL
# ============================================================================
class FilterRequestModel(BaseModel):
    author = models.CharField(max_length=255, null=True, blank=True)
    genre = models.CharField(max_length=255, null=True, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    language = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        null=True,
        blank=True
    )
    search_term = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "filter_request"
        verbose_name = "Filter request"
        verbose_name_plural = "Filter requests"

    def __str__(self):
        return f"Filter(author={self.author}, genre={self.genre}, year={self.year}, lang={self.language})"