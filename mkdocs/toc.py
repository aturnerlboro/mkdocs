# coding: utf-8

"""
Deals with generating the per-page table of contents.

For the sake of simplicity we use an existing markdown extension to generate
an HTML table of contents, and then parse that into the underlying data.

The steps we take to generate a table of contents are:

* Pre-process the markdown, injecting a [TOC] marker.
* Generate HTML from markdown.
* Post-process the HTML, spliting the content and the table of contents.
* Parse table of contents HTML into the underlying data structure.
"""

from __future__ import unicode_literals

try:                                    # pragma: no cover
    from html.parser import HTMLParser  # noqa
except ImportError:                     # pragma: no cover
    from HTMLParser import HTMLParser   # noqa


class TableOfContents(object):
    """
    Represents the table of contents for a given page.
    """
    def __init__(self, html):
        self.items = _parse_html_table_of_contents(html)

    def __iter__(self):
        return iter(self.items)

    def __str__(self):
        return ''.join([str(item) for item in self])


class AnchorLink(object):
    """
    A single entry in the table of contents.
    """
    def __init__(self, title, url):
        self.title, self.url = title, url
        self.children = []

    def __str__(self):
        return self.indent_print()

    def indent_print(self, depth=0):
        indent = '    ' * depth
        ret = '%s%s - %s\n' % (indent, self.title, self.url)
        for item in self.children:
            ret += item.indent_print(depth + 1)
        return ret


class TOCParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.links = []

        self.in_anchor = False
        self.attrs = None
        self.title = ''

        # Prior to Python3.4 no convert_charrefs keyword existed.
        # However, in Python3.5 the default was changed to True.
        # We need the False behavior in all versions but can only
        # set it if it exists.
        if hasattr(self, 'convert_charrefs'):
            self.convert_charrefs = False

    def handle_starttag(self, tag, attrs):

        if not self.in_anchor:
            if tag == 'a':
                self.in_anchor = True
                self.attrs = dict(attrs)

    def handle_endtag(self, tag):
        if tag == 'a':
            self.in_anchor = False

    def handle_data(self, data):

        if self.in_anchor:
            self.title += data

    def handle_charref(self, ref):
        self.handle_entityref("#" + ref)

    def handle_entityref(self, ref):
        self.handle_data("&%s;" % ref)


def _parse_html_table_of_contents(html):
    """
    Given a table of contents string that has been automatically generated by
    the markdown library, parse it into a tree of AnchorLink instances.

    Returns a list of all the parent AnchorLink instances.
    """
    lines = html.splitlines()[2:-2]
    parents = []
    ret = []
    for line in lines:
        parser = TOCParser()
        parser.feed(line)
        if parser.title:
            try:
                href = parser.attrs['href']
            except KeyError:
                continue
            title = parser.title
            nav = AnchorLink(title, href)
            # Add the item to its parent if required.  If it is a topmost
            # item then instead append it to our return value.
            if parents:
                parents[-1].children.append(nav)
            else:
                ret.append(nav)
            # If this item has children, store it as the current parent
            if line.endswith('<ul>'):
                parents.append(nav)
        elif line.startswith('</ul>'):
            if parents:
                parents.pop()

    # For the table of contents, always mark the first element as active
    if ret:
        ret[0].active = True

    return ret
