__author__ = 'emptysamurai'

import wave
import numpy as np


class TimeInterval:
    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, value):
        if self.end < self.start:
            raise ValueError("Interval end is earlier than start")
        self._start = value

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, value):
        if self.end < self.start:
            raise ValueError("Interval end is earlier than start")
        self._end = value

    def __init__(self, start, end):
        if end < start:
            raise ValueError("Interval end is earlier than start")
        self._start = start
        self._end = end

    def length(self):
        return self.end - self.start


def _hz_to_index(hz, length, sampleRate):
    return round(hz * length / sampleRate)


def _voice_frequency_energy(frame, sample_rate):
    fft_frame = np.fft.rfft(frame)
    length = len(fft_frame)
    start_index = _hz_to_index(300, length, sample_rate)
    end_index = _hz_to_index(1000, length, sample_rate)
    sum_energy = 0
    for i in range(min(start_index, length / 2), min(end_index + 1, length / 2)):
        sum_energy += abs(fft_frame[i]) ** 2
    return sum_energy


def _bytes_to_samples(bytes, bytes_per_frame):
    return np.array([int.from_bytes(bytes[i:i + bytes_per_frame], "little") for i in
                     range(0, len(bytes) - bytes_per_frame, bytes_per_frame)])


def _samples_to_frames(samples, number_of_frames):
    return np.split(np.resize(samples, len(samples) - len(samples) % number_of_frames), number_of_frames)


def _decisions_array_to_silence_time_intervals(decisions, frame_length):
    intervals = []
    is_silence = not decisions[0]
    if is_silence:
        intervals.append(TimeInterval(0, frame_length))
    for i in range(len(decisions)):
        if not decisions[i]:
            if is_silence:
                last = intervals[len(intervals) - 1]
                last.end += frame_length
            else:
                time = i * frame_length
                intervals.append(TimeInterval(time, time + frame_length))
    return intervals


def get_silence_intervals(path):
    #constants
    frame_length = 10  #ms
    first_frames_silence = 30
    read_frames = 100
    threshold_level = 10
    min_frames_speech = 5
    min_frames_silence = 10

    #TODO: make file conversion

    #open file
    audio = wave.open(path, "rb")
    bytes_per_frame = audio.getsampwidth()
    sample_rate = audio.getframerate()
    samples_per_frame = int((sample_rate * frame_length) / 1000)
    read_frames = samples_per_frame * 10
    number_of_frames = audio.getnframes() // samples_per_frame
    current_frame = 0

    #estimating silence energy
    decisions = [False]*number_of_frames
    samples_bytes = audio.readframes(first_frames_silence * samples_per_frame)
    current_frame += first_frames_silence
    samples = _bytes_to_samples(samples_bytes, bytes_per_frame)
    frames = _samples_to_frames(samples, first_frames_silence)

    mean_frequency_energy = 0
    for frame in frames:
        mean_frequency_energy += _voice_frequency_energy(frame, sample_rate)
    mean_frequency_energy /= first_frames_silence

    #main evaluation
    read_samples = read_frames * samples_per_frame
    while current_frame < number_of_frames:
        if number_of_frames - current_frame < read_frames:
            read_frames = number_of_frames - current_frame
            read_samples = read_frames * samples_per_frame

        samples_bytes = audio.readframes(read_samples)
        samples = _bytes_to_samples(samples_bytes, bytes_per_frame)
        frames = _samples_to_frames(samples, read_frames)
        for frame in frames:
            frequency_energy = _voice_frequency_energy(frame, sample_rate)
            if frequency_energy / mean_frequency_energy > threshold_level:
                decisions[current_frame] = True
            current_frame += 1

    #removing short intervals
    is_speech = False
    start_index = 0
    for i in range(len(decisions)):
        if decisions[i] != is_speech:
            length = i - start_index
            if is_speech and length < min_frames_speech:
                for j in range(start_index, i):
                    decisions[j] = False
                i -= length
            elif (not is_speech) and length < min_frames_silence:
                for j in range(start_index, i):
                    decisions[j] = True
                i -= length
            is_speech = decisions[i]
            start_index = i

    return _decisions_array_to_silence_time_intervals(decisions, frame_length)