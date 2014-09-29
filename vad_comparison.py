__author__ = 'emptysamurai'

import matplotlib.pyplot as plt
import numpy as np
import argparse
import wave
import vad
import simple_vad
import lsfm_vad
from scipy.io.wavfile import read
from timeit import Timer


def _time_in_interval(ms, intervals):
    for interval in intervals:
        if interval.contains(ms):
            return True
    return False


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
    simple_vad_intervals = simple_vad.get_silence_intervals(path_to_file)
    lsfm_vad_intervals = lsfm_vad.get_silence_intervals(path_to_file)

    my_vad_decisions = np.array([not _time_in_interval(t, my_vad_intervals) for t in range(0, duration, step)])
    simple_vad_decisions = np.array([not _time_in_interval(t, simple_vad_intervals) for t in range(0, duration, step)])
    lsfm_vad_decisions = np.array([not _time_in_interval(t, lsfm_vad_intervals) for t in range(0, duration, step)])

    repeat_times = 10
    my_vad_time = Timer(lambda: vad.get_silence_intervals(path_to_file)).timeit(repeat_times)
    simple_vad_time = Timer(lambda: simple_vad.get_silence_intervals(path_to_file)).timeit(repeat_times)
    lsfm_vad_time = Timer(lambda: lsfm_vad.get_silence_intervals(path_to_file)).timeit(repeat_times)

    times = np.array([my_vad_time, simple_vad_time, lsfm_vad_time])

    fig, axarr = plt.subplots(5, sharex=True, **{"num": "VAD Comparison", "dpi": 150})

    cur = 0
    axarr[cur].plot(np.arange(len(samples)) / sample_rate, samples, 'b')
    axarr[cur].set_title("Sound")
    cur += 1
    axarr[cur].fill_between(np.arange(len(my_vad_decisions)) * step / 1000, 0, my_vad_decisions, facecolor='r')
    axarr[cur].set_ylim(0, 1.2)
    axarr[cur].set_title("My VAD")
    cur += 1
    axarr[cur].fill_between(np.arange(len(simple_vad_decisions)) * step / 1000, 0, simple_vad_decisions, facecolor='g')
    axarr[cur].set_ylim(0, 1.2)
    axarr[cur].set_title("Simple VAD")
    cur += 1
    axarr[cur].fill_between(np.arange(len(lsfm_vad_decisions)) * step / 1000, 0, lsfm_vad_decisions,
                            facecolor='#00FCF8')
    axarr[cur].set_ylim(0, 1.2)
    axarr[cur].set_title("LSFM VAD")

    axarr[cur].set_xlabel('Time (seconds)')

    cur += 1
    ind = np.arange(len(times)) * duration / 1000 / len(times)
    rects = axarr[cur].bar(ind, times, color=("r", "g", "#00FCF8"))
    axarr[cur].legend(rects, ("My VAD", "Simple VAD", "LSFM VAD"))
    axarr[cur].set_title(str(repeat_times) + " executions time")
    axarr[cur].set_ylabel('Time (seconds)')

    fig.set_size_inches(fig.get_size_inches()*2)
    fig.tight_layout()
    plt.savefig("VAD comparison.png", dpi=fig.dpi)

    plt.show()

