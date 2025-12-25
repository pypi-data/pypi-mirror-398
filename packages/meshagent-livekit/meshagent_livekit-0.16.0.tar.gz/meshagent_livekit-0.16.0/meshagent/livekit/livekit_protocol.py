from meshagent.api.protocol import Protocol

from livekit import rtc
import logging

logger = logging.getLogger("protocol.livekit")


class LivekitProtocol(Protocol):
    def __init__(self, room: rtc.Room, remote: rtc.RemoteParticipant, topic: str):
        super().__init__()
        self.room = room
        self.local = room.local_participant
        self.remote = remote
        self.topic = topic

    async def __aenter__(self):
        self.room.on("data_received", self._on_data_packet)
        return await super().__aenter__()

    async def __aexit__(self, exc_type, exc, tb):
        self.room.off("data_received", self._on_data_packet)

        return await super().__aexit__(exc_type, exc, tb)

    async def send_packet(self, data: bytes) -> None:
        logger.info(
            "sending data packet %s  %s to %s",
            self.topic,
            self.remote.identity,
            self.room.remote_participants[self.remote.identity].sid,
        )

        await self.local.publish_data(
            payload=data,
            topic=self.topic,
            reliable=True,
            destination_identities=[self.remote.identity],
        )

    def _on_data_packet(self, evt: rtc.DataPacket):
        if self.remote != evt.participant:
            return

        logger.info(
            "received data packet %s from %s", evt.topic, evt.participant.identity
        )

        if evt.topic == self.topic:
            self.receive_packet(evt.data)
