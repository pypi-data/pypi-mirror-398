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

class ButtonElement(FormElement):
    '''The ButtonElement represents a wrapper that is associated with the HTMLButtonElement.'''
    
    @property
    def element_type(self) -> aspose.html.forms.FormElementType:
        ...
    
    @property
    def name(self) -> str:
        '''Represent the name attribute of the Button element.'''
        ...
    
    @name.setter
    def name(self, value : str):
        '''Represent the name attribute of the Button element.'''
        ...
    
    @property
    def id(self) -> str:
        '''Represents the Id attribute of the Button element.'''
        ...
    
    @id.setter
    def id(self, value : str):
        '''Represents the Id attribute of the Button element.'''
        ...
    
    @property
    def value(self) -> str:
        '''Represents the string value of the button element that is directly mapped to the 'value' attribute.'''
        ...
    
    @value.setter
    def value(self, value : str):
        '''Represents the string value of the button element that is directly mapped to the 'value' attribute.'''
        ...
    
    @property
    def type(self) -> aspose.html.forms.ButtonType:
        '''Type of the form control.'''
        ...
    
    @type.setter
    def type(self, value : aspose.html.forms.ButtonType):
        '''Type of the form control.'''
        ...
    
    @property
    def html_element(self) -> aspose.html.HTMLButtonElement:
        ...
    
    ...

class DataListElement(FormElement):
    '''The DataListElement represents a wrapper that is associated with the HTMLDataListElement'''
    
    @property
    def element_type(self) -> aspose.html.forms.FormElementType:
        ...
    
    @property
    def name(self) -> str:
        '''Gets the name of the form element.'''
        ...
    
    @name.setter
    def name(self, value : str):
        '''Sets the name of the form element.'''
        ...
    
    @property
    def id(self) -> str:
        '''Gets the identifier of the form element.'''
        ...
    
    @id.setter
    def id(self, value : str):
        '''Sets the identifier of the form element.'''
        ...
    
    @property
    def value(self) -> str:
        '''The value of field'''
        ...
    
    @value.setter
    def value(self, value : str):
        '''The value of field'''
        ...
    
    @property
    def options(self) -> aspose.html.forms.OptionCollection:
        '''Returns a list of options'''
        ...
    
    @property
    def html_element(self) -> aspose.html.HTMLDataListElement:
        ...
    
    ...

class FormEditor:
    '''This class represents the editor over the :py:class:`aspose.html.HTMLFormElement` that creates a easier way for .net developers to edit the html forms.'''
    
    @overload
    @staticmethod
    def create(form : aspose.html.HTMLFormElement) -> aspose.html.forms.FormEditor:
        '''Creates a new :py:class:`aspose.html.forms.FormEditor` based on :py:class:`aspose.html.HTMLFormElement`.
        
        :param form: The html form element
        :returns: Return a new instance of the :py:class:`aspose.html.forms.FormEditor` class'''
        ...
    
    @overload
    @staticmethod
    def create(document : aspose.html.HTMLDocumentindex : int) -> aspose.html.forms.FormEditor:
        '''Creates a new :py:class:`aspose.html.forms.FormEditor` based on :py:class:`aspose.html.HTMLFormElement` selected from the :py:attr:`aspose.html.HTMLDocument.forms` collection by index.
        
        :param document: The document.
        :param index: The index inside the forms collection.
        :returns: Return a new instance of the :py:class:`aspose.html.forms.FormEditor` class'''
        ...
    
    @overload
    @staticmethod
    def create(document : aspose.html.HTMLDocumentid : str) -> aspose.html.forms.FormEditor:
        '''Creates a new :py:class:`aspose.html.forms.FormEditor` based on :py:class:`aspose.html.HTMLFormElement` selected from the document by id.
        
        :param document: The document.
        :param id: The identifier.
        :returns: Return a new instance of the :py:class:`aspose.html.forms.FormEditor` class'''
        ...
    
    @overload
    def add_input(self, name : str) -> aspose.html.forms.InputElement:
        '''Creates a new :py:class:`aspose.html.forms.InputElement` and adds it to the end of the form.
        
        :param name: Name of input element
        :returns: Returns a new created :py:class:`aspose.html.forms.InputElement`.'''
        ...
    
    @overload
    def add_input(self, name : str, type : aspose.html.forms.InputElementType) -> aspose.html.forms.InputElement:
        '''Creates a new :py:class:`aspose.html.forms.InputElement` and adds it to the end of the form.
        
        :param name: Name of input element
        :param type: Type of input element
        :returns: Returns a new created :py:class:`aspose.html.forms.InputElement`.'''
        ...
    
    @staticmethod
    def create_new(document : aspose.html.HTMLDocument) -> aspose.html.forms.FormEditor:
        '''Creates a new :py:class:`aspose.html.HTMLFormElement` and associated it with :py:class:`aspose.html.forms.FormEditor`. :py:class:`aspose.html.HTMLFormElement` is created in the detached from the document state; in order to attach it to the document, please select proper location and use :py:func:`aspose.html.dom.Node.append_child` method.
        
        :param document: The :py:class:`aspose.html.HTMLDocument`.
        :returns: Return a new instance of the :py:class:`aspose.html.forms.FormEditor` class'''
        ...
    
    @property
    def form(self) -> aspose.html.HTMLFormElement:
        '''The original :py:class:`aspose.html.HTMLFormElement` that is associated with current instance of :py:class:`aspose.html.forms.FormEditor`.'''
        ...
    
    @property
    def count(self) -> int:
        '''The number of form controls in the form.'''
        ...
    
    @property
    def method(self) -> aspose.html.net.HttpMethod:
        '''HTTP method [`IETF RFC 2616 <http://www.ietf.org/rfc/rfc2616.txt>`] used to submit form. See the method attribute definition in HTML 4.01.'''
        ...
    
    @method.setter
    def method(self, value : aspose.html.net.HttpMethod):
        '''HTTP method [`IETF RFC 2616 <http://www.ietf.org/rfc/rfc2616.txt>`] used to submit form. See the method attribute definition in HTML 4.01.'''
        ...
    
    @property
    def action(self) -> str:
        '''Server-side form handler. See the action attribute definition in HTML 4.01.'''
        ...
    
    @action.setter
    def action(self, value : str):
        '''Server-side form handler. See the action attribute definition in HTML 4.01.'''
        ...
    
    def __getitem__(self, key : int) -> aspose.html.forms.FormElement:
        '''Returns the element by specified index.'''
        ...
    
    ...

class FormElement:
    '''Represents base class for form elements.'''
    
    @property
    def element_type(self) -> aspose.html.forms.FormElementType:
        ...
    
    @property
    def name(self) -> str:
        '''Gets the name of the form element.'''
        ...
    
    @name.setter
    def name(self, value : str):
        '''Sets the name of the form element.'''
        ...
    
    @property
    def id(self) -> str:
        '''Gets the identifier of the form element.'''
        ...
    
    @id.setter
    def id(self, value : str):
        '''Sets the identifier of the form element.'''
        ...
    
    @property
    def value(self) -> str:
        '''The value of field'''
        ...
    
    @value.setter
    def value(self, value : str):
        '''The value of field'''
        ...
    
    ...

class FormSubmitter:
    '''This class allows to prepare specified :py:class:`aspose.html.HTMLFormElement`, collects values from the form element, submit them to the remote server and receives a response.'''
    
    @overload
    def submit(self) -> aspose.html.forms.SubmissionResult:
        '''Submits the form data to the server.
        
        :returns: The result of the submission.'''
        ...
    
    @overload
    def submit(self, timeout : TimeSpan) -> aspose.html.forms.SubmissionResult:
        ...
    
    @property
    def method(self) -> aspose.html.net.HttpMethod:
        '''HTTP method [`IETF RFC 2616 <http://www.ietf.org/rfc/rfc2616.txt>`] used to submit form. See the method attribute definition in HTML 4.01.'''
        ...
    
    @method.setter
    def method(self, value : aspose.html.net.HttpMethod):
        '''HTTP method [`IETF RFC 2616 <http://www.ietf.org/rfc/rfc2616.txt>`] used to submit form. See the method attribute definition in HTML 4.01.'''
        ...
    
    @property
    def action(self) -> str:
        '''Server-side form handler. See the action attribute definition in HTML 4.01.'''
        ...
    
    @action.setter
    def action(self, value : str):
        '''Server-side form handler. See the action attribute definition in HTML 4.01.'''
        ...
    
    ...

class InputElement(FormElement):
    '''The InputElement represents a wrapper that is associated with the HTMLInputElement.'''
    
    def set_url_value(self, value : aspose.html.Url):
        '''This method is used to set :py:class:`aspose.html.Url` object as a value for input element. This method is valid if only the type of the input element is "url"
        
        :param value: The url value.'''
        ...
    
    def get_url_value(self) -> aspose.html.Url:
        '''This method is used to get the value as :py:class:`aspose.html.Url` object. This method is valid if only only type of the input element is "url"
        
        :returns: The field value as url.'''
        ...
    
    def set_email_value(self, value : str):
        '''This method is used to set email string as a value for input element. This method is valid if only the type of the input element is "email"
        
        :param value: The email.'''
        ...
    
    def get_email_value(self) -> str:
        '''This method is used to get the value as an email string object. This method is valid if only only type of the input element is "email"
        
        :returns: The email.'''
        ...
    
    def set_password_value(self, value : str):
        '''This method is used to set password string as a value for input element. This method is valid if only the type of the input element is "password"
        
        :param value: The password.'''
        ...
    
    def get_password_value(self) -> str:
        '''This method is used to get the value as a password string object. This method is valid if only only type of the input element is "password"
        
        :returns: The password.'''
        ...
    
    def set_date_value(self, value : DateTime):
        '''This method is used to set :py:class:`System.DateTime` object as a value for input element. This method is valid if only the type of the input element is "date"
        
        :param value: The date object.'''
        ...
    
    def get_date_value(self) -> DateTime:
        '''This method is used to get the value as a :py:class:`System.DateTime` object. This method is valid if only only type of the input element is "date"
        
        :returns: The date object.'''
        ...
    
    def set_month_value(self, value : DateTime):
        '''This method is used to set :py:class:`System.DateTime` object as a value for input element. This method is valid if only the type of the input element is "month"
        
        :param value: The date object.'''
        ...
    
    def get_month_value(self) -> DateTime:
        '''This method is used to get the value as a :py:class:`System.DateTime` object. This method is valid if only only type of the input element is "month"
        
        :returns: The date object.'''
        ...
    
    def set_week_value(self, value : str):
        '''This method is used to set 'week' string as a value for input element. This method is valid if only the type of the input element is "week"
        
        :param value: The week value.'''
        ...
    
    def get_week_value(self) -> str:
        '''This method is used to get the value as a week string. This method is valid if only only type of the input element is "week"
        
        :returns: The week value.'''
        ...
    
    def set_time_value(self, value : TimeSpan):
        ...
    
    def get_time_value(self) -> TimeSpan:
        '''This method is used to get the value as a :py:class:`System.TimeSpan` object. This method is valid if only only type of the input element is "time"
        
        :returns: The TimeSpan object.'''
        ...
    
    def set_date_time_local_value(self, value : DateTime):
        '''This method is used to set :py:class:`System.DateTime` object as a value for input element. This method is valid if only the type of the input element is "datetime-local"
        
        :param value: The date object.'''
        ...
    
    def get_date_time_local_value(self) -> DateTime:
        '''This method is used to get the value as a :py:class:`System.DateTime` object object. This method is valid if only only type of the input element is "datetime-local"
        
        :returns: The date object.'''
        ...
    
    def set_number_value(self, value : float):
        '''This method is used to set number as a value for input element. This method is valid if only the type of the input element is "number"
        
        :param value: The number object.'''
        ...
    
    def get_number_value(self) -> float:
        '''This method is used to get the value as a number. This method is valid if only only type of the input element is "number"
        
        :returns: The number object.'''
        ...
    
    def set_color_value(self, value : aspose.pydrawing.Color):
        '''This method is used to set color as a value for input element. This method is valid if only the type of the input element is "color"
        
        :param value: The color object.'''
        ...
    
    def get_color_value(self) -> aspose.pydrawing.Color:
        '''This method is used to get the value as a color. This method is valid if only only type of the input element is "color"
        
        :returns: The color object.'''
        ...
    
    def set_checkbox_value(self, value : bool):
        '''Sets the checkedness state for the input elemen with the Checkbox type.
        
        :param value: The checkedness.'''
        ...
    
    def get_checkbox_value(self) -> bool:
        '''Returns the checkedness state for the  input element with the Checkbox type .
        
        :returns: The checkedness state.'''
        ...
    
    def set_radio_value(self, value : bool):
        '''Sets the checkedness state for the input element with the radio type.
        
        :param value: The checkedness.'''
        ...
    
    def get_radio_value(self) -> bool:
        '''Returns the checkedness state for the  input element with the radio type.
        
        :returns: The checkedness.'''
        ...
    
    def add_file(self, uri : str):
        '''This method adds files to the :py:attr:`aspose.html.HTMLInputElement.files` collection which will be sent during the next web request.
        
        :param uri: The file path.'''
        ...
    
    @property
    def element_type(self) -> aspose.html.forms.FormElementType:
        ...
    
    @property
    def name(self) -> str:
        '''Represent the name attribute of the input element.'''
        ...
    
    @name.setter
    def name(self, value : str):
        '''Represent the name attribute of the input element.'''
        ...
    
    @property
    def id(self) -> str:
        '''Represents the Id attribute of the input element.'''
        ...
    
    @id.setter
    def id(self, value : str):
        '''Represents the Id attribute of the input element.'''
        ...
    
    @property
    def value(self) -> str:
        '''Represents the string value of the input element that is directly mapped to the 'value' attribute.'''
        ...
    
    @value.setter
    def value(self, value : str):
        '''Represents the string value of the input element that is directly mapped to the 'value' attribute.'''
        ...
    
    @property
    def list(self) -> aspose.html.forms.DataListElement:
        '''Represents a list of options'''
        ...
    
    @property
    def type(self) -> aspose.html.forms.InputElementType:
        '''Type of the form control.'''
        ...
    
    @type.setter
    def type(self, value : aspose.html.forms.InputElementType):
        '''Type of the form control.'''
        ...
    
    @property
    def html_element(self) -> aspose.html.HTMLInputElement:
        ...
    
    ...

class OptionCollection:
    '''The OptionElements represents a wrapper that is associated with the IHTMLOptionsCollection'''
    
    def add(self) -> aspose.html.forms.OptionElement:
        '''Add new option.
        
        :returns: Return created OptionElement.'''
        ...
    
    def remove(self, option : aspose.html.forms.OptionElement):
        '''Remove the option from list.
        
        :param option: The OptionElement.'''
        ...
    
    @property
    def count(self) -> int:
        '''The number of Option in the list.'''
        ...
    
    def __getitem__(self, key : int) -> aspose.html.forms.OptionElement:
        '''Gets the :py:class:`aspose.html.forms.OptionElement` at the specified index.'''
        ...
    
    ...

class OptionElement(FormElement):
    '''The OptionElement represents a wrapper that is associated with the HTMLOptionElement'''
    
    @property
    def element_type(self) -> aspose.html.forms.FormElementType:
        ...
    
    @property
    def name(self) -> str:
        '''Gets the name of the form element.'''
        ...
    
    @name.setter
    def name(self, value : str):
        '''Sets the name of the form element.'''
        ...
    
    @property
    def id(self) -> str:
        '''Gets the identifier of the form element.'''
        ...
    
    @id.setter
    def id(self, value : str):
        '''Sets the identifier of the form element.'''
        ...
    
    @property
    def value(self) -> str:
        '''The current form control value. See the value attribute definition in HTML 4.01.'''
        ...
    
    @value.setter
    def value(self, value : str):
        '''The current form control value. See the value attribute definition in HTML 4.01.'''
        ...
    
    @property
    def disabled(self) -> bool:
        '''The control is unavailable in this context. See the disabled attribute definition in HTML 4.01.'''
        ...
    
    @disabled.setter
    def disabled(self, value : bool):
        '''The control is unavailable in this context. See the disabled attribute definition in HTML 4.01.'''
        ...
    
    @property
    def label(self) -> str:
        '''Option label for use in hierarchical menus. See the label attribute definition in HTML 4.01.'''
        ...
    
    @label.setter
    def label(self, value : str):
        '''Option label for use in hierarchical menus. See the label attribute definition in HTML 4.01.'''
        ...
    
    @property
    def selected(self) -> bool:
        '''Represents the current state of the corresponding form control, in an interactive user agent. Changing this attribute changes the state of the form control, but does not change the value of the HTML selected attribute of the element.'''
        ...
    
    @selected.setter
    def selected(self, value : bool):
        '''Represents the current state of the corresponding form control, in an interactive user agent. Changing this attribute changes the state of the form control, but does not change the value of the HTML selected attribute of the element.'''
        ...
    
    @property
    def text(self) -> str:
        '''This attribute represents the text content of this node and its descendants.'''
        ...
    
    @text.setter
    def text(self, value : str):
        '''This attribute represents the text content of this node and its descendants.'''
        ...
    
    @property
    def html_element(self) -> aspose.html.HTMLOptionElement:
        ...
    
    ...

class SelectElement(FormElement):
    '''The SelectElement represents a wrapper that is associated with the HTMLSelectElement'''
    
    @overload
    def select_items(self, indexes : List[int]):
        '''This methods allows to select multiple options by their indexes.
        
        :param indexes: An array of indexes for parameter selection.'''
        ...
    
    @overload
    def select_items(self, values : List[str]):
        '''This methods allows to select multiple options by their values.
        
        :param values: An array of values for parameter selection.'''
        ...
    
    @property
    def element_type(self) -> aspose.html.forms.FormElementType:
        ...
    
    @property
    def name(self) -> str:
        '''Represent the name attribute of the input element.'''
        ...
    
    @name.setter
    def name(self, value : str):
        '''Represent the name attribute of the input element.'''
        ...
    
    @property
    def id(self) -> str:
        '''Represents the Id attribute of the input element.'''
        ...
    
    @id.setter
    def id(self, value : str):
        '''Represents the Id attribute of the input element.'''
        ...
    
    @property
    def value(self) -> str:
        '''On getting, must return the value of the first option element in the list of options in tree order that has its selectedness set to true, if any.'''
        ...
    
    @value.setter
    def value(self, value : str):
        '''On getting, must return the value of the first option element in the list of options in tree order that has its selectedness set to true, if any.'''
        ...
    
    @property
    def type(self) -> str:
        '''The type of this form control. This is the string "select-multiple" when the multiple attribute is ``true`` and the string "select-one" when ``false``.'''
        ...
    
    @property
    def multiple(self) -> bool:
        '''If true, multiple ``OPTION`` elements may be selected in this ``SELECT``. See the multiple attribute definition in HTML 4.01.'''
        ...
    
    @multiple.setter
    def multiple(self, value : bool):
        '''If true, multiple ``OPTION`` elements may be selected in this ``SELECT``. See the multiple attribute definition in HTML 4.01.'''
        ...
    
    @property
    def selected_options(self) -> List[str]:
        ...
    
    @property
    def options(self) -> aspose.html.forms.OptionCollection:
        '''Returns a list of options'''
        ...
    
    @property
    def html_element(self) -> aspose.html.HTMLSelectElement:
        ...
    
    ...

class SubmissionResult:
    '''This class represents the result of the submitting form data to the server.'''
    
    def load_document(self) -> aspose.html.dom.Document:
        '''This method loads the new document based on response message.
        
        :returns: The HTML document created based response message.'''
        ...
    
    @property
    def response_message(self) -> aspose.html.net.ResponseMessage:
        ...
    
    @property
    def content(self) -> aspose.html.net.Content:
        '''Gets the content of the response message.'''
        ...
    
    @property
    def is_success(self) -> bool:
        ...
    
    ...

class TextAreaElement(FormElement):
    '''The TextAreaElement represents a wrapper that is associated with the HTMLTextAreaElement'''
    
    @property
    def element_type(self) -> aspose.html.forms.FormElementType:
        ...
    
    @property
    def name(self) -> str:
        '''Represent the name attribute of the input element.'''
        ...
    
    @name.setter
    def name(self, value : str):
        '''Represent the name attribute of the input element.'''
        ...
    
    @property
    def id(self) -> str:
        '''Gets the identifier of the form element.'''
        ...
    
    @id.setter
    def id(self, value : str):
        '''Sets the identifier of the form element.'''
        ...
    
    @property
    def value(self) -> str:
        '''Represents the string value of the input element that is directly mapped to the 'value' attribute.'''
        ...
    
    @value.setter
    def value(self, value : str):
        '''Represents the string value of the input element that is directly mapped to the 'value' attribute.'''
        ...
    
    @property
    def type(self) -> str:
        '''The type of this form control.'''
        ...
    
    @property
    def html_element(self) -> aspose.html.HTMLTextAreaElement:
        ...
    
    ...

class ButtonType:
    '''This enumeration represents states of the button.'''
    
    @classmethod
    @property
    def SUBMIT(cls) -> ButtonType:
        '''The 'submit' state of the button.'''
        ...
    
    @classmethod
    @property
    def RESET(cls) -> ButtonType:
        '''The 'reset' state of the button.'''
        ...
    
    @classmethod
    @property
    def BUTTON(cls) -> ButtonType:
        '''The default 'button' state.'''
        ...
    
    ...

class FormElementType:
    '''Represents an enumeration of the Form Elements types and their corresponding to the HTML Elements'''
    
    @classmethod
    @property
    def UNKNOWN(cls) -> FormElementType:
        '''Corresponding to any HTML Element that is not been converting to the any of implemented :py:class:`aspose.html.forms.FormElement`.'''
        ...
    
    @classmethod
    @property
    def INPUT(cls) -> FormElementType:
        '''Corresponding to the :py:class:`aspose.html.HTMLInputElement`.'''
        ...
    
    @classmethod
    @property
    def SELECT(cls) -> FormElementType:
        '''Corresponding to the :py:class:`aspose.html.HTMLSelectElement`.'''
        ...
    
    @classmethod
    @property
    def TEXT_AREA(cls) -> FormElementType:
        '''Corresponding to the :py:class:`aspose.html.HTMLTextAreaElement`.'''
        ...
    
    @classmethod
    @property
    def OPTION(cls) -> FormElementType:
        '''Corresponding to the :py:class:`aspose.html.HTMLOptionElement`.'''
        ...
    
    @classmethod
    @property
    def BUTTON(cls) -> FormElementType:
        '''Corresponding to the :py:class:`aspose.html.HTMLButtonElement`.'''
        ...
    
    @classmethod
    @property
    def DATA_LIST(cls) -> FormElementType:
        '''Corresponding to the :py:class:`aspose.html.HTMLDataListElement`.'''
        ...
    
    ...

class InputElementType:
    '''Represent states of the input field.'''
    
    @classmethod
    @property
    def HIDDEN(cls) -> InputElementType:
        '''A control that is not displayed.'''
        ...
    
    @classmethod
    @property
    def TEXT(cls) -> InputElementType:
        '''A control that is a text-field.'''
        ...
    
    @classmethod
    @property
    def SEARCH(cls) -> InputElementType:
        '''A control that is used for entering search strings.'''
        ...
    
    @classmethod
    @property
    def TELEPHONE(cls) -> InputElementType:
        '''A control for entering a telephone number.'''
        ...
    
    @classmethod
    @property
    def URL(cls) -> InputElementType:
        '''A field for entering a URL.'''
        ...
    
    @classmethod
    @property
    def EMAIL(cls) -> InputElementType:
        '''A field for entering an email.'''
        ...
    
    @classmethod
    @property
    def PASSWORD(cls) -> InputElementType:
        '''A field for entering a password.'''
        ...
    
    @classmethod
    @property
    def DATE(cls) -> InputElementType:
        '''A field for entering a date.'''
        ...
    
    @classmethod
    @property
    def MONTH(cls) -> InputElementType:
        '''A field for entering a month.'''
        ...
    
    @classmethod
    @property
    def WEEK(cls) -> InputElementType:
        '''A field for entering a week.'''
        ...
    
    @classmethod
    @property
    def TIME(cls) -> InputElementType:
        '''A field for entering a time.'''
        ...
    
    @classmethod
    @property
    def LOCAL_DATE_TIME(cls) -> InputElementType:
        '''A field for entering a local datetime.'''
        ...
    
    @classmethod
    @property
    def NUMBER(cls) -> InputElementType:
        '''A field for entering a number.'''
        ...
    
    @classmethod
    @property
    def RANGE(cls) -> InputElementType:
        '''A field for entering a number inside the range.'''
        ...
    
    @classmethod
    @property
    def COLOR(cls) -> InputElementType:
        '''A field for entering a color.'''
        ...
    
    @classmethod
    @property
    def CHECKBOX(cls) -> InputElementType:
        '''A field for entering a checkbox.'''
        ...
    
    @classmethod
    @property
    def RADIO(cls) -> InputElementType:
        '''A field that allowing a single value to select.'''
        ...
    
    @classmethod
    @property
    def FILE(cls) -> InputElementType:
        '''A field that allows to select and attach user files.'''
        ...
    
    @classmethod
    @property
    def SUBMIT(cls) -> InputElementType:
        '''A button for submitting the form result.'''
        ...
    
    @classmethod
    @property
    def IMAGE(cls) -> InputElementType:
        '''A graphical button for submitting the form result.'''
        ...
    
    @classmethod
    @property
    def RESET(cls) -> InputElementType:
        '''A button for resetting the form data.'''
        ...
    
    @classmethod
    @property
    def BUTTON(cls) -> InputElementType:
        '''A push button.'''
        ...
    
    ...

