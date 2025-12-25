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

class ImageSaveOptions(aspose.svg.rendering.image.ImageRenderingOptions):
    '''Specific options data class.'''
    
    @property
    def css(self) -> aspose.svg.rendering.CssOptions:
        '''Gets a :py:class:`aspose.svg.rendering.CssOptions` object which is used for configuration of css properties processing.'''
        ...
    
    @property
    def page_setup(self) -> aspose.svg.rendering.PageSetup:
        ...
    
    @property
    def horizontal_resolution(self) -> aspose.svg.drawing.Resolution:
        ...
    
    @horizontal_resolution.setter
    def horizontal_resolution(self, value : aspose.svg.drawing.Resolution):
        ...
    
    @property
    def background_color(self) -> aspose.pydrawing.Color:
        ...
    
    @background_color.setter
    def background_color(self, value : aspose.pydrawing.Color):
        ...
    
    @property
    def vertical_resolution(self) -> aspose.svg.drawing.Resolution:
        ...
    
    @vertical_resolution.setter
    def vertical_resolution(self, value : aspose.svg.drawing.Resolution):
        ...
    
    @property
    def format(self) -> aspose.svg.rendering.image.ImageFormat:
        '''Sets or gets :py:class:`aspose.svg.rendering.image.ImageFormat`. By default this property is :py:attr:`aspose.svg.rendering.image.ImageFormat.PNG`.'''
        ...
    
    @format.setter
    def format(self, value : aspose.svg.rendering.image.ImageFormat):
        '''Sets or gets :py:class:`aspose.svg.rendering.image.ImageFormat`. By default this property is :py:attr:`aspose.svg.rendering.image.ImageFormat.PNG`.'''
        ...
    
    @property
    def compression(self) -> aspose.svg.rendering.image.Compression:
        '''Sets or gets Tagged Image File Format (TIFF) :py:class:`aspose.svg.rendering.image.Compression`. By default this property is :py:attr:`aspose.svg.rendering.image.Compression.LZW`.'''
        ...
    
    @compression.setter
    def compression(self, value : aspose.svg.rendering.image.Compression):
        '''Sets or gets Tagged Image File Format (TIFF) :py:class:`aspose.svg.rendering.image.Compression`. By default this property is :py:attr:`aspose.svg.rendering.image.Compression.LZW`.'''
        ...
    
    @property
    def text(self) -> aspose.svg.rendering.image.TextOptions:
        '''Gets a :py:class:`aspose.svg.rendering.image.TextOptions` object which is used for configuration of text rendering.'''
        ...
    
    @property
    def use_antialiasing(self) -> bool:
        ...
    
    @use_antialiasing.setter
    def use_antialiasing(self, value : bool):
        ...
    
    ...

class PdfSaveOptions(aspose.svg.rendering.pdf.PdfRenderingOptions):
    '''Specific options data class.'''
    
    @property
    def css(self) -> aspose.svg.rendering.CssOptions:
        '''Gets a :py:class:`aspose.svg.rendering.CssOptions` object which is used for configuration of css properties processing.'''
        ...
    
    @property
    def page_setup(self) -> aspose.svg.rendering.PageSetup:
        ...
    
    @property
    def horizontal_resolution(self) -> aspose.svg.drawing.Resolution:
        ...
    
    @horizontal_resolution.setter
    def horizontal_resolution(self, value : aspose.svg.drawing.Resolution):
        ...
    
    @property
    def background_color(self) -> aspose.pydrawing.Color:
        ...
    
    @background_color.setter
    def background_color(self, value : aspose.pydrawing.Color):
        ...
    
    @property
    def vertical_resolution(self) -> aspose.svg.drawing.Resolution:
        ...
    
    @vertical_resolution.setter
    def vertical_resolution(self, value : aspose.svg.drawing.Resolution):
        ...
    
    @property
    def document_info(self) -> aspose.svg.rendering.pdf.PdfDocumentInfo:
        ...
    
    @property
    def form_field_behaviour(self) -> aspose.svg.rendering.pdf.FormFieldBehaviour:
        ...
    
    @form_field_behaviour.setter
    def form_field_behaviour(self, value : aspose.svg.rendering.pdf.FormFieldBehaviour):
        ...
    
    @property
    def jpeg_quality(self) -> int:
        ...
    
    @jpeg_quality.setter
    def jpeg_quality(self, value : int):
        ...
    
    @property
    def encryption(self) -> aspose.svg.rendering.pdf.encryption.PdfEncryptionInfo:
        '''Gets a encryption details. If not set, then no encryption will be performed.'''
        ...
    
    @encryption.setter
    def encryption(self, value : aspose.svg.rendering.pdf.encryption.PdfEncryptionInfo):
        '''Sets a encryption details. If not set, then no encryption will be performed.'''
        ...
    
    @property
    def is_tagged_pdf(self) -> bool:
        ...
    
    @is_tagged_pdf.setter
    def is_tagged_pdf(self, value : bool):
        ...
    
    ...

class Resource:
    '''This class describes a resource and provides methods for processing it.'''
    
    def save(self, stream : io.RawIOBase, context : aspose.svg.saving.ResourceHandlingContext) -> aspose.svg.saving.Resource:
        '''Saves the resource to the provided stream.
        
        :param stream: The stream in which the resource will be saved.
        :param context: Resource handling context.
        :returns: This resource so that you can chain calls.'''
        ...
    
    def embed(self, context : aspose.svg.saving.ResourceHandlingContext) -> aspose.svg.saving.Resource:
        '''Embeds this resource within its parent by encoding it as Base64. The encoding result will be written to :py:attr:`aspose.svg.saving.Resource.output_url`.
        
        :param context: Resource handling context.
        :returns: This resource so that you can chain calls.'''
        ...
    
    def with_output_url(self, output_url : aspose.svg.Url) -> aspose.svg.saving.Resource:
        '''Specifies the new URL indicating where the resource will be located after processing.
        
        :param output_url: The new URL indicating where the resource will be located after processing.
        :returns: This resource so that you can chain calls.'''
        ...
    
    @property
    def status(self) -> aspose.svg.saving.ResourceStatus:
        '''Returns the current status of the resource.'''
        ...
    
    @property
    def mime_type(self) -> aspose.svg.MimeType:
        ...
    
    @property
    def original_url(self) -> aspose.svg.Url:
        ...
    
    @property
    def original_reference(self) -> str:
        ...
    
    @property
    def output_url(self) -> aspose.svg.Url:
        ...
    
    @output_url.setter
    def output_url(self, value : aspose.svg.Url):
        ...
    
    ...

class ResourceHandlingContext:
    '''This class contains information used when processing resources.'''
    
    @property
    def parent_resource(self) -> aspose.svg.saving.Resource:
        ...
    
    ...

class ResourceHandlingOptions:
    '''Represents resource handling options.'''
    
    @property
    def java_script(self) -> aspose.svg.saving.ResourceHandling:
        ...
    
    @java_script.setter
    def java_script(self, value : aspose.svg.saving.ResourceHandling):
        ...
    
    @property
    def default(self) -> aspose.svg.saving.ResourceHandling:
        '''Gets enum which represents default way of resources handling. Currently :py:attr:`aspose.svg.saving.ResourceHandling.SAVE`, :py:attr:`aspose.svg.saving.ResourceHandling.IGNORE` and :py:attr:`aspose.svg.saving.ResourceHandling.EMBED` values are supported. Default value is :py:attr:`aspose.svg.saving.ResourceHandling.SAVE`.'''
        ...
    
    @default.setter
    def default(self, value : aspose.svg.saving.ResourceHandling):
        '''Sets enum which represents default way of resources handling. Currently :py:attr:`aspose.svg.saving.ResourceHandling.SAVE`, :py:attr:`aspose.svg.saving.ResourceHandling.IGNORE` and :py:attr:`aspose.svg.saving.ResourceHandling.EMBED` values are supported. Default value is :py:attr:`aspose.svg.saving.ResourceHandling.SAVE`.'''
        ...
    
    @property
    def resource_url_restriction(self) -> aspose.svg.saving.UrlRestriction:
        ...
    
    @resource_url_restriction.setter
    def resource_url_restriction(self, value : aspose.svg.saving.UrlRestriction):
        ...
    
    @property
    def page_url_restriction(self) -> aspose.svg.saving.UrlRestriction:
        ...
    
    @page_url_restriction.setter
    def page_url_restriction(self, value : aspose.svg.saving.UrlRestriction):
        ...
    
    @property
    def max_handling_depth(self) -> int:
        ...
    
    @max_handling_depth.setter
    def max_handling_depth(self, value : int):
        ...
    
    ...

class SVGSaveOptions(SaveOptions):
    '''Represents SVG save options.'''
    
    @property
    def resource_handling_options(self) -> aspose.svg.saving.ResourceHandlingOptions:
        ...
    
    @property
    def vectorize_text(self) -> bool:
        ...
    
    @vectorize_text.setter
    def vectorize_text(self, value : bool):
        ...
    
    ...

class SVGZSaveOptions(SaveOptions):
    '''Represents SVGZ save options.'''
    
    @property
    def resource_handling_options(self) -> aspose.svg.saving.ResourceHandlingOptions:
        ...
    
    @property
    def vectorize_text(self) -> bool:
        ...
    
    @vectorize_text.setter
    def vectorize_text(self, value : bool):
        ...
    
    ...

class SaveOptions:
    '''This is an abstract base class for classes that allow the user to specify additional options when saving a document into a particular format.'''
    
    @property
    def resource_handling_options(self) -> aspose.svg.saving.ResourceHandlingOptions:
        ...
    
    ...

class XpsSaveOptions(aspose.svg.rendering.xps.XpsRenderingOptions):
    '''Specific options data class.'''
    
    @property
    def css(self) -> aspose.svg.rendering.CssOptions:
        '''Gets a :py:class:`aspose.svg.rendering.CssOptions` object which is used for configuration of css properties processing.'''
        ...
    
    @property
    def page_setup(self) -> aspose.svg.rendering.PageSetup:
        ...
    
    @property
    def horizontal_resolution(self) -> aspose.svg.drawing.Resolution:
        ...
    
    @horizontal_resolution.setter
    def horizontal_resolution(self, value : aspose.svg.drawing.Resolution):
        ...
    
    @property
    def background_color(self) -> aspose.pydrawing.Color:
        ...
    
    @background_color.setter
    def background_color(self, value : aspose.pydrawing.Color):
        ...
    
    @property
    def vertical_resolution(self) -> aspose.svg.drawing.Resolution:
        ...
    
    @vertical_resolution.setter
    def vertical_resolution(self, value : aspose.svg.drawing.Resolution):
        ...
    
    ...

class ResourceHandling:
    '''This enum represents resource handling options.'''
    
    @classmethod
    @property
    def SAVE(cls) -> ResourceHandling:
        '''Resource will be saved as file.'''
        ...
    
    @classmethod
    @property
    def EMBED(cls) -> ResourceHandling:
        '''Resource will be emdedded in to owner.'''
        ...
    
    @classmethod
    @property
    def DISCARD(cls) -> ResourceHandling:
        '''Resource will be discarded.'''
        ...
    
    @classmethod
    @property
    def IGNORE(cls) -> ResourceHandling:
        '''Resource will not be saved.'''
        ...
    
    ...

class ResourceStatus:
    '''Indicates the resource status.'''
    
    @classmethod
    @property
    def INITIAL(cls) -> ResourceStatus:
        '''Initial resource status.'''
        ...
    
    @classmethod
    @property
    def IGNORED(cls) -> ResourceStatus:
        '''Resource was ignored by filter.'''
        ...
    
    @classmethod
    @property
    def NOT_FOUND(cls) -> ResourceStatus:
        '''Resource was not found.'''
        ...
    
    @classmethod
    @property
    def SAVED(cls) -> ResourceStatus:
        '''Resource was saved.'''
        ...
    
    @classmethod
    @property
    def EMBEDDED(cls) -> ResourceStatus:
        '''Resource was embedded.'''
        ...
    
    ...

class SVGSaveFormat:
    '''Specifies format in which document is saved.'''
    
    @classmethod
    @property
    def SVG(cls) -> SVGSaveFormat:
        '''Document will be saved as SVG.'''
        ...
    
    @classmethod
    @property
    def SVGZ(cls) -> SVGSaveFormat:
        '''Document will be saved as SVGZ.'''
        ...
    
    ...

class UrlRestriction:
    '''This enum represents restriction applied to URLs of processed resources.'''
    
    @classmethod
    @property
    def ROOT_AND_SUB_FOLDERS(cls) -> UrlRestriction:
        '''Only resources located in the root and sub folders are processed.'''
        ...
    
    @classmethod
    @property
    def SAME_HOST(cls) -> UrlRestriction:
        '''Only resources located in the same host are processed.'''
        ...
    
    @classmethod
    @property
    def NONE(cls) -> UrlRestriction:
        '''All resources are processed.'''
        ...
    
    ...

