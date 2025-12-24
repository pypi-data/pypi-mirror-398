from typing import List, Optional, Dict, Iterable, Any, overload
import io
import collections.abc
from collections.abc import Sequence
from datetime import datetime
from aspose.pyreflection import Type
import aspose.pycore
import aspose.pydrawing
from uuid import UUID
import groupdocs.conversion
import groupdocs.conversion.caching
import groupdocs.conversion.contracts
import groupdocs.conversion.exceptions
import groupdocs.conversion.filetypes
import groupdocs.conversion.logging
import groupdocs.conversion.options
import groupdocs.conversion.options.convert
import groupdocs.conversion.options.load

class CadFileType(FileType):
    '''Defines CAD documents (Computer Aided Design) that are used for a 3D graphics file formats and may contain 2D or 3D designs.
    Includes the following types:
    :py:attr:`groupdocs.conversion.filetypes.CadFileType.CF2`:py:attr:`groupdocs.conversion.filetypes.CadFileType.DGN`,
    :py:attr:`groupdocs.conversion.filetypes.CadFileType.DWF`,
    :py:attr:`groupdocs.conversion.filetypes.CadFileType.DWFX`:py:attr:`groupdocs.conversion.filetypes.CadFileType.DWG`,
    :py:attr:`groupdocs.conversion.filetypes.CadFileType.DWT`,
    :py:attr:`groupdocs.conversion.filetypes.CadFileType.DXF`,
    :py:attr:`groupdocs.conversion.filetypes.CadFileType.IFC`,
    :py:attr:`groupdocs.conversion.filetypes.CadFileType.IGS`,
    :py:attr:`groupdocs.conversion.filetypes.CadFileType.PLT`,
    :py:attr:`groupdocs.conversion.filetypes.CadFileType.STL`.
    Learn more about CAD formats `here <https://wiki.fileformat.com/cad>`.'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.Enumeration) -> bool:
        '''Implements :py:func:`groupdocs.conversion.contracts.Enumeration.equals`
        
        :param other: The object with which to compare'''
        raise NotImplementedError()
    
    def compare_to(self, obj : Any) -> int:
        '''Compares current object to other.
        
        :param obj: The other object
        :returns: zero if equal'''
        raise NotImplementedError()
    
    @staticmethod
    def from_filename(file_name : str) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for specified fileName
        
        :param file_name: The file name
        :returns: The file type of specified file name'''
        raise NotImplementedError()
    
    @staticmethod
    def from_extension(file_extension : str) -> groupdocs.conversion.filetypes.FileType:
        '''Gets FileType for provided fileExtension
        
        :param file_extension: File extension
        :returns: File type'''
        raise NotImplementedError()
    
    @staticmethod
    def from_stream(stream : io._IOBase) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for provided document stream
        
        :param stream: Stream which will be probed
        :returns: The file type of provided stream'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> str:
        '''The file format'''
        raise NotImplementedError()
    
    @property
    def extension(self) -> str:
        '''The file extension'''
        raise NotImplementedError()
    
    @property
    def family(self) -> str:
        '''The file family'''
        raise NotImplementedError()
    
    @property
    def description(self) -> str:
        '''File type description'''
        raise NotImplementedError()
    
    @property
    def UNKNOWN(self) -> groupdocs.conversion.filetypes.FileType:
        '''Unknown file type'''
        raise NotImplementedError()

    @property
    def DXF(self) -> groupdocs.conversion.filetypes.CadFileType:
        '''DXF, Drawing Interchange Format, or Drawing Exchange Format, is a tagged data representation of AutoCAD drawing file.
        Learn more about this file format `here <https://wiki.fileformat.com/cad/dxf>`.'''
        raise NotImplementedError()

    @property
    def DWG(self) -> groupdocs.conversion.filetypes.CadFileType:
        '''Files with DWG extension represent proprietary binary files used for containing 2D and 3D design data. Like DXF, which are ASCII files, DWG represent the binary file format for CAD (Computer Aided Design) drawings.
        Learn more about this file format `here <https://wiki.fileformat.com/cad/dwg>`.'''
        raise NotImplementedError()

    @property
    def DGN(self) -> groupdocs.conversion.filetypes.CadFileType:
        '''DGN, Design, files are drawings created by and supported by CAD applications such as MicroStation and Intergraph Interactive Graphics Design System.
        Learn more about this file format `here <https://wiki.fileformat.com/cad/dgn>`.'''
        raise NotImplementedError()

    @property
    def DWF(self) -> groupdocs.conversion.filetypes.CadFileType:
        '''Design Web Format (DWF) represents 2D/3D drawing in compressed format for viewing, reviewing or printing design files. It contains graphics and text as part of design data and reduce the size of the file due to its compressed format.
        Learn more about this file format `here <https://wiki.fileformat.com/cad/dwf>`.'''
        raise NotImplementedError()

    @property
    def STL(self) -> groupdocs.conversion.filetypes.CadFileType:
        '''STL, abbreviation for stereolithrography, is an interchangeable file format that represents 3-dimensional surface geometry. The file format finds its usage in several fields such as rapid prototyping, 3D printing and computer-aided manufacturing.
        Learn more about this file format `here <https://wiki.fileformat.com/cad/stl>`.'''
        raise NotImplementedError()

    @property
    def IFC(self) -> groupdocs.conversion.filetypes.CadFileType:
        '''Files with IFC extension refer to  Industry Foundation Classes (IFC) file format that establishes international standards to import and export building objects and their properties. This file format provides interoperability between different software applications.
        Learn more about this file format `here <https://wiki.fileformat.com/cad/ifc>`.'''
        raise NotImplementedError()

    @property
    def PLT(self) -> groupdocs.conversion.filetypes.CadFileType:
        '''The PLT file format is a vector-based plotter file introduced by Autodesk, Inc. and contains information for a certain CAD file. Plotting details require accuracy and precision in production, and usage of PLT file guarantee this as all images are printed using lines instead of dots.
        Learn more about this file format `here <https://wiki.fileformat.com/cad/plt>`.'''
        raise NotImplementedError()

    @property
    def IGS(self) -> groupdocs.conversion.filetypes.CadFileType:
        '''Igs document format'''
        raise NotImplementedError()

    @property
    def DWT(self) -> groupdocs.conversion.filetypes.CadFileType:
        '''A DWT file is an AutoCAD drawing template file that is used as starter for creating drawings that can be saved as DWG files.
        Learn more about this file format `here <https://wiki.fileformat.com/cad/dwt>`.'''
        raise NotImplementedError()

    @property
    def DWFX(self) -> groupdocs.conversion.filetypes.CadFileType:
        '''DWFX file is a 2D or 3D drawing created with Autodesk CAD software. It is saved in the DWFx format, which is similar to a . DWF file, but is formatted using Microsoft\'s XML Paper Specification (XPS).'''
        raise NotImplementedError()

    @property
    def CF2(self) -> groupdocs.conversion.filetypes.CadFileType:
        '''Common File Format File. CAD file that contains 3D package designs or other model data; can be processed and cut by a CAD/CAM machine, such as a die cutting device.'''
        raise NotImplementedError()


class CompressionFileType(FileType):
    '''Defines compression formats. Includes the following file types:
    :py:attr:`groupdocs.conversion.filetypes.CompressionFileType.ZIP`.
    :py:attr:`groupdocs.conversion.filetypes.CompressionFileType.RAR`.
    :py:attr:`groupdocs.conversion.filetypes.CompressionFileType.SEVEN_Z`.
    :py:attr:`groupdocs.conversion.filetypes.CompressionFileType.TAR`.
    :py:attr:`groupdocs.conversion.filetypes.CompressionFileType.GZ`.
    :py:attr:`groupdocs.conversion.filetypes.CompressionFileType.GZIP`.
    :py:attr:`groupdocs.conversion.filetypes.CompressionFileType.BZ2`.
    :py:attr:`groupdocs.conversion.filetypes.CompressionFileType.LZ`.
    :py:attr:`groupdocs.conversion.filetypes.CompressionFileType.Z`.
    :py:attr:`groupdocs.conversion.filetypes.CompressionFileType.XZ`.
    :py:attr:`groupdocs.conversion.filetypes.CompressionFileType.XZ`.
    :py:attr:`groupdocs.conversion.filetypes.CompressionFileType.CPIO`.
    :py:attr:`groupdocs.conversion.filetypes.CompressionFileType.CAB`.
    :py:attr:`groupdocs.conversion.filetypes.CompressionFileType.LZMA`.
    :py:attr:`groupdocs.conversion.filetypes.CompressionFileType.ZST`.
    :py:attr:`groupdocs.conversion.filetypes.CompressionFileType.UUE`.
    Learn more about compression formats `here <https://docs.fileformat.com/compression/>`.'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.Enumeration) -> bool:
        '''Implements :py:func:`groupdocs.conversion.contracts.Enumeration.equals`
        
        :param other: The object with which to compare'''
        raise NotImplementedError()
    
    def compare_to(self, obj : Any) -> int:
        '''Compares current object to other.
        
        :param obj: The other object
        :returns: zero if equal'''
        raise NotImplementedError()
    
    @staticmethod
    def from_filename(file_name : str) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for specified fileName
        
        :param file_name: The file name
        :returns: The file type of specified file name'''
        raise NotImplementedError()
    
    @staticmethod
    def from_extension(file_extension : str) -> groupdocs.conversion.filetypes.FileType:
        '''Gets FileType for provided fileExtension
        
        :param file_extension: File extension
        :returns: File type'''
        raise NotImplementedError()
    
    @staticmethod
    def from_stream(stream : io._IOBase) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for provided document stream
        
        :param stream: Stream which will be probed
        :returns: The file type of provided stream'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> str:
        '''The file format'''
        raise NotImplementedError()
    
    @property
    def extension(self) -> str:
        '''The file extension'''
        raise NotImplementedError()
    
    @property
    def family(self) -> str:
        '''The file family'''
        raise NotImplementedError()
    
    @property
    def description(self) -> str:
        '''File type description'''
        raise NotImplementedError()
    
    @property
    def UNKNOWN(self) -> groupdocs.conversion.filetypes.FileType:
        '''Unknown file type'''
        raise NotImplementedError()

    @property
    def ZIP(self) -> groupdocs.conversion.filetypes.CompressionFileType:
        '''A file with .zip extension is an archive that can hold one or more files or directories. The archive can have compression applied to the included files in order to reduce the ZIP file size.
        Learn more about this file format `here <https://docs.fileformat.com/compression/zip/>`.'''
        raise NotImplementedError()

    @property
    def RAR(self) -> groupdocs.conversion.filetypes.CompressionFileType:
        '''Files with .rar extension are archive files that are created for storing information in compressed or normal form. RAR, which stands for Roshal ARchive file format.
        Learn more about this file format `here <https://docs.fileformat.com/compression/rar/>`.'''
        raise NotImplementedError()

    @property
    def SEVEN_Z(self) -> groupdocs.conversion.filetypes.CompressionFileType:
        '''7z is an archiving format for compressing files and folders with a high compression ratio. It is based on Open Source architecture which makes it possible to use any compression and encryption algorithms.
        Learn more about this file format `here <https://docs.fileformat.com/compression/7z/>`.'''
        raise NotImplementedError()

    @property
    def TAR(self) -> groupdocs.conversion.filetypes.CompressionFileType:
        '''Files with .tar extension are archives created with Unix-based utility for collecting one or more files. Multiple files are stored in an uncompressed format with the support of adding files as well as folders to the archive.
        Learn more about this file format `here <https://docs.fileformat.com/compression/tar/>`.'''
        raise NotImplementedError()

    @property
    def GZ(self) -> groupdocs.conversion.filetypes.CompressionFileType:
        '''A GZ file is a compressed archive that is created using the standard gzip (GNU zip) compression algorithm. It may contain multiple compressed files, directories and file stubs.
        Learn more about this file format `here <https://docs.fileformat.com/compression/gz/>`.'''
        raise NotImplementedError()

    @property
    def GZIP(self) -> groupdocs.conversion.filetypes.CompressionFileType:
        '''A Gzip file is a compressed archive that is created using the standard gzip (GNU zip) compression algorithm. It may contain multiple compressed files, directories and file stubs.
        Learn more about this file format `here <https://docs.fileformat.com/compression/gz/>`.'''
        raise NotImplementedError()

    @property
    def BZ2(self) -> groupdocs.conversion.filetypes.CompressionFileType:
        '''BZ2 are compressed files generated using the BZIP2 open source compression method, mostly on UNIX or Linux system. It is used for compression of a single file and is not meant for archiving of multiple files.
        Learn more about this file format `here <https://docs.fileformat.com/compression/bz2/>`.'''
        raise NotImplementedError()

    @property
    def LZ(self) -> groupdocs.conversion.filetypes.CompressionFileType:
        '''A file with .lz extension is a compressed archive file created with Lzip, which is a free command-line tool for compression. It supports concatenation to compress support files. LZ files have media type application/lzip and support higher compression rations than BZ2.
        Learn more about this file format `here <https://docs.fileformat.com/compression/bz2/>`.'''
        raise NotImplementedError()

    @property
    def Z(self) -> groupdocs.conversion.filetypes.CompressionFileType:
        '''A Z file is a category of files belonging to the UNIX Compressed data files. Compressed Unix files are the most popular and widely used extension type of the Z file.
        Learn more about this file format `here <https://docs.fileformat.com/compression/z/>`.'''
        raise NotImplementedError()

    @property
    def XZ(self) -> groupdocs.conversion.filetypes.CompressionFileType:
        '''XZ is a compressed file format that utilizes the LZMA2 compression algorithm. It was designed as a replacement for the popular gzip and bzip2 formats, and offers a number of advantages over these older standards.
        Learn more about this file format `here <https://docs.fileformat.com/compression/xz/>`.'''
        raise NotImplementedError()

    @property
    def CPIO(self) -> groupdocs.conversion.filetypes.CompressionFileType:
        '''Cpio is a general file archiver utility and its associated file format. It is primarily installed on Unix-like computer operating systems.'''
        raise NotImplementedError()

    @property
    def CAB(self) -> groupdocs.conversion.filetypes.CompressionFileType:
        '''A file with a .cab extension belongs to a windows cabinet file that belongs to the category of system files. It is a file that is saved in the archive file format in the versions of Microsoft Windows that support compressed data algorithms, such as the LZX, Quantum, and ZIP.
        Learn more about this file format `here <https://docs.fileformat.com/system/cab/>`.'''
        raise NotImplementedError()

    @property
    def LZMA(self) -> groupdocs.conversion.filetypes.CompressionFileType:
        '''A file with .lzma extension is a compressed archive file created using the LZMA (Lempel-Ziv-Markov chain Algorithm) compression method. These are mainly found/used on Unix operating system and are similar to other compression algorithms such as ZIP for minimising file size.
        Learn more about this file format `here <https://docs.fileformat.com/compression/lzma/>`.'''
        raise NotImplementedError()

    @property
    def ZST(self) -> groupdocs.conversion.filetypes.CompressionFileType:
        '''A ZST file is a compressed file that is generated with the Zstandard (zstd) compression algorithm. It is a compressed file that is created with lossless compression by the algorithm.
        Learn more about this file format `here <https://docs.fileformat.com/compression/zst/>`.'''
        raise NotImplementedError()

    @property
    def ISO(self) -> groupdocs.conversion.filetypes.CompressionFileType:
        '''A file with .iso extension is an uncompressed archive disk image file that represents the contents of entire data on an optical disc such as CD or DVD. Based on the ISO-9660 standard, the ISO image file format contains the disc data along with the filesystem information that is stored in it.
        Learn more about this file format `here <https://docs.fileformat.com/compression/iso/>`.'''
        raise NotImplementedError()

    @property
    def UUE(self) -> groupdocs.conversion.filetypes.CompressionFileType:
        '''A uuencoded archive is a file or collection of files that have been encoded using the Unix-to-Unix encoding scheme (uuencode). This encoding method converts binary data into a text format, which makes it easier to send files over channels that only support text, such as email.'''
        raise NotImplementedError()


class DatabaseFileType(FileType):
    '''Defines database documents. Includes the following file types:
    :py:attr:`groupdocs.conversion.filetypes.DatabaseFileType.NSF`:py:attr:`groupdocs.conversion.filetypes.DatabaseFileType.LOG`:py:attr:`groupdocs.conversion.filetypes.DatabaseFileType.SQL`'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.Enumeration) -> bool:
        '''Implements :py:func:`groupdocs.conversion.contracts.Enumeration.equals`
        
        :param other: The object with which to compare'''
        raise NotImplementedError()
    
    def compare_to(self, obj : Any) -> int:
        '''Compares current object to other.
        
        :param obj: The other object
        :returns: zero if equal'''
        raise NotImplementedError()
    
    @staticmethod
    def from_filename(file_name : str) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for specified fileName
        
        :param file_name: The file name
        :returns: The file type of specified file name'''
        raise NotImplementedError()
    
    @staticmethod
    def from_extension(file_extension : str) -> groupdocs.conversion.filetypes.FileType:
        '''Gets FileType for provided fileExtension
        
        :param file_extension: File extension
        :returns: File type'''
        raise NotImplementedError()
    
    @staticmethod
    def from_stream(stream : io._IOBase) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for provided document stream
        
        :param stream: Stream which will be probed
        :returns: The file type of provided stream'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> str:
        '''The file format'''
        raise NotImplementedError()
    
    @property
    def extension(self) -> str:
        '''The file extension'''
        raise NotImplementedError()
    
    @property
    def family(self) -> str:
        '''The file family'''
        raise NotImplementedError()
    
    @property
    def description(self) -> str:
        '''File type description'''
        raise NotImplementedError()
    
    @property
    def UNKNOWN(self) -> groupdocs.conversion.filetypes.FileType:
        '''Unknown file type'''
        raise NotImplementedError()

    @property
    def NSF(self) -> groupdocs.conversion.filetypes.DatabaseFileType:
        '''A file with .nsf (Notes Storage Facility) extension is a database file format used by the IBM Notes software, which was previously known as Lotus Notes. It defines the schema to store different kind of objects such like emails, appointments, documents, forms and views.
        Learn more about this file format `here <https://docs.fileformat.com/database/nsf>`.'''
        raise NotImplementedError()

    @property
    def LOG(self) -> groupdocs.conversion.filetypes.DatabaseFileType:
        '''A file with .log extension contains the list of plain text with timestamp. Usually, certain activity detail is logged by the softwares or operating systems to help the developers or users to track what was happening at a certain time period.
        Learn more about this file format `here <https://docs.fileformat.com/database/log>`.'''
        raise NotImplementedError()

    @property
    def SQL(self) -> groupdocs.conversion.filetypes.DatabaseFileType:
        '''A file with .sql extension is a Structured Query Language (SQL) file that contains code to work with relational databases. It is used to write SQL statements for CRUD (Create, Read, Update, and Delete) operations on databases.
        Learn more about this file format `here <https://docs.fileformat.com/database/sql>`.'''
        raise NotImplementedError()


class DiagramFileType(FileType):
    '''Defines Diagram documents. Includes the following types:
    :py:attr:`groupdocs.conversion.filetypes.DiagramFileType.VDW`,
    :py:attr:`groupdocs.conversion.filetypes.DiagramFileType.VDX`,
    :py:attr:`groupdocs.conversion.filetypes.DiagramFileType.VSD`,
    :py:attr:`groupdocs.conversion.filetypes.DiagramFileType.VSDM`,
    :py:attr:`groupdocs.conversion.filetypes.DiagramFileType.VSDX`,
    :py:attr:`groupdocs.conversion.filetypes.DiagramFileType.VSS`,
    :py:attr:`groupdocs.conversion.filetypes.DiagramFileType.VSSM`,
    :py:attr:`groupdocs.conversion.filetypes.DiagramFileType.VSSX`,
    :py:attr:`groupdocs.conversion.filetypes.DiagramFileType.VST`,
    :py:attr:`groupdocs.conversion.filetypes.DiagramFileType.VSTM`,
    :py:attr:`groupdocs.conversion.filetypes.DiagramFileType.VSTX`,
    :py:attr:`groupdocs.conversion.filetypes.DiagramFileType.VSX`,
    :py:attr:`groupdocs.conversion.filetypes.DiagramFileType.VTX`.'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.Enumeration) -> bool:
        '''Implements :py:func:`groupdocs.conversion.contracts.Enumeration.equals`
        
        :param other: The object with which to compare'''
        raise NotImplementedError()
    
    def compare_to(self, obj : Any) -> int:
        '''Compares current object to other.
        
        :param obj: The other object
        :returns: zero if equal'''
        raise NotImplementedError()
    
    @staticmethod
    def from_filename(file_name : str) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for specified fileName
        
        :param file_name: The file name
        :returns: The file type of specified file name'''
        raise NotImplementedError()
    
    @staticmethod
    def from_extension(file_extension : str) -> groupdocs.conversion.filetypes.FileType:
        '''Gets FileType for provided fileExtension
        
        :param file_extension: File extension
        :returns: File type'''
        raise NotImplementedError()
    
    @staticmethod
    def from_stream(stream : io._IOBase) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for provided document stream
        
        :param stream: Stream which will be probed
        :returns: The file type of provided stream'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> str:
        '''The file format'''
        raise NotImplementedError()
    
    @property
    def extension(self) -> str:
        '''The file extension'''
        raise NotImplementedError()
    
    @property
    def family(self) -> str:
        '''The file family'''
        raise NotImplementedError()
    
    @property
    def description(self) -> str:
        '''File type description'''
        raise NotImplementedError()
    
    @property
    def UNKNOWN(self) -> groupdocs.conversion.filetypes.FileType:
        '''Unknown file type'''
        raise NotImplementedError()

    @property
    def VSD(self) -> groupdocs.conversion.filetypes.DiagramFileType:
        '''VSD files are drawings created with Microsoft Visio application to represent variety of graphical objects and the interconnection between these.
        Learn more about this file format `here <https://wiki.fileformat.com/image/vsd>`.'''
        raise NotImplementedError()

    @property
    def VSDX(self) -> groupdocs.conversion.filetypes.DiagramFileType:
        '''Files with .VSDX extension represent Microsoft Visio file format introduced from Microsoft Office 2013 onwards. It was developed to replace the binary file format, .VSD, which is supported by earlier versions of Microsoft Visio.
        Learn more about this file format `here <https://wiki.fileformat.com/image/vsdx>`.'''
        raise NotImplementedError()

    @property
    def VSS(self) -> groupdocs.conversion.filetypes.DiagramFileType:
        '''VSS are stencil files created with Microsoft Visio 2007 and earlier. Stencil files provide drawing objects that can be included in a .VSD Visio drawing.
        Learn more about this file format `here <https://wiki.fileformat.com/image/vss>`.'''
        raise NotImplementedError()

    @property
    def VST(self) -> groupdocs.conversion.filetypes.DiagramFileType:
        '''Files with VST extension are vector image files created with Microsoft Visio and act as template for creating further files. These template files are in binary file format and contain the default layout and settings that are utilized for creation of new Visio drawings.
        Learn more about this file format `here <https://wiki.fileformat.com/image/vst>`.'''
        raise NotImplementedError()

    @property
    def VSX(self) -> groupdocs.conversion.filetypes.DiagramFileType:
        '''Files with .VSX extension refer to stencils that consist of drawings and shapes that are used for creating diagrams in Microsoft Visio. VSX files are saved in XML file format and was supported till Visio 2013.
        Learn more about this file format `here <https://wiki.fileformat.com/image/vsx>`.'''
        raise NotImplementedError()

    @property
    def VTX(self) -> groupdocs.conversion.filetypes.DiagramFileType:
        '''A file with VTX extension is a Microsoft Visio drawing template that is saved to disc in XML file format. The template is aimed to provide a file with basic settings that can be used to create multiple Visio files of the same settings.
        Learn more about this file format `here <https://wiki.fileformat.com/image/vtx>`.'''
        raise NotImplementedError()

    @property
    def VDW(self) -> groupdocs.conversion.filetypes.DiagramFileType:
        '''VDW is the Visio Graphics Service file format that specifies the streams and storages required for rendering a Web drawing.
        Learn more about this file format `here <https://wiki.fileformat.com/web/vdw>`.'''
        raise NotImplementedError()

    @property
    def VDX(self) -> groupdocs.conversion.filetypes.DiagramFileType:
        '''Any drawing or chart created in Microsoft Visio, but saved in XML format have .VDX extension. A Visio drawing XML file is created in Visio software, which is developed by Microsoft.
        Learn more about this file format `here <https://wiki.fileformat.com/image/vdx>`.'''
        raise NotImplementedError()

    @property
    def VSSX(self) -> groupdocs.conversion.filetypes.DiagramFileType:
        '''Files with .VSSX extension are drawing stencils created with Microsoft Visio 2013 and above. The VSSX file format can be opened with Visio 2013 and above. Visio files are known for representation of a variety of drawing elements such as collection of shapes, connectors, flowcharts, network layout, UML diagrams,
        Learn more about this file format `here <https://wiki.fileformat.com/image/vssx>`.'''
        raise NotImplementedError()

    @property
    def VSTX(self) -> groupdocs.conversion.filetypes.DiagramFileType:
        '''Files with VSTX extensions are drawing template files created with Microsoft Visio 2013 and above. These VSTX files provide starting point for creating Visio drawings, saved as .VSDX files, with default layout and settings.
        Learn more about this file format `here <https://wiki.fileformat.com/image/vstx>`.'''
        raise NotImplementedError()

    @property
    def VSDM(self) -> groupdocs.conversion.filetypes.DiagramFileType:
        '''Files with VSDM extension are drawing files created with Microsoft Visio application that supports macros. VSDM files are OPC/XML drawings that are similar to VSDX, but also provide the capability to run macros when the file is opened.
        Learn more about this file format `here <https://wiki.fileformat.com/image/vsdm>`.'''
        raise NotImplementedError()

    @property
    def VSSM(self) -> groupdocs.conversion.filetypes.DiagramFileType:
        '''Files with .VSSM extension are Microsoft Visio Stencil files that support provide support for macros. A VSSM file when opened allows to run the macros to achieve desired formatting and placement of shapes in a diagram.
        Learn more about this file format `here <https://wiki.fileformat.com/image/vssm>`.'''
        raise NotImplementedError()

    @property
    def VSTM(self) -> groupdocs.conversion.filetypes.DiagramFileType:
        '''Files with VSTM extension are template files created with Microsoft Visio that support macros. Unlike VSDX files, files created from VSTM templates can run macros that are developed in Visual Basic for Applications (VBA)  code.
        Learn more about this file format `here <https://wiki.fileformat.com/image/vstm>`.'''
        raise NotImplementedError()


class EBookFileType(FileType):
    '''Defines EBook documents. Includes the following file types:
    :py:attr:`groupdocs.conversion.filetypes.EBookFileType.EPUB`:py:attr:`groupdocs.conversion.filetypes.EBookFileType.MOBI`:py:attr:`groupdocs.conversion.filetypes.EBookFileType.AZW3`'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.Enumeration) -> bool:
        '''Implements :py:func:`groupdocs.conversion.contracts.Enumeration.equals`
        
        :param other: The object with which to compare'''
        raise NotImplementedError()
    
    def compare_to(self, obj : Any) -> int:
        '''Compares current object to other.
        
        :param obj: The other object
        :returns: zero if equal'''
        raise NotImplementedError()
    
    @staticmethod
    def from_filename(file_name : str) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for specified fileName
        
        :param file_name: The file name
        :returns: The file type of specified file name'''
        raise NotImplementedError()
    
    @staticmethod
    def from_extension(file_extension : str) -> groupdocs.conversion.filetypes.FileType:
        '''Gets FileType for provided fileExtension
        
        :param file_extension: File extension
        :returns: File type'''
        raise NotImplementedError()
    
    @staticmethod
    def from_stream(stream : io._IOBase) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for provided document stream
        
        :param stream: Stream which will be probed
        :returns: The file type of provided stream'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> str:
        '''The file format'''
        raise NotImplementedError()
    
    @property
    def extension(self) -> str:
        '''The file extension'''
        raise NotImplementedError()
    
    @property
    def family(self) -> str:
        '''The file family'''
        raise NotImplementedError()
    
    @property
    def description(self) -> str:
        '''File type description'''
        raise NotImplementedError()
    
    @property
    def UNKNOWN(self) -> groupdocs.conversion.filetypes.FileType:
        '''Unknown file type'''
        raise NotImplementedError()

    @property
    def EPUB(self) -> groupdocs.conversion.filetypes.EBookFileType:
        '''EPUB extension are an e-book file format that provide a standard digital publication format for publishers and consumers. The format has been so common by now that it is supported by many e-readers and software applications.
        Learn more about this file format `here <https://wiki.fileformat.com/ebook/epub>`.'''
        raise NotImplementedError()

    @property
    def MOBI(self) -> groupdocs.conversion.filetypes.EBookFileType:
        '''The MOBI file format is one of the most widely used ebook file format. The format is an enhancement to the old OEB (Open Ebook Format) format and was used as proprietary format for Mobipocket Reader.
        Learn more about this file format `here <https://wiki.fileformat.com/ebook/mobi>`.'''
        raise NotImplementedError()

    @property
    def AZW3(self) -> groupdocs.conversion.filetypes.EBookFileType:
        '''AZW3, also known as Kindle Format 8 (KF8), is the modified version of the AZW ebook digital file format developed for Amazon Kindle devices. The format is an enhancement to older AZW files and is used on Kindle Fire devices only with backward compatibility for the ancestor file format i.e. MOBI and AZW.
        Learn more about this file format `here <https://docs.fileformat.com/ebook/azw3/>`.'''
        raise NotImplementedError()


class EmailFileType(FileType):
    '''Defines Email file formats that are used by email applications to store their various data including email messages, attachments, folders, address books etc.
    Includes the following file types:
    :py:attr:`groupdocs.conversion.filetypes.EmailFileType.EML`,
    :py:attr:`groupdocs.conversion.filetypes.EmailFileType.EMLX`,
    :py:attr:`groupdocs.conversion.filetypes.EmailFileType.MSG`,
    :py:attr:`groupdocs.conversion.filetypes.EmailFileType.VCF`.
    :py:attr:`groupdocs.conversion.filetypes.EmailFileType.MBOX`.
    :py:attr:`groupdocs.conversion.filetypes.EmailFileType.PST`.
    :py:attr:`groupdocs.conversion.filetypes.EmailFileType.OST`.
    :py:attr:`groupdocs.conversion.filetypes.EmailFileType.OLM`.
    Learn more about Email formats `here <https://wiki.fileformat.com/email>`.'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.Enumeration) -> bool:
        '''Implements :py:func:`groupdocs.conversion.contracts.Enumeration.equals`
        
        :param other: The object with which to compare'''
        raise NotImplementedError()
    
    def compare_to(self, obj : Any) -> int:
        '''Compares current object to other.
        
        :param obj: The other object
        :returns: zero if equal'''
        raise NotImplementedError()
    
    @staticmethod
    def from_filename(file_name : str) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for specified fileName
        
        :param file_name: The file name
        :returns: The file type of specified file name'''
        raise NotImplementedError()
    
    @staticmethod
    def from_extension(file_extension : str) -> groupdocs.conversion.filetypes.FileType:
        '''Gets FileType for provided fileExtension
        
        :param file_extension: File extension
        :returns: File type'''
        raise NotImplementedError()
    
    @staticmethod
    def from_stream(stream : io._IOBase) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for provided document stream
        
        :param stream: Stream which will be probed
        :returns: The file type of provided stream'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> str:
        '''The file format'''
        raise NotImplementedError()
    
    @property
    def extension(self) -> str:
        '''The file extension'''
        raise NotImplementedError()
    
    @property
    def family(self) -> str:
        '''The file family'''
        raise NotImplementedError()
    
    @property
    def description(self) -> str:
        '''File type description'''
        raise NotImplementedError()
    
    @property
    def UNKNOWN(self) -> groupdocs.conversion.filetypes.FileType:
        '''Unknown file type'''
        raise NotImplementedError()

    @property
    def MSG(self) -> groupdocs.conversion.filetypes.EmailFileType:
        '''MSG is a file format used by Microsoft Outlook and Exchange to store email messages, contact, appointment, or other tasks.
        Learn more about this file format `here <https://wiki.fileformat.com/email/msg>`.'''
        raise NotImplementedError()

    @property
    def EML(self) -> groupdocs.conversion.filetypes.EmailFileType:
        '''EML file format represents email messages saved using Outlook and other relevant applications. Almost all emailing clients support this file format for its compliance with RFC-822 Internet Message Format Standard.
        Learn more about this file format `here <https://wiki.fileformat.com/email/eml>`.'''
        raise NotImplementedError()

    @property
    def EMLX(self) -> groupdocs.conversion.filetypes.EmailFileType:
        '''The EMLX file format is implemented and developed by Apple. The Apple Mail application uses the EMLX file format for exporting the emails.
        Learn more about this file format `here <https://wiki.fileformat.com/email/emlx>`.'''
        raise NotImplementedError()

    @property
    def VCF(self) -> groupdocs.conversion.filetypes.EmailFileType:
        '''VCF (Virtual Card Format) or vCard is a digital file format for storing contact information. The format is widely used for data interchange among popular information exchange applications.
        Learn more about this file format `here <https://wiki.fileformat.com/email/vcf>`.'''
        raise NotImplementedError()

    @property
    def MBOX(self) -> groupdocs.conversion.filetypes.EmailFileType:
        '''MBox file format is a generic term that represents a container for collection of electronic mail messages. The messages are stored inside the container along with their attachments.
        Learn more about this file format `here <https://docs.fileformat.com/email/mbox/>`.'''
        raise NotImplementedError()

    @property
    def PST(self) -> groupdocs.conversion.filetypes.EmailFileType:
        '''Files with .PST extension represent Outlook Personal Storage Files (also called Personal Storage Table) that store variety of user information.
        Learn more about this file format `here <https://wiki.fileformat.com/email/pst>`.'''
        raise NotImplementedError()

    @property
    def OST(self) -> groupdocs.conversion.filetypes.EmailFileType:
        '''OST or Offline Storage Files represent user\'s mailbox data in offline mode on local machine upon registration with Exchange Server using Microsoft Outlook.
        Learn more about this file format `here <https://wiki.fileformat.com/email/ost>`.'''
        raise NotImplementedError()

    @property
    def OLM(self) -> groupdocs.conversion.filetypes.EmailFileType:
        '''A file with .olm extension is a Microsoft Outlook file for Mac Operating System. An OLM file stores email messages, journals, calendar data, and other types of application data. These are similar to PST files used by Outlook on Windows Operating System. However, OLM files created by Outlook for Mac can’t be opened in Outlook for Windows.
        Learn more about this file format `here <https://wiki.fileformat.com/email/olm>`.'''
        raise NotImplementedError()


class FileType(groupdocs.conversion.contracts.Enumeration):
    '''File type base class'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.Enumeration) -> bool:
        '''Implements :py:func:`groupdocs.conversion.contracts.Enumeration.equals`
        
        :param other: The object with which to compare'''
        raise NotImplementedError()
    
    def compare_to(self, obj : Any) -> int:
        '''Compares current object to other.
        
        :param obj: The other object
        :returns: zero if equal'''
        raise NotImplementedError()
    
    @staticmethod
    def from_filename(file_name : str) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for specified fileName
        
        :param file_name: The file name
        :returns: The file type of specified file name'''
        raise NotImplementedError()
    
    @staticmethod
    def from_extension(file_extension : str) -> groupdocs.conversion.filetypes.FileType:
        '''Gets FileType for provided fileExtension
        
        :param file_extension: File extension
        :returns: File type'''
        raise NotImplementedError()
    
    @staticmethod
    def from_stream(stream : io._IOBase) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for provided document stream
        
        :param stream: Stream which will be probed
        :returns: The file type of provided stream'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> str:
        '''The file format'''
        raise NotImplementedError()
    
    @property
    def extension(self) -> str:
        '''The file extension'''
        raise NotImplementedError()
    
    @property
    def family(self) -> str:
        '''The file family'''
        raise NotImplementedError()
    
    @property
    def description(self) -> str:
        '''File type description'''
        raise NotImplementedError()
    
    @property
    def UNKNOWN(self) -> groupdocs.conversion.filetypes.FileType:
        '''Unknown file type'''
        raise NotImplementedError()


class FinanceFileType(FileType):
    '''Defines Finance documents
    Includes the following types:
    :py:attr:`groupdocs.conversion.filetypes.FinanceFileType.XBRL`:py:attr:`groupdocs.conversion.filetypes.FinanceFileType.I_XBRL`:py:attr:`groupdocs.conversion.filetypes.FinanceFileType.OFX`
    Learn more about Finance formats `here <https://docs.fileformat.com/finance/>`.'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.Enumeration) -> bool:
        '''Implements :py:func:`groupdocs.conversion.contracts.Enumeration.equals`
        
        :param other: The object with which to compare'''
        raise NotImplementedError()
    
    def compare_to(self, obj : Any) -> int:
        '''Compares current object to other.
        
        :param obj: The other object
        :returns: zero if equal'''
        raise NotImplementedError()
    
    @staticmethod
    def from_filename(file_name : str) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for specified fileName
        
        :param file_name: The file name
        :returns: The file type of specified file name'''
        raise NotImplementedError()
    
    @staticmethod
    def from_extension(file_extension : str) -> groupdocs.conversion.filetypes.FileType:
        '''Gets FileType for provided fileExtension
        
        :param file_extension: File extension
        :returns: File type'''
        raise NotImplementedError()
    
    @staticmethod
    def from_stream(stream : io._IOBase) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for provided document stream
        
        :param stream: Stream which will be probed
        :returns: The file type of provided stream'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> str:
        '''The file format'''
        raise NotImplementedError()
    
    @property
    def extension(self) -> str:
        '''The file extension'''
        raise NotImplementedError()
    
    @property
    def family(self) -> str:
        '''The file family'''
        raise NotImplementedError()
    
    @property
    def description(self) -> str:
        '''File type description'''
        raise NotImplementedError()
    
    @property
    def UNKNOWN(self) -> groupdocs.conversion.filetypes.FileType:
        '''Unknown file type'''
        raise NotImplementedError()

    @property
    def XBRL(self) -> groupdocs.conversion.filetypes.FinanceFileType:
        '''XBRL is an open international standard for digital business reporting that is widely used globally. It is an XML based language that uses XBRL elements, known as tags, to describe each item of business data to formulate data for report sorting and analysis.
        Learn more about this file format `here <https://docs.fileformat.com/finance/xbrl/>`.'''
        raise NotImplementedError()

    @property
    def I_XBRL(self) -> groupdocs.conversion.filetypes.FinanceFileType:
        '''Inside the iXBRL, contents of XBRL are wrapped in xHTML file format that uses XML tags. Like XBRL, is the root element of iXBRL files. The XHTML format represents its contents as collection of different document types and modules. All the files in XHTML are based on XML file format and conform to the XML document standards.
        Learn more about this file format `here <https://docs.fileformat.com/finance/ixbrl/>`.'''
        raise NotImplementedError()

    @property
    def OFX(self) -> groupdocs.conversion.filetypes.FinanceFileType:
        '''Open Financial Exchange (OFX) is a data-stream format for exchanging financial information that evolved from Microsoft\'s Open Financial Connectivity (OFC) and Intuit\'s Open Exchange file formats.
        Learn more about this file format `here <https://en.wikipedia.org/wiki/Open_Financial_Exchange>`.'''
        raise NotImplementedError()


class FontFileType(FileType):
    '''Defines Font documents
    Includes the following types:
    :py:attr:`groupdocs.conversion.filetypes.FontFileType.TTF`:py:attr:`groupdocs.conversion.filetypes.FontFileType.EOT`:py:attr:`groupdocs.conversion.filetypes.FontFileType.OTF`:py:attr:`groupdocs.conversion.filetypes.FontFileType.CFF`:py:attr:`groupdocs.conversion.filetypes.FontFileType.TYPE1`:py:attr:`groupdocs.conversion.filetypes.FontFileType.WOFF`:py:attr:`groupdocs.conversion.filetypes.FontFileType.WOFF2`
    Learn more about Font formats `here <https://docs.fileformat.com/font/>`.'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.Enumeration) -> bool:
        '''Implements :py:func:`groupdocs.conversion.contracts.Enumeration.equals`
        
        :param other: The object with which to compare'''
        raise NotImplementedError()
    
    def compare_to(self, obj : Any) -> int:
        '''Compares current object to other.
        
        :param obj: The other object
        :returns: zero if equal'''
        raise NotImplementedError()
    
    @staticmethod
    def from_filename(file_name : str) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for specified fileName
        
        :param file_name: The file name
        :returns: The file type of specified file name'''
        raise NotImplementedError()
    
    @staticmethod
    def from_extension(file_extension : str) -> groupdocs.conversion.filetypes.FileType:
        '''Gets FileType for provided fileExtension
        
        :param file_extension: File extension
        :returns: File type'''
        raise NotImplementedError()
    
    @staticmethod
    def from_stream(stream : io._IOBase) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for provided document stream
        
        :param stream: Stream which will be probed
        :returns: The file type of provided stream'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> str:
        '''The file format'''
        raise NotImplementedError()
    
    @property
    def extension(self) -> str:
        '''The file extension'''
        raise NotImplementedError()
    
    @property
    def family(self) -> str:
        '''The file family'''
        raise NotImplementedError()
    
    @property
    def description(self) -> str:
        '''File type description'''
        raise NotImplementedError()
    
    @property
    def UNKNOWN(self) -> groupdocs.conversion.filetypes.FileType:
        '''Unknown file type'''
        raise NotImplementedError()

    @property
    def TTF(self) -> groupdocs.conversion.filetypes.FontFileType:
        '''A file with .ttf extension represents font files based on the TrueType specifications font technology. It was initially designed and launched by Apple Computer, Inc for Mac OS and was later adopted by Microsoft for Windows OS.
        Learn more about this file format `here <https://docs.fileformat.com/font/ttf/>`.'''
        raise NotImplementedError()

    @property
    def EOT(self) -> groupdocs.conversion.filetypes.FontFileType:
        '''A file with .eot extension is an OpenType font that is embedded in a document. These are mostly used in web files such as a Web page. It was created by Microsoft and is supported by Microsoft Products including PowerPoint presentation .pps file.
        Learn more about this file format `here <https://docs.fileformat.com/font/eot/>`.'''
        raise NotImplementedError()

    @property
    def OTF(self) -> groupdocs.conversion.filetypes.FontFileType:
        '''A file with .otf extension refers to OpenType font format. OTF font format is more scalable and extends the existing features of TTF formats for digital typography. Developed by Microsoft and Adobe, OTF combines the features of PostScript and TrueType font formats.
        Learn more about this file format `here <https://docs.fileformat.com/font/otf/>`.'''
        raise NotImplementedError()

    @property
    def CFF(self) -> groupdocs.conversion.filetypes.FontFileType:
        '''A file with .cff extension is a Compact Font Format and is also known as a PostScript Type 1, or CIDFont. CFF acts as a container to store multiple fonts together in a single unit known as a FontSet.
        Learn more about this file format `here <https://docs.fileformat.com/font/cff/>`.'''
        raise NotImplementedError()

    @property
    def TYPE1(self) -> groupdocs.conversion.filetypes.FontFileType:
        '''Type 1 fonts is a deprecated Adobe technology which was widely used in the desktop based publishing software and printers that could use PostScript. Although Type 1 fonts are not supported in many modern platforms, web browsers and mobile operating systems, but these are still supported in some of the operating systems.
        Learn more about this file format `here <https://docs.fileformat.com/font/type1/>`.'''
        raise NotImplementedError()

    @property
    def WOFF(self) -> groupdocs.conversion.filetypes.FontFileType:
        '''A file with .woff extension is a web font file based on the Web Open Font Format (WOFF). It has format-specific compressed container based on either TrueType (.TTF) or OpenType (.OTT) font types.
        Learn more about this file format `here <https://docs.fileformat.com/font/woff/>`.'''
        raise NotImplementedError()

    @property
    def WOFF2(self) -> groupdocs.conversion.filetypes.FontFileType:
        '''A file with .woff extension is a web font file based on the Web Open Font Format (WOFF). It has format-specific compressed container based on either TrueType (.TTF) or OpenType (.OTT) font types.
        Learn more about this file format `here <https://docs.fileformat.com/font/woff/>`.'''
        raise NotImplementedError()


class GisFileType(FileType):
    '''Defines GIS documents. Includes the following file types:
    :py:attr:`groupdocs.conversion.filetypes.GisFileType.SHP`.
    :py:attr:`groupdocs.conversion.filetypes.GisFileType.GEO_JSON`.
    :py:attr:`groupdocs.conversion.filetypes.GisFileType.GDB`.
    :py:attr:`groupdocs.conversion.filetypes.GisFileType.GML`.
    :py:attr:`groupdocs.conversion.filetypes.GisFileType.KML`.
    :py:attr:`groupdocs.conversion.filetypes.GisFileType.GPX`.
    :py:attr:`groupdocs.conversion.filetypes.GisFileType.TOPO_JSON`.
    :py:attr:`groupdocs.conversion.filetypes.GisFileType.OSM`.'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.Enumeration) -> bool:
        '''Implements :py:func:`groupdocs.conversion.contracts.Enumeration.equals`
        
        :param other: The object with which to compare'''
        raise NotImplementedError()
    
    def compare_to(self, obj : Any) -> int:
        '''Compares current object to other.
        
        :param obj: The other object
        :returns: zero if equal'''
        raise NotImplementedError()
    
    @staticmethod
    def from_filename(file_name : str) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for specified fileName
        
        :param file_name: The file name
        :returns: The file type of specified file name'''
        raise NotImplementedError()
    
    @staticmethod
    def from_extension(file_extension : str) -> groupdocs.conversion.filetypes.FileType:
        '''Gets FileType for provided fileExtension
        
        :param file_extension: File extension
        :returns: File type'''
        raise NotImplementedError()
    
    @staticmethod
    def from_stream(stream : io._IOBase) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for provided document stream
        
        :param stream: Stream which will be probed
        :returns: The file type of provided stream'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> str:
        '''The file format'''
        raise NotImplementedError()
    
    @property
    def extension(self) -> str:
        '''The file extension'''
        raise NotImplementedError()
    
    @property
    def family(self) -> str:
        '''The file family'''
        raise NotImplementedError()
    
    @property
    def description(self) -> str:
        '''File type description'''
        raise NotImplementedError()
    
    @property
    def UNKNOWN(self) -> groupdocs.conversion.filetypes.FileType:
        '''Unknown file type'''
        raise NotImplementedError()

    @property
    def SHP(self) -> groupdocs.conversion.filetypes.GisFileType:
        '''SHP is the file extension for one of the primary file types used for representation of ESRI Shapefile. It represents Geospatial information in the form of vector data to be used by Geographic Information Systems (GIS) applications.
        Learn more about this file format `here <https://docs.fileformat.com/gis/shp/>`.'''
        raise NotImplementedError()

    @property
    def GEO_JSON(self) -> groupdocs.conversion.filetypes.GisFileType:
        '''GeoJSON is a JSON based format designed to represent the geographical features with their non-spatial attributes. This format defines different JSON (JavaScript Object Notation) objects and their joining fashion. JSON format represents a collective information about the Geographical features, their spatial extents, and properties.
        Learn more about this file format `here <https://docs.fileformat.com/gis/geojson/>`.'''
        raise NotImplementedError()

    @property
    def GDB(self) -> groupdocs.conversion.filetypes.GisFileType:
        '''ESRI file Geodatabase (FileGDB) is a collection of files in a folder on disc that hold related geospatial data such as feature datasets, feature classes and associated tables. It requires certain other files to be kept alongside the .gdb file in the same directory for it to work.
        Learn more about this file format `here <https://docs.fileformat.com/database/gdb/>`.'''
        raise NotImplementedError()

    @property
    def GML(self) -> groupdocs.conversion.filetypes.GisFileType:
        '''GML stands for Geography Markup Language that is based on XML specifications developed by the Open Geospatial Consortium (OGC). The format is used to store geographic data features for interchange among different file formats. It serves as a modeling language for geographic systems as well as an open interchange format for geographic transactions on the internet.
        Learn more about this file format `here <https://docs.fileformat.com/gis/gml/>`.'''
        raise NotImplementedError()

    @property
    def KML(self) -> groupdocs.conversion.filetypes.GisFileType:
        '''KML (Keyhole Markup Language) contains geospatial information in XML notation. Files saved as KML can be opened in Geographic Information System (GIS) applications provided they support it. Many applications have started providing support for KML file format after it has been adopted as international standard. KML uses a tag-based structure with nested elements and attributes.
        Learn more about this file format `here <https://docs.fileformat.com/gis/kml/>`.'''
        raise NotImplementedError()

    @property
    def GPX(self) -> groupdocs.conversion.filetypes.GisFileType:
        '''Files with GPX extension represent GPS Exchange format for interchange of GPS data between applications and web services on the internet. It is a light-weight XML file format that contains GPS data i.e. waypoints, routes and tracks to be imported and red by multiple programs.
        Learn more about this file format `here <https://docs.fileformat.com/gis/gpx/>`.'''
        raise NotImplementedError()

    @property
    def TOPO_JSON(self) -> groupdocs.conversion.filetypes.GisFileType:
        '''TopoJSON is an extension of GeoJSON that encodes topology. Rather than representing geometries discretely, geometries in TopoJSON files are stitched together from shared line segments called arcs.'''
        raise NotImplementedError()

    @property
    def OSM(self) -> groupdocs.conversion.filetypes.GisFileType:
        '''The OSM file format is a structured data format used to store geographical data in the OpenStreetMap project. OSM files are typically in XML format and contain information such as the location of roads, buildings, points of interest, and other features on the map.
        Learn more about this file format `here <https://docs.fileformat.com/gis/osm/>`.'''
        raise NotImplementedError()


class ImageFileType(FileType):
    '''Defines image documents. Includes the following file types:
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.AI`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.BMP`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.CDR`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.CMX`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.DCM`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.DIB`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.DJ_VU`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.DNG`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.EMF`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.EMZ`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.GIF`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.HEIC`:py:attr:`groupdocs.conversion.filetypes.ImageFileType.ICO`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.J2C`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.J2K`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.JLS`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.JP2`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.JPC`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.JFIF`.
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.JPEG`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.JPF`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.JPG`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.JPM`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.JPX`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.ODG`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.PNG`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.PSD`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.SVGZ`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.TIF`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.TIFF`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.WEBP`,
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.WMF`.
    :py:attr:`groupdocs.conversion.filetypes.ImageFileType.WMZ`.
    Learn more about Image formats `here <https://wiki.fileformat.com/image>`.'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.Enumeration) -> bool:
        '''Implements :py:func:`groupdocs.conversion.contracts.Enumeration.equals`
        
        :param other: The object with which to compare'''
        raise NotImplementedError()
    
    def compare_to(self, obj : Any) -> int:
        '''Compares current object to other.
        
        :param obj: The other object
        :returns: zero if equal'''
        raise NotImplementedError()
    
    @staticmethod
    def from_filename(file_name : str) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for specified fileName
        
        :param file_name: The file name
        :returns: The file type of specified file name'''
        raise NotImplementedError()
    
    @staticmethod
    def from_extension(file_extension : str) -> groupdocs.conversion.filetypes.FileType:
        '''Gets FileType for provided fileExtension
        
        :param file_extension: File extension
        :returns: File type'''
        raise NotImplementedError()
    
    @staticmethod
    def from_stream(stream : io._IOBase) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for provided document stream
        
        :param stream: Stream which will be probed
        :returns: The file type of provided stream'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> str:
        '''The file format'''
        raise NotImplementedError()
    
    @property
    def extension(self) -> str:
        '''The file extension'''
        raise NotImplementedError()
    
    @property
    def family(self) -> str:
        '''The file family'''
        raise NotImplementedError()
    
    @property
    def description(self) -> str:
        '''File type description'''
        raise NotImplementedError()
    
    @property
    def UNKNOWN(self) -> groupdocs.conversion.filetypes.FileType:
        '''Unknown file type'''
        raise NotImplementedError()

    @property
    def is_raster(self) -> bool:
        '''Defines if the image is raster'''
        raise NotImplementedError()
    
    @property
    def TIFF(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''TIFF, Tagged Image File Format, represents raster images that are meant for usage on a variety of devices that comply with this file format standard. It is capable of describing bilevel, grayscale, palette-color and full-color image data in several color spaces.
        Learn more about this file format `here <https://wiki.fileformat.com/image/tiff>`.'''
        raise NotImplementedError()

    @property
    def TIF(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''TIF, Tagged Image File Format, represents raster images that are meant for usage on a variety of devices that comply with this file format standard. It is capable of describing bilevel, grayscale, palette-color and full-color image data in several color spaces.
        Learn more about this file format `here <https://wiki.fileformat.com/image/tiff>`.'''
        raise NotImplementedError()

    @property
    def JPG(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''A JPG is a type of image format that is saved using the method of lossy compression. The output image, as result of compression, is a trade-off between storage size and image quality.
        Learn more about this file format `here <https://wiki.fileformat.com/image/jpeg>`.'''
        raise NotImplementedError()

    @property
    def JPEG(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''A JPEG is a type of image format that is saved using the method of lossy compression. The output image, as result of compression, is a trade-off between storage size and image quality.
        Learn more about this file format `here <https://wiki.fileformat.com/image/jpeg>`.'''
        raise NotImplementedError()

    @property
    def PNG(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''PNG, Portable Network Graphics, refers to a type of raster image file format that use loseless compression. This file format was created as a replacement of Graphics Interchange Format (GIF) and has no copyright limitations.
        Learn more about this file format `here <https://wiki.fileformat.com/image/png>`.'''
        raise NotImplementedError()

    @property
    def GIF(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''A GIF or Graphical Interchange Format is a type of highly compressed image. For each image GIF typically allow up to 8 bits per pixel and up to 256 colours are allowed across the image.
        Learn more about this file format `here <https://wiki.fileformat.com/image/gif>`.'''
        raise NotImplementedError()

    @property
    def BMP(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''BMP represent Bitmap Image files that are used to store bitmap digital images. These images are independent of graphics adapter and are also called device independent bitmap (DIB) file format.
        Learn more about this file format `here <https://wiki.fileformat.com/image/bmp>`.'''
        raise NotImplementedError()

    @property
    def ICO(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''Files with ICO extension are image file types used as icon for representation of an application on Microsoft Windows.
        Learn more about this file format `here <https://wiki.fileformat.com/image/ico>`.'''
        raise NotImplementedError()

    @property
    def PSD(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''PSD, Photoshop Document, represents Adobe Photoshop\'s native file format used for graphics designing and development.
        Learn more about this file format `here <https://wiki.fileformat.com/image/psd>`.'''
        raise NotImplementedError()

    @property
    def WMF(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''Files with WMF extension represent Microsoft Windows Metafile (WMF) for storing vector as well as bitmap-format images data.
        Learn more about this file format `here <https://wiki.fileformat.com/image/wmf>`.'''
        raise NotImplementedError()

    @property
    def EMF(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''Enhanced metafile format (EMF) stores graphical images device-independently. Metafiles of EMF comprises of variable-length records in chronological order that can render the stored image after parsing on any output device.
        Learn more about this file format `here <https://wiki.fileformat.com/image/emf>`.'''
        raise NotImplementedError()

    @property
    def DCM(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''Files with .DCM extension represent digital image which stores medical information of patients such as MRIs, CT scans and ultrasound images.
        Learn more about this file format `here <https://wiki.fileformat.com/image/dcm>`.'''
        raise NotImplementedError()

    @property
    def DICOM(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''Files with .DICOM extension represent digital image which stores medical information of patients such as MRIs, CT scans and ultrasound images.
        Learn more about this file format `here <https://wiki.fileformat.com/image/dicom>`.'''
        raise NotImplementedError()

    @property
    def WEBP(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''WebP, introduced by Google, is a modern raster web image file format that is based on lossless and lossy compression. It provides same image quality while considerably reducing the image size.
        Learn more about this file format `here <https://wiki.fileformat.com/image/webp>`.'''
        raise NotImplementedError()

    @property
    def DNG(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''DNG is a digital camera image format used for the storage of raw files. It has been developed by Adobe in September 2004. It was basically developed for digital photography.
        Learn more about this file format `here <https://wiki.fileformat.com/image/dng>`.'''
        raise NotImplementedError()

    @property
    def JP2(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''JPEG 2000 (JP2) is an image coding system and state-of-the-art image compression standard.
        Learn more about this file format `here <https://wiki.fileformat.com/image/jp2>`.'''
        raise NotImplementedError()

    @property
    def ODG(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''The ODG file format is used by Apache OpenOffice\'s Draw application to store drawing elements as a vector image.
        Learn more about this file format `here <https://wiki.fileformat.com/image/odg>`.'''
        raise NotImplementedError()

    @property
    def J2C(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''J2c document format'''
        raise NotImplementedError()

    @property
    def J2K(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''J2K file is an image that is compressed using the wavelet compression instead of DCT compression.
        Learn more about this file format `here <https://wiki.fileformat.com/image/j2k>`.'''
        raise NotImplementedError()

    @property
    def JPX(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''Jpx document format'''
        raise NotImplementedError()

    @property
    def JPF(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''Jpf document format'''
        raise NotImplementedError()

    @property
    def JPM(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''Jpm document format'''
        raise NotImplementedError()

    @property
    def CDR(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''A CDR file is a vector drawing image file that is natively created with CorelDRAW for storing digital image encoded and compressed. Such a drawing file contains text, lines, shapes, images, colours and effects for vector representation of image contents.
        Learn more about this file format `here <https://wiki.fileformat.com/image/cdr>`.'''
        raise NotImplementedError()

    @property
    def CMX(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''Files with CMX extension are Corel Exchange image file format that is used as presentation by CorelSuite applications.
        Learn more about this file format `here <https://wiki.fileformat.com/image/cmx>`.'''
        raise NotImplementedError()

    @property
    def DIB(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''DIB (Device Independent Bitmap) file is a raster image file that is similar in structure to the standard Bitmap files (BMP) but has a different header.
        Learn more about this file format `here <https://wiki.fileformat.com/image/dib>`.'''
        raise NotImplementedError()

    @property
    def JPC(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''Jpc document format'''
        raise NotImplementedError()

    @property
    def JLS(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''Jls document format'''
        raise NotImplementedError()

    @property
    def DJ_VU(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''DjVu is a graphics file format intended for scanned documents and books especially those which contain the combination of text, drawings, images and photographs.
        Learn more about this file format `here <https://wiki.fileformat.com/image/djvu>`.'''
        raise NotImplementedError()

    @property
    def OTG(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''An OTG file is a drawing template that is created using the OpenDocument standard that follows the OASIS Office Applications 1.0 specification.
        Learn more about this file format `here <https://wiki.fileformat.com/image/otg>`.'''
        raise NotImplementedError()

    @property
    def AI(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''AI, Adobe Illustrator Artwork, represents single-page vector-based drawings in either the EPS or PDF formats.'''
        raise NotImplementedError()

    @property
    def EMZ(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''An EMZ file is actually a compressed version of a Microsoft EMF file. This allows for easier distribution of the file online. When an EMF file is compressed using the .GZIP compression algorithm, it is then given the .emz file extension.'''
        raise NotImplementedError()

    @property
    def WMZ(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''An WMZ file is actually a compressed version of a Microsoft WMF file. This allows for easier distribution of the file online. When an EWMFMF file is compressed using the .GZIP compression algorithm, it is then given the .wmz file extension.'''
        raise NotImplementedError()

    @property
    def SVGZ(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''An SVGZ file is actually a compressed version of a SVG file. This allows for easier distribution of the file online. When an SVG file is compressed using the .GZIP compression algorithm, it is then given the .svgz file extension.'''
        raise NotImplementedError()

    @property
    def TGA(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''A file with .tga extension is a raster graphic format and was created by Truevision Inc.
        Learn more about this file format `here <https://docs.fileformat.com/image/tga>`.'''
        raise NotImplementedError()

    @property
    def PSB(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''Adobe photoshop saves files in two formats. Files having 30,000 by 30,000 pixels in size are saved with PSD extension and files larger than PSD upto 300,000 by 300,000 pixels are saved with PSB extension known as “Photoshop Big”.
        Learn more about this file format `here <https://docs.fileformat.com/image/psb>`.'''
        raise NotImplementedError()

    @property
    def FODG(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''FODG is a uncompressed XML-format file used for storing OpenDocument text data. FODG extension is associated with open source office productivity suites Libre Office and OpenOffice.org.'''
        raise NotImplementedError()

    @property
    def JFIF(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''JFIF (JPEG File Interchange Format (JFIF)) is an image format file that uses the .jfif extension. JFIF builds over JIF (JPEG Interchange Format) by reducing complexity and solving its limitations.
        Learn more about this file format `here <https://docs.fileformat.com/image/jfif/>`.'''
        raise NotImplementedError()

    @property
    def HEIC(self) -> groupdocs.conversion.filetypes.ImageFileType:
        '''An HEIC file is a High-Efficiency Container Image file format that can store multiple images as a collection in a single file. The format was adopted by Apple as variant of the HEIF with the launch of iOS 11.
        Learn more about this file format `here <https://docs.fileformat.com/image/heic/>`.'''
        raise NotImplementedError()


class NoteFileType(FileType):
    '''Defines Note-taking formats. Includes the following file types:
    :py:attr:`groupdocs.conversion.filetypes.NoteFileType.ONE`.
    Learn more about Note-taking formats `here <https://wiki.fileformat.com/note-taking>`.'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.Enumeration) -> bool:
        '''Implements :py:func:`groupdocs.conversion.contracts.Enumeration.equals`
        
        :param other: The object with which to compare'''
        raise NotImplementedError()
    
    def compare_to(self, obj : Any) -> int:
        '''Compares current object to other.
        
        :param obj: The other object
        :returns: zero if equal'''
        raise NotImplementedError()
    
    @staticmethod
    def from_filename(file_name : str) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for specified fileName
        
        :param file_name: The file name
        :returns: The file type of specified file name'''
        raise NotImplementedError()
    
    @staticmethod
    def from_extension(file_extension : str) -> groupdocs.conversion.filetypes.FileType:
        '''Gets FileType for provided fileExtension
        
        :param file_extension: File extension
        :returns: File type'''
        raise NotImplementedError()
    
    @staticmethod
    def from_stream(stream : io._IOBase) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for provided document stream
        
        :param stream: Stream which will be probed
        :returns: The file type of provided stream'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> str:
        '''The file format'''
        raise NotImplementedError()
    
    @property
    def extension(self) -> str:
        '''The file extension'''
        raise NotImplementedError()
    
    @property
    def family(self) -> str:
        '''The file family'''
        raise NotImplementedError()
    
    @property
    def description(self) -> str:
        '''File type description'''
        raise NotImplementedError()
    
    @property
    def UNKNOWN(self) -> groupdocs.conversion.filetypes.FileType:
        '''Unknown file type'''
        raise NotImplementedError()

    @property
    def ONE(self) -> groupdocs.conversion.filetypes.NoteFileType:
        '''File represented by .ONE extension are created by Microsoft OneNote application. OneNote lets you gather information using the application as if you are using your draftpad for taking notes.
        Learn more about this file format `here <https://wiki.fileformat.com/note-taking/one>`.'''
        raise NotImplementedError()


class PageDescriptionLanguageFileType(FileType):
    '''Defines Page description documents. Includes the following file types:
    :py:attr:`groupdocs.conversion.filetypes.PageDescriptionLanguageFileType.SVG`:py:attr:`groupdocs.conversion.filetypes.PageDescriptionLanguageFileType.EPS`:py:attr:`groupdocs.conversion.filetypes.PageDescriptionLanguageFileType.CGM`:py:attr:`groupdocs.conversion.filetypes.PageDescriptionLanguageFileType.XPS`:py:attr:`groupdocs.conversion.filetypes.PageDescriptionLanguageFileType.TEX`:py:attr:`groupdocs.conversion.filetypes.PageDescriptionLanguageFileType.PS`:py:attr:`groupdocs.conversion.filetypes.PageDescriptionLanguageFileType.PCL`:py:attr:`groupdocs.conversion.filetypes.PageDescriptionLanguageFileType.OXPS`'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.Enumeration) -> bool:
        '''Implements :py:func:`groupdocs.conversion.contracts.Enumeration.equals`
        
        :param other: The object with which to compare'''
        raise NotImplementedError()
    
    def compare_to(self, obj : Any) -> int:
        '''Compares current object to other.
        
        :param obj: The other object
        :returns: zero if equal'''
        raise NotImplementedError()
    
    @staticmethod
    def from_filename(file_name : str) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for specified fileName
        
        :param file_name: The file name
        :returns: The file type of specified file name'''
        raise NotImplementedError()
    
    @staticmethod
    def from_extension(file_extension : str) -> groupdocs.conversion.filetypes.FileType:
        '''Gets FileType for provided fileExtension
        
        :param file_extension: File extension
        :returns: File type'''
        raise NotImplementedError()
    
    @staticmethod
    def from_stream(stream : io._IOBase) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for provided document stream
        
        :param stream: Stream which will be probed
        :returns: The file type of provided stream'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> str:
        '''The file format'''
        raise NotImplementedError()
    
    @property
    def extension(self) -> str:
        '''The file extension'''
        raise NotImplementedError()
    
    @property
    def family(self) -> str:
        '''The file family'''
        raise NotImplementedError()
    
    @property
    def description(self) -> str:
        '''File type description'''
        raise NotImplementedError()
    
    @property
    def UNKNOWN(self) -> groupdocs.conversion.filetypes.FileType:
        '''Unknown file type'''
        raise NotImplementedError()

    @property
    def SVG(self) -> groupdocs.conversion.filetypes.PageDescriptionLanguageFileType:
        '''An SVG file is a Scalar Vector Graphics file that uses XML based text format for describing the appearance of an image.
        Learn more about this file format `here <https://wiki.fileformat.com/page-description-language/svg>`.'''
        raise NotImplementedError()

    @property
    def EPS(self) -> groupdocs.conversion.filetypes.PageDescriptionLanguageFileType:
        '''Files with EPS extension essentially describe an Encapsulated PostScript language program that describes the appearance of a single page.
        Learn more about this file format `here <https://wiki.fileformat.com/page-description-language/eps>`.'''
        raise NotImplementedError()

    @property
    def CGM(self) -> groupdocs.conversion.filetypes.PageDescriptionLanguageFileType:
        '''Computer Graphics Metafile (CGM) is free, platform-independent, international standard metafile format for storing and exchanging of vector graphics (2D), raster graphics, and text. CGM uses object-oriented approach and many function provisions for image production.
        Learn more about this file format `here <https://wiki.fileformat.com/page-description-language/cgm>`.'''
        raise NotImplementedError()

    @property
    def XPS(self) -> groupdocs.conversion.filetypes.PageDescriptionLanguageFileType:
        '''An XPS file represents page layout files that are based on XML Paper Specifications created by Microsoft. This format was developed by Microsoft as a replacement of EMF file format and is similar to PDF file format, but uses XML in layout, appearance, and printing information of a document.
        Learn more about this file format `here <https://wiki.fileformat.com/page-description-language/xps>`.'''
        raise NotImplementedError()

    @property
    def TEX(self) -> groupdocs.conversion.filetypes.PageDescriptionLanguageFileType:
        '''TeX is a language that comprises of programming as well as mark-up features, used to typeset documents.
        Learn more about this file format `here <https://wiki.fileformat.com/page-description-language/tex>`.'''
        raise NotImplementedError()

    @property
    def PS(self) -> groupdocs.conversion.filetypes.PageDescriptionLanguageFileType:
        '''PostScript (PS) is a general-purpose page description language used in the business of desktop and electronic publishing. The main focus of PostScript (PS) is to facilitate the two-dimensional graphic design.
        Learn more about this file format `here <https://wiki.fileformat.com/page-description-language/ps>`.'''
        raise NotImplementedError()

    @property
    def PCL(self) -> groupdocs.conversion.filetypes.PageDescriptionLanguageFileType:
        '''PCL stands for Printer Command Language which is a Page Description Language introduced by Hewlett Packard (HP).
        Learn more about this file format `here <https://wiki.fileformat.com/page-description-language/pcl>`.'''
        raise NotImplementedError()

    @property
    def OXPS(self) -> groupdocs.conversion.filetypes.PageDescriptionLanguageFileType:
        '''The file format OXPS is known as Open XML Paper Specification. It’s a page description language and document format. Microsoft is the developer of this format. OXPS file format is very much familiar to these PDF files.
        Learn more about this file format `here <https://docs.fileformat.com/page-description-language/oxps>`.'''
        raise NotImplementedError()


class PdfFileType(FileType):
    '''Defines Pdf documents. Includes the following file types:
    :py:attr:`groupdocs.conversion.filetypes.PdfFileType.PDF`,'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.Enumeration) -> bool:
        '''Implements :py:func:`groupdocs.conversion.contracts.Enumeration.equals`
        
        :param other: The object with which to compare'''
        raise NotImplementedError()
    
    def compare_to(self, obj : Any) -> int:
        '''Compares current object to other.
        
        :param obj: The other object
        :returns: zero if equal'''
        raise NotImplementedError()
    
    @staticmethod
    def from_filename(file_name : str) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for specified fileName
        
        :param file_name: The file name
        :returns: The file type of specified file name'''
        raise NotImplementedError()
    
    @staticmethod
    def from_extension(file_extension : str) -> groupdocs.conversion.filetypes.FileType:
        '''Gets FileType for provided fileExtension
        
        :param file_extension: File extension
        :returns: File type'''
        raise NotImplementedError()
    
    @staticmethod
    def from_stream(stream : io._IOBase) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for provided document stream
        
        :param stream: Stream which will be probed
        :returns: The file type of provided stream'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> str:
        '''The file format'''
        raise NotImplementedError()
    
    @property
    def extension(self) -> str:
        '''The file extension'''
        raise NotImplementedError()
    
    @property
    def family(self) -> str:
        '''The file family'''
        raise NotImplementedError()
    
    @property
    def description(self) -> str:
        '''File type description'''
        raise NotImplementedError()
    
    @property
    def UNKNOWN(self) -> groupdocs.conversion.filetypes.FileType:
        '''Unknown file type'''
        raise NotImplementedError()

    @property
    def PDF(self) -> groupdocs.conversion.filetypes.PdfFileType:
        '''Portable Document Format (PDF) is a type of document created by Adobe back in 1990s. The purpose of this file format was to introduce a standard for representation of documents and other reference material in a format that is independent of application software, hardware as well as Operating System.
        Learn more about this file format `here <https://wiki.fileformat.com/view/pdf>`.'''
        raise NotImplementedError()


class PresentationFileType(FileType):
    '''Defines Presentation file formats that store collection of records to accommodate presentation data such as slides, shapes, text, animations, video, audio and embedded objects.
    Includes the following file types:
    :py:attr:`groupdocs.conversion.filetypes.PresentationFileType.ODP`,
    :py:attr:`groupdocs.conversion.filetypes.PresentationFileType.OTP`,
    :py:attr:`groupdocs.conversion.filetypes.PresentationFileType.POT`,
    :py:attr:`groupdocs.conversion.filetypes.PresentationFileType.POTM`,
    :py:attr:`groupdocs.conversion.filetypes.PresentationFileType.POTX`,
    :py:attr:`groupdocs.conversion.filetypes.PresentationFileType.PPS`,
    :py:attr:`groupdocs.conversion.filetypes.PresentationFileType.PPSM`,
    :py:attr:`groupdocs.conversion.filetypes.PresentationFileType.PPSX`,
    :py:attr:`groupdocs.conversion.filetypes.PresentationFileType.PPT`,
    :py:attr:`groupdocs.conversion.filetypes.PresentationFileType.PPTM`,
    :py:attr:`groupdocs.conversion.filetypes.PresentationFileType.PPTX`.
    Learn more about Presentation formats `here <https://wiki.fileformat.com/presentation>`.'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.Enumeration) -> bool:
        '''Implements :py:func:`groupdocs.conversion.contracts.Enumeration.equals`
        
        :param other: The object with which to compare'''
        raise NotImplementedError()
    
    def compare_to(self, obj : Any) -> int:
        '''Compares current object to other.
        
        :param obj: The other object
        :returns: zero if equal'''
        raise NotImplementedError()
    
    @staticmethod
    def from_filename(file_name : str) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for specified fileName
        
        :param file_name: The file name
        :returns: The file type of specified file name'''
        raise NotImplementedError()
    
    @staticmethod
    def from_extension(file_extension : str) -> groupdocs.conversion.filetypes.FileType:
        '''Gets FileType for provided fileExtension
        
        :param file_extension: File extension
        :returns: File type'''
        raise NotImplementedError()
    
    @staticmethod
    def from_stream(stream : io._IOBase) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for provided document stream
        
        :param stream: Stream which will be probed
        :returns: The file type of provided stream'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> str:
        '''The file format'''
        raise NotImplementedError()
    
    @property
    def extension(self) -> str:
        '''The file extension'''
        raise NotImplementedError()
    
    @property
    def family(self) -> str:
        '''The file family'''
        raise NotImplementedError()
    
    @property
    def description(self) -> str:
        '''File type description'''
        raise NotImplementedError()
    
    @property
    def UNKNOWN(self) -> groupdocs.conversion.filetypes.FileType:
        '''Unknown file type'''
        raise NotImplementedError()

    @property
    def PPT(self) -> groupdocs.conversion.filetypes.PresentationFileType:
        '''A file with PPT extension represents PowerPoint file that consists of a collection of slides for displaying as SlideShow. It specifies the Binary File Format used by Microsoft PowerPoint 97-2003.
        Learn more about this file format `here <https://wiki.fileformat.com/presentation/ppt>`.'''
        raise NotImplementedError()

    @property
    def PPS(self) -> groupdocs.conversion.filetypes.PresentationFileType:
        '''PPS, PowerPoint Slide Show, files are created using Microsoft PowerPoint for Slide Show purpose. PPS file reading and creation is supported by Microsoft PowerPoint 97-2003.
        Learn more about this file format `here <https://wiki.fileformat.com/presentation/pps>`.'''
        raise NotImplementedError()

    @property
    def PPTX(self) -> groupdocs.conversion.filetypes.PresentationFileType:
        '''Files with PPTX extension are presentation files created with popular Microsoft PowerPoint application. Unlike the previous version of presentation file format PPT which was binary, the PPTX format is based on the Microsoft PowerPoint open XML presentation file format.
        Learn more about this file format `here <https://wiki.fileformat.com/presentation/pptx>`.'''
        raise NotImplementedError()

    @property
    def PPSX(self) -> groupdocs.conversion.filetypes.PresentationFileType:
        '''PPSX, Power Point Slide Show, file are created using Microsoft PowerPoint 2007 and above for Slide Show purpose.
        Learn more about this file format `here <https://wiki.fileformat.com/presentation/ppsx>`.'''
        raise NotImplementedError()

    @property
    def ODP(self) -> groupdocs.conversion.filetypes.PresentationFileType:
        '''Files with ODP extension represent presentation file format used by OpenOffice.org in the OASISOpen standard.
        Learn more about this file format `here <https://wiki.fileformat.com/presentation/odp>`.'''
        raise NotImplementedError()

    @property
    def OTP(self) -> groupdocs.conversion.filetypes.PresentationFileType:
        '''Files with .OTP extension represent presentation template files created by applications in OASIS OpenDocument standard format.
        Learn more about this file format `here <https://wiki.fileformat.com/presentation/otp>`.'''
        raise NotImplementedError()

    @property
    def POTX(self) -> groupdocs.conversion.filetypes.PresentationFileType:
        '''Files with .POTX extension represent Microsoft PowerPoint template presentations that are created with Microsoft PowerPoint 2007 and above.
        Learn more about this file format `here <https://wiki.fileformat.com/presentation/potx>`.'''
        raise NotImplementedError()

    @property
    def POT(self) -> groupdocs.conversion.filetypes.PresentationFileType:
        '''Files with .POT extension represent Microsoft PowerPoint template files created by PowerPoint 97-2003 versions.
        Learn more about this file format `here <https://wiki.fileformat.com/presentation/pot>`.'''
        raise NotImplementedError()

    @property
    def POTM(self) -> groupdocs.conversion.filetypes.PresentationFileType:
        '''Files with POTM extension are Microsoft PowerPoint template files with support for Macros. POTM files are created with PowerPoint 2007 or above and contains default settings that can be used to create further presentation files.
        Learn more about this file format `here <https://wiki.fileformat.com/presentation/potm>`.'''
        raise NotImplementedError()

    @property
    def PPTM(self) -> groupdocs.conversion.filetypes.PresentationFileType:
        '''Files with PPTM extension are Macro-enabled Presentation files that are created with Microsoft PowerPoint 2007 or higher versions.
        Learn more about this file format `here <https://wiki.fileformat.com/presentation/pptm>`.'''
        raise NotImplementedError()

    @property
    def PPSM(self) -> groupdocs.conversion.filetypes.PresentationFileType:
        '''Files with PPSM extension represent Macro-enabled Slide Show file format created with Microsoft PowerPoint 2007 or higher.
        Learn more about this file format `here <https://wiki.fileformat.com/presentation/ppsm>`.'''
        raise NotImplementedError()

    @property
    def FODP(self) -> groupdocs.conversion.filetypes.PresentationFileType:
        '''Files with FODP extension represent OpenDocument Flat XML Presentation. Presentation file saved in the OpenDocument format, but saved using a flat XML format instead of the .ZIP container used by standard .ODP files'''
        raise NotImplementedError()


class ProjectManagementFileType(FileType):
    '''Defines Project file formats that are created by Project Management software such as Microsoft Project, Primavera P6 etc. A project file is a collection of tasks, resources, and their scheduling to get a measurable output in the form or a product or a service.
    Project management documents. Includes the following file types:
    :py:attr:`groupdocs.conversion.filetypes.ProjectManagementFileType.MPP`,
    :py:attr:`groupdocs.conversion.filetypes.ProjectManagementFileType.MPT`,
    :py:attr:`groupdocs.conversion.filetypes.ProjectManagementFileType.MPX`.
    Learn more about Project Management formats `here <https://wiki.fileformat.com/project-management>`.'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.Enumeration) -> bool:
        '''Implements :py:func:`groupdocs.conversion.contracts.Enumeration.equals`
        
        :param other: The object with which to compare'''
        raise NotImplementedError()
    
    def compare_to(self, obj : Any) -> int:
        '''Compares current object to other.
        
        :param obj: The other object
        :returns: zero if equal'''
        raise NotImplementedError()
    
    @staticmethod
    def from_filename(file_name : str) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for specified fileName
        
        :param file_name: The file name
        :returns: The file type of specified file name'''
        raise NotImplementedError()
    
    @staticmethod
    def from_extension(file_extension : str) -> groupdocs.conversion.filetypes.FileType:
        '''Gets FileType for provided fileExtension
        
        :param file_extension: File extension
        :returns: File type'''
        raise NotImplementedError()
    
    @staticmethod
    def from_stream(stream : io._IOBase) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for provided document stream
        
        :param stream: Stream which will be probed
        :returns: The file type of provided stream'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> str:
        '''The file format'''
        raise NotImplementedError()
    
    @property
    def extension(self) -> str:
        '''The file extension'''
        raise NotImplementedError()
    
    @property
    def family(self) -> str:
        '''The file family'''
        raise NotImplementedError()
    
    @property
    def description(self) -> str:
        '''File type description'''
        raise NotImplementedError()
    
    @property
    def UNKNOWN(self) -> groupdocs.conversion.filetypes.FileType:
        '''Unknown file type'''
        raise NotImplementedError()

    @property
    def MPT(self) -> groupdocs.conversion.filetypes.ProjectManagementFileType:
        '''Microsoft Project template files, contain basic information and structure along with document settings for creating .MPP files.
        Learn more about this file format `here <https://wiki.fileformat.com/project-management/mpt>`.'''
        raise NotImplementedError()

    @property
    def MPP(self) -> groupdocs.conversion.filetypes.ProjectManagementFileType:
        '''MPP is Microsoft Project data file that stores information related to project management in an integrated manner.
        Learn more about this file format `here <https://wiki.fileformat.com/project-management/mpp>`.'''
        raise NotImplementedError()

    @property
    def MPX(self) -> groupdocs.conversion.filetypes.ProjectManagementFileType:
        '''Microsoft Exchange File Format, is an ASCII file format for transferring of project information between Microsoft Project (MSP) and other applications that support the MPX file format such as Primavera Project Planner, Sciforma and Timerline Precision Estimating.
        Learn more about this file format `here <https://wiki.fileformat.com/project-management/mpx>`.'''
        raise NotImplementedError()

    @property
    def XER(self) -> groupdocs.conversion.filetypes.ProjectManagementFileType:
        '''The XER file format is a proprietary project file format used by Primavera P6 project planning and management application.
        Learn more about this file format `here <https://docs.fileformat.com/project-management/xer>`.'''
        raise NotImplementedError()


class PublisherFileType(FileType):
    '''Defines Publisher documents
    Includes the following types:
    :py:attr:`groupdocs.conversion.filetypes.PublisherFileType.PUB`
    Learn more about Publisher formats `here <https://docs.fileformat.com/publisher/>`.'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.Enumeration) -> bool:
        '''Implements :py:func:`groupdocs.conversion.contracts.Enumeration.equals`
        
        :param other: The object with which to compare'''
        raise NotImplementedError()
    
    def compare_to(self, obj : Any) -> int:
        '''Compares current object to other.
        
        :param obj: The other object
        :returns: zero if equal'''
        raise NotImplementedError()
    
    @staticmethod
    def from_filename(file_name : str) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for specified fileName
        
        :param file_name: The file name
        :returns: The file type of specified file name'''
        raise NotImplementedError()
    
    @staticmethod
    def from_extension(file_extension : str) -> groupdocs.conversion.filetypes.FileType:
        '''Gets FileType for provided fileExtension
        
        :param file_extension: File extension
        :returns: File type'''
        raise NotImplementedError()
    
    @staticmethod
    def from_stream(stream : io._IOBase) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for provided document stream
        
        :param stream: Stream which will be probed
        :returns: The file type of provided stream'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> str:
        '''The file format'''
        raise NotImplementedError()
    
    @property
    def extension(self) -> str:
        '''The file extension'''
        raise NotImplementedError()
    
    @property
    def family(self) -> str:
        '''The file family'''
        raise NotImplementedError()
    
    @property
    def description(self) -> str:
        '''File type description'''
        raise NotImplementedError()
    
    @property
    def UNKNOWN(self) -> groupdocs.conversion.filetypes.FileType:
        '''Unknown file type'''
        raise NotImplementedError()

    @property
    def PUB(self) -> groupdocs.conversion.filetypes.PublisherFileType:
        '''A PUB file is a Microsoft Publisher document file format. It is used to create several types of design layout documents such as newsletters, flyers, brochures, postcards, etc. PUB files can contain text, raster and vector images.
        Learn more about this file format `here <https://docs.fileformat.com/publisher/pub/>`.'''
        raise NotImplementedError()


class SpreadsheetFileType(FileType):
    '''Defines Spreadsheet documents. Includes the following file types:
    :py:attr:`groupdocs.conversion.filetypes.SpreadsheetFileType.CSV`,
    :py:attr:`groupdocs.conversion.filetypes.SpreadsheetFileType.FODS`,
    :py:attr:`groupdocs.conversion.filetypes.SpreadsheetFileType.ODS`,
    :py:attr:`groupdocs.conversion.filetypes.SpreadsheetFileType.OTS`,
    :py:attr:`groupdocs.conversion.filetypes.SpreadsheetFileType.TSV`,
    :py:attr:`groupdocs.conversion.filetypes.SpreadsheetFileType.XLAM`,
    :py:attr:`groupdocs.conversion.filetypes.SpreadsheetFileType.XLS`,
    :py:attr:`groupdocs.conversion.filetypes.SpreadsheetFileType.XLSB`,
    :py:attr:`groupdocs.conversion.filetypes.SpreadsheetFileType.XLSM`,
    :py:attr:`groupdocs.conversion.filetypes.SpreadsheetFileType.XLSX`,
    :py:attr:`groupdocs.conversion.filetypes.SpreadsheetFileType.XLT`,
    :py:attr:`groupdocs.conversion.filetypes.SpreadsheetFileType.XLTM`,
    :py:attr:`groupdocs.conversion.filetypes.SpreadsheetFileType.XLTX`.
    Learn more about Spreadsheet formats `here <https://wiki.fileformat.com/spreadsheet>`.'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.Enumeration) -> bool:
        '''Implements :py:func:`groupdocs.conversion.contracts.Enumeration.equals`
        
        :param other: The object with which to compare'''
        raise NotImplementedError()
    
    def compare_to(self, obj : Any) -> int:
        '''Compares current object to other.
        
        :param obj: The other object
        :returns: zero if equal'''
        raise NotImplementedError()
    
    @staticmethod
    def from_filename(file_name : str) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for specified fileName
        
        :param file_name: The file name
        :returns: The file type of specified file name'''
        raise NotImplementedError()
    
    @staticmethod
    def from_extension(file_extension : str) -> groupdocs.conversion.filetypes.FileType:
        '''Gets FileType for provided fileExtension
        
        :param file_extension: File extension
        :returns: File type'''
        raise NotImplementedError()
    
    @staticmethod
    def from_stream(stream : io._IOBase) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for provided document stream
        
        :param stream: Stream which will be probed
        :returns: The file type of provided stream'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> str:
        '''The file format'''
        raise NotImplementedError()
    
    @property
    def extension(self) -> str:
        '''The file extension'''
        raise NotImplementedError()
    
    @property
    def family(self) -> str:
        '''The file family'''
        raise NotImplementedError()
    
    @property
    def description(self) -> str:
        '''File type description'''
        raise NotImplementedError()
    
    @property
    def UNKNOWN(self) -> groupdocs.conversion.filetypes.FileType:
        '''Unknown file type'''
        raise NotImplementedError()

    @property
    def XLS(self) -> groupdocs.conversion.filetypes.SpreadsheetFileType:
        '''XLS represents Excel Binary File Format. Such files can be created by Microsoft Excel as well as other similar spreadsheet programs such as OpenOffice Calc or Apple Numbers.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/xls>`.'''
        raise NotImplementedError()

    @property
    def XLSX(self) -> groupdocs.conversion.filetypes.SpreadsheetFileType:
        '''XLSX is well-known format for Microsoft Excel documents that was introduced by Microsoft with the release of Microsoft Office 2007.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/xlsx>`.'''
        raise NotImplementedError()

    @property
    def XLSM(self) -> groupdocs.conversion.filetypes.SpreadsheetFileType:
        '''XLSM is a type of Spreadsheet files that support macros.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/xlsm>`.'''
        raise NotImplementedError()

    @property
    def XLSB(self) -> groupdocs.conversion.filetypes.SpreadsheetFileType:
        '''XLSB file format specifies the Excel Binary File Format, which is a collection of records and structures that specify Excel workbook content.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/xlsb>`.'''
        raise NotImplementedError()

    @property
    def ODS(self) -> groupdocs.conversion.filetypes.SpreadsheetFileType:
        '''Files with ODS extension stand for OpenDocument Spreadsheet Document format that are editable by user. Data is stored inside ODF file into rows and columns.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/ods>`.'''
        raise NotImplementedError()

    @property
    def OTS(self) -> groupdocs.conversion.filetypes.SpreadsheetFileType:
        '''A file with .ots extension is an OpenDocument Spreadsheet Template file that is created with the Calc application software included in Apache OpenOffice. Calc application software is the similar to Excel available in Microsoft Office.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/ots>`.'''
        raise NotImplementedError()

    @property
    def XLTX(self) -> groupdocs.conversion.filetypes.SpreadsheetFileType:
        '''XLTX file represents Microsoft Excel Template that are based on the Office OpenXML file format specifications. It is used to create a standard template file that can be utilized to generate XLSX files that exhibit the same settings as specified in the XLTX file.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/xltx>`.'''
        raise NotImplementedError()

    @property
    def XLT(self) -> groupdocs.conversion.filetypes.SpreadsheetFileType:
        '''Files with .XLT extension are template files created with Microsoft Excel which is a spreadsheet application which comes as part of Microsoft Office suite.  Microsoft Office 97-2003 supported creating new XLT files as well as opening these.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/xlt>`.'''
        raise NotImplementedError()

    @property
    def XLTM(self) -> groupdocs.conversion.filetypes.SpreadsheetFileType:
        '''The XLTM file extension represents files that are generated by Microsoft Excel as Macro-enabled template files. XLTM files are similar to XLTX in structure other than that the later doesn\'t support creating template files with macros.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/xltm>`.'''
        raise NotImplementedError()

    @property
    def TSV(self) -> groupdocs.conversion.filetypes.SpreadsheetFileType:
        '''A Tab-Separated Values (TSV) file format represents data separated with tabs in plain text format.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/tsv>`.'''
        raise NotImplementedError()

    @property
    def XLAM(self) -> groupdocs.conversion.filetypes.SpreadsheetFileType:
        '''XLAM is an Macro-Enabled Add-In file that is used to add new functions to spreadsheets. An Add-In is a supplemental program that runs additional code and provides additional functionality for spreadsheets.
        Learn more about this file format `here <https://docs.fileformat.com/spreadsheet/xlam/>`.'''
        raise NotImplementedError()

    @property
    def CSV(self) -> groupdocs.conversion.filetypes.SpreadsheetFileType:
        '''Files with CSV (Comma Separated Values) extension represent plain text files that contain records of data with comma separated values.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/csv>`.'''
        raise NotImplementedError()

    @property
    def FODS(self) -> groupdocs.conversion.filetypes.SpreadsheetFileType:
        '''A file with .fods extension is a type of OpenDocument Spreadsheet document format that stores data in rows and columns. The format is specified as part of ODF 1.2 specifications published and maintained by OASIS.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/fods>`.'''
        raise NotImplementedError()

    @property
    def DIF(self) -> groupdocs.conversion.filetypes.SpreadsheetFileType:
        '''DIF stands for Data Interchange Format that is used to import/export spreadsheets data between different applications. These include Microsoft Excel, OpenOffice Calc, StarCalc and many others.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/dif>`.'''
        raise NotImplementedError()

    @property
    def SXC(self) -> groupdocs.conversion.filetypes.SpreadsheetFileType:
        '''The file format SXC(Sun XML Calc) belongs to an office suite called OpenOffice.org. This format generally deals with the spreadsheet needs of users as it is an XML based spreadsheet file format. SXC format supports formulas, functions, macros and charts along with DataPilot.
        Learn more about this file format `here <https://wiki.fileformat.com/spreadsheet/sxc>`.'''
        raise NotImplementedError()

    @property
    def NUMBERS(self) -> groupdocs.conversion.filetypes.SpreadsheetFileType:
        '''The files with .numbers extension are classified as spreadsheet file type, that’s why they are similar to the .xlsx files; but the Numbers files are created by using Apple iWork Numbers spreadsheet software.
        Learn more about this file format `here <https://docs.fileformat.com/spreadsheet/numbers>`.'''
        raise NotImplementedError()


class ThreeDFileType(FileType):
    '''Defines 3D documents
    Includes the following types:
    :py:attr:`groupdocs.conversion.filetypes.ThreeDFileType.FBX`:py:attr:`groupdocs.conversion.filetypes.ThreeDFileType.THREE_DS`:py:attr:`groupdocs.conversion.filetypes.ThreeDFileType.THREE_MF`:py:attr:`groupdocs.conversion.filetypes.ThreeDFileType.AMF`:py:attr:`groupdocs.conversion.filetypes.ThreeDFileType.ASE`:py:attr:`groupdocs.conversion.filetypes.ThreeDFileType.RVM`:py:attr:`groupdocs.conversion.filetypes.ThreeDFileType.DAE`:py:attr:`groupdocs.conversion.filetypes.ThreeDFileType.DRC`:py:attr:`groupdocs.conversion.filetypes.ThreeDFileType.GLTF`:py:attr:`groupdocs.conversion.filetypes.ThreeDFileType.OBJ`:py:attr:`groupdocs.conversion.filetypes.ThreeDFileType.PLY`:py:attr:`groupdocs.conversion.filetypes.ThreeDFileType.JT`:py:attr:`groupdocs.conversion.filetypes.ThreeDFileType.U3D`:py:attr:`groupdocs.conversion.filetypes.ThreeDFileType.USD`:py:attr:`groupdocs.conversion.filetypes.ThreeDFileType.USDZ`:py:attr:`groupdocs.conversion.filetypes.ThreeDFileType.VRML`:py:attr:`groupdocs.conversion.filetypes.ThreeDFileType.X`:py:attr:`groupdocs.conversion.filetypes.ThreeDFileType.GLB`:py:attr:`groupdocs.conversion.filetypes.ThreeDFileType.MA`:py:attr:`groupdocs.conversion.filetypes.ThreeDFileType.MB`
    Learn more about 3D formats `here <https://wiki.fileformat.com/3d>`.'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.Enumeration) -> bool:
        '''Implements :py:func:`groupdocs.conversion.contracts.Enumeration.equals`
        
        :param other: The object with which to compare'''
        raise NotImplementedError()
    
    def compare_to(self, obj : Any) -> int:
        '''Compares current object to other.
        
        :param obj: The other object
        :returns: zero if equal'''
        raise NotImplementedError()
    
    @staticmethod
    def from_filename(file_name : str) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for specified fileName
        
        :param file_name: The file name
        :returns: The file type of specified file name'''
        raise NotImplementedError()
    
    @staticmethod
    def from_extension(file_extension : str) -> groupdocs.conversion.filetypes.FileType:
        '''Gets FileType for provided fileExtension
        
        :param file_extension: File extension
        :returns: File type'''
        raise NotImplementedError()
    
    @staticmethod
    def from_stream(stream : io._IOBase) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for provided document stream
        
        :param stream: Stream which will be probed
        :returns: The file type of provided stream'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> str:
        '''The file format'''
        raise NotImplementedError()
    
    @property
    def extension(self) -> str:
        '''The file extension'''
        raise NotImplementedError()
    
    @property
    def family(self) -> str:
        '''The file family'''
        raise NotImplementedError()
    
    @property
    def description(self) -> str:
        '''File type description'''
        raise NotImplementedError()
    
    @property
    def UNKNOWN(self) -> groupdocs.conversion.filetypes.FileType:
        '''Unknown file type'''
        raise NotImplementedError()

    @property
    def FBX(self) -> groupdocs.conversion.filetypes.ThreeDFileType:
        '''FBX, FilmBox, is a popular 3D file format that was originally developed by Kaydara for MotionBuilder. It was acquired by Autodesk Inc in 2006 and is now one of the main 3D exchange formats as used by many 3D tools. FBX is available in both binary and ASCII file format.
        Learn more about this file format `here <https://docs.fileformat.com/3d/fbx>`.'''
        raise NotImplementedError()

    @property
    def THREE_DS(self) -> groupdocs.conversion.filetypes.ThreeDFileType:
        '''A file with .3ds extension represents 3D Sudio (DOS) mesh file format used by Autodesk 3D Studio. Autodesk 3D Studio has been in 3D file format market since 1990s and has now evolved to 3D Studio MAX for working with 3D modeling, animation and rendering.
        Learn more about this file format `here <https://docs.fileformat.com/3d/3ds>`.'''
        raise NotImplementedError()

    @property
    def THREE_MF(self) -> groupdocs.conversion.filetypes.ThreeDFileType:
        '''3MF, 3D Manufacturing Format, is used by applications to render 3D object models to a variety of other applications, platforms, services and printers. It was built to avoid the limitations and issues in other 3D file formats, like STL, for working with the latest versions of 3D printers.
        Learn more about this file format `here <https://docs.fileformat.com/3d/3mf>`.'''
        raise NotImplementedError()

    @property
    def AMF(self) -> groupdocs.conversion.filetypes.ThreeDFileType:
        '''An AMF file consists of guidelines for objects description in order to be used by Additive Manufacturing processes. It contains an opening XML tag and ends with a element. This is preceded by an XML declaration line specifying the XML version and encoding of the file.
        Learn more about this file format `here <https://docs.fileformat.com/3d/amf>`.'''
        raise NotImplementedError()

    @property
    def ASE(self) -> groupdocs.conversion.filetypes.ThreeDFileType:
        '''A file with a .ase extension is an Autodesk ASCII Scene Export file format that is an ASCII representation of a scene, containing 2D or 3D information while exporting scene data using Autodesk.
        Learn more about this file format `here <https://docs.fileformat.com/3d/ase>`.'''
        raise NotImplementedError()

    @property
    def RVM(self) -> groupdocs.conversion.filetypes.ThreeDFileType:
        '''RVM data files are related to AVEVA PDMS. RVM file is an AVEVA Plant Design Management System Model project file. AVEVA’s Plant Design Management System (PDMS) is the most popular 3D design system using data-centric technology for managing projects.
        Learn more about this file format `here <https://docs.fileformat.com/3d/rvm>`.'''
        raise NotImplementedError()

    @property
    def DAE(self) -> groupdocs.conversion.filetypes.ThreeDFileType:
        '''A DAE file is a Digital Asset Exchange file format that is used for exchanging data between interactive 3D applications. This file format is based on the COLLADA (COLLAborative Design Activity) XML schema which is an open standard XML schema for the exchange of digital assets among graphics software applications.
        Learn more about this file format `here <https://docs.fileformat.com/3d/dae>`.'''
        raise NotImplementedError()

    @property
    def DRC(self) -> groupdocs.conversion.filetypes.ThreeDFileType:
        '''A file with .drc extension is a compressed 3D file format created with Google Draco library. Google offers Draco as open source library for compressing and decompressing 3D geometric meshes and point clouds, and improves storage and transmission of 3D graphics.
        Learn more about this file format `here <https://docs.fileformat.com/3d/drc>`.'''
        raise NotImplementedError()

    @property
    def GLTF(self) -> groupdocs.conversion.filetypes.ThreeDFileType:
        '''glTF (GL Transmission Format) is a 3D file format that stores 3D model information in JSON format. The use of JSON minimizes both the size of 3D assets and the runtime processing needed to unpack and use those assets.
        Learn more about this file format `here <https://docs.fileformat.com/3d/gltf>`.'''
        raise NotImplementedError()

    @property
    def OBJ(self) -> groupdocs.conversion.filetypes.ThreeDFileType:
        '''OBJ files are used by Wavefront’s Advanced Visualizer application to define and store the geometric objects. Backward and forward transmission of geometric data is made possible through OBJ files.
        Learn more about this file format `here <https://docs.fileformat.com/3d/obj>`.'''
        raise NotImplementedError()

    @property
    def PLY(self) -> groupdocs.conversion.filetypes.ThreeDFileType:
        '''PLY, Polygon File Format, represents 3D file format that stores graphical objects described as a collection of polygons. The purpose of this file format was to establish a simple and easy file type that is general enough to be useful for a wide range of models.
        Learn more about this file format `here <https://docs.fileformat.com/3d/ply>`.'''
        raise NotImplementedError()

    @property
    def JT(self) -> groupdocs.conversion.filetypes.ThreeDFileType:
        '''JT (Jupiter Tessellation) is an efficient, industry-focused and flexible ISO-standardized 3D data format developed by Siemens PLM Software. Mechanical CAD domains of Aerospace, automotive industry, and Heavy Equipment use JT as their most leading 3D visualization format.
        Learn more about this file format `here <https://docs.fileformat.com/3d/jt>`.'''
        raise NotImplementedError()

    @property
    def U3D(self) -> groupdocs.conversion.filetypes.ThreeDFileType:
        '''U3D (Universal 3D) is a compressed file format and data structure for 3D computer graphics. It contains 3D model information such as triangle meshes, lighting, shading, motion data, lines and points with color and structure.
        Learn more about this file format `here <https://docs.fileformat.com/3d/u3d>`.'''
        raise NotImplementedError()

    @property
    def USD(self) -> groupdocs.conversion.filetypes.ThreeDFileType:
        '''A file with .usd extension is a Universal Scene Description file format that encodes data for the purpose of data interchanging and augmenting between digital content creation applications. Developed by Pixar, USD provides the ability to interchange elemental assets (such as models) or animation.
        Learn more about this file format `here <https://docs.fileformat.com/3d/usd>`.'''
        raise NotImplementedError()

    @property
    def USDZ(self) -> groupdocs.conversion.filetypes.ThreeDFileType:
        '''A file with .usdz is an uncompressed and unencrypted ZIP archive for the USD (Universal Scene Description) file format that contains and proxies for files of other formats (such as textures, and animations) embedded within the archive and runs them directly with the USD run-time without any need of unpacking.
        Learn more about this file format `here <https://docs.fileformat.com/3d/usdz>`.'''
        raise NotImplementedError()

    @property
    def VRML(self) -> groupdocs.conversion.filetypes.ThreeDFileType:
        '''The Virtual Reality Modeling Language (VRML) is a file format for representation of interactive 3D world objects over the World Wide Web (www). It finds its usage in creating three-dimensional representations of complex scenes such as illustrations, definition and virtual reality presentations.
        Learn more about this file format `here <https://docs.fileformat.com/3d/vrml>`.'''
        raise NotImplementedError()

    @property
    def X(self) -> groupdocs.conversion.filetypes.ThreeDFileType:
        '''A file with .x extension refers to DirectX 3D Graphics legacy file format that was introduced with Microsoft DirectX 2.0. It was used for 3D graphics rendering in games and specifies the structures for meshes, textures, animations, and user-defined objects. It has been deprecated since 2014 as the Autodesk FBX file format serves better as a more modern format.
        Learn more about this file format `here <https://docs.fileformat.com/3d/x>`.'''
        raise NotImplementedError()

    @property
    def GLB(self) -> groupdocs.conversion.filetypes.ThreeDFileType:
        '''GLB is the binary file format representation of 3D models saved in the GL Transmission Format (glTF). This binary format stores the glTF asset (JSON, .bin and images) in a binary blob.
        Learn more about this file format `here <https://docs.fileformat.com/3d/glb>`.'''
        raise NotImplementedError()

    @property
    def MA(self) -> groupdocs.conversion.filetypes.ThreeDFileType:
        '''A file with .ma extension is a 3D project file created with Autodesk Maya application. It contains large list of textual commands to specify information about the file.
        Learn more about this file format `here <https://docs.fileformat.com/3d/ma>`.'''
        raise NotImplementedError()

    @property
    def MB(self) -> groupdocs.conversion.filetypes.ThreeDFileType:
        '''A file with .mb extension is a binary project file created with Autodesk Maya application. Unlike the MA file format, which is in ASCII file format, MB files are stored in binary file format.
        Learn more about this file format `here <https://docs.fileformat.com/3d/mb>`.'''
        raise NotImplementedError()


class WebFileType(FileType):
    '''Defines Web documents. Includes the following file types:
    :py:attr:`groupdocs.conversion.filetypes.WebFileType.XML`:py:attr:`groupdocs.conversion.filetypes.WebFileType.JSON`:py:attr:`groupdocs.conversion.filetypes.WebFileType.HTML`:py:attr:`groupdocs.conversion.filetypes.WebFileType.HTM`:py:attr:`groupdocs.conversion.filetypes.WebFileType.MHT`:py:attr:`groupdocs.conversion.filetypes.WebFileType.MHTML`:py:attr:`groupdocs.conversion.filetypes.WebFileType.CHM`'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.Enumeration) -> bool:
        '''Implements :py:func:`groupdocs.conversion.contracts.Enumeration.equals`
        
        :param other: The object with which to compare'''
        raise NotImplementedError()
    
    def compare_to(self, obj : Any) -> int:
        '''Compares current object to other.
        
        :param obj: The other object
        :returns: zero if equal'''
        raise NotImplementedError()
    
    @staticmethod
    def from_filename(file_name : str) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for specified fileName
        
        :param file_name: The file name
        :returns: The file type of specified file name'''
        raise NotImplementedError()
    
    @staticmethod
    def from_extension(file_extension : str) -> groupdocs.conversion.filetypes.FileType:
        '''Gets FileType for provided fileExtension
        
        :param file_extension: File extension
        :returns: File type'''
        raise NotImplementedError()
    
    @staticmethod
    def from_stream(stream : io._IOBase) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for provided document stream
        
        :param stream: Stream which will be probed
        :returns: The file type of provided stream'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> str:
        '''The file format'''
        raise NotImplementedError()
    
    @property
    def extension(self) -> str:
        '''The file extension'''
        raise NotImplementedError()
    
    @property
    def family(self) -> str:
        '''The file family'''
        raise NotImplementedError()
    
    @property
    def description(self) -> str:
        '''File type description'''
        raise NotImplementedError()
    
    @property
    def UNKNOWN(self) -> groupdocs.conversion.filetypes.FileType:
        '''Unknown file type'''
        raise NotImplementedError()

    @property
    def XML(self) -> groupdocs.conversion.filetypes.WebFileType:
        '''XML stands for Extensible Markup Language that is similar to HTML but different in using tags for defining objects.
        Learn more about this file format `here <https://wiki.fileformat.com/web/xml>`.'''
        raise NotImplementedError()

    @property
    def JSON(self) -> groupdocs.conversion.filetypes.WebFileType:
        '''JSON (JavaScript Object Notation) is an open standard file format for sharing data that uses human-readable text to store and transmit data.
        Learn more about this file format `here <https://docs.fileformat.com/web/json>`.'''
        raise NotImplementedError()

    @property
    def HTML(self) -> groupdocs.conversion.filetypes.WebFileType:
        '''HTML (Hyper Text Markup Language) is the extension for web pages created for display in browsers.
        Learn more about this file format `here <https://wiki.fileformat.com/web/html>`.'''
        raise NotImplementedError()

    @property
    def HTM(self) -> groupdocs.conversion.filetypes.WebFileType:
        '''HTM (Hyper Text Markup Language) is the extension for web pages created for display in browsers.
        Learn more about this file format `here <https://wiki.fileformat.com/web/html>`.'''
        raise NotImplementedError()

    @property
    def MHT(self) -> groupdocs.conversion.filetypes.WebFileType:
        '''Files with MHTML extension represent a web page archive format that can be created by a number of different applications. The format is known as archive format because it saves the web HTML code and associated resources in a single file.
        Learn more about this file format `here <https://wiki.fileformat.com/web/mhtml>`.'''
        raise NotImplementedError()

    @property
    def MHTML(self) -> groupdocs.conversion.filetypes.WebFileType:
        '''Files with MHTML extension represent a web page archive format that can be created by a number of different applications. The format is known as archive format because it saves the web HTML code and associated resources in a single file.
        Learn more about this file format `here <https://wiki.fileformat.com/web/mhtml>`.'''
        raise NotImplementedError()

    @property
    def CHM(self) -> groupdocs.conversion.filetypes.WebFileType:
        '''The CHM file format represents Microsoft HTML help file that consists of a collection of HTML pages. It provides an index for quick accessing the topics and navigation to different parts of the help document.
        Learn more about this file format `here <https://docs.fileformat.com/web/chm>`.'''
        raise NotImplementedError()


class WordProcessingFileType(FileType):
    '''Defines Word Processing files that contain user information in plain text or rich text format. A plain text file format contains unformatted text and no font or page settings etc. can be applied. In contrast, a rich text file format allows formatting options such as setting fonts type, styles (bold, italic, underline, etc.), page margins, headings, bullets and numbers, and several other formatting features.
    Includes the following file types:
    :py:attr:`groupdocs.conversion.filetypes.WordProcessingFileType.DOC`,
    :py:attr:`groupdocs.conversion.filetypes.WordProcessingFileType.DOCM`,
    :py:attr:`groupdocs.conversion.filetypes.WordProcessingFileType.DOCX`,
    :py:attr:`groupdocs.conversion.filetypes.WordProcessingFileType.DOT`,
    :py:attr:`groupdocs.conversion.filetypes.WordProcessingFileType.DOTM`,
    :py:attr:`groupdocs.conversion.filetypes.WordProcessingFileType.DOTX`,
    :py:attr:`groupdocs.conversion.filetypes.WordProcessingFileType.ODT`,
    :py:attr:`groupdocs.conversion.filetypes.WordProcessingFileType.OTT`,
    :py:attr:`groupdocs.conversion.filetypes.WordProcessingFileType.RTF`,
    :py:attr:`groupdocs.conversion.filetypes.WordProcessingFileType.TXT`.
    :py:attr:`groupdocs.conversion.filetypes.WordProcessingFileType.MD`.
    Learn more about Word Processing formats `here <https://wiki.fileformat.com/word-processing>`.'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.Enumeration) -> bool:
        '''Implements :py:func:`groupdocs.conversion.contracts.Enumeration.equals`
        
        :param other: The object with which to compare'''
        raise NotImplementedError()
    
    def compare_to(self, obj : Any) -> int:
        '''Compares current object to other.
        
        :param obj: The other object
        :returns: zero if equal'''
        raise NotImplementedError()
    
    @staticmethod
    def from_filename(file_name : str) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for specified fileName
        
        :param file_name: The file name
        :returns: The file type of specified file name'''
        raise NotImplementedError()
    
    @staticmethod
    def from_extension(file_extension : str) -> groupdocs.conversion.filetypes.FileType:
        '''Gets FileType for provided fileExtension
        
        :param file_extension: File extension
        :returns: File type'''
        raise NotImplementedError()
    
    @staticmethod
    def from_stream(stream : io._IOBase) -> groupdocs.conversion.filetypes.FileType:
        '''Returns FileType for provided document stream
        
        :param stream: Stream which will be probed
        :returns: The file type of provided stream'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> str:
        '''The file format'''
        raise NotImplementedError()
    
    @property
    def extension(self) -> str:
        '''The file extension'''
        raise NotImplementedError()
    
    @property
    def family(self) -> str:
        '''The file family'''
        raise NotImplementedError()
    
    @property
    def description(self) -> str:
        '''File type description'''
        raise NotImplementedError()
    
    @property
    def UNKNOWN(self) -> groupdocs.conversion.filetypes.FileType:
        '''Unknown file type'''
        raise NotImplementedError()

    @property
    def DOC(self) -> groupdocs.conversion.filetypes.WordProcessingFileType:
        '''Files with .doc extension represent documents generated by Microsoft Word or other word processing documents in binary file format.
        Learn more about this file format `here <https://wiki.fileformat.com/word-processing/doc>`.'''
        raise NotImplementedError()

    @property
    def DOCM(self) -> groupdocs.conversion.filetypes.WordProcessingFileType:
        '''DOCM files are Microsoft Word 2007 or higher generated documents with the ability to run macros.
        Learn more about this file format `here <https://wiki.fileformat.com/word-processing/docm>`.'''
        raise NotImplementedError()

    @property
    def DOCX(self) -> groupdocs.conversion.filetypes.WordProcessingFileType:
        '''DOCX is a well-known format for Microsoft Word documents. Introduced from 2007 with the release of Microsoft Office 2007, the structure of this new Document format was changed from plain binary to a combination of XML and binary files.
        Learn more about this file format `here <https://wiki.fileformat.com/word-processing/docx>`.'''
        raise NotImplementedError()

    @property
    def DOT(self) -> groupdocs.conversion.filetypes.WordProcessingFileType:
        '''Files with .DOT extension are template files created by Microsoft Word to have pre-formatted settings for generation of further DOC or DOCX files.
        Learn more about this file format `here <https://wiki.fileformat.com/word-processing/dot>`.'''
        raise NotImplementedError()

    @property
    def DOTM(self) -> groupdocs.conversion.filetypes.WordProcessingFileType:
        '''A file with DOTM extension represents template file created with Microsoft Word 2007 or higher.
        Learn more about this file format `here <https://wiki.fileformat.com/word-processing/dotm>`.'''
        raise NotImplementedError()

    @property
    def DOTX(self) -> groupdocs.conversion.filetypes.WordProcessingFileType:
        '''Files with DOTX extension are template files created by Microsoft Word to have pre-formatted settings for generation of further DOCX files.
        Learn more about this file format `here <https://wiki.fileformat.com/word-processing/dotx>`.'''
        raise NotImplementedError()

    @property
    def RTF(self) -> groupdocs.conversion.filetypes.WordProcessingFileType:
        '''Introduced and documented by Microsoft, the Rich Text Format (RTF) represents a method of encoding formatted text and graphics for use within applications.
        Learn more about this file format `here <https://wiki.fileformat.com/word-processing/rtf>`.'''
        raise NotImplementedError()

    @property
    def ODT(self) -> groupdocs.conversion.filetypes.WordProcessingFileType:
        '''ODT files are type of documents created with word processing applications that are based on OpenDocument Text File format.
        Learn more about this file format `here <https://wiki.fileformat.com/word-processing/odt>`.'''
        raise NotImplementedError()

    @property
    def OTT(self) -> groupdocs.conversion.filetypes.WordProcessingFileType:
        '''Files with OTT extension represent template documents generated by applications in compliance with the OASIS\' OpenDocument standard format.
        Learn more about this file format `here <https://wiki.fileformat.com/word-processing/ott>`.'''
        raise NotImplementedError()

    @property
    def TXT(self) -> groupdocs.conversion.filetypes.WordProcessingFileType:
        '''A file with .TXT extension represents a text document that contains plain text in the form of lines.
        Learn more about this file format `here <https://wiki.fileformat.com/word-processing/txt>`.'''
        raise NotImplementedError()

    @property
    def MD(self) -> groupdocs.conversion.filetypes.WordProcessingFileType:
        '''Text files created with Markdown language dialects is saved with .MD or .MARKDOWN file extension. MD files are saved in plain text format that uses Markdown language which also includes inline text symbols, defining how a text can be formatted such as indentations, table formatting, fonts, and headers.
        Learn more about this file format `here <https://wiki.fileformat.com/word-processing/md>`.'''
        raise NotImplementedError()


