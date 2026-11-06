"""The web demo endpoints."""

import pytest
from starlette.testclient import TestClient

from src.samples import SAMPLES, make_sample
from src.web import MAX_UPLOAD_BYTES, app

client = TestClient(app)


def test_home_page_has_demo():
    r = client.get("/")
    assert r.status_code == 200
    assert 'id="try"' in r.text and "/api/check" in r.text


def test_samples_listed_and_served():
    listed = client.get("/api/samples").json()
    assert [s["name"] for s in listed] == [s.name for s in SAMPLES]
    r = client.get("/api/sample/good")
    assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg"


def test_unknown_sample_404():
    assert client.get("/api/sample/nope").status_code == 404


@pytest.mark.parametrize("sample", SAMPLES, ids=lambda s: s.name)
def test_check_raw_upload(sample):
    r = client.post("/api/check", content=make_sample(sample.name), headers={"content-type": "image/jpeg"})
    assert r.status_code == 200
    assert r.json()["verdict"] == sample.expected


def test_check_multipart_upload():
    r = client.post("/api/check", files={"file": ("eye.jpg", make_sample("good"), "image/jpeg")})
    assert r.status_code == 200
    assert r.json()["verdict"] == "accept" and r.json()["image_url"] == "eye.jpg"


def test_not_an_image_is_a_reject_report_not_a_500():
    r = client.post("/api/check", content=b"hello world", headers={"content-type": "text/plain"})
    assert r.status_code == 200 and r.json()["verdict"] == "reject"


def test_empty_body_is_400():
    assert client.post("/api/check", content=b"").status_code == 400


def test_oversized_upload_is_413():
    r = client.post("/api/check", content=b"x" * (MAX_UPLOAD_BYTES + 1))
    assert r.status_code == 413
