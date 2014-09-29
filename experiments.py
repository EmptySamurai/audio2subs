
import argparse
import math
import numpy as np
import matplotlib.pyplot as plt
from scipy.io.wavfile import read
import wave


def _short_time_energy(frame):
    return sum(x ** 2 for x in frame)


def _index_to_hz(index, length, sample_rate):
    return index * sample_rate / length


def _hz_to_index(hz, length, sample_rate):
    return round(hz * length / sample_rate)


def _most_dominant_frequency(fft_frame, sample_rate):
    index = max(enumerate(fft_frame), key=lambda x: abs(x[1]))[0]
    return _index_to_hz(index, len(fft_frame), sample_rate)


def _voice_frequency_energy(fft_frame, sample_rate):
    length = len(fft_frame) * 2
    start_index = _hz_to_index(300, length, sample_rate)
    end_index = _hz_to_index(3000, length, sample_rate)
    upper_bound = len(fft_frame)
    return sum(abs(fft_frame[i]) ** 2 for i in range(min(start_index, upper_bound-1), min(end_index + 1, upper_bound)))

def _to_mono(samples, channels):
    if channels == 1:
        return samples
    else:
        return np.array([np.mean(i) for i in np.split(samples, samples // channels)])


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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("audio_path", help="Path to the audio wave file")
    args = parser.parse_args()

    path_to_file = args.audio_path
    (sample_rate, samples) = read(path_to_file)
    audio = wave.open(path_to_file, "rb")
    channels = audio.getnchannels()
    bytes_per_sample = audio.getsampwidth()
    samples = _to_mono(samples, channels)
    samples = np.array(samples, dtype="float") / (2 << 8 * bytes_per_sample)

    frame_length = 10  # ms
    samples_per_frame = int((sample_rate * frame_length) / 1000)
    number_of_frames = len(samples) // samples_per_frame
    frames = np.split(np.resize(samples, len(samples) - len(samples) % number_of_frames), number_of_frames)
    ffts = np.array([np.fft.rfft(frame) for frame in frames])

    energy = np.array([_short_time_energy(frame) for frame in frames])
    dominant_frequencies = np.array([_most_dominant_frequency(frame, sample_rate) for frame in ffts])
    frequency_energy = np.array([_voice_frequency_energy(frame, sample_rate) for frame in ffts])
    spectral_flatness_frames = np.array([_spectral_flatness(frame) for frame in ffts])


    # plotting
    fig, axarr = plt.subplots(5, sharex=True, **{"num": "Measures", "dpi": 150})
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
    axarr[cur].set_title("Voice frequency energy")
    cur += 1
    axarr[cur].plot(np.arange(len(spectral_flatness_frames)) * frame_length / 1000, spectral_flatness_frames, '#92C610')
    axarr[cur].set_title("Spectral flatness")

    axarr[-1].set_xlabel('Time (seconds)')

    fig.set_size_inches(fig.get_size_inches()*2)
    fig.tight_layout()
    plt.savefig("Measures.png", dpi=fig.dpi)

    plt.show()



