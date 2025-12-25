class MockAPIClient:  # This class is used to mock an api.
    def __init__(self, userid, token, proxies) -> None:
        self._data = {}
        self.userid = userid
        self.token = token

    def push(self, content: str, to_userid: str):
        print(f"TestPusher Mock Push: to {to_userid}: {content}")
