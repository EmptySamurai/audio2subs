__author__ = 'emptysamurai'

import math
import numpy as np
import wave
from scipy.io.wavfile import read
from timeinterval import TimeInterval

#Not such a bad VAD. Implemented for comparison.
#http://asmp.eurasipjournals.com/content/pdf/1687-4722-2013-21.pdf

_R = 5
_M = 10


def _short_time_spectrum(frames, index, frequency):
    start = max(0, index - _M)
    return sum(abs(frames[i][frequency]) for i in range(start, index)) / (index - start)


def lsfm(frames, index, sample_rate):
    start_frequency = 500
    last_frequency = 4000

    frame_length = frames.shape[1]
    start_frequency_index = _hz_to_index(start_frequency, frame_length, sample_rate)
    last_frequency_index = _hz_to_index(last_frequency, frame_length, sample_rate)

    result = 0
    for i in range(start_frequency_index, last_frequency_index + 1):
        geometric_mean = 0
        arithmetic_mean = 0
        start = max(0, index - _R)
        for j in range(start, index + 1):
            sts = _short_time_spectrum(frames, j, i)
            if not sts == 0:
                geometric_mean += math.log(sts)
                arithmetic_mean += sts
        geometric_mean = math.pow(math.exp(geometric_mean), 1 / _R)
        arithmetic_mean /= _R
        if not (arithmetic_mean == 0 or geometric_mean == 0):
            result += math.log10(geometric_mean / arithmetic_mean)
    return result


def threshold(frames, sample_rate):
    length = 100
    lambda_value = 0.55

    last_speech = 0
    last_silence = _M + _R + length
    number_of_frames = frames.shape[0]
    lsfm_values = np.empty(number_of_frames, dtype=float)
    result = np.empty(number_of_frames, dtype=bool)

    for i in range(_M + _R):
        result[i] = False

    for i in range(_M + _R, _M + _R + length):
        result[i] = False
        lsfm_values[i] = lsfm(frames, i, sample_rate)

    for i in range(_M + _R + length, number_of_frames):
        lsfm_values[i] = lsfm(frames, i, sample_rate)
        threshold_value = lambda_value * _min_silence_value(lsfm_values, last_speech, length) + \
                          (1 - lambda_value) * _max_silence_value(lsfm_values, last_silence, length)
        if lsfm_values[i] > threshold_value:
            result[i] = True
            last_speech = i
        else:
            result[i] = False
            last_silence = i
    return result


def _min_silence_value(lsfm_values, index, length):
    if not index == 0:
        return min(lsfm_values[i] for i in range(index - length + 1, index + 1))
    else:
        return 0


def _max_silence_value(lsfm_values, index, length):
    if not index == 0:
        return max(lsfm_values[i] for i in range(index - length + 1, index + 1))
    else:
        return 0


def _hz_to_index(hz, length, sample_rate):
    return round(hz * length / sample_rate)


def _to_mono(samples, channels):
    if channels == 1:
        return samples
    else:
        return np.array([np.mean(i) for i in np.split(samples, samples // channels)])


def _samples_to_frames(samples, number_of_frames, samples_per_frame, samples_per_overlapping):
    result = np.empty((number_of_frames, samples_per_frame), dtype=complex)
    hann_window = np.hanning(samples_per_frame)
    for i in range(0, number_of_frames):
        start = i * (samples_per_frame - samples_per_overlapping)
        result[i] = samples[start: start + samples_per_frame]*hann_window
    return result


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
    frame_length = 20  # ms
    frame_overlapping = 10  # ms
    read_frames = 2048

    # open file
    (sample_rate, samples) = read(path)
    audio = wave.open(path, "rb")
    channels = audio.getnchannels()
    samples_per_frame = int((sample_rate * frame_length * channels) / 1000)
    samples_per_overlapping = int((sample_rate * frame_overlapping * channels) / 1000)
    number_of_frames = len(samples) // (samples_per_frame - samples_per_overlapping) - 1

    frames = _samples_to_frames(_to_mono(samples, channels), number_of_frames, samples_per_frame,
                                samples_per_overlapping)

    decisions = threshold(frames, sample_rate)

    percent = 0.8
    for i in range(_R + _M, number_of_frames):
        limit = min(i + _R, number_of_frames)
        count = sum(int(decisions[i]) for i in range(i, limit))
        decisions[i] = count / (limit - i) >= percent

    return _decisions_to_silence_time_intervals(decisions, frame_length - frame_overlapping)






