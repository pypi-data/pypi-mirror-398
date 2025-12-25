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

class SVGZoomEvent(aspose.html.dom.events.Event):
    '''The zoom event occurs when the user initiates an action which causes the current view of the SVG document fragment to be rescaled. Event handlers are only recognized on ‘svg’ elements.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    def init_event(self, type : str, bubbles : bool, cancelable : bool):
        '''The :py:func:`aspose.html.dom.events.Event.init_event` method is used to initialize the value of an :py:class:`aspose.html.dom.events.Event` created through the
        :py:class:`aspose.html.dom.events.IDocumentEvent` interface.
        
        :param type: The event type.
        :param bubbles: if set to ``true`` [bubbles].
        :param cancelable: if set to ``true`` [cancelable].'''
        ...
    
    def prevent_default(self):
        '''If an event is cancelable, the :py:func:`aspose.html.dom.events.Event.prevent_default` method is used to signify that the event is to be canceled,
        meaning any default action normally taken by the implementation as a result of the event will not occur.'''
        ...
    
    def stop_propagation(self):
        '''The :py:func:`aspose.html.dom.events.Event.stop_propagation` method is used prevent further propagation of an event during event flow.'''
        ...
    
    def stop_immediate_propagation(self):
        '''Invoking this method prevents event from reaching any event listeners registered after the current one and when dispatched in a tree also prevents event from reaching any other objects.'''
        ...
    
    @property
    def bubbles(self) -> bool:
        '''Used to indicate whether or not an event is a bubbling event. If the event can bubble the value is true, else the value is false.'''
        ...
    
    @property
    def cancelable(self) -> bool:
        '''Used to indicate whether or not an event can have its default action prevented. If the default action can be prevented the value is true, else the value is false.'''
        ...
    
    @property
    def current_target(self) -> aspose.html.dom.EventTarget:
        ...
    
    @property
    def event_phase(self) -> int:
        ...
    
    @property
    def target(self) -> aspose.html.dom.EventTarget:
        '''Used to indicate the :py:class:`aspose.html.dom.events.IEventTarget` to which the event was originally dispatched.'''
        ...
    
    @property
    def time_stamp(self) -> int:
        ...
    
    @property
    def type(self) -> str:
        '''The name of the event (case-insensitive). The name must be an XML name.'''
        ...
    
    @property
    def default_prevented(self) -> bool:
        ...
    
    @property
    def is_trusted(self) -> bool:
        ...
    
    @classmethod
    @property
    def NONE_PHASE(cls) -> int:
        ...
    
    @classmethod
    @property
    def CAPTURING_PHASE(cls) -> int:
        ...
    
    @classmethod
    @property
    def AT_TARGET_PHASE(cls) -> int:
        ...
    
    @classmethod
    @property
    def BUBBLING_PHASE(cls) -> int:
        ...
    
    @property
    def zoom_rect_screen(self) -> aspose.html.dom.svg.datatypes.SVGRect:
        ...
    
    @property
    def previous_scale(self) -> float:
        ...
    
    @property
    def previous_translate(self) -> aspose.html.dom.svg.datatypes.SVGPoint:
        ...
    
    @property
    def new_scale(self) -> float:
        ...
    
    @property
    def new_translate(self) -> aspose.html.dom.svg.datatypes.SVGPoint:
        ...
    
    ...

class TimeEvent(aspose.html.dom.events.Event):
    '''The TimeEvent interface provides specific contextual information associated with Time events.The different types of events that can occur are: beginEvent, endEvent and repeatEvent.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    def init_event(self, type : str, bubbles : bool, cancelable : bool):
        '''The :py:func:`aspose.html.dom.events.Event.init_event` method is used to initialize the value of an :py:class:`aspose.html.dom.events.Event` created through the
        :py:class:`aspose.html.dom.events.IDocumentEvent` interface.
        
        :param type: The event type.
        :param bubbles: if set to ``true`` [bubbles].
        :param cancelable: if set to ``true`` [cancelable].'''
        ...
    
    def prevent_default(self):
        '''If an event is cancelable, the :py:func:`aspose.html.dom.events.Event.prevent_default` method is used to signify that the event is to be canceled,
        meaning any default action normally taken by the implementation as a result of the event will not occur.'''
        ...
    
    def stop_propagation(self):
        '''The :py:func:`aspose.html.dom.events.Event.stop_propagation` method is used prevent further propagation of an event during event flow.'''
        ...
    
    def stop_immediate_propagation(self):
        '''Invoking this method prevents event from reaching any event listeners registered after the current one and when dispatched in a tree also prevents event from reaching any other objects.'''
        ...
    
    def init_time_event(self, type_arg : str, view_arg : aspose.html.dom.views.IAbstractView, detail_arg : int):
        '''The initTimeEvent method is used to initialize the value of a TimeEvent created through the DocumentEvent interface. This method may only be called before the TimeEvent has been dispatched via the dispatchEvent method, though it may be called multiple times during that phase if necessary. If called multiple times, the final invocation takes precedence.
        
        :param type_arg: Specifies the event type.
        :param view_arg: Specifies the Event's AbstractView.
        :param detail_arg: Specifies the Event's detail.'''
        ...
    
    @property
    def bubbles(self) -> bool:
        '''Used to indicate whether or not an event is a bubbling event. If the event can bubble the value is true, else the value is false.'''
        ...
    
    @property
    def cancelable(self) -> bool:
        '''Used to indicate whether or not an event can have its default action prevented. If the default action can be prevented the value is true, else the value is false.'''
        ...
    
    @property
    def current_target(self) -> aspose.html.dom.EventTarget:
        ...
    
    @property
    def event_phase(self) -> int:
        ...
    
    @property
    def target(self) -> aspose.html.dom.EventTarget:
        '''Used to indicate the :py:class:`aspose.html.dom.events.IEventTarget` to which the event was originally dispatched.'''
        ...
    
    @property
    def time_stamp(self) -> int:
        ...
    
    @property
    def type(self) -> str:
        '''The name of the event (case-insensitive). The name must be an XML name.'''
        ...
    
    @property
    def default_prevented(self) -> bool:
        ...
    
    @property
    def is_trusted(self) -> bool:
        ...
    
    @classmethod
    @property
    def NONE_PHASE(cls) -> int:
        ...
    
    @classmethod
    @property
    def CAPTURING_PHASE(cls) -> int:
        ...
    
    @classmethod
    @property
    def AT_TARGET_PHASE(cls) -> int:
        ...
    
    @classmethod
    @property
    def BUBBLING_PHASE(cls) -> int:
        ...
    
    @property
    def view(self) -> aspose.html.dom.views.IAbstractView:
        '''The view attribute identifies the AbstractView [DOM2VIEWS] from which the event was generated.'''
        ...
    
    @property
    def detail(self) -> int:
        '''Specifies some detail information about the Event, depending on the type of the event. For this event type, indicates the repeat number for the animation.'''
        ...
    
    ...

