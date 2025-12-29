class RemoteIO:
    url: str

    def __init__(self, url: str):
        self.url = url

    def __str__(self):
        return self.url

    def __repr__(self):
        return self.url
