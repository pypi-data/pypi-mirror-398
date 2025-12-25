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

class ContentDispositionHeaderValue:
    '''Represent Content-Disposition header value.'''
    
    @property
    def disposition_type(self) -> str:
        ...
    
    @disposition_type.setter
    def disposition_type(self, value : str):
        ...
    
    @property
    def parameters(self) -> List[aspose.svg.net.headers.NameValueHeaderValue]:
        '''Get collection of paremeters'''
        ...
    
    @property
    def name(self) -> str:
        '''The name for a content body part.'''
        ...
    
    @name.setter
    def name(self, value : str):
        '''The name for a content body part.'''
        ...
    
    @property
    def file_name(self) -> str:
        ...
    
    @file_name.setter
    def file_name(self, value : str):
        ...
    
    ...

class ContentTypeHeaderValue(NameValueHeaderValue):
    '''Represents a Content-Type header value.'''
    
    @property
    def name(self) -> str:
        '''Gets the parameter name.'''
        ...
    
    @property
    def value(self) -> str:
        '''Gets the parameter value.'''
        ...
    
    @value.setter
    def value(self, value : str):
        '''Sets the parameter value.'''
        ...
    
    @property
    def char_set(self) -> str:
        ...
    
    @char_set.setter
    def char_set(self, value : str):
        ...
    
    @property
    def media_type(self) -> aspose.svg.MimeType:
        ...
    
    @media_type.setter
    def media_type(self, value : aspose.svg.MimeType):
        ...
    
    ...

class NameValueHeaderValue:
    '''Represents a name/value pair that describe a header value.'''
    
    @property
    def name(self) -> str:
        '''Gets the parameter name.'''
        ...
    
    @property
    def value(self) -> str:
        '''Gets the parameter value.'''
        ...
    
    @value.setter
    def value(self, value : str):
        '''Sets the parameter value.'''
        ...
    
    ...

