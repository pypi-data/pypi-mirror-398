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

class IDeviceInformationService:
    '''An interface that is described an environment in which :py:class:`aspose.svg.dom.Document` is presented to the user.'''
    
    @property
    def screen_size(self) -> aspose.svg.drawing.Size:
        ...
    
    @screen_size.setter
    def screen_size(self, value : aspose.svg.drawing.Size):
        ...
    
    @property
    def window_size(self) -> aspose.svg.drawing.Size:
        ...
    
    @window_size.setter
    def window_size(self, value : aspose.svg.drawing.Size):
        ...
    
    @property
    def horizontal_resolution(self) -> aspose.svg.drawing.Resolution:
        ...
    
    @horizontal_resolution.setter
    def horizontal_resolution(self, value : aspose.svg.drawing.Resolution):
        ...
    
    @property
    def vertical_resolution(self) -> aspose.svg.drawing.Resolution:
        ...
    
    @vertical_resolution.setter
    def vertical_resolution(self, value : aspose.svg.drawing.Resolution):
        ...
    
    ...

class INetworkService:
    '''Provides an interface for the network operations.'''
    
    @property
    def url_resolver(self) -> aspose.svg.net.UrlResolver:
        ...
    
    @url_resolver.setter
    def url_resolver(self, value : aspose.svg.net.UrlResolver):
        ...
    
    @property
    def message_handlers(self) -> aspose.svg.net.MessageHandlerCollection:
        ...
    
    ...

class IRuntimeService:
    '''This service is used to configure runtime related properties.'''
    
    @property
    def java_script_timeout(self) -> TimeSpan:
        ...
    
    @java_script_timeout.setter
    def java_script_timeout(self, value : TimeSpan):
        ...
    
    ...

class IUserAgentService:
    '''An interface that is described a user agent environment.'''
    
    @property
    def language(self) -> str:
        '''The :py:attr:`aspose.svg.services.IUserAgentService.language` specifies the primary language for the element's contents and for any of the element's attributes that contain text.
        Its value must be a valid BCP 47 (:link:`http://www.ietf.org/rfc/bcp/bcp47.txt`) language tag, or the empty string. Setting the attribute to the empty string indicates that the primary language is unknown.'''
        ...
    
    @language.setter
    def language(self, value : str):
        '''The :py:attr:`aspose.svg.services.IUserAgentService.language` specifies the primary language for the element's contents and for any of the element's attributes that contain text.
        Its value must be a valid BCP 47 (:link:`http://www.ietf.org/rfc/bcp/bcp47.txt`) language tag, or the empty string. Setting the attribute to the empty string indicates that the primary language is unknown.'''
        ...
    
    @property
    def user_style_sheet(self) -> str:
        ...
    
    @user_style_sheet.setter
    def user_style_sheet(self, value : str):
        ...
    
    @property
    def char_set(self) -> str:
        ...
    
    @char_set.setter
    def char_set(self, value : str):
        ...
    
    @property
    def css_engine_mode(self) -> aspose.svg.dom.css.CSSEngineMode:
        ...
    
    @css_engine_mode.setter
    def css_engine_mode(self, value : aspose.svg.dom.css.CSSEngineMode):
        ...
    
    @property
    def fonts_settings(self) -> aspose.svg.FontsSettings:
        ...
    
    @property
    def show_image_placeholders(self) -> bool:
        ...
    
    @show_image_placeholders.setter
    def show_image_placeholders(self, value : bool):
        ...
    
    ...

