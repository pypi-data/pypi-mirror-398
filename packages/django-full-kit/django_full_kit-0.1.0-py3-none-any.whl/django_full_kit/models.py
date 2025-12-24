from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from utils.validators import validators
from .upload_paths import user_avatar_upload_path

User = get_user_model()

# --------------------------
# Advanced Fields
# --------------------------
class PhoneNumberField(models.CharField):
    """
    Custom Django model field for validating international phone numbers in E.164 format.
    Usage: like models.EmailField
    """
    default_validators = [
        validators.phone_number_validator
    ]

    description = "International phone number"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 16)
        super().__init__(*args, **kwargs)


class VideoField(models.FileField):
    """
    Custom Django model field for video
    Usage: like models.ImageField
    """
    default_validators = [
        validators.video_validator
    ]
    description = "support video"


class AudioField(models.FileField):
    """
    Custom Django model field for Audio
    Usage: like models.ImageField
    """
    default_validators = [
        validators.audio_validator
    ]
    description = "support audio"



# --------------------------
# Advanced Models
# --------------------------

# -------------
# User models
# -------------
class AdvancedBaseUser(AbstractUser):

    phone_number = PhoneNumberField(verbose_name=_("Phone number"),blank=True,null=True)
    bio = models.TextField(verbose_name=_("Biography"),blank=True,null=True)
    about = models.TextField(verbose_name=_("About"),blank=True,null=True,max_length=500)

    avatar = models.ImageField(verbose_name=_("Avatar"),upload_to=user_avatar_upload_path,blank=True,null=True)

    
    is_verify = models.BooleanField(verbose_name=_("Verify"),default=False)
    is_ban = models.BooleanField(verbose_name=_("Ban"),default=False)
    
    verify_date = models.DateTimeField(verbose_name=_("Verify date"),blank=True,null=True)
    ban_date = models.DateTimeField(verbose_name=_("Ban date"),blank=True,null=True)
    
    following = models.ManyToManyField("self",symmetrical=False,related_name="followers")
    
    def verify(self):
        self.is_verify = True
        self.verify_date = timezone.now()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        abstract = True

    def ban(self):
        self.is_ban = True
        self.ban_date = timezone.now()
    
    def get_followers(self):
        return self.followers.all()
    
    def get_following(self):
        return self.following.all()
    
    def get_full_name(self):
        return super().get_full_name()
    
    def get_short_name(self):
        return super().get_short_name()
    
    def __str__(self):
        return self.get_full_name or self.username

# -------------
# Blog models
# -------------
class BaseBlog(models.Model):
    """
    Blog model so that the author can have several different 
    blogs for their work, 
    such as https://www.blogsky.com/
    """
    name = models.CharField(verbose_name=_("Blog name"),max_length=110)
    content = models.TextField(verbose_name=_("Content"),blank=True,null=True)
    
    is_active = models.BooleanField(verbose_name=_("Active"),default=True)
    
    blogger = models.ForeignKey(User,on_delete=models.CASCADE,verbose_name=_("Blogger"))

    start_date = models.DateTimeField(verbose_name=_("Start date"),auto_now_add=True)
    last_update = models.DateTimeField(verbose_name=_("Last update"),auto_now=True)

    class Meta:
        verbose_name = _("Blog")
        verbose_name_plural = _("Blogs")
        abstract = True

    def __str__(self):
        return self.name