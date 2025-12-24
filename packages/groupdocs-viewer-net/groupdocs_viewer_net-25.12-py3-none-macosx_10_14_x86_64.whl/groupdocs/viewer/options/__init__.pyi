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

class ArchiveOptions:
    '''Contains options for rendering the archive files. For details, see the `documentation <https://docs.groupdocs.com/viewer/net/render-archive-files/>`.'''
    
    def __init__(self) -> None:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.ArchiveOptions` class.'''
        raise NotImplementedError()
    
    @property
    def folder(self) -> str:
        '''Sets the folder to be rendered.'''
        raise NotImplementedError()
    
    @folder.setter
    def folder(self, value : str) -> None:
        '''Sets the folder to be rendered.'''
        raise NotImplementedError()
    
    @property
    def file_name(self) -> groupdocs.viewer.options.FileName:
        '''Sets the displayed archive file name.'''
        raise NotImplementedError()
    
    @file_name.setter
    def file_name(self, value : groupdocs.viewer.options.FileName) -> None:
        '''Sets the displayed archive file name.'''
        raise NotImplementedError()
    
    @property
    def items_per_page(self) -> int:
        '''Number of records per page (for rendering to HTML only)'''
        raise NotImplementedError()
    
    @items_per_page.setter
    def items_per_page(self, value : int) -> None:
        '''Number of records per page (for rendering to HTML only)'''
        raise NotImplementedError()
    

class BaseViewOptions:
    '''Contains the base rendering options.'''
    
    @property
    def render_comments(self) -> bool:
        '''Enables rendering comments.'''
        raise NotImplementedError()
    
    @render_comments.setter
    def render_comments(self, value : bool) -> None:
        '''Enables rendering comments.'''
        raise NotImplementedError()
    
    @property
    def render_notes(self) -> bool:
        '''Enables rendering notes.'''
        raise NotImplementedError()
    
    @render_notes.setter
    def render_notes(self, value : bool) -> None:
        '''Enables rendering notes.'''
        raise NotImplementedError()
    
    @property
    def render_hidden_pages(self) -> bool:
        '''Enables rendering of hidden pages.'''
        raise NotImplementedError()
    
    @render_hidden_pages.setter
    def render_hidden_pages(self, value : bool) -> None:
        '''Enables rendering of hidden pages.'''
        raise NotImplementedError()
    
    @property
    def default_font_name(self) -> str:
        '''Sets the default font for a document.'''
        raise NotImplementedError()
    
    @default_font_name.setter
    def default_font_name(self, value : str) -> None:
        '''Sets the default font for a document.'''
        raise NotImplementedError()
    
    @property
    def archive_options(self) -> groupdocs.viewer.options.ArchiveOptions:
        '''The archive files view options.'''
        raise NotImplementedError()
    
    @archive_options.setter
    def archive_options(self, value : groupdocs.viewer.options.ArchiveOptions) -> None:
        '''The archive files view options.'''
        raise NotImplementedError()
    
    @property
    def cad_options(self) -> groupdocs.viewer.options.CadOptions:
        '''The CAD drawing view options.'''
        raise NotImplementedError()
    
    @cad_options.setter
    def cad_options(self, value : groupdocs.viewer.options.CadOptions) -> None:
        '''The CAD drawing view options.'''
        raise NotImplementedError()
    
    @property
    def email_options(self) -> groupdocs.viewer.options.EmailOptions:
        '''The email messages view options.'''
        raise NotImplementedError()
    
    @email_options.setter
    def email_options(self, value : groupdocs.viewer.options.EmailOptions) -> None:
        '''The email messages view options.'''
        raise NotImplementedError()
    
    @property
    def outlook_options(self) -> groupdocs.viewer.options.OutlookOptions:
        '''The Microsoft Outlook data files view options.'''
        raise NotImplementedError()
    
    @outlook_options.setter
    def outlook_options(self, value : groupdocs.viewer.options.OutlookOptions) -> None:
        '''The Microsoft Outlook data files view options.'''
        raise NotImplementedError()
    
    @property
    def mail_storage_options(self) -> groupdocs.viewer.options.MailStorageOptions:
        '''Mail storage data files view options.'''
        raise NotImplementedError()
    
    @mail_storage_options.setter
    def mail_storage_options(self, value : groupdocs.viewer.options.MailStorageOptions) -> None:
        '''Mail storage data files view options.'''
        raise NotImplementedError()
    
    @property
    def pdf_options(self) -> groupdocs.viewer.options.PdfOptions:
        '''The PDF document view options.'''
        raise NotImplementedError()
    
    @pdf_options.setter
    def pdf_options(self, value : groupdocs.viewer.options.PdfOptions) -> None:
        '''The PDF document view options.'''
        raise NotImplementedError()
    
    @property
    def project_management_options(self) -> groupdocs.viewer.options.ProjectManagementOptions:
        '''The project management files view options.'''
        raise NotImplementedError()
    
    @project_management_options.setter
    def project_management_options(self, value : groupdocs.viewer.options.ProjectManagementOptions) -> None:
        '''The project management files view options.'''
        raise NotImplementedError()
    
    @property
    def spreadsheet_options(self) -> groupdocs.viewer.options.SpreadsheetOptions:
        '''The spreadsheet files view options.'''
        raise NotImplementedError()
    
    @spreadsheet_options.setter
    def spreadsheet_options(self, value : groupdocs.viewer.options.SpreadsheetOptions) -> None:
        '''The spreadsheet files view options.'''
        raise NotImplementedError()
    
    @property
    def word_processing_options(self) -> groupdocs.viewer.options.WordProcessingOptions:
        '''The Word processing files view options.'''
        raise NotImplementedError()
    
    @word_processing_options.setter
    def word_processing_options(self, value : groupdocs.viewer.options.WordProcessingOptions) -> None:
        '''The Word processing files view options.'''
        raise NotImplementedError()
    
    @property
    def visio_rendering_options(self) -> groupdocs.viewer.options.VisioRenderingOptions:
        '''The Visio files view options.'''
        raise NotImplementedError()
    
    @visio_rendering_options.setter
    def visio_rendering_options(self, value : groupdocs.viewer.options.VisioRenderingOptions) -> None:
        '''The Visio files view options.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> groupdocs.viewer.options.TextOptions:
        '''Text files view options.'''
        raise NotImplementedError()
    
    @text_options.setter
    def text_options(self, value : groupdocs.viewer.options.TextOptions) -> None:
        '''Text files view options.'''
        raise NotImplementedError()
    
    @property
    def presentation_options(self) -> groupdocs.viewer.options.PresentationOptions:
        '''The presentation files view options.'''
        raise NotImplementedError()
    
    @presentation_options.setter
    def presentation_options(self, value : groupdocs.viewer.options.PresentationOptions) -> None:
        '''The presentation files view options.'''
        raise NotImplementedError()
    
    @property
    def web_document_options(self) -> groupdocs.viewer.options.WebDocumentOptions:
        '''The Web files view options.'''
        raise NotImplementedError()
    
    @web_document_options.setter
    def web_document_options(self, value : groupdocs.viewer.options.WebDocumentOptions) -> None:
        '''The Web files view options.'''
        raise NotImplementedError()
    

class CadOptions:
    '''Contains options for rendering CAD drawings. For more information and code examples, see the `Render CAD drawings and models as HTML, PDF, and image files <https://docs.groupdocs.com/viewer/net/render-cad-drawings-and-models/>` and `Specify rendering options for CAD files <https://docs.groupdocs.com/viewer/net/specify-cad-rendering-options/>`.'''
    
    @staticmethod
    def for_rendering_by_scale_factor(scale_factor : float) -> groupdocs.viewer.options.CadOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.CadOptions` class for rendering by scale factor.
        
        :param scale_factor: Value higher than 1 enlarges output result; value between 0 and 1 reduces output result.
        :returns: New instance of the :py:class:`groupdocs.viewer.options.CadOptions` class for rendering by scale factor.'''
        raise NotImplementedError()
    
    @staticmethod
    def for_rendering_by_width(width : int) -> groupdocs.viewer.options.CadOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.CadOptions` class for rendering by width.
        
        :param width: The width of the output result (in pixels).
        :returns: New instance of the :py:class:`groupdocs.viewer.options.CadOptions` class for rendering by width.'''
        raise NotImplementedError()
    
    @staticmethod
    def for_rendering_by_height(height : int) -> groupdocs.viewer.options.CadOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.CadOptions` class for rendering by height.
        
        :param height: The height of the output result (in pixels).
        :returns: New instance of the :py:class:`groupdocs.viewer.options.CadOptions` class for rendering by height.'''
        raise NotImplementedError()
    
    @staticmethod
    def for_rendering_by_width_and_height(width : int, height : int) -> groupdocs.viewer.options.CadOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.CadOptions` class for rendering by width and height.
        
        :param width: The width of the output result (in pixels).
        :param height: The height of the output result (in pixels).
        :returns: New instance of :py:class:`groupdocs.viewer.options.CadOptions` class for rendering by width and height.'''
        raise NotImplementedError()
    
    @property
    def scale_factor(self) -> float:
        '''Value higher than 1 enlarges output result; value between 0 and 1 reduces output result.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''The width of the output result (in pixels).'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''The height of the output result (in pixels).'''
        raise NotImplementedError()
    
    @property
    def background_color(self) -> groupdocs.viewer.drawing.Argb32Color:
        '''Image background color.'''
        raise NotImplementedError()
    
    @background_color.setter
    def background_color(self, value : groupdocs.viewer.drawing.Argb32Color) -> None:
        '''Image background color.'''
        raise NotImplementedError()
    
    @property
    def tiles(self) -> System.Collections.Generic.IList`1[[GroupDocs.Viewer.Options.Tile]]:
        '''The drawing regions to render.'''
        raise NotImplementedError()
    
    @tiles.setter
    def tiles(self, value : System.Collections.Generic.IList`1[[GroupDocs.Viewer.Options.Tile]]) -> None:
        '''The drawing regions to render.'''
        raise NotImplementedError()
    
    @property
    def render_layouts(self) -> bool:
        '''Flag if layouts from CAD document should be rendered.'''
        raise NotImplementedError()
    
    @render_layouts.setter
    def render_layouts(self, value : bool) -> None:
        '''Flag if layouts from CAD document should be rendered.'''
        raise NotImplementedError()
    
    @property
    def layout_name(self) -> str:
        '''The name of the specific layout to render. Layout name is case-sensitive.'''
        raise NotImplementedError()
    
    @layout_name.setter
    def layout_name(self, value : str) -> None:
        '''The name of the specific layout to render. Layout name is case-sensitive.'''
        raise NotImplementedError()
    
    @property
    def layers(self) -> System.Collections.Generic.IList`1[[GroupDocs.Viewer.Results.Layer]]:
        '''The CAD drawing layers to render.'''
        raise NotImplementedError()
    
    @layers.setter
    def layers(self, value : System.Collections.Generic.IList`1[[GroupDocs.Viewer.Results.Layer]]) -> None:
        '''The CAD drawing layers to render.'''
        raise NotImplementedError()
    
    @property
    def pc_3_file(self) -> str:
        '''PC3 - plotter configuration file'''
        raise NotImplementedError()
    
    @pc_3_file.setter
    def pc_3_file(self, value : str) -> None:
        '''PC3 - plotter configuration file'''
        raise NotImplementedError()
    
    @property
    def enable_performance_conversion_mode(self) -> bool:
        '''Setting this flag to ``true`` enables a special performance-oriented  conversion mode for all formats within CAD family — in this mode the conversion speed is much faster, but the quality of the resultant documents is signifiantly worser. By default is disabled (``false``) — the quality of the resultant documents is the best possible at the expense of performance.'''
        raise NotImplementedError()
    
    @enable_performance_conversion_mode.setter
    def enable_performance_conversion_mode(self, value : bool) -> None:
        '''Setting this flag to ``true`` enables a special performance-oriented  conversion mode for all formats within CAD family — in this mode the conversion speed is much faster, but the quality of the resultant documents is signifiantly worser. By default is disabled (``false``) — the quality of the resultant documents is the best possible at the expense of performance.'''
        raise NotImplementedError()
    

class EmailOptions:
    '''Contains options for rendering email messages. For details, see the `documentation <https://docs.groupdocs.com/viewer/net/render-email-messages/>`.'''
    
    def __init__(self) -> None:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.EmailOptions` class.'''
        raise NotImplementedError()
    
    @property
    def page_size(self) -> groupdocs.viewer.options.PageSize:
        '''The size of the output page.'''
        raise NotImplementedError()
    
    @page_size.setter
    def page_size(self, value : groupdocs.viewer.options.PageSize) -> None:
        '''The size of the output page.'''
        raise NotImplementedError()
    
    @property
    def date_time_format(self) -> str:
        '''Time Format (can be include TimeZone).
        For example: \'MM d yyyy HH:mm tt\', if not set - current system format is used'''
        raise NotImplementedError()
    
    @date_time_format.setter
    def date_time_format(self, value : str) -> None:
        '''Time Format (can be include TimeZone).
        For example: \'MM d yyyy HH:mm tt\', if not set - current system format is used'''
        raise NotImplementedError()
    
    @property
    def time_zone_offset(self) -> System.TimeSpan:
        '''Message time zone offset.'''
        raise NotImplementedError()
    
    @time_zone_offset.setter
    def time_zone_offset(self, value : System.TimeSpan) -> None:
        '''Message time zone offset.'''
        raise NotImplementedError()
    

class Field:
    '''Represents email message field e.g. From, To, Subject etc. For details, see the `documentation <https://docs.groupdocs.com/viewer/net/render-email-messages/#rename-fields-in-the-message-header>`.'''
    
    @property
    def name(self) -> str:
        '''Field name.'''
        raise NotImplementedError()
    
    @property
    def ANNIVERSARY(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Anniversary".'''
        raise NotImplementedError()

    @property
    def ATTACHMENTS(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Attachments".'''
        raise NotImplementedError()

    @property
    def BCC(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Bcc".'''
        raise NotImplementedError()

    @property
    def BIRTHDAY(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Birthday".'''
        raise NotImplementedError()

    @property
    def BUSINESS(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Business".'''
        raise NotImplementedError()

    @property
    def BUSINESS_ADDRESS(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Business Address".'''
        raise NotImplementedError()

    @property
    def BUSINESS_FAX(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Business Fax".'''
        raise NotImplementedError()

    @property
    def BUSINESS_HOMEPAGE(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "BusinessHomepage".'''
        raise NotImplementedError()

    @property
    def CC(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Cc".'''
        raise NotImplementedError()

    @property
    def COMPANY(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Company".'''
        raise NotImplementedError()

    @property
    def DEPARTMENT(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Department".'''
        raise NotImplementedError()

    @property
    def EMAIL(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Email".'''
        raise NotImplementedError()

    @property
    def EMAIL_DISPLAY_AS(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Email Display As".'''
        raise NotImplementedError()

    @property
    def EMAIL2(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Email2".'''
        raise NotImplementedError()

    @property
    def EMAIL_2_DISPLAY_AS(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Email2 Display As".'''
        raise NotImplementedError()

    @property
    def EMAIL3(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Email3".'''
        raise NotImplementedError()

    @property
    def EMAIL_3_DISPLAY_AS(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Email3 Display As".'''
        raise NotImplementedError()

    @property
    def END(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "End".'''
        raise NotImplementedError()

    @property
    def FIRST_NAME(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "First Name".'''
        raise NotImplementedError()

    @property
    def FROM(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "From".'''
        raise NotImplementedError()

    @property
    def FULL_NAME(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Full Name".'''
        raise NotImplementedError()

    @property
    def GENDER(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Gender".'''
        raise NotImplementedError()

    @property
    def HOBBIES(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Hobbies".'''
        raise NotImplementedError()

    @property
    def HOME(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Home".'''
        raise NotImplementedError()

    @property
    def HOME_ADDRESS(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Home Address".'''
        raise NotImplementedError()

    @property
    def IMPORTANCE(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Importance".'''
        raise NotImplementedError()

    @property
    def JOB_TITLE(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Job Title".'''
        raise NotImplementedError()

    @property
    def LAST_NAME(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Last Name".'''
        raise NotImplementedError()

    @property
    def LOCATION(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Location".'''
        raise NotImplementedError()

    @property
    def MIDDLE_NAME(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Middle Name".'''
        raise NotImplementedError()

    @property
    def MOBILE(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Mobile".'''
        raise NotImplementedError()

    @property
    def ORGANIZER(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Organizer".'''
        raise NotImplementedError()

    @property
    def OTHER_ADDRESS(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Other Address".'''
        raise NotImplementedError()

    @property
    def PERSONAL_HOMEPAGE(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Personal Homepage".'''
        raise NotImplementedError()

    @property
    def PROFESSION(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Profession".'''
        raise NotImplementedError()

    @property
    def RECURRENCE(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Recurrence"'''
        raise NotImplementedError()

    @property
    def RECURRENCE_PATTERN(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Recurrence Pattern".'''
        raise NotImplementedError()

    @property
    def REQUIRED_ATTENDEES(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Required Attendees".'''
        raise NotImplementedError()

    @property
    def SENT(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Sent".'''
        raise NotImplementedError()

    @property
    def SHOW_TIME_AS(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Show Time As".'''
        raise NotImplementedError()

    @property
    def SPOUSE_PARTNER(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Spouse/Partner".'''
        raise NotImplementedError()

    @property
    def START(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Start".'''
        raise NotImplementedError()

    @property
    def SUBJECT(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "Subject".'''
        raise NotImplementedError()

    @property
    def TO(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "To".'''
        raise NotImplementedError()

    @property
    def USER_FIELD1(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "User Field 1".'''
        raise NotImplementedError()

    @property
    def USER_FIELD2(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "User Field 2".'''
        raise NotImplementedError()

    @property
    def USER_FIELD3(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "User Field 3".'''
        raise NotImplementedError()

    @property
    def USER_FIELD4(self) -> groupdocs.viewer.options.Field:
        '''Default field text is "User Field 4".'''
        raise NotImplementedError()


class FileName:
    '''The filename.'''
    
    def __init__(self, file_name : str) -> None:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.FileName` class.
        
        :param file_name: The name of the file.'''
        raise NotImplementedError()
    
    @property
    def EMPTY(self) -> groupdocs.viewer.options.FileName:
        '''The empty filename.'''
        raise NotImplementedError()

    @property
    def SOURCE(self) -> groupdocs.viewer.options.FileName:
        '''The name of the source file.'''
        raise NotImplementedError()


class HtmlViewOptions(ViewOptions):
    '''Contains options for rendering documents into HTML format. For details, see the `topic <https://docs.groupdocs.com/viewer/net/rendering-to-html/>` and its children.'''
    
    @overload
    @staticmethod
    def for_embedded_resources(page_stream_factory : groupdocs.viewer.interfaces.IPageStreamFactory) -> groupdocs.viewer.options.HtmlViewOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.HtmlViewOptions` class for rendering into HTML with embedded resources.
        
        :param page_stream_factory: The factory which implements methods for creating and releasing output page stream.
        :returns: New instance of the :py:class:`groupdocs.viewer.options.HtmlViewOptions` class for rendering into HTML with embedded resources.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def for_embedded_resources() -> groupdocs.viewer.options.HtmlViewOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.HtmlViewOptions` class.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def for_embedded_resources(file_path_format : str) -> groupdocs.viewer.options.HtmlViewOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.HtmlViewOptions` class.
        
        :param file_path_format: The file path format e.g. \'page_{0}.html\'.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def for_external_resources(page_stream_factory : groupdocs.viewer.interfaces.IPageStreamFactory, resource_stream_factory : groupdocs.viewer.interfaces.IResourceStreamFactory) -> groupdocs.viewer.options.HtmlViewOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.HtmlViewOptions` class for rendering into HTML with external resources.
        
        :param page_stream_factory: The factory which implements methods for creating and releasing output page stream.
        :param resource_stream_factory: The factory which implements methods that are required for creating resource URL, instantiating and releasing output HTML resource stream.
        :returns: New instance of the :py:class:`groupdocs.viewer.options.HtmlViewOptions` class for rendering into HTML with external resources.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def for_external_resources() -> groupdocs.viewer.options.HtmlViewOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.HtmlViewOptions` class.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def for_external_resources(file_path_format : str, resource_file_path_format : str, resource_url_format : str) -> groupdocs.viewer.options.HtmlViewOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.HtmlViewOptions` class.
        
        :param file_path_format: The file path format e.g. \'page_{0}.html\'.
        :param resource_file_path_format: The resource file path format e.g. \'page_{0}/resource_{1}\'.
        :param resource_url_format: The resource URL format e.g. \'page_{0}/resource_{1}\'.'''
        raise NotImplementedError()
    
    def rotate_page(self, page_number : int, rotation : groupdocs.viewer.options.Rotation) -> None:
        '''Applies the clockwise rotation to a page.
        
        :param page_number: The page number, must be strictly greater than 0
        :param rotation: The rotation value.'''
        raise NotImplementedError()
    
    @property
    def render_comments(self) -> bool:
        '''Enables rendering comments.'''
        raise NotImplementedError()
    
    @render_comments.setter
    def render_comments(self, value : bool) -> None:
        '''Enables rendering comments.'''
        raise NotImplementedError()
    
    @property
    def render_notes(self) -> bool:
        '''Enables rendering notes.'''
        raise NotImplementedError()
    
    @render_notes.setter
    def render_notes(self, value : bool) -> None:
        '''Enables rendering notes.'''
        raise NotImplementedError()
    
    @property
    def render_hidden_pages(self) -> bool:
        '''Enables rendering of hidden pages.'''
        raise NotImplementedError()
    
    @render_hidden_pages.setter
    def render_hidden_pages(self, value : bool) -> None:
        '''Enables rendering of hidden pages.'''
        raise NotImplementedError()
    
    @property
    def default_font_name(self) -> str:
        '''Sets the default font for a document.'''
        raise NotImplementedError()
    
    @default_font_name.setter
    def default_font_name(self, value : str) -> None:
        '''Sets the default font for a document.'''
        raise NotImplementedError()
    
    @property
    def archive_options(self) -> groupdocs.viewer.options.ArchiveOptions:
        '''The archive files view options.'''
        raise NotImplementedError()
    
    @archive_options.setter
    def archive_options(self, value : groupdocs.viewer.options.ArchiveOptions) -> None:
        '''The archive files view options.'''
        raise NotImplementedError()
    
    @property
    def cad_options(self) -> groupdocs.viewer.options.CadOptions:
        '''The CAD drawing view options.'''
        raise NotImplementedError()
    
    @cad_options.setter
    def cad_options(self, value : groupdocs.viewer.options.CadOptions) -> None:
        '''The CAD drawing view options.'''
        raise NotImplementedError()
    
    @property
    def email_options(self) -> groupdocs.viewer.options.EmailOptions:
        '''The email messages view options.'''
        raise NotImplementedError()
    
    @email_options.setter
    def email_options(self, value : groupdocs.viewer.options.EmailOptions) -> None:
        '''The email messages view options.'''
        raise NotImplementedError()
    
    @property
    def outlook_options(self) -> groupdocs.viewer.options.OutlookOptions:
        '''The Microsoft Outlook data files view options.'''
        raise NotImplementedError()
    
    @outlook_options.setter
    def outlook_options(self, value : groupdocs.viewer.options.OutlookOptions) -> None:
        '''The Microsoft Outlook data files view options.'''
        raise NotImplementedError()
    
    @property
    def mail_storage_options(self) -> groupdocs.viewer.options.MailStorageOptions:
        '''Mail storage data files view options.'''
        raise NotImplementedError()
    
    @mail_storage_options.setter
    def mail_storage_options(self, value : groupdocs.viewer.options.MailStorageOptions) -> None:
        '''Mail storage data files view options.'''
        raise NotImplementedError()
    
    @property
    def pdf_options(self) -> groupdocs.viewer.options.PdfOptions:
        '''The PDF document view options.'''
        raise NotImplementedError()
    
    @pdf_options.setter
    def pdf_options(self, value : groupdocs.viewer.options.PdfOptions) -> None:
        '''The PDF document view options.'''
        raise NotImplementedError()
    
    @property
    def project_management_options(self) -> groupdocs.viewer.options.ProjectManagementOptions:
        '''The project management files view options.'''
        raise NotImplementedError()
    
    @project_management_options.setter
    def project_management_options(self, value : groupdocs.viewer.options.ProjectManagementOptions) -> None:
        '''The project management files view options.'''
        raise NotImplementedError()
    
    @property
    def spreadsheet_options(self) -> groupdocs.viewer.options.SpreadsheetOptions:
        '''The spreadsheet files view options.'''
        raise NotImplementedError()
    
    @spreadsheet_options.setter
    def spreadsheet_options(self, value : groupdocs.viewer.options.SpreadsheetOptions) -> None:
        '''The spreadsheet files view options.'''
        raise NotImplementedError()
    
    @property
    def word_processing_options(self) -> groupdocs.viewer.options.WordProcessingOptions:
        '''The Word processing files view options.'''
        raise NotImplementedError()
    
    @word_processing_options.setter
    def word_processing_options(self, value : groupdocs.viewer.options.WordProcessingOptions) -> None:
        '''The Word processing files view options.'''
        raise NotImplementedError()
    
    @property
    def visio_rendering_options(self) -> groupdocs.viewer.options.VisioRenderingOptions:
        '''The Visio files view options.'''
        raise NotImplementedError()
    
    @visio_rendering_options.setter
    def visio_rendering_options(self, value : groupdocs.viewer.options.VisioRenderingOptions) -> None:
        '''The Visio files view options.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> groupdocs.viewer.options.TextOptions:
        '''Text files view options.'''
        raise NotImplementedError()
    
    @text_options.setter
    def text_options(self, value : groupdocs.viewer.options.TextOptions) -> None:
        '''Text files view options.'''
        raise NotImplementedError()
    
    @property
    def presentation_options(self) -> groupdocs.viewer.options.PresentationOptions:
        '''The presentation files view options.'''
        raise NotImplementedError()
    
    @presentation_options.setter
    def presentation_options(self, value : groupdocs.viewer.options.PresentationOptions) -> None:
        '''The presentation files view options.'''
        raise NotImplementedError()
    
    @property
    def web_document_options(self) -> groupdocs.viewer.options.WebDocumentOptions:
        '''The Web files view options.'''
        raise NotImplementedError()
    
    @web_document_options.setter
    def web_document_options(self, value : groupdocs.viewer.options.WebDocumentOptions) -> None:
        '''The Web files view options.'''
        raise NotImplementedError()
    
    @property
    def watermark(self) -> groupdocs.viewer.options.Watermark:
        '''The text watermark to be applied to each page.'''
        raise NotImplementedError()
    
    @watermark.setter
    def watermark(self, value : groupdocs.viewer.options.Watermark) -> None:
        '''The text watermark to be applied to each page.'''
        raise NotImplementedError()
    
    @property
    def render_responsive(self) -> bool:
        '''Enables responsive rendering.'''
        raise NotImplementedError()
    
    @render_responsive.setter
    def render_responsive(self, value : bool) -> None:
        '''Enables responsive rendering.'''
        raise NotImplementedError()
    
    @property
    def minify(self) -> bool:
        '''Enables HTML content and HTML resources minification.'''
        raise NotImplementedError()
    
    @minify.setter
    def minify(self, value : bool) -> None:
        '''Enables HTML content and HTML resources minification.'''
        raise NotImplementedError()
    
    @property
    def render_to_single_page(self) -> bool:
        '''Enables rendering an entire document to one HTML file.'''
        raise NotImplementedError()
    
    @render_to_single_page.setter
    def render_to_single_page(self, value : bool) -> None:
        '''Enables rendering an entire document to one HTML file.'''
        raise NotImplementedError()
    
    @property
    def image_max_width(self) -> int:
        '''Max width of an output image (in pixels). The property is available when converting single image to HTML only.'''
        raise NotImplementedError()
    
    @image_max_width.setter
    def image_max_width(self, value : int) -> None:
        '''Max width of an output image (in pixels). The property is available when converting single image to HTML only.'''
        raise NotImplementedError()
    
    @property
    def image_max_height(self) -> int:
        '''Max height of an output image (in pixels). The property is available when converting single image to HTML only.'''
        raise NotImplementedError()
    
    @image_max_height.setter
    def image_max_height(self, value : int) -> None:
        '''Max height of an output image (in pixels). The property is available when converting single image to HTML only.'''
        raise NotImplementedError()
    
    @property
    def image_width(self) -> int:
        '''The width of the output image (in pixels). The property is available when converting single image to HTML only.'''
        raise NotImplementedError()
    
    @image_width.setter
    def image_width(self, value : int) -> None:
        '''The width of the output image (in pixels). The property is available when converting single image to HTML only.'''
        raise NotImplementedError()
    
    @property
    def image_height(self) -> int:
        '''The height of an output image (in pixels). The property is available when converting single image to HTML only.'''
        raise NotImplementedError()
    
    @image_height.setter
    def image_height(self, value : int) -> None:
        '''The height of an output image (in pixels). The property is available when converting single image to HTML only.'''
        raise NotImplementedError()
    
    @property
    def for_printing(self) -> bool:
        '''Enables optimization the output HTML for printing.'''
        raise NotImplementedError()
    
    @for_printing.setter
    def for_printing(self, value : bool) -> None:
        '''Enables optimization the output HTML for printing.'''
        raise NotImplementedError()
    
    @property
    def exclude_fonts(self) -> bool:
        '''Disables adding any fonts into HTML document.'''
        raise NotImplementedError()
    
    @exclude_fonts.setter
    def exclude_fonts(self, value : bool) -> None:
        '''Disables adding any fonts into HTML document.'''
        raise NotImplementedError()
    
    @property
    def fonts_to_exclude(self) -> System.Collections.Generic.List`1[[System.String]]:
        '''The list of font names to exclude from HTML document.'''
        raise NotImplementedError()
    
    @fonts_to_exclude.setter
    def fonts_to_exclude(self, value : System.Collections.Generic.List`1[[System.String]]) -> None:
        '''The list of font names to exclude from HTML document.'''
        raise NotImplementedError()
    

class IMaxSizeOptions:
    '''Limits of image size options interface.'''
    
    @property
    def max_width(self) -> int:
        '''Maximum width of an output image in pixels.'''
        raise NotImplementedError()
    
    @max_width.setter
    def max_width(self, value : int) -> None:
        '''Maximum width of an output image in pixels.'''
        raise NotImplementedError()
    
    @property
    def max_height(self) -> int:
        '''Maximum height of an output image in pixels.'''
        raise NotImplementedError()
    
    @max_height.setter
    def max_height(self, value : int) -> None:
        '''Maximum height of an output image in pixels.'''
        raise NotImplementedError()
    

class JpgViewOptions(ViewOptions):
    '''Provides options for rendering documents into JPG format. For details, see this `page <https://docs.groupdocs.com/viewer/net/rendering-to-png-or-jpeg/>` and its children.'''
    
    @overload
    def __init__(self, page_stream_factory : groupdocs.viewer.interfaces.IPageStreamFactory) -> None:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.JpgViewOptions` class.
        
        :param page_stream_factory: The factory which implements methods for creating and releasing output page stream.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self) -> None:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.JpgViewOptions` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_path_format : str) -> None:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.JpgViewOptions` class.
        
        :param file_path_format: The file path format e.g. \'page_{0}.jpg\'.'''
        raise NotImplementedError()
    
    def rotate_page(self, page_number : int, rotation : groupdocs.viewer.options.Rotation) -> None:
        '''Applies the clockwise rotation to a page.
        
        :param page_number: The page number, must be strictly greater than 0
        :param rotation: The rotation value.'''
        raise NotImplementedError()
    
    @property
    def render_comments(self) -> bool:
        '''Enables rendering comments.'''
        raise NotImplementedError()
    
    @render_comments.setter
    def render_comments(self, value : bool) -> None:
        '''Enables rendering comments.'''
        raise NotImplementedError()
    
    @property
    def render_notes(self) -> bool:
        '''Enables rendering notes.'''
        raise NotImplementedError()
    
    @render_notes.setter
    def render_notes(self, value : bool) -> None:
        '''Enables rendering notes.'''
        raise NotImplementedError()
    
    @property
    def render_hidden_pages(self) -> bool:
        '''Enables rendering of hidden pages.'''
        raise NotImplementedError()
    
    @render_hidden_pages.setter
    def render_hidden_pages(self, value : bool) -> None:
        '''Enables rendering of hidden pages.'''
        raise NotImplementedError()
    
    @property
    def default_font_name(self) -> str:
        '''Sets the default font for a document.'''
        raise NotImplementedError()
    
    @default_font_name.setter
    def default_font_name(self, value : str) -> None:
        '''Sets the default font for a document.'''
        raise NotImplementedError()
    
    @property
    def archive_options(self) -> groupdocs.viewer.options.ArchiveOptions:
        '''The archive files view options.'''
        raise NotImplementedError()
    
    @archive_options.setter
    def archive_options(self, value : groupdocs.viewer.options.ArchiveOptions) -> None:
        '''The archive files view options.'''
        raise NotImplementedError()
    
    @property
    def cad_options(self) -> groupdocs.viewer.options.CadOptions:
        '''The CAD drawing view options.'''
        raise NotImplementedError()
    
    @cad_options.setter
    def cad_options(self, value : groupdocs.viewer.options.CadOptions) -> None:
        '''The CAD drawing view options.'''
        raise NotImplementedError()
    
    @property
    def email_options(self) -> groupdocs.viewer.options.EmailOptions:
        '''The email messages view options.'''
        raise NotImplementedError()
    
    @email_options.setter
    def email_options(self, value : groupdocs.viewer.options.EmailOptions) -> None:
        '''The email messages view options.'''
        raise NotImplementedError()
    
    @property
    def outlook_options(self) -> groupdocs.viewer.options.OutlookOptions:
        '''The Microsoft Outlook data files view options.'''
        raise NotImplementedError()
    
    @outlook_options.setter
    def outlook_options(self, value : groupdocs.viewer.options.OutlookOptions) -> None:
        '''The Microsoft Outlook data files view options.'''
        raise NotImplementedError()
    
    @property
    def mail_storage_options(self) -> groupdocs.viewer.options.MailStorageOptions:
        '''Mail storage data files view options.'''
        raise NotImplementedError()
    
    @mail_storage_options.setter
    def mail_storage_options(self, value : groupdocs.viewer.options.MailStorageOptions) -> None:
        '''Mail storage data files view options.'''
        raise NotImplementedError()
    
    @property
    def pdf_options(self) -> groupdocs.viewer.options.PdfOptions:
        '''The PDF document view options.'''
        raise NotImplementedError()
    
    @pdf_options.setter
    def pdf_options(self, value : groupdocs.viewer.options.PdfOptions) -> None:
        '''The PDF document view options.'''
        raise NotImplementedError()
    
    @property
    def project_management_options(self) -> groupdocs.viewer.options.ProjectManagementOptions:
        '''The project management files view options.'''
        raise NotImplementedError()
    
    @project_management_options.setter
    def project_management_options(self, value : groupdocs.viewer.options.ProjectManagementOptions) -> None:
        '''The project management files view options.'''
        raise NotImplementedError()
    
    @property
    def spreadsheet_options(self) -> groupdocs.viewer.options.SpreadsheetOptions:
        '''The spreadsheet files view options.'''
        raise NotImplementedError()
    
    @spreadsheet_options.setter
    def spreadsheet_options(self, value : groupdocs.viewer.options.SpreadsheetOptions) -> None:
        '''The spreadsheet files view options.'''
        raise NotImplementedError()
    
    @property
    def word_processing_options(self) -> groupdocs.viewer.options.WordProcessingOptions:
        '''The Word processing files view options.'''
        raise NotImplementedError()
    
    @word_processing_options.setter
    def word_processing_options(self, value : groupdocs.viewer.options.WordProcessingOptions) -> None:
        '''The Word processing files view options.'''
        raise NotImplementedError()
    
    @property
    def visio_rendering_options(self) -> groupdocs.viewer.options.VisioRenderingOptions:
        '''The Visio files view options.'''
        raise NotImplementedError()
    
    @visio_rendering_options.setter
    def visio_rendering_options(self, value : groupdocs.viewer.options.VisioRenderingOptions) -> None:
        '''The Visio files view options.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> groupdocs.viewer.options.TextOptions:
        '''Text files view options.'''
        raise NotImplementedError()
    
    @text_options.setter
    def text_options(self, value : groupdocs.viewer.options.TextOptions) -> None:
        '''Text files view options.'''
        raise NotImplementedError()
    
    @property
    def presentation_options(self) -> groupdocs.viewer.options.PresentationOptions:
        '''The presentation files view options.'''
        raise NotImplementedError()
    
    @presentation_options.setter
    def presentation_options(self, value : groupdocs.viewer.options.PresentationOptions) -> None:
        '''The presentation files view options.'''
        raise NotImplementedError()
    
    @property
    def web_document_options(self) -> groupdocs.viewer.options.WebDocumentOptions:
        '''The Web files view options.'''
        raise NotImplementedError()
    
    @web_document_options.setter
    def web_document_options(self, value : groupdocs.viewer.options.WebDocumentOptions) -> None:
        '''The Web files view options.'''
        raise NotImplementedError()
    
    @property
    def watermark(self) -> groupdocs.viewer.options.Watermark:
        '''The text watermark to be applied to each page.'''
        raise NotImplementedError()
    
    @watermark.setter
    def watermark(self, value : groupdocs.viewer.options.Watermark) -> None:
        '''The text watermark to be applied to each page.'''
        raise NotImplementedError()
    
    @property
    def quality(self) -> int:
        '''Sets the quality of the output image.'''
        raise NotImplementedError()
    
    @quality.setter
    def quality(self, value : int) -> None:
        '''Sets the quality of the output image.'''
        raise NotImplementedError()
    
    @property
    def extract_text(self) -> bool:
        '''Enables text extraction.'''
        raise NotImplementedError()
    
    @extract_text.setter
    def extract_text(self, value : bool) -> None:
        '''Enables text extraction.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''Sets the width of the output image (in pixels).'''
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : int) -> None:
        '''Sets the width of the output image (in pixels).'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''Sets the height of an output image (in pixels).'''
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : int) -> None:
        '''Sets the height of an output image (in pixels).'''
        raise NotImplementedError()
    
    @property
    def max_width(self) -> int:
        '''Sets the maximum width of an output image (in pixels).'''
        raise NotImplementedError()
    
    @max_width.setter
    def max_width(self, value : int) -> None:
        '''Sets the maximum width of an output image (in pixels).'''
        raise NotImplementedError()
    
    @property
    def max_height(self) -> int:
        '''Sets the maximum height of an output image (in pixels).'''
        raise NotImplementedError()
    
    @max_height.setter
    def max_height(self, value : int) -> None:
        '''Sets the maximum height of an output image (in pixels).'''
        raise NotImplementedError()
    

class LoadOptions:
    '''Contains options that used to open the file. For details, see this `page <https://docs.groupdocs.com/viewer/net/loading/>` and its children.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.LoadOptions` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_type : groupdocs.viewer.FileType) -> None:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.LoadOptions` class.
        
        :param file_type: The type of the file to open.'''
        raise NotImplementedError()
    
    @property
    def file_type(self) -> groupdocs.viewer.FileType:
        '''Sets the type of the file to open.'''
        raise NotImplementedError()
    
    @file_type.setter
    def file_type(self, value : groupdocs.viewer.FileType) -> None:
        '''Sets the type of the file to open.'''
        raise NotImplementedError()
    
    @property
    def password(self) -> str:
        '''Sets the password to open encrypted file.'''
        raise NotImplementedError()
    
    @password.setter
    def password(self, value : str) -> None:
        '''Sets the password to open encrypted file.'''
        raise NotImplementedError()
    
    @property
    def encoding(self) -> str:
        '''Sets the encoding used when opening text-based files or email messages such as
        :py:attr:`groupdocs.viewer.FileType.CSV`,
        :py:attr:`groupdocs.viewer.FileType.TXT`,
        and :py:attr:`groupdocs.viewer.FileType.MSG`.
        Default value is :py:attr:`str.UTF8`.'''
        raise NotImplementedError()
    
    @encoding.setter
    def encoding(self, value : str) -> None:
        '''Sets the encoding used when opening text-based files or email messages such as
        :py:attr:`groupdocs.viewer.FileType.CSV`,
        :py:attr:`groupdocs.viewer.FileType.TXT`,
        and :py:attr:`groupdocs.viewer.FileType.MSG`.
        Default value is :py:attr:`str.UTF8`.'''
        raise NotImplementedError()
    
    @property
    def detect_encoding(self) -> bool:
        '''Enables the encoding detection for the :py:attr:`groupdocs.viewer.FileType.TXT`, :py:attr:`groupdocs.viewer.FileType.CSV`, and :py:attr:`groupdocs.viewer.FileType.TSV` files.'''
        raise NotImplementedError()
    
    @detect_encoding.setter
    def detect_encoding(self, value : bool) -> None:
        '''Enables the encoding detection for the :py:attr:`groupdocs.viewer.FileType.TXT`, :py:attr:`groupdocs.viewer.FileType.CSV`, and :py:attr:`groupdocs.viewer.FileType.TSV` files.'''
        raise NotImplementedError()
    
    @property
    def resource_loading_timeout(self) -> System.TimeSpan:
        '''Sets the timeout to load external resources.'''
        raise NotImplementedError()
    
    @resource_loading_timeout.setter
    def resource_loading_timeout(self, value : System.TimeSpan) -> None:
        '''Sets the timeout to load external resources.'''
        raise NotImplementedError()
    
    @property
    def skip_external_resources(self) -> bool:
        '''Disables loading of all external resource such as images except :py:attr:`groupdocs.viewer.options.LoadOptions.whitelisted_resources`.'''
        raise NotImplementedError()
    
    @skip_external_resources.setter
    def skip_external_resources(self, value : bool) -> None:
        '''Disables loading of all external resource such as images except :py:attr:`groupdocs.viewer.options.LoadOptions.whitelisted_resources`.'''
        raise NotImplementedError()
    
    @property
    def whitelisted_resources(self) -> System.Collections.Generic.List`1[[System.String]]:
        '''The list of URL fragments corresponding to external resources that should be loaded
        when :py:attr:`groupdocs.viewer.options.LoadOptions.skip_external_resources` is set to ``true``.'''
        raise NotImplementedError()
    
    @whitelisted_resources.setter
    def whitelisted_resources(self, value : System.Collections.Generic.List`1[[System.String]]) -> None:
        '''The list of URL fragments corresponding to external resources that should be loaded
        when :py:attr:`groupdocs.viewer.options.LoadOptions.skip_external_resources` is set to ``true``.'''
        raise NotImplementedError()
    
    @property
    def try_repair(self) -> bool:
        '''When enabled GroupDocs.Viewer tries to repair structural corruption in PDF documents.
        Default value is `false`.'''
        raise NotImplementedError()
    
    @try_repair.setter
    def try_repair(self, value : bool) -> None:
        '''When enabled GroupDocs.Viewer tries to repair structural corruption in PDF documents.
        Default value is `false`.'''
        raise NotImplementedError()
    

class MailStorageOptions:
    '''Contains options for rendering Mail storage (Lotus Notes, MBox) data files. For details, see the `documentation <https://docs.groupdocs.com/viewer/net/render-lotus-notes-database-files/#specify-rendering-options>`.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def text_filter(self) -> str:
        '''Sets the keywords used to filter messages.'''
        raise NotImplementedError()
    
    @text_filter.setter
    def text_filter(self, value : str) -> None:
        '''Sets the keywords used to filter messages.'''
        raise NotImplementedError()
    
    @property
    def address_filter(self) -> str:
        '''Sets the email-address used to filter messages by sender or recipient.'''
        raise NotImplementedError()
    
    @address_filter.setter
    def address_filter(self, value : str) -> None:
        '''Sets the email-address used to filter messages by sender or recipient.'''
        raise NotImplementedError()
    
    @property
    def max_items(self) -> int:
        '''Sets the maximum number of messages or items to render.'''
        raise NotImplementedError()
    
    @max_items.setter
    def max_items(self, value : int) -> None:
        '''Sets the maximum number of messages or items to render.'''
        raise NotImplementedError()
    

class OutlookOptions:
    '''Contains options for rendering Outlook data files. For details, see the `documentation <https://docs.groupdocs.com/viewer/net/render-lotus-notes-database-files/#specify-rendering-options>`.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def folder(self) -> str:
        '''Sets the name of the folder (e.g. Inbox, Sent Item or Deleted Items) to render.'''
        raise NotImplementedError()
    
    @folder.setter
    def folder(self, value : str) -> None:
        '''Sets the name of the folder (e.g. Inbox, Sent Item or Deleted Items) to render.'''
        raise NotImplementedError()
    
    @property
    def text_filter(self) -> str:
        '''Sets the keywords used to filter messages.'''
        raise NotImplementedError()
    
    @text_filter.setter
    def text_filter(self, value : str) -> None:
        '''Sets the keywords used to filter messages.'''
        raise NotImplementedError()
    
    @property
    def address_filter(self) -> str:
        '''Sets the email-address used to filter messages by sender or recipient.'''
        raise NotImplementedError()
    
    @address_filter.setter
    def address_filter(self, value : str) -> None:
        '''Sets the email-address used to filter messages by sender or recipient.'''
        raise NotImplementedError()
    
    @property
    def max_items_in_folder(self) -> int:
        '''The maximum number of messages or items, that can be rendered from one folder.'''
        raise NotImplementedError()
    
    @max_items_in_folder.setter
    def max_items_in_folder(self, value : int) -> None:
        '''The maximum number of messages or items, that can be rendered from one folder.'''
        raise NotImplementedError()
    

class PdfOptimizationOptions:
    '''Contains the PDF optimization options to apply to the output PDF file. For details and code samples, see this `page <https://docs.groupdocs.com/viewer/net/optimization-pdf-options/>` and its children.'''
    
    def __init__(self) -> None:
        '''Sets up default values of MaxResolution option to 300 and ImageQuality option to 100'''
        raise NotImplementedError()
    
    @property
    def lineriaze(self) -> bool:
        '''Enables optimization the output PDF file for viewing online with a web browser.'''
        raise NotImplementedError()
    
    @lineriaze.setter
    def lineriaze(self, value : bool) -> None:
        '''Enables optimization the output PDF file for viewing online with a web browser.'''
        raise NotImplementedError()
    
    @property
    def remove_annotations(self) -> bool:
        '''Enables removing annotation from the output PDF file.'''
        raise NotImplementedError()
    
    @remove_annotations.setter
    def remove_annotations(self, value : bool) -> None:
        '''Enables removing annotation from the output PDF file.'''
        raise NotImplementedError()
    
    @property
    def remove_form_fields(self) -> bool:
        '''Enables removing form fields from a PDF file.'''
        raise NotImplementedError()
    
    @remove_form_fields.setter
    def remove_form_fields(self, value : bool) -> None:
        '''Enables removing form fields from a PDF file.'''
        raise NotImplementedError()
    
    @property
    def convert_to_gray_scale(self) -> bool:
        '''Enables converting the output PDF file to a grayscale.'''
        raise NotImplementedError()
    
    @convert_to_gray_scale.setter
    def convert_to_gray_scale(self, value : bool) -> None:
        '''Enables converting the output PDF file to a grayscale.'''
        raise NotImplementedError()
    
    @property
    def subset_fonts(self) -> bool:
        '''Subsets fonts in the output PDF file.'''
        raise NotImplementedError()
    
    @subset_fonts.setter
    def subset_fonts(self, value : bool) -> None:
        '''Subsets fonts in the output PDF file.'''
        raise NotImplementedError()
    
    @property
    def compress_images(self) -> bool:
        '''Enables compressing images in the output PDF file.'''
        raise NotImplementedError()
    
    @compress_images.setter
    def compress_images(self, value : bool) -> None:
        '''Enables compressing images in the output PDF file.'''
        raise NotImplementedError()
    
    @property
    def image_quality(self) -> int:
        '''Sets the image quality in the output PDF file (in percent).'''
        raise NotImplementedError()
    
    @image_quality.setter
    def image_quality(self, value : int) -> None:
        '''Sets the image quality in the output PDF file (in percent).'''
        raise NotImplementedError()
    
    @property
    def resize_images(self) -> bool:
        '''Enables setting the maximum resolution in the output PDF file.'''
        raise NotImplementedError()
    
    @resize_images.setter
    def resize_images(self, value : bool) -> None:
        '''Enables setting the maximum resolution in the output PDF file.'''
        raise NotImplementedError()
    
    @property
    def max_resolution(self) -> int:
        '''Sets the maximum resolution in the output PDF file.'''
        raise NotImplementedError()
    
    @max_resolution.setter
    def max_resolution(self, value : int) -> None:
        '''Sets the maximum resolution in the output PDF file.'''
        raise NotImplementedError()
    
    @property
    def optimize_spreadsheets(self) -> bool:
        '''Enables optimization of spreadsheets in the PDF files.'''
        raise NotImplementedError()
    
    @optimize_spreadsheets.setter
    def optimize_spreadsheets(self, value : bool) -> None:
        '''Enables optimization of spreadsheets in the PDF files.'''
        raise NotImplementedError()
    
    @property
    def remove_unused_objects(self) -> bool:
        '''Removes unused (orphaned) objects from a PDF file, which are placed in the PDF document, but are not referenced from resource dictionaries of any page and thus are not used at all. Activating this property (``true``) will decrease the output PDF document size. By default is disabled (``false``).'''
        raise NotImplementedError()
    
    @remove_unused_objects.setter
    def remove_unused_objects(self, value : bool) -> None:
        '''Removes unused (orphaned) objects from a PDF file, which are placed in the PDF document, but are not referenced from resource dictionaries of any page and thus are not used at all. Activating this property (``true``) will decrease the output PDF document size. By default is disabled (``false``).'''
        raise NotImplementedError()
    
    @property
    def remove_unused_streams(self) -> bool:
        '''Removes unused (orphaned) streams from a PDF file, which are still referenced from the resource dictionary of the page, but actually are never used in the page contents. By default is disabled (``false``), its enabling (``true``) will decrease the output PDF document size.'''
        raise NotImplementedError()
    
    @remove_unused_streams.setter
    def remove_unused_streams(self, value : bool) -> None:
        '''Removes unused (orphaned) streams from a PDF file, which are still referenced from the resource dictionary of the page, but actually are never used in the page contents. By default is disabled (``false``), its enabling (``true``) will decrease the output PDF document size.'''
        raise NotImplementedError()
    

class PdfOptions:
    '''Contains options for rendering to PDF documents. For details, see the `documentation <https://docs.groupdocs.com/viewer/net/render-pdf-documents/>`.'''
    
    def __init__(self) -> None:
        '''Initializes new instance of the :py:class:`groupdocs.viewer.options.PdfOptions` class.'''
        raise NotImplementedError()
    
    @property
    def disable_chars_grouping(self) -> bool:
        '''Disables symbol grouping for precise symbol positioning during page rendering.'''
        raise NotImplementedError()
    
    @disable_chars_grouping.setter
    def disable_chars_grouping(self, value : bool) -> None:
        '''Disables symbol grouping for precise symbol positioning during page rendering.'''
        raise NotImplementedError()
    
    @property
    def enable_layered_rendering(self) -> bool:
        '''Enables rendering text and graphics in the original PDF document\'s z-order when rendering to HTML.'''
        raise NotImplementedError()
    
    @enable_layered_rendering.setter
    def enable_layered_rendering(self, value : bool) -> None:
        '''Enables rendering text and graphics in the original PDF document\'s z-order when rendering to HTML.'''
        raise NotImplementedError()
    
    @property
    def enable_font_hinting(self) -> bool:
        '''Enables font hinting.'''
        raise NotImplementedError()
    
    @enable_font_hinting.setter
    def enable_font_hinting(self, value : bool) -> None:
        '''Enables font hinting.'''
        raise NotImplementedError()
    
    @property
    def render_original_page_size(self) -> bool:
        '''Sets the output page size the same as the source PDF document\'s page size.'''
        raise NotImplementedError()
    
    @render_original_page_size.setter
    def render_original_page_size(self, value : bool) -> None:
        '''Sets the output page size the same as the source PDF document\'s page size.'''
        raise NotImplementedError()
    
    @property
    def image_quality(self) -> groupdocs.viewer.options.ImageQuality:
        '''Sets the output image quality for image resources when rendering to HTML. The default quality is ``Low``.'''
        raise NotImplementedError()
    
    @image_quality.setter
    def image_quality(self, value : groupdocs.viewer.options.ImageQuality) -> None:
        '''Sets the output image quality for image resources when rendering to HTML. The default quality is ``Low``.'''
        raise NotImplementedError()
    
    @property
    def render_text_as_image(self) -> bool:
        '''Enables rendering texts in the PDF files as an image in the HTML output.'''
        raise NotImplementedError()
    
    @render_text_as_image.setter
    def render_text_as_image(self, value : bool) -> None:
        '''Enables rendering texts in the PDF files as an image in the HTML output.'''
        raise NotImplementedError()
    
    @property
    def fixed_layout(self) -> bool:
        '''Enables rendering the PDF and EPUB documents to HTML with a fixed layout.'''
        raise NotImplementedError()
    
    @fixed_layout.setter
    def fixed_layout(self, value : bool) -> None:
        '''Enables rendering the PDF and EPUB documents to HTML with a fixed layout.'''
        raise NotImplementedError()
    
    @property
    def wrap_images_in_svg(self) -> bool:
        '''Enables wrapping each image in the output HTML document in SVG tag to improve the output quality.'''
        raise NotImplementedError()
    
    @wrap_images_in_svg.setter
    def wrap_images_in_svg(self, value : bool) -> None:
        '''Enables wrapping each image in the output HTML document in SVG tag to improve the output quality.'''
        raise NotImplementedError()
    
    @property
    def disable_font_license_verifications(self) -> bool:
        '''Disables any license restrictions for all fonts in the current XPS/OXPS document.'''
        raise NotImplementedError()
    
    @disable_font_license_verifications.setter
    def disable_font_license_verifications(self, value : bool) -> None:
        '''Disables any license restrictions for all fonts in the current XPS/OXPS document.'''
        raise NotImplementedError()
    
    @property
    def disable_copy_protection(self) -> bool:
        '''Turns off content copy protection when rendering to HTML.'''
        raise NotImplementedError()
    
    @disable_copy_protection.setter
    def disable_copy_protection(self, value : bool) -> None:
        '''Turns off content copy protection when rendering to HTML.'''
        raise NotImplementedError()
    
    @property
    def fix_link_issue(self) -> bool:
        '''Tries to fix the issue when whole HTML page content is a link. Works only when input format is PDF and output format is HTML (with embedded or external resources). By default is disabled (``false``). Turn it on only when you know what and why you\'re doing. Turing this option on increases the document processing time.'''
        raise NotImplementedError()
    
    @fix_link_issue.setter
    def fix_link_issue(self, value : bool) -> None:
        '''Tries to fix the issue when whole HTML page content is a link. Works only when input format is PDF and output format is HTML (with embedded or external resources). By default is disabled (``false``). Turn it on only when you know what and why you\'re doing. Turing this option on increases the document processing time.'''
        raise NotImplementedError()
    

class PdfViewOptions(ViewOptions):
    '''Contains options for rendering documents into PDF format.
    For details, see the `documentation <https://docs.groupdocs.com/viewer/net/rendering-to-pdf/>`.'''
    
    @overload
    def __init__(self, file_stream_factory : groupdocs.viewer.interfaces.IFileStreamFactory) -> None:
        '''Initializes an instance of :py:class:`groupdocs.viewer.options.PdfViewOptions` class.
        
        :param file_stream_factory: The factory which implements methods for creating and releasing output file stream.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self) -> None:
        '''Initializes an instance of :py:class:`groupdocs.viewer.options.PdfViewOptions` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, output_file_path : str) -> None:
        '''Initializes an instance of :py:class:`groupdocs.viewer.options.PdfViewOptions` class.
        
        :param output_file_path: The path for output PDF file.'''
        raise NotImplementedError()
    
    def rotate_page(self, page_number : int, rotation : groupdocs.viewer.options.Rotation) -> None:
        '''Applies the clockwise rotation to a page.
        
        :param page_number: The page number, must be strictly greater than 0
        :param rotation: The rotation value.'''
        raise NotImplementedError()
    
    @property
    def render_comments(self) -> bool:
        '''Enables rendering comments.'''
        raise NotImplementedError()
    
    @render_comments.setter
    def render_comments(self, value : bool) -> None:
        '''Enables rendering comments.'''
        raise NotImplementedError()
    
    @property
    def render_notes(self) -> bool:
        '''Enables rendering notes.'''
        raise NotImplementedError()
    
    @render_notes.setter
    def render_notes(self, value : bool) -> None:
        '''Enables rendering notes.'''
        raise NotImplementedError()
    
    @property
    def render_hidden_pages(self) -> bool:
        '''Enables rendering of hidden pages.'''
        raise NotImplementedError()
    
    @render_hidden_pages.setter
    def render_hidden_pages(self, value : bool) -> None:
        '''Enables rendering of hidden pages.'''
        raise NotImplementedError()
    
    @property
    def default_font_name(self) -> str:
        '''Sets the default font for a document.'''
        raise NotImplementedError()
    
    @default_font_name.setter
    def default_font_name(self, value : str) -> None:
        '''Sets the default font for a document.'''
        raise NotImplementedError()
    
    @property
    def archive_options(self) -> groupdocs.viewer.options.ArchiveOptions:
        '''The archive files view options.'''
        raise NotImplementedError()
    
    @archive_options.setter
    def archive_options(self, value : groupdocs.viewer.options.ArchiveOptions) -> None:
        '''The archive files view options.'''
        raise NotImplementedError()
    
    @property
    def cad_options(self) -> groupdocs.viewer.options.CadOptions:
        '''The CAD drawing view options.'''
        raise NotImplementedError()
    
    @cad_options.setter
    def cad_options(self, value : groupdocs.viewer.options.CadOptions) -> None:
        '''The CAD drawing view options.'''
        raise NotImplementedError()
    
    @property
    def email_options(self) -> groupdocs.viewer.options.EmailOptions:
        '''The email messages view options.'''
        raise NotImplementedError()
    
    @email_options.setter
    def email_options(self, value : groupdocs.viewer.options.EmailOptions) -> None:
        '''The email messages view options.'''
        raise NotImplementedError()
    
    @property
    def outlook_options(self) -> groupdocs.viewer.options.OutlookOptions:
        '''The Microsoft Outlook data files view options.'''
        raise NotImplementedError()
    
    @outlook_options.setter
    def outlook_options(self, value : groupdocs.viewer.options.OutlookOptions) -> None:
        '''The Microsoft Outlook data files view options.'''
        raise NotImplementedError()
    
    @property
    def mail_storage_options(self) -> groupdocs.viewer.options.MailStorageOptions:
        '''Mail storage data files view options.'''
        raise NotImplementedError()
    
    @mail_storage_options.setter
    def mail_storage_options(self, value : groupdocs.viewer.options.MailStorageOptions) -> None:
        '''Mail storage data files view options.'''
        raise NotImplementedError()
    
    @property
    def pdf_options(self) -> groupdocs.viewer.options.PdfOptions:
        '''The PDF document view options.'''
        raise NotImplementedError()
    
    @pdf_options.setter
    def pdf_options(self, value : groupdocs.viewer.options.PdfOptions) -> None:
        '''The PDF document view options.'''
        raise NotImplementedError()
    
    @property
    def project_management_options(self) -> groupdocs.viewer.options.ProjectManagementOptions:
        '''The project management files view options.'''
        raise NotImplementedError()
    
    @project_management_options.setter
    def project_management_options(self, value : groupdocs.viewer.options.ProjectManagementOptions) -> None:
        '''The project management files view options.'''
        raise NotImplementedError()
    
    @property
    def spreadsheet_options(self) -> groupdocs.viewer.options.SpreadsheetOptions:
        '''The spreadsheet files view options.'''
        raise NotImplementedError()
    
    @spreadsheet_options.setter
    def spreadsheet_options(self, value : groupdocs.viewer.options.SpreadsheetOptions) -> None:
        '''The spreadsheet files view options.'''
        raise NotImplementedError()
    
    @property
    def word_processing_options(self) -> groupdocs.viewer.options.WordProcessingOptions:
        '''The Word processing files view options.'''
        raise NotImplementedError()
    
    @word_processing_options.setter
    def word_processing_options(self, value : groupdocs.viewer.options.WordProcessingOptions) -> None:
        '''The Word processing files view options.'''
        raise NotImplementedError()
    
    @property
    def visio_rendering_options(self) -> groupdocs.viewer.options.VisioRenderingOptions:
        '''The Visio files view options.'''
        raise NotImplementedError()
    
    @visio_rendering_options.setter
    def visio_rendering_options(self, value : groupdocs.viewer.options.VisioRenderingOptions) -> None:
        '''The Visio files view options.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> groupdocs.viewer.options.TextOptions:
        '''Text files view options.'''
        raise NotImplementedError()
    
    @text_options.setter
    def text_options(self, value : groupdocs.viewer.options.TextOptions) -> None:
        '''Text files view options.'''
        raise NotImplementedError()
    
    @property
    def presentation_options(self) -> groupdocs.viewer.options.PresentationOptions:
        '''The presentation files view options.'''
        raise NotImplementedError()
    
    @presentation_options.setter
    def presentation_options(self, value : groupdocs.viewer.options.PresentationOptions) -> None:
        '''The presentation files view options.'''
        raise NotImplementedError()
    
    @property
    def web_document_options(self) -> groupdocs.viewer.options.WebDocumentOptions:
        '''The Web files view options.'''
        raise NotImplementedError()
    
    @web_document_options.setter
    def web_document_options(self, value : groupdocs.viewer.options.WebDocumentOptions) -> None:
        '''The Web files view options.'''
        raise NotImplementedError()
    
    @property
    def watermark(self) -> groupdocs.viewer.options.Watermark:
        '''The text watermark to be applied to each page.'''
        raise NotImplementedError()
    
    @watermark.setter
    def watermark(self, value : groupdocs.viewer.options.Watermark) -> None:
        '''The text watermark to be applied to each page.'''
        raise NotImplementedError()
    
    @property
    def security(self) -> groupdocs.viewer.options.Security:
        '''Sets the output PDF document security options.'''
        raise NotImplementedError()
    
    @security.setter
    def security(self, value : groupdocs.viewer.options.Security) -> None:
        '''Sets the output PDF document security options.'''
        raise NotImplementedError()
    
    @property
    def pdf_optimization_options(self) -> groupdocs.viewer.options.PdfOptimizationOptions:
        '''Reduces output PDF file size by applying optimization techniques with different options.'''
        raise NotImplementedError()
    
    @pdf_optimization_options.setter
    def pdf_optimization_options(self, value : groupdocs.viewer.options.PdfOptimizationOptions) -> None:
        '''Reduces output PDF file size by applying optimization techniques with different options.'''
        raise NotImplementedError()
    
    @property
    def image_max_width(self) -> int:
        '''Sets the maximum width of an output image (in pixels).'''
        raise NotImplementedError()
    
    @image_max_width.setter
    def image_max_width(self, value : int) -> None:
        '''Sets the maximum width of an output image (in pixels).'''
        raise NotImplementedError()
    
    @property
    def image_max_height(self) -> int:
        '''Sets the maximum height of an output image (in pixels).'''
        raise NotImplementedError()
    
    @image_max_height.setter
    def image_max_height(self, value : int) -> None:
        '''Sets the maximum height of an output image (in pixels).'''
        raise NotImplementedError()
    
    @property
    def image_width(self) -> int:
        '''Sets the width of an output image (in pixels).'''
        raise NotImplementedError()
    
    @image_width.setter
    def image_width(self, value : int) -> None:
        '''Sets the width of an output image (in pixels).'''
        raise NotImplementedError()
    
    @property
    def image_height(self) -> int:
        '''Sets the height of an output image (in pixels).'''
        raise NotImplementedError()
    
    @image_height.setter
    def image_height(self, value : int) -> None:
        '''Sets the height of an output image (in pixels).'''
        raise NotImplementedError()
    

class PngViewOptions(ViewOptions):
    '''Contains options for rendering documents into PNG format.  For details, see this `page <https://docs.groupdocs.com/viewer/net/rendering-to-png-or-jpeg/>` and its children.'''
    
    @overload
    def __init__(self, page_stream_factory : groupdocs.viewer.interfaces.IPageStreamFactory) -> None:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.PngViewOptions` class.
        
        :param page_stream_factory: The factory which implements methods for creating and releasing output page stream.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self) -> None:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.PngViewOptions` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_path_format : str) -> None:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.PngViewOptions` class.
        
        :param file_path_format: The file path format e.g. \'page_{0}.png\'.'''
        raise NotImplementedError()
    
    def rotate_page(self, page_number : int, rotation : groupdocs.viewer.options.Rotation) -> None:
        '''Applies the clockwise rotation to a page.
        
        :param page_number: The page number, must be strictly greater than 0
        :param rotation: The rotation value.'''
        raise NotImplementedError()
    
    @property
    def render_comments(self) -> bool:
        '''Enables rendering comments.'''
        raise NotImplementedError()
    
    @render_comments.setter
    def render_comments(self, value : bool) -> None:
        '''Enables rendering comments.'''
        raise NotImplementedError()
    
    @property
    def render_notes(self) -> bool:
        '''Enables rendering notes.'''
        raise NotImplementedError()
    
    @render_notes.setter
    def render_notes(self, value : bool) -> None:
        '''Enables rendering notes.'''
        raise NotImplementedError()
    
    @property
    def render_hidden_pages(self) -> bool:
        '''Enables rendering of hidden pages.'''
        raise NotImplementedError()
    
    @render_hidden_pages.setter
    def render_hidden_pages(self, value : bool) -> None:
        '''Enables rendering of hidden pages.'''
        raise NotImplementedError()
    
    @property
    def default_font_name(self) -> str:
        '''Sets the default font for a document.'''
        raise NotImplementedError()
    
    @default_font_name.setter
    def default_font_name(self, value : str) -> None:
        '''Sets the default font for a document.'''
        raise NotImplementedError()
    
    @property
    def archive_options(self) -> groupdocs.viewer.options.ArchiveOptions:
        '''The archive files view options.'''
        raise NotImplementedError()
    
    @archive_options.setter
    def archive_options(self, value : groupdocs.viewer.options.ArchiveOptions) -> None:
        '''The archive files view options.'''
        raise NotImplementedError()
    
    @property
    def cad_options(self) -> groupdocs.viewer.options.CadOptions:
        '''The CAD drawing view options.'''
        raise NotImplementedError()
    
    @cad_options.setter
    def cad_options(self, value : groupdocs.viewer.options.CadOptions) -> None:
        '''The CAD drawing view options.'''
        raise NotImplementedError()
    
    @property
    def email_options(self) -> groupdocs.viewer.options.EmailOptions:
        '''The email messages view options.'''
        raise NotImplementedError()
    
    @email_options.setter
    def email_options(self, value : groupdocs.viewer.options.EmailOptions) -> None:
        '''The email messages view options.'''
        raise NotImplementedError()
    
    @property
    def outlook_options(self) -> groupdocs.viewer.options.OutlookOptions:
        '''The Microsoft Outlook data files view options.'''
        raise NotImplementedError()
    
    @outlook_options.setter
    def outlook_options(self, value : groupdocs.viewer.options.OutlookOptions) -> None:
        '''The Microsoft Outlook data files view options.'''
        raise NotImplementedError()
    
    @property
    def mail_storage_options(self) -> groupdocs.viewer.options.MailStorageOptions:
        '''Mail storage data files view options.'''
        raise NotImplementedError()
    
    @mail_storage_options.setter
    def mail_storage_options(self, value : groupdocs.viewer.options.MailStorageOptions) -> None:
        '''Mail storage data files view options.'''
        raise NotImplementedError()
    
    @property
    def pdf_options(self) -> groupdocs.viewer.options.PdfOptions:
        '''The PDF document view options.'''
        raise NotImplementedError()
    
    @pdf_options.setter
    def pdf_options(self, value : groupdocs.viewer.options.PdfOptions) -> None:
        '''The PDF document view options.'''
        raise NotImplementedError()
    
    @property
    def project_management_options(self) -> groupdocs.viewer.options.ProjectManagementOptions:
        '''The project management files view options.'''
        raise NotImplementedError()
    
    @project_management_options.setter
    def project_management_options(self, value : groupdocs.viewer.options.ProjectManagementOptions) -> None:
        '''The project management files view options.'''
        raise NotImplementedError()
    
    @property
    def spreadsheet_options(self) -> groupdocs.viewer.options.SpreadsheetOptions:
        '''The spreadsheet files view options.'''
        raise NotImplementedError()
    
    @spreadsheet_options.setter
    def spreadsheet_options(self, value : groupdocs.viewer.options.SpreadsheetOptions) -> None:
        '''The spreadsheet files view options.'''
        raise NotImplementedError()
    
    @property
    def word_processing_options(self) -> groupdocs.viewer.options.WordProcessingOptions:
        '''The Word processing files view options.'''
        raise NotImplementedError()
    
    @word_processing_options.setter
    def word_processing_options(self, value : groupdocs.viewer.options.WordProcessingOptions) -> None:
        '''The Word processing files view options.'''
        raise NotImplementedError()
    
    @property
    def visio_rendering_options(self) -> groupdocs.viewer.options.VisioRenderingOptions:
        '''The Visio files view options.'''
        raise NotImplementedError()
    
    @visio_rendering_options.setter
    def visio_rendering_options(self, value : groupdocs.viewer.options.VisioRenderingOptions) -> None:
        '''The Visio files view options.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> groupdocs.viewer.options.TextOptions:
        '''Text files view options.'''
        raise NotImplementedError()
    
    @text_options.setter
    def text_options(self, value : groupdocs.viewer.options.TextOptions) -> None:
        '''Text files view options.'''
        raise NotImplementedError()
    
    @property
    def presentation_options(self) -> groupdocs.viewer.options.PresentationOptions:
        '''The presentation files view options.'''
        raise NotImplementedError()
    
    @presentation_options.setter
    def presentation_options(self, value : groupdocs.viewer.options.PresentationOptions) -> None:
        '''The presentation files view options.'''
        raise NotImplementedError()
    
    @property
    def web_document_options(self) -> groupdocs.viewer.options.WebDocumentOptions:
        '''The Web files view options.'''
        raise NotImplementedError()
    
    @web_document_options.setter
    def web_document_options(self, value : groupdocs.viewer.options.WebDocumentOptions) -> None:
        '''The Web files view options.'''
        raise NotImplementedError()
    
    @property
    def watermark(self) -> groupdocs.viewer.options.Watermark:
        '''The text watermark to be applied to each page.'''
        raise NotImplementedError()
    
    @watermark.setter
    def watermark(self, value : groupdocs.viewer.options.Watermark) -> None:
        '''The text watermark to be applied to each page.'''
        raise NotImplementedError()
    
    @property
    def extract_text(self) -> bool:
        '''Enables text extraction.'''
        raise NotImplementedError()
    
    @extract_text.setter
    def extract_text(self, value : bool) -> None:
        '''Enables text extraction.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''The width of the output image (in pixels).'''
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : int) -> None:
        '''The width of the output image (in pixels).'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''Sets the height of an output image (in pixels).'''
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : int) -> None:
        '''Sets the height of an output image (in pixels).'''
        raise NotImplementedError()
    
    @property
    def max_width(self) -> int:
        '''Sets the maximum width of an output image (in pixels).'''
        raise NotImplementedError()
    
    @max_width.setter
    def max_width(self, value : int) -> None:
        '''Sets the maximum width of an output image (in pixels).'''
        raise NotImplementedError()
    
    @property
    def max_height(self) -> int:
        '''Sets the maximum height of an output image (in pixels).'''
        raise NotImplementedError()
    
    @max_height.setter
    def max_height(self, value : int) -> None:
        '''Sets the maximum height of an output image (in pixels).'''
        raise NotImplementedError()
    

class PresentationOptions:
    '''Contains options for rendering presentations. For details, see the `documentation <https://docs.groupdocs.com/viewer/net/render-presentations/>`.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def resolution(self) -> groupdocs.viewer.options.Resolution:
        '''Resolution of the presentation images (for rendering to HTML/PDF only).'''
        raise NotImplementedError()
    
    @resolution.setter
    def resolution(self, value : groupdocs.viewer.options.Resolution) -> None:
        '''Resolution of the presentation images (for rendering to HTML/PDF only).'''
        raise NotImplementedError()
    
    @property
    def render_to_pure_html(self) -> bool:
        '''Enables a new HTML rendering mode for the Presentation documents — in this mode the Presentation files are rendered to **pure HTML/CSS markup**, without SVG images. By default is disabled (``false``) — existing SVG-based HTML-renderer is used.'''
        raise NotImplementedError()
    
    @render_to_pure_html.setter
    def render_to_pure_html(self, value : bool) -> None:
        '''Enables a new HTML rendering mode for the Presentation documents — in this mode the Presentation files are rendered to **pure HTML/CSS markup**, without SVG images. By default is disabled (``false``) — existing SVG-based HTML-renderer is used.'''
        raise NotImplementedError()
    

class ProjectManagementOptions:
    '''Contains options for rendering project management files. For details, see the `documentation <https://docs.groupdocs.com/viewer/net/render-ms-project-files/>`.'''
    
    def __init__(self) -> None:
        '''Creates an instance of the :py:class:`groupdocs.viewer.options.ProjectManagementOptions` class.'''
        raise NotImplementedError()
    
    @property
    def page_size(self) -> groupdocs.viewer.options.PageSize:
        '''The output page size.'''
        raise NotImplementedError()
    
    @page_size.setter
    def page_size(self, value : groupdocs.viewer.options.PageSize) -> None:
        '''The output page size.'''
        raise NotImplementedError()
    
    @property
    def time_unit(self) -> groupdocs.viewer.options.TimeUnit:
        '''The time unit.'''
        raise NotImplementedError()
    
    @time_unit.setter
    def time_unit(self, value : groupdocs.viewer.options.TimeUnit) -> None:
        '''The time unit.'''
        raise NotImplementedError()
    
    @property
    def start_date(self) -> datetime:
        '''The start date of the Gantt Chart View to be included into the output.'''
        raise NotImplementedError()
    
    @start_date.setter
    def start_date(self, value : datetime) -> None:
        '''The start date of the Gantt Chart View to be included into the output.'''
        raise NotImplementedError()
    
    @property
    def end_date(self) -> datetime:
        '''The end date of the Gantt Chart View to be included into the output.'''
        raise NotImplementedError()
    
    @end_date.setter
    def end_date(self, value : datetime) -> None:
        '''The end date of the Gantt Chart View to be included into the output.'''
        raise NotImplementedError()
    

class Resolution:
    '''Contains option to set resolution for images in output document.'''
    
    def __init__(self, value : int) -> None:
        '''Sets resolution in DPI.
        
        :param value: Resolution in DPI.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> int:
        '''Quality DPI.'''
        raise NotImplementedError()
    
    @property
    def DPI330(self) -> groupdocs.viewer.options.Resolution:
        '''Good quality for high-definition (HD) displays.'''
        raise NotImplementedError()

    @property
    def DPI220(self) -> groupdocs.viewer.options.Resolution:
        '''Excellent quality on most printers and screens.'''
        raise NotImplementedError()

    @property
    def DPI150(self) -> groupdocs.viewer.options.Resolution:
        '''Good for web pages and projectors.'''
        raise NotImplementedError()

    @property
    def DPI96(self) -> groupdocs.viewer.options.Resolution:
        '''Good for web pages and projectors.'''
        raise NotImplementedError()

    @property
    def DPI72(self) -> groupdocs.viewer.options.Resolution:
        '''Default compression level.'''
        raise NotImplementedError()

    @property
    def DOCUMENT_RESOLUTION(self) -> groupdocs.viewer.options.Resolution:
        '''Default compression level - as in the document.'''
        raise NotImplementedError()


class Security:
    '''Contains the PDF document security options. For details, see the `documentation <https://docs.groupdocs.com/viewer/net/protect-pdf-documents/>`.'''
    
    def __init__(self) -> None:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.Security` class.'''
        raise NotImplementedError()
    
    @property
    def document_open_password(self) -> str:
        '''The password required to open the PDF document.'''
        raise NotImplementedError()
    
    @document_open_password.setter
    def document_open_password(self, value : str) -> None:
        '''The password required to open the PDF document.'''
        raise NotImplementedError()
    
    @property
    def permissions_password(self) -> str:
        '''The password required to change permission settings.
        Using a permissions password you can restrict printing, modification and data extraction.'''
        raise NotImplementedError()
    
    @permissions_password.setter
    def permissions_password(self, value : str) -> None:
        '''The password required to change permission settings.
        Using a permissions password you can restrict printing, modification and data extraction.'''
        raise NotImplementedError()
    
    @property
    def permissions(self) -> groupdocs.viewer.options.Permissions:
        '''The PDF document permissions such as printing, modification and data extraction.'''
        raise NotImplementedError()
    
    @permissions.setter
    def permissions(self, value : groupdocs.viewer.options.Permissions) -> None:
        '''The PDF document permissions such as printing, modification and data extraction.'''
        raise NotImplementedError()
    

class Size:
    '''Contains the watermark size.'''
    
    def __init__(self, relative_size : int) -> None:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.Size` class.
        
        :param relative_size: The size in percents in relation to page size.'''
        raise NotImplementedError()
    
    @property
    def relative_size(self) -> int:
        '''The watermark text size in percentages in relation to page width.
        Valid values are between 1 and 100.'''
        raise NotImplementedError()
    
    @property
    def FULL_SIZE(self) -> groupdocs.viewer.options.Size:
        '''The maximum size of watermark text that fits page.'''
        raise NotImplementedError()

    @property
    def HALF_SIZE(self) -> groupdocs.viewer.options.Size:
        '''The half of the maximum size of watermark text that fits page.'''
        raise NotImplementedError()

    @property
    def ONE_THIRD(self) -> groupdocs.viewer.options.Size:
        '''The one third of the maximum size of watermark text that fits page.'''
        raise NotImplementedError()


class SpreadsheetOptions:
    '''Contains options for rendering spreadsheets. For details, see children of the `Render spreadsheet files <https://docs.groupdocs.com/viewer/net/render-spreadsheets/>` topic.'''
    
    @overload
    @staticmethod
    def for_split_sheet_into_pages(count_rows_per_page : int) -> groupdocs.viewer.options.SpreadsheetOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.SpreadsheetOptions` class for rendering sheet into pages.
        
        :param count_rows_per_page: Count of rows to include into each page.
        :returns: New instance of the :py:class:`groupdocs.viewer.options.SpreadsheetOptions` class for rendering sheet into pages.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def for_split_sheet_into_pages(count_rows_per_page : int, count_columns_per_page : int) -> groupdocs.viewer.options.SpreadsheetOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.SpreadsheetOptions` class for rendering sheet into pages.
        
        :param count_rows_per_page: Count of rows to include into each page.
        :param count_columns_per_page: Count of columns to include into each page.
        :returns: New instance of the :py:class:`groupdocs.viewer.options.SpreadsheetOptions` class for rendering sheet into pages.'''
        raise NotImplementedError()
    
    @staticmethod
    def for_one_page_per_sheet() -> groupdocs.viewer.options.SpreadsheetOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.SpreadsheetOptions` class for rendering the whole sheet into one page.
        
        :returns: New instance of the :py:class:`groupdocs.viewer.options.SpreadsheetOptions` class for rendering the whole sheet into one page.'''
        raise NotImplementedError()
    
    @staticmethod
    def for_rendering_print_area() -> groupdocs.viewer.options.SpreadsheetOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.SpreadsheetOptions` class for rendering the print areas only.
        
        :returns: New instance of the :py:class:`groupdocs.viewer.options.SpreadsheetOptions` class for rendering print areas only.'''
        raise NotImplementedError()
    
    @staticmethod
    def for_rendering_print_area_and_page_breaks() -> groupdocs.viewer.options.SpreadsheetOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.SpreadsheetOptions` class for rendering print areas and page breaks.
        
        :returns: New instance of the :py:class:`groupdocs.viewer.options.SpreadsheetOptions` class for rendering pages basing on page brakes that are included into print area. The behavior is similar to printing in Excel.'''
        raise NotImplementedError()
    
    @staticmethod
    def for_rendering_by_page_breaks() -> groupdocs.viewer.options.SpreadsheetOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.SpreadsheetOptions` class for splitting to pages by page breaks.
        
        :returns: New instance of :py:class:`groupdocs.viewer.options.SpreadsheetOptions` for splitting to pages by page breaks. The behavior is similar to printing in Excel.'''
        raise NotImplementedError()
    
    @property
    def count_rows_per_page(self) -> int:
        '''The rows count to include on each page when splitting the worksheet into pages.'''
        raise NotImplementedError()
    
    @property
    def count_columns_per_page(self) -> int:
        '''The columns count to include on each page when splitting the worksheet into pages.'''
        raise NotImplementedError()
    
    @property
    def render_grid_lines(self) -> bool:
        '''Enables grid lines rendering.'''
        raise NotImplementedError()
    
    @render_grid_lines.setter
    def render_grid_lines(self, value : bool) -> None:
        '''Enables grid lines rendering.'''
        raise NotImplementedError()
    
    @property
    def skip_empty_rows(self) -> bool:
        '''Disables empty rows rendering.'''
        raise NotImplementedError()
    
    @skip_empty_rows.setter
    def skip_empty_rows(self, value : bool) -> None:
        '''Disables empty rows rendering.'''
        raise NotImplementedError()
    
    @property
    def skip_empty_columns(self) -> bool:
        '''Disables empty columns rendering.'''
        raise NotImplementedError()
    
    @skip_empty_columns.setter
    def skip_empty_columns(self, value : bool) -> None:
        '''Disables empty columns rendering.'''
        raise NotImplementedError()
    
    @property
    def render_hidden_rows(self) -> bool:
        '''Enables hidden rows rendering.'''
        raise NotImplementedError()
    
    @render_hidden_rows.setter
    def render_hidden_rows(self, value : bool) -> None:
        '''Enables hidden rows rendering.'''
        raise NotImplementedError()
    
    @property
    def render_headings(self) -> bool:
        '''Enables headings rendering.'''
        raise NotImplementedError()
    
    @render_headings.setter
    def render_headings(self, value : bool) -> None:
        '''Enables headings rendering.'''
        raise NotImplementedError()
    
    @property
    def render_hidden_columns(self) -> bool:
        '''Enables hidden columns rendering.'''
        raise NotImplementedError()
    
    @render_hidden_columns.setter
    def render_hidden_columns(self, value : bool) -> None:
        '''Enables hidden columns rendering.'''
        raise NotImplementedError()
    
    @property
    def detect_separator(self) -> bool:
        '''Detect a separator (for CSV/TSV files).'''
        raise NotImplementedError()
    
    @detect_separator.setter
    def detect_separator(self, value : bool) -> None:
        '''Detect a separator (for CSV/TSV files).'''
        raise NotImplementedError()
    
    @property
    def left_margin(self) -> float:
        '''Sets the left margin of a page when converting to PDF.'''
        raise NotImplementedError()
    
    @left_margin.setter
    def left_margin(self, value : float) -> None:
        '''Sets the left margin of a page when converting to PDF.'''
        raise NotImplementedError()
    
    @property
    def right_margin(self) -> float:
        '''Sets the right margin of a page when converting to PDF.'''
        raise NotImplementedError()
    
    @right_margin.setter
    def right_margin(self, value : float) -> None:
        '''Sets the right margin of a page when converting to PDF.'''
        raise NotImplementedError()
    
    @property
    def top_margin(self) -> float:
        '''Sets the top margin of a page when converting to PDF.'''
        raise NotImplementedError()
    
    @top_margin.setter
    def top_margin(self, value : float) -> None:
        '''Sets the top margin of a page when converting to PDF.'''
        raise NotImplementedError()
    
    @property
    def bottom_margin(self) -> float:
        '''Sets the bottom margin of a page when converting to PDF.'''
        raise NotImplementedError()
    
    @bottom_margin.setter
    def bottom_margin(self, value : float) -> None:
        '''Sets the bottom margin of a page when converting to PDF.'''
        raise NotImplementedError()
    
    @property
    def text_overflow_mode(self) -> groupdocs.viewer.options.TextOverflowMode:
        '''Sets the text overflow mode for rendering spreadsheet documents into HTML.'''
        raise NotImplementedError()
    
    @text_overflow_mode.setter
    def text_overflow_mode(self, value : groupdocs.viewer.options.TextOverflowMode) -> None:
        '''Sets the text overflow mode for rendering spreadsheet documents into HTML.'''
        raise NotImplementedError()
    

class TextOptions:
    '''Text files splitting to pages options.'''
    
    def __init__(self) -> None:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.TextOptions` class.'''
        raise NotImplementedError()
    
    @property
    def max_chars_per_row(self) -> int:
        '''The maximum number of characters per row on a page.'''
        raise NotImplementedError()
    
    @max_chars_per_row.setter
    def max_chars_per_row(self, value : int) -> None:
        '''The maximum number of characters per row on a page.'''
        raise NotImplementedError()
    
    @property
    def max_rows_per_page(self) -> int:
        '''The maximum number of rows per page.'''
        raise NotImplementedError()
    
    @max_rows_per_page.setter
    def max_rows_per_page(self, value : int) -> None:
        '''The maximum number of rows per page.'''
        raise NotImplementedError()
    

class Tile:
    '''Represents the drawing region.'''
    
    def __init__(self, start_point_x : int, start_point_y : int, width : int, height : int) -> None:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.Tile` class.
        
        :param start_point_x: The X coordinate of the lowest left point on the drawing where the tile begins
        :param start_point_y: The Y coordinate of the lowest left point on the drawing where the tile begins.
        :param width: The width of the tile in pixels.
        :param height: The height of the tile in pixels.'''
        raise NotImplementedError()
    
    def get_end_point_x(self) -> int:
        '''Returns the X coordinate of the highest right point on the drawing where the tile ends.'''
        raise NotImplementedError()
    
    def get_end_point_y(self) -> int:
        '''Returns the Y coordinate of the highest right point on the drawing where the tile ends.'''
        raise NotImplementedError()
    
    @property
    def start_point_x(self) -> int:
        '''The X coordinate of the lowest left point on the drawing where the tile begins.'''
        raise NotImplementedError()
    
    @property
    def start_point_y(self) -> int:
        '''The Y coordinate of the lowest left point on the drawing where the tile begins.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''The width of the tile in pixels.'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''The height of the tile in pixels.'''
        raise NotImplementedError()
    

class ViewInfoOptions(BaseViewOptions):
    '''Contains options for retrieving information about view.'''
    
    @overload
    @staticmethod
    def for_html_view() -> groupdocs.viewer.options.ViewInfoOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.ViewInfoOptions` class to retrieve information about view when rendering into HTML.
        
        :returns: New instance of the :py:class:`groupdocs.viewer.options.ViewInfoOptions` class.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def for_html_view(render_single_page : bool) -> groupdocs.viewer.options.ViewInfoOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.ViewInfoOptions` class to retrieve information about view when rendering into HTML.
        
        :param render_single_page: Enables HTML content rendering to a single page.
        :returns: New instance of the :py:class:`groupdocs.viewer.options.ViewInfoOptions` class.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def for_jpg_view() -> groupdocs.viewer.options.ViewInfoOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.ViewInfoOptions` class to retrieve information about view when rendering into JPG.
        
        :returns: New instance of the :py:class:`groupdocs.viewer.options.ViewInfoOptions` class.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def for_jpg_view(extract_text : bool) -> groupdocs.viewer.options.ViewInfoOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.ViewInfoOptions` class to retrieve information about view when rendering into JPG.
        
        :param extract_text: Enables text extraction.
        :returns: New instance of the :py:class:`groupdocs.viewer.options.ViewInfoOptions` class.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def for_png_view() -> groupdocs.viewer.options.ViewInfoOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.ViewInfoOptions` class to retrieve information about view when rendering into PNG.
        
        :returns: New instance of the :py:class:`groupdocs.viewer.options.ViewInfoOptions` class.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def for_png_view(extract_text : bool) -> groupdocs.viewer.options.ViewInfoOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.ViewInfoOptions` class to retrieve information about view when rendering into PNG.
        
        :param extract_text: Enables text extraction.
        :returns: New instance of the :py:class:`groupdocs.viewer.options.ViewInfoOptions` class.'''
        raise NotImplementedError()
    
    @staticmethod
    def for_pdf_view() -> groupdocs.viewer.options.ViewInfoOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.ViewInfoOptions` class to retrieve information about view when rendering into PDF.
        
        :returns: New instance of the :py:class:`groupdocs.viewer.options.ViewInfoOptions` class.'''
        raise NotImplementedError()
    
    @staticmethod
    def from_html_view_options(options : groupdocs.viewer.options.HtmlViewOptions) -> groupdocs.viewer.options.ViewInfoOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.ViewInfoOptions` class based on the :py:class:`groupdocs.viewer.options.HtmlViewOptions` object.
        
        :param options: The HTML view options.
        :returns: New instance of the :py:class:`groupdocs.viewer.options.ViewInfoOptions` class.'''
        raise NotImplementedError()
    
    @staticmethod
    def from_png_view_options(options : groupdocs.viewer.options.PngViewOptions) -> groupdocs.viewer.options.ViewInfoOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.ViewInfoOptions` class based on the :py:class:`groupdocs.viewer.options.PngViewOptions` object.
        
        :param options: The PNG view options.
        :returns: New instance of the :py:class:`groupdocs.viewer.options.ViewInfoOptions` class.'''
        raise NotImplementedError()
    
    @staticmethod
    def from_jpg_view_options(options : groupdocs.viewer.options.JpgViewOptions) -> groupdocs.viewer.options.ViewInfoOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.ViewInfoOptions` class based on the :py:class:`groupdocs.viewer.options.JpgViewOptions` object.
        
        :param options: The JPG view options.
        :returns: New instance of the :py:class:`groupdocs.viewer.options.ViewInfoOptions` class.'''
        raise NotImplementedError()
    
    @staticmethod
    def from_pdf_view_options(options : groupdocs.viewer.options.PdfViewOptions) -> groupdocs.viewer.options.ViewInfoOptions:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.ViewInfoOptions` class based on the :py:class:`groupdocs.viewer.options.PdfViewOptions` object.
        
        :param options: The PDF view options.
        :returns: New instance of the :py:class:`groupdocs.viewer.options.ViewInfoOptions` class.'''
        raise NotImplementedError()
    
    @property
    def render_comments(self) -> bool:
        '''Enables rendering comments.'''
        raise NotImplementedError()
    
    @render_comments.setter
    def render_comments(self, value : bool) -> None:
        '''Enables rendering comments.'''
        raise NotImplementedError()
    
    @property
    def render_notes(self) -> bool:
        '''Enables rendering notes.'''
        raise NotImplementedError()
    
    @render_notes.setter
    def render_notes(self, value : bool) -> None:
        '''Enables rendering notes.'''
        raise NotImplementedError()
    
    @property
    def render_hidden_pages(self) -> bool:
        '''Enables rendering of hidden pages.'''
        raise NotImplementedError()
    
    @render_hidden_pages.setter
    def render_hidden_pages(self, value : bool) -> None:
        '''Enables rendering of hidden pages.'''
        raise NotImplementedError()
    
    @property
    def default_font_name(self) -> str:
        '''Sets the default font for a document.'''
        raise NotImplementedError()
    
    @default_font_name.setter
    def default_font_name(self, value : str) -> None:
        '''Sets the default font for a document.'''
        raise NotImplementedError()
    
    @property
    def archive_options(self) -> groupdocs.viewer.options.ArchiveOptions:
        '''The archive files view options.'''
        raise NotImplementedError()
    
    @archive_options.setter
    def archive_options(self, value : groupdocs.viewer.options.ArchiveOptions) -> None:
        '''The archive files view options.'''
        raise NotImplementedError()
    
    @property
    def cad_options(self) -> groupdocs.viewer.options.CadOptions:
        '''The CAD drawing view options.'''
        raise NotImplementedError()
    
    @cad_options.setter
    def cad_options(self, value : groupdocs.viewer.options.CadOptions) -> None:
        '''The CAD drawing view options.'''
        raise NotImplementedError()
    
    @property
    def email_options(self) -> groupdocs.viewer.options.EmailOptions:
        '''The email messages view options.'''
        raise NotImplementedError()
    
    @email_options.setter
    def email_options(self, value : groupdocs.viewer.options.EmailOptions) -> None:
        '''The email messages view options.'''
        raise NotImplementedError()
    
    @property
    def outlook_options(self) -> groupdocs.viewer.options.OutlookOptions:
        '''The Microsoft Outlook data files view options.'''
        raise NotImplementedError()
    
    @outlook_options.setter
    def outlook_options(self, value : groupdocs.viewer.options.OutlookOptions) -> None:
        '''The Microsoft Outlook data files view options.'''
        raise NotImplementedError()
    
    @property
    def mail_storage_options(self) -> groupdocs.viewer.options.MailStorageOptions:
        '''Mail storage data files view options.'''
        raise NotImplementedError()
    
    @mail_storage_options.setter
    def mail_storage_options(self, value : groupdocs.viewer.options.MailStorageOptions) -> None:
        '''Mail storage data files view options.'''
        raise NotImplementedError()
    
    @property
    def pdf_options(self) -> groupdocs.viewer.options.PdfOptions:
        '''The PDF document view options.'''
        raise NotImplementedError()
    
    @pdf_options.setter
    def pdf_options(self, value : groupdocs.viewer.options.PdfOptions) -> None:
        '''The PDF document view options.'''
        raise NotImplementedError()
    
    @property
    def project_management_options(self) -> groupdocs.viewer.options.ProjectManagementOptions:
        '''The project management files view options.'''
        raise NotImplementedError()
    
    @project_management_options.setter
    def project_management_options(self, value : groupdocs.viewer.options.ProjectManagementOptions) -> None:
        '''The project management files view options.'''
        raise NotImplementedError()
    
    @property
    def spreadsheet_options(self) -> groupdocs.viewer.options.SpreadsheetOptions:
        '''The spreadsheet files view options.'''
        raise NotImplementedError()
    
    @spreadsheet_options.setter
    def spreadsheet_options(self, value : groupdocs.viewer.options.SpreadsheetOptions) -> None:
        '''The spreadsheet files view options.'''
        raise NotImplementedError()
    
    @property
    def word_processing_options(self) -> groupdocs.viewer.options.WordProcessingOptions:
        '''The Word processing files view options.'''
        raise NotImplementedError()
    
    @word_processing_options.setter
    def word_processing_options(self, value : groupdocs.viewer.options.WordProcessingOptions) -> None:
        '''The Word processing files view options.'''
        raise NotImplementedError()
    
    @property
    def visio_rendering_options(self) -> groupdocs.viewer.options.VisioRenderingOptions:
        '''The Visio files view options.'''
        raise NotImplementedError()
    
    @visio_rendering_options.setter
    def visio_rendering_options(self, value : groupdocs.viewer.options.VisioRenderingOptions) -> None:
        '''The Visio files view options.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> groupdocs.viewer.options.TextOptions:
        '''Text files view options.'''
        raise NotImplementedError()
    
    @text_options.setter
    def text_options(self, value : groupdocs.viewer.options.TextOptions) -> None:
        '''Text files view options.'''
        raise NotImplementedError()
    
    @property
    def presentation_options(self) -> groupdocs.viewer.options.PresentationOptions:
        '''The presentation files view options.'''
        raise NotImplementedError()
    
    @presentation_options.setter
    def presentation_options(self, value : groupdocs.viewer.options.PresentationOptions) -> None:
        '''The presentation files view options.'''
        raise NotImplementedError()
    
    @property
    def web_document_options(self) -> groupdocs.viewer.options.WebDocumentOptions:
        '''The Web files view options.'''
        raise NotImplementedError()
    
    @web_document_options.setter
    def web_document_options(self, value : groupdocs.viewer.options.WebDocumentOptions) -> None:
        '''The Web files view options.'''
        raise NotImplementedError()
    
    @property
    def extract_text(self) -> bool:
        '''Enables text extraction.'''
        raise NotImplementedError()
    
    @extract_text.setter
    def extract_text(self, value : bool) -> None:
        '''Enables text extraction.'''
        raise NotImplementedError()
    
    @property
    def max_width(self) -> int:
        '''Sets the maximum width of an output image (in pixels, for rendering to PNG/JPG only).'''
        raise NotImplementedError()
    
    @max_width.setter
    def max_width(self, value : int) -> None:
        '''Sets the maximum width of an output image (in pixels, for rendering to PNG/JPG only).'''
        raise NotImplementedError()
    
    @property
    def max_height(self) -> int:
        '''Sets the maximum height of an output image (in pixels, for rendering to PNG/JPG only).'''
        raise NotImplementedError()
    
    @max_height.setter
    def max_height(self, value : int) -> None:
        '''Sets the maximum height of an output image (in pixels, for rendering to PNG/JPG only).'''
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''The width of the output image (in pixels, for rendering to PNG/JPG only).'''
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : int) -> None:
        '''The width of the output image (in pixels, for rendering to PNG/JPG only).'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''The height of the output image (in pixels, for rendering to PNG/JPG only).'''
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : int) -> None:
        '''The height of the output image (in pixels, for rendering to PNG/JPG only).'''
        raise NotImplementedError()
    

class ViewOptions(BaseViewOptions):
    '''Contains the rendering options.'''
    
    def rotate_page(self, page_number : int, rotation : groupdocs.viewer.options.Rotation) -> None:
        '''Applies the clockwise rotation to a page.
        
        :param page_number: The page number, must be strictly greater than 0
        :param rotation: The rotation value.'''
        raise NotImplementedError()
    
    @property
    def render_comments(self) -> bool:
        '''Enables rendering comments.'''
        raise NotImplementedError()
    
    @render_comments.setter
    def render_comments(self, value : bool) -> None:
        '''Enables rendering comments.'''
        raise NotImplementedError()
    
    @property
    def render_notes(self) -> bool:
        '''Enables rendering notes.'''
        raise NotImplementedError()
    
    @render_notes.setter
    def render_notes(self, value : bool) -> None:
        '''Enables rendering notes.'''
        raise NotImplementedError()
    
    @property
    def render_hidden_pages(self) -> bool:
        '''Enables rendering of hidden pages.'''
        raise NotImplementedError()
    
    @render_hidden_pages.setter
    def render_hidden_pages(self, value : bool) -> None:
        '''Enables rendering of hidden pages.'''
        raise NotImplementedError()
    
    @property
    def default_font_name(self) -> str:
        '''Sets the default font for a document.'''
        raise NotImplementedError()
    
    @default_font_name.setter
    def default_font_name(self, value : str) -> None:
        '''Sets the default font for a document.'''
        raise NotImplementedError()
    
    @property
    def archive_options(self) -> groupdocs.viewer.options.ArchiveOptions:
        '''The archive files view options.'''
        raise NotImplementedError()
    
    @archive_options.setter
    def archive_options(self, value : groupdocs.viewer.options.ArchiveOptions) -> None:
        '''The archive files view options.'''
        raise NotImplementedError()
    
    @property
    def cad_options(self) -> groupdocs.viewer.options.CadOptions:
        '''The CAD drawing view options.'''
        raise NotImplementedError()
    
    @cad_options.setter
    def cad_options(self, value : groupdocs.viewer.options.CadOptions) -> None:
        '''The CAD drawing view options.'''
        raise NotImplementedError()
    
    @property
    def email_options(self) -> groupdocs.viewer.options.EmailOptions:
        '''The email messages view options.'''
        raise NotImplementedError()
    
    @email_options.setter
    def email_options(self, value : groupdocs.viewer.options.EmailOptions) -> None:
        '''The email messages view options.'''
        raise NotImplementedError()
    
    @property
    def outlook_options(self) -> groupdocs.viewer.options.OutlookOptions:
        '''The Microsoft Outlook data files view options.'''
        raise NotImplementedError()
    
    @outlook_options.setter
    def outlook_options(self, value : groupdocs.viewer.options.OutlookOptions) -> None:
        '''The Microsoft Outlook data files view options.'''
        raise NotImplementedError()
    
    @property
    def mail_storage_options(self) -> groupdocs.viewer.options.MailStorageOptions:
        '''Mail storage data files view options.'''
        raise NotImplementedError()
    
    @mail_storage_options.setter
    def mail_storage_options(self, value : groupdocs.viewer.options.MailStorageOptions) -> None:
        '''Mail storage data files view options.'''
        raise NotImplementedError()
    
    @property
    def pdf_options(self) -> groupdocs.viewer.options.PdfOptions:
        '''The PDF document view options.'''
        raise NotImplementedError()
    
    @pdf_options.setter
    def pdf_options(self, value : groupdocs.viewer.options.PdfOptions) -> None:
        '''The PDF document view options.'''
        raise NotImplementedError()
    
    @property
    def project_management_options(self) -> groupdocs.viewer.options.ProjectManagementOptions:
        '''The project management files view options.'''
        raise NotImplementedError()
    
    @project_management_options.setter
    def project_management_options(self, value : groupdocs.viewer.options.ProjectManagementOptions) -> None:
        '''The project management files view options.'''
        raise NotImplementedError()
    
    @property
    def spreadsheet_options(self) -> groupdocs.viewer.options.SpreadsheetOptions:
        '''The spreadsheet files view options.'''
        raise NotImplementedError()
    
    @spreadsheet_options.setter
    def spreadsheet_options(self, value : groupdocs.viewer.options.SpreadsheetOptions) -> None:
        '''The spreadsheet files view options.'''
        raise NotImplementedError()
    
    @property
    def word_processing_options(self) -> groupdocs.viewer.options.WordProcessingOptions:
        '''The Word processing files view options.'''
        raise NotImplementedError()
    
    @word_processing_options.setter
    def word_processing_options(self, value : groupdocs.viewer.options.WordProcessingOptions) -> None:
        '''The Word processing files view options.'''
        raise NotImplementedError()
    
    @property
    def visio_rendering_options(self) -> groupdocs.viewer.options.VisioRenderingOptions:
        '''The Visio files view options.'''
        raise NotImplementedError()
    
    @visio_rendering_options.setter
    def visio_rendering_options(self, value : groupdocs.viewer.options.VisioRenderingOptions) -> None:
        '''The Visio files view options.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> groupdocs.viewer.options.TextOptions:
        '''Text files view options.'''
        raise NotImplementedError()
    
    @text_options.setter
    def text_options(self, value : groupdocs.viewer.options.TextOptions) -> None:
        '''Text files view options.'''
        raise NotImplementedError()
    
    @property
    def presentation_options(self) -> groupdocs.viewer.options.PresentationOptions:
        '''The presentation files view options.'''
        raise NotImplementedError()
    
    @presentation_options.setter
    def presentation_options(self, value : groupdocs.viewer.options.PresentationOptions) -> None:
        '''The presentation files view options.'''
        raise NotImplementedError()
    
    @property
    def web_document_options(self) -> groupdocs.viewer.options.WebDocumentOptions:
        '''The Web files view options.'''
        raise NotImplementedError()
    
    @web_document_options.setter
    def web_document_options(self, value : groupdocs.viewer.options.WebDocumentOptions) -> None:
        '''The Web files view options.'''
        raise NotImplementedError()
    
    @property
    def watermark(self) -> groupdocs.viewer.options.Watermark:
        '''The text watermark to be applied to each page.'''
        raise NotImplementedError()
    
    @watermark.setter
    def watermark(self, value : groupdocs.viewer.options.Watermark) -> None:
        '''The text watermark to be applied to each page.'''
        raise NotImplementedError()
    

class VisioRenderingOptions:
    '''Contains options for rendering Visio documents. For details, see the `documentation <https://docs.groupdocs.com/viewer/net/render-visio-documents/>`.'''
    
    def __init__(self) -> None:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.VisioRenderingOptions` class.'''
        raise NotImplementedError()
    
    @property
    def render_figures_only(self) -> bool:
        '''Render only Visio figures, not a diagram.'''
        raise NotImplementedError()
    
    @render_figures_only.setter
    def render_figures_only(self, value : bool) -> None:
        '''Render only Visio figures, not a diagram.'''
        raise NotImplementedError()
    
    @property
    def figure_width(self) -> int:
        '''Figure width, height will be calculated automatically. Default value is 100.'''
        raise NotImplementedError()
    
    @figure_width.setter
    def figure_width(self, value : int) -> None:
        '''Figure width, height will be calculated automatically. Default value is 100.'''
        raise NotImplementedError()
    

class Watermark:
    '''Represents a text watermark. For details, see the `documentation <https://docs.groupdocs.com/viewer/net/add-text-watermark/>`.'''
    
    def __init__(self, text : str) -> None:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.Watermark` class.
        
        :param text: Watermark text.'''
        raise NotImplementedError()
    
    @property
    def text(self) -> str:
        '''The watermark text.'''
        raise NotImplementedError()
    
    @property
    def color(self) -> groupdocs.viewer.drawing.Argb32Color:
        '''The watermark color.
        Default value is :py:attr:`GroupDocs.Viewer.Drawing.Rgb24Color.KnownColors.CssLevel1.Red`.'''
        raise NotImplementedError()
    
    @color.setter
    def color(self, value : groupdocs.viewer.drawing.Argb32Color) -> None:
        '''The watermark color.
        Default value is :py:attr:`GroupDocs.Viewer.Drawing.Rgb24Color.KnownColors.CssLevel1.Red`.'''
        raise NotImplementedError()
    
    @property
    def position(self) -> groupdocs.viewer.options.Position:
        '''The watermark position.
        Default value is :py:attr:`groupdocs.viewer.options.Position.DIAGONAL`.'''
        raise NotImplementedError()
    
    @position.setter
    def position(self, value : groupdocs.viewer.options.Position) -> None:
        '''The watermark position.
        Default value is :py:attr:`groupdocs.viewer.options.Position.DIAGONAL`.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> groupdocs.viewer.options.Size:
        '''The watermark size.
        Default value is :py:attr:`groupdocs.viewer.options.Size.FULL_SIZE`.'''
        raise NotImplementedError()
    
    @size.setter
    def size(self, value : groupdocs.viewer.options.Size) -> None:
        '''The watermark size.
        Default value is :py:attr:`groupdocs.viewer.options.Size.FULL_SIZE`.'''
        raise NotImplementedError()
    
    @property
    def font_name(self) -> str:
        '''The font name used for the watermark.'''
        raise NotImplementedError()
    
    @font_name.setter
    def font_name(self, value : str) -> None:
        '''The font name used for the watermark.'''
        raise NotImplementedError()
    

class WebDocumentOptions:
    '''Contains options for rendering web documents. For details, see the `documentation <https://docs.groupdocs.com/viewer/net/render-web-documents/>`.'''
    
    def __init__(self) -> None:
        '''Initializes an instance of the :py:class:`groupdocs.viewer.options.WebDocumentOptions` class.'''
        raise NotImplementedError()
    
    @property
    def page_size(self) -> groupdocs.viewer.options.PageSize:
        '''Sets the size of the output page.'''
        raise NotImplementedError()
    
    @page_size.setter
    def page_size(self, value : groupdocs.viewer.options.PageSize) -> None:
        '''Sets the size of the output page.'''
        raise NotImplementedError()
    
    @property
    def left_margin(self) -> float:
        '''Sets the left margin of a page. The default value is 5 points.'''
        raise NotImplementedError()
    
    @left_margin.setter
    def left_margin(self, value : float) -> None:
        '''Sets the left margin of a page. The default value is 5 points.'''
        raise NotImplementedError()
    
    @property
    def right_margin(self) -> float:
        '''Sets the right margin of a page. The default value is 5 points.'''
        raise NotImplementedError()
    
    @right_margin.setter
    def right_margin(self, value : float) -> None:
        '''Sets the right margin of a page. The default value is 5 points.'''
        raise NotImplementedError()
    
    @property
    def top_margin(self) -> float:
        '''Sets the top margin of a page. The default value is 72 points.'''
        raise NotImplementedError()
    
    @top_margin.setter
    def top_margin(self, value : float) -> None:
        '''Sets the top margin of a page. The default value is 72 points.'''
        raise NotImplementedError()
    
    @property
    def bottom_margin(self) -> float:
        '''Sets the bottom margin of a page. The default value is 72 points.'''
        raise NotImplementedError()
    
    @bottom_margin.setter
    def bottom_margin(self, value : float) -> None:
        '''Sets the bottom margin of a page. The default value is 72 points.'''
        raise NotImplementedError()
    

class WordProcessingOptions:
    '''Contains options for rendering Word documents. For details, see the `documentation <https://docs.groupdocs.com/viewer/net/render-word-documents/>`.'''
    
    def __init__(self) -> None:
        '''Contains options for rendering word processing documents. For details, see the `documentation <https://docs.groupdocs.com/viewer/net/render-word-documents/#render-tracked-changes>`.'''
        raise NotImplementedError()
    
    @property
    def page_size(self) -> groupdocs.viewer.options.PageSize:
        '''The size of the output page.
        The default value is :py:attr:`groupdocs.viewer.options.PageSize.UNSPECIFIED` which means that a page size is set in a page settings (Page Setup) is used.'''
        raise NotImplementedError()
    
    @page_size.setter
    def page_size(self, value : groupdocs.viewer.options.PageSize) -> None:
        '''The size of the output page.
        The default value is :py:attr:`groupdocs.viewer.options.PageSize.UNSPECIFIED` which means that a page size is set in a page settings (Page Setup) is used.'''
        raise NotImplementedError()
    
    @property
    def render_tracked_changes(self) -> bool:
        '''Enables tracked changes (revisions) rendering.'''
        raise NotImplementedError()
    
    @render_tracked_changes.setter
    def render_tracked_changes(self, value : bool) -> None:
        '''Enables tracked changes (revisions) rendering.'''
        raise NotImplementedError()
    
    @property
    def left_margin(self) -> System.Nullable`1[[System.Single]]:
        '''Sets the left margin of a page.'''
        raise NotImplementedError()
    
    @left_margin.setter
    def left_margin(self, value : System.Nullable`1[[System.Single]]) -> None:
        '''Sets the left margin of a page.'''
        raise NotImplementedError()
    
    @property
    def right_margin(self) -> System.Nullable`1[[System.Single]]:
        '''Sets the right margin of a page.'''
        raise NotImplementedError()
    
    @right_margin.setter
    def right_margin(self, value : System.Nullable`1[[System.Single]]) -> None:
        '''Sets the right margin of a page.'''
        raise NotImplementedError()
    
    @property
    def top_margin(self) -> System.Nullable`1[[System.Single]]:
        '''Sets the top margin of a page.'''
        raise NotImplementedError()
    
    @top_margin.setter
    def top_margin(self, value : System.Nullable`1[[System.Single]]) -> None:
        '''Sets the top margin of a page.'''
        raise NotImplementedError()
    
    @property
    def bottom_margin(self) -> System.Nullable`1[[System.Single]]:
        '''Sets the bottom margin of a page.'''
        raise NotImplementedError()
    
    @bottom_margin.setter
    def bottom_margin(self, value : System.Nullable`1[[System.Single]]) -> None:
        '''Sets the bottom margin of a page.'''
        raise NotImplementedError()
    
    @property
    def enable_open_type_features(self) -> bool:
        '''This option enables kerning and other OpenType Features when rendering Arabic, Hebrew, Indian Latin-based, or Cyrillic-based scripts.'''
        raise NotImplementedError()
    
    @enable_open_type_features.setter
    def enable_open_type_features(self, value : bool) -> None:
        '''This option enables kerning and other OpenType Features when rendering Arabic, Hebrew, Indian Latin-based, or Cyrillic-based scripts.'''
        raise NotImplementedError()
    
    @property
    def unlink_table_of_contents(self) -> bool:
        '''When rendering to HTML or PDF, you can set this option to `true` to disable navigation from the table of contents.
        For HTML rendering, `a` tags with relative links will be replaced with `span` tags, removing functionality but preserving visual appearance.
        For PDF rendering, the table of contents will be rendered as plain text without links to document sections.'''
        raise NotImplementedError()
    
    @unlink_table_of_contents.setter
    def unlink_table_of_contents(self, value : bool) -> None:
        '''When rendering to HTML or PDF, you can set this option to `true` to disable navigation from the table of contents.
        For HTML rendering, `a` tags with relative links will be replaced with `span` tags, removing functionality but preserving visual appearance.
        For PDF rendering, the table of contents will be rendered as plain text without links to document sections.'''
        raise NotImplementedError()
    

class ImageQuality:
    '''The quality of images in the output HTML contained by the PDF documents.'''
    
    LOW : ImageQuality
    '''The acceptable quality and best performance.'''
    MEDIUM : ImageQuality
    '''Better quality and slower performance.'''
    HIGH : ImageQuality
    '''The best quality but slow performance.'''

class PageSize:
    '''The size of the page.'''
    
    UNSPECIFIED : PageSize
    '''The default, unspecified page size.'''
    LETTER : PageSize
    '''The size of the Letter page in points is 792 x 612'''
    LEDGER : PageSize
    '''The size of the Ledger page in points is 1224 x 792'''
    A0 : PageSize
    '''The size of the A0 page in points is 3371 x 2384'''
    A1 : PageSize
    '''The size of the A1 page in points is 2384 x 1685'''
    A2 : PageSize
    '''The size of the A2 page in points is 1684 x 1190'''
    A3 : PageSize
    '''The size of the A3 page in points is 1190 x 842'''
    A4 : PageSize
    '''The size of the A4 page in points is 842 x 595'''

class Permissions:
    '''Defines PDF document permissions.'''
    
    ALLOW_ALL : Permissions
    '''Allow printing, modification and data extraction.'''
    DENY_PRINTING : Permissions
    '''Deny printing.'''
    DENY_MODIFICATION : Permissions
    '''Deny content modification, filling in forms, adding or modifying annotations.'''
    DENY_DATA_EXTRACTION : Permissions
    '''Deny text and graphics extraction.'''
    DENY_ALL : Permissions
    '''Deny printing, content modification and data extraction.'''

class Position:
    '''Defines the watermark position.'''
    
    DIAGONAL : Position
    '''The diagonal position.'''
    TOP_LEFT : Position
    '''The top left position.'''
    TOP_CENTER : Position
    '''The top center position.'''
    TOP_RIGHT : Position
    '''The top right position.'''
    BOTTOM_LEFT : Position
    '''The bottom left position.'''
    BOTTOM_CENTER : Position
    '''The bottom center position.'''
    BOTTOM_RIGHT : Position
    '''The bottom right position.'''

class Rotation:
    '''Contains page rotation in degrees (clockwise).'''
    
    ON_90_DEGREE : Rotation
    '''The 90 degree page rotation.'''
    ON_180_DEGREE : Rotation
    '''The 180 degree page rotation.'''
    ON_270_DEGREE : Rotation
    '''The 270 degree page rotation.'''

class TextOverflowMode:
    '''Sets the text overflow mode for rendering spreadsheet documents into HTML.'''
    
    OVERLAY : TextOverflowMode
    '''Overlay next cells even they are not empty.'''
    OVERLAY_IF_NEXT_IS_EMPTY : TextOverflowMode
    '''Overlay next cells only if they are empty.'''
    AUTO_FIT_COLUMN : TextOverflowMode
    '''Expand columns to fit the text.'''
    HIDE_TEXT : TextOverflowMode
    '''Hide overflow text.'''

class TimeUnit:
    '''Time unit of the project duration.'''
    
    UNSPECIFIED : TimeUnit
    '''The unknown, unspecified time scale.'''
    DAYS : TimeUnit
    '''The one day interval.'''
    THIRDS_OF_MONTHS : TimeUnit
    '''The one third of the month.'''
    MONTHS : TimeUnit
    '''The one month interval.'''

