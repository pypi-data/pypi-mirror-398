# Copyright 2023 LiveKit, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import asyncio
import os
import weakref
from dataclasses import dataclass

import aiohttp
import msgpack
import numpy as np

from livekit import rtc
from livekit.agents import (
    DEFAULT_API_CONNECT_OPTIONS,
    APIConnectOptions,
    stt,
    utils,
)
from livekit.agents.types import (
    NOT_GIVEN,
    NotGivenOr,
)
from livekit.agents.utils import AudioBuffer, is_given

from .log import logger


@dataclass
class STTOptions:
    endpoint_url: str
    sample_rate: int = 24000
    num_channels: int = 1


class STT(stt.STT):
    def __init__(
        self,
        *,
        sample_rate: int = 24000,
        api_key: str = "public_token",
        http_session: aiohttp.ClientSession | None = None,
        base_url: str = "ws://127.0.0.1:8080/api/asr-streaming",
    ) -> None:
        """Create a new instance of Kyutai STT

        Args:
            sample_rate: The sample rate of the audio stream.
            api_key: The API key for the Kyutai API.
            http_session: The HTTP session to use for the Kyutai API.
            base_url: The base URL for the Kyutai API. Default to ws://127.0.0.1:8080/api/asr-streaming

        Note:
            The api_key must be set either through the constructor argument or by setting
            the KYUTAI_API_KEY environmental variable.
        """
        super().__init__(capabilities=stt.STTCapabilities(streaming=True, interim_results=True))

        kyutai_api_key = api_key if is_given(api_key) else os.environ.get("KYUTAI_API_KEY")
        if not kyutai_api_key:
            raise ValueError("Kyutai API key is required")
        self._api_key = kyutai_api_key

        self._opts = STTOptions(sample_rate=sample_rate, num_channels=1, endpoint_url=base_url)
        self._session = http_session
        self._streams = weakref.WeakSet[SpeechStream]()

    def _ensure_session(self) -> aiohttp.ClientSession:
        if not self._session:
            self._session = utils.http_context.http_session()
        return self._session

    async def _recognize_impl(
        self,
        buffer: AudioBuffer,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> stt.SpeechEvent:
        raise NotImplementedError("Kyutai STT only supports streaming recognition.")

    def stream(self, *, conn_options=DEFAULT_API_CONNECT_OPTIONS) -> SpeechStream:
        stream = SpeechStream(
            stt=self,
            opts=self._opts,
            conn_options=conn_options,
            api_key=self._api_key,
            http_session=self._ensure_session(),
            base_url=self._opts.endpoint_url,
        )
        self._streams.add(stream)
        return stream

    def update_options(
        self,
        *,
        sample_rate: NotGivenOr[int] = NOT_GIVEN,
        endpoint_url: NotGivenOr[str] = NOT_GIVEN,
    ) -> None:
        if is_given(sample_rate):
            self._opts.sample_rate = sample_rate
        if is_given(endpoint_url):
            self._opts.endpoint_url = endpoint_url

        for stream in self._streams:
            stream.update_options(sample_rate=sample_rate, endpoint_url=endpoint_url)


class SpeechStream(stt.SpeechStream):
    def __init__(
        self,
        *,
        stt: STT,
        opts: STTOptions,
        conn_options: APIConnectOptions,
        api_key: str,
        http_session: aiohttp.ClientSession,
        base_url: str,
    ) -> None:
        super().__init__(stt=stt, conn_options=conn_options, sample_rate=opts.sample_rate)
        self._opts = opts
        self._api_key = api_key
        self._session = http_session
        self._opts.endpoint_url = base_url
        self._ws = None
        self._request_id = ""
        self._reconnect_event = asyncio.Event()

    def update_options(
        self,
        *,
        sample_rate: NotGivenOr[int] = NOT_GIVEN,
        endpoint_url: NotGivenOr[str] = NOT_GIVEN,
    ):
        if is_given(sample_rate):
            self._opts.sample_rate = sample_rate
        if is_given(endpoint_url):
            self._opts.endpoint_url = endpoint_url

        self._reconnect_event.set()

    async def _run(self) -> None:
        @utils.log_exceptions(logger=logger)
        async def send_task(ws: aiohttp.ClientWebSocketResponse) -> None:
            # forward audio to deepgram in chunks of 80ms
            samples_80ms = 1920
            audio_bstream = utils.audio.AudioByteStream(
                sample_rate=self._opts.sample_rate,
                num_channels=self._opts.num_channels,
                samples_per_channel=samples_80ms,
            )
            async for data in self._input_ch:
                frames: list[rtc.AudioFrame] = []
                if isinstance(data, rtc.AudioFrame):
                    frames.extend(audio_bstream.write(data.data.tobytes()))
                elif isinstance(data, self._FlushSentinel):
                    frames.extend(audio_bstream.flush())

                for frame in frames:
                    # Convert frame to 32-bit PCM for Kyutai and normalize
                    pcm = np.frombuffer(frame.data, dtype=np.int16).astype(np.float32) / 32768.0
                    chunk = {"type": "Audio", "pcm": pcm.tolist()}
                    msg = msgpack.packb(chunk, use_bin_type=True, use_single_float=True)
                    await ws.send_bytes(msg)

        @utils.log_exceptions(logger=logger)
        async def recv_task(ws: aiohttp.ClientWebSocketResponse) -> None:
            while True:
                msg = await ws.receive()
                if msg.type in (
                    aiohttp.WSMsgType.CLOSED,
                    aiohttp.WSMsgType.CLOSE,
                    aiohttp.WSMsgType.CLOSING,
                ):
                    return
                if msg.type != aiohttp.WSMsgType.BINARY:
                    continue
                try:
                    data = msgpack.unpackb(msg.data, raw=False)
                    self._process_stream_event(data)
                except Exception:
                    logger.exception("failed to process kyutai message")

        while True:
            try:
                ws = await self._connect_ws()
                self._ws = ws
                tasks = [
                    asyncio.create_task(send_task(ws)),
                    asyncio.create_task(recv_task(ws)),
                ]
                tasks_group = asyncio.gather(*tasks)
                wait_reconnect_task = asyncio.create_task(self._reconnect_event.wait())
                try:
                    done, _ = await asyncio.wait(
                        (tasks_group, wait_reconnect_task),
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    # propagate exceptions from completed tasks
                    for task in done:
                        if task != wait_reconnect_task:
                            task.result()

                    if wait_reconnect_task not in done:
                        break

                    self._reconnect_event.clear()
                    logger.info("Reconnecting Kyutai session due to options change")
                finally:
                    await utils.aio.gracefully_cancel(*tasks, wait_reconnect_task)
                    tasks_group.cancel()
                    tasks_group.exception()  # retrieve the exception
            finally:
                if self._ws is not None:
                    await self._ws.close()

    async def _connect_ws(self) -> aiohttp.ClientWebSocketResponse:
        headers = {"kyutai-api-key": self._api_key}
        ws = await self._session.ws_connect(
            self._opts.endpoint_url,
            headers=headers,
            timeout=self._conn_options.timeout,
        )
        logger.info(f"Connected to Kyutai session {self._request_id}")
        return ws

    def _process_stream_event(self, data: dict) -> None:
        if data["type"] == "Word":
            sd = stt.SpeechData(
                language="-",
                start_time=data.get("start_time", 0),
                text=data["text"],
            )
            event = stt.SpeechEvent(
                type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                request_id=self._request_id,
                alternatives=[sd],
            )
            self._event_ch.send_nowait(event)
        elif data["type"] == "Marker":
            event = stt.SpeechEvent(
                type=stt.SpeechEventType.END_OF_SPEECH, request_id=self._request_id
            )
            self._event_ch.send_nowait(event)
