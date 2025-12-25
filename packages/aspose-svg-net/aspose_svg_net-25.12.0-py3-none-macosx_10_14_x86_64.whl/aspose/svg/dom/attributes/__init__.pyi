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

class DOMConstructorAttribute:
    '''Specifies a constructor that is defined by the W3C.'''
    
    ...

class DOMNameAttribute:
    '''Specifies the official DOM object name as it defined by the W3C.'''
    
    @property
    def name(self) -> str:
        '''Gets the DOM name.'''
        ...
    
    ...

class DOMNamedPropertyGetterAttribute:
    '''Specifies that the method will be used as named property getter.'''
    
    ...

class DOMNoInterfaceObjectAttribute:
    '''If the [NoInterfaceObject] extended attribute appears on an interface, it indicates that an interface object will not exist for the interface in the ECMAScript binding.'''
    
    ...

class DOMNullableAttribute:
    '''Specifies a DOM object can be assigned null value.'''
    
    ...

class DOMObjectAttribute:
    '''Specifies that object is marked with this attribute is defined by the W3C.'''
    
    ...

class DOMTreatNullAsAttribute:
    '''Indicates that null of the member value will be treated as specified value.'''
    
    @property
    def type(self) -> Type:
        '''Gets value the type.'''
        ...
    
    @type.setter
    def type(self, value : Type):
        '''Sets value the type.'''
        ...
    
    @property
    def value(self) -> any:
        '''Gets the value.'''
        ...
    
    @value.setter
    def value(self, value : any):
        '''Sets the value.'''
        ...
    
    ...

class Accessors:
    '''Represents the enumeration of member accessors that is defined by the W3C.'''
    
    @classmethod
    @property
    def NONE(cls) -> Accessors:
        '''Specifies that the property does not have any special meaning.'''
        ...
    
    @classmethod
    @property
    def GETTER(cls) -> Accessors:
        '''Specifies that the property or method should be handled as a getter.'''
        ...
    
    @classmethod
    @property
    def SETTER(cls) -> Accessors:
        '''Specifies that the property or method should be handled as a setter.'''
        ...
    
    @classmethod
    @property
    def DELETER(cls) -> Accessors:
        '''Specifies that the property or method should be handled by delete.'''
        ...
    
    ...

