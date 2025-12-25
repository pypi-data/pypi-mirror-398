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

class Converter:
    '''Shared facade only for most often conversion scenarios.
    It provides a wide range of conversions to the popular formats, such as PDF, XPS, image formats, etc.
    More specific conversion (rendering, saving) user cases are presented by well known and documented low level API functions.'''
    
    @overload
    @staticmethod
    def convert_template(template : aspose.html.HTMLDocumentdata : aspose.html.converters.TemplateData, options : aspose.html.loading.TemplateLoadOptions, output_path : str):
        '''Merge html template with user data. Result is html file.
        
        :param template: Source skeleton html doc.
        :param data: Data for merging (XML, JSON).
        :param options: Merging options object.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_template(url : aspose.html.Urldata : aspose.html.converters.TemplateData, options : aspose.html.loading.TemplateLoadOptions, output_path : str):
        '''Merge html template with user data. Result is html file.
        
        :param url: Template source document URL.
        :param data: Data for merging (XML, JSON).
        :param options: Merging options object.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_template(url : aspose.html.Urlconfiguration : aspose.html.Configuration, data : aspose.html.converters.TemplateData, options : aspose.html.loading.TemplateLoadOptions, output_path : str):
        '''Merge html template with user data. Result is html file.
        
        :param url: Template source document URL.
        :param configuration: The environment configuration.
        :param data: Data for merging (XML, JSON).
        :param options: Merging options object.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_template(source_path : strdata : aspose.html.converters.TemplateData, options : aspose.html.loading.TemplateLoadOptions, output_path : str):
        '''Merge html template with user data. Result is html file.
        
        :param source_path: Path to template source html file. It will be combined with the current directory path to form an absolute URL.
        :param data: Data for merging (XML, JSON).
        :param options: Merging options object.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_template(source_path : strconfiguration : aspose.html.Configuration, data : aspose.html.converters.TemplateData, options : aspose.html.loading.TemplateLoadOptions, output_path : str):
        '''Merge html template with user data. Result is html file.
        
        :param source_path: Path to template source html file. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param data: Data for merging (XML, JSON).
        :param options: Merging options object.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_template(content : strbase_url : str, data : aspose.html.converters.TemplateData, options : aspose.html.loading.TemplateLoadOptions, output_path : str):
        '''Merge html template with user data. Result is html file.
        
        :param content: Inline html template - skeleton.
        :param base_url: Base URI of the html template. It will be combined with the current directory path to form an absolute URL.
        :param data: Data for merging (XML, JSON).
        :param options: Merging options object.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_template(content : strbase_url : str, configuration : aspose.html.Configuration, data : aspose.html.converters.TemplateData, options : aspose.html.loading.TemplateLoadOptions, output_path : str):
        '''Merge html template with user data. Result is html file.
        
        :param content: Inline html template - skeleton.
        :param base_url: Base URI of the html template. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param data: Data for merging (XML, JSON).
        :param options: Merging options object.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_template(template : aspose.html.HTMLDocumentdata : aspose.html.converters.TemplateData, options : aspose.html.loading.TemplateLoadOptions) -> aspose.html.HTMLDocument:
        '''Merge html template with user data. Result is :py:class:`aspose.html.HTMLDocument`.
        
        :param template: Source skeleton html doc.
        :param data: Data for merging (XML, JSON).
        :param options: Merging options object.
        :returns: Conversion result HTMLDocument.'''
        ...
    
    @overload
    @staticmethod
    def convert_template(url : aspose.html.Urldata : aspose.html.converters.TemplateData, options : aspose.html.loading.TemplateLoadOptions) -> aspose.html.HTMLDocument:
        '''Merge html template with user data. Result is :py:class:`aspose.html.HTMLDocument`.
        
        :param url: Template source document URL.
        :param data: Data for merging (XML, JSON).
        :param options: Merging options object.
        :returns: Conversion result HTMLDocument.'''
        ...
    
    @overload
    @staticmethod
    def convert_template(url : aspose.html.Urlconfiguration : aspose.html.Configuration, data : aspose.html.converters.TemplateData, options : aspose.html.loading.TemplateLoadOptions) -> aspose.html.HTMLDocument:
        '''Merge html template with user data. Result is :py:class:`aspose.html.HTMLDocument`.
        
        :param url: Template source document URL.
        :param configuration: The environment configuration.
        :param data: Data for merging (XML, JSON).
        :param options: Merging options object.
        :returns: Conversion result HTMLDocument.'''
        ...
    
    @overload
    @staticmethod
    def convert_template(source_path : strdata : aspose.html.converters.TemplateData, options : aspose.html.loading.TemplateLoadOptions) -> aspose.html.HTMLDocument:
        '''Merge html template with user data. Result is :py:class:`aspose.html.HTMLDocument`.
        
        :param source_path: Path to template source html file. It will be combined with the current directory path to form an absolute URL.
        :param data: Data for merging (XML, JSON).
        :param options: Merging options object.
        :returns: Conversion result HTMLDocument.'''
        ...
    
    @overload
    @staticmethod
    def convert_template(source_path : strconfiguration : aspose.html.Configuration, data : aspose.html.converters.TemplateData, options : aspose.html.loading.TemplateLoadOptions) -> aspose.html.HTMLDocument:
        '''Merge html template with user data. Result is :py:class:`aspose.html.HTMLDocument`.
        
        :param source_path: Path to template source html file. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param data: Data for merging (XML, JSON).
        :param options: Merging options object.
        :returns: Conversion result HTMLDocument.'''
        ...
    
    @overload
    @staticmethod
    def convert_template(content : strbase_url : str, data : aspose.html.converters.TemplateData, options : aspose.html.loading.TemplateLoadOptions) -> aspose.html.HTMLDocument:
        '''Merge html template with user data. Result is :py:class:`aspose.html.HTMLDocument`.
        
        :param content: Inline html template - skeleton.
        :param base_url: Base URI of the html template. It will be combined with the current directory path to form an absolute URL.
        :param data: Data for merging (XML, JSON).
        :param options: Merging options object.
        :returns: Conversion result HTMLDocument.'''
        ...
    
    @overload
    @staticmethod
    def convert_template(content : strbase_url : str, configuration : aspose.html.Configuration, data : aspose.html.converters.TemplateData, options : aspose.html.loading.TemplateLoadOptions) -> aspose.html.HTMLDocument:
        '''Merge html template with user data. Result is :py:class:`aspose.html.HTMLDocument`.
        
        :param content: Inline html template - skeleton.
        :param base_url: Base URI of the html template. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param data: Data for merging (XML, JSON).
        :param options: Merging options object.
        :returns: Conversion result HTMLDocument.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(document : aspose.html.HTMLDocumentoptions : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert html source document to PDF. Result is pdf file.
        
        :param document: Conversion source :py:class:`aspose.html.HTMLDocument`.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(url : aspose.html.Urloptions : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert html source document to PDF. Result is pdf file.
        
        :param url: The document URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert html source document to PDF. Result is pdf file.
        
        :param url: The document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(source_path : stroptions : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert html source document to PDF. Result is pdf file.
        
        :param source_path: Html file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert html source document to PDF. Result is pdf file.
        
        :param source_path: Html file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(content : strbase_uri : str, options : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert html source document to PDF. Result is pdf file.
        
        :param content: Inline string html content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(content : strbase_uri : str, configuration : aspose.html.Configuration, options : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert html source document to PDF. Result is pdf file.
        
        :param content: Inline string html content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(document : aspose.html.HTMLDocumentoptions : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert html source document to PDF. Result is pdf file.
        
        :param document: Conversion source :py:class:`aspose.html.HTMLDocument`.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(url : aspose.html.Urloptions : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert html source document to PDF. Result is pdf file.
        
        :param url: The document URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert html source document to PDF. Result is pdf file.
        
        :param url: The document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(source_path : stroptions : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert html source document to PDF. Result is pdf file.
        
        :param source_path: Html file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert html source document to PDF. Result is pdf file.
        
        :param source_path: Html file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(content : strbase_uri : str, options : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert html source document to PDF. Result is pdf file.
        
        :param content: Inline string html content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(content : strbase_uri : str, configuration : aspose.html.Configuration, options : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert html source document to PDF. Result is pdf file.
        
        :param content: Inline string html content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(document : aspose.html.HTMLDocumentoptions : aspose.html.saving.MHTMLSaveOptions, output_path : str):
        '''Convert html document to mhtml. Result is mhtml file.
        
        :param document: Conversion source.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(url : aspose.html.Urloptions : aspose.html.saving.MHTMLSaveOptions, output_path : str):
        '''Convert html document to mhtml. Result is mhtml file.
        
        :param url: The document URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.MHTMLSaveOptions, output_path : str):
        '''Convert html document to mhtml. Result is mhtml file.
        
        :param url: The document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(source_path : stroptions : aspose.html.saving.MHTMLSaveOptions, output_path : str):
        '''Convert html document to mhtml. Result is mhtml file.
        
        :param source_path: Html file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.MHTMLSaveOptions, output_path : str):
        '''Convert html document to mhtml. Result is mhtml file.
        
        :param source_path: Html file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(content : strbase_uri : str, options : aspose.html.saving.MHTMLSaveOptions, output_path : str):
        '''Convert html document to mhtml. Result is mhtml file.
        
        :param content: Inline string html content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(content : strbase_uri : str, configuration : aspose.html.Configuration, options : aspose.html.saving.MHTMLSaveOptions, output_path : str):
        '''Convert html document to mhtml. Result is mhtml file.
        
        :param content: Inline string html content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(document : aspose.html.HTMLDocumentoptions : aspose.html.saving.MarkdownSaveOptions, output_path : str):
        '''Convert html document to markdown. Result is md file.
        
        :param document: Conversion source.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(url : aspose.html.Urloptions : aspose.html.saving.MarkdownSaveOptions, output_path : str):
        '''Convert html source to markdown. Result is md file.
        
        :param url: The document URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.MarkdownSaveOptions, output_path : str):
        '''Convert html source to markdown. Result is md file.
        
        :param url: The document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(source_path : stroptions : aspose.html.saving.MarkdownSaveOptions, output_path : str):
        '''Convert html source to markdown. Result is md file.
        
        :param source_path: Html file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.MarkdownSaveOptions, output_path : str):
        '''Convert html source to markdown. Result is md file.
        
        :param source_path: Html file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(content : strbase_uri : str, options : aspose.html.saving.MarkdownSaveOptions, output_path : str):
        '''Convert html source to markdown. Result is md file.
        
        :param content: Inline string html content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(content : strbase_uri : str, configuration : aspose.html.Configuration, options : aspose.html.saving.MarkdownSaveOptions, output_path : str):
        '''Convert html source to markdown. Result is md file.
        
        :param content: Inline string html content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(stream : io.RawIOBaseconfiguration : aspose.html.Configuration, options : aspose.html.saving.MarkdownSaveOptions, output_path : str):
        '''Convert HTML source stream to markdown. Result is md file.
        
        :param stream: HTML source stream.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(stream : io.RawIOBasebase_uri : str, options : aspose.html.saving.MarkdownSaveOptions, output_path : str):
        '''Convert HTML source stream to markdown. Result is md file.
        
        :param stream: HTML source stream.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(stream : io.RawIOBasebase_uri : str, configuration : aspose.html.Configuration, options : aspose.html.saving.MarkdownSaveOptions, output_path : str):
        '''Convert HTML source stream to markdown. Result is md file.
        
        :param stream: HTML source stream.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(document : aspose.html.HTMLDocumentoptions : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert html document to xps. Result is xps file.
        
        :param document: Conversion source.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(url : aspose.html.Urloptions : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert html document to xps. Result is xps file.
        
        :param url: The document URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert html document to xps. Result is xps file.
        
        :param url: The document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(source_path : stroptions : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert html document to xps. Result is xps file.
        
        :param source_path: Html file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert html document to xps. Result is xps file.
        
        :param source_path: Html file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(content : strbase_uri : str, options : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert html document to xps. Result is xps file.
        
        :param content: Inline string html content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(content : strbase_uri : str, configuration : aspose.html.Configuration, options : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert html document to xps. Result is xps file.
        
        :param content: Inline string html content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(document : aspose.html.HTMLDocumentoptions : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert html source to xps. Result is xps file.
        
        :param document: Conversion source.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(url : aspose.html.Urloptions : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert html source to xps. Result is xps file.
        
        :param url: The document URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert html source to xps. Result is xps file.
        
        :param url: The document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(source_path : stroptions : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert html source to xps. Result is xps file.
        
        :param source_path: Html file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert html source to xps. Result is xps file.
        
        :param source_path: Html file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(content : strbase_uri : str, options : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert html source to xps. Result is xps file.
        
        :param content: Inline string html content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(content : strbase_uri : str, configuration : aspose.html.Configuration, options : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert html source to xps. Result is xps file.
        
        :param content: Inline string html content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(document : aspose.html.HTMLDocumentoptions : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert html document to image. Result is image file.
        
        :param document: Conversion source.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(url : aspose.html.Urloptions : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert html document to image. Result is image file.
        
        :param url: The document URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert html document to image. Result is image file.
        
        :param url: The document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(source_path : stroptions : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert html document to image. Result is image file.
        
        :param source_path: Html file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert html document to image. Result is image file.
        
        :param source_path: Html file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(content : strbase_uri : str, options : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert html document to image. Result is image file.
        
        :param content: Inline string html content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(content : strbase_uri : str, configuration : aspose.html.Configuration, options : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert html document to image. Result is image file.
        
        :param content: Inline string html content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(document : aspose.html.HTMLDocumentoptions : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert html source to image. Result is image file.
        
        :param document: Conversion source.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(url : aspose.html.Urloptions : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert html source to image. Result is image file.
        
        :param url: The document URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert html source to image. Result is image file.
        
        :param url: The document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(source_path : stroptions : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert html source to image. Result is image file.
        
        :param source_path: Html file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert html source to image. Result is image file.
        
        :param source_path: Html file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(content : strbase_uri : str, options : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert html source to image. Result is image file.
        
        :param content: Inline string html content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(content : strbase_uri : str, configuration : aspose.html.Configuration, options : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert html source to image. Result is image file.
        
        :param content: Inline string html content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(document : aspose.html.HTMLDocumentoptions : aspose.html.saving.TextSaveOptions, output_path : str):
        '''Convert html document to text. Result is TXT file.
        
        :param document: Conversion source.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(url : aspose.html.Urloptions : aspose.html.saving.TextSaveOptions, output_path : str):
        '''Convert html document to text. Result is TXT file.
        
        :param url: The document URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.TextSaveOptions, output_path : str):
        '''Convert html document to text. Result is TXT file.
        
        :param url: The document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(source_path : stroptions : aspose.html.saving.TextSaveOptions, output_path : str):
        '''Convert html document to text. Result is TXT file.
        
        :param source_path: Html file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.TextSaveOptions, output_path : str):
        '''Convert html document to text. Result is TXT file.
        
        :param source_path: Html file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(content : strbase_uri : str, options : aspose.html.saving.TextSaveOptions, output_path : str):
        '''Convert html document to text. Result is TXT file.
        
        :param content: Inline string html content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(content : strbase_uri : str, configuration : aspose.html.Configuration, options : aspose.html.saving.TextSaveOptions, output_path : str):
        '''Convert html document to text. Result is TXT file.
        
        :param content: Inline string html content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(document : aspose.html.HTMLDocumentoptions : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert HTML source document to DOCX. Result is docx file.
        
        :param document: Conversion source :py:class:`aspose.html.HTMLDocument`.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(url : aspose.html.Urloptions : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert HTML source document to DOCX. Result is docx file.
        
        :param url: The document URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert HTML source document to DOCX. Result is docx file.
        
        :param url: The document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(source_path : stroptions : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert HTML source document to DOCX. Result is docx file.
        
        :param source_path: HTML file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert HTML source document to DOCX. Result is docx file.
        
        :param source_path: HTML file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(content : strbase_uri : str, options : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert HTML source document to DOCX. Result is docx file.
        
        :param content: Inline string HTML content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(content : strbase_uri : str, configuration : aspose.html.Configuration, options : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert HTML source document to DOCX. Result is docx file.
        
        :param content: Inline string html content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(document : aspose.html.HTMLDocumentoptions : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert HTML source document to DOCX. Result is docx file.
        
        :param document: Conversion source :py:class:`aspose.html.HTMLDocument`.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(url : aspose.html.Urloptions : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert HTML source document to DOCX. Result is docx file.
        
        :param url: The document URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert HTML source document to DOCX. Result is docx file.
        
        :param url: The document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(source_path : stroptions : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert HTML source document to DOCX. Result is docx file.
        
        :param source_path: HTML file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert HTML source document to DOCX. Result is docx file.
        
        :param source_path: HTML file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(content : strbase_uri : str, options : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert HTML source document to DOCX. Result is docx file.
        
        :param content: Inline string HTML content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_html(content : strbase_uri : str, configuration : aspose.html.Configuration, options : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert HTML source document to DOCX. Result is docx file.
        
        :param content: Inline string HTML content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source : aspose.html.dom.svg.SVGDocumentoptions : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert svg document to xps.Result is xps file.
        
        :param source: Conversion source.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.html.Urloptions : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert svg source to xps. Result is xps file.
        
        :param url: Source document URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert svg source to xps. Result is xps file.
        
        :param url: Source document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : stroptions : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert svg source to xps. Result is xps file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert svg source to xps. Result is xps file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, options : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert svg source to xps. Result is xps file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, configuration : aspose.html.Configuration, options : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert svg source to xps. Result is xps file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(document : aspose.html.dom.svg.SVGDocumentoptions : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert svg source to xps. Result is xps file.
        
        :param document: Conversion source.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.html.Urloptions : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert svg source to xps. Result is xps file.
        
        :param url: The document URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert svg source to xps. Result is xps file.
        
        :param url: The document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : stroptions : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert svg source to xps. Result is xps file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert svg source to xps. Result is xps file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, options : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert svg source to xps. Result is xps file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, configuration : aspose.html.Configuration, options : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert svg source to xps. Result is xps file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source : aspose.html.dom.svg.SVGDocumentoptions : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert SVG document to DOCX. Result is docx file.
        
        :param source: Conversion source.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.html.Urloptions : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert SVG document to DOCX. Result is docx file.
        
        :param url: Source document URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert SVG document to DOCX. Result is docx file.
        
        :param url: Source document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : stroptions : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert SVG document to DOCX. Result is docx file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert SVG document to DOCX. Result is docx file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, options : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert SVG document to DOCX. Result is docx file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, configuration : aspose.html.Configuration, options : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert SVG document to DOCX. Result is docx file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(document : aspose.html.dom.svg.SVGDocumentoptions : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert SVG document to DOCX. Result is docx file.
        
        :param document: Conversion source.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.html.Urloptions : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert SVG document to DOCX. Result is docx file.
        
        :param url: The document URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert SVG document to DOCX. Result is docx file.
        
        :param url: The document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : stroptions : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert SVG document to DOCX. Result is docx file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert SVG document to DOCX. Result is docx file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, options : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert SVG document to DOCX. Result is docx file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, configuration : aspose.html.Configuration, options : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert SVG document to DOCX. Result is docx file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source : aspose.html.dom.svg.SVGDocumentoptions : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param source: Conversion source.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.html.Urloptions : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param url: The document URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param url: The document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : stroptions : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, options : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, configuration : aspose.html.Configuration, options : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(document : aspose.html.dom.svg.SVGDocumentoptions : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param document: Conversion source.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.html.Urloptions : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param url: The document URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param url: The document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : stroptions : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, options : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param content: Source document content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, configuration : aspose.html.Configuration, options : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source : aspose.html.dom.svg.SVGDocumentoptions : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert svg document to image. Result is image file.
        
        :param source: Conversion source.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.html.Urloptions : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert svg document to image. Result is image file.
        
        :param url: The document URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert svg document to image. Result is image file.
        
        :param url: The document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : stroptions : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert svg document to image. Result is image file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert svg document to image. Result is image file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, options : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert svg document to image. Result is image file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, configuration : aspose.html.Configuration, options : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert svg document to image. Result is image file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(document : aspose.html.dom.svg.SVGDocumentoptions : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert svg source to image. Result is image file.
        
        :param document: Conversion source.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.html.Urloptions : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert svg source to image. Result is image file.
        
        :param url: The document URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert svg source to image. Result is image file.
        
        :param url: The document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : stroptions : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert svg source to image. Result is image file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert svg source to image. Result is image file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, options : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert svg source to image. Result is image file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, configuration : aspose.html.Configuration, options : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert svg source to image. Result is image file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(stream : io.RawIOBaseoptions : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert epub source to xps. Result is xps file.
        
        :param stream: Conversion source.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_path : stroptions : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert epub source to xps. Result is xps file.
        
        :param source_path: EPUB source file path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_url : aspose.html.Urloptions : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert epub source to xps. Result is xps file.
        
        :param source_url: The source URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(stream : io.RawIOBaseconfiguration : aspose.html.Configuration, options : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert epub source to xps. Result is xps file.
        
        :param stream: Conversion source.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert epub source to xps. Result is xps file.
        
        :param source_path: EPUB source file path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert epub source to xps. Result is xps file.
        
        :param source_url: The source URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(stream : io.RawIOBaseoptions : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert epub source to xps. Result is xps file.
        
        :param stream: Conversion source.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_path : stroptions : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert epub source to xps. Result is xps file.
        
        :param source_path: EPUB source file path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_url : aspose.html.Urloptions : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert epub source to xps. Result is xps file.
        
        :param source_url: The source URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(stream : io.RawIOBaseconfiguration : aspose.html.Configuration, options : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert epub source to xps. Result is xps file.
        
        :param stream: Conversion source.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert epub source to xps. Result is xps file.
        
        :param source_path: EPUB source file path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert epub source to xps. Result is xps file.
        
        :param source_url: The source URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(stream : io.RawIOBaseoptions : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert EPUB source to DOCX. Result is docx file.
        
        :param stream: Conversion source.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_path : stroptions : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert EPUB source to DOCX. Result is docx file.
        
        :param source_path: EPUB source file path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_url : aspose.html.Urloptions : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert EPUB source to DOCX. Result is docx file.
        
        :param source_url: The source URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(stream : io.RawIOBaseconfiguration : aspose.html.Configuration, options : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert EPUB source to DOCX. Result is docx file.
        
        :param stream: Conversion source.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert EPUB source to DOCX. Result is docx file.
        
        :param source_path: EPUB source file path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert EPUB source to DOCX. Result is docx file.
        
        :param source_url: The source URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(stream : io.RawIOBaseoptions : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert EPUB source to DOCX. Result is docx file.
        
        :param stream: Conversion source.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_path : stroptions : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert EPUB source to DOCX. Result is docx file.
        
        :param source_path: EPUB source file path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_url : aspose.html.Urloptions : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert EPUB source to DOCX. Result is docx file.
        
        :param source_url: The source URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(stream : io.RawIOBaseconfiguration : aspose.html.Configuration, options : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert EPUB source to DOCX. Result is docx file.
        
        :param stream: Conversion source.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert EPUB source to DOCX. Result is docx file.
        
        :param source_path: EPUB source file path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert EPUB source to DOCX. Result is docx file.
        
        :param source_url: The source URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(stream : io.RawIOBaseoptions : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert epub source to pdf. Result is pdf file.
        
        :param stream: Conversion source.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_path : stroptions : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert epub source to pdf. Result is pdf file.
        
        :param source_path: EPUB source file path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_url : aspose.html.Urloptions : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert epub source to pdf. Result is pdf file.
        
        :param source_url: The source URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(stream : io.RawIOBaseconfiguration : aspose.html.Configuration, options : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert epub source to pdf. Result is pdf file.
        
        :param stream: Conversion source.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert epub source to pdf. Result is pdf file.
        
        :param source_path: EPUB source file path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert epub source to pdf. Result is pdf file.
        
        :param source_url: The source URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(stream : io.RawIOBaseoptions : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert epub source to pdf. Result is pdf file.
        
        :param stream: Conversion source.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_path : stroptions : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert epub source to pdf. Result is pdf file.
        
        :param source_path: EPUB source file path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_url : aspose.html.Urloptions : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert epub source to pdf. Result is pdf file.
        
        :param source_url: The source URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(stream : io.RawIOBaseconfiguration : aspose.html.Configuration, options : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert epub source to pdf. Result is pdf file.
        
        :param stream: Conversion source.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert epub source to pdf. Result is pdf file.
        
        :param source_path: EPUB source file path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert epub source to pdf. Result is pdf file.
        
        :param source_url: The source URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(stream : io.RawIOBaseoptions : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert epub source to image. Result is image file.
        
        :param stream: Conversion source.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_path : stroptions : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert epub source to image. Result is image file.
        
        :param source_path: EPUB source file path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_url : aspose.html.Urloptions : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert epub source to image. Result is image file.
        
        :param source_url: The source URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(stream : io.RawIOBaseconfiguration : aspose.html.Configuration, options : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert epub source to image. Result is image file.
        
        :param stream: Conversion source.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert epub source to image. Result is image file.
        
        :param source_path: EPUB source file path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert epub source to image. Result is image file.
        
        :param source_url: The source URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(stream : io.RawIOBaseoptions : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert epub source to image. Result is image file.
        
        :param stream: Conversion source.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_path : stroptions : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert epub source to image. Result is image file.
        
        :param source_path: EPUB source file path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_url : aspose.html.Urloptions : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert epub source to image. Result is image file.
        
        :param source_url: The source URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(stream : io.RawIOBaseconfiguration : aspose.html.Configuration, options : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert epub source to image. Result is image file.
        
        :param stream: Conversion source.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert epub source to image. Result is image file.
        
        :param source_path: EPUB source file path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_epub(source_url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert epub source to image. Result is image file.
        
        :param source_url: The source URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_markdown(stream : io.RawIOBasebase_uri : str) -> aspose.html.HTMLDocument:
        '''Convert Markdown source to html. Result is :py:class:`aspose.html.HTMLDocument`.
        
        :param stream: Conversion source.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :returns: Conversion result :py:class:`aspose.html.HTMLDocument`.'''
        ...
    
    @overload
    @staticmethod
    def convert_markdown(stream : io.RawIOBasebase_uri : str, configuration : aspose.html.Configuration) -> aspose.html.HTMLDocument:
        '''Convert Markdown source to html. Result is :py:class:`aspose.html.HTMLDocument`.
        
        :param stream: Conversion source.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :returns: Conversion result :py:class:`aspose.html.HTMLDocument`.'''
        ...
    
    @overload
    @staticmethod
    def convert_markdown(stream : io.RawIOBasebase_uri : str, output_path : str):
        '''Convert Markdown source to html. Result is html file.
        
        :param stream: Conversion source.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_markdown(stream : io.RawIOBasebase_uri : str, configuration : aspose.html.Configuration, output_path : str):
        '''Convert Markdown source to html. Result is html file.
        
        :param stream: Conversion source.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_markdown(source_path : str) -> aspose.html.HTMLDocument:
        '''Convert Markdown source to html. Result is :py:class:`aspose.html.HTMLDocument`.
        
        :param source_path: Path to source Markdown file. It will be combined with the current directory path to form an absolute URL.
        :returns: Conversion result :py:class:`aspose.html.HTMLDocument`.'''
        ...
    
    @overload
    @staticmethod
    def convert_markdown(source_path : strconfiguration : aspose.html.Configuration) -> aspose.html.HTMLDocument:
        '''Convert Markdown source to html. Result is :py:class:`aspose.html.HTMLDocument`.
        
        :param source_path: Path to source Markdown file. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :returns: Conversion result :py:class:`aspose.html.HTMLDocument`.'''
        ...
    
    @overload
    @staticmethod
    def convert_markdown(source_path : stroutput_path : str):
        '''Convert Markdown source to html. Result is html file.
        
        :param source_path: Path to source Markdown file. It will be combined with the current directory path to form an absolute URL.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_markdown(source_path : strconfiguration : aspose.html.Configuration, output_path : str):
        '''Convert Markdown source to html. Result is html file.
        
        :param source_path: Path to source Markdown file. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(stream : io.RawIOBaseoptions : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert mhtml source to xps. Result is xps file.
        
        :param stream: Conversion source stream.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_path : stroptions : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert mhtml source to xps. Result is xps file.
        
        :param source_path: MHTML source file path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_url : aspose.html.Urloptions : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert mhtml source to xps. Result is xps file.
        
        :param source_url: The source URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(stream : io.RawIOBaseconfiguration : aspose.html.Configuration, options : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert mhtml source to xps. Result is xps file.
        
        :param stream: Conversion source stream.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert mhtml source to xps. Result is xps file.
        
        :param source_path: MHTML source file path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.XpsSaveOptions, output_path : str):
        '''Convert mhtml source to xps. Result is xps file.
        
        :param source_url: The source URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(stream : io.RawIOBaseoptions : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert mhtml source to xps. Result is xps file.
        
        :param stream: Conversion source stream.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_path : stroptions : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert mhtml source to xps. Result is xps file.
        
        :param source_path: MHTML source file path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_url : aspose.html.Urloptions : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert mhtml source to xps. Result is xps file.
        
        :param source_url: The source URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(stream : io.RawIOBaseconfiguration : aspose.html.Configuration, options : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert mhtml source to xps. Result is xps file.
        
        :param stream: Conversion source stream.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert mhtml source to xps. Result is xps file.
        
        :param source_path: MHTML source file path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.XpsSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert mhtml source to xps. Result is xps file.
        
        :param source_url: The source URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(stream : io.RawIOBaseoptions : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert MHTML source to DOCX. Result is docx file.
        
        :param stream: Conversion source stream.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_path : stroptions : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert MHTML source to DOCX. Result is docx file.
        
        :param source_path: MHTML source file path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_url : aspose.html.Urloptions : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert MHTML source to DOCX. Result is docx file.
        
        :param source_url: The source URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(stream : io.RawIOBaseconfiguration : aspose.html.Configuration, options : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert MHTML source to DOCX. Result is docx file.
        
        :param stream: Conversion source stream.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert MHTML source to DOCX. Result is docx file.
        
        :param source_path: MHTML source file path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.DocSaveOptions, output_path : str):
        '''Convert MHTML source to DOCX. Result is docx file.
        
        :param source_url: The source URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(stream : io.RawIOBaseoptions : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert MHTML source to DOCX. Result is docx file.
        
        :param stream: Conversion source stream.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_path : stroptions : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert MHTML source to DOCX. Result is docx file.
        
        :param source_path: MHTML source file path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_url : aspose.html.Urloptions : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert MHTML source to DOCX. Result is docx file.
        
        :param source_url: The source URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(stream : io.RawIOBaseconfiguration : aspose.html.Configuration, options : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert MHTML source to DOCX. Result is docx file.
        
        :param stream: Conversion source stream.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert MHTML source to DOCX. Result is docx file.
        
        :param source_path: MHTML source file path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.DocSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert MHTML source to DOCX. Result is docx file.
        
        :param source_url: The source URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(stream : io.RawIOBaseoptions : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert mhtml source to pdf. Result is pdf file.
        
        :param stream: Conversion source stream.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_path : stroptions : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert mhtml source to pdf. Result is pdf file.
        
        :param source_path: MHTML source file path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_url : aspose.html.Urloptions : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert mhtml source to pdf. Result is pdf file.
        
        :param source_url: The source URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(stream : io.RawIOBaseconfiguration : aspose.html.Configuration, options : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert mhtml source to pdf. Result is pdf file.
        
        :param stream: Conversion source stream.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert mhtml source to pdf. Result is pdf file.
        
        :param source_path: MHTML source file path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.PdfSaveOptions, output_path : str):
        '''Convert mhtml source to pdf. Result is pdf file.
        
        :param source_url: The source URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(stream : io.RawIOBaseoptions : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert mhtml source to pdf. Result is pdf file.
        
        :param stream: Conversion source stream.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_path : stroptions : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert mhtml source to pdf. Result is pdf file.
        
        :param source_path: MHTML source file path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_url : aspose.html.Urloptions : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert mhtml source to pdf. Result is pdf file.
        
        :param source_url: The source URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(stream : io.RawIOBaseconfiguration : aspose.html.Configuration, options : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert mhtml source to pdf. Result is pdf file.
        
        :param stream: Conversion source stream.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert mhtml source to pdf. Result is pdf file.
        
        :param source_path: MHTML source file path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.PdfSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert mhtml source to pdf. Result is pdf file.
        
        :param source_url: The source URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(stream : io.RawIOBaseoptions : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert mhtml source to image. Result is image file.
        
        :param stream: Conversion source stream.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_path : stroptions : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert mhtml source to image. Result is image file.
        
        :param source_path: MHTML source file path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_url : aspose.html.Urloptions : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert mhtml source to image. Result is image file.
        
        :param source_url: The source URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(stream : io.RawIOBaseconfiguration : aspose.html.Configuration, options : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert mhtml source to image. Result is image file.
        
        :param stream: Conversion source stream.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert mhtml source to image. Result is image file.
        
        :param source_path: MHTML source file path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.ImageSaveOptions, output_path : str):
        '''Convert mhtml source to image. Result is image file.
        
        :param source_url: The source URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(stream : io.RawIOBaseoptions : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert mhtml source to image. Result is image file.
        
        :param stream: Conversion source stream.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_path : stroptions : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert mhtml source to image. Result is image file.
        
        :param source_path: MHTML source file path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_url : aspose.html.Urloptions : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert mhtml source to image. Result is image file.
        
        :param source_url: The source URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(stream : io.RawIOBaseconfiguration : aspose.html.Configuration, options : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert mhtml source to image. Result is image file.
        
        :param stream: Conversion source stream.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_path : strconfiguration : aspose.html.Configuration, options : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert mhtml source to image. Result is image file.
        
        :param source_path: MHTML source file path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_mhtml(source_url : aspose.html.Urlconfiguration : aspose.html.Configuration, options : aspose.html.saving.ImageSaveOptions, provider : aspose.html.io.ICreateStreamProvider):
        '''Convert mhtml source to image. Result is image file.
        
        :param source_url: The source URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.html.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    ...

class TemplateContentOptions:
    '''Inline content object for merging processing.'''
    
    @property
    def data_content(self) -> str:
        ...
    
    @property
    def content_type(self) -> aspose.html.converters.TemplateContent:
        ...
    
    @property
    def format(self) -> str:
        '''String representation of :py:attr:`aspose.html.converters.TemplateContentOptions.content_type` property.'''
        ...
    
    ...

class TemplateData:
    '''Merging (User) data object.'''
    
    @property
    def data_path(self) -> str:
        ...
    
    @property
    def content_options(self) -> aspose.html.converters.TemplateContentOptions:
        ...
    
    ...

class TemplateContent:
    '''Content type identifier.'''
    
    @classmethod
    @property
    def UNDEFINED(cls) -> TemplateContent:
        '''Undetermined value.'''
        ...
    
    @classmethod
    @property
    def XML(cls) -> TemplateContent:
        '''XML content identifier.'''
        ...
    
    @classmethod
    @property
    def JSON(cls) -> TemplateContent:
        '''JSON content identifier.'''
        ...
    
    ...

