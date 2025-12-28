import json

import pytest
from jupyter_server.base.handlers import APIHandler
from jupyter_server.extension.application import ExtensionApp


async def test_hello_world_handler(jp_fetch):
    # When
    response = await jp_fetch("signalpilot-ai-internal", "hello-world")

    # Then
    assert response.code == 200
    payload = json.loads(response.body)
    assert payload["data"] == "Hello World from SignalPilot AI backend!"
    assert "message" in payload