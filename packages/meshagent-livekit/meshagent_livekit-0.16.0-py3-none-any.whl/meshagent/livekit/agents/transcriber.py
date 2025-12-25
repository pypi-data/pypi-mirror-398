import logging
import asyncio
from asyncio import CancelledError

from meshagent.api import RoomMessage, Requirement, Participant, RemoteParticipant
from meshagent.api.room_server_client import RoomClient

from livekit.agents import Agent, AgentSession

from openai import AsyncOpenAI

from livekit.agents.stt import STT
from livekit.agents import RoomOutputOptions, StopResponse
from livekit.agents import llm

from livekit.plugins import openai, silero

from .voice import VoiceConnection
from livekit import rtc

from typing import Optional


from meshagent.agents import SingleRoomAgent


import re

logger = logging.getLogger("voice")


def _replace_non_matching(text: str, allowed_chars: str, replacement: str) -> str:
    """
    Replaces every character in `text` that does not match the given
    `allowed_chars` regex set with `replacement`.

    Parameters:
    -----------
    text : str
        The input string on which the replacement is to be done.
    allowed_chars : str
        A string defining the set of allowed characters (part of a character set).
        For example, "a-zA-Z0-9" will keep only letters and digits.
    replacement : str
        The string to replace non-matching characters with.

    Returns:
    --------
    str
        A new string where all characters not in `allowed_chars` are replaced.
    """
    # Build a regex that matches any character NOT in allowed_chars
    pattern = rf"[^{allowed_chars}]"
    return re.sub(pattern, replacement, text)


def safe_tool_name(name: str):
    return _replace_non_matching(name, "a-zA-Z0-9_-", "_")


class _Transcriber(Agent):
    def __init__(self, *, stt: STT, room: RoomClient, participant: RemoteParticipant):
        super().__init__(instructions="not-needed", stt=stt)
        self.room = room
        self.participant = participant

    async def on_user_turn_completed(
        self, chat_ctx: llm.ChatContext, new_message: llm.ChatMessage
    ):
        logger.info(f"transcription: {new_message.text_content}")
        self.room.messaging.send_message_nowait(
            to=self.participant,
            type="transcript",
            message={"text": new_message.text_content},
        )

        raise StopResponse()


class Transcriber(SingleRoomAgent):
    def __init__(
        self,
        name: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        labels: Optional[list[str]] = None,
        requires: list[Requirement] = None,
    ):
        super().__init__(
            name=name,
            description=description,
            title=title,
            labels=labels,
            requires=requires,
        )

    async def start(self, *, room):
        await super().start(room=room)
        await room.local_participant.set_attribute("supports_voice", True)
        await room.messaging.enable()
        room.messaging.on("message", self.on_message)

    def on_message(self, message: RoomMessage):
        if message.type == "voice_call":
            breakout_room = message.message["breakout_room"]

            logger.info(f"joining breakout room {breakout_room}")

            def on_done(task: asyncio.Task):
                try:
                    task.result()
                except CancelledError:
                    pass
                except Exception as e:
                    logger.error(f"{e}", exc_info=e)

            for participant in self.room.messaging.remote_participants:
                if participant.id == message.from_participant_id:
                    task = asyncio.create_task(
                        self.run_voice_agent(
                            participant=participant, breakout_room=breakout_room
                        )
                    )
                    task.add_done_callback(on_done)
                    return

            logger.error(f"unable to find participant {message.from_participant_id}")

    async def _wait_for_disconnect(self, room: rtc.Room):
        disconnected = asyncio.Future()

        def on_disconnected(_):
            disconnected.set_result(True)

        room.on("disconnected", on_disconnected)

        logger.info("waiting for disconnection")
        await disconnected

    async def create_agent(
        self, *, session: AgentSession, participant: RemoteParticipant
    ):
        return _Transcriber(
            stt=openai.STT(),
            room=self.room,
            participant=participant,
        )

    def create_session(self) -> AgentSession:
        token: str = self.room.protocol.token
        url: str = self.room.room_url

        room_proxy_url = f"{url}/v1"

        oaiclient = AsyncOpenAI(
            api_key=token,
            base_url=room_proxy_url,
            default_headers={"Meshagent-Session": self.room.session_id},
        )

        session = AgentSession(
            max_tool_steps=50,
            allow_interruptions=False,
            vad=silero.VAD.load(),
            stt=openai.STT(client=oaiclient),
            # turn_detection=MultilingualModel(),
        )
        return session

    async def run_voice_agent(self, *, participant: Participant, breakout_room: str):
        async with VoiceConnection(
            room=self.room, breakout_room=breakout_room
        ) as connection:
            logger.info("starting transcription agent")

            session = self.create_session()

            agent = await self.create_agent(session=session, participant=participant)

            await session.start(
                agent=agent,
                room=connection.livekit_room,
                room_output_options=RoomOutputOptions(transcription_enabled=True),
            )

            logger.info("started transcription agent")
            await self._wait_for_disconnect(room=connection.livekit_room)
