__author__ = 'emptysamurai'

import matplotlib.pyplot as plt
import numpy as np
import argparse
import wave
import vad
from scipy.io.wavfile import read

def _time_in_interval(ms, intervals):
    for interval in intervals:
        if interval.contains(ms):
            return True
    return False

def _short_time_energy(frame, sample_rate):
    return sum(x ** 2 for x in frame)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("audio_path", help="Path to the audio wave file")
    args = parser.parse_args()

    step = 10

    path_to_file = args.audio_path
    (sample_rate, samples) = read(path_to_file)
    audio = wave.open(path_to_file, "rb")
    sample_rate = audio.getframerate()
    channels = audio.getnchannels()
    number_of_samples = audio.getnframes()
    duration = int(number_of_samples / channels / sample_rate * 1000)

    my_vad_intervals = vad.get_silence_intervals(path_to_file)
    vad._voice_frequency_energy = _short_time_energy
    energy_vad_intervals = vad.get_silence_intervals(path_to_file)

    my_vad_decisions = np.array([not _time_in_interval(t, my_vad_intervals) for t in range(0, duration, step)])
    energy_vad_decisions = np.array([not _time_in_interval(t, energy_vad_intervals) for t in range(0, duration, step)])

    fig, axarr = plt.subplots(3, sharex=True, **{"num": "Energies comparison", "dpi": 150})

    cur = 0
    axarr[cur].plot(np.arange(len(samples)) / sample_rate, samples, 'b')
    axarr[cur].set_title("Sound")
    cur += 1
    axarr[cur].fill_between(np.arange(len(my_vad_decisions)) * step / 1000, 0, my_vad_decisions, facecolor='r')
    axarr[cur].set_ylim(0, 1.2)
    axarr[cur].set_title("My VAD")
    cur += 1
    axarr[cur].fill_between(np.arange(len(energy_vad_decisions)) * step / 1000, 0, energy_vad_decisions, facecolor='g')
    axarr[cur].set_ylim(0, 1.2)
    axarr[cur].set_title("Energy VAD")

    axarr[cur].set_xlabel('Time (seconds)')

    fig.set_size_inches(fig.get_size_inches()*2)
    fig.tight_layout()
    plt.savefig("Energies comparison.png", dpi=fig.dpi)

    plt.show()