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

class RuleValidationResult:
    '''Class - result of rule check, contains a list of :py:class:`aspose.html.accessibility.ITechniqueResult`, which are ways to satisfy the success criteria.'''
    
    @property
    def success(self) -> bool:
        '''Returns the result of rule validation.'''
        ...
    
    @property
    def rule(self) -> aspose.html.accessibility.IRule:
        '''Rule that has been tested.'''
        ...
    
    @property
    def results(self) -> List[aspose.html.accessibility.ITechniqueResult]:
        '''Collection of :py:class:`aspose.html.accessibility.ITechniqueResult` on rule validation.'''
        ...
    
    @property
    def errors(self) -> List[aspose.html.accessibility.ITechniqueResult]:
        '''Collection of results with Errors'''
        ...
    
    @property
    def warnings(self) -> List[aspose.html.accessibility.ITechniqueResult]:
        '''Collection of results with Warnings'''
        ...
    
    ...

class ValidationResult:
    '''The main result class, that contains Results for all Criterion from AccessibilityRules object.'''
    
    def save_to_string(self) -> str:
        '''Save validation results to string
        
        :returns: string with results'''
        ...
    
    @property
    def success(self) -> bool:
        '''The result of validation.'''
        ...
    
    @property
    def details(self) -> List[aspose.html.accessibility.results.RuleValidationResult]:
        '''Validation result details'''
        ...
    
    ...

