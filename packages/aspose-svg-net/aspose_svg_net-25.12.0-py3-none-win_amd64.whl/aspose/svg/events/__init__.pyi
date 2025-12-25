from typing import List, Optional, Dict, Iterable
import aspose.pycore
import aspose.pydrawing
import aspose.svg
import aspose.svg.builder
import aspose.svg.collections
import aspose.svg.converters
import aspose.svg.datatypes
import aspose.svg.diagnostics
import aspose.svg.dom
import aspose.svg.dom.attributes
import aspose.svg.dom.css
import aspose.svg.dom.events
import aspose.svg.dom.mutations
import aspose.svg.dom.traversal
import aspose.svg.dom.traversal.filters
import aspose.svg.dom.views
import aspose.svg.dom.xpath
import aspose.svg.drawing
import aspose.svg.events
import aspose.svg.filters
import aspose.svg.imagevectorization
import aspose.svg.io
import aspose.svg.net
import aspose.svg.net.headers
import aspose.svg.net.messagefilters
import aspose.svg.net.messagehandlers
import aspose.svg.paths
import aspose.svg.rendering
import aspose.svg.rendering.fonts
import aspose.svg.rendering.image
import aspose.svg.rendering.pdf
import aspose.svg.rendering.pdf.encryption
import aspose.svg.rendering.skia
import aspose.svg.rendering.xps
import aspose.svg.saving
import aspose.svg.saving.resourcehandlers
import aspose.svg.services
import aspose.svg.toolkit
import aspose.svg.toolkit.optimizers
import aspose.svg.window

class SVGZoomEvent(aspose.svg.dom.events.Event):
    '''The zoom event occurs when the user initiates an action which causes the current view of the SVG document fragment to be rescaled. Event handlers are only recognized on ‘svg’ elements.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    def init_event(self, type : str, bubbles : bool, cancelable : bool):
        '''The :py:func:`aspose.svg.dom.events.Event.init_event` method is used to initialize the value of an :py:class:`aspose.svg.dom.events.Event` created through the
        :py:class:`aspose.svg.dom.events.IDocumentEvent` interface.
        
        :param type: The event type.
        :param bubbles: if set to ``true`` [bubbles].
        :param cancelable: if set to ``true`` [cancelable].'''
        ...
    
    def prevent_default(self):
        '''If an event is cancelable, the :py:func:`aspose.svg.dom.events.Event.prevent_default` method is used to signify that the event is to be canceled,
        meaning any default action normally taken by the implementation as a result of the event will not occur.'''
        ...
    
    def stop_propagation(self):
        '''The :py:func:`aspose.svg.dom.events.Event.stop_propagation` method is used prevent further propagation of an event during event flow.'''
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
    def current_target(self) -> aspose.svg.dom.EventTarget:
        ...
    
    @property
    def event_phase(self) -> int:
        ...
    
    @property
    def target(self) -> aspose.svg.dom.EventTarget:
        '''Used to indicate the :py:class:`aspose.svg.dom.events.IEventTarget` to which the event was originally dispatched.'''
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
    def zoom_rect_screen(self) -> aspose.svg.datatypes.SVGRect:
        ...
    
    @property
    def previous_scale(self) -> float:
        ...
    
    @property
    def previous_translate(self) -> aspose.svg.datatypes.SVGPoint:
        ...
    
    @property
    def new_scale(self) -> float:
        ...
    
    @property
    def new_translate(self) -> aspose.svg.datatypes.SVGPoint:
        ...
    
    ...

class TimeEvent(aspose.svg.dom.events.Event):
    '''The TimeEvent interface provides specific contextual information associated with Time events.The different types of events that can occur are: beginEvent, endEvent and repeatEvent.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    def init_event(self, type : str, bubbles : bool, cancelable : bool):
        '''The :py:func:`aspose.svg.dom.events.Event.init_event` method is used to initialize the value of an :py:class:`aspose.svg.dom.events.Event` created through the
        :py:class:`aspose.svg.dom.events.IDocumentEvent` interface.
        
        :param type: The event type.
        :param bubbles: if set to ``true`` [bubbles].
        :param cancelable: if set to ``true`` [cancelable].'''
        ...
    
    def prevent_default(self):
        '''If an event is cancelable, the :py:func:`aspose.svg.dom.events.Event.prevent_default` method is used to signify that the event is to be canceled,
        meaning any default action normally taken by the implementation as a result of the event will not occur.'''
        ...
    
    def stop_propagation(self):
        '''The :py:func:`aspose.svg.dom.events.Event.stop_propagation` method is used prevent further propagation of an event during event flow.'''
        ...
    
    def stop_immediate_propagation(self):
        '''Invoking this method prevents event from reaching any event listeners registered after the current one and when dispatched in a tree also prevents event from reaching any other objects.'''
        ...
    
    def init_time_event(self, type_arg : str, view_arg : aspose.svg.dom.views.IAbstractView, detail_arg : int):
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
    def current_target(self) -> aspose.svg.dom.EventTarget:
        ...
    
    @property
    def event_phase(self) -> int:
        ...
    
    @property
    def target(self) -> aspose.svg.dom.EventTarget:
        '''Used to indicate the :py:class:`aspose.svg.dom.events.IEventTarget` to which the event was originally dispatched.'''
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
    def view(self) -> aspose.svg.dom.views.IAbstractView:
        '''The view attribute identifies the AbstractView [DOM2VIEWS] from which the event was generated.'''
        ...
    
    @property
    def detail(self) -> int:
        '''Specifies some detail information about the Event, depending on the type of the event. For this event type, indicates the repeat number for the animation.'''
        ...
    
    ...

