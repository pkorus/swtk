import re
import pickle
from swtk.processors import *
from collections import defaultdict

class RareWordProcessor(Plugin):
    help = 'Finds rare words that are frequently used in the manuscript. Rare words...'
    run_priority = 100

    def __init__(self, dictionary_filename='./data/frequent_words.pickle'):
        self.found_words = defaultdict(lambda: 0)
        self.found_tokens = defaultdict(lambda: [])
        # Initialize a list of 5,000 most frequent words in English
        with open(dictionary_filename) as f:
            self.dictionary = pickle.load(f)

    def process_token(self, token):
        if len(token.word) > 4 and token.word.lower() not in self.dictionary:
            if not re.match(r'^[0-9\.,]+$', token.word) and '_' not in token.word and token.word.find('$') == -1:
                # token.reports.append('rareWord')
                self.found_words[token.word] += 1
                self.found_tokens[token.word].append(token)

    def finalize(self, paper):
        # Select only certain sub-set of most frequent words, then sort by frequency
        sortedItems = sorted([(k,v) for (k,v) in self.found_words.iteritems() if v > 5], key=lambda x: x[1], reverse=True)
        # Append numbered css styles to selected tokens
        css_mapping = {}
        current_counter = 1
        for k, tokens in [(k, self.found_tokens[k]) for (k,v) in sortedItems]:
            css_mapping[k] = 'rareWord_{}'.format(current_counter)
            current_counter += 1
            for token in tokens:
                token.reports.append('_'+css_mapping[k]) # Prepend '_' to disable the highlight be default
        # Generate a detailed report and a summary
        if len(sortedItems) > 0:
            detailedReport = [('{} : {}'.format(k,v), css_mapping[k]) for (k,v) in sortedItems]
            summary = 'Top {} : {}'.format(min(3, len(sortedItems)), ', '.join([k for (k,v) in sortedItems[:3]]))
        else:
            detailedReport = None
            summary = 'No rare words found'
        report = Report('Rare words', Plugin.toggle_button_generator(detailedReport), self.help, summary)
        report.css_classes = css_mapping.values()
        paper.reports.append(report)


