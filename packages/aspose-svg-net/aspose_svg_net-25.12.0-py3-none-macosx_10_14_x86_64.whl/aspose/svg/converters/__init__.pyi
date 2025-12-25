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

class Converter:
    '''Shared facade only for most often conversion scenarios.
    It provides a wide range of conversions to the popular formats, such as PDF, XPS, image formats, etc.
    More specific conversion (rendering, saving) user cases are presented by well known and documented low level API functions.'''
    
    @overload
    @staticmethod
    def convert_svg(source : aspose.svg.SVGDocumentoptions : aspose.svg.saving.XpsSaveOptions, output_path : str):
        '''Convert svg document to xps.Result is xps file.
        
        :param source: Conversion source.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.svg.Urloptions : aspose.svg.saving.XpsSaveOptions, output_path : str):
        '''Convert svg source to xps. Result is xps file.
        
        :param url: Source document URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.svg.Urlconfiguration : aspose.svg.Configuration, options : aspose.svg.saving.XpsSaveOptions, output_path : str):
        '''Convert svg source to xps. Result is xps file.
        
        :param url: Source document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : stroptions : aspose.svg.saving.XpsSaveOptions, output_path : str):
        '''Convert svg source to xps. Result is xps file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : strconfiguration : aspose.svg.Configuration, options : aspose.svg.saving.XpsSaveOptions, output_path : str):
        '''Convert svg source to xps. Result is xps file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, options : aspose.svg.saving.XpsSaveOptions, output_path : str):
        '''Convert svg source to xps. Result is xps file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, configuration : aspose.svg.Configuration, options : aspose.svg.saving.XpsSaveOptions, output_path : str):
        '''Convert svg source to xps. Result is xps file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(document : aspose.svg.SVGDocumentoptions : aspose.svg.saving.XpsSaveOptions, provider : aspose.svg.io.ICreateStreamProvider):
        '''Convert svg source to xps. Result is xps file.
        
        :param document: Conversion source.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.svg.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.svg.Urloptions : aspose.svg.saving.XpsSaveOptions, provider : aspose.svg.io.ICreateStreamProvider):
        '''Convert svg source to xps. Result is xps file.
        
        :param url: The document URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.svg.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.svg.Urlconfiguration : aspose.svg.Configuration, options : aspose.svg.saving.XpsSaveOptions, provider : aspose.svg.io.ICreateStreamProvider):
        '''Convert svg source to xps. Result is xps file.
        
        :param url: The document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.svg.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : stroptions : aspose.svg.saving.XpsSaveOptions, provider : aspose.svg.io.ICreateStreamProvider):
        '''Convert svg source to xps. Result is xps file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.svg.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : strconfiguration : aspose.svg.Configuration, options : aspose.svg.saving.XpsSaveOptions, provider : aspose.svg.io.ICreateStreamProvider):
        '''Convert svg source to xps. Result is xps file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.svg.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, options : aspose.svg.saving.XpsSaveOptions, provider : aspose.svg.io.ICreateStreamProvider):
        '''Convert svg source to xps. Result is xps file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.svg.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, configuration : aspose.svg.Configuration, options : aspose.svg.saving.XpsSaveOptions, provider : aspose.svg.io.ICreateStreamProvider):
        '''Convert svg source to xps. Result is xps file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.svg.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source : aspose.svg.SVGDocumentoptions : aspose.svg.saving.PdfSaveOptions, output_path : str):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param source: Conversion source.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.svg.Urloptions : aspose.svg.saving.PdfSaveOptions, output_path : str):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param url: The document URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.svg.Urlconfiguration : aspose.svg.Configuration, options : aspose.svg.saving.PdfSaveOptions, output_path : str):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param url: The document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : stroptions : aspose.svg.saving.PdfSaveOptions, output_path : str):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : strconfiguration : aspose.svg.Configuration, options : aspose.svg.saving.PdfSaveOptions, output_path : str):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, options : aspose.svg.saving.PdfSaveOptions, output_path : str):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, configuration : aspose.svg.Configuration, options : aspose.svg.saving.PdfSaveOptions, output_path : str):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(document : aspose.svg.SVGDocumentoptions : aspose.svg.saving.PdfSaveOptions, provider : aspose.svg.io.ICreateStreamProvider):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param document: Conversion source.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.svg.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.svg.Urloptions : aspose.svg.saving.PdfSaveOptions, provider : aspose.svg.io.ICreateStreamProvider):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param url: The document URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.svg.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.svg.Urlconfiguration : aspose.svg.Configuration, options : aspose.svg.saving.PdfSaveOptions, provider : aspose.svg.io.ICreateStreamProvider):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param url: The document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.svg.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : stroptions : aspose.svg.saving.PdfSaveOptions, provider : aspose.svg.io.ICreateStreamProvider):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.svg.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : strconfiguration : aspose.svg.Configuration, options : aspose.svg.saving.PdfSaveOptions, provider : aspose.svg.io.ICreateStreamProvider):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.svg.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, options : aspose.svg.saving.PdfSaveOptions, provider : aspose.svg.io.ICreateStreamProvider):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param content: Source document content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.svg.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, configuration : aspose.svg.Configuration, options : aspose.svg.saving.PdfSaveOptions, provider : aspose.svg.io.ICreateStreamProvider):
        '''Convert svg source to pdf. Result is pdf file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.svg.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source : aspose.svg.SVGDocumentoptions : aspose.svg.saving.ImageSaveOptions, output_path : str):
        '''Convert svg document to image. Result is image file.
        
        :param source: Conversion source.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.svg.Urloptions : aspose.svg.saving.ImageSaveOptions, output_path : str):
        '''Convert svg document to image. Result is image file.
        
        :param url: The document URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.svg.Urlconfiguration : aspose.svg.Configuration, options : aspose.svg.saving.ImageSaveOptions, output_path : str):
        '''Convert svg document to image. Result is image file.
        
        :param url: The document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : stroptions : aspose.svg.saving.ImageSaveOptions, output_path : str):
        '''Convert svg document to image. Result is image file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : strconfiguration : aspose.svg.Configuration, options : aspose.svg.saving.ImageSaveOptions, output_path : str):
        '''Convert svg document to image. Result is image file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, options : aspose.svg.saving.ImageSaveOptions, output_path : str):
        '''Convert svg document to image. Result is image file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, configuration : aspose.svg.Configuration, options : aspose.svg.saving.ImageSaveOptions, output_path : str):
        '''Convert svg document to image. Result is image file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param output_path: Output file path.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(document : aspose.svg.SVGDocumentoptions : aspose.svg.saving.ImageSaveOptions, provider : aspose.svg.io.ICreateStreamProvider):
        '''Convert svg source to image. Result is image file.
        
        :param document: Conversion source.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.svg.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.svg.Urloptions : aspose.svg.saving.ImageSaveOptions, provider : aspose.svg.io.ICreateStreamProvider):
        '''Convert svg source to image. Result is image file.
        
        :param url: The document URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.svg.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(url : aspose.svg.Urlconfiguration : aspose.svg.Configuration, options : aspose.svg.saving.ImageSaveOptions, provider : aspose.svg.io.ICreateStreamProvider):
        '''Convert svg source to image. Result is image file.
        
        :param url: The document URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.svg.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : stroptions : aspose.svg.saving.ImageSaveOptions, provider : aspose.svg.io.ICreateStreamProvider):
        '''Convert svg source to image. Result is image file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.svg.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(source_path : strconfiguration : aspose.svg.Configuration, options : aspose.svg.saving.ImageSaveOptions, provider : aspose.svg.io.ICreateStreamProvider):
        '''Convert svg source to image. Result is image file.
        
        :param source_path: Svg file source path. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.svg.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, options : aspose.svg.saving.ImageSaveOptions, provider : aspose.svg.io.ICreateStreamProvider):
        '''Convert svg source to image. Result is image file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.svg.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_svg(content : strbase_uri : str, configuration : aspose.svg.Configuration, options : aspose.svg.saving.ImageSaveOptions, provider : aspose.svg.io.ICreateStreamProvider):
        '''Convert svg source to image. Result is image file.
        
        :param content: Inline string svg content.
        :param base_uri: The base URI of the document. It will be combined with the current directory path to form an absolute URL.
        :param configuration: The environment configuration.
        :param options: Conversion options.
        :param provider: Implementation of the :py:class:`aspose.svg.io.ICreateStreamProvider` interface, which will be used to get an output stream.'''
        ...
    
    @overload
    @staticmethod
    def convert_image_to_svg(configuration : aspose.svg.imagevectorization.ImageVectorizerConfigurationimage_file : str, output_path : str):
        '''Converts a raster image located on disk to SVG format.
        
        :param configuration: The :py:class:`aspose.svg.imagevectorization.ImageVectorizerConfiguration` that controls tracing parameters.
        :param image_file: Path to the source image file.
        :param output_path: Destination path for the generated SVG.'''
        ...
    
    @overload
    @staticmethod
    def convert_image_to_svg(configuration : aspose.svg.imagevectorization.ImageVectorizerConfigurationimage_stream : io.RawIOBase, output_path : str):
        '''Converts a raster image provided as a :py:class:`io.RawIOBase` to SVG format.
        
        :param configuration: The :py:class:`aspose.svg.imagevectorization.ImageVectorizerConfiguration` that controls tracing parameters.
        :param image_stream: Readable stream that contains the source image.
        :param output_path: Destination path for the generated SVG.'''
        ...
    
    ...

