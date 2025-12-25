import pytest

from JUSU.storage import generate_s3_presigned_post


class DummyClient:
    def generate_presigned_post(self, bucket, key, ExpiresIn=3600):
        return {"url": f"https://s3.example/{bucket}/{key}", "fields": {"key": key}}


def test_generate_presigned_post_with_client():
    c = DummyClient()
    data = generate_s3_presigned_post(c, "my-bucket", "uploads/1.json")
    assert "url" in data and "fields" in data


def test_raises_on_incorrect_client():
    class BadClient:
        pass

    with pytest.raises(RuntimeError):
        generate_s3_presigned_post(BadClient(), "b", "k")
