import nltk
from swtk.processors import *
from collections import defaultdict


class POSTaggerProcessor(Plugin):
    run_priority = 2
    help = 'Part of speech (POS) tagger based on maximal entropy. <ul><li>Counts occurrences of specific tags</li>' \
           '<li>Highlights verbs, modals, and adjectives.</li></ul>' \
           'POS tagging is not 100% accurate - the statistics & tags should be considered ' \
           'as estimates.'

    # Which POS tags should be highlighted
    highlight = {'MD': 'pos_modals', 'VB': 'pos_verb', 'VBD': 'pos_verb', 'VBG': 'pos_verb', 'VBN': 'pos_verb',
                 'VBP': 'pos_verb', 'VBZ': 'pos_verb', 'RB': 'pos_adverb'}

    # Maps counters to css class names
    toggle_specs = defaultdict(lambda: None, {'modals': 'pos_modals', 'verbs': 'pos_verb', 'adverbs': 'pos_adverb'})

    # Maps POS tags to counters
    counter_mapping = {'VBG': 'gerunds', 'VBD': 'verbs, past tense',
                       'VBN': 'verbs, past participle', 'JJ': 'adjectives', 'IN': 'preposition',
                       'RB': 'adverbs', 'PRP': 'personal pronoun', 'MD': 'modals', 'JJR': 'adjectives, comparative',
                       'JJS': 'adjectives, superlative'}

    # Colors
    color_mapping = {'pos_modals': 'C5E9FF', 'pos_verb': 'F5E679', 'pos_adverb': 'F1C5FF'}

    def __init__(self):
        self.counters = defaultdict(lambda: 0)

    def process_text(self, paper):
        # Count characters
        for paragraph in [p for p in paper.content if p.count_as_paragraph]:
            for sentence in paragraph.get_sentences():

                # TODO POS tagger seems to get confused by things like Fig. 2 ('Fig', '.', '2') - can this be fixed?
                tagged = nltk.pos_tag([t.word for t in sentence.tokens])
                item_id = 0

                for w, t in tagged:
                    # Check for general classes of tags
                    if t.startswith('V'): self.counters['verbs'] += 1
                    if t.startswith('N'): self.counters['nouns'] += 1
                    # Check specific tags
                    if self.counter_mapping.has_key(t):
                        self.counters[self.counter_mapping[t]] += 1
                    # Add tag to the token object
                    sentence.tokens[item_id].pos_tag = t
                    # Highlight, if applicable
                    if self.highlight.has_key(t):
                        sentence.tokens[item_id].reports.append('_'+self.highlight[t])
                    item_id += 1

        details = [('{} : {:,}'.format(k, v), self.toggle_specs[k]) for (k, v) in sorted(self.counters.iteritems(), key=lambda o: o[1], reverse=True)]
        summary = '{:,} verbs, {:,} nouns'.format(self.counters['verbs'], self.counters['nouns'])
        report = Report('Part of Speech Tagger', Plugin.toggle_button_generator(details), self.help, summary)
        # report.css_classes = [x for x in set(self.highlight.values()) if x is not None]
        report.css_classes = [CSS(name, self.color_mapping[name]) for name in self.highlight.values()]
        paper.reports.append(report)
        paper.stats.update(self.counters)
