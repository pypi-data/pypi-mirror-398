
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

class FileType:
    '''Represents file type. Provides methods to obtain list of all file types supported by **GroupDocs.Viewer**.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.FileType` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_format : str, extension : str) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.FileType` class.
        
        :param file_format: File format e.g. "Drawing Exchange Format File"
        :param extension: File extension with dot e.g. ".dxf"'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def from_stream(stream : io._IOBase) -> groupdocs.viewer.FileType:
        '''Detects file type by reading the file signature.
        
        :param stream: The file stream.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def from_stream(stream : io._IOBase, password : str) -> groupdocs.viewer.FileType:
        '''Detects file type by reading the file signature.
        
        :param stream: The file stream.
        :param password: The password to open the file.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def from_stream(stream : io._IOBase, logger : groupdocs.viewer.logging.ILogger) -> groupdocs.viewer.FileType:
        '''Detects file type by reading the file signature.
        
        :param stream: The file stream.
        :param logger: The logger.
        :returns: Returns file type in case it was detected successfully otherwise returns default :py:attr:`groupdocs.viewer.FileType.UNKNOWN` file type.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def from_stream(stream : io._IOBase, password : str, logger : groupdocs.viewer.logging.ILogger) -> groupdocs.viewer.FileType:
        '''Detects file type by reading the file signature.
        
        :param stream: The file stream.
        :param password: The password to open the file.
        :param logger: The logger.
        :returns: Returns file type in case it was detected successfully otherwise returns default :py:attr:`groupdocs.viewer.FileType.UNKNOWN` file type.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def detect_encoding(file_path : str) -> str:
        '''Attempts to detect text :py:attr:`groupdocs.viewer.FileType.TXT`, :py:attr:`groupdocs.viewer.FileType.TSV`, and :py:attr:`groupdocs.viewer.FileType.CSV` files encoding by path.
        
        :param file_path: The file name or file path.
        :returns: Encoding or null when fails to detect a file encoding.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def detect_encoding(stream : io._IOBase) -> str:
        '''Attempts to detect text :py:attr:`groupdocs.viewer.FileType.TXT`, :py:attr:`groupdocs.viewer.FileType.TSV`, and :py:attr:`groupdocs.viewer.FileType.CSV` file encoding by stream.
        
        :param stream: The file stream.
        :returns: Encoding or null when fails to detect a file encoding.'''
        raise NotImplementedError()
    
    @staticmethod
    def from_extension(extension : str) -> groupdocs.viewer.FileType:
        '''Maps file extension to file type.
        
        :param extension: File extension with or without the period ".".
        :returns: When file type is supported returns it, otherwise returns default :py:attr:`groupdocs.viewer.FileType.UNKNOWN` file type.'''
        raise NotImplementedError()
    
    @staticmethod
    def from_file_path(file_path : str) -> groupdocs.viewer.FileType:
        '''Extracts file extension and maps it to file type.
        
        :param file_path: The file name or file path.
        :returns: When file type is supported returns it, otherwise returns default :py:attr:`groupdocs.viewer.FileType.UNKNOWN` file type.'''
        raise NotImplementedError()
    
    @staticmethod
    def from_media_type(media_type : str) -> groupdocs.viewer.FileType:
        '''Maps file media type to file type e.g. \'application/pdf\' will be mapped to :py:attr:`groupdocs.viewer.FileType.PDF`.
        
        :param media_type: File media type e.g. application/pdf.
        :returns: Returns corresponding media type when found, otherwise returns default :py:attr:`groupdocs.viewer.FileType.UNKNOWN` file type.'''
        raise NotImplementedError()
    
    @staticmethod
    def get_supported_file_types() -> System.Collections.Generic.IEnumerable`1[[GroupDocs.Viewer.FileType]]:
        '''Retrieves supported file types
        
        :returns: Returns sequence of supported file types'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.viewer.FileType) -> bool:
        '''Determines whether the current :py:class:`groupdocs.viewer.FileType` is the same as specified :py:class:`groupdocs.viewer.FileType` object.
        
        :param other: The object to compare with the current :py:class:`groupdocs.viewer.FileType` object.
        :returns: true
        if both :py:class:`groupdocs.viewer.FileType` objects are the same; otherwise,     false'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> str:
        '''File type name e.g. "Microsoft Word Document".'''
        raise NotImplementedError()
    
    @file_format.setter
    def file_format(self, value : str) -> None:
        '''File type name e.g. "Microsoft Word Document".'''
        raise NotImplementedError()
    
    @property
    def extension(self) -> str:
        '''Filename suffix (including the period ".") e.g. ".doc".'''
        raise NotImplementedError()
    
    @extension.setter
    def extension(self, value : str) -> None:
        '''Filename suffix (including the period ".") e.g. ".doc".'''
        raise NotImplementedError()
    
    @property
    def UNKNOWN(self) -> groupdocs.viewer.FileType:
        '''Represents unknown file type.'''
        raise NotImplementedError()

    @property
    def ZIP(self) -> groupdocs.viewer.FileType:
        '''Zipped File (.zip) represents archives that can hold one or more files or directories.
        Learn more about this file format `here <https://wiki.fileformat.com/compression/zip>`.'''
        raise NotImplementedError()

    @property
    def TAR(self) -> groupdocs.viewer.FileType:
        '''Consolidated Unix File Archive (.tar) are archives created with Unix-based utility for collecting one or more files.
        Learn more about this file format `here <https://wiki.fileformat.com/compression/tar>`.'''
        raise NotImplementedError()

    @property
    def XZ(self) -> groupdocs.viewer.FileType:
        '''XZ file (.xz) is archive compressed a high-ratio compression algorithm based on the LZMA algorithm.
        Learn more about this file format `here <https://fileinfo.com/extension/xz>`.'''
        raise NotImplementedError()

    @property
    def TXZ(self) -> groupdocs.viewer.FileType:
        '''Consolidated Unix File Archive (.txz, .tar.xz) are archives created with Unix-based utility for collecting one or more files.
        Learn more about this file format `here <https://fileinfo.com/extension/txz>`.'''
        raise NotImplementedError()

    @property
    def TARXZ(self) -> groupdocs.viewer.FileType:
        '''Consolidated Unix File Archive (.txz, .tar.xz) are archives created with Unix-based utility for collecting one or more files.
        Learn more about this file format `here <https://fileinfo.com/extension/txz>`.'''
        raise NotImplementedError()

    @property
    def TGZ(self) -> groupdocs.viewer.FileType:
        '''Consolidated Unix File Archive (.tgz, .tar.gz) are archives created with Unix-based utility for collecting one or more files.
        Learn more about this file format `here <https://fileinfo.com/extension/tgz>`.'''
        raise NotImplementedError()

    @property
    def TARGZ(self) -> groupdocs.viewer.FileType:
        '''Consolidated Unix File Archive (.tgz, .tar.gz) are archives created with Unix-based utility for collecting one or more files.
        Learn more about this file format `here <https://fileinfo.com/extension/tgz>`.'''
        raise NotImplementedError()

    @property
    def BZ2(self) -> groupdocs.viewer.FileType:
        '''Bzip2 Compressed File (.bz2) are compressed files generated using the BZIP2 open source compression method, mostly on UNIX or Linux system.
        Learn more about this file format `here <https://wiki.fileformat.com/compression/bz2>`.'''
        raise NotImplementedError()

    @property
    def RAR(self) -> groupdocs.viewer.FileType:
        '''Roshal ARchive (.rar) are compressed files generated using the RAR (WINRAR) compression method.
        Learn more about this file format `here <https://wiki.fileformat.com/compression/rar>`.'''
        raise NotImplementedError()

    @property
    def GZ(self) -> groupdocs.viewer.FileType:
        '''Gnu Zipped File (.gz) are compressed files created with gzip compression application. It can contain multiple compressed files and is commonly used on UNIX and Linux systems.
        Learn more about this file format `here <https://wiki.fileformat.com/compression/gz>`.'''
        raise NotImplementedError()

    @property
    def GZIP(self) -> groupdocs.viewer.FileType:
        '''Gnu Zipped File (.gzip) was introduced as a free utility for replacing the Compress program used in Unix systems. Such files can be opened and extracted with a several applications such as WinZip which is available on both Windows and MacOS.
        Learn more about this file format `here <https://wiki.fileformat.com/compression/gz>`.'''
        raise NotImplementedError()

    @property
    def SEVEN_ZIP(self) -> groupdocs.viewer.FileType:
        '''7Zip (.7z, .7zip) is free open source archiver with LZMA and LZMA2 compression.
        Learn more about this file format `here <https://docs.fileformat.com/compression/7z/>`.'''
        raise NotImplementedError()

    @property
    def CPIO(self) -> groupdocs.viewer.FileType:
        '''Cpio is a general file archiver utility and its associated file format. It is primarily installed on Unix-like computer operating systems.
        Learn more about this file format `here <https://wiki.fileformat.com/compression/cpio>`.'''
        raise NotImplementedError()

    @property
    def ZSTANDARD(self) -> groupdocs.viewer.FileType:
        '''ZST file is a compressed file that is generated with the Zstandard (zstd) compression algorithm. It is a compressed file that is created with lossless compression by the algorithm. ZST files can be used to compress different types of files such as databases, file systems, networks, and games.
        Learn more about this file format `here <https://docs.fileformat.com/compression/zst/>`.'''
        raise NotImplementedError()

    @property
    def TZST(self) -> groupdocs.viewer.FileType:
        '''TZST files (.tar.zst, .tzst) are Zstandard archives (ZST), which internally contain a Consolidated Unix File Archive (Tar), created with Unix-based utility for collecting one or more files.'''
        raise NotImplementedError()

    @property
    def TAR_ZST(self) -> groupdocs.viewer.FileType:
        '''TZST files (.tar.zst, .tzst) are Zstandard archives (ZST), which internally contain a Consolidated Unix File Archive (Tar), created with Unix-based utility for collecting one or more files.'''
        raise NotImplementedError()

    @property
    def ISO(self) -> groupdocs.viewer.FileType:
        '''ISO optical disc image is an uncompressed archive disk image file that represents the contents of entire data on an optical disc such as CD or DVD, based on the ISO-9660 standard.
        Learn more about this file format `here <https://docs.fileformat.com/compression/iso/>`.'''
        raise NotImplementedError()

    @property
    def DXF(self) -> groupdocs.viewer.FileType:
        '''Drawing Exchange Format File (.dxf) is a tagged data representation of AutoCAD drawing file.
        Learn more about this file format `here <https://wiki.fileformat.com/cad/dxf>`.'''
        raise NotImplementedError()

    @property
    def DWG(self) -> groupdocs.viewer.FileType:
        '''AutoCAD Drawing Database File (.dwg) represents proprietary binary files used for containing 2D and 3D design data. Like DXF, which are ASCII files, DWG represent the binary file format for CAD (Computer Aided Design) drawings.
        Learn more about this file format `here <https://wiki.fileformat.com/cad/dwg>`.'''
        raise NotImplementedError()

    @property
    def DWT(self) -> groupdocs.viewer.FileType:
        '''AutoCAD Drawing Template (.dwt) is an AutoCAD drawing template file that is used as starter for creating drawings that can be saved as DWG files.
        Learn more about this file format `here <https://wiki.fileformat.com/cad/dwt>`.'''
        raise NotImplementedError()

    @property
    def STL(self) -> groupdocs.viewer.FileType:
        '''Stereolithography File (.stl) is an interchangeable file format that represents 3-dimensional surface geometry. The file format finds its usage in several fields such as rapid prototyping, 3D printing and computer-aided manufacturing.
        Learn more about this file format `here <https://wiki.fileformat.com/cad/stl>`.'''
        raise NotImplementedError()

    @property
    def IFC(self) -> groupdocs.viewer.FileType:
        '''Industry Foundation Classes File (.ifc) is a file format that establishes international standards to import and export building objects and their properties. This file format provides interoperability between different software applications.
        Learn more about this file format `here <https://wiki.fileformat.com/cad/ifc>`.'''
        raise NotImplementedError()

    @property
    def DWF(self) -> groupdocs.viewer.FileType:
        '''Design Web Format File (.dwf) represents 2D/3D drawing in compressed format for viewing, reviewing or printing design files. It contains graphics and text as part of design data and reduce the size of the file due to its compressed format.
        Learn more about this file format `here <https://wiki.fileformat.com/cad/dwf>`.'''
        raise NotImplementedError()

    @property
    def FBX(self) -> groupdocs.viewer.FileType:
        '''Autodesk FBX Interchange File (FilmBoX) (.fbx) represents 3D model format.
        Learn more about this file format `here <https://wiki.fileformat.com/cad/fbx>`.'''
        raise NotImplementedError()

    @property
    def DWFX(self) -> groupdocs.viewer.FileType:
        '''Design Web Format File XPS (.dwfx) represents 2D/3D drawing as XPS document in compressed format for viewing, reviewing or printing design files. It contains graphics and text as part of design data and reduce the size of the file due to its compressed format.
        Learn more about this file format `here <https://wiki.fileformat.com/cad/dwfx>`.'''
        raise NotImplementedError()

    @property
    def DGN(self) -> groupdocs.viewer.FileType:
        '''MicroStation Design File (.dgn) are drawings created by and supported by CAD applications such as MicroStation and Intergraph Interactive Graphics Design System.
        Learn more about this file format `here <https://wiki.fileformat.com/cad/dgn>`.'''
        raise NotImplementedError()

    @property
    def PLT(self) -> groupdocs.viewer.FileType:
        '''PLT (HPGL) (.plt) is a vector-based plotter file introduced by Autodesk, Inc. and contains information for a certain CAD file. Plotting details require accuracy and precision in production, and usage of PLT file guarantee this as all images are printed using lines instead of dots.
        Learn more about this file format `here <https://wiki.fileformat.com/cad/plt>`.'''
        raise NotImplementedError()

    @property
    def CF2(self) -> groupdocs.viewer.FileType:
        '''Common File Format File
        Learn more about this file format `here <https://fileinfo.com/extension/cf2>`.'''
        raise NotImplementedError()

    @property
    def OBJ(self) -> groupdocs.viewer.FileType:
        '''Wavefront 3D Object File (.obj) is 3D image file introduced by Wavefront Technologies
        Learn more about this file format `here <https://wiki.fileformat.com/3d/obj/>`.'''
        raise NotImplementedError()

    @property
    def HPG(self) -> groupdocs.viewer.FileType:
        '''PLT (HPGL) (.hpg)'''
        raise NotImplementedError()

    @property
    def IGS(self) -> groupdocs.viewer.FileType:
        '''Initial Graphics Exchange Specification (IGES) (.igs)'''
        raise NotImplementedError()

    @property
    def VSD(self) -> groupdocs.viewer.FileType:
        '''Visio Drawing File (.vsd) are drawings created with Microsoft Visio application to represent variety of graphical objects and the interconnection between these.
        Learn more about this file format `here <https://wiki.fileformat.com/image/vsd>`.'''
        raise NotImplementedError()

    @property
    def VSDX(self) -> groupdocs.viewer.FileType:
        '''Visio Drawing (.vsdx) represents Microsoft Visio file format introduced from Microsoft Office 2013 onwards. It was developed to replace the binary file format, .VSD, which is supported by earlier versions of Microsoft Visio.
        Learn more about this file format `here <https://wiki.fileformat.com/image/vsdx>`.'''
        raise NotImplementedError()

    @property
    def VSS(self) -> groupdocs.viewer.FileType:
        '''Visio Stencil File(.vss) are stencil files created with Microsoft Visio 2007 and earlier. Stencil files provide drawing objects that can be included in a .VSD Visio drawing.
        Learn more about this file format `here <https://wiki.fileformat.com/image/vss>`.'''
        raise NotImplementedError()

    @property
    def VSSX(self) -> groupdocs.viewer.FileType:
        '''Visio Stencil File (.vssx) are drawing stencils created with Microsoft Visio 2013 and above. The VSSX file format can be opened with Visio 2013 and above. Visio files are known for representation of a variety of drawing elements such as collection of shapes, connectors, flowcharts, network layout, UML diagrams,
        Learn more about this file format `here <https://wiki.fileformat.com/image/vssx>`.'''
        raise NotImplementedError()

    @property
    def VSDM(self) -> groupdocs.viewer.FileType:
        '''Visio Macro-Enabled Drawing (.vsdm) are drawing files created with Microsoft Visio application that supports macros. VSDM files are OPC/XML drawings that are similar to VSDX, but also provide the capability to run macros when the file is opened.
        Learn more about this file format `here <https://wiki.fileformat.com/image/vsdm>`.'''
        raise NotImplementedError()

    @property
    def VST(self) -> groupdocs.viewer.FileType:
        '''Visio Drawing Template (.vst) are vector image files created with Microsoft Visio and act as template for creating further files. These template files are in binary file format and contain the default layout and settings that are utilized for creation of new Visio drawings.
        Learn more about this file format `here <https://wiki.fileformat.com/image/vst>`.'''
        raise NotImplementedError()

    @property
    def VSTX(self) -> groupdocs.viewer.FileType:
        '''Visio Drawing Template (.vstx) are drawing template files created with Microsoft Visio 2013 and above. These VSTX files provide starting point for creating Visio drawings, saved as .VSDX files, with default layout and settings.
        Learn more about this file format `here <https://wiki.fileformat.com/image/vstx>`.'''
        raise NotImplementedError()

    @property
    def VSTM(self) -> groupdocs.viewer.FileType:
        '''Visio Macro-Enabled Drawing Template (.vstm) are template files created with Microsoft Visio that support macros. Unlike VSDX files, files created from VSTM templates can run macros that are developed in Visual Basic for Applications (VBA)  code.
        Learn more about this file format `here <https://wiki.fileformat.com/image/vstm>`.'''
        raise NotImplementedError()

    @property
    def VSSM(self) -> groupdocs.viewer.FileType:
        '''Visio Macro-Enabled Stencil File (.vssm) are Microsoft Visio Stencil files that support provide support for macros. A VSSM file when opened allows to run the macros to achieve desired formatting and placement of shapes in a diagram.
        Learn more about this file format `here <https://wiki.fileformat.com/image/vssm>`.'''
        raise NotImplementedError()

    @property
    def VSX(self) -> groupdocs.viewer.FileType:
        '''Visio Stencil XML File (.vsx) refers to stencils that consist of drawings and shapes that are used for creating diagrams in Microsoft Visio. VSX files are saved in XML file format and was supported till Visio 2013.
        Learn more about this file format `here <https://wiki.fileformat.com/image/vsx>`.'''
        raise NotImplementedError()

    @property
    def VTX(self) -> groupdocs.viewer.FileType:
        '''Visio Template XML File (.vtx) is a Microsoft Visio drawing template that is saved to disc in XML file format. The template is aimed to provide a file with basic settings that can be used to create multiple Visio files of the same settings.
        Learn more about this file format `here <https://wiki.fileformat.com/image/vtx>`.'''
        raise NotImplementedError()

    @property
    def VDW(self) -> groupdocs.viewer.FileType:
        '''Visio Web Drawing (.vdw) represents file format that specifies the streams and storages required for rendering a Web drawing.
        Learn more about this file format `here <https://wiki.fileformat.com/web/vdw>`.'''
        raise NotImplementedError()

    @property
    def VDX(self) -> groupdocs.viewer.FileType:
        '''Visio Drawing XML File (.vdx) represents any drawing or chart created in Microsoft Visio, but saved in XML format have .VDX extension. A Visio drawing XML file is created in Visio software, which is developed by Microsoft.
        Learn more about this file format `here <https://wiki.fileformat.com/image/vdx>`.'''
        raise NotImplementedError()

    @property
    def EPUB(self) -> groupdocs.viewer.FileType:
        '''Open eBook File (.epub) is an e-book file format that provide a standard digital publication format for publishers and consumers. The format has been so common by now that it is supported by many e-readers and software applications.
        Learn more about this file format `here <https://wiki.fileformat.com/ebook/epub>`.'''
        raise NotImplementedError()

    @property
    def MOBI(self) -> groupdocs.viewer.FileType:
        '''Mobipocket eBook (.mobi) is one of the most widely used ebook file format. The format is an enhancement to the old OEB (Open Ebook Format) format and was used as proprietary format for Mobipocket Reader.
        Learn more about this file format `here <https://wiki.fileformat.com/ebook/mobi>`.'''
        raise NotImplementedError()

    @property
    def AZW3(self) -> groupdocs.viewer.FileType:
        '''Amazon Kindle Format 8 (KF8) ebook is the digital file format developed for Amazon Kindle devices. The format is an enhancement to older AZW files and is used on Kindle Fire devices only with backward compatibility for the ancestor file format i.e. MOBI and AZW.
        Learn more about this file format `here <https://wiki.fileformat.com/ebook/azw3>`.'''
        raise NotImplementedError()

    @property
    def MSG(self) -> groupdocs.viewer.FileType:
        '''Outlook Mail Message (.msg) is a file format used by Microsoft Outlook and Exchange to store email messages, contact, appointment, or other tasks.
        Learn more about this file format `here <https://wiki.fileformat.com/email/msg>`.'''
        raise NotImplementedError()

    @property
    def EML(self) -> groupdocs.viewer.FileType:
        '''E-Mail Message (.eml) represents email messages saved using Outlook and other relevant applications. Almost all emailing clients support this file format for its compliance with RFC-822 Internet Message Format Standard.
        Learn more about this file format `here <https://wiki.fileformat.com/email/eml>`.'''
        raise NotImplementedError()

    @property
    def NSF(self) -> groupdocs.viewer.FileType:
        '''Lotus Notes Database (.nsf)
        Learn more about this file format `here <https://fileinfo.com/extension/nsf>`.'''
        raise NotImplementedError()

    @property
    def MBOX(self) -> groupdocs.viewer.FileType:
        '''Email Mailbox File (.mbox)
        Learn more about this file format `here <https://fileinfo.com/extension/mbox>`.'''
        raise NotImplementedError()

    @property
    def EMLX(self) -> groupdocs.viewer.FileType:
        '''Apple Mail Message (.emlx) is implemented and developed by Apple. The Apple Mail application uses the EMLX file format for exporting the emails.
        Learn more about this file format `here <https://wiki.fileformat.com/email/emlx>`.'''
        raise NotImplementedError()

    @property
    def PST(self) -> groupdocs.viewer.FileType:
        '''Outlook Personal Information Store File (.pst) represents Outlook Personal Storage Files (also called Personal Storage Table) that store variety of user information.
        Learn more about this file format `here <https://wiki.fileformat.com/email/pst>`.'''
        raise NotImplementedError()

    @property
    def OST(self) -> groupdocs.viewer.FileType:
        '''Outlook Offline Data File (.ost) represents user\'s mailbox data in offline mode on local machine upon registration with Exchange Server using Microsoft Outlook.
        Learn more about this file format `here <https://wiki.fileformat.com/email/ost>`.'''
        raise NotImplementedError()

    @property
    def TIF(self) -> groupdocs.viewer.FileType:
        '''Tagged Image File (.tif) represents raster images that are meant for usage on a variety of devices that comply with this file format standard. It is capable of describing bilevel, grayscale, palette-color and full-color image data in several color spaces.
        Learn more about this file format `here <https://wiki.fileformat.com/image/tiff>`.'''
        raise NotImplementedError()

    @property
    def TIFF(self) -> groupdocs.viewer.FileType:
        '''Tagged Image File Format (.tiff) represents raster images that are meant for usage on a variety of devices that comply with this file format standard. It is capable of describing bilevel, grayscale, palette-color and full-color image data in several color spaces.
        Learn more about this file format `here <https://wiki.fileformat.com/image/tiff>`.'''
        raise NotImplementedError()

    @property
    def JPG(self) -> groupdocs.viewer.FileType:
        '''JPEG Image (.jpg) is a type of image format that is saved using the method of lossy compression. The output image, as result of compression, is a trade-off between storage size and image quality.
        Learn more about this file format `here <https://wiki.fileformat.com/image/jpeg>`.'''
        raise NotImplementedError()

    @property
    def JPEG(self) -> groupdocs.viewer.FileType:
        '''JPEG Image (.jpeg) is a type of image format that is saved using the method of lossy compression. The output image, as result of compression, is a trade-off between storage size and image quality.
        Learn more about this file format `here <https://wiki.fileformat.com/image/jpeg>`.'''
        raise NotImplementedError()

    @property
    def JFIF(self) -> groupdocs.viewer.FileType:
        '''JPEG File Interchange Format (.jfif) is image that was developed for fast exchange between platforms.
        This format uses JPEG compression. Learn more about this file format `here <https://wiki.fileformat.com/image/jfif>`.'''
        raise NotImplementedError()

    @property
    def PNG(self) -> groupdocs.viewer.FileType:
        '''Portable Network Graphic (.png) is a type of raster image file format that use loseless compression. This file format was created as a replacement of Graphics Interchange Format (GIF) and has no copyright limitations.
        Learn more about this file format `here <https://wiki.fileformat.com/image/png>`.'''
        raise NotImplementedError()

    @property
    def GIF(self) -> groupdocs.viewer.FileType:
        '''Graphical Interchange Format File (.gif) is a type of highly compressed image. For each image GIF typically allow up to 8 bits per pixel and up to 256 colours are allowed across the image.
        Learn more about this file format `here <https://wiki.fileformat.com/image/gif>`.'''
        raise NotImplementedError()

    @property
    def APNG(self) -> groupdocs.viewer.FileType:
        '''Animated Portable Network Graphic (.apng) is extension of  PNG format that support animation.
        Learn more about this file format `here <https://wiki.fileformat.com/image/apng>`.'''
        raise NotImplementedError()

    @property
    def BMP(self) -> groupdocs.viewer.FileType:
        '''Bitmap Image File (.bmp) is used to store bitmap digital images. These images are independent of graphics adapter and are also called device independent bitmap (DIB) file format.
        Learn more about this file format `here <https://wiki.fileformat.com/image/bmp>`.'''
        raise NotImplementedError()

    @property
    def TGA(self) -> groupdocs.viewer.FileType:
        '''Truevision TGA (Truevision Advanced Raster Adapter - TARGA) is used to store bitmap digital images developed by TRUEVISION.
        Learn more about this file format `here <https://wiki.fileformat.com/image/tga>`.'''
        raise NotImplementedError()

    @property
    def ICO(self) -> groupdocs.viewer.FileType:
        '''Icon File (.ico) are image file types used as icon for representation of an application on Microsoft Windows.
        Learn more about this file format `here <https://wiki.fileformat.com/image/ico>`.'''
        raise NotImplementedError()

    @property
    def JP2(self) -> groupdocs.viewer.FileType:
        '''JPEG 2000 Core Image File (.jp2) is an image coding system and state-of-the-art image compression standard.
        Learn more about this file format `here <https://wiki.fileformat.com/image/jp2>`.'''
        raise NotImplementedError()

    @property
    def JPF(self) -> groupdocs.viewer.FileType:
        '''JPEG 2000 Image File (.jpf)'''
        raise NotImplementedError()

    @property
    def JPX(self) -> groupdocs.viewer.FileType:
        '''JPEG 2000 Image File (.jpx)'''
        raise NotImplementedError()

    @property
    def JPM(self) -> groupdocs.viewer.FileType:
        '''JPEG 2000 Image File (.jpm)'''
        raise NotImplementedError()

    @property
    def J2C(self) -> groupdocs.viewer.FileType:
        '''JPEG 2000 Code Stream (.j2c)'''
        raise NotImplementedError()

    @property
    def J2K(self) -> groupdocs.viewer.FileType:
        '''JPEG 2000 Code Stream (.j2k) is an image that is compressed using the wavelet compression instead of DCT compression.
        Learn more about this file format `here <https://wiki.fileformat.com/image/j2k>`.'''
        raise NotImplementedError()

    @property
    def JPC(self) -> groupdocs.viewer.FileType:
        '''JPEG 2000 Code Stream (.jpc)'''
        raise NotImplementedError()

    @property
    def JLS(self) -> groupdocs.viewer.FileType:
        '''JPEG-LS (JLS) (.jls)'''
        raise NotImplementedError()

    @property
    def DIB(self) -> groupdocs.viewer.FileType:
        '''Device Independent Bitmap File (.dib)'''
        raise NotImplementedError()

    @property
    def WMF(self) -> groupdocs.viewer.FileType:
        '''Windows Metafile (.wmf) represents Microsoft Windows Metafile (WMF) for storing vector as well as bitmap-format images data.
        Learn more about this file format `here <https://wiki.fileformat.com/image/wmf>`.'''
        raise NotImplementedError()

    @property
    def WMZ(self) -> groupdocs.viewer.FileType:
        '''Compressed Windows Metafile (.wmz) represents Microsoft Windows Metafile (WMF) compressed in GZIP archvive - for storing vector as well as bitmap-format images data.
        Learn more about this file format `here <https://fileinfo.com/extension/wmz#compressed_windows_metafile>`.'''
        raise NotImplementedError()

    @property
    def EMF(self) -> groupdocs.viewer.FileType:
        '''Enhanced Windows Metafile (.emf) represents graphical images device-independently. Metafiles of EMF comprises of variable-length records in chronological order that can render the stored image after parsing on any output device.
        Learn more about this file format `here <https://wiki.fileformat.com/image/emf>`.'''
        raise NotImplementedError()

    @property
    def EMZ(self) -> groupdocs.viewer.FileType:
        '''Enhanced Windows Metafile compressed (.emz) represents graphical images device-independently compressed by GZIP. Metafiles of EMF comprises of variable-length records in chronological order that can render the stored image after parsing on any output device.
        Learn more about this file format `here <https://wiki.fileformat.com/image/emz>`.'''
        raise NotImplementedError()

    @property
    def WEBP(self) -> groupdocs.viewer.FileType:
        '''WebP Image (.webp) is a modern raster web image file format that is based on lossless and lossy compression. It provides same image quality while considerably reducing the image size.
        Learn more about this file format `here <https://wiki.fileformat.com/image/webp>`.'''
        raise NotImplementedError()

    @property
    def DNG(self) -> groupdocs.viewer.FileType:
        '''Digital Negative Specification (.dng) is a digital camera image format used for the storage of raw files. It has been developed by Adobe in September 2004. It was basically developed for digital photography.
        Learn more about this file format `here <https://wiki.fileformat.com/image/dng>`.'''
        raise NotImplementedError()

    @property
    def CDR(self) -> groupdocs.viewer.FileType:
        '''CorelDraw Vector Graphic Drawing (.cdr) is a vector drawing image file that is natively created with CorelDRAW for storing digital image encoded and compressed. Such a drawing file contains text, lines, shapes, images, colours and effects for vector representation of image contents.
        Learn more about this file format `here <https://wiki.fileformat.com/image/cdr>`.'''
        raise NotImplementedError()

    @property
    def CMX(self) -> groupdocs.viewer.FileType:
        '''Corel Exchange (.cmx) is a drawing image file that may contain vector graphics as well as bitmap graphics.
        Learn more about this file format `here <https://wiki.fileformat.com/image/cmx>`.'''
        raise NotImplementedError()

    @property
    def DJVU(self) -> groupdocs.viewer.FileType:
        '''DjVu Image (.djvu) is a graphics file format intended for scanned documents and books especially those which contain the combination of text, drawings, images and photographs.
        Learn more about this file format `here <https://wiki.fileformat.com/image/djvu>`.'''
        raise NotImplementedError()

    @property
    def CGM(self) -> groupdocs.viewer.FileType:
        '''Computer Graphics Metafile (.cgm) is a free, platform-independent, international standard metafile format for storing and exchanging of vector graphics (2D), raster graphics, and text. CGM uses object-oriented approach and many function provisions for image production.
        Learn more about this file format `here <https://wiki.fileformat.com/page-description-language/cgm>`.'''
        raise NotImplementedError()

    @property
    def PCL(self) -> groupdocs.viewer.FileType:
        '''Printer Command Language Document (.pcl)'''
        raise NotImplementedError()

    @property
    def PSD(self) -> groupdocs.viewer.FileType:
        '''Adobe Photoshop Document (.psd) represents Adobe Photoshop\'s native file format used for graphics designing and development.
        Learn more about this file format `here <https://wiki.fileformat.com/image/psd>`.'''
        raise NotImplementedError()

    @property
    def PSB(self) -> groupdocs.viewer.FileType:
        '''Photoshop Large Document Format (.psb) represents Photoshop Large Document Format used for graphics designing and development.
        Learn more about this file format `here <https://wiki.fileformat.com/image/psb>`.'''
        raise NotImplementedError()

    @property
    def DCM(self) -> groupdocs.viewer.FileType:
        '''DICOM Image (.dcm) represents digital image which stores medical information of patients such as MRIs, CT scans and ultrasound images.
        Learn more about this file format `here <https://wiki.fileformat.com/image/dcm>`.'''
        raise NotImplementedError()

    @property
    def PS(self) -> groupdocs.viewer.FileType:
        '''PostScript File (.ps)'''
        raise NotImplementedError()

    @property
    def EPS(self) -> groupdocs.viewer.FileType:
        '''Encapsulated PostScript File (.eps) describes an Encapsulated PostScript language program that describes the appearance of a single page.
        Learn more about this file format `here <https://wiki.fileformat.com/page-description-language/eps>`.'''
        raise NotImplementedError()

    @property
    def ODG(self) -> groupdocs.viewer.FileType:
        '''OpenDocument Graphic File (.odg) is used by Apache OpenOffice\'s Draw application to store drawing elements as a vector image.
        Learn more about this file format `here <https://wiki.fileformat.com/image/odg>`.'''
        raise NotImplementedError()

    @property
    def FODG(self) -> groupdocs.viewer.FileType:
        '''Flat XML ODF Template (.fodg) is used by Apache OpenOffice\'s Draw application to store drawing elements as a vector image.
        Learn more about this file format `here <https://wiki.fileformat.com/image/fodg>`.'''
        raise NotImplementedError()

    @property
    def SVG(self) -> groupdocs.viewer.FileType:
        '''Scalable Vector Graphics File (.svg) is a Scalar Vector Graphics file that uses XML based text format for describing the appearance of an image.
        Learn more about this file format `here <https://wiki.fileformat.com/page-description-language/svg>`.'''
        raise NotImplementedError()

    @property
    def SVGZ(self) -> groupdocs.viewer.FileType:
        '''Scalable Vector Graphics File (.svgz) is a Scalar Vector Graphics file that uses XML based text format, compressed by GZIP for describing the appearance of an image.
        Learn more about this file format `here <https://fileinfo.com/extension/svgz>`.'''
        raise NotImplementedError()

    @property
    def OTG(self) -> groupdocs.viewer.FileType:
        '''OpenDocument Graphic Template (.otg)'''
        raise NotImplementedError()

    @property
    def HTM(self) -> groupdocs.viewer.FileType:
        '''Hypertext Markup Language File (.htm) is the extension for web pages created for display in browsers.
        Learn more about this file format `here <https://wiki.fileformat.com/web/html>`.'''
        raise NotImplementedError()

    @property
    def HTML(self) -> groupdocs.viewer.FileType:
        '''Hypertext Markup Language File (.html) is the extension for web pages created for display in browsers.
        Learn more about this file format `here <https://wiki.fileformat.com/web/html>`.'''
        raise NotImplementedError()

    @property
    def MHT(self) -> groupdocs.viewer.FileType:
        '''MHTML Web Archive (.mht)'''
        raise NotImplementedError()

    @property
    def MHTML(self) -> groupdocs.viewer.FileType:
        '''MIME HTML File (.mhtml)'''
        raise NotImplementedError()

    @property
    def XML(self) -> groupdocs.viewer.FileType:
        '''XML File (.xml)'''
        raise NotImplementedError()

    @property
    def ONE(self) -> groupdocs.viewer.FileType:
        '''OneNote Document (.one) is created by Microsoft OneNote application. OneNote lets you gather information using the application as if you are using your draftpad for taking notes.
        Learn more about this file format `here <https://wiki.fileformat.com/note-taking/one>`.'''
        raise NotImplementedError()

    @property
    def PDF(self) -> groupdocs.viewer.FileType:
        '''Portable Document Format File (.pdf) is a type of document created by Adobe back in 1990s. The purpose of this file format was to introduce a standard for representation of documents and other reference material in a format that is independent of application software, hardware as well as Operating System.
        Learn more about this file format `here <https://wiki.fileformat.com/view/pdf>`.'''
        raise NotImplementedError()

    @property
    def XPS(self) -> groupdocs.viewer.FileType:
        '''XML Paper Specification File (.xps) represents page layout files that are based on XML Paper Specifications created by Microsoft. This format was developed by Microsoft as a replacement of EMF file format and is similar to PDF file format, but uses XML in layout, appearance, and printing information of a document.
        Learn more about this file format `here <https://wiki.fileformat.com/page-description-language/xps>`.'''
        raise NotImplementedError()

    @property
    def OXPS(self) -> groupdocs.viewer.FileType:
        '''OpenXPS File (.oxps)'''
        raise NotImplementedError()

    @property
    def TEX(self) -> groupdocs.viewer.FileType:
        '''LaTeX Source Document (.tex) is a language that comprises of programming as well as mark-up features, used to typeset documents.
        Learn more about this file format `here <https://wiki.fileformat.com/page-description-language/tex>`.'''
        raise NotImplementedError()

    @property
    def PPT(self) -> groupdocs.viewer.FileType:
        '''PowerPoint Presentation (.ppt) represents PowerPoint file that consists of a collection of slides for displaying as SlideShow. It specifies the Binary File Format used by Microsoft PowerPoint 97-2003.
        Learn more about this file format `here <https://wiki.fileformat.com/presentation/ppt>`.'''
        raise NotImplementedError()

    @property
    def PPTX(self) -> groupdocs.viewer.FileType:
        '''PowerPoint Open XML Presentation (.pptx) are presentation files created with popular Microsoft PowerPoint application. Unlike the previous version of presentation file format PPT which was binary, the PPTX format is based on the Microsoft PowerPoint open XML presentation file format.
        Learn more about this file format `here <https://wiki.fileformat.com/presentation/pptx>`.'''
        raise NotImplementedError()

    @property
    def PPS(self) -> groupdocs.viewer.FileType:
        '''PowerPoint Slide Show (.pps) are created using Microsoft PowerPoint for Slide Show purpose. PPS file reading and creation is supported by Microsoft PowerPoint 97-2003.
        Learn more about this file format `here <https://wiki.fileformat.com/presentation/pps>`.'''
        raise NotImplementedError()

    @property
    def PPSX(self) -> groupdocs.viewer.FileType:
        '''PowerPoint Open XML Slide Show (.ppsx) files are created using Microsoft PowerPoint 2007 and above for Slide Show purpose.
        Learn more about this file format `here <https://wiki.fileformat.com/presentation/ppsx>`.'''
        raise NotImplementedError()

    @property
    def ODP(self) -> groupdocs.viewer.FileType:
        '''OpenDocument Presentation (.odp) represents presentation file format used by OpenOffice.org in the OASISOpen standard.
        Learn more about this file format `here <https://wiki.fileformat.com/presentation/odp>`.'''
        raise NotImplementedError()

    @property
    def FODP(self) -> groupdocs.viewer.FileType:
        '''OpenDocument Presentation (.fodp) represents OpenDocument Flat XML Presentation.
        Learn more about this file format `here <https://fileinfo.com/extension/fodp>`.'''
        raise NotImplementedError()

    @property
    def POT(self) -> groupdocs.viewer.FileType:
        '''PowerPoint Template (.pot) represents Microsoft PowerPoint template files created by PowerPoint 97-2003 versions.
        Learn more about this file format `here <https://wiki.fileformat.com/presentation/pot>`.'''
        raise NotImplementedError()

    @property
    def PPTM(self) -> groupdocs.viewer.FileType:
        '''PowerPoint Open XML Macro-Enabled Presentation are Macro-enabled Presentation files that are created with Microsoft PowerPoint 2007 or higher versions.
        Learn more about this file format `here <https://wiki.fileformat.com/presentation/pptm>`.'''
        raise NotImplementedError()

    @property
    def POTX(self) -> groupdocs.viewer.FileType:
        '''PowerPoint Open XML Presentation Template (.potx) represents Microsoft PowerPoint template presentations that are created with Microsoft PowerPoint 2007 and above.
        Learn more about this file format `here <https://wiki.fileformat.com/presentation/potx>`.'''
        raise NotImplementedError()

    @property
    def POTM(self) -> groupdocs.viewer.FileType:
        '''PowerPoint Open XML Macro-Enabled Presentation Template (.potm) are Microsoft PowerPoint template files with support for Macros. POTM files are created with PowerPoint 2007 or above and contains default settings that can be used to create further presentation files.
        Learn more about this file format `here <https://wiki.fileformat.com/presentation/potm>`.'''
        raise NotImplementedError()

    @property
    def PPSM(self) -> groupdocs.viewer.FileType:
        '''PowerPoint Open XML Macro-Enabled Slide (.ppsm) represents Macro-enabled Slide Show file format created with Microsoft PowerPoint 2007 or higher.
        Learn more about this file format `here <https://wiki.fileformat.com/presentation/ppsm>`.'''
        raise NotImplementedError()

    @property
    def OTP(self) -> groupdocs.viewer.FileType:
        '''OpenDocument Presentation Template (.otp) represents presentation template files created by applications in OASIS OpenDocument standard format.
        Learn more about this file format `here <https://wiki.fileformat.com/presentation/otp>`.'''
        raise NotImplementedError()

    @property
    def XLS(self) -> groupdocs.viewer.FileType:
        '''Excel Spreadsheet (.xls) represents Excel Binary File Format. Such files can be created by Microsoft Excel as well as other similar spreadsheet programs such as OpenOffice Calc or Apple Numbers.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/xls>`.'''
        raise NotImplementedError()

    @property
    def EXCEL_2003XML(self) -> groupdocs.viewer.FileType:
        '''Excel 2003 XML (SpreadsheetML) represents Excel Binary File Format. Such files can be created by Microsoft Excel as well as other similar spreadsheet programs such as OpenOffice Calc or Apple Numbers.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/xls>`.'''
        raise NotImplementedError()

    @property
    def NUMBERS(self) -> groupdocs.viewer.FileType:
        '''Apple numbers represents Excel like Binary File Format. Such files can be created by Apple numbers application.
        Learn more about this file format `here <https://fileinfo.com/extension/numbers>`.'''
        raise NotImplementedError()

    @property
    def XLSX(self) -> groupdocs.viewer.FileType:
        '''Microsoft Excel Open XML Spreadsheet (.xlsx) is a well-known format for Microsoft Excel documents that was introduced by Microsoft with the release of Microsoft Office 2007.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/xlsx>`.'''
        raise NotImplementedError()

    @property
    def XLSM(self) -> groupdocs.viewer.FileType:
        '''Excel Open XML Macro-Enabled Spreadsheet (.xlsm) is a type of Spreasheet files that support macros.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/xlsm>`.'''
        raise NotImplementedError()

    @property
    def XLSB(self) -> groupdocs.viewer.FileType:
        '''Excel Binary Spreadsheet (.xlsb) specifies the Excel Binary File Format, which is a collection of records and structures that specify Excel workbook content.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/xlsb>`.'''
        raise NotImplementedError()

    @property
    def CSV(self) -> groupdocs.viewer.FileType:
        '''Comma Separated Values File (.csv) represents plain text files that contain records of data with comma separated values.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/csv>`.'''
        raise NotImplementedError()

    @property
    def TSV(self) -> groupdocs.viewer.FileType:
        '''Tab Separated Values File (.tsv) represents data separated with tabs in plain text format.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/tsv>`.'''
        raise NotImplementedError()

    @property
    def ODS(self) -> groupdocs.viewer.FileType:
        '''OpenDocument Spreadsheet (.ods) stands for OpenDocument Spreadsheet Document format that are editable by user. Data is stored inside ODF file into rows and columns.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/ods>`.'''
        raise NotImplementedError()

    @property
    def FODS(self) -> groupdocs.viewer.FileType:
        '''OpenDocument Flat XML Spreadsheet (.fods)'''
        raise NotImplementedError()

    @property
    def OTS(self) -> groupdocs.viewer.FileType:
        '''OpenDocument Spreadsheet Template (.ots)'''
        raise NotImplementedError()

    @property
    def XLAM(self) -> groupdocs.viewer.FileType:
        '''Microsoft Excel Add-in (.xlam)'''
        raise NotImplementedError()

    @property
    def XLTM(self) -> groupdocs.viewer.FileType:
        '''Microsoft Excel Macro-Enabled Template (.xltm) represents files that are generated by Microsoft Excel as Macro-enabled template files. XLTM files are similar to XLTX in structure other than that the later doesn\'t support creating template files with macros.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/xltm>`.'''
        raise NotImplementedError()

    @property
    def XLT(self) -> groupdocs.viewer.FileType:
        '''Microsoft Excel Template (.xlt) are template files created with Microsoft Excel which is a spreadsheet application which comes as part of Microsoft Office suite.  Microsoft Office 97-2003 supported creating new XLT files as well as opening these.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/xlt>`.'''
        raise NotImplementedError()

    @property
    def XLTX(self) -> groupdocs.viewer.FileType:
        '''Excel Open XML Spreadsheet Template	(.xltx) represents Microsoft Excel Template that are based on the Office OpenXML file format specifications. It is used to create a standard template file that can be utilized to generate XLSX files that exhibit the same settings as specified in the XLTX file.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/xltx>`.'''
        raise NotImplementedError()

    @property
    def SXC(self) -> groupdocs.viewer.FileType:
        '''StarOffice Calc Spreadsheet (.sxc)'''
        raise NotImplementedError()

    @property
    def MPP(self) -> groupdocs.viewer.FileType:
        '''Microsoft Project File (.mpp) is Microsoft Project data file that stores information related to project management in an integrated manner.
        Learn more about this file format `here <https://wiki.fileformat.com/project-management/mpp>`.'''
        raise NotImplementedError()

    @property
    def MPT(self) -> groupdocs.viewer.FileType:
        '''Microsoft Project Template (.mpt) contains basic information and structure along with document settings for creating .MPP files.
        Learn more about this file format `here <https://wiki.fileformat.com/project-management/mpt>`.'''
        raise NotImplementedError()

    @property
    def MPX(self) -> groupdocs.viewer.FileType:
        '''Microsoft Project Exchange file (.mpx) is an ASCII file format for transferring of project information between Microsoft Project (MSP) and other applications that support the MPX file format such as Primavera Project Planner, Sciforma and Timerline Precision Estimating.
        Learn more about this file format `here <https://wiki.fileformat.com/project-management/mpx>`.'''
        raise NotImplementedError()

    @property
    def AS(self) -> groupdocs.viewer.FileType:
        '''ActionScript File (.as)'''
        raise NotImplementedError()

    @property
    def AS3(self) -> groupdocs.viewer.FileType:
        '''ActionScript File (.as)'''
        raise NotImplementedError()

    @property
    def ASM(self) -> groupdocs.viewer.FileType:
        '''Assembly Language Source Code File (.asm)'''
        raise NotImplementedError()

    @property
    def BAT(self) -> groupdocs.viewer.FileType:
        '''DOS Batch File (.bat)'''
        raise NotImplementedError()

    @property
    def C(self) -> groupdocs.viewer.FileType:
        '''C/C++ Source Code File (.c)'''
        raise NotImplementedError()

    @property
    def CC(self) -> groupdocs.viewer.FileType:
        '''C++ Source Code File (.cc)'''
        raise NotImplementedError()

    @property
    def CMAKE(self) -> groupdocs.viewer.FileType:
        '''CMake File (.cmake)'''
        raise NotImplementedError()

    @property
    def CPP(self) -> groupdocs.viewer.FileType:
        '''C++ Source Code File (.cpp)'''
        raise NotImplementedError()

    @property
    def CS(self) -> groupdocs.viewer.FileType:
        '''C# Source Code File (.cs) is a source code file for C# programming language. Introduced by Microsoft for use with the .NET Framework.
        Learn more about this file format `here <https://wiki.fileformat.com/programming/cs>`.'''
        raise NotImplementedError()

    @property
    def VB(self) -> groupdocs.viewer.FileType:
        '''Visual Basic Project Item File (.vb) is a source code file created in Visual Basic language that was created by Microsoft for development of .NET applications.
        Learn more about this file format `here <https://wiki.fileformat.com/programming/vb>`.'''
        raise NotImplementedError()

    @property
    def CSS(self) -> groupdocs.viewer.FileType:
        '''Cascading Style Sheet (.css)'''
        raise NotImplementedError()

    @property
    def CXX(self) -> groupdocs.viewer.FileType:
        '''C++ Source Code File (.cxx)'''
        raise NotImplementedError()

    @property
    def DIFF(self) -> groupdocs.viewer.FileType:
        '''Patch File (.diff)'''
        raise NotImplementedError()

    @property
    def ERB(self) -> groupdocs.viewer.FileType:
        '''Ruby ERB Script (.erb)'''
        raise NotImplementedError()

    @property
    def GROOVY(self) -> groupdocs.viewer.FileType:
        '''Groovy Source Code File (.groovy)'''
        raise NotImplementedError()

    @property
    def H(self) -> groupdocs.viewer.FileType:
        '''C/C++/Objective-C Header File (.h)'''
        raise NotImplementedError()

    @property
    def HAML(self) -> groupdocs.viewer.FileType:
        '''Haml Source Code File (.haml)'''
        raise NotImplementedError()

    @property
    def HH(self) -> groupdocs.viewer.FileType:
        '''C++ Header File (.hh)'''
        raise NotImplementedError()

    @property
    def JAVA(self) -> groupdocs.viewer.FileType:
        '''Java Source Code File (.java)'''
        raise NotImplementedError()

    @property
    def JS(self) -> groupdocs.viewer.FileType:
        '''JavaScript File (.js)'''
        raise NotImplementedError()

    @property
    def JSON(self) -> groupdocs.viewer.FileType:
        '''JavaScript Object Notation File (.json)'''
        raise NotImplementedError()

    @property
    def LESS(self) -> groupdocs.viewer.FileType:
        '''LESS Style Sheet (.less)'''
        raise NotImplementedError()

    @property
    def LOG(self) -> groupdocs.viewer.FileType:
        '''Log File (.log)'''
        raise NotImplementedError()

    @property
    def M(self) -> groupdocs.viewer.FileType:
        '''Objective-C Implementation File (.m)'''
        raise NotImplementedError()

    @property
    def MAKE(self) -> groupdocs.viewer.FileType:
        '''Xcode Makefile Script (.make)'''
        raise NotImplementedError()

    @property
    def MD(self) -> groupdocs.viewer.FileType:
        '''Markdown Documentation File (.md)'''
        raise NotImplementedError()

    @property
    def ML(self) -> groupdocs.viewer.FileType:
        '''ML Source Code File (.ml)'''
        raise NotImplementedError()

    @property
    def MM(self) -> groupdocs.viewer.FileType:
        '''Objective-C++ Source File (.mm)'''
        raise NotImplementedError()

    @property
    def PHP(self) -> groupdocs.viewer.FileType:
        '''PHP Source Code File (.php)'''
        raise NotImplementedError()

    @property
    def PL(self) -> groupdocs.viewer.FileType:
        '''Perl Script (.pl)'''
        raise NotImplementedError()

    @property
    def PROPERTIES(self) -> groupdocs.viewer.FileType:
        '''Java Properties File (.properties)'''
        raise NotImplementedError()

    @property
    def PY(self) -> groupdocs.viewer.FileType:
        '''Python Script (.py)'''
        raise NotImplementedError()

    @property
    def RB(self) -> groupdocs.viewer.FileType:
        '''Ruby Source Code (.rb)'''
        raise NotImplementedError()

    @property
    def RST(self) -> groupdocs.viewer.FileType:
        '''reStructuredText File (.rst)'''
        raise NotImplementedError()

    @property
    def SASS(self) -> groupdocs.viewer.FileType:
        '''Syntactically Awesome StyleSheets File (.sass)'''
        raise NotImplementedError()

    @property
    def SCALA(self) -> groupdocs.viewer.FileType:
        '''Scala Source Code File (.scala)'''
        raise NotImplementedError()

    @property
    def SCM(self) -> groupdocs.viewer.FileType:
        '''Scheme Source Code File (.scm)'''
        raise NotImplementedError()

    @property
    def SCRIPT(self) -> groupdocs.viewer.FileType:
        '''Generic Script File (.script)'''
        raise NotImplementedError()

    @property
    def SH(self) -> groupdocs.viewer.FileType:
        '''Bash Shell Script (.sh)'''
        raise NotImplementedError()

    @property
    def SML(self) -> groupdocs.viewer.FileType:
        '''Standard ML Source Code File (.sml)'''
        raise NotImplementedError()

    @property
    def SQL(self) -> groupdocs.viewer.FileType:
        '''Structured Query Language Data File (.sql)'''
        raise NotImplementedError()

    @property
    def VIM(self) -> groupdocs.viewer.FileType:
        '''Vim Settings File (.vim)'''
        raise NotImplementedError()

    @property
    def YAML(self) -> groupdocs.viewer.FileType:
        '''YAML Document (.yaml)'''
        raise NotImplementedError()

    @property
    def DOC(self) -> groupdocs.viewer.FileType:
        '''Microsoft Word Document (.doc) represents documents generated by Microsoft Word or other word processing documents in binary file format.
        Learn more about this file format `here <https://wiki.fileformat.com/word-processing/doc>`.'''
        raise NotImplementedError()

    @property
    def DOCX(self) -> groupdocs.viewer.FileType:
        '''Microsoft Word Open XML Document (.docx) is a well-known format for Microsoft Word documents. Introduced from 2007 with the release of Microsoft Office 2007, the structure of this new Document format was changed from plain binary to a combination of XML and binary files.
        Learn more about this file format `here <https://wiki.fileformat.com/word-processing/docx>`.'''
        raise NotImplementedError()

    @property
    def CHM(self) -> groupdocs.viewer.FileType:
        '''Microsoft Compiled HTML Help File (.chm) is a well-known format for HELP (documentation to some application) documents.
        Learn more about this file format `here <https://docs.fileformat.com/web/chm/>`.'''
        raise NotImplementedError()

    @property
    def DOCM(self) -> groupdocs.viewer.FileType:
        '''Word Open XML Macro-Enabled Document (.docm) is a Microsoft Word 2007 or higher generated documents with the ability to run macros.
        Learn more about this file format `here <https://wiki.fileformat.com/word-processing/docm>`.'''
        raise NotImplementedError()

    @property
    def DOT(self) -> groupdocs.viewer.FileType:
        '''Word Document Template (.dot) are template files created by Microsoft Word to have pre-formatted settings for generation of further DOC or DOCX files.
        Learn more about this file format `here <https://wiki.fileformat.com/word-processing/dot>`.'''
        raise NotImplementedError()

    @property
    def DOTX(self) -> groupdocs.viewer.FileType:
        '''Word Open XML Document Template (.dotx) are template files created by Microsoft Word to have pre-formatted settings for generation of further DOCX files.
        Learn more about this file format `here <https://wiki.fileformat.com/word-processing/dotx>`.'''
        raise NotImplementedError()

    @property
    def DOTM(self) -> groupdocs.viewer.FileType:
        '''Word Open XML Macro-Enabled Document Template (.dotm) represents template file created with Microsoft Word 2007 or higher.
        Learn more about this file format `here <https://wiki.fileformat.com/word-processing/dotm>`.'''
        raise NotImplementedError()

    @property
    def RTF(self) -> groupdocs.viewer.FileType:
        '''Rich Text Format File (.rtf) represents a method of encoding formatted text and graphics for use within applications.
        Learn more about this file format `here <https://wiki.fileformat.com/word-processing/rtf>`.'''
        raise NotImplementedError()

    @property
    def TXT(self) -> groupdocs.viewer.FileType:
        '''Plain Text File (.txt) represents a text document that contains plain text in the form of lines.
        Learn more about this file format `here <https://wiki.fileformat.com/word-processing/txt>`.'''
        raise NotImplementedError()

    @property
    def ODT(self) -> groupdocs.viewer.FileType:
        '''OpenDocument Text Document (.odt) are type of documents created with word processing applications that are based on OpenDocument Text File format.
        Learn more about this file format `here <https://wiki.fileformat.com/word-processing/odt>`.'''
        raise NotImplementedError()

    @property
    def OTT(self) -> groupdocs.viewer.FileType:
        '''OpenDocument Document Template (.ott) represents template documents generated by applications in compliance with the OASIS\' OpenDocument standard format.
        Learn more about this file format `here <https://wiki.fileformat.com/word-processing/ott>`.'''
        raise NotImplementedError()

    @property
    def VCF(self) -> groupdocs.viewer.FileType:
        '''vCard File (.vcf) is a digital file format for storing contact information. The format is widely used for data interchange among popular information exchange applications.
        Learn more about this file format `here <https://wiki.fileformat.com/email/vcf>`.'''
        raise NotImplementedError()

    @property
    def AI(self) -> groupdocs.viewer.FileType:
        '''Adobe Illustrator (.ai) is a file format for Adobe Illustrator drawings.
        Learn more about this file format `here <https://fileinfo.com/extension/ai#adobe_illustrator_file>`.'''
        raise NotImplementedError()

    @property
    def PSM1(self) -> groupdocs.viewer.FileType:
        '''PowerShell script module (.psm1) a file format for PowerShell module scripts.
        Learn more about this file format `here <https://fileinfo.com/extension/psm1>`.'''
        raise NotImplementedError()

    @property
    def PS1(self) -> groupdocs.viewer.FileType:
        '''PowerShell script file (.ps1) a file format for Windows PowerShell Cmdlet files.
        Learn more about this file format `here <https://fileinfo.com/extension/ps1>`.'''
        raise NotImplementedError()

    @property
    def PSD1(self) -> groupdocs.viewer.FileType:
        '''PowerShell script module manifest (.psd1) a file format for PowerShell module manifest scripts.
        Learn more about this file format `here <https://fileinfo.com/extension/psd1>`.'''
        raise NotImplementedError()


class IAuxDisposable:
    '''Expands the standard :py:class:`System.IDisposable` interface, allows to obtain a current state of an object and subscribe to disposing event'''
    
    @property
    def is_disposed(self) -> bool:
        '''Determines whether a resource is already disposed (``true``) or not (``false``)'''
        raise NotImplementedError()
    

class License:
    '''Provides methods to license the component. Learn more about licensing `here <https://purchase.groupdocs.com/faqs/licensing>`.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @overload
    def set_license(self, license_stream : io._IOBase) -> None:
        '''Licenses the component.
        
        :param license_stream: The license stream.'''
        raise NotImplementedError()
    
    @overload
    def set_license(self, license_path : str) -> None:
        '''Licenses the component.
        
        :param license_path: The license file path.'''
        raise NotImplementedError()
    

class Metered:
    '''Provides methods for applying `Metered <https://purchase.groupdocs.com/faqs/licensing/metered>` license.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def set_metered_key(self, public_key : str, private_key : str) -> None:
        '''Activates product with Metered keys.
        
        :param public_key: The public key.
        :param private_key: The private key.'''
        raise NotImplementedError()
    
    @staticmethod
    def get_consumption_quantity() -> System.Decimal:
        '''Retrieves amount of MBs processed.'''
        raise NotImplementedError()
    
    @staticmethod
    def get_consumption_credit() -> System.Decimal:
        '''Retrieves count of credits consumed.'''
        raise NotImplementedError()
    

class Viewer:
    '''Represents main class that controls document rendering process.'''
    
    @overload
    def __init__(self, stream : io._IOBase) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.Viewer` class.
        
        :param stream: The file stream.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, stream : io._IOBase, leave_open : bool) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.Viewer` class.
        
        :param stream: The file stream.
        :param leave_open: to leave the stream open after the Viewer object is disposed; otherwise, .'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, stream : io._IOBase, load_options : groupdocs.viewer.options.LoadOptions) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.Viewer` class.
        
        :param stream: The file stream.
        :param load_options: The document load options.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, stream : io._IOBase, load_options : groupdocs.viewer.options.LoadOptions, leave_open : bool) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.Viewer` class.
        
        :param stream: The file stream.
        :param load_options: The document load options.
        :param leave_open: to leave the stream open after the Viewer object is disposed; otherwise, .'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, stream : io._IOBase, settings : groupdocs.viewer.ViewerSettings) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.Viewer` class.
        
        :param stream: The file stream.
        :param settings: The Viewer settings.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, stream : io._IOBase, settings : groupdocs.viewer.ViewerSettings, leave_open : bool) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.Viewer` class.
        
        :param stream: The file stream.
        :param settings: The Viewer settings.
        :param leave_open: to leave the stream open after the Viewer object is disposed; otherwise, .'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, stream : io._IOBase, load_options : groupdocs.viewer.options.LoadOptions, settings : groupdocs.viewer.ViewerSettings) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.Viewer` class.
        
        :param stream: The file stream.
        :param load_options: The document load options.
        :param settings: The Viewer settings.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, stream : io._IOBase, load_options : groupdocs.viewer.options.LoadOptions, settings : groupdocs.viewer.ViewerSettings, leave_open : bool) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.Viewer` class.
        
        :param stream: The file stream.
        :param load_options: The document load options.
        :param settings: The Viewer settings.
        :param leave_open: to leave the stream open after the Viewer object is disposed; otherwise, .'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_path : str) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.Viewer` class.
        
        :param file_path: The path to the file to render.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_path : str, settings : groupdocs.viewer.ViewerSettings) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.Viewer` class.
        
        :param file_path: The path to the file to render.
        :param settings: The Viewer settings.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_path : str, load_options : groupdocs.viewer.options.LoadOptions) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.Viewer` class.
        
        :param file_path: The path to the file to render.
        :param load_options: The options that used to open the file.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_path : str, load_options : groupdocs.viewer.options.LoadOptions, settings : groupdocs.viewer.ViewerSettings) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.Viewer` class.
        
        :param file_path: The path to the file to render.
        :param load_options: The options that used to open the file.
        :param settings: The Viewer settings.'''
        raise NotImplementedError()
    
    @overload
    def view(self, options : groupdocs.viewer.options.ViewOptions) -> None:
        '''Creates view of all document pages.
        
        :param options: The view options.'''
        raise NotImplementedError()
    
    @overload
    def view(self, options : groupdocs.viewer.options.ViewOptions, page_numbers : List[int]) -> None:
        '''Creates view of specific document pages.
        
        :param options: The view options.
        :param page_numbers: The page numbers to view.'''
        raise NotImplementedError()
    
    def get_view_info(self, options : groupdocs.viewer.options.ViewInfoOptions) -> groupdocs.viewer.results.ViewInfo:
        '''Returns information about view and document specific information.
        
        :param options: The view info options.
        :returns: Information about view and document specific information.'''
        raise NotImplementedError()
    
    def get_attachments(self) -> System.Collections.Generic.IList`1[[GroupDocs.Viewer.Results.Attachment]]:
        '''Returns attachments contained by the document.
        
        :returns: Attachments contained by the document.'''
        raise NotImplementedError()
    
    def save_attachment(self, attachment : groupdocs.viewer.results.Attachment, destination : io._IOBase) -> None:
        '''Saves attachment file to ``destination`` stream.
        
        :param attachment: The attachment.
        :param destination: The writable stream.'''
        raise NotImplementedError()
    
    def get_file_info(self) -> groupdocs.viewer.results.FileInfo:
        '''Returns information about file such as file-type and flag that indicates if file is encrypted.
        
        :returns: The file information.'''
        raise NotImplementedError()
    

class ViewerSettings:
    '''Defines settings for customizing :py:class:`groupdocs.viewer.Viewer` behaviour.'''
    
    def __init__(self, logger : groupdocs.viewer.logging.ILogger) -> None:
        '''Initializes new instance of :py:class:`groupdocs.viewer.ViewerSettings` class.
        
        :param logger: The logger.'''
        raise NotImplementedError()
    
    @property
    def logger(self) -> groupdocs.viewer.logging.ILogger:
        '''The logger implementation used for logging (Errors, Warnings, Traces).'''
        raise NotImplementedError()
    

