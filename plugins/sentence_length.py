import re
from swtk.processors import *
from collections import defaultdict


class SentenceLengthProcessor(Plugin):
    run_priority = 50

    def __init__(self):
        self.stats = defaultdict(lambda: 0)
        self.class_mapping = {'extra long sentences': CSS('longSentence', 'C7E1F7'), 'extra short sentences': CSS('shortSentence', 'D7FFD9')}

    def process_sentence(self, sentence):
        # Refrain from processing section titles
        if sentence.tokens[-1].word not in ['.', '?', '!']:
            return
        # Count only tokens that look like words, discard punctuation and 1 char words
        simple_tokens = [t for t in sentence.tokens if len(t.word) > 1 and re.match(r'^\w+$', t.word)]

        # Final decision
        if len(simple_tokens) > 35:
            sentence.reports.append('_longSentence')
            self.stats['extra long sentences'] += 1
        elif len(simple_tokens) < 5:
            sentence.reports.append('_shortSentence')
            self.stats['extra short sentences'] += 1

    def finalize(self, paper):
        detailedInfo = [('{} : {}'.format(k,v), self.class_mapping[k].name) for (k,v) in sorted(self.stats.iteritems(), key=lambda x : x[1],reverse=True)]
        sentences = paper.stats['sentences']
        if sentences is not None and sentences > 0:
            summary = '{} long sentences ({:.1f}%)'.format(self.stats['extra long sentences'], float(self.stats['extra long sentences'])/sentences*100)
        else:
            summary = '{} long sentences'.format(self.stats['extra long sentences'])
        report = Report('Sentence length', Plugin.toggle_button_generator(detailedInfo), None, summary)
        report.css_classes = self.class_mapping.values()
        paper.reports.append(report)
