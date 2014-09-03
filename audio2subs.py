__author__ = 'emptysamurai'

if __name__ == "__main__":

    import argparse
    import re
    from vad import get_silence_intervals
    from subrip import SubRip
    from pathlib import PurePath
    from timeinterval import TimeInterval
    import sys

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
    except OSError as err:
        print("Can't find text file. Interpret as a plain text.")
        text = args.text

    # process text
    pattern = r"((\d+|(\S(.|\n)+?))([.!?]|$))(?=\s+|$)"  # divide in sentences
    sentences = re.findall(pattern, text)
    for i, sentence in enumerate(sentences):
        if isinstance(sentence, tuple):
            sentences[i] = sentence[0]
    number_of_sentences = len(sentences)


    # select intervals
    intervals = get_silence_intervals(args.audio_path)
    number_of_intervals = number_of_sentences + 1
    if len(intervals) < number_of_intervals:
        print("Error: not enough intervals")
        sys.exit(1)
    intervals = sorted(intervals, key=lambda interval: interval.length, reverse=True)[:number_of_intervals]
    intervals = sorted(intervals, key=lambda interval: interval.begin)

    # create SubRip
    speech_intervals = [None] * (len(intervals) - 1)
    for i in range(len(intervals) - 1):
        speech_intervals[i] = TimeInterval.between(intervals[i], intervals[i + 1])
    subtitles = SubRip(speech_intervals, sentences)
    if args.subtitles_path is not None:
        path_to_subs = args.subtitles_path
    else:
        path_to_subs = PurePath(args.audio_path).with_suffix(".srt")
    with open(str(path_to_subs), 'w') as f:
        f.write(str(subtitles))
