import re
import nltk
import json
from swtk.processors import *


def find_sequence(long_sequence, sequence_pattern):
    return [(i, i+len(sequence_pattern)) for i in range(len(long_sequence)) if long_sequence[i:i+len(sequence_pattern)] == sequence_pattern]

class FilterWordsProcessor(Plugin):
    help = 'Finds vague and colloquial words and phrases typical for spoken language. If possible, offers an explanation or a substitute.'
    run_priority = 150
    dictionary_filename = './data/filter_words.json'

    def __init__(self, dictionary_filename='./data/frequent_words.pickle'):
        self.found_phrases = set()
        self.found_words = set()
        with open(self.dictionary_filename) as f:
            self.dictionary = json.loads(f.read().decode())
        self.counter = 0

    def __process_token(self, token):
        if len(token.word) > 1 and token.word.lower() in self.dictionary['words']:
            if not re.match(r'^[0-9\.,]+$', token.word) and '_' not in token.word:
                self.found_words.add(token.word.lower)
                token.reports.append('_filterWord')
                self.counter += 1

    def process_sentence(self, sentence):
        # Match words in the dictionary
        for token in sentence.tokens:
            self.__process_token(token)
        # Match phrases in the dictionary
        for pattern in self.dictionary['phrases'].keys():
            if sentence.__str__().lower().find(pattern) >= 0:
                # Find specific tokens that constitute the phrase
                self.found_phrases.add(pattern)
                indices = find_sequence([x.word.lower() for x in sentence.tokens], nltk.word_tokenize(pattern))
                for index in indices:
                    for i in range(*index):
                        sentence.tokens[i].reports.append('_filterPhrase')

    def finalize(self, paper):
        # Generate a short summary
        summary = []
        if len(self.found_words) == 1:
            summary.append('1 word')
        elif len(self.found_words) > 1:
            summary.append('{} words'.format(len(self.found_words)))

        if len(self.found_phrases) > 0:
            summary.append(' and ')
            if len(self.found_phrases) == 1:
                summary.append('1 phrase')
            else:
                summary.append('{} phrases'.format(len(self.found_phrases)))

        # List found phrases, recommendations & summarize filter words
        details = ['{} - {}'.format(k,self.dictionary['phrases'][k]) for k in self.found_phrases]
        details.append('{} filter words'.format(self.counter))
        report = Report('Filter words & phrases', details, self.help, ''.join(summary))
        report.css_classes = [CSS('filterWord', 'FF9494'), CSS('filterPhrase', 'FF9494')]
        paper.reports.append(report)
