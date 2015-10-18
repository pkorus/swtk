__author__ = 'pkorus'

import os, sys, argparse, re
from swtk import paper
from swtk import processors

# Parse command line arguments
parser = argparse.ArgumentParser(description='Scientific Writing Toolbox')
parser.add_argument('filename', type=str, help='input file (LaTeX, markdown, plaintext)')
parser.add_argument('-o', '--output', type=str, help='Output filename (HTML) / use - for stdout')
parser.add_argument('-s', '--stylesheet', type=str, help='Custom CSS stylesheet')
parser.add_argument('-j', '--javascript', type=str, help='Custom Java Script')
parser.add_argument('-e', '--external', help='Use external resources in HTML output',action='store_true')
parser.add_argument('-v', '--verbose', help='Print analysis summary to stdout',action='store_true')
parser.add_argument('-f', '--floats', help='Include captions from floats (tables & figures)', action='store_true')
parser.add_argument('-m', '--math', help='Enable experimental MathJax support (CDN only)', action='store_true')
parser.add_argument('-M', '--Math', help='Enable MathJax support & include standalone equations', action='store_true')
args = parser.parse_args()

supported_formats = {'.tex' : paper.LatexPaper, '.md': paper.MarkdownPaper, '.txt': paper.PlaintextPaper}

# Verify params
if not os.path.splitext(args.filename)[-1].lower() in supported_formats.keys():
    print 'Error: Unsupported document format (%s)' % os.path.split(args.filename)[-1]
    sys.exit(1)

if not args.output:
    # args.output = args.filename.replace('.tex', '.html')
    args.output = re.sub('({})'.format('|'.join(supported_formats.keys())), '.html', args.filename)

if not args.output.endswith('.html') and not args.output == '-':
    print 'Error: Unsupported output format (%s)' % os.path.split(args.output)[-1]
    sys.exit(1)

# Read lines from the input file
with open(args.filename) as f:
    lines = f.readlines()

# Check if the user specified valid resources
if args.stylesheet is not None and not os.path.exists(args.stylesheet):
    print('ERROR File does not exist {}'.format(args.stylesheet))
    sys.exit(1)

if args.javascript is not None and not os.path.exists(args.javascript):
    print('ERROR File does not exist {}'.format(args.javascript))
    sys.exit(1)

# Configure paths for external resources
resources = {}
if args.stylesheet is not None: resources['css'] = args.stylesheet
if args.javascript is not None: resources['js'] = args.javascript

# Enable experimental MathJax support
if args.math: paper.math = True
if args.Math:
    paper.math = True
    paper.display_math = True

# Enable float caption parsing
if args.floats: paper.display_floats = True

# Parse paper
paper_class = supported_formats[os.path.splitext(args.filename)[-1].lower()]
p = paper_class(lines, resources)

# Load and execute text analysis plugins
root_path = os.path.split(__file__)[0]
processors.Plugin.register_plugins('{}/plugins'.format(root_path if len(root_path) > 0 else '.'))
processors.Plugin.run_all(p)

# Print summary
if args.verbose:
    print 'Input filename: %s' % args.filename
    print 'Output filename: %s' % args.output
    print 'Resources: %s' % p.resources
    print 'Opened LaTeX document with %d lines' % len(lines)
    print p.to_summary()

# Save as HTML
if args.output == '-':
    print p.to_html(args.external)
else:
    with open(args.output, 'w') as f:
        f.write(p.to_html(args.external))