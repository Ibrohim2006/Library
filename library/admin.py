from django.contrib import admin
from django.utils.html import format_html
from .models import (
    GenreModel,
    BookModel,
    SavedBookModel,
    CommentModel,
    RatingModel,
    CommentLikeModel,
    SearchHistory,
)


# ============================================================================
# GENRE ADMIN
# ============================================================================
@admin.register(GenreModel)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created_at']
    search_fields = ['name', 'name_uz', 'name_ru', 'name_en']
    list_filter = ['created_at']


# ============================================================================
# BOOK ADMIN
# ============================================================================
@admin.register(BookModel)
class BookAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title', 'author', 'genre', 'year',
        'language', 'rating_display', 'stats_display',
        'image_preview'
    ]
    list_filter = ['genre', 'language', 'year', 'created_at']
    search_fields = [
        'title', 'author',
        'title_uz', 'title_ru', 'title_en',
        'author_uz', 'author_ru', 'author_en'
    ]
    readonly_fields = [
        'avg_rating', 'total_ratings',
        'total_saves', 'total_comments',
        'image_preview', 'created_at', 'updated_at'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'author', 'description', 'genre', 'year', 'language')
        }),
        ('Media', {
            'fields': ('image', 'image_preview', 'youtube_url')
        }),
        ('Links', {
            'fields': ('library_url', 'store_url')
        }),
        ('Statistics (Auto-calculated)', {
            'fields': ('avg_rating', 'total_ratings', 'total_saves', 'total_comments'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def rating_display(self, obj):
        if obj.avg_rating:
            stars = '⭐' * int(obj.avg_rating)
            return format_html(
                '<span title="{}/5">{} {:.2f}</span>',
                obj.avg_rating, stars, obj.avg_rating
            )
        return '—'

    rating_display.short_description = 'Rating'

    def stats_display(self, obj):
        return format_html(
            '💾 {} | 💬 {} | ⭐ {}',
            obj.total_saves, obj.total_comments, obj.total_ratings
        )

    stats_display.short_description = 'Stats'

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 200px;" />',
                obj.image.url
            )
        return '—'

    image_preview.short_description = 'Preview'


# ============================================================================
# SAVED BOOK ADMIN
# ============================================================================
@admin.register(SavedBookModel)
class SavedBookAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_display', 'book', 'status',
        'is_active', 'created_at'
    ]
    list_filter = ['status', 'is_active', 'created_at']
    search_fields = ['user__email', 'book__title', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['user', 'book']

    def user_display(self, obj):
        return obj.user.email

    user_display.short_description = 'User'


# ============================================================================
# COMMENT ADMIN
# ============================================================================
@admin.register(CommentModel)
class CommentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_display', 'book', 'text_preview',
        'status', 'likes_count', 'is_active', 'created_at'
    ]
    list_filter = ['status', 'is_active', 'created_at']
    search_fields = ['user__email', 'book__title', 'text']
    readonly_fields = [
        'likes_count', 'is_edited', 'edited_at',
        'created_at', 'updated_at'
    ]
    raw_id_fields = ['user', 'book', 'parent']
    actions = ['approve_comments', 'reject_comments', 'mark_as_spam']

    def user_display(self, obj):
        return obj.user.email

    user_display.short_description = 'User'

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text

    text_preview.short_description = 'Comment'

    def approve_comments(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} comments approved.')

    approve_comments.short_description = 'Approve selected comments'

    def reject_comments(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} comments rejected.')

    reject_comments.short_description = 'Reject selected comments'

    def mark_as_spam(self, request, queryset):
        updated = queryset.update(status='spam')
        self.message_user(request, f'{updated} comments marked as spam.')

    mark_as_spam.short_description = 'Mark as spam'


# ============================================================================
# RATING ADMIN
# ============================================================================
@admin.register(RatingModel)
class RatingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_display', 'book', 'stars_display',
        'has_review', 'is_active', 'created_at'
    ]
    list_filter = ['stars', 'is_active', 'created_at']
    search_fields = ['user__email', 'book__title', 'review_text']
    readonly_fields = ['previous_rating', 'created_at', 'updated_at']
    raw_id_fields = ['user', 'book']

    def user_display(self, obj):
        return obj.user.email

    user_display.short_description = 'User'

    def stars_display(self, obj):
        return '⭐' * obj.stars

    stars_display.short_description = 'Rating'

    def has_review(self, obj):
        return '✓' if obj.review_text else '—'

    has_review.short_description = 'Review'


# ============================================================================
# COMMENT LIKE ADMIN
# ============================================================================
@admin.register(CommentLikeModel)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_display', 'comment_preview',
        'is_like', 'created_at'
    ]
    list_filter = ['is_like', 'created_at']
    search_fields = ['user__email', 'comment__text']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['user', 'comment']

    def user_display(self, obj):
        return obj.user.email

    user_display.short_description = 'User'

    def comment_preview(self, obj):
        text = obj.comment.text
        return text[:30] + '...' if len(text) > 30 else text

    comment_preview.short_description = 'Comment'


# ============================================================================
# SEARCH HISTORY ADMIN
# ============================================================================
@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_display', 'query', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'query']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['user']
    date_hierarchy = 'created_at'

    def user_display(self, obj):
        return obj.user.email

    user_display.short_description = 'User'