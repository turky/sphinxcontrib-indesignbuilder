# -*- coding: utf-8 -*-
import logging
import os
from xml.sax.saxutils import XMLGenerator

from docutils import nodes
from docutils.nodes import NodeVisitor
from docutils.writers import Writer
from six import StringIO
from sphinx.ext.imgmath import MathExtError, get_tooltip, render_math
from sphinx.locale import __, _
from sphinx.util.math import get_node_equation_number, wrap_displaymath

logger = logging.getLogger(__name__)

class IndesignWriter(Writer):
    def __init__(self, builder, single=False):
        Writer.__init__(self)
        self.single = single
        self.builder = builder

    def translate(self):
        if self.single:
            self.visitor = visitor = SingleIndesignVisitor(self.document)
        else:
            self.visitor = visitor = IndesignVisitor(self.document)
        self.document.walkabout(visitor)
        self.output = visitor.astext()


class IndesignVisitor(NodeVisitor):
    def __init__(self, document):
        NodeVisitor.__init__(self, document)

        self._output = StringIO()
        self.generator = XMLGenerator(self._output, "utf-8")
        self.generator.outf = self._output

        self.listenv = None
        self.listlevel = 0
        self.tableenv = False
        self.within_index = False
        self.restrect_newline = True

    def newline(self):
        if self.restrect_newline is not True:
            self.generator.outf.write("\n")

    def astext(self):
        return self._output.getvalue()

    def visit_document(self, node):
        self.generator.startDocument()

        self.generator.outf.write(
            '<doc xmlns:aid="http://ns.adobe.com/AdobeInDesign/4.0/" xmlns:aid5="http://ns.adobe.com/AdobeInDesign/5.0/">')
        self.sec_level = 0

    def depart_document(self, node):
        self.generator.endDocument()
        self.generator.outf.write("</doc>")

    def visit_paragraph(self, node):
        # not print <p> in list item
        if (self.listenv is None) and (self.tableenv is not True):
            self.generator.startElement('p', {})

    def depart_paragraph(self, node):
        if (self.listenv is None) and (self.tableenv is not True):
            self.generator.endElement('p')
            self.newline()

    def visit_section(self, node):
        assert not self.within_index
        self.sec_level += 1

    def depart_section(self, node):
        self.sec_level -= 1
        self.newline()

    def visit_title(self, node):
        if self.tableenv is not True:
            level = "h" + str(self.sec_level)
            self.generator.startElement('title',
                                        {"aid:pstyle": level})
        else:
            self.generator.startElement('caption', {})

    def depart_title(self, node):
        if self.tableenv is not True:
            self.generator.endElement('title')
            dtp = u'<?dtp level="{0}" section="{1}"?>'.format(
                self.sec_level,
                node.astext(),
            )
            self.generator.outf.write(dtp)
        else:
            self.generator.endElement('caption')

        self.newline()

    def visit_Text(self, node):
        self.generator.characters(node.astext())

    def depart_Text(self, node):
        pass

    def visit_index(self, node):
        # self.generator.startElement('index', {})
        self.within_index = True
        pass

    def depart_index(self, node):
        # self.generator.endElement('index')
        self.within_index = False
        pass

    def visit_target(self, node):
        # self.generator.startElement('section', {})
        pass

    def depart_target(self, node):
        pass

    def visit_emphasis(self, node):
        self.generator.startElement("i", {})

    def depart_emphasis(self, node):
        self.generator.endElement("i")

    def visit_math(self, node):
        self.generator.startElement("m", {})

    def depart_math(self, node):
        self.generator.endElement("m")

    def visit_math_block(self, node):
        self.generator.startElement("equation", {})

    def depart_math_block(self, node):
        self.generator.endElement("equation")

    def visit_doctest_block(self, node):
        self.generator.startElement("programlisting",
                                    {"language": "python"})

    def depart_doctest_block(self, node):
        self.generator.endElement("programlisting")

    def visit_strong(self, node):
        self.generator.startElement("b", {})

    def depart_strong(self, node):
        self.generator.endElement("b")

    def visit_title_reference(self, node):
        pass

    def depart_title_reference(self, node):
        pass

    def visit_displaymath(self, node):
        pass

    def depart_displaymath(self, node):
        pass

    def visit_note(self, node):
        self.generator.startElement('note', {})

    def depart_note(self, node):
        self.generator.endElement('note')

    def visit_tip(self, node):
        self.generator.startElement('tip', {})

    def depart_tip(self, node):
        self.generator.endElement('tip')

    def visit_warning(self, node):
        self.generator.startElement('warning', {})

    def depart_warning(self, node):
        self.generator.endElement('warning')

    def visit_caution(self, node):
        self.generator.startElement('caution', {})

    def depart_caution(self, node):
        self.generator.endElement('caution')

    def visit_unknown_visit(self, node):
        pass

    def depart_unknown_visit(self, node):
        pass

    def visit_number_reference(self, node):
        pass

    def depart_number_reference(self, node):
        pass

    def visit_literal_block(self, node):
        if "highlight_args" in node.attributes.keys():
            self.generator.startElement(
                "listinfo",
                {"language": node.attributes["language"]})
            self._lit_block_tag = "listinfo"
        else:
            self.generator.startElement("list", {'type': 'emlist'})
            self._lit_block_tag = "list"
        self.newline()

    def depart_literal_block(self, node):
        self.newline()
        self.generator.endElement(self._lit_block_tag)
        del self._lit_block_tag
        self.newline()

    def visit_literal(self, node):
        self.generator.startElement('tt', {'type': 'inline-code'})

    def depart_literal(self, node):
        self.generator.endElement('tt')

    def visit_comment(self, node):
        raise nodes.SkipNode

    def depart_comment(self, node):
        pass

    def visit_compound(self, node):
        pass

    def depart_compound(self, node):
        pass

    def visit_compact_paragraph(self, node):
        pass

    def depart_compact_paragraph(self, node):
        pass

    def visit_figure(self, node):
        pass

    def depart_figure(self, node):
        pass

    def visit_image(self, node):
        caption = None
        legend = None
        try:
            for c in node.parent.children:
                if isinstance(c, nodes.caption):
                    caption = c.astext()
            
            for c in node.parent.children:
                if isinstance(c, nodes.legend):
                    legend = c.astext()
        except AttributeError:
            logger.debug("node doesn't have parent")
        filename = os.path.basename(os.path.splitext(node['uri'])[0])
        if node.get('inline'):
            self.generator.startElement('a', {"linkurl": filename})
            self.generatorendElement('a')
        else:
            self.generator.startElement('img', {})
            self.generator.startElement('Image', {'href': filename})
            self.generator.endElement('Image')
            if caption:
                self.generator.startElement('caption', {})
                self.generator.outf.write(caption)
                self.generator.endElement('caption')
            if legend:
               self.add_lines([legend])
            self.generator.endElement('img')
        raise nodes.SkipNode

    def depart_image(self, node):
        pass

    def depart_reference(self, node):
        self.generator.endElement("ref")

    def visit_caption(self, node):
        if node.parent.tagname == 'figure':
            raise nodes.SkipNode
        elif node.parent.attributes['literal_block']:
            tagname = 'caption'
            self.generator.startElement(tagname, {})
        else:
            pass

    def depart_caption(self, node):
        if node.parent.attributes['literal_block']:
            tagname = 'caption'
            self.generator.endElement(tagname)
        pass

    def visit_bullet_list(self, node):
        self.listenv = 'ul'
        self.listlevel = self.listlevel + 1
        if self.listlevel > 1:
            tagname = self.listenv + str(self.listlevel)
            self.newline()
            self.generator.startElement(tagname, {})
        else:
            tagname = self.listenv
            self.generator.startElement(tagname, {})
        self.newline()

    def depart_bullet_list(self, node):
        if self.listlevel > 1:
            tagname = self.listenv + str(self.listlevel)
        else:
            tagname = self.listenv
        self.generator.endElement(tagname)
        self.listlevel = self.listlevel - 1
        if self.listlevel == 0:
            self.listenv = None
        self.newline()

    def visit_enumerated_list(self, node):
        self.listenv = "ol"
        self.listlevel = self.listlevel + 1
        if self.listlevel > 1:
            tagname = self.listenv + str(self.listlevel)
        else:
            tagname = self.listenv
        self.generator.startElement(tagname, {})
        self.newline()

    def depart_enumerated_list(self, node):
        if self.listlevel > 1:
            tagname = self.listenv + str(self.listlevel)
        else:
            tagname = self.listenv
        self.generator.endElement(tagname)
        self.listlevel = self.listlevel - 1
        if self.listlevel == 0:
            self.listenv = None
        self.newline()

    def visit_reference(self, node):
        atts = {'class': 'reference'}
        if node.get('internal') or 'refuri' not in node:
            atts['class'] += ' internal'
        else:
            atts['class'] += ' external'
        if 'refuri' in node:
            atts['href'] = node['refuri']
        else:
            assert 'refid' in node, \
                   'References must have "refuri" or "refid" attribute.'
            atts['href'] = '#' + node['refid']
        if not isinstance(node.parent, nodes.TextElement):
            assert len(node) == 1 and isinstance(node[0], nodes.image)
            atts['class'] += ' image-reference'
        if 'reftitle' in node:
            atts['title'] = node['reftitle']
        self.generator.startElement("ref", atts)

        #self.generator.endElement("ref")

#        if node.get('secnumber'):
#            self.body.append(('%s' + self.secnumber_suffix) %
#                             '.'.join(map(str, node['secnumber'])))

    def visit_footnote(self, node):
        self.generator.startElement("footnote", {'id':node['ids'][0]})

    def depart_footnote(self, node):
        self.generator.endElement("footnote")

    def visit_list_item(self, node):
        style = "%s-item" % (self.listenv)
        self.generator.startElement("li", {"aid:pstyle": style})

    def depart_list_item(self, node):
        self.generator.endElement("li")
        self.newline()

    def visit_field_list(self, node):
        self.generator.startElement("variablelist", {})

    def depart_field_list(self, node):
        self.generator.endElement("variablelist")

    def visit_field(self, node):
        self.generator.startElement("varlistentry", {})

    def depart_field(self, node):
        self.generator.endElement("varlistentry")

    def visit_field_name(self, node):
        self.generator.startElement("term", {})

    def depart_field_name(self, node):
        self.generator.endElement("term")

    def visit_field_body(self, node):
        self.generator.startElement("listitem", {})

    def depart_field_body(self, node):
        self.generator.endElement("listitem")

    def visit_definition_list(self, node):
        self.listenv = "dl"
        self.generator.startElement("dl", {})

    def depart_definition_list(self, node):
        self.generator.endElement("dl")
        self.listenv = None
        self.newline()

    def visit_definition_list_item(self, node):
        pass
#        self.generator.startElement("dt", {})

    def depart_definition_list_item(self, node):
        pass
#        self.generator.endElement("dt")

    def visit_term(self, node):
        self.generator.startElement("dt", {})

    def depart_term(self, node):
        self.generator.endElement("dt")

    def visit_definition(self, node):
        self.generator.startElement("dd", {})

    def depart_definition(self, node):
        self.generator.endElement("dd")

    def visit_block_quote(self, node):
        self.generator.startElement("quote", {})

    def depart_block_quote(self, node):
        self.generator.endElement("quote")
        self.newline()

    def visit_inline(self, node):
        if 'xref' in node['classes'] or 'term' in node['classes']:
            self.generator.outf.write('*')

    def depart_inline(self, node):
        if 'xref' in node['classes'] or 'term' in node['classes']:
            self.generator.outf.write('*')

    def visit_todo_node(self, node):
        pass

    def depart_todo_node(self, node):
        pass

    def visit_container(self, node):
        pass

    def depart_container(self, node):
        pass

    def visit_citation(self, node):
        self.generator.startElement('a', {})
        self.generator.outf.write(node.rawsource)
        #print(node.__dict__)

    def depart_citation(self, node):
        self.generator.endElement('a')

    def visit_label(self, node):
        self.generator.startElement('label', {})

    def depart_label(self, node):
        self.generator.endElement('label')

    def visit_footnote_reference(self, node):
        self.generator.startElement('footnote', {'href': node['refid']})

    def depart_footnote_reference(self, node):
        self.generator.endElement('footnote')

    def visit_substitution_definition(self, node):
        pass

    def depart_substitution_definition(self, node):
        pass

    def visit_table(self, node):
        self.tableenv = True
        self.generator.startElement('table', {})

    def depart_table(self, node):
        self.generator.endElement('table')
        self.tableenv = False

    def visit_tgroup(self, node):
        self.generator.startElement('tgroup', {})

    def depart_tgroup(self, node):
        self.generator.endElement('tgroup')

    def visit_colspec(self, node):
        pass
        # self.generator.startElement('colspec', {})

    def depart_colspec(self, node):
        pass
        # self.generator.endElement('colspec')

    def visit_thead(self, node):
        self.generator.startElement('thead', {'aid:pstyle': 'header'})

    def depart_thead(self, node):
        self.generator.endElement('thead')

    def visit_row(self, node):
        if node.parent.tagname == 'thead':
            cur_attr = {'type': 'header'}
        else:
            cur_attr = {}
        self.generator.startElement('tr', cur_attr)

    def depart_row(self, node):
        self.generator.endElement('tr')

    def visit_entry(self, node):
        #self.generator.startElement('entry', {})
        pass

    def depart_entry(self, node):
        #self.generator.endElement('entry')
        self.generator.outf.write('\t')

    def visit_tbody(self, node):
        self.generator.startElement('tbody', {})

    def depart_tbody(self, node):
        self.generator.endElement('tbody')

    def visit_problematic(self, node):
        pass

    def depart_problematic(self, node):
        pass

    def visit_superscript(self, node):
        self.generator.startElement('sup', {})

    def depart_superscript(self, node):
        self.generator.endElement('sup')

    def visit_subscript(self, node):
        self.generator.startElement('sub', {})

    def depart_subscript(self, node):
        self.generator.endElement('sub')

    def visit_column(self, node):
        self.generator.startElement('column', {})
        self.generator.outf.write('<title aid:pstyle="column-title">%s</title>' % node['title'])

    def depart_column(self, node):
        self.generator.endElement('column')

    def visit_raw(self, node):
        self.generator.startElement('raw', {})

    def depart_raw(self, node):
        self.generator.endElement('raw')

    def visit_transition(self, node):
        self.generator.startElement('transition', {})

    def depart_transition(self, node):
        self.generator.endElement('transition')


class SingleIndesignVisitor(IndesignVisitor):
    sec_level = 0

    def visit_start_of_file(self, node):
        pass

    def depart_start_of_file(self, node):
        self.newline()

    def visit_document(self, node):
        self.generator.startDocument()
        # only occurs in the single-file builder
        self.generator.outf.write(
            '<doc xmlns:aid="http://ns.adobe.com/AdobeInDesign/4.0/">')
        self.newline()

    def depart_document(self, node):
        self.generator.endDocument()
        self.generator.outf.write("</doc>")
