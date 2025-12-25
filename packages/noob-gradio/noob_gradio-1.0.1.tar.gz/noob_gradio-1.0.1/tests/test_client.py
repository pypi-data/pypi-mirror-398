import aiohttp
import pytest
from noob_gradio.client import Client, NoSessionError, handle_file


@pytest.mark.asyncio
async def test_connect_and_close():
    client = Client("https://example.com")
    await client.connect()
    assert isinstance(client.session, aiohttp.ClientSession)
    await client.close()
    assert client.session is None


def test_handle_file_local(tmp_path):
    f = tmp_path / "example.txt"
    f.write_text("data")
    data = handle_file(f)
    assert "path" in data and "orig_name" in data
    assert data["meta"]["_type"] == "gradio.FileData"


def test_handle_file_url():
    data = handle_file("https://example.com/file.png")
    assert data["url"] == "https://example.com/file.png"


@pytest.mark.asyncio
async def test_get_json(monkeypatch):
    client = Client("https://example.com")
    await client.connect()

    def fake_get(url):
        class FakeResp:
            status = 200

            async def json(self):
                return {"ok": True}

            async def __aenter__(self): return self
            async def __aexit__(self, *a): pass
            def raise_for_status(self): pass
        return FakeResp()

    monkeypatch.setattr(client.session, "get", fake_get)
    result = await client._get_json("https://example.com/config")
    assert result == {"ok": True}
    await client.close()


fake_cache = {
    "https://example.com": {
        "api_info": {"named_endpoints": {
            "test": {"parameters": [{"parameter_name": "x", "python_type": {"type": "int"}}]},
        }},
    },
}


@pytest.mark.asyncio
async def test_predict_type_check(monkeypatch):
    """Check that type mismatch raises TypeError"""
    client = Client("https://example.com")
    await client.connect()
    client._space_cache = fake_cache

    async def fake_resolve(api_name, base): return 0
    monkeypatch.setattr(client, "_resolve_fn_index", fake_resolve)
    with pytest.raises(TypeError):
        await client.predict(api_name="test", x="not-an-int")
    await client.close()


@pytest.mark.asyncio
async def test_predict_success(monkeypatch):
    """Check that correct types pass and return mocked response"""
    client = Client("https://example.com")
    client._space_cache = fake_cache

    async def fake_resolve(api_name, base): return 0

    def fake_post(url, json):
        class FakeResp:
            status = 200

            async def json(self):
                return {}

            async def __aenter__(self): return self
            async def __aexit__(self, *a): pass
        return FakeResp()

    class FakeStreamResp:
        async def content_iterator(self):
            # Simulate SSE messages as bytes
            yield b'data: {"msg": "process_starts"}\n\n'
            yield b'data: {"msg": "process_completed", "success": true, "output": {"data": {"result": "success"}}}\n\n'

        @property
        def content(self):
            return self

        async def __aiter__(self):
            async for chunk in self.content_iterator():
                yield chunk

        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass

    def fake_get(url):
        return FakeStreamResp()

    async with client:
        monkeypatch.setattr(client, "_resolve_fn_index", fake_resolve)
        monkeypatch.setattr(client.session, "post", fake_post)
        monkeypatch.setattr(client.session, "get", fake_get)
        result = await client.predict(api_name="test", x=42)
    assert result == {"result": "success"}


@pytest.mark.asyncio
async def test_session_required():
    client = Client("https://example.com")
    with pytest.raises(NoSessionError):
        await client._get_json("https://example.com/test")
