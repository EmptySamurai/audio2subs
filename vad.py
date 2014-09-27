__author__ = 'emptysamurai'

import wave
import numpy as np
from timeinterval import TimeInterval
import struct


def _hz_to_index(hz, length, sample_rate):
    return round(hz * length / sample_rate)


def _voice_frequency_energy(frame, sample_rate):
    fft_frame = np.fft.rfft(frame)
    length = len(frame)
    start_index = _hz_to_index(300, length, sample_rate)
    end_index = _hz_to_index(1250, length, sample_rate)
    upper_bound = len(fft_frame)
    sum_energy = 0
    for i in range(min(start_index, upper_bound - 1), min(end_index + 1, upper_bound)):
        sum_energy += abs(fft_frame[i]) ** 2
    return sum_energy


def _bytes_to_samples(samples_bytes, bytes_per_frame):
    length = len(samples_bytes) // bytes_per_frame
    if bytes_per_frame == 4:
        int_type = 'i'
    elif bytes_per_frame == 2:
        int_type = 'h'
    elif bytes_per_frame == 1:
        int_type = 'c'
    elif bytes_per_frame == 8:
        int_type = 'q'
    else:
        raise ValueError("Can't read "+str(bytes_per_frame)+"-byte audio")

    return np.array(struct.unpack("<" + str(length) + int_type, samples_bytes))


def _to_mono(samples, channels):
    if channels == 1:
        return samples
    else:
        return np.array(np.mean(i) for i in np.split(samples, samples // channels))


def _samples_to_frames(samples, number_of_frames):
    return np.split(np.resize(samples, len(samples) - len(samples) % number_of_frames), number_of_frames)


def _decisions_to_silence_time_intervals(decisions, frame_length):
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
            is_silence = True
        else:
            is_silence = False
    return intervals


def get_silence_intervals(path):
    # initial constants
    frame_length = 10  # ms
    read_frames = 2048
    first_frames_silence = 30
    threshold_level = 10
    min_frames_speech = 5
    min_frames_silence = 10

    # TODO: make file conversion

    # open file
    audio = wave.open(path, "rb")
    bytes_per_frame = audio.getsampwidth()
    sample_rate = audio.getframerate()
    channels = audio.getnchannels()
    samples_per_frame = int((sample_rate * frame_length * channels) / 1000)
    number_of_frames = audio.getnframes() // samples_per_frame

    if number_of_frames < first_frames_silence:
        raise ValueError("Audio file should be at least " + str(frame_length * first_frames_silence) + "ms")

    current_frame = 0

    # estimating silence energy
    decisions = [False] * number_of_frames
    samples_bytes = audio.readframes(first_frames_silence * samples_per_frame)
    current_frame += first_frames_silence
    samples = _to_mono(_bytes_to_samples(samples_bytes, bytes_per_frame), channels)
    frames = _samples_to_frames(samples, first_frames_silence)

    mean_frequency_energy = 0
    for frame in frames:
        mean_frequency_energy += _voice_frequency_energy(frame, sample_rate)
    mean_frequency_energy /= first_frames_silence

    # main evaluation
    read_samples = read_frames * samples_per_frame
    mean_frequency_energy_zero = mean_frequency_energy == 0
    while current_frame < number_of_frames:
        if number_of_frames - current_frame < read_frames:
            read_frames = number_of_frames - current_frame
            read_samples = read_frames * samples_per_frame

        samples_bytes = audio.readframes(read_samples)
        samples = _to_mono(_bytes_to_samples(samples_bytes, bytes_per_frame), channels)
        frames = _samples_to_frames(samples, read_frames)
        for frame in frames:
            frequency_energy = _voice_frequency_energy(frame, sample_rate)
            if mean_frequency_energy_zero:
                decisions[current_frame] = bool(frequency_energy)
            else:
                if frequency_energy / mean_frequency_energy > threshold_level:
                    decisions[current_frame] = True
            current_frame += 1

    # removing short intervals
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

    return _decisions_to_silence_time_intervals(decisions, frame_length)