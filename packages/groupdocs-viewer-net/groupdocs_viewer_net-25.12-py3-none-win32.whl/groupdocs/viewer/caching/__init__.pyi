from typing import List, Optional, Dict, Iterable, Any, overload
import io
import collections.abc
from collections.abc import Sequence
from datetime import datetime
from aspose.pyreflection import Type
import aspose.pycore
import aspose.pydrawing
from uuid import UUID
import groupdocs.viewer
import groupdocs.viewer.caching
import groupdocs.viewer.drawing
import groupdocs.viewer.exceptions
import groupdocs.viewer.fonts
import groupdocs.viewer.interfaces
import groupdocs.viewer.logging
import groupdocs.viewer.options
import groupdocs.viewer.results

class CacheKeys:
    '''Provides methods to retrieve unique identifier for the cache entry.'''
    
    @staticmethod
    def get_attachments_key() -> str:
        '''Returns unique identifier for the cache entry that represents collection of :py:class:`groupdocs.viewer.results.Attachment` objects.
        
        :returns: Unique identifier for the cache entry that represents collection of :py:class:`groupdocs.viewer.results.Attachment` objects.'''
        raise NotImplementedError()
    
    @staticmethod
    def get_attachment_key(attachment_id : str) -> str:
        '''Returns unique identifier for the cache entry that represents attachment file.
        
        :param attachment_id: Unique (in context of single file) identifier of the attachment.
        :returns: Unique identifier for the cache entry that represents attachment file.'''
        raise NotImplementedError()
    
    @staticmethod
    def get_view_info_key() -> str:
        '''Returns unique identifier for the cache entry that represents :py:class:`groupdocs.viewer.results.ViewInfo` object.
        
        :returns: Unique identifier for the cache entry that represents :py:class:`groupdocs.viewer.results.ViewInfo` object.'''
        raise NotImplementedError()
    
    @staticmethod
    def get_file_info_key() -> str:
        '''Returns unique identifier for the cache entry that represents :py:class:`groupdocs.viewer.results.ViewInfo` object.
        
        :returns: Unique identifier for the cache entry that represents :py:class:`groupdocs.viewer.results.ViewInfo` object.'''
        raise NotImplementedError()
    
    @staticmethod
    def get_file_key(extension : str) -> str:
        '''Returns unique identifier for the cache entry that represents file.
        
        :param extension: The filename suffix (including the period ".") e.g. ".doc".
        :returns: Unique identifier for the cache entry that represents file.'''
        raise NotImplementedError()
    
    @staticmethod
    def get_page_key(page_number : int, extension : str) -> str:
        '''Returns unique identifier for the cache entry that represents page file.
        
        :param page_number: The number of the page.
        :param extension: The filename suffix (including the period ".") e.g. ".doc".
        :returns: Unique identifier for the cache entry that represents page file.'''
        raise NotImplementedError()
    
    @staticmethod
    def get_resource_key(page_number : int, resource : groupdocs.viewer.results.Resource) -> str:
        '''Returns unique identifier for the cache entry that represents :py:class:`groupdocs.viewer.results.Resource` object.
        
        :param page_number: The number of the page.
        :param resource: The HTML resource.
        :returns: Unique identifier for the cache entry that represents :py:class:`groupdocs.viewer.results.Resource` object.'''
        raise NotImplementedError()
    
    @staticmethod
    def get_resource_filter(page_number : int) -> str:
        '''Returns filter string to search for cache entries that represents :py:class:`groupdocs.viewer.results.Resource` objects.
        
        :param page_number: The number of page.
        :returns: Filter string to search for cache entries that represents :py:class:`groupdocs.viewer.results.Resource` objects.'''
        raise NotImplementedError()
    

class FileCache:
    '''Represents a local on-disk cache.'''
    
    @overload
    def __init__(self, cache_path : str) -> None:
        '''Creates new instance of :py:class:`groupdocs.viewer.caching.FileCache` class.
        
        :param cache_path: Relative or absolute path where document cache will be stored.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, cache_path : str, cache_sub_folder : str) -> None:
        '''Creates new instance of :py:class:`groupdocs.viewer.caching.FileCache` class.
        
        :param cache_path: Relative or absolute path where document cache will be stored.
        :param cache_sub_folder: The sub-folder to append to ``cachePath``.'''
        raise NotImplementedError()
    
    def set(self, key : str, value : Any) -> None:
        '''Serializes data to the local disk.
        
        :param key: An unique identifier for the cache entry.
        :param value: The object to serialize.'''
        raise NotImplementedError()
    
    def get_keys(self, filter : str) -> System.Collections.Generic.IEnumerable`1[[System.String]]:
        '''Returns all file names that contains filter in filename.
        
        :param filter: The filter to use.
        :returns: File names that contains filter in filename.'''
        raise NotImplementedError()
    
    @property
    def cache_path(self) -> str:
        '''The Relative or absolute path to the cache folder.'''
        raise NotImplementedError()
    
    @property
    def cache_sub_folder(self) -> str:
        '''The sub-folder to append to the :py:attr:`groupdocs.viewer.caching.FileCache.cache_path`.'''
        raise NotImplementedError()
    

