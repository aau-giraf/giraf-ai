def test_health(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["providers"]["image"] is True
    assert data["providers"]["tts"] is True


def test_generate_image_requires_auth(client):
    resp = client.post("/api/v1/generate/image", json={"prompt": "test"})
    assert resp.status_code == 401


def test_generate_image(client, auth_header):
    resp = client.post(
        "/api/v1/generate/image",
        json={"prompt": "lasagna"},
        headers=auth_header,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["image_base64"]
    assert data["format"] == "png"
    assert data["provider"] == "mock"


def test_tts_synthesize(client, auth_header):
    resp = client.post(
        "/api/v1/tts",
        json={"text": "Lasagne", "language": "da"},
        headers=auth_header,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["audio_base64"]
    assert data["provider"] == "mock"


def test_tts_voices(client, auth_header):
    resp = client.get("/api/v1/tts/voices?language=da", headers=auth_header)
    assert resp.status_code == 200
    voices = resp.json()
    assert len(voices) >= 1


def test_tts_requires_auth(client):
    resp = client.post("/api/v1/tts", json={"text": "test"})
    assert resp.status_code == 401
