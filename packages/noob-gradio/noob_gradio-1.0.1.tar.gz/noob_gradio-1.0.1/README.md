# noob-gradio

> A lightweight, async, dependency-free alternative to the official python [`gradio_client`](https://github.com/gradio-app/gradio) — written for speed, simplicity, and control.

[![PyPI](https://img.shields.io/pypi/v/noob-gradio.svg)](https://pypi.org/project/noob-gradio/)
[![Python Version](https://img.shields.io/pypi/pyversions/noob-gradio.svg)](https://pypi.org/project/noob-gradio/)
[![License](https://img.shields.io/pypi/l/noob-gradio.svg)](https://github.com/Noob-Lol/noob-gradio/blob/main/LICENSE)

---

## Features

- **Fast & Async** – built on top of `aiohttp` and `aiofiles`, thats all
- **Smart Parameter Checking** – validates types, min/max/step before sending
- **Tiny Dependency Footprint** – no heavy `huggingface_hub` and it's reqiurements (a lot)
- **Drop-in familiar syntax** – like the official client, but simpler and async

---

### Installation

```bash
pip install noob-gradio
```

### Details
This project was inspired by the official gradio_client
 but rewritten to:

remove unnecessary dependencies,

run fully async,

and perform parameter validation before sending data to the server.
- gradio_client is ok, but it installs a ton of stuff, so this is a noob remake of it.
- Available functions: "handle_file", "client.predict" and "client.view_api".
- Client functions are async and must be awaited.
- The syntax is exacly the same as in official gradio_client.

### New in 1.0.1
You can pass existing session to Client, to reuse it.
```py
import aiohttp
from noob_gradio import Client

async def main():
    session = aiohttp.ClientSession()
    client = Client("url", session=session)
    result = await client.predict(kwargs)
    print(result)
    # in on_close or similar event/function, at exit
    await session.close()
```

### Example
```py
import asyncio
from noob_gradio import Client, handle_file

async def main():
    async with Client("black-forest-labs/FLUX.1-schnell") as client:
        result = await client.predict(
            prompt="a cat sitting on a chair",
            width=512,
            height=512,
            api_name="/infer",
        )
        print(result)
        # you should get a path to downloaded image and image seed - (Result, Seed) or whatever the space returns
        # to not download you can add download_files=False in Client

asyncio.run(main())
```
Also this supports the hf_token and other methods of creating a Client and session, here is example of everything

```py
client = Client("black-forest-labs/FLUX.1-schnell", hf_token="secret", download_files=False, headers={"User-Agent": "gradio_real/1.0"})

async def main():
    async with client:
        # args and kwargs are suported
        res = await client.predict("a white cat", width=512, api_name="/infer")
        print(res)
    
    # "async with" alternative
    await client.connect()
    await client.view_api()
    # example file
    file = handle_file("https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png")
    # also you can choose different space for each predict or view_api, with src
    res = await client.predict(src="some space with file support", file=file, api_name="/predict")
    print(res)

    await client.close()
    # "async with" or "connect+close" is required because its async
```
handle_file is needed for input of image or any file, local or from url - predict(image=handle_file("local_path_or_url"), ...)
