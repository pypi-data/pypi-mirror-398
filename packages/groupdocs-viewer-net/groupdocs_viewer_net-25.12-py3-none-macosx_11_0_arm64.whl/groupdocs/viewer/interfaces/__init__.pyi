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

class IFileStreamFactory:
    '''Defines the methods that are required for instantiating and releasing output file stream.'''
    
    def create_file_stream(self) -> io._IOBase:
        '''Creates the stream used to write output file data.
        
        :returns: Stream used to write output file data.'''
        raise NotImplementedError()
    
    def release_file_stream(self, file_stream : io._IOBase) -> None:
        '''Releases the stream created by :py:func:`groupdocs.viewer.interfaces.IFileStreamFactory.create_file_stream` method.
        
        :param file_stream: Stream created by :py:func:`groupdocs.viewer.interfaces.IFileStreamFactory.create_file_stream` method.'''
        raise NotImplementedError()
    

class IPageStreamFactory:
    '''Defines the methods that are required for instantiating and releasing output page stream.'''
    
    def create_page_stream(self, page_number : int) -> io._IOBase:
        '''Creates the stream used to write output page data.
        
        :param page_number: The number of a page.
        :returns: Stream used to write output page data.'''
        raise NotImplementedError()
    
    def release_page_stream(self, page_number : int, page_stream : io._IOBase) -> None:
        '''Releases the stream created by :py:func:`groupdocs.viewer.interfaces.IPageStreamFactory.create_page_stream` method.
        
        :param page_number: The number of a page.
        :param page_stream: Stream created by :py:func:`groupdocs.viewer.interfaces.IPageStreamFactory.create_page_stream` method.'''
        raise NotImplementedError()
    

class IResourceStreamFactory:
    '''Defines the methods that are required for creating resource URL, instantiating and releasing output HTML resource stream.'''
    
    def create_resource_stream(self, page_number : int, resource : groupdocs.viewer.results.Resource) -> io._IOBase:
        '''Creates the stream used to write output HTML resource data.
        
        :param page_number: The number of a page.
        :param resource: The HTML resource such as font, style, image or graphics.
        :returns: Stream used to write output resource data.'''
        raise NotImplementedError()
    
    def create_resource_url(self, page_number : int, resource : groupdocs.viewer.results.Resource) -> str:
        '''Creates the URL for HTML resource.
        
        :param page_number: The number of a page.
        :param resource: The HTML resource such as font, style, image or graphics.
        :returns: URL for HTML resource.'''
        raise NotImplementedError()
    
    def release_resource_stream(self, page_number : int, resource : groupdocs.viewer.results.Resource, resource_stream : io._IOBase) -> None:
        '''Releases the stream created by :py:func:`groupdocs.viewer.interfaces.IResourceStreamFactory.create_resource_stream` method.
        
        :param page_number: The number of a page.
        :param resource: The HTML resource such as font, style, image or graphics.
        :param resource_stream: Stream created by :py:func:`groupdocs.viewer.interfaces.IResourceStreamFactory.create_resource_stream` method.'''
        raise NotImplementedError()
    

