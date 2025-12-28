from x_client.aiohttp import Client


async def test_public_request():
    pub = Client("xync.net")
    resp = await pub._get("")
    assert resp.startswith("<!DOCTYPE html>"), "Bad request"
