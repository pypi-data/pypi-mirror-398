from django.utils import timezone

def user_avatar_upload_path(instance,filename):
    now = timezone.now()

    date_part = now.strftime("%Y%m%d%S")
    user = instance.id or "new"
    return f"users/avatars/{instance.id}/{date_part}/{filename}"