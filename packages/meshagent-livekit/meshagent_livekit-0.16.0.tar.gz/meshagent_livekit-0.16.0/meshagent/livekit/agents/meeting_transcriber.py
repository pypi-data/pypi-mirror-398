import asyncio
import logging

from typing import Optional

from datetime import datetime, timezone
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
    RoomInputOptions,
    RoomIO,
    RoomOutputOptions,
    StopResponse,
    llm,
    utils,
)
from livekit.agents.stt import STT

from meshagent.openai.proxy import get_client
from livekit.plugins import openai, silero
from meshagent.api import MeshDocument, SchemaRegistration, SchemaRegistry
from meshagent.agents import SingleRoomAgent
from meshagent.tools import RemoteToolkit, ToolContext, Tool
from meshagent.api.room_server_client import Requirement
from meshagent.livekit.agents.voice import VoiceConnection
from meshagent.agents.schemas.transcript import transcript_schema

logger = logging.getLogger("meeting_transcriber")


class StartTranscriptionTool(Tool):
    def __init__(self, *, transcriber: "MeetingTranscriber"):
        self.transcriber = transcriber
        super().__init__(
            name="start_transcription",
            input_schema={
                "type": "object",
                "required": [
                    "breakout_room",
                    "path",
                ],
                "additionalProperties": False,
                "properties": {
                    "breakout_room": {
                        "type": "string",
                    },
                    "path": {
                        "type": "string",
                    },
                },
            },
        )

    async def execute(self, context: ToolContext, *, breakout_room: str, path: str):
        await self.transcriber.start_transcription(
            breakout_room=breakout_room, path=path
        )
        return {"status": "started"}


class StopTranscriptionTool(Tool):
    def __init__(self, *, transcriber: "MeetingTranscriber"):
        self.transcriber = transcriber
        super().__init__(
            name="stop_transcription",
            input_schema={
                "type": "object",
                "required": [
                    "breakout_room",
                ],
                "additionalProperties": False,
                "properties": {
                    "breakout_room": {
                        "type": "string",
                    },
                },
            },
        )

    async def execute(self, context: ToolContext, *, breakout_room: str):
        await self.transcriber.stop_transcription(
            breakout_room=breakout_room,
        )
        return {"status": "stopped"}


class MeetingTranscriber(SingleRoomAgent):
    def __init__(
        self,
        name: str,
        requires: Optional[list[Requirement]] = None,
        stt: Optional[STT] = None,
    ):
        super().__init__(
            name=name,
            requires=requires,
        )
        self._toolkit = RemoteToolkit(
            name="transcription",
            tools=[
                StartTranscriptionTool(transcriber=self),
                StopTranscriptionTool(transcriber=self),
            ],
        )
        self.stt = stt
        self._vad = None
        self._transcription_tasks = dict[str, tuple[asyncio.Task, asyncio.Future]]()

    async def start(self, *, room):
        await super().start(room=room)
        await self._toolkit.start(room=room)
        await room.local_participant.set_attribute("supports_voice", True)
        await room.messaging.enable()

        self._vad = silero.VAD.load()

    async def start_transcription(self, *, breakout_room: Optional[str], path: str):
        stop_fut = asyncio.Future()

        async def transcribe():
            await self.room.local_participant.set_attribute(
                f"transcribing.{breakout_room}", True
            )

            try:
                async with VoiceConnection(
                    room=self.room, breakout_room=breakout_room
                ) as conn:
                    doc = await self.room.sync.open(path=path, create=True)

                    stt = self.stt
                    if stt is None:
                        openai_client = get_client(room=self.room)
                        stt = openai.STT(client=openai_client)

                    transcriber = MultiUserTranscriber(conn, doc, self._vad, stt)
                    transcriber.start()

                    for participant in conn.livekit_room.remote_participants.values():
                        # handle all existing participants
                        transcriber.on_participant_connected(participant)

                    await stop_fut

                    await self.room.local_participant.set_attribute(
                        f"transcribing.{breakout_room}", False
                    )

                    await self.room.sync.close(path=path)

                    await transcriber.aclose()
            except Exception as ex:
                logger.error(f"error during transcription {ex}", exc_info=ex)
                pass

            await self.room.local_participant.set_attribute(
                f"transcribing.{breakout_room}", False
            )

        if breakout_room not in self._transcription_tasks:
            self._transcription_tasks[breakout_room] = (
                asyncio.create_task(transcribe()),
                stop_fut,
            )

    async def stop_transcription(self, *, breakout_room: Optional[str]):
        if breakout_room in self._transcription_tasks:
            task, fut = self._transcription_tasks.pop(breakout_room)
            fut.set_result(True)
            await asyncio.gather(task)

    async def stop(self):
        await self._toolkit.stop()

        tasks = []
        for breakout_room, _ in self._transcription_tasks.items():
            task, fut = self._transcription_tasks.pop(breakout_room)
            fut.set_result(True)
            tasks.append(task)

        await asyncio.gather(*tasks)
        await super().stop()


class TranscriptRegistry(SchemaRegistry):
    def __init__(self):
        name = "transcript"
        super().__init__(
            name=f"meshagent.schema.{name}",
            validate_webhook_secret=False,
            schemas=[SchemaRegistration(name=name, schema=transcript_schema)],
        )


class Transcriber(Agent):
    def __init__(self, *, participant, doc: MeshDocument, stt):
        super().__init__(
            instructions="not-needed",
            stt=stt,
        )
        self.doc = doc
        self.participant = participant

    async def on_user_turn_completed(
        self, chat_ctx: llm.ChatContext, new_message: llm.ChatMessage
    ):
        segments = self.doc.root
        segments.append_child(
            "segment",
            {
                "text": new_message.text_content,
                "participant_name": self.participant.name,
                "participant_id": self.participant.sid,
                "time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            },
        )
        raise StopResponse()


class MultiUserTranscriber:
    def __init__(self, ctx: VoiceConnection, doc: MeshDocument, vad, stt):
        self.ctx = ctx
        self.doc = doc
        self.vad = vad
        self.stt = stt
        self._sessions: dict[str, AgentSession] = {}
        self._tasks: set[asyncio.Task] = set()

    def start(self):
        self.ctx.livekit_room.on("participant_connected", self.on_participant_connected)
        self.ctx.livekit_room.on(
            "participant_disconnected", self.on_participant_disconnected
        )

    async def aclose(self):
        await utils.aio.cancel_and_wait(*self._tasks)

        await asyncio.gather(
            *[self._close_session(session) for session in self._sessions.values()]
        )

        self.ctx.livekit_room.off(
            "participant_connected", self.on_participant_connected
        )
        self.ctx.livekit_room.off(
            "participant_disconnected", self.on_participant_disconnected
        )

    def on_participant_connected(self, participant: rtc.RemoteParticipant):
        if participant.identity in self._sessions:
            return

        logger.info(f"starting session for {participant.identity}")
        task = asyncio.create_task(self._start_session(participant))
        self._tasks.add(task)

        def on_task_done(task: asyncio.Task):
            try:
                self._sessions[participant.identity] = task.result()
            finally:
                self._tasks.discard(task)

        task.add_done_callback(on_task_done)

    def on_participant_disconnected(self, participant: rtc.RemoteParticipant):
        if (session := self._sessions.pop(participant.identity)) is None:
            return

        logger.info(f"closing session for {participant.identity}")
        task = asyncio.create_task(self._close_session(session))
        self._tasks.add(task)
        task.add_done_callback(lambda _: self._tasks.discard(task))

    async def _start_session(self, participant: rtc.RemoteParticipant) -> AgentSession:
        if participant.identity in self._sessions:
            return self._sessions[participant.identity]

        session = AgentSession(
            vad=self.vad,
        )
        room_io = RoomIO(
            agent_session=session,
            room=self.ctx.livekit_room,
            participant=participant,
            input_options=RoomInputOptions(
                # text input is not supported for multiple room participants
                # if needed, register the text stream handler by yourself
                # and route the text to different sessions based on the participant identity
                text_enabled=False,
                delete_room_on_close=False,
            ),
            output_options=RoomOutputOptions(
                transcription_enabled=True,
                audio_enabled=False,
            ),
        )
        await room_io.start()
        await session.start(
            agent=Transcriber(
                participant=participant,
                doc=self.doc,
                stt=self.stt,
            )
        )
        return session

    async def _close_session(self, sess: AgentSession) -> None:
        await sess.drain()
        await sess.aclose()
