__author__ = 'pkorus'

from swtk.processors import *

# TODO This plugin needs a major improvement!
class BuriedVerbProcessor(Plugin):
    run_priority = 75
    counter = 0
    help = 'Finds sentences with potentially buried verbs (far away from the subject).'
    distance_threshold = 3

    def __init__(self):
        pass

    def process_sentence(self, sentence):
        verb_locations = []
        noun_locations = []
        index = 0
        for t in sentence.tokens:
            if hasattr(t, 'pos_tag') and t.pos_tag.startswith('V'):
                verb_locations.append(index)
            if hasattr(t, 'pos_tag') and ((t.pos_tag.startswith('N') and len(t.word) > 1) or t.pos_tag == 'PRP'):
                noun_locations.append(index)
            index += 1
        if len(verb_locations) > 0 and len(noun_locations) > 0:
            # Find closest noun before the first verb
            index = 0
            while index < len(noun_locations) and noun_locations[index] < verb_locations[0]: index += 1
            if index < len(noun_locations):
                distance = (verb_locations[0] - noun_locations[index - 1])
                # Verify if the "words" in between are not actually punctuation marks
                for token in sentence.tokens[noun_locations[index - 1]+1:verb_locations[0]]:
                    if len(token.word) == 1: distance -= 1
                if distance > self.distance_threshold:
                    sentence.tokens[noun_locations[index - 1]].reports.append('_buriedVerbsSubject')
                    sentence.tokens[verb_locations[0]].reports.append('_buriedVerb')
                    sentence.reports.append('_buriedVerbSentence')
                    self.counter += 1
                    # print ''
                    # print sentence
                    # print [(t.word, t.pos_tag) for t in sentence.tokens]

    def finalize(self, paper):
        sentences = paper.stats['sentences']
        if sentences is not None and sentences > 0:
            summary = '{} difficult sentences ({:.1f}%)'.format(self.counter, float(self.counter)/sentences*100)
        else:
            summary = '{} difficult sentences'.format(self.counter)
        report = Report('Buried verbs', ['Sentences with buried verbs: {}'.format(self.counter)], self.help, summary)
        report.css_classes = ['buriedVerbSentence', 'buriedVerb', 'buriedVerbsSubject']
        paper.reports.append(report)
