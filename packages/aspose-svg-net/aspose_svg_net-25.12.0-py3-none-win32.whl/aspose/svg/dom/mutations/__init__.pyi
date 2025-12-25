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

class MutationObserver(aspose.svg.dom.DOMObject):
    '''A :py:class:`aspose.svg.dom.mutations.MutationObserver` object can be used to observe mutations to the tree of :py:class:`aspose.svg.dom.Node`.'''
    
    @overload
    def observe(self, target : aspose.svg.dom.Node):
        '''Instructs the user agent to observe a given target (a node) and report any mutations based on the criteria given by options (an object).
        The options argument allows for setting mutation observation options via object members.
        
        :param target: The target for observe.'''
        ...
    
    @overload
    def observe(self, target : aspose.svg.dom.Node, options : aspose.svg.dom.mutations.MutationObserverInit):
        '''Instructs the user agent to observe a given target (a node) and report any mutations based on the criteria given by options (an object).
        The options argument allows for setting mutation observation options via object members.
        
        :param target: The target for observe.
        :param options: The observer options.'''
        ...
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    def disconnect(self):
        '''Stops observer from observing any mutations. Until the observe() method is used again, observer’s callback will not be invoked.'''
        ...
    
    def take_records(self) -> List[aspose.svg.dom.mutations.MutationRecord]:
        '''The method returns a copy of the record queue and then empty the record queue.
        
        :returns: The copy of the record queue.'''
        ...
    
    ...

class MutationObserverInit:
    '''This class represents an options collection which is used to configure :py:class:`aspose.svg.dom.mutations.MutationObserver`.'''
    
    def clear(self):
        '''Removes all the elements from the :py:class:`aspose.svg.dom.mutations.MutationObserverInit` collection.'''
        ...
    
    def contains_key(self, key : str) -> bool:
        '''Determines whether the :py:class:`aspose.svg.dom.mutations.MutationObserverInit` collection contain a specified key.
        
        :param key: The key to check.
        :returns: True if the :py:class:`aspose.svg.dom.mutations.MutationObserverInit` contain a specified key; otherwise, false.'''
        ...
    
    def add(self, key : str, value : any):
        '''Adds the specified key and value to the :py:class:`aspose.svg.dom.mutations.MutationObserverInit` collection.
        
        :param key: The key of the element to add.
        :param value: The value of the element to add.'''
        ...
    
    def remove(self, key : str) -> bool:
        '''Removes the value associated with the specified key from the :py:class:`aspose.svg.dom.mutations.MutationObserverInit` collection.
        
        :param key: The key of the element to remove.
        :returns: True if the element is successfully found and removed; otherwise, false.'''
        ...
    
    def try_get_value(self, key : str, value : Any) -> bool:
        '''Gets the value associated with the specified key.
        
        :param key: The key of the value to get.
        :param value: When this method returns, contains the value associated with the specified key, if the key is found; otherwise null.
        :returns: True if the :py:class:`aspose.svg.dom.mutations.MutationObserverInit` contain a specified key; otherwise, false.'''
        ...
    
    @property
    def child_list(self) -> bool:
        ...
    
    @child_list.setter
    def child_list(self, value : bool):
        ...
    
    @property
    def attributes(self) -> bool:
        '''Set to true if mutations to target’s attributes are to be observed. Can be omitted if attributeOldValue and/or attributeFilter is specified.'''
        ...
    
    @attributes.setter
    def attributes(self, value : bool):
        '''Set to true if mutations to target’s attributes are to be observed. Can be omitted if attributeOldValue and/or attributeFilter is specified.'''
        ...
    
    @property
    def character_data(self) -> bool:
        ...
    
    @character_data.setter
    def character_data(self, value : bool):
        ...
    
    @property
    def subtree(self) -> bool:
        '''Set to true if mutations to not just target, but also target’s descendants are to be observed'''
        ...
    
    @subtree.setter
    def subtree(self, value : bool):
        '''Set to true if mutations to not just target, but also target’s descendants are to be observed'''
        ...
    
    @property
    def attribute_old_value(self) -> bool:
        ...
    
    @attribute_old_value.setter
    def attribute_old_value(self, value : bool):
        ...
    
    @property
    def character_data_old_value(self) -> bool:
        ...
    
    @character_data_old_value.setter
    def character_data_old_value(self, value : bool):
        ...
    
    @property
    def attribute_filter(self) -> List[str]:
        ...
    
    @attribute_filter.setter
    def attribute_filter(self, value : List[str]):
        ...
    
    @property
    def count(self) -> int:
        '''Gets the number of key/value pairs contained in the :py:class:`aspose.svg.dom.mutations.MutationObserverInit` collection.'''
        ...
    
    @property
    def is_read_only(self) -> bool:
        ...
    
    @property
    def keys(self) -> List[str]:
        '''Gets a collection containing the keys in the :py:class:`aspose.svg.dom.mutations.MutationObserverInit` collection.'''
        ...
    
    @property
    def values(self) -> List[any]:
        '''Gets a collection containing the values in the :py:class:`aspose.svg.dom.mutations.MutationObserverInit` collection.'''
        ...
    
    ...

class MutationRecord(aspose.svg.dom.DOMObject):
    '''A MutationRecord represents an individual DOM mutation. It is the object that is passed to :py:class:`aspose.svg.dom.mutations.MutationObserver`'s :py:class:`Aspose.Svg.Dom.Mutations.MutationCallback`.'''
    
    def get_platform_type(self) -> Type:
        '''This method is used to retrieve the ECMAScript object :py:class:`System.Type`.
        
        :returns: The ECMAScript object.'''
        ...
    
    @property
    def type(self) -> str:
        '''Returns "attributes" if it was an attribute mutation, "characterData" if it was a mutation to a CharacterData node and "childList" if it was a mutation to the tree of nodes.'''
        ...
    
    @property
    def target(self) -> aspose.svg.dom.Node:
        '''Returns the node the mutation affected, depending on the type. For "attributes", it is the element whose attribute changed. For "characterData", it is the CharacterData node. For "childList", it is the node whose children changed.'''
        ...
    
    @property
    def added_nodes(self) -> aspose.svg.collections.NodeList:
        ...
    
    @property
    def removed_nodes(self) -> aspose.svg.collections.NodeList:
        ...
    
    @property
    def previous_sibling(self) -> aspose.svg.dom.Node:
        ...
    
    @property
    def next_sibling(self) -> aspose.svg.dom.Node:
        ...
    
    @property
    def attribute_name(self) -> str:
        ...
    
    @property
    def attribute_namespace(self) -> str:
        ...
    
    @property
    def old_value(self) -> str:
        ...
    
    ...

