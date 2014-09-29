import argparse
import re
from vad import get_silence_intervals
from subrip import SubRip
from pathlib import PurePath
from timeinterval import TimeInterval
import wave
import sys
from num2words import num2words


def _is_character(char):
    lower = char.lower()
    return 'a' <= lower <= 'z' or 'а' <= lower <= 'я'


def _is_vowel(char):
    vowels = ('a', 'e', 'i', 'o', 'u', 'а', 'у', 'о', 'ы', 'и', 'э', 'я', 'ю', 'ё', 'е')
    return char.lower() in vowels


def _character_points(char):
    if _is_character(char):
        if _is_vowel(char):
            return 3
        else:
            return 1
    return 0


def _sentence_points(sentence):
    points = 0
    sentence = _replace_numbers(sentence)
    for character in sentence:
        points += _character_points(character)
    return points


def _replace_numbers(string):
    string = string.replace("$", "dollars")
    return re.sub(r"\d+", lambda n: num2words(int(n.group(0))), string)

if __name__ == "__main__":

    # parse arguments
    parser = argparse.ArgumentParser(
        description="Generates SubRip (srt) subtitles for the given audio file with speech and text")
    parser.add_argument("audio_path", help="Path to the audio wave file")
    parser.add_argument("text", help="Text or path to the text file")
    parser.add_argument("subtitles_path", nargs='?', help="Path to save subtitles")
    args = parser.parse_args()

    try:
        with open(args.text) as content_file:
            text = content_file.read()
    except Exception as err:
        print(str(err))
        sys.exit(1)

    # process text
    pattern = r"((\d+|(\S(.|\n)+?))(…|\.+|[!?]|$))(?=\s+|$|\n+)"  # divide in sentences
    sentences = re.findall(pattern, text)
    for i, sentence in enumerate(sentences):
        if isinstance(sentence, tuple):
            sentences[i] = sentence[0]
    number_of_sentences = len(sentences)

    # select intervals
    try:
        intervals = get_silence_intervals(args.audio_path)
    except Exception as err:
        print(str(err))
        sys.exit(1)

    number_of_intervals = number_of_sentences + 1
    audio = wave.open(args.audio_path, 'rb')
    audio_length = audio.getnframes() / audio.getframerate() / audio.getnchannels() * 1000

    sentences_points = [_sentence_points(sentence) for sentence in sentences]
    silence_intervals_length = sum(interval.length for interval in intervals)
    average_silence_interval_length = silence_intervals_length / len(intervals)
    audio_length -= silence_intervals_length
    average_speed = audio_length / sum(sentences_points)
    sentences_lengths = [average_speed * sentence_points for sentence_points in sentences_points]
    time_sorted_intervals = sorted(intervals, key=lambda interval: interval.begin)
    result_intervals = [time_sorted_intervals[0]]
    for sentence_length in sentences_lengths:
        min_sentence_length = sentence_length * 0.5
        max_sentence_length = sentence_length * 1.8
        longest_interval = None
        previous_interval = result_intervals[-1]
        for interval in time_sorted_intervals:
            if interval.is_later(previous_interval.end):
                sentence_interval_length = TimeInterval.between(previous_interval, interval).length
                if min_sentence_length < sentence_interval_length < max_sentence_length:
                    if longest_interval is None or longest_interval.length < interval.length:
                        longest_interval = interval
                elif sentence_interval_length >= max_sentence_length:
                    break
        if longest_interval is None:
            end = previous_interval.end + sentence_length
            if sentence_length > average_silence_interval_length:
                result_intervals.append(TimeInterval(end - average_silence_interval_length, end))
            else:
                result_intervals.append(TimeInterval(end - sentence_length / 2.5, end))
        else:
            result_intervals.append(longest_interval)
    intervals = result_intervals

    # create SubRip
    speech_intervals = [None] * (len(intervals) - 1)
    for i in range(len(intervals) - 1):
        speech_intervals[i] = TimeInterval.between(intervals[i], intervals[i + 1])
    subtitles = SubRip(speech_intervals, sentences)
    try:
        if args.subtitles_path is not None:
            path_to_subs = args.subtitles_path
        else:
            path_to_subs = PurePath(args.audio_path).with_suffix(".srt")
        with open(str(path_to_subs), 'w') as f:
            f.write(str(subtitles))
    except Exception as err:
        print(str(err))
        sys.exit(1)