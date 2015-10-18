import re
import nltk
import math
from swtk.processors import *
from collections import defaultdict


def is_word(word):
    return word not in ignore_tokens


class TextStatsProcessor(Plugin):
    run_priority = 1
    word_regex = r'^[\w\-0-9]+$'

    def __init__(self):
        self.counters = defaultdict(lambda : 0)
        # Reg-expression for rejecting references and figure numbers from token counts
        self.reject_tokens_expression = r'^\[.*\]$'

    def process_text(self, paper):
        # Count characters
        self.counters['characters'] = len(paper.to_raw_text())
        self.counters['begun pages (1,500 chars)'] = int(math.ceil(self.counters['characters'] / 1500.0))
        self.counters['non-space characters'] = len(re.sub(' +','',paper.to_raw_text()))
        self.counters['paragraphs'] = len([x for x in paper.content if x.count_as_paragraph])
        # Count sentences and words
        unique_tokens = set()
        for paragraph in paper.content:
            for sentence in paragraph.get_sentences():
                self.counters['sentences'] += 1
                valid_tokens = [t for t in sentence.tokens if is_word(t.word)]
                self.counters['words'] += len(valid_tokens)
                for token in valid_tokens:
                    unique_tokens.add(token.word)
        # Count unique words
        self.counters['unique words'] = len(unique_tokens)
        # Abstract stats
        abstract = paper.get_abstract()
        self.counters['words (abstract)'] = len([t for t in nltk.word_tokenize(abstract) if is_word(t)])
        self.counters['non-space characters (abstract)'] = len(abstract.replace(' ', ''))
        # Generate report
        details = ['{} : {:,}'.format(k,v) for (k,v) in sorted(self.counters.iteritems(), key=lambda x : x[1],reverse=True)]
        paper.reports.append(Report('Statistics', details, None, '{:,} chars, {:,} words'.format(self.counters['characters'], self.counters['words'])))
        paper.stats.update(self.counters)

