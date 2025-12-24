from datetime import UTC
from datetime import datetime as bake
from logging import getLogger
from typing import BinaryIO

from httpx import AsyncClient as HttpxClient
from orjson import loads

from .utils import random_string, strtime, x_sig, x_signature
from .utils.exceptions import UnsuccessfulRequestError
from .utils.objects import (
    BaseProfile,
    Chat,
    FromCircleLink,
    FromShareLink,
    MuteDuration,
)
from .utils.wrappers import require_auth


class Client:
    def __init__(
        self,
        device_id: str | None = None,
        app_version: str | None = None,
        base_url: str | None = None,
        timezone: str | None = None,
        language: str | None = None,
        signature_secret: str | None = "9d93933f-7864-4872-96b2-9541ac03cf6c",
        http2: bool = False,
    ):
        self.logger = getLogger(__name__)
        self.auth_token = None
        if device_id is None:
            self.device_id = random_string()
            self.logger.warning(
                "Not providing the same device-id can lead to issues. Please grab a valid one and always use it. Also please note that the generation of device-id is experimental and may not work. We generated you this device-id: %s",
                self.device_id,
            )
        else:
            self.device_id = device_id
        if signature_secret is None:
            raise ValueError("signature_secret is required")
        else:
            self.signature_secret = signature_secret
        self.app_version = app_version or "4.135.671"
        self.base_url = base_url or "https://api.kyodo.app/v1/"
        self.timezone = timezone or "Europe/Minsk"
        self.language = language or "ru"
        self.http = HttpxClient(
            base_url=self.base_url,
            http2=http2,
            verify=False,
            headers={
                "User-Agent": "Kyodo/135 CFNetwork/3826.500.111.1.1 Darwin/24.4.0",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "application/json, text/plain, */*",
                "Connection": "keep-alive",
                "app-id": "ios app.kyodo.android/{}".format(self.app_version),
                "app-version": self.app_version,
                "device-id": self.device_id,
                "device-timezone": self.timezone,
                "device-language": self.language,
            },
        )
        self.base_profile: BaseProfile | None = None
        self.uid: str | None = None

    async def request(
        self,
        method: str,
        path: str,
        json: dict = {},
        headers: dict = {},
        **kwargs,
    ) -> dict:
        reqtime = strtime()
        additional_headers = {
            "x-signature": x_signature(self.device_id),
            "start-time": reqtime,
        } | headers
        if self.auth_token:
            additional_headers["Authorization"] = self.auth_token
            if not self.uid:
                self.logger.warning("No UID found! 'X-Sig' header will be missing.")
            else:
                additional_headers["x-sig"] = x_sig(
                    self.device_id, self.uid, reqtime, json
                )
        response = await self.http.request(
            method, path, json=json, headers=additional_headers, **kwargs
        )
        if response.status_code == 200:
            return loads(response.content)
        else:
            raise UnsuccessfulRequestError(response)

    async def login(self, email: str, password: str):
        response = await self.request(
            "POST",
            "g/s/auth/login",
            json={"type": 0, "email": email, "password": password},
        )
        self.auth_token = response["apiToken"]
        self.base_profile = BaseProfile(response.get("apiUser") or {})
        self.uid = response.get("apiUser", {}).get("id")
        return True

    @require_auth
    async def logout(self):
        await self.request(
            "POST",
            "g/s/auth/logout",
            json={},
        )
        self.auth_token = None
        return True

    @require_auth
    async def refresh_token(self):
        response = await self.request(
            "POST",
            "g/s/auth/login",
            json={"type": 1},
        )
        self.auth_token = response["apiToken"]
        return True

    @require_auth
    async def join_chat(self, circle_id: str, chat_id: str):
        await self.request(
            "POST",
            "{}/s/chats/{}/join".format(circle_id, chat_id),
            json={},
        )
        return True

    @require_auth
    async def leave_chat(self, circle_id: str, chat_id: str):
        await self.request(
            "POST",
            "{}/s/chats/{}/leave".format(circle_id, chat_id),
            json={},
        )
        return True

    @require_auth
    async def read_chat(self, circle_id: str, chat_id: str):
        await self.request(
            "POST",
            "{}/s/chats/{}/read".format(circle_id, chat_id),
            json={},
        )
        return True

    @require_auth
    async def join_circle(self, circle_id: str):
        await self.request(
            "POST",
            "{}/s/circles/join".format(circle_id),
            json={},
        )
        return True

    @require_auth
    async def leave_circle(self, circle_id: str):
        await self.request(
            "POST",
            "{}/s/circles/leave".format(circle_id),
            json={},
        )
        return True

    @require_auth
    async def send_entity_to_chat(
        self,
        circle_id: str,
        chat_id: str,
        entity: dict,
        reply_message_id: str | None = None,
        to_mention: list | None = None,
    ):
        try:
            entity["config"]["refId"] = random_string()
        except KeyError:
            raise Exception("Invalid entity, please check documentation")

        if reply_message_id:
            entity["config"]["replyMessageId"] = reply_message_id
        if to_mention:
            entity["config"]["mentionedUids"] = to_mention
            entity["config"]["mentionUids"] = to_mention
            entity["mentionUids"] = to_mention
            entity["mentionedUids"] = to_mention

        await self.request(
            "POST",
            "{}/s/chats/{}/messages".format(circle_id, chat_id),
            json=entity,
        )
        return True

    @require_auth
    async def send_message(
        self,
        circle_id: str,
        chat_id: str,
        message: str,
        reply_message_id: str | None = None,
        to_mention: list | None = None,
    ):
        entity = {"content": message, "config": {"type": 0}}
        return await self.send_entity_to_chat(
            circle_id,
            chat_id,
            entity,
            reply_message_id,
            to_mention,
        )

    @require_auth
    async def send_photo(
        self,
        circle_id: str,
        chat_id: str,
        link_to_photo: str,
        reply_message_id: str | None = None,
    ):
        entity = {"content": link_to_photo, "config": {"type": 2}}
        return await self.send_entity_to_chat(
            circle_id, chat_id, entity, reply_message_id
        )

    @require_auth
    async def send_video(
        self,
        circle_id: str,
        chat_id: str,
        link_to_photo: str,
        reply_message_id: str | None = None,
    ):
        entity = {"content": link_to_photo, "config": {"type": 3}}
        return await self.send_entity_to_chat(
            circle_id, chat_id, entity, reply_message_id
        )

    @require_auth
    async def delete_message(self, circle_id: str, chat_id: str, message_id: str):
        await self.request(
            "DELETE",
            "{}/s/chats/{}/messages/{}".format(circle_id, chat_id, message_id),
        )
        return True

    @require_auth
    async def get_joined_circles(self):
        return (
            await self.request(
                "GET",
                "g/s/accounts/joined-circles",
            )
        ).get("circleIds", ["g"])

    @require_auth
    async def get_circle(self, circle_id: str):
        return await self.request(
            "GET",
            "{}/s/circles".format(circle_id),
            json={},
        )

    @require_auth
    async def upload_media(self, file: BinaryIO, content_type: str, target: str):
        """
        Targets:
            - chat-message = image/jpg, image/png, image/gif
            - chat-video = video/mp4
        """
        return await self.request(
            "POST",
            "g/s/media/target/{}".format(target),
            data=file.read(),
            headers={"Content-Type": content_type},
        )

    async def decode_circle_link(self, link: str):
        code = link.split("/")[-1]
        return FromCircleLink(
            await self.request(
                "GET",
                "g/s/circles/vanities/{}".format(code),
            )
        )

    async def decode_link(self, link: str):
        code = link.split("/")[-1]
        if "s/c/" in link:
            raise ValueError("Link should be passed to decode_circle_link function")

        return FromShareLink(
            await self.request(
                "GET",
                "g/s/share-links/{}".format(code),
            )
        )

    @require_auth
    async def kick(self, circle_id: str, chat_id: str, user_id: str):
        await self.request(
            "DELETE",
            "{}/s/chats/{}/members/{}".format(circle_id, chat_id, user_id),
        )
        return True

    @require_auth
    async def unkick(self, circle_id: str, chat_id: str, user_id: str):
        await self.request(
            "POST",
            "{}/s/chats/{}/members/{}/unkick".format(circle_id, chat_id, user_id),
        )
        return True

    @require_auth
    async def edit_account_handle(self, handle: str):
        await self.request(
            "POST",
            "g/s/accounts/handle",
            json={"handle": handle},
        )
        return True

    @require_auth
    async def edit_profile(
        self, circle_id: str, nickname: str | None = None, bio: str | None = None
    ):
        data = {}
        if nickname:
            data["nickname"] = nickname
        if bio:
            data["bio"] = bio
        await self.request(
            "POST",
            "{}/s/users/{}/profile".format(circle_id, self.uid),
            json=data,
        )
        return True

    @require_auth
    async def join_voice_chat(self, circle_id: str, chat_id: str, join_type: str):
        """
        join_type:
        - speak: Join the voice chat as a speaker.
        - listen: Join the voice chat as a listener.
        """
        await self.request(
            "POST",
            "{}/s/chats/{}/live-activity/voice?joinType={}".format(
                circle_id, chat_id, join_type
            ),
            json={},
        )
        return True

    @require_auth
    async def voice_chat_join_permission(
        self, circle_id: str, chat_id: str, is_invite_only: bool = False
    ) -> bool:
        await self.request(
            "POST",
            "{}/s/chats/{}/live-activity/privacy".format(circle_id, chat_id),
            json={"privacy": 2 if is_invite_only else 0},
        )
        return True

    @require_auth
    async def get_user(self, circle_id: str, user_id: str) -> BaseProfile:
        return BaseProfile(
            (await self.request("GET", "{}/s/users/{}".format(circle_id, user_id))).get(
                "user"
            )
        )

    @require_auth
    async def get_chat(self, circle_id: str, chat_id: str) -> Chat:
        return Chat(
            (await self.request("GET", "{}/s/chats/{}".format(circle_id, chat_id))).get(
                "chat"
            )
        )

    @require_auth
    async def get_chat_members(
        self, circle_id: str, chat_id: str, start: int = 0, limit: int = 15
    ) -> list[BaseProfile]:
        members = (
            await self.request(
                "GET",
                "{}/s/chats/{}/members?start={}&limit={}".format(
                    circle_id, chat_id, start, limit
                ),
            )
        ).get("users")

        return [BaseProfile(user) for user in members]

    @require_auth
    async def mute_user(
        self, circle_id: str, user_id: str, reason: str, exp_time: MuteDuration
    ) -> bool:
        actual_time = bake.now(UTC) + exp_time.value
        await self.request(
            "POST",
            "{}/s/notices".format(circle_id),
            json={
                "uid": user_id,
                "content": reason,
                "muteExpTime": actual_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            },
        )
        return True

    @require_auth
    async def unmute_user(self, circle_id: str, user_id: str, reason: str) -> bool:
        await self.request(
            "POST",
            "{}/s/notices/mute/cancel".format(circle_id),
            json={
                "uid": user_id,
                "note": reason,
            },
        )
        return True

    @require_auth
    async def warn_user(self, circle_id: str, user_id: str, reason: str) -> bool:
        await self.request(
            "POST",
            "{}/s/notices".format(circle_id),
            json={
                "uid": user_id,
                "content": reason,
            },
        )
        return True

    @require_auth
    async def switch_ban_status(
        self, circle_id: str, user_id: str, reason: str = ""
    ) -> int:
        """
        Returns the new status of the user after switching the ban status.
        - 0 is unbanned
        - 1 is banned
        """
        result = await self.request(
            "POST", f"/{circle_id}/s/users/{user_id}/status", json={"note": reason}
        )
        data: dict = await result.json()
        return data["objectStatus"]
