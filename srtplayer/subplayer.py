import alsaaudio
from pathlib import PurePath
from subrip import SubRip
import wave
import threading
from math import ceil
from PySide import QtCore


class SubPlayer(QtCore.QObject):
    _CHUNK = 1024

    text_changed = QtCore.Signal(str)

    @property
    def sub(self):
        return self._sub

    @property
    def time(self):
        if self.loaded:
            return self._audio.tell() / (self._audio.getframerate() * self._audio.getnchannels()) * 1000
        else:
            return 0

    @time.setter
    def time(self, value):
        if self.loaded:
            if 0 <= value <= self.length:
                pos = value * self._audio.getframerate() * self._audio.getnchannels() / 1000
                pos = ceil(pos)
                play = self._playing
                self.pause()
                self._audio.setpos(pos)
                if play:
                    self.play()
            else:
                self.pause()
                raise ValueError("Attempt to set incorrect time")

    @property
    def playing(self):
        return self._playing

    @property
    def length(self):
        return self._length

    @property
    def loaded(self):
        return self._audio is not None

    def __init__(self):
        super(SubPlayer, self).__init__()
        self._playing = False
        self._device = alsaaudio.PCM()
        self._length = None
        self._audio = None
        self._audio_thread = None
        self._subs = None
        self._sub = None

    def play(self):
        if self.loaded and not self._playing:
            self._audio_thread = threading.Thread(target=self._update)
            self._playing = True
            self._audio_thread.start()

    def pause(self):
        self._playing = False
        if self._audio_thread is not None:
            self._audio_thread.join()

    def play_pause(self):
        if self._playing:
            self.pause()
        else:
            self.play()

    def _update(self):
        data = self._audio.readframes(self._CHUNK)
        while data and self._playing:
            length = len(data) // self._audio.getsampwidth()
            if length != self._CHUNK:
                data += b"\x00" * (self._CHUNK - length) * self._audio.getsampwidth()
            self._device.write(data)
            if self._subs is not None:
                sub = self._subs.find(self.time)
                if sub is not self._sub:
                    self._sub = sub
                    self._emit_sub_changed_new_thread()
            data = self._audio.readframes(self._CHUNK)
        if data == '':
            self._playing = False
            self._audio.rewind()

    def load_subs(self, subs_path):
        with open(subs_path) as subs:
            self._subs = SubRip.parse(subs.read())
        self._sub = None
        self._emit_sub_changed_new_thread()

    def open(self, audio):
        self.pause()
        path = PurePath(audio)
        if path.suffix == ".wav":
            self._audio = wave.open(audio, "rb")
        else:
            self._audio = None
            raise ValueError("Unsupported format " + path.suffix)
        self._length = self._audio.getnframes() / self._audio.getframerate() / self._audio.getnchannels() * 1000
        self._device.setchannels(self._audio.getnchannels())
        self._device.setrate(self._audio.getframerate())

        # 8bit is unsigned in wav files
        if self._audio.getsampwidth() == 1:
            self._device.setformat(alsaaudio.PCM_FORMAT_U8)
        # Otherwise we assume signed data, little endian
        elif self._audio.getsampwidth() == 2:
            self._device.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        elif self._audio.getsampwidth() == 3:
            self._device.setformat(alsaaudio.PCM_FORMAT_S24_LE)
        elif self._audio.getsampwidth() == 4:
            self._device.setformat(alsaaudio.PCM_FORMAT_S32_LE)
        else:
            raise ValueError('Unsupported format')

        self._device.setperiodsize(self._CHUNK)

        try:
            with open(str(path.with_suffix(".srt"))) as subs:
                self._subs = SubRip.parse(subs.read())
        except Exception:
            self._subs = None
        self._emit_sub_changed_new_thread()

    def _emit_sub_changed(self):
        if self.sub is None:
            self.text_changed.emit("")
        else:
            self.text_changed.emit(self.sub.text)

    def _emit_sub_changed_new_thread(self):
        threading.Thread(target=self._emit_sub_changed).start()

