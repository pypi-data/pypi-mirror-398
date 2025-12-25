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

class SVGOptimizationOptions:
    '''SVGOptimizationOptions is a class for storing options for optimizing SVG documents.'''
    
    @property
    def collapse_groups(self) -> bool:
        ...
    
    @collapse_groups.setter
    def collapse_groups(self, value : bool):
        ...
    
    @property
    def remove_descriptions(self) -> bool:
        ...
    
    @remove_descriptions.setter
    def remove_descriptions(self, value : bool):
        ...
    
    @property
    def remove_empty_attributes(self) -> bool:
        ...
    
    @remove_empty_attributes.setter
    def remove_empty_attributes(self, value : bool):
        ...
    
    @property
    def remove_empty_containers(self) -> bool:
        ...
    
    @remove_empty_containers.setter
    def remove_empty_containers(self, value : bool):
        ...
    
    @property
    def remove_empty_text(self) -> bool:
        ...
    
    @remove_empty_text.setter
    def remove_empty_text(self, value : bool):
        ...
    
    @property
    def remove_hidden_elements(self) -> bool:
        ...
    
    @remove_hidden_elements.setter
    def remove_hidden_elements(self, value : bool):
        ...
    
    @property
    def remove_metadata(self) -> bool:
        ...
    
    @remove_metadata.setter
    def remove_metadata(self, value : bool):
        ...
    
    @property
    def remove_unused_namespaces(self) -> bool:
        ...
    
    @remove_unused_namespaces.setter
    def remove_unused_namespaces(self, value : bool):
        ...
    
    @property
    def remove_unused_defs(self) -> bool:
        ...
    
    @remove_unused_defs.setter
    def remove_unused_defs(self, value : bool):
        ...
    
    @property
    def remove_useless_stroke_and_fill(self) -> bool:
        ...
    
    @remove_useless_stroke_and_fill.setter
    def remove_useless_stroke_and_fill(self, value : bool):
        ...
    
    @property
    def clean_list_of_values(self) -> bool:
        ...
    
    @clean_list_of_values.setter
    def clean_list_of_values(self, value : bool):
        ...
    
    @property
    def remove_indents_and_line_breaks(self) -> bool:
        ...
    
    @remove_indents_and_line_breaks.setter
    def remove_indents_and_line_breaks(self, value : bool):
        ...
    
    @property
    def path_optimization_options(self) -> aspose.html.toolkit.optimizers.SVGPathOptimizationOptions:
        ...
    
    @path_optimization_options.setter
    def path_optimization_options(self, value : aspose.html.toolkit.optimizers.SVGPathOptimizationOptions):
        ...
    
    ...

class SVGOptimizer:
    '''SVGOptimizer is a static class designed to optimize SVG documents.
    By optimization, we mean removing unused or invisible elements and their attributes,
    merging groups, and reducing the size of path segments.'''
    
    @overload
    @staticmethod
    def optimize(document : aspose.html.dom.svg.SVGDocument):
        '''Optimizes :py:class:`aspose.html.dom.svg.SVGDocument` by applying a set of default optimization options.
        
        :param document: The instance of SVGDocument.'''
        ...
    
    @overload
    @staticmethod
    def optimize(document : aspose.html.dom.svg.SVGDocumentoptions : aspose.html.toolkit.optimizers.SVGOptimizationOptions):
        '''Optimizes :py:class:`aspose.html.dom.svg.SVGDocument` by applying a set of specified optimization options.
        
        :param document: The instance of SVGDocument.
        :param options: The instance of SVGOptimizationOptions.'''
        ...
    
    ...

class SVGPathOptimizationOptions:
    '''SVGPathOptimizationOptions is a class for storing options for optimizing segments of SVG path elements.'''
    
    @property
    def remove_space_after_flags(self) -> bool:
        ...
    
    @remove_space_after_flags.setter
    def remove_space_after_flags(self, value : bool):
        ...
    
    @property
    def apply_transforms(self) -> bool:
        ...
    
    @apply_transforms.setter
    def apply_transforms(self, value : bool):
        ...
    
    @property
    def float_precision(self) -> int:
        ...
    
    @float_precision.setter
    def float_precision(self, value : int):
        ...
    
    @property
    def arc_building_threshold(self) -> float:
        ...
    
    @arc_building_threshold.setter
    def arc_building_threshold(self, value : float):
        ...
    
    @property
    def arc_building_tolerance(self) -> float:
        ...
    
    @arc_building_tolerance.setter
    def arc_building_tolerance(self, value : float):
        ...
    
    ...

