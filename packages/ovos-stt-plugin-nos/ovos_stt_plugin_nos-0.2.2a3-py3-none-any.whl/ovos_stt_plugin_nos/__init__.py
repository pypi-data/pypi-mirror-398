from typing import Optional

from ovos_plugin_manager.templates.stt import STT
from ovos_stt_plugin_wav2vec import Wav2VecSTT
from ovos_utils import classproperty
from speech_recognition import AudioData


class NosSTT(STT):
    MODEL = "proxectonos/Nos_ASR-wav2vec2-large-xlsr-53-gl-with-lm"

    def __init__(self, config: dict = None):
        config = config or {}
        config["model"] = self.MODEL
        super().__init__(config)
        self.stt = Wav2VecSTT(config=config)

    def execute(self, audio: AudioData, language: Optional[str] = None):
        return self.stt.execute(audio, language)

    @classproperty
    def available_languages(cls) -> set:
        return {"gl"}


if __name__ == "__main__":
    b = NosSTT({"use_cuda": True})
    print(len(b.available_languages), sorted(list(b.available_languages)))
    from speech_recognition import Recognizer, AudioFile

    eu = "/home/miro/PycharmProjects/ovos-stt-wav2vec-plugin/9ooDUDs5.wav"
    with AudioFile(eu) as source:
        audio = Recognizer().record(source)

    a = b.execute(audio, language="gl")
    print(a)
    # ten en conta que as funcionarlidades incluídas nesta páxino ofrécense unicamente con fins de demostración se tes algún comentario subxestión ou detectas algún problema durante a demostración ponte en contacto con nosco
