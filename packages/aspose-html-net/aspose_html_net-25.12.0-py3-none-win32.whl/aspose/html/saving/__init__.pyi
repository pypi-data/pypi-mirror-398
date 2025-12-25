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

class DocSaveOptions(aspose.html.rendering.doc.DocRenderingOptions):
    '''Specific options data class.'''
    
    @property
    def css(self) -> aspose.html.rendering.CssOptions:
        '''Gets a :py:class:`aspose.html.rendering.CssOptions` object which is used for configuration of css properties processing.'''
        ...
    
    @property
    def page_setup(self) -> aspose.html.rendering.PageSetup:
        ...
    
    @property
    def horizontal_resolution(self) -> aspose.html.drawing.Resolution:
        ...
    
    @horizontal_resolution.setter
    def horizontal_resolution(self, value : aspose.html.drawing.Resolution):
        ...
    
    @property
    def background_color(self) -> aspose.pydrawing.Color:
        ...
    
    @background_color.setter
    def background_color(self, value : aspose.pydrawing.Color):
        ...
    
    @property
    def vertical_resolution(self) -> aspose.html.drawing.Resolution:
        ...
    
    @vertical_resolution.setter
    def vertical_resolution(self, value : aspose.html.drawing.Resolution):
        ...
    
    @property
    def font_embedding_rule(self) -> aspose.html.rendering.doc.FontEmbeddingRule:
        ...
    
    @font_embedding_rule.setter
    def font_embedding_rule(self, value : aspose.html.rendering.doc.FontEmbeddingRule):
        ...
    
    @property
    def document_format(self) -> aspose.html.rendering.doc.DocumentFormat:
        ...
    
    @document_format.setter
    def document_format(self, value : aspose.html.rendering.doc.DocumentFormat):
        ...
    
    ...

class HTMLSaveOptions(SaveOptions):
    '''Represents HTML save options.'''
    
    @property
    def resource_handling_options(self) -> aspose.html.saving.ResourceHandlingOptions:
        ...
    
    @property
    def serialize_input_value(self) -> bool:
        ...
    
    @serialize_input_value.setter
    def serialize_input_value(self, value : bool):
        ...
    
    @property
    def document_type(self) -> byte:
        ...
    
    @document_type.setter
    def document_type(self, value : byte):
        ...
    
    @classmethod
    @property
    def AUTO(cls) -> byte:
        '''The output document type will be selected automatically.'''
        ...
    
    @classmethod
    @property
    def HTML(cls) -> byte:
        '''The document will be saved as HTML.'''
        ...
    
    @classmethod
    @property
    def XHTML(cls) -> byte:
        '''The document will be saved as XHTML.'''
        ...
    
    ...

class ImageSaveOptions(aspose.html.rendering.image.ImageRenderingOptions):
    '''Specific options data class.'''
    
    @property
    def css(self) -> aspose.html.rendering.CssOptions:
        '''Gets a :py:class:`aspose.html.rendering.CssOptions` object which is used for configuration of css properties processing.'''
        ...
    
    @property
    def page_setup(self) -> aspose.html.rendering.PageSetup:
        ...
    
    @property
    def horizontal_resolution(self) -> aspose.html.drawing.Resolution:
        ...
    
    @horizontal_resolution.setter
    def horizontal_resolution(self, value : aspose.html.drawing.Resolution):
        ...
    
    @property
    def background_color(self) -> aspose.pydrawing.Color:
        ...
    
    @background_color.setter
    def background_color(self, value : aspose.pydrawing.Color):
        ...
    
    @property
    def vertical_resolution(self) -> aspose.html.drawing.Resolution:
        ...
    
    @vertical_resolution.setter
    def vertical_resolution(self, value : aspose.html.drawing.Resolution):
        ...
    
    @property
    def format(self) -> aspose.html.rendering.image.ImageFormat:
        '''Sets or gets :py:class:`aspose.html.rendering.image.ImageFormat`. By default this property is :py:attr:`aspose.html.rendering.image.ImageFormat.PNG`.'''
        ...
    
    @format.setter
    def format(self, value : aspose.html.rendering.image.ImageFormat):
        '''Sets or gets :py:class:`aspose.html.rendering.image.ImageFormat`. By default this property is :py:attr:`aspose.html.rendering.image.ImageFormat.PNG`.'''
        ...
    
    @property
    def compression(self) -> aspose.html.rendering.image.Compression:
        '''Sets or gets Tagged Image File Format (TIFF) :py:class:`aspose.html.rendering.image.Compression`. By default this property is :py:attr:`aspose.html.rendering.image.Compression.LZW`.'''
        ...
    
    @compression.setter
    def compression(self, value : aspose.html.rendering.image.Compression):
        '''Sets or gets Tagged Image File Format (TIFF) :py:class:`aspose.html.rendering.image.Compression`. By default this property is :py:attr:`aspose.html.rendering.image.Compression.LZW`.'''
        ...
    
    @property
    def text(self) -> aspose.html.rendering.image.TextOptions:
        '''Gets a :py:class:`aspose.html.rendering.image.TextOptions` object which is used for configuration of text rendering.'''
        ...
    
    @property
    def use_antialiasing(self) -> bool:
        ...
    
    @use_antialiasing.setter
    def use_antialiasing(self, value : bool):
        ...
    
    ...

class MHTMLSaveOptions(SaveOptions):
    '''Represents MHTML save options.'''
    
    @property
    def resource_handling_options(self) -> aspose.html.saving.ResourceHandlingOptions:
        ...
    
    ...

class MarkdownSaveOptions(SaveOptions):
    '''Represents Markdown save options.'''
    
    @property
    def resource_handling_options(self) -> aspose.html.saving.ResourceHandlingOptions:
        ...
    
    @property
    def features(self) -> aspose.html.saving.MarkdownFeatures:
        '''Flag set that controls which elements are converted to markdown.'''
        ...
    
    @features.setter
    def features(self, value : aspose.html.saving.MarkdownFeatures):
        '''Flag set that controls which elements are converted to markdown.'''
        ...
    
    @property
    def formatter(self) -> aspose.html.saving.MarkdownFormatter:
        '''Gets the markdown formatting style.'''
        ...
    
    @formatter.setter
    def formatter(self, value : aspose.html.saving.MarkdownFormatter):
        '''Sets the markdown formatting style.'''
        ...
    
    @classmethod
    @property
    def default(cls) -> aspose.html.saving.MarkdownSaveOptions:
        '''Returns set of options which are compatible with default Markdown documentation.'''
        ...
    
    @classmethod
    @property
    def git(cls) -> aspose.html.saving.MarkdownSaveOptions:
        '''Returns set of options which are compatible with GitLab Flavored Markdown.'''
        ...
    
    ...

class PdfSaveOptions(aspose.html.rendering.pdf.PdfRenderingOptions):
    '''Specific options data class.'''
    
    @property
    def css(self) -> aspose.html.rendering.CssOptions:
        '''Gets a :py:class:`aspose.html.rendering.CssOptions` object which is used for configuration of css properties processing.'''
        ...
    
    @property
    def page_setup(self) -> aspose.html.rendering.PageSetup:
        ...
    
    @property
    def horizontal_resolution(self) -> aspose.html.drawing.Resolution:
        ...
    
    @horizontal_resolution.setter
    def horizontal_resolution(self, value : aspose.html.drawing.Resolution):
        ...
    
    @property
    def background_color(self) -> aspose.pydrawing.Color:
        ...
    
    @background_color.setter
    def background_color(self, value : aspose.pydrawing.Color):
        ...
    
    @property
    def vertical_resolution(self) -> aspose.html.drawing.Resolution:
        ...
    
    @vertical_resolution.setter
    def vertical_resolution(self, value : aspose.html.drawing.Resolution):
        ...
    
    @property
    def document_info(self) -> aspose.html.rendering.pdf.PdfDocumentInfo:
        ...
    
    @property
    def form_field_behaviour(self) -> aspose.html.rendering.pdf.FormFieldBehaviour:
        ...
    
    @form_field_behaviour.setter
    def form_field_behaviour(self, value : aspose.html.rendering.pdf.FormFieldBehaviour):
        ...
    
    @property
    def jpeg_quality(self) -> int:
        ...
    
    @jpeg_quality.setter
    def jpeg_quality(self, value : int):
        ...
    
    @property
    def encryption(self) -> aspose.html.rendering.pdf.encryption.PdfEncryptionInfo:
        '''Gets a encryption details. If not set, then no encryption will be performed.'''
        ...
    
    @encryption.setter
    def encryption(self, value : aspose.html.rendering.pdf.encryption.PdfEncryptionInfo):
        '''Sets a encryption details. If not set, then no encryption will be performed.'''
        ...
    
    @property
    def is_tagged_pdf(self) -> bool:
        ...
    
    @is_tagged_pdf.setter
    def is_tagged_pdf(self, value : bool):
        ...
    
    ...

class Resource:
    '''This class describes a resource and provides methods for processing it.'''
    
    def save(self, stream : io.RawIOBase, context : aspose.html.saving.ResourceHandlingContext) -> aspose.html.saving.Resource:
        '''Saves the resource to the provided stream.
        
        :param stream: The stream in which the resource will be saved.
        :param context: Resource handling context.
        :returns: This resource so that you can chain calls.'''
        ...
    
    def embed(self, context : aspose.html.saving.ResourceHandlingContext) -> aspose.html.saving.Resource:
        '''Embeds this resource within its parent by encoding it as Base64. The encoding result will be written to :py:attr:`aspose.html.saving.Resource.output_url`.
        
        :param context: Resource handling context.
        :returns: This resource so that you can chain calls.'''
        ...
    
    def with_output_url(self, output_url : aspose.html.Url) -> aspose.html.saving.Resource:
        '''Specifies the new URL indicating where the resource will be located after processing.
        
        :param output_url: The new URL indicating where the resource will be located after processing.
        :returns: This resource so that you can chain calls.'''
        ...
    
    @property
    def status(self) -> aspose.html.saving.ResourceStatus:
        '''Returns the current status of the resource.'''
        ...
    
    @property
    def mime_type(self) -> aspose.html.MimeType:
        ...
    
    @property
    def original_url(self) -> aspose.html.Url:
        ...
    
    @property
    def original_reference(self) -> str:
        ...
    
    @property
    def output_url(self) -> aspose.html.Url:
        ...
    
    @output_url.setter
    def output_url(self, value : aspose.html.Url):
        ...
    
    ...

class ResourceHandlingContext:
    '''This class contains information used when processing resources.'''
    
    @property
    def parent_resource(self) -> aspose.html.saving.Resource:
        ...
    
    ...

class ResourceHandlingOptions:
    '''Represents resource handling options.'''
    
    @property
    def java_script(self) -> aspose.html.saving.ResourceHandling:
        ...
    
    @java_script.setter
    def java_script(self, value : aspose.html.saving.ResourceHandling):
        ...
    
    @property
    def default(self) -> aspose.html.saving.ResourceHandling:
        '''Gets enum which represents default way of resources handling. Currently :py:attr:`aspose.html.saving.ResourceHandling.SAVE`, :py:attr:`aspose.html.saving.ResourceHandling.IGNORE` and :py:attr:`aspose.html.saving.ResourceHandling.EMBED` values are supported. Default value is :py:attr:`aspose.html.saving.ResourceHandling.SAVE`.'''
        ...
    
    @default.setter
    def default(self, value : aspose.html.saving.ResourceHandling):
        '''Sets enum which represents default way of resources handling. Currently :py:attr:`aspose.html.saving.ResourceHandling.SAVE`, :py:attr:`aspose.html.saving.ResourceHandling.IGNORE` and :py:attr:`aspose.html.saving.ResourceHandling.EMBED` values are supported. Default value is :py:attr:`aspose.html.saving.ResourceHandling.SAVE`.'''
        ...
    
    @property
    def resource_url_restriction(self) -> aspose.html.saving.UrlRestriction:
        ...
    
    @resource_url_restriction.setter
    def resource_url_restriction(self, value : aspose.html.saving.UrlRestriction):
        ...
    
    @property
    def page_url_restriction(self) -> aspose.html.saving.UrlRestriction:
        ...
    
    @page_url_restriction.setter
    def page_url_restriction(self, value : aspose.html.saving.UrlRestriction):
        ...
    
    @property
    def max_handling_depth(self) -> int:
        ...
    
    @max_handling_depth.setter
    def max_handling_depth(self, value : int):
        ...
    
    ...

class SaveOptions:
    '''This is an abstract base class for classes that allow the user to specify additional options when saving a document into a particular format.'''
    
    @property
    def resource_handling_options(self) -> aspose.html.saving.ResourceHandlingOptions:
        ...
    
    ...

class TextSaveOptions:
    '''Represents Text save options'''
    
    @property
    def enable_list_item_markers(self) -> bool:
        ...
    
    @enable_list_item_markers.setter
    def enable_list_item_markers(self, value : bool):
        ...
    
    ...

class XpsSaveOptions(aspose.html.rendering.xps.XpsRenderingOptions):
    '''Specific options data class.'''
    
    @property
    def css(self) -> aspose.html.rendering.CssOptions:
        '''Gets a :py:class:`aspose.html.rendering.CssOptions` object which is used for configuration of css properties processing.'''
        ...
    
    @property
    def page_setup(self) -> aspose.html.rendering.PageSetup:
        ...
    
    @property
    def horizontal_resolution(self) -> aspose.html.drawing.Resolution:
        ...
    
    @horizontal_resolution.setter
    def horizontal_resolution(self, value : aspose.html.drawing.Resolution):
        ...
    
    @property
    def background_color(self) -> aspose.pydrawing.Color:
        ...
    
    @background_color.setter
    def background_color(self, value : aspose.pydrawing.Color):
        ...
    
    @property
    def vertical_resolution(self) -> aspose.html.drawing.Resolution:
        ...
    
    @vertical_resolution.setter
    def vertical_resolution(self, value : aspose.html.drawing.Resolution):
        ...
    
    ...

class HTMLSaveFormat:
    '''Specifies format in which document is saved.'''
    
    @classmethod
    @property
    def ORIGINAL(cls) -> HTMLSaveFormat:
        '''The document will be saved in its original format.'''
        ...
    
    @classmethod
    @property
    def MARKDOWN(cls) -> HTMLSaveFormat:
        '''Document will be saved as Markdown.'''
        ...
    
    @classmethod
    @property
    def MHTML(cls) -> HTMLSaveFormat:
        '''Document will be saved as MHTML.'''
        ...
    
    ...

class MarkdownFeatures:
    '''A :py:class:`aspose.html.saving.MarkdownFeatures` flag set is a set of zero or more of the following flags, which are used to select elements converted to markdown.'''
    
    @classmethod
    @property
    def INLINE_HTML(cls) -> MarkdownFeatures:
        '''This flag enables HTML elements inlining. If this flag is set than block level elements (such as ``div``) whose ``markdown`` attribute value equals ``inline`` will be inserted in to resulting markdown.'''
        ...
    
    @classmethod
    @property
    def AUTOMATIC_PARAGRAPH(cls) -> MarkdownFeatures:
        '''This flag enables conversion of ``paragraph`` elements. Content of such elements will be placed on separate lines, so markdown handlers will wrap it.'''
        ...
    
    @classmethod
    @property
    def HEADER(cls) -> MarkdownFeatures:
        '''This flag enables conversion of ``header`` elements.'''
        ...
    
    @classmethod
    @property
    def BLOCKQUOTE(cls) -> MarkdownFeatures:
        '''This flag enables conversion of ``blockquote`` elements.'''
        ...
    
    @classmethod
    @property
    def LIST(cls) -> MarkdownFeatures:
        '''This flag enables conversion of ``list`` elements.'''
        ...
    
    @classmethod
    @property
    def CODE_BLOCK(cls) -> MarkdownFeatures:
        '''This flag enables conversion of code blocks. Code block consists of 2 elements ``pre`` and ``code``, content of such construction is processes "as is".'''
        ...
    
    @classmethod
    @property
    def HORIZONTAL_RULE(cls) -> MarkdownFeatures:
        '''This flag enables conversion of ``horizontal rules``.'''
        ...
    
    @classmethod
    @property
    def LINK(cls) -> MarkdownFeatures:
        '''This flag enables conversion of ``a`` elements.'''
        ...
    
    @classmethod
    @property
    def EMPHASIS(cls) -> MarkdownFeatures:
        '''This flag enables conversion of ``emphasis`` elements.'''
        ...
    
    @classmethod
    @property
    def INLINE_CODE(cls) -> MarkdownFeatures:
        '''This flag enables conversion of ``code`` elements.'''
        ...
    
    @classmethod
    @property
    def IMAGE(cls) -> MarkdownFeatures:
        '''This flag enables conversion of ``img`` elements.'''
        ...
    
    @classmethod
    @property
    def LINE_BREAK(cls) -> MarkdownFeatures:
        '''This flag enables conversion of ``br`` elements.'''
        ...
    
    @classmethod
    @property
    def VIDEO(cls) -> MarkdownFeatures:
        '''This flag enables conversion of ``video`` elements.'''
        ...
    
    @classmethod
    @property
    def TABLE(cls) -> MarkdownFeatures:
        '''This flag enables conversion of ``table`` elements.'''
        ...
    
    @classmethod
    @property
    def TASK_LIST(cls) -> MarkdownFeatures:
        '''This flag enables conversion of task lists. Task list consists of ``input`` element, which must be the first child of ``list`` element and whose ``type`` attribute value should equal ``checkbox``.'''
        ...
    
    @classmethod
    @property
    def STRIKETHROUGH(cls) -> MarkdownFeatures:
        '''This flag enables conversion of ``del`` elements.'''
        ...
    
    @classmethod
    @property
    def STRONG(cls) -> MarkdownFeatures:
        '''This flag enables conversion of ``strong`` elements.'''
        ...
    
    ...

class MarkdownFormatter:
    '''Specifies the way output will be formatted.'''
    
    @classmethod
    @property
    def DEFAULT(cls) -> MarkdownFormatter:
        '''Document will be saved using default markdown style.'''
        ...
    
    @classmethod
    @property
    def GIT(cls) -> MarkdownFormatter:
        '''Document will be saved using Git markdown style.'''
        ...
    
    ...

class ResourceHandling:
    '''This enum represents resource handling options.'''
    
    @classmethod
    @property
    def SAVE(cls) -> ResourceHandling:
        '''Resource will be saved as file.'''
        ...
    
    @classmethod
    @property
    def EMBED(cls) -> ResourceHandling:
        '''Resource will be emdedded in to owner.'''
        ...
    
    @classmethod
    @property
    def DISCARD(cls) -> ResourceHandling:
        '''Resource will be discarded.'''
        ...
    
    @classmethod
    @property
    def IGNORE(cls) -> ResourceHandling:
        '''Resource will not be saved.'''
        ...
    
    ...

class ResourceStatus:
    '''Indicates the resource status.'''
    
    @classmethod
    @property
    def INITIAL(cls) -> ResourceStatus:
        '''Initial resource status.'''
        ...
    
    @classmethod
    @property
    def IGNORED(cls) -> ResourceStatus:
        '''Resource was ignored by filter.'''
        ...
    
    @classmethod
    @property
    def NOT_FOUND(cls) -> ResourceStatus:
        '''Resource was not found.'''
        ...
    
    @classmethod
    @property
    def SAVED(cls) -> ResourceStatus:
        '''Resource was saved.'''
        ...
    
    @classmethod
    @property
    def EMBEDDED(cls) -> ResourceStatus:
        '''Resource was embedded.'''
        ...
    
    ...

class UrlRestriction:
    '''This enum represents restriction applied to URLs of processed resources.'''
    
    @classmethod
    @property
    def ROOT_AND_SUB_FOLDERS(cls) -> UrlRestriction:
        '''Only resources located in the root and sub folders are processed.'''
        ...
    
    @classmethod
    @property
    def SAME_HOST(cls) -> UrlRestriction:
        '''Only resources located in the same host are processed.'''
        ...
    
    @classmethod
    @property
    def NONE(cls) -> UrlRestriction:
        '''All resources are processed.'''
        ...
    
    ...

