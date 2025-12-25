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

class IWindow(aspose.html.dom.events.IEventTarget):
    '''The window object represents a window containing a DOM document.'''
    
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
    
    def alert(self, message : str):
        '''Displays a modal alert with the given message, and waits for the user to dismiss it
        
        :param message: The message.'''
        ...
    
    def confirm(self, message : str) -> bool:
        '''Displays a modal OK/Cancel prompt with the given message, waits for the user to dismiss it, and returns true if the user clicks OK and false if the user clicks Cancel.
        
        :param message: The message.
        :returns: Returns true if the user clicks OK and false if the user clicks Cancel'''
        ...
    
    def prompt(self, message : str, default : str) -> str:
        '''Displays a modal text field prompt with the given message, waits for the user to dismiss it, and returns the value that the user entered. If the user cancels the prompt, then returns null instead. If the second argument is present, then the given value is used as a default.
        
        :param message: The message.
        :param default: The default.
        :returns: Returns the value that the user entered'''
        ...
    
    def btoa(self, data : str) -> str:
        '''Takes the input data, in the form of a Unicode string containing only characters in the range U+0000 to U+00FF,
        each representing a binary byte with values 0x00 to 0xFF respectively, and converts it to its base64 representation, which it returns.
        
        :param data: The Unicode string containing only characters in the range U+0000 to U+00FF.
        :returns: The base64 string.'''
        ...
    
    def atob(self, data : str) -> str:
        '''Takes the input data, in the form of a Unicode string containing base64-encoded binary data,
        decodes it, and returns a string consisting of characters in the range U+0000 to U+00FF,
        each representing a binary byte with values 0x00 to 0xFF respectively, corresponding to that binary data.
        
        :param data: The Unicode string containing base64-encoded binary data
        :returns: The string consisting of characters in the range U+0000 to U+00FF'''
        ...
    
    def match_media(self, query : str) -> aspose.html.window.MediaQueryList:
        '''Returns a new MediaQueryList object that can then be used to determine if the document matches the media query string,
        as well as to monitor the document to detect when it matches (or stops matching) that media query.
        See CSSOM View Module specification: :link:`https://www.w3.org/TR/cssom-view/#extensions-to-the-window-interface`
        
        :param query: The string containing a media query;
        see :link:`https://drafts.csswg.org/mediaqueries/` for details.
        :returns: MediaQueryList object'''
        ...
    
    def dispatch_event(self, event : aspose.html.dom.events.Event) -> bool:
        '''This method allows the dispatch of events into the implementations event model.
        
        :param event: Specifies the event type, behavior, and contextual information to be used in processing the event.
        :returns: The return value of :py:func:`aspose.html.dom.EventTarget.dispatch_event` indicates whether any of the listeners which handled the event called :py:func:`aspose.html.dom.events.Event.prevent_default`.
        If :py:func:`aspose.html.dom.events.Event.prevent_default` was called the value is false, else the value is true.'''
        ...
    
    def set_timeout(self, handler : any, timeout : int, args : List[any]) -> int:
        ...
    
    def clear_timeout(self, handle : int):
        ...
    
    def set_interval(self, handler : any, timeout : int, args : List[any]) -> int:
        ...
    
    def clear_interval(self, handle : int):
        ...
    
    @property
    def window(self) -> aspose.html.window.IWindow:
        '''Returns the Window object's browsing context's WindowProxy object.'''
        ...
    
    @property
    def self(self) -> aspose.html.window.IWindow:
        '''Returns the Window object's browsing context's WindowProxy object.'''
        ...
    
    @property
    def document(self) -> aspose.html.dom.Document:
        '''The document attribute must return the Window object's newest Document object.'''
        ...
    
    @property
    def name(self) -> str:
        '''The name attribute of the Window object must, on getting, return the current name of the browsing context, and, on setting, set the name of the browsing context to the new value.'''
        ...
    
    @name.setter
    def name(self, value : str):
        '''The name attribute of the Window object must, on getting, return the current name of the browsing context, and, on setting, set the name of the browsing context to the new value.'''
        ...
    
    @property
    def location(self) -> aspose.html.window.Location:
        '''The location attribute of the Window interface must return the Location object for that Window object's Document.'''
        ...
    
    @property
    def top(self) -> aspose.html.window.IWindow:
        '''The top IDL attribute on the Window object of a Document in a browsing context b must return the WindowProxy object of its top-level browsing context (which would be its own WindowProxy object if it was a top-level browsing context itself), if it has one, or its own WindowProxy object otherwise (e.g. if it was a detached nested browsing context).'''
        ...
    
    @property
    def opener(self) -> aspose.html.window.IWindow:
        '''The opener IDL attribute on the Window object, on getting, must return the WindowProxy object of the browsing context from which the current browsing context was created (its opener browsing context), if there is one, if it is still available, and if the current browsing context has not disowned its opener; otherwise, it must return null. On setting, if the new value is null then the current browsing context must disown its opener; if the new value is anything else then the user agent must call the [[DefineOwnProperty]] internal method of the Window object, passing the property name "opener" as the property key, and the Property Descriptor { [[Value]]: value, [[Writable]]: true, [[Enumerable]]: true, [[Configurable]]: true } as the property descriptor, where value is the new value.'''
        ...
    
    @property
    def parent(self) -> aspose.html.window.IWindow:
        '''The parent IDL attribute on the Window object of a Document in a browsing context b must return the WindowProxy object of the parent browsing context, if there is one (i.e. if b is a child browsing context), or the WindowProxy object of the browsing context b itself, otherwise (i.e. if it is a top-level browsing context or a detached nested browsing context).'''
        ...
    
    @property
    def frame_element(self) -> aspose.html.dom.Element:
        ...
    
    @property
    def local_storage(self) -> aspose.html.dom.IStorage:
        ...
    
    @property
    def default_view(self) -> aspose.html.dom.views.IAbstractView:
        ...
    
    ...

class IWindowEventHandlers:
    '''Represents interface that must be inherited by window object'''
    
    ...

class IWindowTimers:
    '''Allows authors to schedule timer-based callbacks.'''
    
    def set_timeout(self, handler : any, timeout : int, args : List[any]) -> int:
        '''Schedules a timeout to run handler after timeout milliseconds. Any arguments are passed straight through to the handler.
        
        :param handler: The handler.
        :param timeout: The timeout.
        :param args: The arguments.
        :returns: The handle'''
        ...
    
    def clear_timeout(self, handle : int):
        '''Cancels the timeout set with setTimeout() identified by handle.
        
        :param handle: The handle.'''
        ...
    
    def set_interval(self, handler : any, timeout : int, args : List[any]) -> int:
        '''Schedules a timeout to run handler every timeout milliseconds. Any arguments are passed straight through to the handler.
        
        :param handler: The handler.
        :param timeout: The timeout.
        :param args: The arguments.
        :returns: The handle'''
        ...
    
    def clear_interval(self, handle : int):
        '''Cancels the timeout set with setInterval() identified by handle
        
        :param handle: The handle.'''
        ...
    
    ...

class Location(aspose.html.dom.DOMObject):
    '''Location objects provide a representation of the address of the active document of their Document's browsing context, and allow the current entry of the browsing context's session history to be changed, by adding or replacing entries in the history object.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    def assign(self, url : str):
        '''Navigates to the given page.
        
        :param url: The URL to navigate.'''
        ...
    
    def replace(self, url : str):
        '''Removes the current page from the session history and navigates to the given page.
        
        :param url: The string URL to navigate.'''
        ...
    
    def reload(self):
        '''Reloads the current page.'''
        ...
    
    @property
    def href(self) -> str:
        '''Returns the Location object's URL.
        Can be set, to navigate to the given URL.'''
        ...
    
    @href.setter
    def href(self, value : str):
        '''Returns the Location object's URL.
        Can be set, to navigate to the given URL.'''
        ...
    
    @property
    def origin(self) -> str:
        '''Returns the Location object's URL's origin.'''
        ...
    
    @property
    def protocol(self) -> str:
        '''Returns the Location object's URL's scheme.
        Can be set, to navigate to the same URL with a changed scheme.'''
        ...
    
    @protocol.setter
    def protocol(self, value : str):
        '''Returns the Location object's URL's scheme.
        Can be set, to navigate to the same URL with a changed scheme.'''
        ...
    
    @property
    def host(self) -> str:
        '''Returns the Location object's URL's host and port (if different from the default port for the scheme).
        Can be set, to navigate to the same URL with a changed host and port.'''
        ...
    
    @host.setter
    def host(self, value : str):
        '''Returns the Location object's URL's host and port (if different from the default port for the scheme).
        Can be set, to navigate to the same URL with a changed host and port.'''
        ...
    
    @property
    def hostname(self) -> str:
        '''Returns the Location object's URL's host.
        Can be set, to navigate to the same URL with a changed host.'''
        ...
    
    @hostname.setter
    def hostname(self, value : str):
        '''Returns the Location object's URL's host.
        Can be set, to navigate to the same URL with a changed host.'''
        ...
    
    @property
    def port(self) -> str:
        '''Returns the Location object's URL's port.
        Can be set, to navigate to the same URL with a changed port.'''
        ...
    
    @port.setter
    def port(self, value : str):
        '''Returns the Location object's URL's port.
        Can be set, to navigate to the same URL with a changed port.'''
        ...
    
    @property
    def pathname(self) -> str:
        '''Returns the Location object's URL's path.
        Can be set, to navigate to the same URL with a changed path.'''
        ...
    
    @pathname.setter
    def pathname(self, value : str):
        '''Returns the Location object's URL's path.
        Can be set, to navigate to the same URL with a changed path.'''
        ...
    
    @property
    def search(self) -> str:
        '''Returns the Location object's URL's query (includes leading "?" if non-empty).
        Can be set, to navigate to the same URL with a changed query(ignores leading "?").'''
        ...
    
    @search.setter
    def search(self, value : str):
        '''Returns the Location object's URL's query (includes leading "?" if non-empty).
        Can be set, to navigate to the same URL with a changed query(ignores leading "?").'''
        ...
    
    @property
    def hash(self) -> str:
        '''Returns the Location object's URL's fragment (includes leading "#" if non-empty).
        Can be set, to navigate to the same URL with a changed fragment(ignores leading "#").'''
        ...
    
    @hash.setter
    def hash(self, value : str):
        '''Returns the Location object's URL's fragment (includes leading "#" if non-empty).
        Can be set, to navigate to the same URL with a changed fragment(ignores leading "#").'''
        ...
    
    ...

class MediaQueryList(aspose.html.dom.EventTarget):
    '''A MediaQueryList object stores information on a media query applied to a document,
    with support for both immediate and event-driven matching against the state of the document.
    See CSSOM View Module specification: :link:`https://www.w3.org/TR/cssom-view/#the-mediaquerylist-interface`'''
    
    @overload
    def add_event_listener(self, type : str, listener : aspose.html.dom.events.IEventListener):
        '''Sets up a function that will be called whenever the specified event is delivered to the target.
        
        It works by adding a function, or an object that implements :py:class:`aspose.html.dom.events.IEventListener`,
        to the list of event listeners for the specified event type on the :py:class:`aspose.html.dom.EventTarget` on which it's called.
        If the function or object, is already in the list of event listeners for this target, they are not added a second time.
        
        :param type: The event type for which the user is registering
        :param listener: Takes an interface implemented by the user which contains the methods to be called when the event occurs.'''
        ...
    
    @overload
    def add_event_listener(self, type : str, listener : aspose.html.dom.events.IEventListener, use_capture : bool):
        '''Sets up a function that will be called whenever the specified event is delivered to the target.
        
        It works by adding a function, or an object that implements :py:class:`aspose.html.dom.events.IEventListener`,
        to the list of event listeners for the specified event type on the :py:class:`aspose.html.dom.EventTarget` on which it's called.
        If the function or object, is already in the list of event listeners for this target, they are not added a second time.
        
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
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    def dispatch_event(self, event : aspose.html.dom.events.Event) -> bool:
        '''Dispatches an Event at the specified :py:class:`aspose.html.dom.events.IEventTarget`, (synchronously) invoking
        the affected EventListeners in the appropriate order.
        The normal event processing rules (including the capturing and optional bubbling phase) also apply to events
        dispatched manually with :py:func:`aspose.html.dom.events.IEventTarget.dispatch_event`.
        
        :param event: Specifies the event type, behavior, and contextual information to be used in processing the event.
        :returns: The return value of :py:func:`aspose.html.dom.EventTarget.dispatch_event` indicates whether any of the listeners which handled the event called :py:func:`aspose.html.dom.events.Event.prevent_default`.
        If :py:func:`aspose.html.dom.events.Event.prevent_default` was called the value is false, else the value is true.'''
        ...
    
    def add_listener(self, listener : aspose.html.dom.events.IEventListener):
        '''Add MediaQueryList matches state change event listener.
        
        :param listener: Takes an interface implemented by the user which contains the methods to be called when the event occurs.'''
        ...
    
    def remove_listener(self, listener : aspose.html.dom.events.IEventListener):
        '''Remove MediaQueryList matches state change event listener.
        
        :param listener: The :py:class:`aspose.html.dom.events.IEventListener` parameter indicates the :py:class:`aspose.html.dom.events.IEventListener` to be removed.'''
        ...
    
    @property
    def document(self) -> aspose.html.dom.Document:
        '''Context object's associated document.'''
        ...
    
    @property
    def media(self) -> str:
        '''A string representing a serialized media query.'''
        ...
    
    @property
    def matches(self) -> bool:
        '''A boolean value that returns true if the document currently matches the media query list,
        or false if not.'''
        ...
    
    ...

