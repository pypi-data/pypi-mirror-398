import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import pytest
import os

from livekit import api
from livekit import rtc

import livekit_protocol
import asyncio

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_protocol():
    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    token1 = (
        api.AccessToken(api_key=api_key, api_secret=api_secret)
        .with_identity("core:user.test.agent-send")
        .with_name("Agent")
        .with_kind("agent")
        .with_grants(
            api.VideoGrants(
                can_update_own_metadata=True,
                room_join=True,
                room="test-process",
                agent=True,
            )
        )
    )

    jwt1 = token1.to_jwt()

    token2 = (
        api.AccessToken(api_key=api_key, api_secret=api_secret)
        .with_identity("core:user.test.agent-recv")
        .with_name("Agent")
        .with_kind("agent")
        .with_grants(
            api.VideoGrants(
                can_update_own_metadata=True,
                room_join=True,
                room="test-process",
                agent=True,
            )
        )
    )

    jwt2 = token2.to_jwt()

    room1 = rtc.Room()
    await room1.connect(url=url, token=jwt1)

    room2 = rtc.Room()
    await room2.connect(url=url, token=jwt2)

    topic = "test_topic"

    while True:
        await asyncio.sleep(0.1)

        if (
            room2.local_participant.identity in room1.remote_participants
            and room1.local_participant.identity in room2.remote_participants
        ):
            break

    async with livekit_protocol.LivekitProtocol(
        room=room1,
        remote=room1.remote_participants[room2.local_participant.identity],
        topic=topic,
    ) as proto1:
        async with livekit_protocol.LivekitProtocol(
            room=room2,
            remote=room2.remote_participants[room1.local_participant.identity],
            topic=topic,
        ) as proto2:
            test_data_builder = bytearray()
            for i in range(1024 * 1024):
                test_data_builder.append(i % 255)

            test_data = bytes(test_data_builder)

            done = asyncio.Future[bool]()

            matches = 0

            async def test_fn(protocol, id: int, type: str, data: bytes):
                nonlocal matches
                logger.info("Message received")
                if test_data != data:
                    raise "data isn't equal"
                matches += 1

                if matches == 2:
                    done.set_result(True)

            proto2.register_handler("test", test_fn)

            await asyncio.sleep(1)

            await proto1.send("test", test_data)
            await proto1.send("test", test_data)

            await done

    await room2.disconnect()
    await room1.disconnect()
