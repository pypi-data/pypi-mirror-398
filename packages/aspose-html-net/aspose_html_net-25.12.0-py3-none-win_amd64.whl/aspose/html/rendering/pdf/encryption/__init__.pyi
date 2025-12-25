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

class PdfEncryptionInfo:
    '''Contains details for a pdf encryption.'''
    
    @property
    def user_password(self) -> str:
        ...
    
    @user_password.setter
    def user_password(self, value : str):
        ...
    
    @property
    def owner_password(self) -> str:
        ...
    
    @owner_password.setter
    def owner_password(self, value : str):
        ...
    
    @property
    def permissions(self) -> aspose.html.rendering.pdf.encryption.PdfPermissions:
        '''Gets the permissions.'''
        ...
    
    @permissions.setter
    def permissions(self, value : aspose.html.rendering.pdf.encryption.PdfPermissions):
        '''Sets the permissions.'''
        ...
    
    @property
    def encryption_algorithm(self) -> aspose.html.rendering.pdf.encryption.PdfEncryptionAlgorithm:
        ...
    
    @encryption_algorithm.setter
    def encryption_algorithm(self, value : aspose.html.rendering.pdf.encryption.PdfEncryptionAlgorithm):
        ...
    
    ...

class PdfEncryptionAlgorithm:
    '''Encryption mode enum. Describe using algorithm and key length.
    This enum is extended in order to be able to further increase functionality.
    This enum implements "Base-to-Core" pattern.'''
    
    @classmethod
    @property
    def RC4_40(cls) -> PdfEncryptionAlgorithm:
        '''Algorithm, with an RC4 encryption key length of 40 bits;'''
        ...
    
    @classmethod
    @property
    def RC4_128(cls) -> PdfEncryptionAlgorithm:
        '''Algorithm, with an RC4 encryption key length of 128 bits and advanced permission set;'''
        ...
    
    ...

class PdfPermissions:
    '''This enum represents user's permissions for a pdf.'''
    
    @classmethod
    @property
    def PRINT_DOCUMENT(cls) -> PdfPermissions:
        '''(Security handlers of revision 2) Print the document.
        (Security handlers of revision 3 or greater) Print the document (possibly not at the highest quality level, depending on whether PrintingQuality is also set).'''
        ...
    
    @classmethod
    @property
    def MODIFY_CONTENT(cls) -> PdfPermissions:
        '''Modify the contents of the document by operations other than those controlled by ModifyTextAnnotations, FillForm, and 11.'''
        ...
    
    @classmethod
    @property
    def EXTRACT_CONTENT(cls) -> PdfPermissions:
        '''Security handlers of revision 2) Copy or otherwise extract text and graphics from the document,
        including extracting text and graphics (in support of accessibility to users with disabilities or for other purposes).
        (Security handlers of revision 3 or greater) Copy or otherwise extract text and graphics from the document by operations other than that controlled by
        ExtractContentWithDisabilities.'''
        ...
    
    @classmethod
    @property
    def MODIFY_TEXT_ANNOTATIONS(cls) -> PdfPermissions:
        '''Add or modify text annotations, fill in interactive form fields, and, if ModifyContent is also set, create or modify interactive form fields (including signature fields).'''
        ...
    
    @classmethod
    @property
    def FILL_FORM(cls) -> PdfPermissions:
        '''(Security handlers of revision 3 or greater) Fill in existing interactive form fields (including signature fields), even if ModifyTextAnnotations is clear.'''
        ...
    
    @classmethod
    @property
    def EXTRACT_CONTENT_WITH_DISABILITIES(cls) -> PdfPermissions:
        '''(Security handlers of revision 3 or greater) Extract text and graphics (in support of accessibility to users with disabilities or for other purposes).'''
        ...
    
    @classmethod
    @property
    def ASSEMBLE_DOCUMENT(cls) -> PdfPermissions:
        '''(Security handlers of revision 3 or greater) Assemble the document (insert, rotate, or delete pages and create bookmarks or thumbnail images), even if ModifyContent is clear.'''
        ...
    
    @classmethod
    @property
    def PRINTING_QUALITY(cls) -> PdfPermissions:
        '''(Security handlers of revision 3 or greater) Print the document to a representation from which a faithful digital copy of the PDF content could be generated.
        When this bit is clear (and bit 3 is set), printing is limited to a low-level representation of the appearance, possibly of degraded quality.'''
        ...
    
    ...

