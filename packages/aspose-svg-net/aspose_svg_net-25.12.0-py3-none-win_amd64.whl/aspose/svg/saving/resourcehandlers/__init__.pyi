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

class FileSystemResourceHandler(ResourceHandler):
    '''This class is an implementation of the :py:class:`aspose.svg.saving.resourcehandlers.ResourceHandler` class designed to save resources to the local file system.'''
    
    def handle_resource(self, resource : aspose.svg.saving.Resource, context : aspose.svg.saving.ResourceHandlingContext):
        '''This method is responsible for handling the resource. In it you can save the :py:class:`aspose.svg.saving.Resource` to the stream or embed it into the parent resource.
        
        :param resource: The :py:class:`aspose.svg.saving.Resource` which will be handled.
        :param context: Resource handling context.'''
        ...
    
    def handle_resource_reference(self, resource : aspose.svg.saving.Resource, context : aspose.svg.saving.ResourceHandlingContext) -> str:
        '''This method is responsible for handling the resource reference. In this method, you can set what the reference to the resource being handled will look like.
        
        :param resource: The :py:class:`aspose.svg.saving.Resource` which will be handled.
        :param context: Resource handling context.
        :returns: A string that will be written to the parent resource and which represents a reference to the resource that is currently being handled.'''
        ...
    
    ...

class ResourceHandler:
    '''This class is responsible for handling resources. It provides methods that allow you to control what will be done with the :py:class:`aspose.svg.saving.Resource`, as well as what reference will be written to the parent :py:class:`aspose.svg.saving.Resource`.'''
    
    def handle_resource(self, resource : aspose.svg.saving.Resource, context : aspose.svg.saving.ResourceHandlingContext):
        '''This method is responsible for handling the resource. In it you can save the :py:class:`aspose.svg.saving.Resource` to the stream or embed it into the parent resource.
        
        :param resource: The :py:class:`aspose.svg.saving.Resource` which will be handled.
        :param context: Resource handling context.'''
        ...
    
    def handle_resource_reference(self, resource : aspose.svg.saving.Resource, context : aspose.svg.saving.ResourceHandlingContext) -> str:
        '''This method is responsible for handling the resource reference. In this method, you can set what the reference to the resource being handled will look like.
        
        :param resource: The :py:class:`aspose.svg.saving.Resource` which will be handled.
        :param context: Resource handling context.
        :returns: A string that will be written to the parent resource and which represents a reference to the resource that is currently being handled.'''
        ...
    
    ...

