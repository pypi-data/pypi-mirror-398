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

class GroupDocsViewerException:
    '''Represents the generic errors that occur during document processing.'''
    
    def __init__(self, message : str) -> None:
        '''Initializes a new instance of the :py:class:`groupdocs.viewer.exceptions.GroupDocsViewerException` class with a specified error message.
        
        :param message: The message that describes the error.'''
        raise NotImplementedError()
    

class IncorrectPasswordException(GroupDocsViewerException):
    '''The exception that is thrown when specified password is incorrect.'''
    

class InvalidFontFormatException:
    '''The exception that is thrown when trying to open, load, save or process somehow else some content, that presumably is a font of supported (known) format, but actually is a font of unexpected and/or unsupported format or not a font at all.'''
    
    def __init__(self, message : str) -> None:
        '''Creates new instance of :py:class:`groupdocs.viewer.exceptions.InvalidFontFormatException` with specified error message
        
        :param message: Textual message, that describes the error, can be null or empty'''
        raise NotImplementedError()
    

class InvalidImageFormatException:
    '''The exception that is thrown when trying to open, load, save or process somehow else some content, that presumably is an image (raster or vector),
    but actually is an image of unexpected and/or unsupported format or not an image at all.'''
    
    def __init__(self, message : str) -> None:
        '''Creates new instance of :py:class:`groupdocs.viewer.exceptions.InvalidImageFormatException` with specified error message
        
        :param message: Textual message, that describes the error, can be null or empty'''
        raise NotImplementedError()
    

class PasswordRequiredException(GroupDocsViewerException):
    '''The exception that is thrown when password is required to load the document.'''
    

