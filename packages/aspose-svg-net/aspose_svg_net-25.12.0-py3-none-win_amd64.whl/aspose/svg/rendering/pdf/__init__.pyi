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

class PdfDevice(aspose.svg.rendering.Device):
    '''Represents rendering to a pdf document.'''
    
    def save_graphic_context(self):
        ...
    
    def restore_graphic_context(self):
        ...
    
    def begin_document(self, document : aspose.svg.dom.Document):
        ...
    
    def end_document(self):
        ...
    
    def begin_page(self, size : aspose.pydrawing.SizeF):
        ...
    
    def end_page(self):
        ...
    
    def flush(self):
        ...
    
    def begin_element(self, element : aspose.svg.dom.Element, rect : aspose.pydrawing.RectangleF) -> bool:
        ...
    
    def end_element(self, element : aspose.svg.dom.Element):
        ...
    
    def close_path(self):
        ...
    
    def move_to(self, pt : aspose.pydrawing.PointF):
        ...
    
    def line_to(self, pt : aspose.pydrawing.PointF):
        ...
    
    def add_rect(self, rect : aspose.pydrawing.RectangleF):
        ...
    
    def cubic_bezier_to(self, pt1 : aspose.pydrawing.PointF, pt2 : aspose.pydrawing.PointF, pt3 : aspose.pydrawing.PointF):
        ...
    
    def stroke(self):
        ...
    
    def fill(self, rule : aspose.svg.drawing.FillRule):
        ...
    
    def clip(self, rule : aspose.svg.drawing.FillRule):
        ...
    
    def stroke_and_fill(self, rule : aspose.svg.drawing.FillRule):
        ...
    
    def fill_text(self, text : str, pt : aspose.pydrawing.PointF):
        ...
    
    def stroke_text(self, text : str, pt : aspose.pydrawing.PointF):
        ...
    
    def draw_image(self, data : bytes, image_format : aspose.svg.drawing.WebImageFormat, rect : aspose.pydrawing.RectangleF):
        ...
    
    @property
    def options(self) -> aspose.svg.rendering.pdf.PdfRenderingOptions:
        ...
    
    @property
    def graphic_context(self) -> PdfDevice.PdfGraphicContext:
        ...
    
    ...

class PdfDocumentInfo:
    '''Represents the information about the PDF document.'''
    
    @property
    def title(self) -> str:
        '''The document's title.'''
        ...
    
    @title.setter
    def title(self, value : str):
        '''The document's title.'''
        ...
    
    @property
    def author(self) -> str:
        '''The name of the person who created the document.'''
        ...
    
    @author.setter
    def author(self, value : str):
        '''The name of the person who created the document.'''
        ...
    
    @property
    def subject(self) -> str:
        '''The subject of the document.'''
        ...
    
    @subject.setter
    def subject(self, value : str):
        '''The subject of the document.'''
        ...
    
    @property
    def keywords(self) -> str:
        '''Keywords associated with the document.'''
        ...
    
    @keywords.setter
    def keywords(self, value : str):
        '''Keywords associated with the document.'''
        ...
    
    @property
    def creator(self) -> str:
        '''The name of the product that created the original document.'''
        ...
    
    @creator.setter
    def creator(self, value : str):
        '''The name of the product that created the original document.'''
        ...
    
    @property
    def producer(self) -> str:
        '''The name of the product that converted the document.'''
        ...
    
    @producer.setter
    def producer(self, value : str):
        '''The name of the product that converted the document.'''
        ...
    
    @property
    def creation_date(self) -> DateTime:
        ...
    
    @creation_date.setter
    def creation_date(self, value : DateTime):
        ...
    
    @property
    def modification_date(self) -> DateTime:
        ...
    
    @modification_date.setter
    def modification_date(self, value : DateTime):
        ...
    
    ...

class PdfRenderingOptions(aspose.svg.rendering.RenderingOptions):
    '''Represents rendering options for :py:class:`aspose.svg.rendering.pdf.PdfDevice`.'''
    
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

class FormFieldBehaviour:
    '''This enumeration is used to specify the behavior of form fields in the output PDF document.'''
    
    @classmethod
    @property
    def INTERACTIVE(cls) -> FormFieldBehaviour:
        '''The output PDF document will contain interactive form fields.'''
        ...
    
    @classmethod
    @property
    def FLATTENED(cls) -> FormFieldBehaviour:
        '''The output PDF document will contain flattened form fields.'''
        ...
    
    ...

