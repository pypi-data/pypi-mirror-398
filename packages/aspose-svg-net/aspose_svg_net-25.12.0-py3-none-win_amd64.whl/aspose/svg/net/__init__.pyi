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

class ByteArrayContent(Content):
    '''Represents content based on a byte array.'''
    
    def read_as_stream(self) -> io.RawIOBase:
        '''Serialize the HTTP content and return a stream that represents the content.
        
        :returns: Serialized stream that represents the content'''
        ...
    
    def read_as_byte_array(self) -> bytes:
        '''Serialize the HTTP content and return a byte array that represents the content.
        
        :returns: Serialized byte array that represents the content'''
        ...
    
    def read_as_string(self) -> str:
        '''Serialize the HTTP content and return a string that represents the content.
        
        :returns: Serialized string that represents the content'''
        ...
    
    @property
    def headers(self) -> aspose.svg.net.ContentHeaders:
        '''Gets the HTTP content headers.'''
        ...
    
    ...

class Content:
    '''Represents a base class for an HTTP entity body and content headers.'''
    
    def read_as_stream(self) -> io.RawIOBase:
        '''Serialize the HTTP content and return a stream that represents the content.
        
        :returns: Serialized stream that represents the content'''
        ...
    
    def read_as_byte_array(self) -> bytes:
        '''Serialize the HTTP content and return a byte array that represents the content.
        
        :returns: Serialized byte array that represents the content'''
        ...
    
    def read_as_string(self) -> str:
        '''Serialize the HTTP content and return a string that represents the content.
        
        :returns: Serialized string that represents the content'''
        ...
    
    @property
    def headers(self) -> aspose.svg.net.ContentHeaders:
        '''Gets the HTTP content headers.'''
        ...
    
    ...

class ContentHeaders:
    '''Contains the headers associated with a content.'''
    
    @property
    def content_type(self) -> aspose.svg.net.headers.ContentTypeHeaderValue:
        ...
    
    ...

class FormUrlEncodedContent(ByteArrayContent):
    '''A container for name/value tuples encoded using application/x-www-form-urlencoded MIME type.'''
    
    def read_as_stream(self) -> io.RawIOBase:
        '''Serialize the HTTP content and return a stream that represents the content.
        
        :returns: Serialized stream that represents the content'''
        ...
    
    def read_as_byte_array(self) -> bytes:
        '''Serialize the HTTP content and return a byte array that represents the content.
        
        :returns: Serialized byte array that represents the content'''
        ...
    
    def read_as_string(self) -> str:
        '''Serialize the HTTP content and return a string that represents the content.
        
        :returns: Serialized string that represents the content'''
        ...
    
    @property
    def headers(self) -> aspose.svg.net.ContentHeaders:
        '''Gets the HTTP content headers.'''
        ...
    
    ...

class HttpMethod:
    '''Represents utility class for retrieving and comparing standard HTTP methods.'''
    
    def equals(self, other : aspose.svg.net.HttpMethod) -> bool:
        '''Indicates whether the current object is equal to another object of the same type.
        
        :param other: An object to compare with this object.
        :returns: true if the current object is equal to the ``other`` parameter; otherwise, false.'''
        ...
    
    @classmethod
    @property
    def get(cls) -> aspose.svg.net.HttpMethod:
        '''Represents an HTTP GET protocol method.'''
        ...
    
    @classmethod
    @property
    def put(cls) -> aspose.svg.net.HttpMethod:
        '''Represents an HTTP PUT protocol method.'''
        ...
    
    @classmethod
    @property
    def post(cls) -> aspose.svg.net.HttpMethod:
        '''Represents an HTTP POST protocol method.'''
        ...
    
    @classmethod
    @property
    def delete(cls) -> aspose.svg.net.HttpMethod:
        '''Represents an HTTP DELETE protocol method.'''
        ...
    
    ...

class INetwork:
    '''Provides an interface for network services.'''
    
    def send(self, message : aspose.svg.net.RequestMessage) -> aspose.svg.net.ResponseMessage:
        '''Sends a :py:class:`aspose.svg.net.RequestMessage` message.
        
        :param message: The message to send.
        :returns: A :py:class:`aspose.svg.net.ResponseMessage` message'''
        ...
    
    ...

class INetworkOperationContext:
    '''Provides contextual information for the network services.'''
    
    @property
    def request(self) -> aspose.svg.net.RequestMessage:
        '''Gets the request message.'''
        ...
    
    @request.setter
    def request(self, value : aspose.svg.net.RequestMessage):
        '''Sets the request message.'''
        ...
    
    @property
    def response(self) -> aspose.svg.net.ResponseMessage:
        '''Gets the response message.'''
        ...
    
    @response.setter
    def response(self, value : aspose.svg.net.ResponseMessage):
        '''Sets the response message.'''
        ...
    
    ...

class MessageFilter:
    '''Represents abstract base class for different classes of filters used to query messages'''
    
    def match(self, context : aspose.svg.net.INetworkOperationContext) -> bool:
        '''When overridden in a derived class, tests whether a Context satisfies the filter criteria.
        
        :param context: The context.
        :returns: true if the Context object satisfies the filter criteria; otherwise, false.'''
        ...
    
    ...

class MessageHandler:
    '''Represents a base type for message handlers.'''
    
    def invoke(self, context : aspose.svg.net.INetworkOperationContext):
        '''When overridden in a derived class is used to implement the message handling.
        
        :param context: The context.'''
        ...
    
    @property
    def filters(self) -> Any:
        '''Gets the filters list that are corresponding to the specified handler type.'''
        ...
    
    ...

class MessageHandlerCollection:
    '''Represents collection of the :py:class:`aspose.svg.net.MessageHandler`.'''
    
    ...

class MultipartContent(Content):
    '''Represents a multipart/* content.'''
    
    def read_as_stream(self) -> io.RawIOBase:
        '''Serialize the HTTP content and return a stream that represents the content.
        
        :returns: Serialized stream that represents the content'''
        ...
    
    def read_as_byte_array(self) -> bytes:
        '''Serialize the HTTP content and return a byte array that represents the content.
        
        :returns: Serialized byte array that represents the content'''
        ...
    
    def read_as_string(self) -> str:
        '''Serialize the HTTP content and return a string that represents the content.
        
        :returns: Serialized string that represents the content'''
        ...
    
    def add(self, content : aspose.svg.net.Content):
        '''Add a new content to the :py:class:`aspose.svg.net.MultipartContent`
        
        :param content: Content to be added to the :py:class:`aspose.svg.net.MultipartContent`'''
        ...
    
    @property
    def headers(self) -> aspose.svg.net.ContentHeaders:
        '''Gets the HTTP content headers.'''
        ...
    
    ...

class MultipartFormDataContent(MultipartContent):
    '''Represent content for  multipart/form-data encoding algorithm'''
    
    @overload
    def add(self, content : aspose.svg.net.Content):
        '''Add the content to the :py:class:`aspose.svg.net.MultipartFormDataContent` class
        
        :param content: The content.'''
        ...
    
    @overload
    def add(self, content : aspose.svg.net.Content, name : str):
        '''Add the content to the :py:class:`aspose.svg.net.MultipartFormDataContent` class with field name parameter
        
        :param content: The content.
        :param name: The field name.'''
        ...
    
    @overload
    def add(self, content : aspose.svg.net.Content, name : str, file_name : str):
        '''Add the content to the :py:class:`aspose.svg.net.MultipartFormDataContent` class with field and file name parameter
        
        :param content: The content.
        :param name: The field name.
        :param file_name: The file name.'''
        ...
    
    def read_as_stream(self) -> io.RawIOBase:
        '''Serialize the HTTP content and return a stream that represents the content.
        
        :returns: Serialized stream that represents the content'''
        ...
    
    def read_as_byte_array(self) -> bytes:
        '''Serialize the HTTP content and return a byte array that represents the content.
        
        :returns: Serialized byte array that represents the content'''
        ...
    
    def read_as_string(self) -> str:
        '''Serialize the HTTP content and return a string that represents the content.
        
        :returns: Serialized string that represents the content'''
        ...
    
    @property
    def headers(self) -> aspose.svg.net.ContentHeaders:
        '''Gets the HTTP content headers.'''
        ...
    
    ...

class RequestHeaders:
    '''Contains protocol headers associated with a request.'''
    
    ...

class RequestMessage:
    '''Represents a request message.'''
    
    @property
    def method(self) -> aspose.svg.net.HttpMethod:
        '''Gets the :py:class:`aspose.svg.net.HttpMethod`.'''
        ...
    
    @method.setter
    def method(self, value : aspose.svg.net.HttpMethod):
        '''Sets the :py:class:`aspose.svg.net.HttpMethod`.'''
        ...
    
    @property
    def request_uri(self) -> aspose.svg.Url:
        ...
    
    @request_uri.setter
    def request_uri(self, value : aspose.svg.Url):
        ...
    
    @property
    def headers(self) -> aspose.svg.net.RequestHeaders:
        '''Gets the :py:class:`aspose.svg.net.RequestHeaders`.'''
        ...
    
    @property
    def content(self) -> aspose.svg.net.Content:
        '''Gets the request content.'''
        ...
    
    @content.setter
    def content(self, value : aspose.svg.net.Content):
        '''Sets the request content.'''
        ...
    
    @property
    def timeout(self) -> TimeSpan:
        '''The number of milliseconds to wait before the request times out. The default value is 100,000 milliseconds (100 seconds).'''
        ...
    
    @timeout.setter
    def timeout(self, value : TimeSpan):
        '''The number of milliseconds to wait before the request times out. The default value is 100,000 milliseconds (100 seconds).'''
        ...
    
    @property
    def pre_authenticate(self) -> bool:
        ...
    
    @pre_authenticate.setter
    def pre_authenticate(self, value : bool):
        ...
    
    ...

class ResponseHeaders:
    '''Contains protocol headers associated with a response.'''
    
    @property
    def content_type(self) -> aspose.svg.net.headers.ContentTypeHeaderValue:
        ...
    
    ...

class ResponseMessage:
    '''Represents a response message.'''
    
    @property
    def headers(self) -> aspose.svg.net.ResponseHeaders:
        '''Gets the headers.'''
        ...
    
    @property
    def content(self) -> aspose.svg.net.Content:
        '''Gets the response content.'''
        ...
    
    @content.setter
    def content(self, value : aspose.svg.net.Content):
        '''Sets the response content.'''
        ...
    
    @property
    def request(self) -> aspose.svg.net.RequestMessage:
        '''Gets the associated request.'''
        ...
    
    @request.setter
    def request(self, value : aspose.svg.net.RequestMessage):
        '''Sets the associated request.'''
        ...
    
    @property
    def is_success(self) -> bool:
        ...
    
    @property
    def response_uri(self) -> aspose.svg.Url:
        ...
    
    @response_uri.setter
    def response_uri(self, value : aspose.svg.Url):
        ...
    
    ...

class StreamContent(Content):
    '''Represents content based on a stream.'''
    
    def read_as_stream(self) -> io.RawIOBase:
        '''Serialize the HTTP content and return a stream that represents the content.
        
        :returns: Serialized stream that represents the content'''
        ...
    
    def read_as_byte_array(self) -> bytes:
        '''Serialize the HTTP content and return a byte array that represents the content.
        
        :returns: Serialized byte array that represents the content'''
        ...
    
    def read_as_string(self) -> str:
        '''Serialize the HTTP content and return a string that represents the content.
        
        :returns: Serialized string that represents the content'''
        ...
    
    @property
    def headers(self) -> aspose.svg.net.ContentHeaders:
        '''Gets the HTTP content headers.'''
        ...
    
    ...

class StringContent(ByteArrayContent):
    '''Represents content based on a string.'''
    
    def read_as_stream(self) -> io.RawIOBase:
        '''Serialize the HTTP content and return a stream that represents the content.
        
        :returns: Serialized stream that represents the content'''
        ...
    
    def read_as_byte_array(self) -> bytes:
        '''Serialize the HTTP content and return a byte array that represents the content.
        
        :returns: Serialized byte array that represents the content'''
        ...
    
    def read_as_string(self) -> str:
        '''Serialize the HTTP content and return a string that represents the content.
        
        :returns: Serialized string that represents the content'''
        ...
    
    @property
    def headers(self) -> aspose.svg.net.ContentHeaders:
        '''Gets the HTTP content headers.'''
        ...
    
    ...

class UrlResolver:
    '''Represents utility class for resolving absolute URL by a Uniform Resource Identifier (URI).'''
    
    def resolve(self, base_uri : str, relative_uri : str) -> aspose.svg.Url:
        '''Resolves the absolute URI from the base and relative URIs.
        
        :param base_uri: The base URI.
        :param relative_uri: The relative URI.
        :returns: The absolute URI'''
        ...
    
    ...

