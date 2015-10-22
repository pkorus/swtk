import re
from swtk.processors import *
from collections import defaultdict


class AbbreviationsProcessor(Plugin):
    help = 'Finds frequently used abbreviations, e.g., DCT, DWT.'
    run_priority = 110
    min_occurrences = 2

    def __init__(self):
        self.found_words = defaultdict(lambda: 0)
        self.found_tokens = defaultdict(lambda: [])

    def process_token(self, token):
        if len(token.word) <= 5 and re.match('^[A-Z]{2,5}$', token.word):
            self.found_words[token.word] += 1
            self.found_tokens[token.word].append(token)

    def finalize(self, paper):
        # Select only certain sub-set of most frequent words, then sort by frequency
        sortedItems = sorted([(k,v) for (k,v) in self.found_words.iteritems() if v >= self.min_occurrences], key=lambda x: x[1], reverse=True)
        # Append numbered css styles to selected tokens
        css_mapping = {}
        current_counter = 1
        color_index = 240
        for k, tokens in [(k, self.found_tokens[k]) for (k,v) in sortedItems]:
            css_mapping[k] = CSS('abbrev_{}'.format(current_counter), '{0:02x}{0:02x}{1:02x}'.format(color_index, 0))
            color_index = max(color_index - 8, 208)
            current_counter += 1
            for token in tokens:
                token.reports.append('_'+css_mapping[k].name)
        # Generate a detailed report and a summary
        if len(sortedItems) > 0:
            detailedReport = [('{} : {}'.format(k,v), css_mapping[k].name) for (k,v) in sortedItems]
            summary = 'Top {} : {}'.format(min(3, len(sortedItems)), ', '.join([k for (k,v) in sortedItems[:3]]))
        else:
            detailedReport = None
            summary = 'No abbreviations found'
        report = Report('Abbreviations', Plugin.toggle_button_generator(detailedReport), self.help, summary)
        report.css_classes = css_mapping.values()
        paper.reports.append(report)


