__author__ = 'emptysamurai'

import argparse
import re
import VAD

parser = argparse.ArgumentParser()
parser.add_argument("audio_path", help="Path to the audio wave file")
parser.add_argument("text", help="Text or path to the text file")
args = parser.parse_args()

text = None

try:
    with open(args.text) as content_file:
        text = content_file.read()
except OSError as err:
    print("Can't find text file. Interpret as plain text")
    text = args.text

#process text
pattern = r"(\S.+?[.!?])(?=\s+|$)"  #end of sentences
sentences = re.findall(pattern, text)

intervals = VAD.get_silence_intervals(args.audio_path)

#sort by length
intervals = sorted(intervals, key=lambda interval: interval.length())

