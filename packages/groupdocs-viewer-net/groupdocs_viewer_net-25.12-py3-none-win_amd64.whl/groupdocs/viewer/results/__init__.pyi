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

class ArchiveViewInfo(ViewInfo):
    '''Represents view information for archive file.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.ArchiveViewInfo` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_type : groupdocs.viewer.FileType, pages : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Page]], folders : System.Collections.Generic.List`1[[System.String]]) -> None:
        raise NotImplementedError()
    
    @property
    def file_type(self) -> groupdocs.viewer.FileType:
        '''The type of the file.'''
        raise NotImplementedError()
    
    @file_type.setter
    def file_type(self, value : groupdocs.viewer.FileType) -> None:
        '''The type of the file.'''
        raise NotImplementedError()
    
    @property
    def pages(self) -> System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Page]]:
        '''The list of pages to view.'''
        raise NotImplementedError()
    
    @pages.setter
    def pages(self, value : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Page]]) -> None:
        '''The list of pages to view.'''
        raise NotImplementedError()
    
    @property
    def folders(self) -> System.Collections.Generic.List`1[[System.String]]:
        '''The folders contained by the archive file.'''
        raise NotImplementedError()
    
    @folders.setter
    def folders(self, value : System.Collections.Generic.List`1[[System.String]]) -> None:
        '''The folders contained by the archive file.'''
        raise NotImplementedError()
    

class Attachment:
    '''Represents attachment file contained by email message, archive, PDF document or Outlook data file.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.Attachment` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_name : str, file_path : str) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.Attachment` class.
        
        :param file_name: Attachment file name.
        :param file_path: Attachment relative path e.g.  or filename when the file is located in the root of an archive, in e-mail message or data file.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, id : str, file_name : str, file_path : str, size : int) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.Attachment` class.
        
        :param id: Unique (in context of single file) identifier of the attachment.
        :param file_name: Attachment file name.
        :param file_path: Attachment relative path e.g.  or filename when the file is located in the root of an archive, in e-mail message or data file.
        :param size: Attachment file size in bytes.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, id : str, file_name : str, file_path : str, file_type : groupdocs.viewer.FileType, size : int) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.Attachment` class.
        
        :param id: Unique (in context of single file) identifier of the attachment.
        :param file_name: Attachment file name.
        :param file_path: Attachment relative path e.g.  or filename when the file is located in the root of an archive, in e-mail message or data file.
        :param file_type: Attachment file type.
        :param size: Attachment file size in bytes.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> str:
        '''Unique identifier of the attachment in context of a single file that contains this attachment.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : str) -> None:
        '''Unique identifier of the attachment in context of a single file that contains this attachment.'''
        raise NotImplementedError()
    
    @property
    def file_name(self) -> str:
        '''Attachment file name.'''
        raise NotImplementedError()
    
    @file_name.setter
    def file_name(self, value : str) -> None:
        '''Attachment file name.'''
        raise NotImplementedError()
    
    @property
    def file_path(self) -> str:
        '''Attachment relative path e.g.  or filename when the file is located in the root of an archive, in e-mail message or data file.'''
        raise NotImplementedError()
    
    @file_path.setter
    def file_path(self, value : str) -> None:
        '''Attachment relative path e.g.  or filename when the file is located in the root of an archive, in e-mail message or data file.'''
        raise NotImplementedError()
    
    @property
    def file_type(self) -> groupdocs.viewer.FileType:
        '''Attachment file type.'''
        raise NotImplementedError()
    
    @file_type.setter
    def file_type(self, value : groupdocs.viewer.FileType) -> None:
        '''Attachment file type.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Attachment file size in bytes.'''
        raise NotImplementedError()
    
    @size.setter
    def size(self, value : int) -> None:
        '''Attachment file size in bytes.'''
        raise NotImplementedError()
    

class CadViewInfo(ViewInfo):
    '''Represents view information for CAD drawing.'''
    
    def __init__(self, file_type : groupdocs.viewer.FileType, pages : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Page]], layers : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Layer]], layouts : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Layout]]) -> None:
        raise NotImplementedError()
    
    @property
    def file_type(self) -> groupdocs.viewer.FileType:
        '''The type of the file.'''
        raise NotImplementedError()
    
    @file_type.setter
    def file_type(self, value : groupdocs.viewer.FileType) -> None:
        '''The type of the file.'''
        raise NotImplementedError()
    
    @property
    def pages(self) -> System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Page]]:
        '''The list of pages to view.'''
        raise NotImplementedError()
    
    @pages.setter
    def pages(self, value : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Page]]) -> None:
        '''The list of pages to view.'''
        raise NotImplementedError()
    
    @property
    def layers(self) -> System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Layer]]:
        '''The list of layers contained by the CAD drawing.'''
        raise NotImplementedError()
    
    @layers.setter
    def layers(self, value : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Layer]]) -> None:
        '''The list of layers contained by the CAD drawing.'''
        raise NotImplementedError()
    
    @property
    def layouts(self) -> System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Layout]]:
        '''The list of layouts contained by the CAD drawing.'''
        raise NotImplementedError()
    
    @layouts.setter
    def layouts(self, value : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Layout]]) -> None:
        '''The list of layouts contained by the CAD drawing.'''
        raise NotImplementedError()
    

class Character:
    '''Represents relatively positioned rectangle which contains single character.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.Character` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, character : System.Char, x : float, y : float, width : float, height : float) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.Character` class.
        
        :param character: The character.
        :param x: The X coordinate of the highest left point on the page layout where the rectangle that contains character begins.
        :param y: The Y coordinate of the highest left point on the page layout where the rectangle that contains character begins.
        :param width: The width of the rectangle which contains single character (in pixels).
        :param height: The height of the rectangle which contains single character (in pixels).'''
        raise NotImplementedError()
    
    @property
    def value(self) -> System.Char:
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : System.Char) -> None:
        raise NotImplementedError()
    
    @property
    def x(self) -> float:
        raise NotImplementedError()
    
    @x.setter
    def x(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def y(self) -> float:
        raise NotImplementedError()
    
    @y.setter
    def y(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : float) -> None:
        raise NotImplementedError()
    

class FileInfo:
    '''Contains information about file.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes new instance of :py:attr:`groupdocs.viewer.results.FileInfo.file_type` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_type : groupdocs.viewer.FileType) -> None:
        '''Initializes new instance of :py:attr:`groupdocs.viewer.results.FileInfo.file_type` class.
        
        :param file_type: The type of the file.'''
        raise NotImplementedError()
    
    @property
    def file_type(self) -> groupdocs.viewer.FileType:
        '''The type of the file.'''
        raise NotImplementedError()
    
    @file_type.setter
    def file_type(self, value : groupdocs.viewer.FileType) -> None:
        '''The type of the file.'''
        raise NotImplementedError()
    
    @property
    def encrypted(self) -> bool:
        '''Indicates that file is encrypted.'''
        raise NotImplementedError()
    
    @encrypted.setter
    def encrypted(self, value : bool) -> None:
        '''Indicates that file is encrypted.'''
        raise NotImplementedError()
    

class Layer:
    '''Represents layer contained by the CAD drawing.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.Layer` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, name : str) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.Layer` class.
        
        :param name: The name of the layer.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, name : str, visible : bool) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.Layer` class.
        
        :param name: The name of the layer.
        :param visible: The layer visibility indicator.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.viewer.results.Layer) -> bool:
        '''Determines whether the current :py:class:`groupdocs.viewer.results.Layer` is the same as specified :py:class:`groupdocs.viewer.results.Layer` object.
        
        :param other: The object to compare with the current :py:class:`groupdocs.viewer.results.Layer` object.
        :returns: true
        if both :py:class:`groupdocs.viewer.results.Layer` objects are the same; otherwise,     false'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''The name of the layer.'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''The name of the layer.'''
        raise NotImplementedError()
    
    @property
    def visible(self) -> bool:
        '''The layer visibility indicator.'''
        raise NotImplementedError()
    
    @visible.setter
    def visible(self, value : bool) -> None:
        '''The layer visibility indicator.'''
        raise NotImplementedError()
    

class Layout:
    '''Represents layout contained by the CAD drawing.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.Layout` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, name : str, width : float, height : float) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.Layout` class.
        
        :param name: The name of the layout.
        :param width: The width of the layout in pixels.
        :param height: The height of the layout in pixels.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.viewer.results.Layout) -> bool:
        '''Determines whether the current :py:class:`groupdocs.viewer.results.Layout` is the same as specified :py:class:`groupdocs.viewer.results.Layout` object.
        
        :param other: The object to compare with the current :py:class:`groupdocs.viewer.results.Layout` object.
        :returns: true
        if both :py:class:`groupdocs.viewer.results.Layout` objects are the same; otherwise,     false'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''The name of the layout.'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''The name of the layout.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        '''The width of the layout.'''
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : float) -> None:
        '''The width of the layout.'''
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        '''The height of the layout.'''
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : float) -> None:
        '''The height of the layout.'''
        raise NotImplementedError()
    

class Line:
    '''Represents relatively positioned rectangle which contains single line.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.Line` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, line : str, x : float, y : float, width : float, height : float, words : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Word]]) -> None:
        raise NotImplementedError()
    
    @property
    def words(self) -> System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Word]]:
        '''The words contained by the line.'''
        raise NotImplementedError()
    
    @words.setter
    def words(self, value : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Word]]) -> None:
        '''The words contained by the line.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> str:
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def x(self) -> float:
        raise NotImplementedError()
    
    @x.setter
    def x(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def y(self) -> float:
        raise NotImplementedError()
    
    @y.setter
    def y(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : float) -> None:
        raise NotImplementedError()
    

class LotusNotesViewInfo(ViewInfo):
    '''Represents view information for Lotus notes database storage'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.LotusNotesViewInfo` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_type : groupdocs.viewer.FileType, pages : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Page]], notes_count : int) -> None:
        raise NotImplementedError()
    
    @property
    def file_type(self) -> groupdocs.viewer.FileType:
        '''The type of the file.'''
        raise NotImplementedError()
    
    @file_type.setter
    def file_type(self, value : groupdocs.viewer.FileType) -> None:
        '''The type of the file.'''
        raise NotImplementedError()
    
    @property
    def pages(self) -> System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Page]]:
        '''The list of pages to view.'''
        raise NotImplementedError()
    
    @pages.setter
    def pages(self, value : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Page]]) -> None:
        '''The list of pages to view.'''
        raise NotImplementedError()
    
    @property
    def notes_count(self) -> int:
        '''Notes count in storage'''
        raise NotImplementedError()
    
    @notes_count.setter
    def notes_count(self, value : int) -> None:
        '''Notes count in storage'''
        raise NotImplementedError()
    

class MboxViewInfo(ViewInfo):
    '''Represents view information for Mbox files storage'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.MboxViewInfo` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_type : groupdocs.viewer.FileType, pages : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Page]], notes_count : int) -> None:
        raise NotImplementedError()
    
    @property
    def file_type(self) -> groupdocs.viewer.FileType:
        '''The type of the file.'''
        raise NotImplementedError()
    
    @file_type.setter
    def file_type(self, value : groupdocs.viewer.FileType) -> None:
        '''The type of the file.'''
        raise NotImplementedError()
    
    @property
    def pages(self) -> System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Page]]:
        '''The list of pages to view.'''
        raise NotImplementedError()
    
    @pages.setter
    def pages(self, value : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Page]]) -> None:
        '''The list of pages to view.'''
        raise NotImplementedError()
    
    @property
    def messages_count(self) -> int:
        '''Notes count in storage'''
        raise NotImplementedError()
    
    @messages_count.setter
    def messages_count(self, value : int) -> None:
        '''Notes count in storage'''
        raise NotImplementedError()
    

class OutlookViewInfo(ViewInfo):
    '''Represents view information for Outlook Data file.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.OutlookViewInfo` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_type : groupdocs.viewer.FileType, pages : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Page]], folders : System.Collections.Generic.List`1[[System.String]]) -> None:
        raise NotImplementedError()
    
    @property
    def file_type(self) -> groupdocs.viewer.FileType:
        '''The type of the file.'''
        raise NotImplementedError()
    
    @file_type.setter
    def file_type(self, value : groupdocs.viewer.FileType) -> None:
        '''The type of the file.'''
        raise NotImplementedError()
    
    @property
    def pages(self) -> System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Page]]:
        '''The list of pages to view.'''
        raise NotImplementedError()
    
    @pages.setter
    def pages(self, value : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Page]]) -> None:
        '''The list of pages to view.'''
        raise NotImplementedError()
    
    @property
    def folders(self) -> System.Collections.Generic.List`1[[System.String]]:
        '''The list of folders contained by the Outlook Data file.'''
        raise NotImplementedError()
    
    @folders.setter
    def folders(self, value : System.Collections.Generic.List`1[[System.String]]) -> None:
        '''The list of folders contained by the Outlook Data file.'''
        raise NotImplementedError()
    

class Page:
    '''Represents single page that can be viewed.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.Page` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, number : int, visible : bool) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.Page` class.
        
        :param number: The page number.
        :param visible: The page visibility indicator.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, number : int, name : str, visible : bool) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.Page` class.
        
        :param number: The page number.
        :param name: The worksheet or page name.
        :param visible: The page visibility indicator.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, number : int, visible : bool, width : int, height : int) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.Page` class.
        
        :param number: The page number.
        :param visible: The page visibility indicator.
        :param width: The width of the page in pixels when viewing as JPG or PNG.
        :param height: The height of the page in pixels when viewing as JPG or PNG.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, number : int, name : str, visible : bool, width : int, height : int) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.Page` class.
        
        :param number: The page number.
        :param name: The worksheet or page name.
        :param visible: The page visibility indicator.
        :param width: The width of the page in pixels when viewing as JPG or PNG.
        :param height: The height of the page in pixels when viewing as JPG or PNG.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, number : int, visible : bool, width : int, height : int, lines : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Line]]) -> None:
        raise NotImplementedError()
    
    @overload
    def __init__(self, number : int, name : str, visible : bool, width : int, height : int, lines : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Line]]) -> None:
        raise NotImplementedError()
    
    @property
    def number(self) -> int:
        '''The page number.'''
        raise NotImplementedError()
    
    @number.setter
    def number(self, value : int) -> None:
        '''The page number.'''
        raise NotImplementedError()
    
    @property
    def visible(self) -> bool:
        '''The page visibility indicator.'''
        raise NotImplementedError()
    
    @visible.setter
    def visible(self, value : bool) -> None:
        '''The page visibility indicator.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''The width of the page in pixels when viewing as JPG or PNG.'''
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : int) -> None:
        '''The width of the page in pixels when viewing as JPG or PNG.'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''The height of the page in pixels when viewing as JPG or PNG.'''
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : int) -> None:
        '''The height of the page in pixels when viewing as JPG or PNG.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''The worksheet or page name.'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''The worksheet or page name.'''
        raise NotImplementedError()
    
    @property
    def lines(self) -> System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Line]]:
        '''The lines contained by the page when viewing as JPG or PNG with enabled Text Extraction.'''
        raise NotImplementedError()
    
    @lines.setter
    def lines(self, value : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Line]]) -> None:
        '''The lines contained by the page when viewing as JPG or PNG with enabled Text Extraction.'''
        raise NotImplementedError()
    

class PdfViewInfo(ViewInfo):
    '''Represents view information for PDF document.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.PdfViewInfo` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_type : groupdocs.viewer.FileType, pages : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Page]], printing_allowed : bool) -> None:
        raise NotImplementedError()
    
    @property
    def file_type(self) -> groupdocs.viewer.FileType:
        '''The type of the file.'''
        raise NotImplementedError()
    
    @file_type.setter
    def file_type(self, value : groupdocs.viewer.FileType) -> None:
        '''The type of the file.'''
        raise NotImplementedError()
    
    @property
    def pages(self) -> System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Page]]:
        '''The list of pages to view.'''
        raise NotImplementedError()
    
    @pages.setter
    def pages(self, value : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Page]]) -> None:
        '''The list of pages to view.'''
        raise NotImplementedError()
    
    @property
    def printing_allowed(self) -> bool:
        '''Indicates if printing of the document is allowed.'''
        raise NotImplementedError()
    
    @printing_allowed.setter
    def printing_allowed(self, value : bool) -> None:
        '''Indicates if printing of the document is allowed.'''
        raise NotImplementedError()
    

class ProjectManagementViewInfo(ViewInfo):
    '''Represents view information for MS Project document.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.ProjectManagementViewInfo` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_type : groupdocs.viewer.FileType, pages : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Page]], start_date : datetime, end_date : datetime) -> None:
        raise NotImplementedError()
    
    @property
    def file_type(self) -> groupdocs.viewer.FileType:
        '''The type of the file.'''
        raise NotImplementedError()
    
    @file_type.setter
    def file_type(self, value : groupdocs.viewer.FileType) -> None:
        '''The type of the file.'''
        raise NotImplementedError()
    
    @property
    def pages(self) -> System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Page]]:
        '''The list of pages to view.'''
        raise NotImplementedError()
    
    @pages.setter
    def pages(self, value : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Page]]) -> None:
        '''The list of pages to view.'''
        raise NotImplementedError()
    
    @property
    def start_date(self) -> datetime:
        '''The date time from which the project started.'''
        raise NotImplementedError()
    
    @start_date.setter
    def start_date(self, value : datetime) -> None:
        '''The date time from which the project started.'''
        raise NotImplementedError()
    
    @property
    def end_date(self) -> datetime:
        '''The date time when the project is to be completed.'''
        raise NotImplementedError()
    
    @end_date.setter
    def end_date(self, value : datetime) -> None:
        '''The date time when the project is to be completed.'''
        raise NotImplementedError()
    

class Resource:
    '''Represents HTML resource such as font, style, image or graphics.'''
    
    @overload
    def __init__(self) -> None:
        '''Creates new instance of :py:class:`groupdocs.viewer.results.Resource` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_name : str, nested : bool) -> None:
        '''Creates new instance of :py:class:`groupdocs.viewer.results.Resource` class.
        
        :param file_name: Resource file name.
        :param nested: Indicates whether resource resides inside another resource, e.g. font resource that resides in CSS or SVG resource.'''
        raise NotImplementedError()
    
    @property
    def file_name(self) -> str:
        '''The resource file name.'''
        raise NotImplementedError()
    
    @file_name.setter
    def file_name(self, value : str) -> None:
        '''The resource file name.'''
        raise NotImplementedError()
    
    @property
    def nested(self) -> bool:
        '''Indicates whether resource resides inside another resource,
        e.g. font resource that resides in CSS or SVG resource.'''
        raise NotImplementedError()
    
    @nested.setter
    def nested(self, value : bool) -> None:
        '''Indicates whether resource resides inside another resource,
        e.g. font resource that resides in CSS or SVG resource.'''
        raise NotImplementedError()
    

class ViewInfo:
    '''Represents view information for generic document.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.ViewInfo` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_type : groupdocs.viewer.FileType, pages : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Page]]) -> None:
        raise NotImplementedError()
    
    @property
    def file_type(self) -> groupdocs.viewer.FileType:
        '''The type of the file.'''
        raise NotImplementedError()
    
    @file_type.setter
    def file_type(self, value : groupdocs.viewer.FileType) -> None:
        '''The type of the file.'''
        raise NotImplementedError()
    
    @property
    def pages(self) -> System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Page]]:
        '''The list of pages to view.'''
        raise NotImplementedError()
    
    @pages.setter
    def pages(self, value : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Page]]) -> None:
        '''The list of pages to view.'''
        raise NotImplementedError()
    

class Word:
    '''Represents relatively positioned rectangle which contains single word.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.results.Word` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, word : str, x : float, y : float, width : float, height : float, characters : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Character]]) -> None:
        raise NotImplementedError()
    
    @property
    def characters(self) -> System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Character]]:
        '''The characters contained by the word.'''
        raise NotImplementedError()
    
    @characters.setter
    def characters(self, value : System.Collections.Generic.List`1[[GroupDocs.Viewer.Results.Character]]) -> None:
        '''The characters contained by the word.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> str:
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def x(self) -> float:
        raise NotImplementedError()
    
    @x.setter
    def x(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def y(self) -> float:
        raise NotImplementedError()
    
    @y.setter
    def y(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : float) -> None:
        raise NotImplementedError()
    

