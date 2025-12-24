from httpx import Response


class NeedAuthError(Exception):
    pass


class UnsuccessfulRequestError(Exception):
    def __init__(self, response: Response):
        self.body = response.content
        try:
            self.json = response.json()
            self.message = self.json.get("message") or "Unknown error with request"
            self.code = self.json.get("code") or 0
            self.apiCode = self.json.get("apiCode") or 0
        except Exception:
            self.json = {}
            self.message = "Unknown error with request"
            self.code = 0
            self.apiCode = 0

        super().__init__(self.message, self.code, self.apiCode, self.body, self.json)
