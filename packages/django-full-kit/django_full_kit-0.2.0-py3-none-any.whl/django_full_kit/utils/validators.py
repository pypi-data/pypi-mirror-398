from django.core.validators import FileExtensionValidator,RegexValidator
from django.utils.translation import gettext_lazy as _


# --------------------------
# Charecter validators
# --------------------------
phone_number_validator = RegexValidator(
    regex=r'^\+[1-9]\d{1,14}$',
    message=_("Phone number must be entered in E.164 format (e.g. +989123456789).")
)
# --------------------------
# File validators
# --------------------------
video_validator = FileExtensionValidator(
    allowed_extensions = [
    "mp4", "mkv", "mov", "avi", "wmv", "flv", "webm", "mpeg", "mpg",
    "mpe", "m2v", "m2ts", "mts", "ts", "vob", "3gp", "3g2", "f4v",
    "f4p", "f4a", "f4b", "ogv", "rm", "rmvb", "asf", "divx", "xvid",
    "mxf", "gxf", "mjpg", "mj2", "qt", "dv", "hdv", "avchd", "h264",
    "h265", "hevc", "vp8", "vp9", "av1", "yuv", "y4m", "bik", "smk",
    "drc", "amv", "nsv", "m4v", "ismv", "isma", "wtv", "dvr-ms",
    "ivf", "tsv", "mng"
    ],
    message=_("You can only use video")
)   

audio_validator = FileExtensionValidator(
    allowed_extensions = [
    "mp3", "wav", "aac", "ogg", "flac", "alac", "wma", "aiff", "aif",
    "aifc", "amr", "m4a", "m4b", "m4p", "m4r", "m4v", "mp2", "mp1",
    "opus", "ac3", "dts", "pcm", "caf", "ra", "rm", "ram", "vqf",
    "au", "snd", "gsm", "mid", "midi", "rmi", "kar", "spx", "tta",
    "wv", "ape", "mpc", "vqf", "s3m", "xm", "it", "mod", "mtm",
    "dsd", "dsf", "dff", "brstm", "adx", "ast", "hca", "at3",
    "voc", "ivs", "ivf", "fla", "oga", "mogg", "8svx", "16svx"
    ],
    message=_("You can only use audio")
)

# --------------------------
# Url Validators
# --------------------------
github_url_validator = RegexValidator(
    regex=r"^(https?:\/\/)?(www\.)?github\.com(\/.*)?$",
    message=_("Enter a valid GitHub URL.")
)
gitlab_url_validator = RegexValidator(
    regex=r"^(https?:\/\/)?(www\.)?gitlab\.com(\/.*)?$",
    message=_("Enter a valid GitLab URL.")
)
