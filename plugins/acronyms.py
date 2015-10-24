import re
from swtk.processors import *
from collections import defaultdict, deque


class AcronymProcessor(Plugin):
    help = 'Finds frequently used capital-letter acronyms (e.g., IEEE) and checks if they are explained in the text.'
    run_priority = 110
    min_occurrences = 2
    max_length = 6

    def __init__(self):
        self.found_words = defaultdict(lambda: 0)
        self.found_tokens = defaultdict(lambda: [])
        self.cache = deque(maxlen=self.max_length)
        self.defined = set()
        self.regex = '^[A-Z]{{2,{}}}$'.format(self.max_length)

    def is_defined(self,word):
        return '' if word in self.defined else ' (possibly undefined)'

    def process_token(self, token):
        if len(token.word) <= self.max_length and re.match(self.regex, token.word):
            self.found_words[token.word] += 1
            self.found_tokens[token.word].append(token)
            # check if the current acronym is "defined" by the words in the cache
            # TODO a more sophisticated fuzzy matching would be nice
            # TODO Consider using human-provided hints - capital letters in the definition
            if len(self.cache) >= len(token.word) and self.cache[-1].lower() not in ['and', 'the']:
                cache_extract = [w[0].upper() for w in self.cache][(self.max_length-len(token.word)):]
                if token.word == ''.join(cache_extract):
                    self.defined.add(token.word)
        # Add to cache
        if len(token.word) > 2:
            self.cache.append(token.word.lower())

        # A period clears the cache
        if token.word == '.':
            self.cache.clear()

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
            detailedReport = [('{} : {}{}'.format(k,v,self.is_defined(k)), css_mapping[k].name) for (k,v) in sortedItems]
            summary = 'Top {} : {}'.format(min(3, len(sortedItems)), ', '.join([k for (k,v) in sortedItems[:3]]))
        else:
            detailedReport = None
            summary = 'No acronyms found'

        report = Report('Acronyms', Plugin.toggle_button_generator(detailedReport), self.help, summary)
        report.css_classes = css_mapping.values()
        paper.reports.append(report)


