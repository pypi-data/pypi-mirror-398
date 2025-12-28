import logging

from aiohttp import ClientSession, ClientResponse
from aiohttp.http_exceptions import HttpProcessingError

from x_client import HttpNotFound, df_hdrs


class Client:
    is_started: bool = False
    host: str | None  # required
    headers: dict[str, str] = df_hdrs
    cookies: dict[str, str] = None
    proxy: str = None
    session: ClientSession

    def __init__(
        self, host: str = None, headers: dict[str, str] = df_hdrs, cookies: dict[str, str] = None, proxy: str = None
    ):
        base_url = f"https://{h}" if (h := host or self.host) else h
        hdrs, cooks = {**self.headers, **(headers or {})}, {**(self.cookies or {}), **(cookies or {})}
        self.session = ClientSession(base_url, headers=hdrs, cookies=cooks, proxy=proxy)

    async def stop(self):
        await self.session.close()

    # noinspection PyMethodMayBeStatic
    def _prehook(self, _payload: dict = None):
        return {}

    async def _get(self, url: str, params: dict = None, hdrs: dict = None):
        resp = await self.session.get(url, params=params, headers=(hdrs or {}) | self._prehook(params))
        return await self._proc(resp, params)

    async def _post(self, url: str, json: dict = None, form_data: dict = None, hdrs: dict = None):
        hdrs = (hdrs or {}) | self._prehook(json or form_data)
        if json:
            hdrs |= {"content-type": "application/json;charset=UTF-8"}
        elif form_data:
            hdrs |= {"Content-Type": "application/x-www-form-urlencoded"}
        skip_hdrs = ["user-agent"]
        resp = await self.session.post(url, json=json, data=form_data, headers=hdrs, skip_auto_headers=skip_hdrs)
        return await self._proc(resp, json or form_data)

    async def _put(self, url: str, json: dict = None, form_data: dict = None, hdrs: dict = None):
        hdrs = (hdrs or {}) | self._prehook(json or form_data)
        if json:
            hdrs |= {"content-type": "application/json;charset=UTF-8"}
        elif form_data:
            hdrs |= {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"}
        skip_hdrs = ["user-agent"]
        resp = await self.session.put(url, json=json, data=form_data, headers=hdrs, skip_auto_headers=skip_hdrs)
        return await self._proc(resp, json or form_data)

    async def _delete(self, url: str, params: dict = None):
        resp: ClientResponse = await self.session.delete(url, params=params, headers=self._prehook(params))
        return await self._proc(resp)

    async def _proc(self, resp: ClientResponse, bp=None) -> dict | str:
        if not str(resp.status).startswith("2"):
            logging.error(f"response {resp.status}: {await resp.text()}")
            if resp.status == 404:
                raise HttpNotFound()
            raise HttpProcessingError(code=resp.status, message=await resp.text())
        if resp.content_type.endswith("/json"):
            if not (data := await resp.json()):
                logging.warning("empty response: " + await resp.text())
            return data
        return await resp.text()

    METHS = {
        "GET": _get,
        "POST": _post,
        "PUT": _put,
        "DELETE": _delete,
    }
