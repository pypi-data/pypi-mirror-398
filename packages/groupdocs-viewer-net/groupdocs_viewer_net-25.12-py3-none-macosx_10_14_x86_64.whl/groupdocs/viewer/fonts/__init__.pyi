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

class FolderFontSource(IFontSource):
    '''Represents the folder that contains TrueType fonts.'''
    
    def __init__(self, folder_path : str, search_option : groupdocs.viewer.fonts.SearchOption) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.fonts.FolderFontSource` class.
        
        :param folder_path: Path to the folder that contains TrueType fonts.
        :param search_option: Specifies whether to search the current folder, or the current folder and all sub-folders.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.viewer.fonts.FolderFontSource) -> bool:
        '''Determines whether the current :py:class:`groupdocs.viewer.fonts.FolderFontSource` is the same as specified :py:class:`groupdocs.viewer.fonts.FolderFontSource` object.
        
        :param other: The object to compare with the current :py:class:`groupdocs.viewer.fonts.FolderFontSource` object.
        :returns: true
        if both :py:class:`groupdocs.viewer.fonts.FolderFontSource` objects are the same; otherwise,     false'''
        raise NotImplementedError()
    
    @property
    def folder_path(self) -> str:
        '''Path to the folder that contains TrueType fonts.'''
        raise NotImplementedError()
    
    @property
    def search_option(self) -> groupdocs.viewer.fonts.SearchOption:
        '''Specifies whether to search the current folder, or the current folder and all subfolders.'''
        raise NotImplementedError()
    

class FontSettings:
    '''Provides methods for working with sources to look for TrueType fonts.'''
    
    @staticmethod
    def set_font_sources(font_sources : List[groupdocs.viewer.fonts.IFontSource]) -> None:
        '''Set the sources to look for TrueType fonts when rendering documents.
        
        :param font_sources: The font sources.'''
        raise NotImplementedError()
    
    @staticmethod
    def reset_font_sources() -> None:
        '''Resets font sources that have been set before.'''
        raise NotImplementedError()
    

class IFontSource:
    '''Marker interface for the font sources.'''
    

class SearchOption:
    '''Specifies whether to search the current folder, or the current folder and all subfolders.'''
    
    TOP_FOLDER_ONLY : SearchOption
    '''Includes only the current folder in a search.'''
    ALL_FOLDERS : SearchOption
    '''Includes the current folder and all the subfolders in a search.'''

