import nltk
from swtk.processors import *
from collections import defaultdict


def generate_token_triples(tokens):
    output = []
    for i in range(len(tokens)-2):
        output.append(tuple(v.word.lower() for v in tokens[i:i+3]))
    return output


class TrigramProcessor(Plugin):
    run_priority = 101
    min_frequency = 3
    min_chars = 4
    help = 'Frequently occurring (at least {} times) triples of words.'.format(min_frequency)

    def __init__(self):
        self.counters = defaultdict(lambda : 0)
        # Reg-expression for rejecting references and figure numbers from token counts
        self.reject_tokens_expression = r'^\[.*\]$'

    def process_text(self, paper):
        # Find bigrams and their frequencies
        words = nltk.word_tokenize(paper.to_raw_text().lower())
        distribution = nltk.FreqDist(nltk.trigrams(words))
        # Leave only bigrams that meet the requirements for minimum bigram frequency and word length
        distribution = [ (k, v) for (k,v) in distribution.iteritems() if v >= self.min_frequency and len(k[0]) >= self.min_chars and len(k[1]) >= self.min_chars and len(k[2]) >= self.min_chars]
        distribution = sorted(distribution, key=lambda x: x[1], reverse=True)

        # Generate unique CSS classes for successive bigrams
        css_mapping = {}
        bigram_id = 1
        color_index = 192
        for pattern, freq in distribution:
            css_mapping['{} {} {}'.format(*pattern)] = CSS('trigram_{}'.format(bigram_id), '{0:02x}{1:02x}{0:02x}'.format(int(color_index*0.65), color_index))
            color_index = min(color_index + 2, 255)
            bigram_id += 1

        # Highlight bigrams in the text
        for p in paper.content:
            for s in p.get_sentences():
                item_id = 0
                for bg in generate_token_triples(s.tokens):
                    for pattern, freq in distribution:
                        if pattern == bg:
                            current_class = '_'+css_mapping['{} {} {}'.format(*pattern)].name # Prepend '_' do disable the highlight by default
                            s.tokens[item_id].reports.append(current_class)
                            s.tokens[item_id+1].reports.append(current_class)
                            s.tokens[item_id+2].reports.append(current_class)
                    item_id += 1

        # Generate report
        if len(distribution) > 0:
            details = [('{} {} {} : {}'.format(k[0], k[1], k[2], v), css_mapping['{} {} {}'.format(*k)].name) for (k,v) in distribution]
            summary = '{} popular trigrams: {} {} {}, ...'.format(len(distribution), *distribution[0][0])
        else:
            details = None
            summary = 'No frequent trigrams'

        report = Report('Trigrams', Plugin.toggle_button_generator(details), self.help, summary)
        report.css_classes = css_mapping.values()
        paper.reports.append(report)
