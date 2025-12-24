from datetime import timedelta
from enum import Enum


class Title:
    def __init__(self, data: dict):
        self.data = data
        self.slug = self.data.get("slug", "")
        self.text = self.data.get("text", "")
        self.isGlobal = self.data.get("global", False)
        self.bgColor = self.data.get("bgColor", "")
        self.fontColor = self.data.get("fontColor", "")


class BaseProfile:
    """
    User profile object
    """

    def __init__(self, data: dict):
        self.data = data
        self.id = self.data.get("id") or ""
        self.intId = self.data.get("intId") or 0
        self.circleId = self.data.get("circleId") or ""
        self.banner = self.data.get("banner") or ""
        self.bannerTheme = self.data.get("bannerTheme") or {}
        self.avatar = self.data.get("avatar") or ""
        self.nickname = self.data.get("nickname") or ""
        self.handle = self.data.get("handle") or ""
        self.globalRole = self.gRole = self.data.get("gRole") or 0
        self.role = UserRole(self.data.get("role") or 0)
        self.botType = self.data.get("botType") or 0
        self.premiumType = self.data.get("premiumType") or 0
        self.globalStatus = self.gStatus = self.data.get("gStatus") or 0
        self.status = self.data.get("status") or 0
        self.badgeFlags = self.data.get("badgeFlags") or 0
        self.isVerified = self.data.get("isVerified") or False
        self.titles = [Title(title) for title in (self.data.get("titles") or [])]
        self.joined = self.data.get("joined") or False
        self.adminInfo = self.data.get("adminInfo") or {}
        self.isOnline = self.data.get("isOnline") or False
        self.lastOnline = self.data.get("lastOnline") or ""

    def __str__(self):
        return "BaseProfile(id={}, intId={}, circleId={})".format(
            self.id, self.intId, self.circleId
        )


class Message:
    """
    Message object
    """

    def __init__(self, data: dict):
        self.data = data
        self.chatId = self.data.get("chatId") or ""
        self.circleId = self.data.get("circleId") or ""
        self.mentionedUids = self.data.get("mentionedUids") or []

        self.fullMessage = self.data.get("message") or {}
        self.message = self.content = self.fullMessage.get("content") or ""
        self.messageId = self.id = self.fullMessage.get("id") or ""
        self.circleId = self.fullMessage.get("circleId") or ""
        self.chatId = self.fullMessage.get("chatId") or ""
        self.authorId = self.fullMessage.get("uid") or ""
        self.author = BaseProfile(self.fullMessage.get("author") or {})
        self.messageType = self.fullMessage.get("type") or 0
        self.messageStatus = self.status = self.fullMessage.get("status") or 0
        self.stickerId = self.fullMessage.get("stickerId")
        self.createdTime = self.fullMessage.get("createdTime") or ""

    def __str__(self):
        return "Message(id={}, chatId={}, authorId={}, circleId={}, createdTime={})".format(
            self.id, self.chatId, self.authorId, self.circleId, self.createdTime
        )


class FromCircleLink:
    def __init__(self, data: dict):
        self.data = data
        self.id = self.circleId = data.get("id") or ""

    def __str__(self):
        return "FromCircleLink(id={})".format(self.circleId)


class FromShareLink:
    def __init__(self, data: dict):
        self.data = data
        self.isCircleJoined = self.data.get("isCircleJoined") or False

        self.shareLinkData = self.data.get("shareLink") or {}
        self.id = self.shareLinkData.get("id") or ""
        self.circleId = self.shareLinkData.get("circleId") or ""
        self.objectId = self.shareLinkData.get("objectId") or ""
        self.objectType = self.shareLinkData.get("objectType") or 0
        self.shareLink = self.shareLinkData.get("shareLink") or ""
        self.isVanity = self.shareLinkData.get("isVanity") or False
        self.createdTime = self.shareLinkData.get("createdTime") or ""
        self.updatedTime = self.shareLinkData.get("updatedTime") or ""

    def __str__(self):
        return "FromShareLink(id={})".format(
            self.id,
        )


class UserRole(Enum):
    """Role in a circle"""

    USER = 0
    MODERATOR = 1
    ADMIN = 2
    OWNER = 3


class ChatType(Enum):
    """Type of chat"""

    PRIVATE = 0
    GROUP = 1
    PUBLIC = 2


class Chat:
    def __init__(self, data: dict):
        self.data = data

        self.host = BaseProfile(self.data.get("host"))
        self.hostId = self.data.get("hostId") or ""
        self.coHostIds: list[str] = self.data.get("coHostIds") or []
        self.admins: list[str] = [self.hostId] + self.coHostIds
        self.id = self.data.get("id") or ""
        self.circleId = self.data.get("circleId") or ""
        self.icon = self.data.get("icon") or ""
        self.background = self.data.get("background") or ""
        self.condition = self.data.get("condition") or 0
        self.type = ChatType(self.data.get("type") or 0)
        self.status = self.data.get("status") or 0
        self.activityType = self.data.get("activityType") or 0
        self.activityPrivacy = self.data.get("activityPrivacy") or 0
        self.specialBadge = self.data.get("specialBadge") or 0
        self.memberSummary = [
            BaseProfile(member) for member in (self.data.get("memberSummary") or [])
        ]
        self.memberCount = self.data.get("memberCount") or 0
        self.memberLimit = self.data.get("memberLimit") or 0
        self.readOnly = self.data.get("readOnly") or False


class MuteDuration(Enum):
    ONE_HOUR = timedelta(hours=1)
    SIX_HOURS = timedelta(hours=6)
    ONE_DAY = timedelta(days=1)
    THREE_DAYS = timedelta(days=3)
    SEVEN_DAYS = timedelta(days=7)
