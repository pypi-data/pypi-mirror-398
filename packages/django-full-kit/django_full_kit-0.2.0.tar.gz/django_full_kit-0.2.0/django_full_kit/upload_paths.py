from django.utils import timezone

def user_avatar_upload_path(instance,filename):
    now = timezone.now()

    date_part = now.strftime("%Y%m%d%S")
    user = instance.id or "new"
    return f"users/avatars/{user}/{date_part}/{filename}"

def article_thumbnail_upload_path(instance,filename):
    now = timezone.now()

    date_part = now.strftime("%Y%m%d%S")
    article = instance.id or "new"
    return f"users/avatars/{article}/{date_part}/{filename}"