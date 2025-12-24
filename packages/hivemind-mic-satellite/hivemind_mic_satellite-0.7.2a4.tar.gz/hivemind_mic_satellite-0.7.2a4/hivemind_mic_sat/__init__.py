import pybase64
import os.path
from queue import Queue
from typing import Optional, List

import click
from ovos_audio.audio import AudioService
from ovos_audio.playback import PlaybackThread as _PT
from ovos_bus_client.message import Message
from ovos_plugin_manager.microphone import OVOSMicrophoneFactory, Microphone
from ovos_plugin_manager.utils.tts_cache import hash_sentence
from ovos_plugin_manager.vad import OVOSVADFactory, VADEngine
from ovos_utils.fakebus import FakeBus
from ovos_utils.log import LOG
from ovos_utils.sound import play_audio

from hivemind_bus_client.client import HiveMessageBusClient, BinaryDataCallbacks
from hivemind_bus_client.identity import NodeIdentity
from hivemind_bus_client.message import HiveMessage, HiveMessageType
from hivemind_bus_client.serialization import HiveMindBinaryPayloadType


class PlaybackThread(_PT):
    # TODO - send PR to ovos-audio adding util method
    def put(self, wav: str,
            visemes: Optional[List[str]] = None,
            listen: bool = False,
            tts_id: Optional[str] = None,
            message: Optional[Message] = None):
        message = message or Message("")
        # queue audio for playback
        self.queue.put(
            (wav, visemes, listen, tts_id, message)
        )


class TTSHandler(BinaryDataCallbacks):
    def __init__(self, playback: PlaybackThread):
        self.playback: PlaybackThread = playback
        super().__init__()

    def handle_receive_tts(self, bin_data: bytes,
                           utterance: str,
                           lang: str,
                           file_name: str):
        LOG.info(f"Received TTS: {file_name}")
        wav = f"/tmp/{file_name}"
        with open(wav, "wb") as f:
            f.write(bin_data)

        # queue audio for playback
        m = Message("speak", {"utterance": utterance, "lang": lang})
        # message is optional, allows G2P plugin to create mouth movements if configured
        self.playback.put(wav, message=m)


class HiveMindMicrophoneClient:

    def __init__(self, prefer_b64=False, enable_media=True, **kwargs):
        self.prefer_b64 = prefer_b64
        internal = FakeBus()
        self.playback: PlaybackThread = PlaybackThread(bus=internal,
                                                       queue=Queue())
        self.hm_bus = HiveMessageBusClient(bin_callbacks=TTSHandler(self.playback),
                                           internal_bus=internal, **kwargs)
        self.hm_bus.connect(FakeBus())
        self.hm_bus.connected_event.wait()
        LOG.info("== connected to HiveMind")
        self.mic: Microphone = OVOSMicrophoneFactory.create()
        self.vad: VADEngine = OVOSVADFactory.create()
        self.audio: Optional[AudioService] = None
        if enable_media:
            try:
                self.audio = AudioService(bus=internal, validate_source=False)
                LOG.info("Media playback support enabled")
            except Exception as e:
                LOG.error(f"Failed to initialize AudioService: {e}")
                LOG.warning("Media playback support will be disabled")
        self.running = False
        self.hm_bus.on_mycroft("recognizer_loop:wakeword", self.handle_ww)
        self.hm_bus.on_mycroft("recognizer_loop:record_begin", self.handle_rec_start)
        self.hm_bus.on_mycroft("recognizer_loop:record_end", self.handle_rec_end)
        self.hm_bus.on_mycroft("recognizer_loop:utterance", self.handle_utt)
        self.hm_bus.on_mycroft("recognizer_loop:speech.recognition.unknown", self.handle_stt_error)
        self.hm_bus.on_mycroft("mycroft.audio.play_sound", self.handle_sound)
        self.hm_bus.on_mycroft("speak", self.handle_speak)
        self.hm_bus.on_mycroft("speak:b64_audio.response", self.handle_speak_b64)
        self.hm_bus.on_mycroft("ovos.utterance.handled", self.handle_complete)
        try:
            from ovos_PHAL.service import PHAL
            self.phal = PHAL(bus=self.hm_bus)
            self.phal.start()
        except ImportError:
            LOG.warning("PHAL is not available")
            self.phal = None

    def handle_stt_error(self, message: Message):
        LOG.error("STT ERROR - transcription failed!")

    def handle_sound(self, message: Message):
        LOG.debug(f"PLAY SOUND: {message.data}")
        uri: str = message.data["uri"]
        if not os.path.isfile(uri):
            if uri.startswith("snd"):
                resolved = f"{os.path.dirname(__file__)}/res/{uri}"
                if os.path.isfile(resolved):
                    uri = resolved
        if not os.path.isfile(uri):
            LOG.error(f"unknown sound file: {uri}")
            return
        play_audio(uri)

    def handle_ww(self, message: Message):
        LOG.info(f"WAKE WORD: {message.data}")

    def handle_utt(self, message: Message):
        LOG.info(f"UTTERANCE: {message.data}")

    def handle_rec_start(self, message: Message):
        LOG.debug("STT BEGIN")

    def handle_rec_end(self, message: Message):
        LOG.debug("STT END")

    def handle_speak(self, message: Message):
        LOG.info(f"SPEAK: {message.data['utterance']}")
        if self.prefer_b64:
            m = message.reply("speak:b64_audio", message.data)
        else:
            m = message.reply("speak:synth", message.data)
        self.hm_bus.emit(HiveMessage(HiveMessageType.BUS, payload=m))
        LOG.debug("Requested TTS audio")

    def handle_speak_b64(self, message: Message):
        LOG.debug("TTS base64 encoded audio received")  # TODO - support binary transport too
        b64data = message.data["audio"]
        utt = message.data["utterance"]
        audio_file = f"/tmp/{hash_sentence(utt)}.wav"
        with open(audio_file, "wb") as f:
            f.write(pybase64.b64decode(b64data))
        LOG.info(f"TTS: {audio_file}")
        self.playback.put(audio_file,
                          listen=message.data.get("listen"),
                          message=message)

    def handle_complete(self, message: Message):
        LOG.info("UTTERANCE HANDLED!")

    def run(self):
        self.running = True
        self.mic.start()
        self.playback.start()

        chunk_duration = self.mic.chunk_size / self.mic.sample_rate  # time (in seconds) per chunk
        total_silence_duration = 0.0  # in seconds
        in_speech = False
        max_silence_duration = 6  # silence duration limit in seconds
        LOG.info("Listener Loop Started")
        while self.running:
            chunk = self.mic.read_chunk()
            if chunk is None:
                continue

            is_silence = self.vad.is_silence(chunk)
            if is_silence:
                total_silence_duration += chunk_duration

            # got speech data
            if not is_silence:
                total_silence_duration = 0  # reset silence duration when speech is detected
                if not in_speech:
                    LOG.info("Speech start, initiating audio transmission")
                    in_speech = True

            if in_speech:
                self.hm_bus.emit(
                    HiveMessage(msg_type=HiveMessageType.BINARY, payload=chunk),
                    binary_type=HiveMindBinaryPayloadType.RAW_AUDIO
                )
                # reached the max allowed silence time, stop sending audio
                if total_silence_duration >= max_silence_duration:
                    in_speech = False
                    LOG.info(f"No speech for {max_silence_duration} seconds, stopping audio transmission")

        self.running = False

    def stop(self):
        self.running = False
        if self.phal:
            self.phal.shutdown()
        self.playback.shutdown()
        self.mic.stop()


@click.command()
@click.option("--key", help="HiveMind access key (default read from identity file)", type=str, default="")
@click.option("--password", help="HiveMind password (default read from identity file)", type=str, default="")
@click.option("--host", help="HiveMind host (default read from identity file)", type=str, default="")
@click.option("--port", help="HiveMind port number (default read from identity file or 5678)", type=int, required=False)
@click.option("--siteid", help="location identifier for message.context  (default read from identity file)", type=str,
              default="")
def run(key: str, password: str, host: str, port: int, siteid: str):
    identity = NodeIdentity()
    password = password or identity.password
    key = key or identity.access_key
    host = host or identity.default_master
    identity.siteid = siteid or identity.site_id or "unknown"
    port = port or identity.default_port or 5678

    if not host.startswith("ws://") and not host.startswith("wss://"):
        host = "ws://" + host

    if not key or not password or not host:
        raise RuntimeError("NodeIdentity not set, please pass key/password/host or "
                           "call 'hivemind-client set-identity'")

    h = HiveMindMicrophoneClient(key=key, host=host, port=port,
                                 password=password, identity=identity)
    h.run()


if __name__ == "__main__":
    run()
