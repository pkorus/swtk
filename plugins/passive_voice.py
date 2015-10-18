from swtk.processors import *


class PassiveVoiceProcessor(Plugin):
    help = 'Finds sentences in passive voice.'
    run_priority = 160
    dictionary = ['is', 'are', 'were', 'was', 'been', 'be']

    def __init__(self, dictionary_filename='./data/frequent_words.pickle'):
        self.counter = 0

    def process_sentence(self, sentence):
        indices = [i for i in range(len(sentence.tokens)-1) if sentence.tokens[i].word.lower() in self.dictionary and sentence.tokens[i+1].pos_tag == 'VBN']
        if len(indices) > 0:
            sentence.reports.append('_passiveVoice')
            self.counter += 1
        for index in indices:
            sentence.tokens[index].reports.append('_passiveVerb')
            sentence.tokens[index+1].reports.append('_passiveVerb')

    def finalize(self, paper):
        sentence_count = paper.stats['sentences']
        percent_info = ' ({:.1f}%)'.format(100*float(self.counter)/sentence_count) if sentence_count is not None and sentence_count > 0 else ''
        summary = '1 sentence' if self.counter == 1 else '{} sentences{}'.format(self.counter, percent_info)
        report = Report('Passive voice sentences', None, self.help, summary)
        report.css_classes = [CSS('passiveVoice', 'D0DEFF'), CSS('passiveVerb', 'ECBFEC')]
        paper.reports.append(report)
        paper.stats['passive voice sentences'] = self.counter
