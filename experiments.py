__author__ = 'emptysamurai'

import argparse
import math
import numpy as np
import matplotlib.pyplot as plt
from scipy.io.wavfile import read, write


def short_time_energy(frame):
    return sum([x ** 2 for x in frame])


def index_to_hz(index, length, sample_rate):
    return index * sample_rate / length


def hz_to_index(hz, length, sample_rate):
    return round(hz * length / sample_rate)


def most_dominant_frequency(frame, sampleRate):
    max = frame[0]
    index = 0
    for i in range(len(frame)):
        abs_value = abs(frame[i])
        if abs_value > max:
            max = abs_value
            index = i
    return index_to_hz(index, len(frame), sampleRate)


def voice_frequency_energy(frame, sample_rate):
    length = len(frame) * 2
    start_index = hz_to_index(300, length, sample_rate)
    end_index = hz_to_index(1000, length, sample_rate)
    sum_energy = 0
    for i in range(min(start_index, length / 2), min(end_index + 1, length / 2)):
        sum_energy += abs(frame[i]) ** 2
    return sum_energy


def spectral_flatness(frame):
    arithmetic_mean = 0
    geometric_mean = 0
    for x in frame:
        power = abs(x) ** 2
        if power != 0:
            arithmetic_mean += power
            geometric_mean += math.log(power)
    length = len(frame)
    arithmetic_mean /= length
    geometric_mean = math.exp(geometric_mean / length)
    return 10 * math.log10(geometric_mean / arithmetic_mean)


parser = argparse.ArgumentParser()
parser.add_argument("audio_path", help="Path to the audio wave file")
args = parser.parse_args()

pathToFile = args.audio_path
(sample_rate, samples) = read(pathToFile)
samples = np.array(samples, dtype="float") / (2 << 16)

frame_length = 10  # ms
samples_per_frame = int((sample_rate * frame_length) / 1000)
number_of_frames = len(samples) // samples_per_frame
frames = np.split(np.resize(samples, len(samples) - len(samples) % number_of_frames), number_of_frames)
energy = [short_time_energy(frame) for frame in frames]
ffts = [np.fft.rfft(frame) for frame in frames]
dominant_frequencies = [most_dominant_frequency(frame, sample_rate) for frame in ffts]
frequency_energy = [voice_frequency_energy(frame, sample_rate) for frame in ffts]
spectral_flatness_frames = [spectral_flatness(frame) for frame in ffts]

speech_energy_detection = np.zeros(len(energy))
speech_frequency_energy_detection = np.zeros(len(frequency_energy))
speech_both_energy_detection = np.zeros(len(frequency_energy))

first_frames_silence = 30
mean_energy = 0
mean_frequency_energy = 0
for i in range(first_frames_silence):
    mean_energy += energy[i]
    mean_frequency_energy += frequency_energy[i]
mean_energy /= first_frames_silence
mean_frequency_energy /= first_frames_silence

threshold_level = 10

# detection based on energy
for i in range(first_frames_silence, len(energy)):
    if energy[i] / mean_energy > threshold_level:
        speech_energy_detection[i] = 1

is_speech = False
start_index = 0
for i in range(len(speech_energy_detection)):
    if bool(speech_energy_detection[i]) != is_speech:
        length = i - start_index
        if is_speech and length < 5:
            for j in range(start_index, i):
                speech_energy_detection[j] = 0
            i -= length
        elif (not is_speech) and length < 10:
            for j in range(start_index, i):
                speech_energy_detection[j] = 1
            i -= length
        is_speech = bool(speech_energy_detection[i])
        start_index = i

# detection based on frequency energy
for i in range(first_frames_silence, len(energy)):
    if frequency_energy[i] / mean_frequency_energy > threshold_level:
        speech_frequency_energy_detection[i] = 1

is_speech = False
start_index = 0
for i in range(len(speech_frequency_energy_detection)):
    if bool(speech_frequency_energy_detection[i]) != is_speech:
        length = i - start_index
        if is_speech and length < 5:
            for j in range(start_index, i):
                speech_frequency_energy_detection[j] = 0
            i -= length
        elif (not is_speech) and length < 10:
            for j in range(start_index, i):
                speech_frequency_energy_detection[j] = 1
            i -= length
        is_speech = bool(speech_frequency_energy_detection[i])
        start_index = i

#detection based on both energies
for i in range(first_frames_silence, len(energy)):
    if frequency_energy[i] / mean_frequency_energy > threshold_level and energy[i] / mean_energy > threshold_level:
        speech_both_energy_detection[i] = 1

is_speech = False
start_index = 0
for i in range(len(speech_both_energy_detection)):
    if bool(speech_both_energy_detection[i]) != is_speech:
        length = i - start_index
        if is_speech and length < 5:
            for j in range(start_index, i):
                speech_both_energy_detection[j] = 0
            i -= length
        elif (not is_speech) and length < 10:
            for j in range(start_index, i):
                speech_both_energy_detection[j] = 1
            i -= length
        is_speech = bool(speech_both_energy_detection[i])
        start_index = i

"""#write file without sound
output_name = "no_noise.wav"
for i in range(len(speech_frequency_energy_detection)):
    if not bool(speech_frequency_energy_detection[i]):
        frames[i].fill(0)
output_samples = np.concatenate(tuple(frames))
write(output_name, sampleRate, output_samples)"""


#plotting
f, axarr = plt.subplots(8, sharex=True)
cur = 0
axarr[cur].plot(np.arange(len(samples)) / sample_rate, samples, 'b')
axarr[cur].set_title("Sound")
cur += 1
axarr[cur].plot(np.arange(len(energy)) * frame_length / 1000, energy, 'r')
axarr[cur].set_title("Short-time energy")
cur += 1
axarr[cur].plot(np.arange(len(dominant_frequencies)) * frame_length / 1000, dominant_frequencies, 'g')
axarr[cur].set_title("Most dominant frequencies")
cur += 1
axarr[cur].plot(np.arange(len(frequency_energy)) * frame_length / 1000, frequency_energy, '#00FCF8')
axarr[cur].set_title("Frequency energy")
cur += 1
axarr[cur].plot(np.arange(len(spectral_flatness_frames)) * frame_length / 1000, spectral_flatness_frames, '#92C610')
axarr[cur].set_title("Spectral flatness")
cur += 1
axarr[cur].plot(np.arange(len(speech_energy_detection)) * frame_length / 1000, speech_energy_detection, '#FFA305')
axarr[cur].set_title("Speech detection based on energy")
cur += 1
axarr[cur].plot(np.arange(len(speech_frequency_energy_detection)) * frame_length / 1000,
                speech_frequency_energy_detection,
                '#C905FF')
axarr[cur].set_title("Speech detection based on frequency energy")
cur += 1
axarr[cur].plot(np.arange(len(speech_both_energy_detection)) * frame_length / 1000, speech_both_energy_detection,
                '#DB7093')
axarr[cur].set_title("Speech detection based on both energies")
cur += 1
axarr[-1].set_xlabel('Time (seconds)')
plt.show()



