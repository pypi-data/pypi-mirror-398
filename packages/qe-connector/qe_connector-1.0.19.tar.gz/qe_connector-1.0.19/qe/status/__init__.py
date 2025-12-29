from qe.api import API


class Status(API):
    def __init__(self, api_key=None, api_secret=None, **kwargs):
        if "base_url" not in kwargs:
            kwargs["base_url"] = "https://api.quantumexecute.com"
        super().__init__(api_key, api_secret, **kwargs)

    # PUBLIC
    from qe.status.ping import ping
    from qe.status.timestamp import timestamp