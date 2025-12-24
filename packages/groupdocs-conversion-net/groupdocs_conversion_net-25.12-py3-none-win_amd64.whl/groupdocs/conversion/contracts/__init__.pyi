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

class AudioDocumentInfo(DocumentInfo):
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class BitmapInfo(ValueObject):
    '''Object containing array of pixels and bitmap information.'''
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @staticmethod
    def create(pixel_bytes : List[int], width : int, height : int, format : GroupDocs.Conversion.Contracts.BitmapInfo+PixelFormat) -> groupdocs.conversion.contracts.BitmapInfo:
        raise NotImplementedError()
    
    @property
    def format(self) -> GroupDocs.Conversion.Contracts.BitmapInfo+PixelFormat:
        '''Gets the pixel format of the bitmap.'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''Gets the height of the bitmap.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''Gets the width of the bitmap.'''
        raise NotImplementedError()
    
    @property
    def pixel_bytes(self) -> List[int]:
        '''Gets the array of pixels.'''
        raise NotImplementedError()
    

class Bzip2DocumentInfo(DocumentInfo):
    '''Contains Bzip2 document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class CabDocumentInfo(DocumentInfo):
    '''Contains Cab document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class CadDocumentInfo(DocumentInfo):
    '''Contains Cad document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''Width'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''Height'''
        raise NotImplementedError()
    
    @property
    def layouts(self) -> System.Collections.Generic.IList`1[[System.String]]:
        '''Layouts in the document'''
        raise NotImplementedError()
    
    @property
    def layers(self) -> System.Collections.Generic.IList`1[[System.String]]:
        '''Layers in the document'''
        raise NotImplementedError()
    

class CgmDocumentInfo(PdfDocumentInfo):
    '''Contains Cgm document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def version(self) -> str:
        '''Gets version'''
        raise NotImplementedError()
    
    @property
    def title(self) -> str:
        '''Gets title'''
        raise NotImplementedError()
    
    @property
    def author(self) -> str:
        '''Gets author'''
        raise NotImplementedError()
    
    @property
    def is_password_protected(self) -> bool:
        '''Gets is document password protected'''
        raise NotImplementedError()
    
    @property
    def is_landscape(self) -> bool:
        '''Gets is page landscaped'''
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        '''Gets page height'''
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        '''Gets page width'''
        raise NotImplementedError()
    
    @property
    def table_of_contents(self) -> System.Collections.Generic.IList`1[[GroupDocs.Conversion.Contracts.TableOfContentsItem]]:
        '''Table of contents'''
        raise NotImplementedError()
    

class CpioDocumentInfo(DocumentInfo):
    '''Contains Cpio document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class CsvDocumentInfo(SpreadsheetDocumentInfo):
    '''Contains Csv document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def title(self) -> str:
        '''Gets title'''
        raise NotImplementedError()
    
    @property
    def worksheets(self) -> List[str]:
        '''Worksheets names'''
        raise NotImplementedError()
    
    @property
    def worksheets_count(self) -> int:
        '''Gets worksheets count'''
        raise NotImplementedError()
    
    @property
    def author(self) -> str:
        '''Gets author'''
        raise NotImplementedError()
    
    @property
    def is_password_protected(self) -> bool:
        '''Gets is document password protected'''
        raise NotImplementedError()
    

class DiagramDocumentInfo(DocumentInfo):
    '''Contains Diagram document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class DjVuDocumentInfo(ImageDocumentInfo):
    '''Contains DjVu document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def bits_per_pixel(self) -> int:
        '''Gets bits per pixel'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''Gets height'''
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''Gets width'''
        raise NotImplementedError()
    
    @property
    def vertical_resolution(self) -> float:
        '''Gets vertical resolution'''
        raise NotImplementedError()
    
    @property
    def horizontal_resolution(self) -> float:
        '''Get horizontal resolution'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> float:
        '''Gets image opacity'''
        raise NotImplementedError()
    

class DocumentInfo(IDocumentInfo):
    '''Provides base implementation for retrieving polymorphic document information'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class EmailDocumentInfo(DocumentInfo):
    '''Contains Email document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def is_signed(self) -> bool:
        '''Gets is signed'''
        raise NotImplementedError()
    
    @property
    def is_encrypted(self) -> bool:
        '''Gets is encrypted'''
        raise NotImplementedError()
    
    @property
    def is_html(self) -> bool:
        '''Gets is html'''
        raise NotImplementedError()
    
    @property
    def attachments_count(self) -> int:
        '''Gets attachments count'''
        raise NotImplementedError()
    
    @property
    def attachments_names(self) -> System.Collections.Generic.IList`1[[System.String]]:
        '''Gets attachments names'''
        raise NotImplementedError()
    

class Enumeration:
    '''Generic enumeration class.'''
    
    def equals(self, other : groupdocs.conversion.contracts.Enumeration) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def compare_to(self, obj : Any) -> int:
        '''Compares current object to other.
        
        :param obj: The other object
        :returns: zero if equal'''
        raise NotImplementedError()
    

class EpsDocumentInfo(ImageDocumentInfo):
    '''Contains Ps document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def bits_per_pixel(self) -> int:
        '''Gets bits per pixel'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''Gets height'''
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''Gets width'''
        raise NotImplementedError()
    

class EpubDocumentInfo(PdfDocumentInfo):
    '''Contains Epub document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def version(self) -> str:
        '''Gets version'''
        raise NotImplementedError()
    
    @property
    def title(self) -> str:
        '''Gets title'''
        raise NotImplementedError()
    
    @property
    def author(self) -> str:
        '''Gets author'''
        raise NotImplementedError()
    
    @property
    def is_password_protected(self) -> bool:
        '''Gets is document password protected'''
        raise NotImplementedError()
    
    @property
    def is_landscape(self) -> bool:
        '''Gets is page landscaped'''
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        '''Gets page height'''
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        '''Gets page width'''
        raise NotImplementedError()
    
    @property
    def table_of_contents(self) -> System.Collections.Generic.IList`1[[GroupDocs.Conversion.Contracts.TableOfContentsItem]]:
        '''Table of contents'''
        raise NotImplementedError()
    

class FontSubstitute(ValueObject):
    '''Describes substitution for missing font.'''
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @staticmethod
    def create(original_font : str, substitute_with : str) -> groupdocs.conversion.contracts.FontSubstitute:
        '''Instantiate new font substitution pair.
        
        :param original_font: Font from the source document.
        :param substitute_with: Font which will be used to replace "originalFont.'''
        raise NotImplementedError()
    
    @property
    def original_font_name(self) -> str:
        '''The original font name.'''
        raise NotImplementedError()
    
    @property
    def substitute_font_name(self) -> str:
        '''The substitute font name.'''
        raise NotImplementedError()
    

class GisDocumentInfo(DocumentInfo):
    '''Contains GIS document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class GzipDocumentInfo(DocumentInfo):
    '''Contains Gzip document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class HeicDocumentInfo(ImageDocumentInfo):
    '''Contains Heic document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def bits_per_pixel(self) -> int:
        '''Gets bits per pixel'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''Gets height'''
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''Gets width'''
        raise NotImplementedError()
    

class IDocumentInfo:
    '''Contains metadata for a document.'''
    
    @property
    def pages_count(self) -> int:
        '''Document pages count.'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Document format'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Document size in bytes'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Document creation date'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Enumerable of all properties which could be get for the current document info'''
        raise NotImplementedError()
    

class IDocumentsContainerLoadOptions:
    '''Loading options for documents container'''
    
    @property
    def convert_owner(self) -> bool:
        '''Option to control whether the documents container itself must be converted
        If this property is true the documents container will be the first converted document'''
        raise NotImplementedError()
    
    @property
    def convert_owned(self) -> bool:
        '''Option to control whether the owned documents in the documents container must be converted'''
        raise NotImplementedError()
    
    @property
    def depth(self) -> int:
        '''Option to control how many levels in depth to perform conversion'''
        raise NotImplementedError()
    

class IcoDocumentInfo(ImageDocumentInfo):
    '''Contains Ico document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def bits_per_pixel(self) -> int:
        '''Gets bits per pixel'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''Gets height'''
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''Gets width'''
        raise NotImplementedError()
    

class ImageDocumentInfo(DocumentInfo):
    '''Contains Image document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def bits_per_pixel(self) -> int:
        '''Gets bits per pixel'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''Gets height'''
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''Gets width'''
        raise NotImplementedError()
    

class InlineXbrlDocumentInfo(DocumentInfo):
    '''Contains iXbrl document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class IsoDocumentInfo(DocumentInfo):
    '''Contains ISO document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class JsonDocumentInfo(DocumentInfo):
    '''Contains Json document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class LzipDocumentInfo(DocumentInfo):
    '''Contains Lzip document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class LzmaDocumentInfo(DocumentInfo):
    '''Contains Lzma document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class NoteDocumentInfo(DocumentInfo):
    '''Contains Note document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def title(self) -> str:
        '''Gets title'''
        raise NotImplementedError()
    

class OlmDocumentInfo(DocumentInfo):
    '''Contains personal storage document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def folders(self) -> System.Collections.Generic.IList`1[[GroupDocs.Conversion.Contracts.OlmFolderInfo]]:
        '''Folders in the storage'''
        raise NotImplementedError()
    

class OlmFolderInfo(ValueObject):
    '''Personal Storage Folder info'''
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Name of the folder'''
        raise NotImplementedError()
    
    @property
    def items_count(self) -> int:
        '''Count of the items in the folder'''
        raise NotImplementedError()
    

class PasswordProtectedDocumentInfo(DocumentInfo):
    '''Provided document is password protected'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def is_password_protected(self) -> bool:
        '''Gets is document password protected'''
        raise NotImplementedError()
    

class PclDocumentInfo(DocumentInfo):
    '''Contains Pcl document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class PdfDocumentInfo(DocumentInfo):
    '''Contains Pdf document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def version(self) -> str:
        '''Gets version'''
        raise NotImplementedError()
    
    @property
    def title(self) -> str:
        '''Gets title'''
        raise NotImplementedError()
    
    @property
    def author(self) -> str:
        '''Gets author'''
        raise NotImplementedError()
    
    @property
    def is_password_protected(self) -> bool:
        '''Gets is document password protected'''
        raise NotImplementedError()
    
    @property
    def is_landscape(self) -> bool:
        '''Gets is page landscaped'''
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        '''Gets page height'''
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        '''Gets page width'''
        raise NotImplementedError()
    
    @property
    def table_of_contents(self) -> System.Collections.Generic.IList`1[[GroupDocs.Conversion.Contracts.TableOfContentsItem]]:
        '''Table of contents'''
        raise NotImplementedError()
    

class PersonalStorageDocumentInfo(DocumentInfo):
    '''Contains personal storage document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def is_password_protected(self) -> bool:
        '''Is storage password protected'''
        raise NotImplementedError()
    
    @property
    def root_folder_name(self) -> str:
        '''Root folder name'''
        raise NotImplementedError()
    
    @property
    def content_count(self) -> int:
        '''Get count of contents in the root folder'''
        raise NotImplementedError()
    
    @property
    def folders(self) -> System.Collections.Generic.IList`1[[GroupDocs.Conversion.Contracts.PersonalStorageFolderInfo]]:
        '''Folders in the storage'''
        raise NotImplementedError()
    

class PersonalStorageFolderInfo(ValueObject):
    '''Personal Storage Folder info'''
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Name of the folder'''
        raise NotImplementedError()
    
    @property
    def items_count(self) -> int:
        '''Count of the items in the folder'''
        raise NotImplementedError()
    
    @property
    def sub_folders(self) -> System.Collections.Generic.IList`1[[GroupDocs.Conversion.Contracts.PersonalStorageFolderInfo]]:
        '''Sub Folders'''
        raise NotImplementedError()
    
    @property
    def items(self) -> System.Collections.Generic.IList`1[[GroupDocs.Conversion.Contracts.PersonalStorageItemInfo]]:
        '''Items in the folder'''
        raise NotImplementedError()
    

class PersonalStorageItemInfo(ValueObject):
    '''Personal Storage Item info'''
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @property
    def title(self) -> str:
        '''Item Title'''
        raise NotImplementedError()
    
    @property
    def from_address(self) -> str:
        '''Item From'''
        raise NotImplementedError()
    
    @property
    def to(self) -> str:
        '''Item To'''
        raise NotImplementedError()
    
    @property
    def cc(self) -> str:
        '''Item Cc'''
        raise NotImplementedError()
    
    @property
    def bcc(self) -> str:
        '''Item Bcc'''
        raise NotImplementedError()
    
    @property
    def subject(self) -> str:
        '''Item Subject'''
        raise NotImplementedError()
    
    @property
    def sent(self) -> System.Nullable`1[[System.DateTime]]:
        '''Item Sent DateTime'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Item Size'''
        raise NotImplementedError()
    
    @property
    def attachments_count(self) -> int:
        '''Item Attachments Count'''
        raise NotImplementedError()
    

class PossibleConversions(ValueObject):
    '''Represents a mapping what conversion pairs
    are supported for specific source file format'''
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @property
    def source(self) -> groupdocs.conversion.filetypes.FileType:
        '''Source file formats'''
        raise NotImplementedError()
    
    @property
    def load_options(self) -> groupdocs.conversion.options.load.LoadOptions:
        '''Predefined load options which could be used to convert from current type'''
        raise NotImplementedError()
    
    @property
    def all(self) -> System.Collections.Generic.IEnumerable`1[[GroupDocs.Conversion.Contracts.TargetConversion]]:
        '''All target file types and primary/secondary flag'''
        raise NotImplementedError()
    
    @property
    def primary(self) -> System.Collections.Generic.IEnumerable`1[[GroupDocs.Conversion.FileTypes.FileType]]:
        '''Primary target file types'''
        raise NotImplementedError()
    
    @property
    def secondary(self) -> System.Collections.Generic.IEnumerable`1[[GroupDocs.Conversion.FileTypes.FileType]]:
        '''Secondary target file types'''
        raise NotImplementedError()
    

class PresentationDocumentInfo(DocumentInfo):
    '''Contains Presentation document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def title(self) -> str:
        '''Gets title'''
        raise NotImplementedError()
    
    @property
    def author(self) -> str:
        '''Gets author'''
        raise NotImplementedError()
    
    @property
    def is_password_protected(self) -> bool:
        '''Gets is the document password protected'''
        raise NotImplementedError()
    

class ProjectManagementDocumentInfo(DocumentInfo):
    '''Contains ProjectManagement document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def tasks_count(self) -> int:
        '''Tasks count'''
        raise NotImplementedError()
    
    @property
    def start_date(self) -> datetime:
        '''Project start date'''
        raise NotImplementedError()
    
    @property
    def end_date(self) -> datetime:
        '''Project end date'''
        raise NotImplementedError()
    

class PsDocumentInfo(DocumentInfo):
    '''Contains Ps document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class PsdDocumentInfo(DocumentInfo):
    '''Contains Psd document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def bits_per_pixel(self) -> int:
        '''Gets bits per pixel'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''Gets height'''
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''Gets width'''
        raise NotImplementedError()
    

class PublisherDocumentInfo(DocumentInfo):
    '''Contains Publisher document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class RarDocumentInfo(DocumentInfo):
    '''Contains Rar document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class SevenZipDocumentInfo(DocumentInfo):
    '''Contains 7Zip document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class SpreadsheetDocumentInfo(DocumentInfo):
    '''Contains Spreadsheet document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def title(self) -> str:
        '''Gets title'''
        raise NotImplementedError()
    
    @property
    def worksheets(self) -> List[str]:
        '''Worksheets names'''
        raise NotImplementedError()
    
    @property
    def worksheets_count(self) -> int:
        '''Gets worksheets count'''
        raise NotImplementedError()
    
    @property
    def author(self) -> str:
        '''Gets author'''
        raise NotImplementedError()
    
    @property
    def is_password_protected(self) -> bool:
        '''Gets is document password protected'''
        raise NotImplementedError()
    

class SvgDocumentInfo(DocumentInfo):
    '''Contains Svg document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class TableOfContentsItem:
    '''Contains Table of contents item metadata'''
    
    @property
    def title(self) -> str:
        '''Bookmark title'''
        raise NotImplementedError()
    
    @property
    def page(self) -> int:
        '''Bookmark page'''
        raise NotImplementedError()
    

class TarDocumentInfo(DocumentInfo):
    '''Contains Tar document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class TargetConversion:
    '''Represents possible target conversion and a flag is it a primary or secondary'''
    
    @property
    def format(self) -> groupdocs.conversion.filetypes.FileType:
        '''Target document format'''
        raise NotImplementedError()
    
    @property
    def is_primary(self) -> bool:
        '''Is the conversion primary'''
        raise NotImplementedError()
    
    @property
    def convert_options(self) -> groupdocs.conversion.options.convert.ConvertOptions:
        '''Predefined convert options which could be used to convert to current type'''
        raise NotImplementedError()
    

class TexDocumentInfo(DocumentInfo):
    '''Contains Tex document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class ThreeDDocumentInfo(DocumentInfo):
    '''Contains 3D document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class TsvDocumentInfo(SpreadsheetDocumentInfo):
    '''Contains Tsv document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def title(self) -> str:
        '''Gets title'''
        raise NotImplementedError()
    
    @property
    def worksheets(self) -> List[str]:
        '''Worksheets names'''
        raise NotImplementedError()
    
    @property
    def worksheets_count(self) -> int:
        '''Gets worksheets count'''
        raise NotImplementedError()
    
    @property
    def author(self) -> str:
        '''Gets author'''
        raise NotImplementedError()
    
    @property
    def is_password_protected(self) -> bool:
        '''Gets is document password protected'''
        raise NotImplementedError()
    

class TxtDocumentInfo(WordProcessingDocumentInfo):
    '''Contains Txt document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def words(self) -> int:
        '''Gets words count'''
        raise NotImplementedError()
    
    @property
    def lines(self) -> int:
        '''Gets lines count'''
        raise NotImplementedError()
    
    @property
    def title(self) -> str:
        '''Gets title'''
        raise NotImplementedError()
    
    @property
    def author(self) -> str:
        '''Gets author'''
        raise NotImplementedError()
    
    @property
    def is_password_protected(self) -> bool:
        '''Gets is document password protected'''
        raise NotImplementedError()
    
    @property
    def table_of_contents(self) -> System.Collections.Generic.IList`1[[GroupDocs.Conversion.Contracts.TableOfContentsItem]]:
        '''Table of contents'''
        raise NotImplementedError()
    

class UueDocumentInfo(DocumentInfo):
    '''Contains Uue document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class ValueObject:
    '''Abstract value object class.'''
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    

class VcfDocumentInfo(DocumentInfo):
    '''Contains Vcf document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def contacts_count(self) -> int:
        '''Contacts count'''
        raise NotImplementedError()
    

class WebDocumentInfo(DocumentInfo):
    '''Contains Web document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def encoding(self) -> str:
        '''Detected document encoding'''
        raise NotImplementedError()
    

class WordProcessingDocumentInfo(DocumentInfo):
    '''Contains WordProcessing document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def words(self) -> int:
        '''Gets words count'''
        raise NotImplementedError()
    
    @property
    def lines(self) -> int:
        '''Gets lines count'''
        raise NotImplementedError()
    
    @property
    def title(self) -> str:
        '''Gets title'''
        raise NotImplementedError()
    
    @property
    def author(self) -> str:
        '''Gets author'''
        raise NotImplementedError()
    
    @property
    def is_password_protected(self) -> bool:
        '''Gets is document password protected'''
        raise NotImplementedError()
    
    @property
    def table_of_contents(self) -> System.Collections.Generic.IList`1[[GroupDocs.Conversion.Contracts.TableOfContentsItem]]:
        '''Table of contents'''
        raise NotImplementedError()
    

class XbrlDocumentInfo(DocumentInfo):
    '''Contains Xbrl document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class XmlDocumentInfo(DocumentInfo):
    '''Contains Xml document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class XpsDocumentInfo(PdfDocumentInfo):
    '''Contains Xps document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def version(self) -> str:
        '''Gets version'''
        raise NotImplementedError()
    
    @property
    def title(self) -> str:
        '''Gets title'''
        raise NotImplementedError()
    
    @property
    def author(self) -> str:
        '''Gets author'''
        raise NotImplementedError()
    
    @property
    def is_password_protected(self) -> bool:
        '''Gets is document password protected'''
        raise NotImplementedError()
    
    @property
    def is_landscape(self) -> bool:
        '''Gets is page landscaped'''
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        '''Gets page height'''
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        '''Gets page width'''
        raise NotImplementedError()
    
    @property
    def table_of_contents(self) -> System.Collections.Generic.IList`1[[GroupDocs.Conversion.Contracts.TableOfContentsItem]]:
        '''Table of contents'''
        raise NotImplementedError()
    

class XslFoDocumentInfo(PdfDocumentInfo):
    '''Contains XslFo document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    
    @property
    def version(self) -> str:
        '''Gets version'''
        raise NotImplementedError()
    
    @property
    def title(self) -> str:
        '''Gets title'''
        raise NotImplementedError()
    
    @property
    def author(self) -> str:
        '''Gets author'''
        raise NotImplementedError()
    
    @property
    def is_password_protected(self) -> bool:
        '''Gets is document password protected'''
        raise NotImplementedError()
    
    @property
    def is_landscape(self) -> bool:
        '''Gets is page landscaped'''
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        '''Gets page height'''
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        '''Gets page width'''
        raise NotImplementedError()
    
    @property
    def table_of_contents(self) -> System.Collections.Generic.IList`1[[GroupDocs.Conversion.Contracts.TableOfContentsItem]]:
        '''Table of contents'''
        raise NotImplementedError()
    

class XzDocumentInfo(DocumentInfo):
    '''Contains Xz document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class ZDocumentInfo(DocumentInfo):
    '''Contains Z document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class ZipDocumentInfo(DocumentInfo):
    '''Contains compression document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

class ZstDocumentInfo(DocumentInfo):
    '''Contains Zst document metadata'''
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.pages_count`'''
        raise NotImplementedError()
    
    @property
    def format(self) -> str:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.format`'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.size`'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> datetime:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.creation_date`'''
        raise NotImplementedError()
    
    @property
    def property_names(self) -> List[str]:
        '''Implements :py:attr:`groupdocs.conversion.contracts.IDocumentInfo.property_names`'''
        raise NotImplementedError()
    

