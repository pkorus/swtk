__author__ = 'pkorus'

import os
import imp
import logging

ignore_tags = ['e']
ignore_tokens = ['.', ',', ';', '[', ']', '(', ')', '-', '$', '!', '?']


def dump_as_list(data):
    if hasattr(data, '__iter__'):
        details = ['<ul>']
        for statistic in data:
            details.append('<li>{}</li>'.format(statistic))
        details.append('</ul>')
        return ''.join(details)
    else:
        return data


def run_text_processor(paper, processor):
    processor.process_text(paper)


def run_sentence_processor(paper, processor):
    for p in paper.content:
        for s in p.get_sentences():
            processor.process_sentence(s)

    processor.finalize(paper)


def run_token_processor(paper, processor):
    for p in paper.content:
        for s in p.get_sentences():
            for t in [t for t in s.tokens if t.word not in ignore_tokens and not t.word.startswith('$')]:
                processor.process_token(t)

    processor.finalize(paper)


class CSS:

    def __init__(self, name, color, custom_style=None):
        self.name = name
        self.color = color
        self.custom_style = custom_style

    def to_css(self):
        if self.custom_style is not None:
            return '.{} {{ {} }}'.format(self.name, self.custom_style)
        else:
            return '.{} {{ background-color: #{}; }}'.format(self.name, self.color)

    def __str__(self):
        return self.name


class Report:

    def __init__(self, label, details, help=None, summary=None):
        self.label = label
        self.details = details
        if help is not None: self.help = help
        if summary is not None: self.summary = summary

    def details_html(self):
        return dump_as_list(self.details)

    def __str__(self):
        return '{} : {}'.format(self.label, ', '.join(self.details))


class PluginManager(type):

    def __init__(cls, name, parents, attributes):
        super(PluginManager, cls).__init__(name, parents, attributes)
        if not hasattr(cls, 'text_processors'):
            cls.text_processors = []
            cls.sentence_processors = []
            cls.token_processors = []
        else:
            instance = cls()
            if attributes.has_key('process_text'):
                logging.debug('Registering text processor plugin %s' % cls)
                cls.text_processors.append(instance)
            if attributes.has_key('process_sentence'):
                logging.debug('Registering sentence processor plugin %s' % cls)
                cls.sentence_processors.append(instance)
            if attributes.has_key('process_token'):
                logging.debug('Registering token processor plugin %s' % cls)
                cls.token_processors.append(instance)


class Plugin:

    __metaclass__ = PluginManager
    run_priority = 100

    def finalize(self, paper):
        pass

    @staticmethod
    def run_all(paper):
        # TODO Add plug-in prioritization - so that other plugins could use info from other plugins
        for p in [p for p in sorted(Plugin.text_processors, key=lambda x: x.run_priority)]:
            run_text_processor(paper, p)
        for p in [p for p in sorted(Plugin.sentence_processors, key=lambda x: x.run_priority)]:
            run_sentence_processor(paper, p)
        for p in [p for p in sorted(Plugin.token_processors, key=lambda x: x.run_priority)]:
            run_token_processor(paper, p)

    @staticmethod
    def register_plugins(path):
        for filename in os.listdir(path):
            if filename.endswith('.py') and filename != '__init__.py':
                module = os.path.splitext(filename)[0]
                mod_obj = globals().get(module)
                if mod_obj is None:
                    f, filename, desc = imp.find_module(module, [path])
                    globals()[module] = mod_obj = imp.load_module(module, f, filename, desc)

    @staticmethod
    def toggle_button_generator(items):
        """
        Generates HTML code for toggle buttons for individual report items.
        :param items: a list of tuples ('report item text', 'CSS class that should be toggled')
        :return: list of strings with HTML code of the buttons
        """
        output = []
        for (i, c) in items:
            if c is None:
                output.append(i)
            else:
                output.append('<div class="toggleButton" data-css="{}">{}</div>'.format(c, i))
        return output

