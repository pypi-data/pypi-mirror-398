from dataclasses import dataclass


@dataclass
class MockURL:
    path: str


@dataclass
class MockAttributes:
    state: str
    url: MockURL


@dataclass
class MockData:
    id: str
    attributes: MockAttributes


class MockAssetResponse:
    def __init__(self, asset_id=None, state=None, url=None):
        self.data = MockData(id=asset_id, attributes=MockAttributes(state=state, url=MockURL(path=url)))


class MockUploader:
    """Mock uploader, can be used for testing. Doesn't do anything instead of uploading a file."""

    def upload(self, file_to_upload: str, upload_url: str):
        pass
