import os
import logging
from swtk.processors import *


class HelpProcessor(Plugin):
    run_priority = 0

    def __init__(self):
        filename = '{}/guidelines.html'.format(os.path.split(__file__)[0].replace('/plugins', '/data'))
        if not os.path.exists(filename):
            logging.error('Cannot open file {}'.format(filename))
        else:
            with open(filename) as f:
                self.content = f.read()

    def process_text(self, paper):
        if hasattr(self, 'content'):
            paper.reports.append(Report('Getting started', None, self.content, None))
