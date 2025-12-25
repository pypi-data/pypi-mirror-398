from typing import List, Optional, Dict, Iterable
import aspose.pycore
import aspose.pydrawing
import aspose.html
import aspose.html.accessibility
import aspose.html.accessibility.results
import aspose.html.accessibility.saving
import aspose.html.collections
import aspose.html.converters
import aspose.html.diagnostics
import aspose.html.dom
import aspose.html.dom.attributes
import aspose.html.dom.canvas
import aspose.html.dom.css
import aspose.html.dom.events
import aspose.html.dom.mutations
import aspose.html.dom.svg
import aspose.html.dom.svg.datatypes
import aspose.html.dom.svg.events
import aspose.html.dom.svg.filters
import aspose.html.dom.svg.paths
import aspose.html.dom.svg.saving
import aspose.html.dom.traversal
import aspose.html.dom.traversal.filters
import aspose.html.dom.views
import aspose.html.dom.xpath
import aspose.html.drawing
import aspose.html.forms
import aspose.html.io
import aspose.html.loading
import aspose.html.net
import aspose.html.net.headers
import aspose.html.net.messagefilters
import aspose.html.net.messagehandlers
import aspose.html.rendering
import aspose.html.rendering.doc
import aspose.html.rendering.fonts
import aspose.html.rendering.image
import aspose.html.rendering.pdf
import aspose.html.rendering.pdf.encryption
import aspose.html.rendering.xps
import aspose.html.saving
import aspose.html.saving.resourcehandlers
import aspose.html.services
import aspose.html.toolkit
import aspose.html.toolkit.markdown
import aspose.html.toolkit.markdown.syntax
import aspose.html.toolkit.markdown.syntax.extensions
import aspose.html.toolkit.markdown.syntax.parser
import aspose.html.toolkit.markdown.syntax.parser.extensions
import aspose.html.toolkit.markdown.syntax.parser.extensions.gfm
import aspose.html.toolkit.markdown.syntax.text
import aspose.html.toolkit.optimizers
import aspose.html.window

class FontMatcher:
    '''This class allows you to control some parts of the font matching algorithm.'''
    
    def match_font_fallback(self, font_matching_properties : aspose.html.rendering.fonts.FontMatchingProperties, char_code : int) -> bytes:
        '''This method is called if there is no appropriate font found in the fonts lookup folders.
        It should return true type font based on the ``fontMatchingProperties`` which can render ``charCode``, or ``null`` if such font is not available.
        
        :param font_matching_properties: Properties of the matched font.
        :param char_code: Code of the character which will be rendered using the matched font.
        :returns: A byte array containing the fonts data or ``null``.'''
        ...
    
    ...

class FontMatchingProperties:
    '''This class contains properties which describe the font being matched.'''
    
    @property
    def font_families(self) -> Iterable[str]:
        ...
    
    @property
    def font_style(self) -> str:
        ...
    
    @property
    def font_weight(self) -> int:
        ...
    
    @property
    def font_stretch(self) -> float:
        ...
    
    ...

