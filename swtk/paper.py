# coding=utf-8
__author__ = 'pkorus'

import re, nltk.data, os, logging
from collections import defaultdict

# Read data for the sentence tokenizer
sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')

# Flag for experimental math support
math = False
# Display standalone equations
display_math = False
# Parse floats
display_floats = False


def word_splitter(text):
    # Make initial split using nltk
    initial_split = nltk.word_tokenize(text)
    if not math: return initial_split
    final_split = []
    # Merge math expressions
    expression = []
    for t in initial_split:
        if t == '$' or len(expression) > 0:
            expression.append(t)
            if t == '$' and len(expression) > 1:
                final_split.append(' '.join(expression))
                expression = []
        else:
            final_split.append(t)
    return final_split


def sentence_splitter(text, custom_replacements):
    return [Sentence(s, custom_replacements) for s in sent_detector.tokenize(text.strip())]


def read_data(filename):
    with open(filename) as f:
        return f.read()


def parse_tex_command(line, strip_inside=True):
    logging.info('Parsing command {:.50}'.format(line))
    braces = []
    content = []
    isCommand = False
    for c in line:

        if c == '{':
            braces.append('{')
            isCommand = False
            if strip_inside or len(braces) == 1:
                continue
        elif c == '}':
            b = braces.pop()
            if not b == '{':
                raise Exception('Parsing Error')
            if len(braces) == 0:
                break
            isCommand = False
            if strip_inside or len(braces) == 0:
                continue
        elif c == ' ':
            isCommand = False
        elif c == '\\':
            isCommand = True
            if strip_inside or len(braces) == 0:
                continue

        if (len(braces) == 1 or (not strip_inside and len(braces) > 1)) and not (strip_inside and isCommand):
            if c == '~': c = ' '
            if len(content) == 0 or not (c == ' ' and content[-1] == ' '):
                content.append(c)

    while len(content) > 0 and (content[-1] == ' ' or content[-1] == ','): content.pop()
    return ''.join(content)


def get_environment_name(body):
    name = re.findall('begin{([a-z\\*]+)}', body)
    return name[0] if len(name) > 0 else None


def parse_latex_environment(body):
    """
    Extracts the content of a LaTeX environment.
    :param body: string with LaTeX syntax
    :return: content of the first identified environment
    """
    # Find the name of the environment
    logging.info('Parsing environment {:.50}'.format(body))

    name = re.findall('begin{([a-z\\*]+)}', body)

    if len(name) == 0:
        logging.warn('Error while parsing LaTeX environment: {:.20}'.format(body))
        return

    # Find the locations of the begin and end commands
    e_pattern = r'\end{{{}}}'.format(name[0])
    b_pattern = r'\begin{{{}}}'.format(name[0])
    end_index = body.find(e_pattern)
    start_index = body.find(b_pattern)

    if end_index < 0 or start_index < 0:
        logging.error('Error while parsing LaTeX environment: {:.20}'.format(body))
        return

    # Return the content in between
    return body[start_index+len(b_pattern):end_index]


class Token:

    def __init__(self, word):
        self.word = word
        self.reports = []
        self.alternatives = []
        self.pos_tag = ''

    def __str__(self):
        return self.word

    def to_html(self):
        if len(self.reports) == 0:
            if math and self.word.startswith('$'):
                return r'\({}\)'.format(self.word[1:-1])
            else:
                return self.word
        else:
            alt_html = ' data-alt="{}"'.format(', '.join(self.alternatives)) if len(self.alternatives) > 0 else ''
            return '<span class="{}"{}>{}</span>'.format(' '.join(self.reports), alt_html, self.word)


class Sentence:

    tokenization_fix = {' .': '.', ' ,': ',', ' ?': '?',' :': ':', ' ;': ';',
                        '[ ': '[', ' ]': ']', '( ': '(', ' )': ')', ' \'s ': '\'s '}

    def __init__(self, raw, custom_replacements = None):
        self.raw = raw
        # General replacements
        raw = re.sub(r' +', ' ', raw)
        # Custom replacements (for handling various text formats)
        if custom_replacements is not None:
            for k, v in custom_replacements.iteritems():
                raw = re.sub(k, v, raw)
        # When done, tokenize
        self.reports = []
        self.tokens = [Token(t) for t in word_splitter(raw.replace('~', ' '))]

    def __str__(self):
        return ' '.join([t.__str__() for t in self.tokens])

    def to_html(self):
        candidate = ' '.join([t.to_html() for t in self.tokens])
        # Fix problems with tokenization of punctuation marks
        for (k,v) in self.tokenization_fix.iteritems(): candidate = candidate.replace(k, v)
        return candidate


class TextBlock(object):

    def __init__(self, body):
        self.reports = []
        self.count_as_paragraph = False

    def get_sentences(self):
        raise NotImplementedError("Class %s doesn't implement get_sentences()" % (self.__class__.__name__))

    def to_html(self):
        raise NotImplementedError("Class %s doesn't implement to_html()" % (self.__class__.__name__))

    def __str__(self):
        s_preamble = ''
        output = ['  {} : '.format(self.__class__.__name__)]
        sentences = self.get_sentences()
        if len(sentences) > 1 :
            output.append('[{} sentences]\n'.format(len(sentences)))
            s_preamble = '      '
        for s in sentences:
            output.append('{}{:.50} '.format(s_preamble, s))
            output.append('[{}]\n'.format(', '.join(s.reports)))
        return ''.join(output)

    def to_raw_text(self):
        return ' '.join([s.__str__() for s in self.get_sentences()])


class Float(TextBlock):

    def __init__(self, body, custom_replacements=None):
        TextBlock.__init__(self, body)
        index = body.find(r'\caption{')
        if index >= 0:
            body_fragment = body[index:]
            self.__content = Paragraph(parse_tex_command(body_fragment, False), 'float', custom_replacements)

    def get_sentences(self):
        return self.__content.get_sentences()

    def to_html(self):
        return self.__content.to_html()


class Section(TextBlock):

    def __init__(self, body, html_tag):
        TextBlock.__init__(self, body)
        self.__html_tag = html_tag
        self.__content = Sentence(body)

    def get_sentences(self):
        return [self.__content]

    def to_html(self):
        return '<{0}>{1}</{0}>'.format(self.__html_tag, self.__content)


class Equation(TextBlock):

    def __init__(self, body):
        TextBlock.__init__(self, body)
        self.__equation = parse_latex_environment(body)

    def get_sentences(self):
        return []

    def to_html(self):
        return '<p class="equation">$${}$$</p>'.format(self.__equation)


class Enumeration(TextBlock):

    def __init__(self, body, numbered=False, split_string='\n', syntax_replacements=None):
        TextBlock.__init__(self, body)
        self.count_as_paragraph = True
        self.numbered = numbered
        # Split items
        self.__content = [Paragraph(o.strip(), syntax_replacements=syntax_replacements) for o in re.split(split_string, body) if len(o.strip()) > 0]

    def get_sentences(self):
        sentences = []
        for p in self.__content:
            for s in p.get_sentences():
                sentences.append(s)
        return sentences

    def to_html(self):
        output = []
        output.append('<ul>' if not self.numbered else '<ol>')
        for p in self.__content:
            output.append('<li>{}</li>'.format(p.to_html()))
        output.append('</ul>' if not self.numbered else '</ol>')
        return ''.join(output)


class Paragraph(TextBlock):

    def __init__(self, body, html_class=None, syntax_replacements=None):
        TextBlock.__init__(self, body)
        self.count_as_paragraph = True
        self.html_class = html_class
        self.__sentences = sentence_splitter(body, syntax_replacements)

    def get_sentences(self):
        return self.__sentences

    def to_html(self):
        output = []
        # if math and self.tag == 'e': output.append(r'$$')
        for s in self.__sentences:
            if len(s.reports) > 0:
                output.append('<span class="{}">{}</span>'.format(' '.join(s.reports), s.to_html()))
            else:
                output.append(s.to_html())
        # if math and self.tag == 'e': output.append(r'$$')
        format_class = '' if self.html_class is None else ' class="{}"'.format(self.html_class)
        return '<p{}>{}</p>'.format(format_class, ' '.join(output))


class Paper:
    resources = {'css': './data/default.css',
                 'js': './data/default.js',
                 'jquery': './data/jquery-2.1.4.min.js',
                 'math': 'https://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML'
                 }

    def __init__(self, lines, resources):
        # Configure structures for paper content
        self.meta = {}
        self.content = []
        # Parse
        self.parse(lines)
        # Configure structures for storing reports
        self.reports = []
        self.stats = defaultdict(lambda: None)
        self.resources.update(resources)

    def parse(self, lines):
        pass

    def __str__(self):
        return '<Paper "{}" by {} : {} paragraphs>'.format(self.meta['title'], self.meta['author'], len(self.content))

    def to_summary(self):
        output = ['Paper:\n']
        for k, v in self.meta.iteritems():
            output.append('  %s = %s\n' % (k,v))
        output.append('Content:\n')
        for p in self.content:
            output.append('  {}\n'.format(p))
        return ''.join(output)

    def to_raw_text(self):
        if hasattr(self, 'raw_text_cache'):
            return self.raw_text_cache
        else:
            output = []
            for p in self.content:
                output.append('{}\n\n'.format(p.to_raw_text()))
            self.raw_text_cache = ' '.join(output)
            return self.raw_text_cache

    def get_abstract(self):
        output = []
        for p in [p for p in self.content if type(p) is Paragraph and p.html_class == 'abstract']:
            output.append('{}\n\n'.format(p.to_raw_text()))
        return ' '.join(output)

    def to_html(self, external=False):
        output = []
        # Write html preamble
        output.append('<html><head>')
        output.append('<meta http-equiv="Content-Type" content="text/html; charset=utf-8">')
        # Embed or reference external resources
        if external:
            output.append('<link rel="stylesheet" type="text/css" href="%s"></link>' % os.path.abspath(self.resources['css']))
            output.append('<script src="%s"></script>' % os.path.abspath(self.resources['jquery']))
            output.append('<script src="%s"></script>' % os.path.abspath(self.resources['js']))
        else:
            output.append('<style>%s</style>' % read_data(self.resources['css']))
            output.append('<script>%s</script>' % read_data(self.resources['jquery']))
            output.append('<script>%s</script>' % read_data(self.resources['js']))

        # Add plug-in defined classes
        dynamic_css = []
        color_rotation = ['fcc', 'cfc', 'ccf', 'cff', 'fcf', 'ffc']
        next_color = -1
        for r in self.reports:
            if hasattr(r, 'css_classes'):
                for c in r.css_classes:
                    # If what is reported is a full-fledged CSS class
                    if hasattr(c, 'to_css'):
                        dynamic_css.append(c.to_css())
                    else:
                        next_color = (next_color + 1) % len(color_rotation)
                        dynamic_css.append('.{} {{ background-color: #{}; }}'.format(c, color_rotation[next_color]))
        if len(dynamic_css) > 0:
            output.append('<style>%s</style>' % ''.join(dynamic_css))

        # Add experimental math support
        if math:
            output.append('<script type="text/javascript" src="{}"></script>'.format(self.resources['math']))

        # Begin main body
        output.append('</head><body>')
        # Main toolbar
        output.append('<div class="header">Scientific Writing Toolkit <div id="tooltip"></div>')
        output.append('<div class="button" id="expand-button">details</div>')
        output.append('<div class="button" id="clear-highlights">highlights</div>')
        output.append('<div class="label">Toggle: </div>')
        output.append('<div class="separator"></div>')
        output.append('<div class="button blue" id="verb-report">verb report</div>')
        output.append('<div class="button blue" id="frequent-phrases">frequent phrases</div>')
        output.append('<div class="button blue" id="clutter">clutter</div>')
        output.append('<div class="label">Reports: </div>')
        output.append('<div class="separator"></div>')
        output.append('<div class="button green" id="general-guidelines">getting started</div>')
        output.append('<div class="label">Help: </div>')
        output.append('</div>')
        # Document content
        output.append('<div class="textWrapper"><div class="content">')
        # Write meta data
        if (self.meta.has_key('title')): output.append('<div class="title">%s</div>' % self.meta['title'])
        if (self.meta.has_key('author')): output.append('<div class="author">%s</div>' % self.meta['author'])
        # Write main content
        for p in self.content:
            output.append(p.to_html())
        output.append('</div></div>')
        # Write reports
        if len(self.reports) > 0:
            output.append('<div class="globalReports">')
            for r in self.reports:
                output.append('<div class="reportItem" id="{}">'.format(r.label.lower().replace(' ', '-')))
                buttons_specs = []
                if hasattr(r, 'css_classes'):
                    buttons_specs.append('<div class="toggleButton" data-css="{}">{}</div>'.format(' '.join([c.__str__() for c in r.css_classes]),  r.label))
                else:
                    buttons_specs.append('<div class="reportLabel">{}</div>'.format(r.label))
                if hasattr(r, 'help'): buttons_specs.append('<div class="button" id="helpButton">help</div>')
                if r.details != None: buttons_specs.append('<div class="button" id="detailsButton">details</div>')
                if hasattr(r, 'summary'): buttons_specs.append('<div class="reportSummary">{}</div>'.format(r.summary))
                buttons_specs.append('<div style="clear: both;"></div>')
                output.append('<div class="reportTitle">{}</div>'.format(''.join(buttons_specs)))
                if hasattr(r, 'help'): output.append('<div class="reportHelp">{}</div>'.format(r.help))
                if r.details != None: output.append('<div class="reportDetails">{}</div>'.format(r.details_html()))
                output.append('</div>')
            output.append('<div class="about">report generated with <a href="http://github.com/pkorus/swtk"><em>scientific writing toolkit</em></a>  &copy; 2015 Paweł Korus</div>')
            output.append('</div>')
        # Close tags
        output.append('</body></html>')
        return ''.join(output)


class LatexPaper(Paper):

    reject_commands = ['begin', 'maketitle', 'end', 'bibliography', 'def', 'title', 'name', 'address', r'\[', 'appendices', 'appendix', 'newtheorem']
    accepted_commands = ['noindent', 'emph', 'textbf', 'textit', 'paragraph', 'cite', 'ref', 'eqref']
    syntax_replacements = {r'\\%': r'%', r'\\$': r'$',      # Replace basic escape symbols
                           r'\\cite\{[^\}]+\}': '[1]',        # Render citations, references, and formulas into dummies
                           r'\\ref\{[^\}]+\}': '2',
                           r'\\eqref\{[^\}]+\}': '(3)',
                           r'\\emph\{([^\}]+)\}': r'\1',      # Render text styles
                           r'\\textbf\{([^\}]+)\}': r'\1',
                           r'\\textit\{([^\}]+)\}': r'\1',
                           r'\\mbox\{([^\}]+)\}': r'\1',
                           r'\\paragraph\{([^\}]+)\}': r'\1',
                           r'\\proof': '',                    # Remove unnecessary commands
                           r'\\qed': '',
                           r'\\noindent ': '',
                           r'\\begin\{equation\}': ' $',      # Convert overlooked equation environments to their inline equivalents
                           r'\\end\{equation\}': '$. '
                          }

    def __init__(self, lines, resources):
        if not math: self.syntax_replacements[r'\$[^\$]+\$'] = '[Eq]'
        Paper.__init__(self, lines, resources)

    def parse(self, lines):
        paragraph = []
        env_end_marker = None

        # Process file
        for line in lines:

            process_block = 0

            # Remove trailing white spaces
            line = line.strip()

            # Discard full-line comments
            if line.startswith('%'): continue

            # Discard comments
            index = line.find('%')
            if index >= 1 and line[index-1] != '\\': line = line[0:index]

            if len(line) > 0:

                # If a begin commands appears in the current paragraph, force a paragraph break (e.g., when equation
                # environment is stuck to the previous paragraph)
                if line.startswith(r'\begin') and env_end_marker is None:
                    environment_name = get_environment_name(line)
                    # Only care about the outermost environment (except for 'document')
                    if environment_name != 'document':
                        env_end_marker = r'\end{{{}}}'.format(environment_name)
                        if len(paragraph) > 0: process_block = 2 # Marks that this line should be included in the next paragraph

                # If an end marker of the outermost environment appears, force a paragraph break
                if env_end_marker is not None and line.startswith(env_end_marker):
                    env_end_marker = None
                    process_block = 1 # Marks that this line should not be included in the next paragraph

                # If the current line does not enforce a beginning of a new paragraph, add it to the current one
                if process_block != 2:
                    paragraph.append(line)

            # Empty lines end the paragraph - except when inside an environment
            if len(line) == 0 and len(paragraph) > 0 and env_end_marker is None:
                process_block = 1

            # If all lines have been collected, process the paragraph
            if process_block > 0:

                # Merge the lines of the current paragraph
                body = ''.join(paragraph).strip()

                # If for some reason, the current paragraph is empty - skip it
                if len(body) > 0:

                    # Parse document title
                    if not self.meta.has_key('title'):
                        if body.startswith(r'\title'):
                            result = parse_tex_command(body)
                            if result:
                                self.meta['title'] = result

                    # Parse authors
                    if not self.meta.has_key('author'):
                        if body.startswith(r'\author{') or body.startswith(r'\name{') :
                            result = parse_tex_command(body)
                            if result:
                                self.meta['author'] = result

                    # TODO Handle the paragraph commands
                    # TODO Handle cor environment (corollary) / theorem
                    # TODO Handle problems with text block creation?
                    # Parse main document content
                    if body.startswith(r'\section'):
                        result = parse_tex_command(body)
                        if result and len(result) > 0:
                            self.content.append(Section(result, 'h1'))
                        else:
                            self.content.append(Section('Appendix', 'h1'))

                    elif body.startswith(r'\subsection'):
                        result = parse_tex_command(body)
                        if result and len(result) > 0:
                            self.content.append(Section(result, 'h2'))

                    elif body.startswith(r'\subsubsection'):
                        result = parse_tex_command(body)
                        if result and len(result) > 0:
                            self.content.append(Section(result, 'h3'))

                    elif body.startswith(r'\abstract'):
                        result = parse_tex_command(body, False)
                        if result and len(result) > 0:
                            self.content.append(Paragraph(result, 'abstract', self.syntax_replacements))
                        else:
                            logging.error("Could not parse: {:.50}".format(body))

                    elif body.startswith(r'\begin{abstract}'):
                        self.content.append(Paragraph(parse_latex_environment(body), 'abstract', self.syntax_replacements))

                    elif body.startswith(r'\begin{equation'):
                        if math and display_math: self.content.append(Equation(body))

                    elif body.startswith(r'\begin{figure') or body.startswith(r'\begin{table'):
                        if display_floats: self.content.append(Float(body, self.syntax_replacements))

                    elif body.startswith(r'\begin{enumerate'):
                        main_body = parse_latex_environment(body)
                        self.content.append(Enumeration(main_body, True, r'\\item ', self.syntax_replacements))

                    elif body.startswith(r'\begin{itemize'):
                        main_body = parse_latex_environment(body)
                        self.content.append(Enumeration(main_body, False, r'\\item ', self.syntax_replacements))

                    elif not body.startswith('\\') or re.match(r'^\\({})'.format('|'.join(self.accepted_commands)), body):
                        self.content.append(Paragraph(body, syntax_replacements=self.syntax_replacements))

                # When finished, clear the current paragraph (add the line that begins an environment if necessary)
                paragraph = [line] if process_block == 2 else []


class MarkdownPaper(Paper):

    syntax_replacements = {r'\\%': r'%', r'\\$': r'$', ' \*{1,2}': ' ', '\*{1,2} ': '', '_ ': '', ' _': '',
                           r'\[([^\]]+)\]\([^\)]+\)': r'\1',  # Links
                           '`[^`]+`': '[code]'}

    def parse(self, lines):
        paragraph = []
        env_end_marker = None

        # Process file
        for line in lines:

            process_block = 0

            # Remove trailing white spaces
            line = line.strip()

            if len(line) > 0:
                paragraph.append(line)

            # Empty lines end the paragraph
            if len(line) == 0 and len(paragraph) > 0:
                process_block = 1

            # If all lines have been collected, process the paragraph
            if process_block > 0:

                # Merge the lines of the current paragraph
                body = ''.join(paragraph).strip()

                # If for some reason, the current paragraph is empty - skip it
                if len(body) > 0:

                    if body.startswith('# '):
                        self.content.append(Section(body[2:], 'h1'))
                    elif body.startswith('## '):
                        self.content.append(Section(body[3:], 'h2'))
                    elif body.startswith('### '):
                        self.content.append(Section(body[4:], 'h3'))
                    elif body.startswith('#### '):
                        self.content.append(Section(body[5:], 'h4'))
                    elif body.startswith('##### '):
                        self.content.append(Section(body[5:], 'h5'))
                    elif all([x.startswith('- ') for x in paragraph if len(x) > 0]):
                        # prepend \n to facilitate easier splitting
                        self.content.append(Enumeration('\n'+'\n'.join(paragraph), split_string='\n- ', syntax_replacements=self.syntax_replacements))
                    elif all([x.startswith('* ') for x in paragraph if len(x) > 0]):
                        # prepend \n to facilitate easier splitting
                        self.content.append(Enumeration('\n'+'\n'.join(paragraph), split_string='\n* ', syntax_replacements=self.syntax_replacements))
                    elif all([re.match(r'^[0-9]+\. ', x) for x in paragraph if len(x) > 0]):
                        self.content.append(Enumeration('\n'.join(paragraph), True, '\n{0,1}[0-9]+\\. ', self.syntax_replacements))
                    elif not body.startswith('```'):
                        self.content.append(Paragraph(body, syntax_replacements=self.syntax_replacements))

                # When finished, clear the current paragraph (add the line that begins an environment if necessary)
                paragraph = []


class PlaintextPaper(Paper):

    def parse(self, lines):
        paragraph = []

        # Process file
        for line in lines:

            process_block = 0

            # Remove trailing white spaces
            line = line.strip()

            if len(line) > 0:
                paragraph.append(line)

            # Empty lines end the paragraph
            if len(line) == 0 and len(paragraph) > 0:
                process_block = 1

            # If all lines have been collected, process the paragraph
            if process_block > 0:

                # Merge the lines of the current paragraph
                body = ''.join(paragraph).strip()

                # If for some reason, the current paragraph is empty - skip it
                if len(body) > 0:

                    if len(paragraph) == 1 and '.' not in body:
                        self.content.append(Section(body, 'h1'))
                    elif all([x.startswith('- ') for x in paragraph if len(x) > 0]):
                        self.content.append(Enumeration(body, split_string='- '))
                    else:
                        self.content.append(Paragraph(body))

                # When finished, clear the current paragraph (add the line that begins an environment if necessary)
                paragraph = []

