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

class CustomEvent(Event):
    '''Events using the CustomEvent interface can be used to carry custom data.'''
    
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
    
    def init_custom_event(self, type : str, bubbles : bool, cancelable : bool, detail : any):
        '''/// The :py:func:`aspose.html.dom.events.Event.init_event` method is used to initialize the value of an :py:class:`aspose.html.dom.events.Event` created through the :py:class:`aspose.html.dom.events.IDocumentEvent` interface.
        
        :param type: The event type.
        :param bubbles: if set to ``true`` [bubbles].
        :param cancelable: if set to ``true`` [cancelable].
        :param detail: The custom data.'''
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
    def detail(self) -> any:
        '''Gets the custom data.'''
        ...
    
    ...

class DocumentLoadErrorEvent(ErrorEvent):
    '''The :py:class:`aspose.html.dom.events.DocumentLoadErrorEvent` occurres when the requested resource is not available.'''
    
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
    def message(self) -> str:
        '''The message attribute must return the value it was initialized to. When the object is created, this attribute must be initialized to the empty string. It represents the error message.'''
        ...
    
    @property
    def file_name(self) -> str:
        ...
    
    @property
    def line_no(self) -> int:
        ...
    
    @property
    def col_no(self) -> int:
        ...
    
    @property
    def error(self) -> any:
        '''The error attribute must return the value it was initialized to. When the object is created, this attribute must be initialized to null. Where appropriate, it is set to the object representing the error (e.g. the exception object in the case of an uncaught DOM exception).'''
        ...
    
    ...

class ErrorEvent(Event):
    '''The :py:class:`aspose.html.dom.events.ErrorEvent` provides contextual information about an errors that occurred during runtime.'''
    
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
    def message(self) -> str:
        '''The message attribute must return the value it was initialized to. When the object is created, this attribute must be initialized to the empty string. It represents the error message.'''
        ...
    
    @property
    def file_name(self) -> str:
        ...
    
    @property
    def line_no(self) -> int:
        ...
    
    @property
    def col_no(self) -> int:
        ...
    
    @property
    def error(self) -> any:
        '''The error attribute must return the value it was initialized to. When the object is created, this attribute must be initialized to null. Where appropriate, it is set to the object representing the error (e.g. the exception object in the case of an uncaught DOM exception).'''
        ...
    
    ...

class Event(aspose.html.dom.DOMObject):
    '''The :py:class:`aspose.html.dom.events.Event` is used to provide contextual information about an event to the handler processing the event.'''
    
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
    
    ...

class FocusEvent(UIEvent):
    '''The FocusEvent interface provides specific contextual information associated with Focus events.'''
    
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
    def view(self) -> aspose.html.window.IWindow:
        '''The view attribute identifies the Window from which the event was generated.
        The un-initialized value of this attribute MUST be null.'''
        ...
    
    @property
    def detail(self) -> int:
        '''Specifies some detail information about the Event, depending on the type of event.'''
        ...
    
    @property
    def related_target(self) -> aspose.html.dom.EventTarget:
        ...
    
    ...

class IDocumentEvent:
    '''The :py:class:`aspose.html.dom.events.IDocumentEvent` interface provides a mechanism by which the user can create an :py:class:`aspose.html.dom.events.Event` of a type supported by the implementation.'''
    
    def create_event(self, event_type : str) -> aspose.html.dom.events.Event:
        '''Creates an :py:class:`aspose.html.dom.events.Event` of a type supported by the implementation.
        
        :param event_type: The eventType parameter specifies the type of :py:class:`aspose.html.dom.events.Event` interface to be created.
        :returns: The newly created :py:class:`aspose.html.dom.events.Event`'''
        ...
    
    ...

class IEventListener:
    '''The :py:class:`aspose.html.dom.events.IEventListener` interface is the primary method for handling events.
    Users implement the :py:class:`aspose.html.dom.events.IEventListener` interface and register their listener on an :py:class:`aspose.html.dom.EventTarget` using the :py:func:`aspose.html.dom.EventTarget.add_event_listener` method.
    The users should also remove their :py:class:`aspose.html.dom.events.IEventListener` from its :py:class:`aspose.html.dom.EventTarget` after they have completed using the listener.'''
    
    def handle_event(self, event : aspose.html.dom.events.Event):
        '''This method is called whenever an event occurs of the type for which the :py:class:`aspose.html.dom.events.IEventListener` interface was registered.
        
        :param event: The :py:class:`aspose.html.dom.events.Event` contains contextual information about the event.
        It also contains the :py:func:`aspose.html.dom.events.Event.stop_propagation` and :py:func:`aspose.html.dom.events.Event.prevent_default` methods which are used in determining the event's flow and default action.'''
        ...
    
    ...

class IEventTarget:
    '''The :py:class:`aspose.html.dom.EventTarget` interface is implemented by all Nodes in an implementation which supports the DOM Event Model.
    Therefore, this interface can be obtained by using binding-specific casting methods on an instance of the Node interface.
    The interface allows registration and removal of Event Listeners on an :py:class:`aspose.html.dom.EventTarget` and dispatch of events to that :py:class:`aspose.html.dom.events.IEventTarget`.'''
    
    @overload
    def add_event_listener(self, type : str, listener : aspose.html.dom.events.IEventListener):
        '''This method allows the registration of event listeners on the event target.
        
        :param type: The event type for which the user is registering
        :param listener: Takes an interface implemented by the user which contains the methods to be called when the event occurs.'''
        ...
    
    @overload
    def add_event_listener(self, type : str, listener : aspose.html.dom.events.IEventListener, use_capture : bool):
        '''This method allows the registration of event listeners on the event target.
        
        :param type: The event type for which the user is registering
        :param listener: Takes an interface implemented by the user which contains the methods to be called when the event occurs.
        :param use_capture: If true, useCapture indicates that the user wishes to initiate capture.
        After initiating capture, all events of the specified type will be dispatched to the registered
        :py:class:`aspose.html.dom.events.IEventListener`
        before being dispatched to any Event Targets beneath them in the tree.
        Events which are bubbling upward through the tree will not trigger an :py:class:`aspose.html.dom.events.IEventListener` designated to use capture.'''
        ...
    
    @overload
    def remove_event_listener(self, type : str, listener : aspose.html.dom.events.IEventListener):
        '''This method allows the removal of event listeners from the event target.
        If an :py:class:`aspose.html.dom.events.IEventListener` is removed from an :py:class:`aspose.html.dom.EventTarget` while it is processing an event, it will not be triggered by the current actions.
        Event Listeners can never be invoked after being removed.
        
        :param type: Specifies the event type of the :py:class:`aspose.html.dom.events.IEventListener` being removed.
        :param listener: The :py:class:`aspose.html.dom.events.IEventListener` parameter indicates the :py:class:`aspose.html.dom.events.IEventListener` to be removed.'''
        ...
    
    @overload
    def remove_event_listener(self, type : str, listener : aspose.html.dom.events.IEventListener, use_capture : bool):
        '''This method allows the removal of event listeners from the event target.
        If an :py:class:`aspose.html.dom.events.IEventListener` is removed from an :py:class:`aspose.html.dom.EventTarget` while it is processing an event, it will not be triggered by the current actions.
        Event Listeners can never be invoked after being removed.
        
        :param type: Specifies the event type of the :py:class:`aspose.html.dom.events.IEventListener` being removed.
        :param listener: The :py:class:`aspose.html.dom.events.IEventListener` parameter indicates the :py:class:`aspose.html.dom.events.IEventListener` to be removed.
        :param use_capture: Specifies whether the EventListener being removed was registered as a capturing listener or not.
        If a listener was registered twice, one with capture and one without, each must be removed separately.
        Removal of a capturing listener does not affect a non-capturing version of the same listener, and vice versa.'''
        ...
    
    def dispatch_event(self, event : aspose.html.dom.events.Event) -> bool:
        '''This method allows the dispatch of events into the implementations event model.
        
        :param event: Specifies the event type, behavior, and contextual information to be used in processing the event.
        :returns: The return value of :py:func:`aspose.html.dom.EventTarget.dispatch_event` indicates whether any of the listeners which handled the event called :py:func:`aspose.html.dom.events.Event.prevent_default`.
        If :py:func:`aspose.html.dom.events.Event.prevent_default` was called the value is false, else the value is true.'''
        ...
    
    ...

class InputEvent(UIEvent):
    '''Input events are sent as notifications whenever the DOM is being updated.'''
    
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
    def view(self) -> aspose.html.window.IWindow:
        '''The view attribute identifies the Window from which the event was generated.
        The un-initialized value of this attribute MUST be null.'''
        ...
    
    @property
    def detail(self) -> int:
        '''Specifies some detail information about the Event, depending on the type of event.'''
        ...
    
    @property
    def data(self) -> str:
        '''The data holds the value of the characters generated by an input method. This MAY be a single Unicode character or a non-empty sequence of Unicode characters [Unicode]. Characters SHOULD be normalized as defined by the Unicode normalization form NFC, defined in [UAX15]. This attribute MAY contain the empty string.'''
        ...
    
    @property
    def is_composing(self) -> bool:
        ...
    
    ...

class KeyboardEvent(UIEvent):
    '''The KeyboardEvent interface provides specific contextual information associated with keyboard devices. Each keyboard event references a key using a value. Keyboard events are commonly directed at the element that has the focus.'''
    
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
    def view(self) -> aspose.html.window.IWindow:
        '''The view attribute identifies the Window from which the event was generated.
        The un-initialized value of this attribute MUST be null.'''
        ...
    
    @property
    def detail(self) -> int:
        '''Specifies some detail information about the Event, depending on the type of event.'''
        ...
    
    @property
    def key(self) -> str:
        '''The key holds the key value of the key pressed. If the value is has a printed representation, it MUST be a non-empty Unicode character string, conforming to the algorithm for determining the key value defined in this specification. If the value is a control key which has no printed representation, it MUST be one of the key values defined in the key values set, as determined by the algorithm for determining the key value. Implementations that are unable to identify a key MUST use the key value Unidentified.'''
        ...
    
    @property
    def code(self) -> str:
        '''The code holds a string that identifies the physical key being pressed. The value is not affected by the current keyboard layout or modifier state, so a particular key will always return the same value.'''
        ...
    
    @property
    def location(self) -> int:
        '''The location attribute contains an indication of the logical location of the key on the device.'''
        ...
    
    @property
    def ctrl_key(self) -> bool:
        ...
    
    @property
    def shift_key(self) -> bool:
        ...
    
    @property
    def alt_key(self) -> bool:
        ...
    
    @property
    def meta_key(self) -> bool:
        ...
    
    @property
    def repeat(self) -> bool:
        '''true if the key has been pressed in a sustained manner. Holding down a key MUST result in the repeating the events keydown, beforeinput, input in this	order, at a rate determined by the system configuration. For mobile devices which have long-key-press behavior, the first key event with a repeat attribute value of true MUST serve as an indication of a long-key-press. The length of time that the key MUST be pressed in order to begin repeating is configuration-dependent.'''
        ...
    
    @property
    def is_composing(self) -> bool:
        ...
    
    @classmethod
    @property
    def DOM_KEY_LOCATION_STANDARD(cls) -> int:
        '''The key activation MUST NOT be distinguished as the left or right version of the key, and (other than the NumLock key) did not originate from the numeric keypad (or did not originate with a virtual key corresponding to the numeric keypad).'''
        ...
    
    @classmethod
    @property
    def DOM_KEY_LOCATION_LEFT(cls) -> int:
        '''The key activated originated from the left key location (when there is more than one possible location for this key).'''
        ...
    
    @classmethod
    @property
    def DOM_KEY_LOCATION_RIGHT(cls) -> int:
        '''The key activation originated from the right key location (when there is more than one possible location for this key).'''
        ...
    
    @classmethod
    @property
    def DOM_KEY_LOCATION_NUMPAD(cls) -> int:
        '''The key activation originated on the numeric keypad or with a virtual key corresponding to the numeric keypad (when there is more than one possible location for this key). Note that the NumLock key should always be encoded with a location of DOM_KEY_LOCATION_STANDARD.'''
        ...
    
    ...

class MouseEvent(UIEvent):
    '''The MouseEvent interface provides specific contextual information associated with Mouse events.'''
    
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
    def view(self) -> aspose.html.window.IWindow:
        '''The view attribute identifies the Window from which the event was generated.
        The un-initialized value of this attribute MUST be null.'''
        ...
    
    @property
    def detail(self) -> int:
        '''Specifies some detail information about the Event, depending on the type of event.'''
        ...
    
    @property
    def screen_x(self) -> int:
        ...
    
    @property
    def screen_y(self) -> int:
        ...
    
    @property
    def client_x(self) -> int:
        ...
    
    @property
    def client_y(self) -> int:
        ...
    
    @property
    def ctrl_key(self) -> bool:
        ...
    
    @property
    def shift_key(self) -> bool:
        ...
    
    @property
    def alt_key(self) -> bool:
        ...
    
    @property
    def meta_key(self) -> bool:
        ...
    
    @property
    def button(self) -> int:
        '''During mouse events caused by the depression or release of a mouse button, button MUST be used to indicate which pointer device button changed state.'''
        ...
    
    @property
    def buttons(self) -> int:
        '''During any mouse events, buttons MUST be used to indicate which combination of mouse buttons are currently being pressed, expressed as a bitmask.'''
        ...
    
    @property
    def related_target(self) -> aspose.html.dom.EventTarget:
        ...
    
    ...

class UIEvent(Event):
    '''The UIEvent interface provides specific contextual information associated with User Interface events.'''
    
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
    def view(self) -> aspose.html.window.IWindow:
        '''The view attribute identifies the Window from which the event was generated.
        The un-initialized value of this attribute MUST be null.'''
        ...
    
    @property
    def detail(self) -> int:
        '''Specifies some detail information about the Event, depending on the type of event.'''
        ...
    
    ...

class WheelEvent(MouseEvent):
    '''The WheelEvent interface provides specific contextual information associated with wheel events. To create an instance of the WheelEvent interface, use the WheelEvent constructor, passing an optional WheelEventInit dictionary.'''
    
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
    def view(self) -> aspose.html.window.IWindow:
        '''The view attribute identifies the Window from which the event was generated.
        The un-initialized value of this attribute MUST be null.'''
        ...
    
    @property
    def detail(self) -> int:
        '''Specifies some detail information about the Event, depending on the type of event.'''
        ...
    
    @property
    def screen_x(self) -> int:
        ...
    
    @property
    def screen_y(self) -> int:
        ...
    
    @property
    def client_x(self) -> int:
        ...
    
    @property
    def client_y(self) -> int:
        ...
    
    @property
    def ctrl_key(self) -> bool:
        ...
    
    @property
    def shift_key(self) -> bool:
        ...
    
    @property
    def alt_key(self) -> bool:
        ...
    
    @property
    def meta_key(self) -> bool:
        ...
    
    @property
    def button(self) -> int:
        '''During mouse events caused by the depression or release of a mouse button, button MUST be used to indicate which pointer device button changed state.'''
        ...
    
    @property
    def buttons(self) -> int:
        '''During any mouse events, buttons MUST be used to indicate which combination of mouse buttons are currently being pressed, expressed as a bitmask.'''
        ...
    
    @property
    def related_target(self) -> aspose.html.dom.EventTarget:
        ...
    
    @property
    def delta_x(self) -> float:
        ...
    
    @property
    def delta_y(self) -> float:
        ...
    
    @property
    def delta_z(self) -> float:
        ...
    
    @property
    def delta_mode(self) -> int:
        ...
    
    @classmethod
    @property
    def DOM_DELTA_PIXEL(cls) -> int:
        '''The units of measurement for the delta MUST be pixels. This is the most typical case in most operating system and implementation configurations.'''
        ...
    
    @classmethod
    @property
    def DOM_DELTA_LINE(cls) -> int:
        '''The units of measurement for the delta MUST be individual lines of text. This is the case for many form controls.'''
        ...
    
    @classmethod
    @property
    def DOM_DELTA_PAGE(cls) -> int:
        '''The units of measurement for the delta MUST be pages, either defined as a single screen or as a demarcated page.'''
        ...
    
    ...

