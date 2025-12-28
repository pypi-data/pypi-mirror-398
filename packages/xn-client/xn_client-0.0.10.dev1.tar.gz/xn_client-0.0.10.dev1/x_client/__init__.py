from aiohttp.http_exceptions import HttpProcessingError

df_hdrs = {
    "accept": "application/json",
    "cookie": ";",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
}


class HttpNotFound(HttpProcessingError):
    code = 404
    message = "NotFound"


# decorator for network funcs
def repeat_on_fault(times: int = 4, wait: int = 3):
    def decorator(func: callable):
        from asyncio import sleep

        async def wrapper(*args, **kwargs):
            for attempt in range(times):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    print(f"{func.__name__}: attempt {attempt + 1}:", e)
                    await sleep(wait)
            return print("Patience over!")

        return wrapper

    return decorator
