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

class ConsoleLogger(ILogger):
    '''Writes log messages to the console.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def trace(self, message : str) -> None:
        '''Writes a trace message to the console.
        Trace log messages provide generally useful information about application flow.
        
        :param message: The trace message.'''
        raise NotImplementedError()
    
    def warning(self, message : str) -> None:
        '''Writes a warning message to the console.
        Warning log messages provide information about unexpected and recoverable events in application flow.
        
        :param message: The warning message.'''
        raise NotImplementedError()
    

class FileLogger(ILogger):
    '''Writes log messages to the file.'''
    
    def __init__(self, file_name : str) -> None:
        '''Create logger to file.
        
        :param file_name: Full file name with path'''
        raise NotImplementedError()
    
    def trace(self, message : str) -> None:
        '''Writes a trace message to the console.
        Trace log messages provide generally useful information about application flow.
        
        :param message: The trace message.'''
        raise NotImplementedError()
    
    def warning(self, message : str) -> None:
        '''Writes a warning message to the console.
        Warning log messages provide information about unexpected and recoverable events in application flow.
        
        :param message: The warning message.'''
        raise NotImplementedError()
    

class ILogger:
    '''Defines the methods that are used to perform logging.'''
    
    def trace(self, message : str) -> None:
        '''Writes a trace message.
        Trace log messages provide generally useful information about application flow.
        
        :param message: The trace message.'''
        raise NotImplementedError()
    
    def warning(self, message : str) -> None:
        '''Writes a warning message.
        Warning log messages provide information about unexpected and recoverable events in application flow.
        
        :param message: The warning message.'''
        raise NotImplementedError()
    

