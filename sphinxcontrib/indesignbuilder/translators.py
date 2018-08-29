# -*- coding: utf-8 -*-
"""
    sphinxcontrib-indesignbuilder
"""

from docutils import nodes
from sphinx.transforms import SphinxTransform
from sphinx.util import logging

logger = logging.getLogger(__name__)

class IdgxmlFootnoteTransform(SphinxTransform):
    default_priority = 100

    def apply(self):
         # type: () -> None
        # TBD: footnote and footnote_ref can't work expected.
        #      autofootnote is going well.
        for fn_ref in self.document.footnote_refs:
            for fn in self.document.footnotes:
                if fn_ref == fn['names'][0]:
                    fn.remove(fn.children[0])
                    self.document.footnote_refs[fn_ref][0] = fn.deepcopy()
                    break
        for autfn_ref in self.document.autofootnote_refs:
            cur_id = autfn_ref['refid']
            for autfn in self.document.autofootnotes:
                if cur_id == autfn['ids'][0]:
                    autfn.remove(autfn.children[0])
                    autfn_ref.replace_self(autfn.deepcopy())
                    autfn.parent.remove(autfn)
                    break
