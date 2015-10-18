import re
from swtk.processors import *
from collections import defaultdict

class WeakVerbProcessor(Plugin):
    help = 'Finds weak, overused verbs like: to be, to do, to have'
    run_priority = 110

    def __init__(self, dictionary_filename='./data/frequent_words.pickle'):
        self.found_words = defaultdict(lambda: 0)
        self.found_tokens = defaultdict(lambda: [])
        self.dictionary = ['am', 'is', 'are', 'do', 'does', 'did', 'didn\'t' , 'isn\'t', 'don\'t', 'doesn\'t', 'have', 'has', 'been', 'were', 'weren\'t', 'had']
        self.counter = 0

    def process_token(self, token):
        if len(token.word) > 1 and token.word.lower() in self.dictionary:
            if not re.match(r'^[0-9\.,]+$', token.word) and '_' not in token.word:
                token.reports.append('_weakVerb')
                self.counter += 1

    def finalize(self, paper):
        # Count all words
        total_words = paper.stats['verbs']
        if total_words is None or total_words == 0:
            summary = '{:,} verbs'.format(self.counter)
        else:
            summary = '{:,} of {:,} verbs ({:.1f}%)'.format(self.counter, total_words, float(self.counter) / total_words * 100)
        report = Report('Weak verbs', None, self.help, summary)
        report.css_classes = [CSS('weakVerb', 'FFFCA0')]
        paper.reports.append(report)
