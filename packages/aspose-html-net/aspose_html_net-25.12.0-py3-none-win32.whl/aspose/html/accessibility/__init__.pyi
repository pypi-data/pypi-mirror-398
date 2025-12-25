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

class AccessibilityRules:
    '''Quick reference to Web Content Accessibility Guidelines (WCAG) 2 requirements (success criteria) and techniques.
    Contain a list of Principle.
    
    https://www.w3.org/WAI/WCAG21/quickref/'''
    
    def get_principle(self, code : str) -> aspose.html.accessibility.Principle:
        '''Get Principle by code from WCAG
        
        :param code: principle code from WCAG
        :returns: Principle object'''
        ...
    
    def get_principles(self) -> Iterable[aspose.html.accessibility.Principle]:
        '''Get list of all rules from quick reference
        
        :returns: list objects of Priniciple'''
        ...
    
    def get_rules(self, codes : List[str]) -> List[aspose.html.accessibility.IRule]:
        '''Get rules by codes from WCAG with type IRule
        
        :param codes: list of rules code from WCAG
        :returns: IList{IRule} object'''
        ...
    
    ...

class AccessibilityValidator:
    '''The validator class handles quick reference rules. Contains a Validate method to check accessibility.'''
    
    def validate(self, document : aspose.html.HTMLDocument) -> aspose.html.accessibility.results.ValidationResult:
        '''Checks all methods in the Rule List.
        
        :param document: HTMLDocument object for validation.
        :returns: result object of validation.'''
        ...
    
    ...

class Criterion(Rule):
    '''Verifiable success criteria are provided for each recommendation, so WCAG 2.0 can be applied in areas where compliance testing is required.
    
    https://www.w3.org/WAI/WCAG21/Understanding/understanding-techniques'''
    
    @property
    def code(self) -> str:
        '''Rule code from the quick reference WCAG
        
        https://www.w3.org/WAI/WCAG21/quickref/?versions=2.0'''
        ...
    
    @property
    def description(self) -> str:
        '''Description of Rule from the quick reference WCAG.
        
        https://www.w3.org/WAI/WCAG21/quickref/?versions=2.0'''
        ...
    
    @property
    def level(self) -> str:
        '''Compliance levels: A (lowest), AA and AAA (highest).'''
        ...
    
    @property
    def sufficient_techniques(self) -> List[aspose.html.accessibility.IRule]:
        ...
    
    @property
    def advisory_techniques(self) -> List[aspose.html.accessibility.IRule]:
        ...
    
    @property
    def failures(self) -> List[aspose.html.accessibility.IRule]:
        '''Failures are things that cause accessibility barriers and fail specific success criteria.'''
        ...
    
    ...

class Guideline(Rule):
    '''Guidelines - the next level after principles.
    There are not testable, but outline frameworks and general goals that help authors understand success criteria and better apply the techniques.
    
    Guidelines are a list of acceptance criteria with type RuleDirectory{Criterion}.'''
    
    def get_criterion(self, code : str) -> aspose.html.accessibility.Criterion:
        '''Get Criterion by code from WCAG
        
        :param code: criterion code
        :returns: Criterion object'''
        ...
    
    def get_criterions(self) -> List[aspose.html.accessibility.Criterion]:
        '''Get all the criteria contained in the Guideline
        
        :returns: list of Criterion'''
        ...
    
    @property
    def code(self) -> str:
        '''Rule code from the quick reference WCAG
        
        https://www.w3.org/WAI/WCAG21/quickref/?versions=2.0'''
        ...
    
    @property
    def description(self) -> str:
        '''Description of Rule from the quick reference WCAG.
        
        https://www.w3.org/WAI/WCAG21/quickref/?versions=2.0'''
        ...
    
    ...

class IError:
    '''The interface describes the error of the validation'''
    
    @property
    def error_message(self) -> str:
        ...
    
    @property
    def target(self) -> aspose.html.accessibility.Target:
        '''Return html or css object with error'''
        ...
    
    @property
    def error_type_name(self) -> str:
        ...
    
    @property
    def error_type(self) -> int:
        ...
    
    @property
    def success(self) -> bool:
        '''Returns result of the criterion.'''
        ...
    
    ...

class IRule:
    '''Interface describing the main properties of the rules.'''
    
    @property
    def code(self) -> str:
        '''Rule code from the quick reference WCAG.
        
        https://www.w3.org/WAI/WCAG21/quickref/?versions=2.0'''
        ...
    
    @property
    def description(self) -> str:
        '''Description of criterion from the quick reference WCAG.
        
        https://www.w3.org/WAI/WCAG21/quickref/?versions=2.0'''
        ...
    
    ...

class ITechniqueResult:
    '''Describes the result of the technique validation.'''
    
    @property
    def rule(self) -> aspose.html.accessibility.IRule:
        '''The rule that is checked'''
        ...
    
    @property
    def error(self) -> aspose.html.accessibility.IError:
        '''Error object that implemented interface IError'''
        ...
    
    @property
    def success(self) -> bool:
        '''Returns result of the criterion.'''
        ...
    
    ...

class Principle(Rule):
    '''Accessibility Principle - The highest levels that provide the foundation of web accessibility, contain a list of Guidelines with type RuleCollection{Guideline}.
    The object is not allowed to be created outside the assembly.
    
    https://www.w3.org/WAI/fundamentals/accessibility-principles/'''
    
    def get_guideline(self, code : str) -> aspose.html.accessibility.Guideline:
        '''Get by WCAG code for Guideline
        
        :param code: Guideline code
        :returns: Guideline object'''
        ...
    
    def get_guidelines(self) -> List[aspose.html.accessibility.Guideline]:
        '''Get all the Guidelines contained in the Principle
        
        :returns: list of Guidelines'''
        ...
    
    @property
    def code(self) -> str:
        '''Rule code from the quick reference WCAG
        
        https://www.w3.org/WAI/WCAG21/quickref/?versions=2.0'''
        ...
    
    @property
    def description(self) -> str:
        '''Description of Rule from the quick reference WCAG.
        
        https://www.w3.org/WAI/WCAG21/quickref/?versions=2.0'''
        ...
    
    ...

class Rule(IRule):
    '''An abstract class that defines the characteristics of a Rule and implements interface IRule'''
    
    @property
    def code(self) -> str:
        '''Rule code from the quick reference WCAG
        
        https://www.w3.org/WAI/WCAG21/quickref/?versions=2.0'''
        ...
    
    @property
    def description(self) -> str:
        '''Description of Rule from the quick reference WCAG.
        
        https://www.w3.org/WAI/WCAG21/quickref/?versions=2.0'''
        ...
    
    ...

class Target:
    '''Class contains item of html or css element where the error was found.'''
    
    @property
    def item(self) -> any:
        '''Returns Object of html or css element.'''
        ...
    
    @property
    def target_type(self) -> aspose.html.accessibility.TargetTypes:
        ...
    
    ...

class ValidationBuilder:
    '''The ValidationBuilder class provides concrete implementations of the configuration steps.
    Defines methods and settings for a class ValidationSettings.'''
    
    def all_levels(self) -> aspose.html.accessibility.ValidationBuilder:
        '''A method that sets all criteria levels. And indicates that the document will be checked according to the criteria of all three levels.
        
        :returns: set levels and init settings.'''
        ...
    
    def use_lowest_level(self) -> aspose.html.accessibility.ValidationBuilder:
        '''Use Lowest Level A of Criterion in Rules
        
        :returns: set levels and init settings.'''
        ...
    
    def use_middle_level(self) -> aspose.html.accessibility.ValidationBuilder:
        '''Use Middle Level AA of Criterion in Rules
        
        :returns: set levels and init in settings.'''
        ...
    
    def use_highest_level(self) -> aspose.html.accessibility.ValidationBuilder:
        '''Use Highest Level AAA of Criterion in Rules
        
        :returns: set levels and init in settings.'''
        ...
    
    def all_technologies(self) -> aspose.html.accessibility.ValidationBuilder:
        '''A method that sets all technologies to test criterion
        
        :returns: set technologies and init in settings.'''
        ...
    
    def use_html(self) -> aspose.html.accessibility.ValidationBuilder:
        '''A method that includes HTML technologies in a set of rules
        
        :returns: set technologies types and init in settings.'''
        ...
    
    def use_css(self) -> aspose.html.accessibility.ValidationBuilder:
        '''A method that includes CSS technologies in a set of rules
        
        :returns: set technologies types and init in settings.'''
        ...
    
    def use_script(self) -> aspose.html.accessibility.ValidationBuilder:
        '''A method that includes ClientSideScript technologies in a set of rules
        
        :returns: set technologies types and init in settings.'''
        ...
    
    def use_failures(self) -> aspose.html.accessibility.ValidationBuilder:
        '''A method that includes Failures in a set of rules
        
        :returns: set technologies types and init in settings.'''
        ...
    
    def use_general(self) -> aspose.html.accessibility.ValidationBuilder:
        '''A method that includes General technologies in a set of rules
        
        :returns: set technologies types and init in settings.'''
        ...
    
    def set_html_tags(self, tags : List[str]) -> aspose.html.accessibility.ValidationBuilder:
        '''List of html tags to check
        If the tags are not specified explicitly, then the tags array is empty and the check passes through all
        
        :param tags: list of html tag - where value is a string description of the tag
        :returns: set tags and init in settings.'''
        ...
    
    @classmethod
    @property
    def none(cls) -> aspose.html.accessibility.ValidationBuilder:
        '''None settings - none of the parameters are specified.'''
        ...
    
    @classmethod
    @property
    def default(cls) -> aspose.html.accessibility.ValidationBuilder:
        '''Default settings: only General technologies is used and for Lowest criterion level'''
        ...
    
    @classmethod
    @property
    def all(cls) -> aspose.html.accessibility.ValidationBuilder:
        '''Includes all levels and all technologies settings'''
        ...
    
    ...

class WebAccessibility:
    '''Object to Web Content Accessibility Guidelines (WCAG) 2 requirements (success criteria) and techniques.
    https://www.w3.org/WAI/WCAG21/quickref/'''
    
    @overload
    def create_validator(self, rule : aspose.html.accessibility.IRule) -> aspose.html.accessibility.AccessibilityValidator:
        '''An AccessibilityValidator instance is created for a specific rule, given the full parameters of the ValidationBuilder.All object.
        
        :param rule: object of rule that implemented IRule interface
        :returns: AccessibilityValidator object'''
        ...
    
    @overload
    def create_validator(self, rule : aspose.html.accessibility.IRule, builder : aspose.html.accessibility.ValidationBuilder) -> aspose.html.accessibility.AccessibilityValidator:
        '''Create AccessibilityValidator instance
        
        :param rule: object of rule that implemented IRule interface
        :param builder: object ValidationBuilder
        :returns: AccessibilityValidator object'''
        ...
    
    @overload
    def create_validator(self, builder : aspose.html.accessibility.ValidationBuilder) -> aspose.html.accessibility.AccessibilityValidator:
        '''Create AccessibilityValidator instance
        
        :param builder: object ValidationBuilder
        :returns: AccessibilityValidator object'''
        ...
    
    @overload
    def create_validator(self) -> aspose.html.accessibility.AccessibilityValidator:
        '''An AccessibilityValidator instance is created according to all the rules with a ValidationBuilder.All object.
        
        :returns: AccessibilityValidator object'''
        ...
    
    @overload
    def create_validator(self, rules : List[aspose.html.accessibility.IRule]) -> aspose.html.accessibility.AccessibilityValidator:
        ...
    
    @overload
    def create_validator(self, rules : List[aspose.html.accessibility.IRule], builder : aspose.html.accessibility.ValidationBuilder) -> aspose.html.accessibility.AccessibilityValidator:
        ...
    
    @property
    def rules(self) -> aspose.html.accessibility.AccessibilityRules:
        '''Return list of all rules'''
        ...
    
    ...

class TargetTypes:
    '''Enum of types of the resulting object from the html document containing the error..'''
    
    @classmethod
    @property
    def HTML_ELEMENT(cls) -> TargetTypes:
        '''The element containing the HTMLElement from document'''
        ...
    
    @classmethod
    @property
    def CSS_STYLE_RULE(cls) -> TargetTypes:
        '''The element containing the CSSStyleRule from document'''
        ...
    
    @classmethod
    @property
    def CSS_STYLE_SHEET(cls) -> TargetTypes:
        '''The element containing the CSSStyleSheet from document'''
        ...
    
    ...

