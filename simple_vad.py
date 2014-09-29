__author__ = 'emptysamurai'

# Just bad VAD for demonstration
# http://www.eurasip.org/Proceedings/Eusipco/Eusipco2009/contents/papers/1569192958.pdf


import math
import numpy as np
import wave
import struct
from timeinterval import TimeInterval


def _index_to_hz(index, length, sample_rate):
    return index * sample_rate / length


def _frame_energy(frame):
    return sum(x ** 2 for x in frame)


def _spectral_flatness(fft_frame):
    arithmetic_mean = 0
    geometric_mean = 0
    for x in fft_frame:
        power = abs(x) ** 2
        if power != 0:
            arithmetic_mean += power
            geometric_mean += math.log(power)
    length = len(fft_frame)
    arithmetic_mean /= length
    geometric_mean = math.exp(geometric_mean / length)
    if arithmetic_mean == 0:
        return 0
    else:
        return 10 * math.log10(geometric_mean / arithmetic_mean)


def _most_dominant_frequency(fft_frame, sample_rate):
    index = max(enumerate(fft_frame), key=lambda x: abs(x[1]))[0]
    return _index_to_hz(index, len(fft_frame), sample_rate)


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
        raise ValueError("Can't read " + str(bytes_per_frame) + "-byte audio")

    return np.array(struct.unpack("<" + str(length) + int_type, samples_bytes))


def _to_mono(samples, channels):
    if channels == 1:
        return samples
    else:
        return np.array([np.mean(i) for i in np.split(samples, samples // channels)])


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
    min_frames_speech = 5
    min_frames_silence = 10
    energy_prim_thresh = 40
    f_prim_thresh = 185
    sf_prim_thresh = 5

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
    decisions = [False] * number_of_frames

    min_e = None
    min_f = None
    min_sf = None

    thresh_e = 0
    thresh_f = 0
    thresh_sf = 0

    silence_count = 0
    # main evaluation
    read_samples = read_frames * samples_per_frame
    while current_frame < number_of_frames:
        if number_of_frames - current_frame < read_frames:
            read_frames = number_of_frames - current_frame
            read_samples = read_frames * samples_per_frame

        samples_bytes = audio.readframes(read_samples)
        samples = _to_mono(_bytes_to_samples(samples_bytes, bytes_per_frame), channels)
        frames = _samples_to_frames(samples, read_frames)
        for frame in frames:
            e = _frame_energy(frame)
            frame_fft = np.fft.rfft(frame)
            f = _most_dominant_frequency(frame_fft, sample_rate)
            sfm = _spectral_flatness(frame_fft)
            if current_frame < first_frames_silence:
                if min_e is None:
                    min_e = e
                else:
                    min_e = min(e, min_e)

                if min_f is None:
                    min_f = f
                else:
                    min_f = min(f, min_f)

                if min_sf is None:
                    min_sf = sfm
                else:
                    min_sf = min(sfm, min_sf)

                decisions[current_frame] = False

            else:
                thresh_e = energy_prim_thresh * math.log(min_e)
                thresh_f = f_prim_thresh
                thresh_sf = sf_prim_thresh

                counter = 0
                if e - min_e >= thresh_e:
                    counter += 1

                if f - min_f >= thresh_f:
                    counter += 1

                if sfm - min_sf >= thresh_sf:
                    counter += 1

                if counter > 1:
                    decisions[current_frame] = True
                else:
                    decisions[current_frame] = False
                    min_e = (silence_count * min_e + e) / (silence_count + 1)
                    silence_count += 1

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