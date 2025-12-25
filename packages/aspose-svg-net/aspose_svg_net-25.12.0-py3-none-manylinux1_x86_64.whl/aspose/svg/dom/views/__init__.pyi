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

class IAbstractView:
    '''A base interface that all views shall derive from.'''
    
    @property
    def document(self) -> aspose.svg.dom.views.IDocumentView:
        '''The source DocumentView of which this is an AbstractView.'''
        ...
    
    ...

class IDocumentView(IAbstractView):
    '''The DocumentView interface is implemented by Document objects in DOM implementations supporting DOM Views. It provides an attribute to retrieve the default view of a document.'''
    
    @property
    def default_view(self) -> aspose.svg.dom.views.IAbstractView:
        ...
    
    @property
    def document(self) -> aspose.svg.dom.views.IDocumentView:
        '''The source DocumentView of which this is an AbstractView.'''
        ...
    
    ...

