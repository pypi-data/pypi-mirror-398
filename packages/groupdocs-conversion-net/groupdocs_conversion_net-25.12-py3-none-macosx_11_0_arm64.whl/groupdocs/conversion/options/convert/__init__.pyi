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

class CadConvertOptions(ConvertOptions):
    '''Options for conversion to Cad type.'''
    
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.options.convert.CadConvertOptions` class.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def clone(self) -> Any:
        '''Clones current options instance.'''
        raise NotImplementedError()
    
    @property
    def format(self) -> groupdocs.conversion.filetypes.FileType:
        '''Overrides the Format property to ensure it is of type CadFileType.'''
        raise NotImplementedError()
    
    @format.setter
    def format(self, value : groupdocs.conversion.filetypes.FileType) -> None:
        '''Overrides the Format property to ensure it is of type CadFileType.'''
        raise NotImplementedError()
    
    @property
    def page_number(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @page_number.setter
    def page_number(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    
    @pages_count.setter
    def pages_count(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    
    @property
    def page_size(self) -> groupdocs.conversion.options.convert.PageSize:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_size`'''
        raise NotImplementedError()
    
    @page_size.setter
    def page_size(self, value : groupdocs.conversion.options.convert.PageSize) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_size`'''
        raise NotImplementedError()
    
    @property
    def page_width(self) -> float:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_width`'''
        raise NotImplementedError()
    
    @page_width.setter
    def page_width(self, value : float) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_width`'''
        raise NotImplementedError()
    
    @property
    def page_height(self) -> float:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_height`'''
        raise NotImplementedError()
    
    @page_height.setter
    def page_height(self, value : float) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_height`'''
        raise NotImplementedError()
    

class CommonConvertOptions(ConvertOptions):
    '''Abstract generic common conversion options class.'''
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def clone(self) -> Any:
        '''Clones current options instance.'''
        raise NotImplementedError()
    
    @property
    def format(self) -> groupdocs.conversion.filetypes.FileType:
        '''Overrides the Format property to ensure it is of type FileType.'''
        raise NotImplementedError()
    
    @format.setter
    def format(self, value : groupdocs.conversion.filetypes.FileType) -> None:
        '''Overrides the Format property to ensure it is of type FileType.'''
        raise NotImplementedError()
    
    @property
    def watermark(self) -> groupdocs.conversion.options.convert.WatermarkOptions:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IWatermarkedConvertOptions.watermark`'''
        raise NotImplementedError()
    
    @watermark.setter
    def watermark(self, value : groupdocs.conversion.options.convert.WatermarkOptions) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IWatermarkedConvertOptions.watermark`'''
        raise NotImplementedError()
    
    @property
    def page_number(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @page_number.setter
    def page_number(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    
    @pages_count.setter
    def pages_count(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    
    @property
    def pages(self) -> System.Collections.Generic.List`1[[System.Int32]]:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageRangedConvertOptions.pages`'''
        raise NotImplementedError()
    
    @pages.setter
    def pages(self, value : System.Collections.Generic.List`1[[System.Int32]]) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageRangedConvertOptions.pages`'''
        raise NotImplementedError()
    

class CompressionConvertOptions(ConvertOptions):
    '''Options for conversion to Compression file type.'''
    
    def __init__(self) -> None:
        '''Create ConvertOptions instance.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def clone(self) -> Any:
        '''Clones current options instance.'''
        raise NotImplementedError()
    
    @property
    def format(self) -> groupdocs.conversion.filetypes.FileType:
        '''Overrides the Format property to ensure it is of type CompressionFileType.'''
        raise NotImplementedError()
    
    @format.setter
    def format(self, value : groupdocs.conversion.filetypes.FileType) -> None:
        '''Overrides the Format property to ensure it is of type CompressionFileType.'''
        raise NotImplementedError()
    
    @property
    def password(self) -> str:
        '''Set this property if you want to protect the converted document with a password.'''
        raise NotImplementedError()
    
    @password.setter
    def password(self, value : str) -> None:
        '''Set this property if you want to protect the converted document with a password.'''
        raise NotImplementedError()
    

class ConvertOptions(groupdocs.conversion.contracts.ValueObject):
    '''The general conversion options class.'''
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def clone(self) -> Any:
        '''Clones current options instance.'''
        raise NotImplementedError()
    
    @property
    def format(self) -> groupdocs.conversion.filetypes.FileType:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IConvertOptions.format`'''
        raise NotImplementedError()
    
    @format.setter
    def format(self, value : groupdocs.conversion.filetypes.FileType) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IConvertOptions.format`'''
        raise NotImplementedError()
    

class DiagramConvertOptions(CommonConvertOptions):
    '''Options for conversion to Diagram file type.'''
    
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.options.convert.DiagramConvertOptions` class.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def clone(self) -> Any:
        '''Clones current options instance.'''
        raise NotImplementedError()
    
    @property
    def format(self) -> groupdocs.conversion.filetypes.FileType:
        '''Overrides the Format property to ensure it is of type DiagramFileType.'''
        raise NotImplementedError()
    
    @format.setter
    def format(self, value : groupdocs.conversion.filetypes.FileType) -> None:
        '''Overrides the Format property to ensure it is of type DiagramFileType.'''
        raise NotImplementedError()
    
    @property
    def watermark(self) -> groupdocs.conversion.options.convert.WatermarkOptions:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IWatermarkedConvertOptions.watermark`'''
        raise NotImplementedError()
    
    @watermark.setter
    def watermark(self, value : groupdocs.conversion.options.convert.WatermarkOptions) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IWatermarkedConvertOptions.watermark`'''
        raise NotImplementedError()
    
    @property
    def page_number(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @page_number.setter
    def page_number(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    
    @pages_count.setter
    def pages_count(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    
    @property
    def pages(self) -> System.Collections.Generic.List`1[[System.Int32]]:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageRangedConvertOptions.pages`'''
        raise NotImplementedError()
    
    @pages.setter
    def pages(self, value : System.Collections.Generic.List`1[[System.Int32]]) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageRangedConvertOptions.pages`'''
        raise NotImplementedError()
    
    @property
    def auto_fit_page_to_drawing_content(self) -> bool:
        '''Defines whether need enlarge page to fit drawing content or not'''
        raise NotImplementedError()
    
    @auto_fit_page_to_drawing_content.setter
    def auto_fit_page_to_drawing_content(self, value : bool) -> None:
        '''Defines whether need enlarge page to fit drawing content or not'''
        raise NotImplementedError()
    

class EBookConvertOptions(CommonConvertOptions):
    '''Options for conversion to EBook file type.'''
    
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.options.convert.EBookConvertOptions` class.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def clone(self) -> Any:
        '''Clones current options instance.'''
        raise NotImplementedError()
    
    @property
    def format(self) -> groupdocs.conversion.filetypes.FileType:
        '''Overrides the Format property to ensure it is of type EBookFileType.'''
        raise NotImplementedError()
    
    @format.setter
    def format(self, value : groupdocs.conversion.filetypes.FileType) -> None:
        '''Overrides the Format property to ensure it is of type EBookFileType.'''
        raise NotImplementedError()
    
    @property
    def watermark(self) -> groupdocs.conversion.options.convert.WatermarkOptions:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IWatermarkedConvertOptions.watermark`'''
        raise NotImplementedError()
    
    @watermark.setter
    def watermark(self, value : groupdocs.conversion.options.convert.WatermarkOptions) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IWatermarkedConvertOptions.watermark`'''
        raise NotImplementedError()
    
    @property
    def page_number(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @page_number.setter
    def page_number(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    
    @pages_count.setter
    def pages_count(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    
    @property
    def pages(self) -> System.Collections.Generic.List`1[[System.Int32]]:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageRangedConvertOptions.pages`'''
        raise NotImplementedError()
    
    @pages.setter
    def pages(self, value : System.Collections.Generic.List`1[[System.Int32]]) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageRangedConvertOptions.pages`'''
        raise NotImplementedError()
    
    @property
    def page_size(self) -> groupdocs.conversion.options.convert.PageSize:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_size`'''
        raise NotImplementedError()
    
    @page_size.setter
    def page_size(self, value : groupdocs.conversion.options.convert.PageSize) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_size`'''
        raise NotImplementedError()
    
    @property
    def page_width(self) -> float:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_width`'''
        raise NotImplementedError()
    
    @page_width.setter
    def page_width(self, value : float) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_width`'''
        raise NotImplementedError()
    
    @property
    def page_height(self) -> float:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_height`'''
        raise NotImplementedError()
    
    @page_height.setter
    def page_height(self, value : float) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_height`'''
        raise NotImplementedError()
    
    @property
    def page_orientation(self) -> groupdocs.conversion.options.convert.PageOrientation:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageOrientationConvertOptions.page_orientation`'''
        raise NotImplementedError()
    
    @page_orientation.setter
    def page_orientation(self, value : groupdocs.conversion.options.convert.PageOrientation) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageOrientationConvertOptions.page_orientation`'''
        raise NotImplementedError()
    

class EmailConvertOptions(ConvertOptions):
    '''Options for conversion to Email file type.'''
    
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.options.convert.EmailConvertOptions` class.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def clone(self) -> Any:
        '''Clones current options instance.'''
        raise NotImplementedError()
    
    @property
    def format(self) -> groupdocs.conversion.filetypes.FileType:
        '''Overrides the Format property to ensure it is of type EmailFileType.'''
        raise NotImplementedError()
    
    @format.setter
    def format(self, value : groupdocs.conversion.filetypes.FileType) -> None:
        '''Overrides the Format property to ensure it is of type EmailFileType.'''
        raise NotImplementedError()
    

class FinanceConvertOptions(ConvertOptions):
    '''Options for conversion to finance type.'''
    
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.options.convert.FinanceConvertOptions` class.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def clone(self) -> Any:
        '''Clones current options instance.'''
        raise NotImplementedError()
    
    @property
    def format(self) -> groupdocs.conversion.filetypes.FileType:
        '''Overrides the Format property to ensure it is of type FinanceFileType.'''
        raise NotImplementedError()
    
    @format.setter
    def format(self, value : groupdocs.conversion.filetypes.FileType) -> None:
        '''Overrides the Format property to ensure it is of type FinanceFileType.'''
        raise NotImplementedError()
    
    @property
    def page_number(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @page_number.setter
    def page_number(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    
    @pages_count.setter
    def pages_count(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    

class Font(groupdocs.conversion.contracts.ValueObject):
    '''Font settings'''
    
    def __init__(self, font_family_name : str, size : float) -> None:
        '''creates new Font instance
        
        :param font_family_name: Font name
        :param size: Font size'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @property
    def family_name(self) -> str:
        '''Font family name'''
        raise NotImplementedError()
    
    @property
    def size(self) -> float:
        '''Font size'''
        raise NotImplementedError()
    
    @property
    def bold(self) -> bool:
        '''Font bold'''
        raise NotImplementedError()
    
    @bold.setter
    def bold(self, value : bool) -> None:
        '''Font bold'''
        raise NotImplementedError()
    
    @property
    def italic(self) -> bool:
        '''Font italic'''
        raise NotImplementedError()
    
    @italic.setter
    def italic(self, value : bool) -> None:
        '''Font italic'''
        raise NotImplementedError()
    
    @property
    def underline(self) -> bool:
        '''Font underline'''
        raise NotImplementedError()
    
    @underline.setter
    def underline(self, value : bool) -> None:
        '''Font underline'''
        raise NotImplementedError()
    

class FontConvertOptions(ConvertOptions):
    '''Options for conversion to Font type.'''
    
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.options.convert.FontConvertOptions` class.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def clone(self) -> Any:
        '''Clones current options instance.'''
        raise NotImplementedError()
    
    @property
    def format(self) -> groupdocs.conversion.filetypes.FileType:
        '''Overrides the Format property to ensure it is of type FontFileType.'''
        raise NotImplementedError()
    
    @format.setter
    def format(self, value : groupdocs.conversion.filetypes.FileType) -> None:
        '''Overrides the Format property to ensure it is of type FontFileType.'''
        raise NotImplementedError()
    

class GisConvertOptions(ConvertOptions):
    '''Options for conversion to GIS type.'''
    
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.options.convert.GisConvertOptions` class.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def clone(self) -> Any:
        '''Clones current options instance.'''
        raise NotImplementedError()
    
    @property
    def format(self) -> groupdocs.conversion.filetypes.FileType:
        '''Overrides the Format property to ensure it is of type GisFileType.'''
        raise NotImplementedError()
    
    @format.setter
    def format(self, value : groupdocs.conversion.filetypes.FileType) -> None:
        '''Overrides the Format property to ensure it is of type GisFileType.'''
        raise NotImplementedError()
    

class IConvertOptions:
    '''Represents convert options'''
    
    @property
    def format(self) -> groupdocs.conversion.filetypes.FileType:
        '''The desired file type the input document should be converted to.'''
        raise NotImplementedError()
    
    @format.setter
    def format(self, value : groupdocs.conversion.filetypes.FileType) -> None:
        '''The desired file type the input document should be converted to.'''
        raise NotImplementedError()
    

class IPageMarginConvertOptions:
    '''Represents convert options that support page margins'''
    
    @property
    def margin_top(self) -> System.Nullable`1[[System.Single]]:
        '''Desired page top margin in points after conversion.'''
        raise NotImplementedError()
    
    @margin_top.setter
    def margin_top(self, value : System.Nullable`1[[System.Single]]) -> None:
        '''Desired page top margin in points after conversion.'''
        raise NotImplementedError()
    
    @property
    def margin_bottom(self) -> System.Nullable`1[[System.Single]]:
        '''Desired page bottom margin in points after conversion.'''
        raise NotImplementedError()
    
    @margin_bottom.setter
    def margin_bottom(self, value : System.Nullable`1[[System.Single]]) -> None:
        '''Desired page bottom margin in points after conversion.'''
        raise NotImplementedError()
    
    @property
    def margin_left(self) -> System.Nullable`1[[System.Single]]:
        '''Desired page left margin in points after conversion.'''
        raise NotImplementedError()
    
    @margin_left.setter
    def margin_left(self, value : System.Nullable`1[[System.Single]]) -> None:
        '''Desired page left margin in points after conversion.'''
        raise NotImplementedError()
    
    @property
    def margin_right(self) -> System.Nullable`1[[System.Single]]:
        '''Desired page right margin in points after conversion.'''
        raise NotImplementedError()
    
    @margin_right.setter
    def margin_right(self, value : System.Nullable`1[[System.Single]]) -> None:
        '''Desired page right margin in points after conversion.'''
        raise NotImplementedError()
    

class IPageOrientationConvertOptions:
    '''Represents convert options that support page orientation'''
    
    @property
    def page_orientation(self) -> groupdocs.conversion.options.convert.PageOrientation:
        '''Desired page orientation after conversion'''
        raise NotImplementedError()
    
    @page_orientation.setter
    def page_orientation(self, value : groupdocs.conversion.options.convert.PageOrientation) -> None:
        '''Desired page orientation after conversion'''
        raise NotImplementedError()
    

class IPageRangedConvertOptions:
    '''Represents convert options that support conversion of specific list of pages'''
    
    @property
    def pages(self) -> System.Collections.Generic.List`1[[System.Int32]]:
        '''The list of page indexes to be converted. Should be specified to convert specific pages.'''
        raise NotImplementedError()
    
    @pages.setter
    def pages(self, value : System.Collections.Generic.List`1[[System.Int32]]) -> None:
        '''The list of page indexes to be converted. Should be specified to convert specific pages.'''
        raise NotImplementedError()
    

class IPageSizeConvertOptions:
    '''Represents convert options that support page size'''
    
    @property
    def page_size(self) -> groupdocs.conversion.options.convert.PageSize:
        '''Desired page size after conversion'''
        raise NotImplementedError()
    
    @page_size.setter
    def page_size(self, value : groupdocs.conversion.options.convert.PageSize) -> None:
        '''Desired page size after conversion'''
        raise NotImplementedError()
    
    @property
    def page_width(self) -> float:
        '''Specified page width in points if :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_size` is set to PageSize.Custom'''
        raise NotImplementedError()
    
    @page_width.setter
    def page_width(self, value : float) -> None:
        '''Specified page width in points if :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_size` is set to PageSize.Custom'''
        raise NotImplementedError()
    
    @property
    def page_height(self) -> float:
        '''Specified page height in points if :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_size` is set to PageSize.Custom'''
        raise NotImplementedError()
    
    @page_height.setter
    def page_height(self, value : float) -> None:
        '''Specified page height in points if :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_size` is set to PageSize.Custom'''
        raise NotImplementedError()
    

class IPagedConvertOptions:
    '''Represents convert options that allows conversion to perform page limitation by specifying start page and pages count'''
    
    @property
    def page_number(self) -> int:
        '''The page number to start conversion from.'''
        raise NotImplementedError()
    
    @page_number.setter
    def page_number(self, value : int) -> None:
        '''The page number to start conversion from.'''
        raise NotImplementedError()
    
    @property
    def pages_count(self) -> int:
        '''Number of pages to convert starting from ``PageNumber``.'''
        raise NotImplementedError()
    
    @pages_count.setter
    def pages_count(self, value : int) -> None:
        '''Number of pages to convert starting from ``PageNumber``.'''
        raise NotImplementedError()
    

class IPdfRecognitionModeOptions:
    '''Represents convert options that control recognition mode when converting from PDF'''
    
    @property
    def pdf_recognition_mode(self) -> groupdocs.conversion.options.convert.PdfRecognitionMode:
        '''Recognition mode when converting from pdf'''
        raise NotImplementedError()
    
    @pdf_recognition_mode.setter
    def pdf_recognition_mode(self, value : groupdocs.conversion.options.convert.PdfRecognitionMode) -> None:
        '''Recognition mode when converting from pdf'''
        raise NotImplementedError()
    

class IWatermarkedConvertOptions:
    '''Represents convert options that allow output of conversion to be watermarked'''
    
    @property
    def watermark(self) -> groupdocs.conversion.options.convert.WatermarkOptions:
        '''Watermark specific options'''
        raise NotImplementedError()
    
    @watermark.setter
    def watermark(self, value : groupdocs.conversion.options.convert.WatermarkOptions) -> None:
        '''Watermark specific options'''
        raise NotImplementedError()
    

class ImageConvertOptions(CommonConvertOptions):
    '''Options for conversion to Image file type.'''
    
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.options.convert.ImageConvertOptions` class.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def clone(self) -> Any:
        '''Clones current options instance.'''
        raise NotImplementedError()
    
    @property
    def format(self) -> groupdocs.conversion.filetypes.FileType:
        '''Overrides the Format property to ensure it is of type ImageFileType.'''
        raise NotImplementedError()
    
    @format.setter
    def format(self, value : groupdocs.conversion.filetypes.FileType) -> None:
        '''Overrides the Format property to ensure it is of type ImageFileType.'''
        raise NotImplementedError()
    
    @property
    def watermark(self) -> groupdocs.conversion.options.convert.WatermarkOptions:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IWatermarkedConvertOptions.watermark`'''
        raise NotImplementedError()
    
    @watermark.setter
    def watermark(self, value : groupdocs.conversion.options.convert.WatermarkOptions) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IWatermarkedConvertOptions.watermark`'''
        raise NotImplementedError()
    
    @property
    def page_number(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @page_number.setter
    def page_number(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    
    @pages_count.setter
    def pages_count(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    
    @property
    def pages(self) -> System.Collections.Generic.List`1[[System.Int32]]:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageRangedConvertOptions.pages`'''
        raise NotImplementedError()
    
    @pages.setter
    def pages(self, value : System.Collections.Generic.List`1[[System.Int32]]) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageRangedConvertOptions.pages`'''
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''Desired image width after conversion.'''
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : int) -> None:
        '''Desired image width after conversion.'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''Desired image height after conversion.'''
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : int) -> None:
        '''Desired image height after conversion.'''
        raise NotImplementedError()
    
    @property
    def use_pdf(self) -> bool:
        '''If ``true``, the input firstly is converted to PDF and after that to desired format.'''
        raise NotImplementedError()
    
    @use_pdf.setter
    def use_pdf(self, value : bool) -> None:
        '''If ``true``, the input firstly is converted to PDF and after that to desired format.'''
        raise NotImplementedError()
    
    @property
    def horizontal_resolution(self) -> int:
        '''Desired image horizontal resolution after conversion. The default resolution is the resolution of the input file or 96 dpi.'''
        raise NotImplementedError()
    
    @horizontal_resolution.setter
    def horizontal_resolution(self, value : int) -> None:
        '''Desired image horizontal resolution after conversion. The default resolution is the resolution of the input file or 96 dpi.'''
        raise NotImplementedError()
    
    @property
    def vertical_resolution(self) -> int:
        '''Desired image vertical resolution after conversion. The default resolution is the resolution of the input file or 96 dpi.'''
        raise NotImplementedError()
    
    @vertical_resolution.setter
    def vertical_resolution(self, value : int) -> None:
        '''Desired image vertical resolution after conversion. The default resolution is the resolution of the input file or 96 dpi.'''
        raise NotImplementedError()
    
    @property
    def tiff_options(self) -> groupdocs.conversion.options.convert.TiffOptions:
        '''Tiff specific convert options.'''
        raise NotImplementedError()
    
    @tiff_options.setter
    def tiff_options(self, value : groupdocs.conversion.options.convert.TiffOptions) -> None:
        '''Tiff specific convert options.'''
        raise NotImplementedError()
    
    @property
    def psd_options(self) -> groupdocs.conversion.options.convert.PsdOptions:
        '''Psd specific convert options.'''
        raise NotImplementedError()
    
    @psd_options.setter
    def psd_options(self, value : groupdocs.conversion.options.convert.PsdOptions) -> None:
        '''Psd specific convert options.'''
        raise NotImplementedError()
    
    @property
    def webp_options(self) -> groupdocs.conversion.options.convert.WebpOptions:
        '''Webp specific convert options.'''
        raise NotImplementedError()
    
    @webp_options.setter
    def webp_options(self, value : groupdocs.conversion.options.convert.WebpOptions) -> None:
        '''Webp specific convert options.'''
        raise NotImplementedError()
    
    @property
    def grayscale(self) -> bool:
        '''Indicates whether to convert into grayscale image.'''
        raise NotImplementedError()
    
    @grayscale.setter
    def grayscale(self, value : bool) -> None:
        '''Indicates whether to convert into grayscale image.'''
        raise NotImplementedError()
    
    @property
    def rotate_angle(self) -> int:
        '''Image rotation angle.'''
        raise NotImplementedError()
    
    @rotate_angle.setter
    def rotate_angle(self, value : int) -> None:
        '''Image rotation angle.'''
        raise NotImplementedError()
    
    @property
    def jpeg_options(self) -> groupdocs.conversion.options.convert.JpegOptions:
        '''Jpeg specific convert options.'''
        raise NotImplementedError()
    
    @jpeg_options.setter
    def jpeg_options(self, value : groupdocs.conversion.options.convert.JpegOptions) -> None:
        '''Jpeg specific convert options.'''
        raise NotImplementedError()
    
    @property
    def flip_mode(self) -> groupdocs.conversion.options.convert.ImageFlipModes:
        '''Image flip mode.'''
        raise NotImplementedError()
    
    @flip_mode.setter
    def flip_mode(self, value : groupdocs.conversion.options.convert.ImageFlipModes) -> None:
        '''Image flip mode.'''
        raise NotImplementedError()
    
    @property
    def brightness(self) -> int:
        '''Adjusts image brightness.'''
        raise NotImplementedError()
    
    @brightness.setter
    def brightness(self, value : int) -> None:
        '''Adjusts image brightness.'''
        raise NotImplementedError()
    
    @property
    def contrast(self) -> int:
        '''Adjusts image contrast.'''
        raise NotImplementedError()
    
    @contrast.setter
    def contrast(self, value : int) -> None:
        '''Adjusts image contrast.'''
        raise NotImplementedError()
    
    @property
    def gamma(self) -> float:
        '''Adjusts image gamma.'''
        raise NotImplementedError()
    
    @gamma.setter
    def gamma(self, value : float) -> None:
        '''Adjusts image gamma.'''
        raise NotImplementedError()
    
    @property
    def background_color(self) -> aspose.pydrawing.Color:
        '''Sets background color where supported by the source format'''
        raise NotImplementedError()
    
    @background_color.setter
    def background_color(self, value : aspose.pydrawing.Color) -> None:
        '''Sets background color where supported by the source format'''
        raise NotImplementedError()
    

class ImageFlipModes(groupdocs.conversion.contracts.Enumeration):
    '''Describes image flip modes.'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
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
    
    @staticmethod
    def get_all() -> System.Collections.Generic.IEnumerable`1[[GroupDocs.Conversion.Options.Convert.ImageFlipModes]]:
        '''Returns all enumeration values.
        
        :returns: Enumerable of the provided type'''
        raise NotImplementedError()
    
    @property
    def NONE(self) -> groupdocs.conversion.options.convert.ImageFlipModes:
        '''No flipping.'''
        raise NotImplementedError()

    @property
    def FLIP_X(self) -> groupdocs.conversion.options.convert.ImageFlipModes:
        '''Horizontal flip.'''
        raise NotImplementedError()

    @property
    def FLIP_Y(self) -> groupdocs.conversion.options.convert.ImageFlipModes:
        '''Flip vertical.'''
        raise NotImplementedError()

    @property
    def FLIP_XY(self) -> groupdocs.conversion.options.convert.ImageFlipModes:
        '''Flip horizontal and vertical.'''
        raise NotImplementedError()


class JpegOptions(groupdocs.conversion.contracts.ValueObject):
    '''Options for conversion to Jpeg file type.'''
    
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.options.convert.JpegOptions` class.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @property
    def quality(self) -> int:
        '''Desired image quality. The value must be between 0 and 100. The default value is 100.'''
        raise NotImplementedError()
    
    @quality.setter
    def quality(self, value : int) -> None:
        '''Desired image quality. The value must be between 0 and 100. The default value is 100.'''
        raise NotImplementedError()
    
    @property
    def color_mode(self) -> groupdocs.conversion.options.convert.JpgColorModes:
        '''Jpg color mode.'''
        raise NotImplementedError()
    
    @color_mode.setter
    def color_mode(self, value : groupdocs.conversion.options.convert.JpgColorModes) -> None:
        '''Jpg color mode.'''
        raise NotImplementedError()
    
    @property
    def compression(self) -> groupdocs.conversion.options.convert.JpgCompressionMethods:
        '''Jpg compression method.'''
        raise NotImplementedError()
    
    @compression.setter
    def compression(self, value : groupdocs.conversion.options.convert.JpgCompressionMethods) -> None:
        '''Jpg compression method.'''
        raise NotImplementedError()
    

class JpgColorModes(groupdocs.conversion.contracts.Enumeration):
    '''Describes Jpg color modes enumeration.'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
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
    
    @staticmethod
    def get_all() -> System.Collections.Generic.IEnumerable`1[[GroupDocs.Conversion.Options.Convert.JpgColorModes]]:
        '''Returns all enumeration values.
        
        :returns: Enumerable of the provided type'''
        raise NotImplementedError()
    
    @property
    def Y_CB_CR(self) -> groupdocs.conversion.options.convert.JpgColorModes:
        '''YCbCr image. Standard option for jpeg images.'''
        raise NotImplementedError()

    @property
    def RGB(self) -> groupdocs.conversion.options.convert.JpgColorModes:
        '''RGB.'''
        raise NotImplementedError()

    @property
    def CMYK(self) -> groupdocs.conversion.options.convert.JpgColorModes:
        '''CMYK.'''
        raise NotImplementedError()

    @property
    def YCCK(self) -> groupdocs.conversion.options.convert.JpgColorModes:
        '''Ycck.'''
        raise NotImplementedError()

    @property
    def GRAYSCALE(self) -> groupdocs.conversion.options.convert.JpgColorModes:
        '''Grayscale.'''
        raise NotImplementedError()


class JpgCompressionMethods(groupdocs.conversion.contracts.Enumeration):
    '''Describes Jpg compression modes'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
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
    
    @staticmethod
    def get_all() -> System.Collections.Generic.IEnumerable`1[[GroupDocs.Conversion.Options.Convert.JpgCompressionMethods]]:
        '''Returns all enumeration values.
        
        :returns: Enumerable of the provided type'''
        raise NotImplementedError()
    
    @property
    def BASELINE(self) -> groupdocs.conversion.options.convert.JpgCompressionMethods:
        '''The baseline compression.'''
        raise NotImplementedError()

    @property
    def PROGRESSIVE(self) -> groupdocs.conversion.options.convert.JpgCompressionMethods:
        '''Progressive compression.'''
        raise NotImplementedError()

    @property
    def LOSSLESS(self) -> groupdocs.conversion.options.convert.JpgCompressionMethods:
        '''Lossless compression.'''
        raise NotImplementedError()

    @property
    def JPEG_LS(self) -> groupdocs.conversion.options.convert.JpgCompressionMethods:
        '''JpegLs compression.'''
        raise NotImplementedError()


class MarkdownOptions(groupdocs.conversion.contracts.ValueObject):
    '''Options for conversion to markdown file type.'''
    
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.options.convert.MarkdownOptions` class.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @property
    def export_images_as_base64(self) -> bool:
        '''Export images as base64. Default is true.'''
        raise NotImplementedError()
    
    @export_images_as_base64.setter
    def export_images_as_base64(self, value : bool) -> None:
        '''Export images as base64. Default is true.'''
        raise NotImplementedError()
    

class NoConvertOptions(ConvertOptions):
    '''Special convert option class, which instructs converter to copy source document without any processing'''
    
    def __init__(self) -> None:
        '''ctor'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def clone(self) -> Any:
        '''Clones current options instance.'''
        raise NotImplementedError()
    
    @property
    def format(self) -> groupdocs.conversion.filetypes.FileType:
        '''Overrides the Format property to ensure it is of type FileType.'''
        raise NotImplementedError()
    
    @format.setter
    def format(self, value : groupdocs.conversion.filetypes.FileType) -> None:
        '''Overrides the Format property to ensure it is of type FileType.'''
        raise NotImplementedError()
    

class PageDescriptionLanguageConvertOptions(CommonConvertOptions):
    '''Options for conversion to page descriptions language file type.'''
    
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.filetypes.PageDescriptionLanguageFileType` class.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def clone(self) -> Any:
        '''Clones current options instance.'''
        raise NotImplementedError()
    
    @property
    def format(self) -> groupdocs.conversion.filetypes.FileType:
        '''Overrides the Format property to ensure it is of type PageDescriptionLanguageFileType.'''
        raise NotImplementedError()
    
    @format.setter
    def format(self, value : groupdocs.conversion.filetypes.FileType) -> None:
        '''Overrides the Format property to ensure it is of type PageDescriptionLanguageFileType.'''
        raise NotImplementedError()
    
    @property
    def watermark(self) -> groupdocs.conversion.options.convert.WatermarkOptions:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IWatermarkedConvertOptions.watermark`'''
        raise NotImplementedError()
    
    @watermark.setter
    def watermark(self, value : groupdocs.conversion.options.convert.WatermarkOptions) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IWatermarkedConvertOptions.watermark`'''
        raise NotImplementedError()
    
    @property
    def page_number(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @page_number.setter
    def page_number(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    
    @pages_count.setter
    def pages_count(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    
    @property
    def pages(self) -> System.Collections.Generic.List`1[[System.Int32]]:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageRangedConvertOptions.pages`'''
        raise NotImplementedError()
    
    @pages.setter
    def pages(self, value : System.Collections.Generic.List`1[[System.Int32]]) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageRangedConvertOptions.pages`'''
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''Desired page width after conversion.'''
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : int) -> None:
        '''Desired page width after conversion.'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''Desired page height after conversion.'''
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : int) -> None:
        '''Desired page height after conversion.'''
        raise NotImplementedError()
    

class PageOrientation(groupdocs.conversion.contracts.Enumeration):
    '''Specifies page orientation'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
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
    
    @staticmethod
    def set_default(value: groupdocs.conversion.options.convert.PageOrientation) -> None:
        '''Default page orientation e.g. as is in source document'''
    @property
    def default(self) -> groupdocs.conversion.options.convert.PageOrientation:
        '''Default page orientation e.g. as is in source document'''
        raise NotImplementedError()

    @staticmethod
    def set_landscape(value: groupdocs.conversion.options.convert.PageOrientation) -> None:
        '''Landscape page orientation (wide and short).'''
    @property
    def landscape(self) -> groupdocs.conversion.options.convert.PageOrientation:
        '''Landscape page orientation (wide and short).'''
        raise NotImplementedError()

    @staticmethod
    def set_portrait(value: groupdocs.conversion.options.convert.PageOrientation) -> None:
        '''Portrait page orientation (narrow and tall).'''
    @property
    def portrait(self) -> groupdocs.conversion.options.convert.PageOrientation:
        '''Portrait page orientation (narrow and tall).'''
        raise NotImplementedError()


class PageSize(groupdocs.conversion.contracts.Enumeration):
    '''Specifies page size'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
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
    
    @property
    def A3(self) -> groupdocs.conversion.options.convert.PageSize:
        '''297 x 420 mm.'''
        raise NotImplementedError()

    @property
    def A4(self) -> groupdocs.conversion.options.convert.PageSize:
        '''210 x 297 mm.'''
        raise NotImplementedError()

    @property
    def A5(self) -> groupdocs.conversion.options.convert.PageSize:
        '''148 x 210 mm.'''
        raise NotImplementedError()

    @property
    def B4(self) -> groupdocs.conversion.options.convert.PageSize:
        '''250 x 353 mm'''
        raise NotImplementedError()

    @property
    def B5(self) -> groupdocs.conversion.options.convert.PageSize:
        '''176 x 250 mm.'''
        raise NotImplementedError()

    @property
    def CUSTOM(self) -> groupdocs.conversion.options.convert.PageSize:
        '''Custom paper size.'''
        raise NotImplementedError()

    @property
    def ENVELOPE_DL(self) -> groupdocs.conversion.options.convert.PageSize:
        '''110 x 220 mm.'''
        raise NotImplementedError()

    @property
    def EXECUTIVE(self) -> groupdocs.conversion.options.convert.PageSize:
        '''7.25 x 10.5 inches.'''
        raise NotImplementedError()

    @property
    def FOLIO(self) -> groupdocs.conversion.options.convert.PageSize:
        '''8.5 x 13 inches.'''
        raise NotImplementedError()

    @property
    def LEDGER(self) -> groupdocs.conversion.options.convert.PageSize:
        '''17 x 11 inches.'''
        raise NotImplementedError()

    @property
    def LEGAL(self) -> groupdocs.conversion.options.convert.PageSize:
        '''8.5 x 14 inches.'''
        raise NotImplementedError()

    @property
    def LETTER(self) -> groupdocs.conversion.options.convert.PageSize:
        '''8.5 x 11 inches.'''
        raise NotImplementedError()

    @property
    def PAPER_10X14(self) -> groupdocs.conversion.options.convert.PageSize:
        '''10 x 14 inches.'''
        raise NotImplementedError()

    @property
    def PAPER_11X17(self) -> groupdocs.conversion.options.convert.PageSize:
        '''11 x 17 inches.'''
        raise NotImplementedError()

    @property
    def QUARTO(self) -> groupdocs.conversion.options.convert.PageSize:
        '''8.47 x 10.83 inches.'''
        raise NotImplementedError()

    @property
    def STATEMENT(self) -> groupdocs.conversion.options.convert.PageSize:
        '''8.5 x 5.5 inches.'''
        raise NotImplementedError()

    @property
    def TABLOID(self) -> groupdocs.conversion.options.convert.PageSize:
        '''11 x 17 inches.'''
        raise NotImplementedError()

    @property
    def UNSET(self) -> groupdocs.conversion.options.convert.PageSize:
        '''Unset paper size.'''
        raise NotImplementedError()


class PdfConvertOptions(CommonConvertOptions):
    '''Options for conversion to Pdf file type.'''
    
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.options.convert.PdfConvertOptions` class.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def clone(self) -> Any:
        '''Clones current options instance.'''
        raise NotImplementedError()
    
    @property
    def format(self) -> groupdocs.conversion.filetypes.FileType:
        '''Overrides the Format property to ensure it is of type PdfFileType.'''
        raise NotImplementedError()
    
    @format.setter
    def format(self, value : groupdocs.conversion.filetypes.FileType) -> None:
        '''Overrides the Format property to ensure it is of type PdfFileType.'''
        raise NotImplementedError()
    
    @property
    def watermark(self) -> groupdocs.conversion.options.convert.WatermarkOptions:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IWatermarkedConvertOptions.watermark`'''
        raise NotImplementedError()
    
    @watermark.setter
    def watermark(self, value : groupdocs.conversion.options.convert.WatermarkOptions) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IWatermarkedConvertOptions.watermark`'''
        raise NotImplementedError()
    
    @property
    def page_number(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @page_number.setter
    def page_number(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    
    @pages_count.setter
    def pages_count(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    
    @property
    def pages(self) -> System.Collections.Generic.List`1[[System.Int32]]:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageRangedConvertOptions.pages`'''
        raise NotImplementedError()
    
    @pages.setter
    def pages(self, value : System.Collections.Generic.List`1[[System.Int32]]) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageRangedConvertOptions.pages`'''
        raise NotImplementedError()
    
    @property
    def dpi(self) -> int:
        '''Desired page DPI after conversion. The default resolution is: 96 dpi.'''
        raise NotImplementedError()
    
    @dpi.setter
    def dpi(self, value : int) -> None:
        '''Desired page DPI after conversion. The default resolution is: 96 dpi.'''
        raise NotImplementedError()
    
    @property
    def password(self) -> str:
        '''Set this property if you want to protect the converted document with a password.'''
        raise NotImplementedError()
    
    @password.setter
    def password(self, value : str) -> None:
        '''Set this property if you want to protect the converted document with a password.'''
        raise NotImplementedError()
    
    @property
    def margin_top(self) -> System.Nullable`1[[System.Single]]:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageMarginConvertOptions.margin_top`'''
        raise NotImplementedError()
    
    @margin_top.setter
    def margin_top(self, value : System.Nullable`1[[System.Single]]) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageMarginConvertOptions.margin_top`'''
        raise NotImplementedError()
    
    @property
    def margin_bottom(self) -> System.Nullable`1[[System.Single]]:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageMarginConvertOptions.margin_bottom`'''
        raise NotImplementedError()
    
    @margin_bottom.setter
    def margin_bottom(self, value : System.Nullable`1[[System.Single]]) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageMarginConvertOptions.margin_bottom`'''
        raise NotImplementedError()
    
    @property
    def margin_left(self) -> System.Nullable`1[[System.Single]]:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageMarginConvertOptions.margin_left`'''
        raise NotImplementedError()
    
    @margin_left.setter
    def margin_left(self, value : System.Nullable`1[[System.Single]]) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageMarginConvertOptions.margin_left`'''
        raise NotImplementedError()
    
    @property
    def margin_right(self) -> System.Nullable`1[[System.Single]]:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageMarginConvertOptions.margin_right`'''
        raise NotImplementedError()
    
    @margin_right.setter
    def margin_right(self, value : System.Nullable`1[[System.Single]]) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageMarginConvertOptions.margin_right`'''
        raise NotImplementedError()
    
    @property
    def pdf_options(self) -> groupdocs.conversion.options.convert.PdfOptions:
        '''Pdf specific convert options'''
        raise NotImplementedError()
    
    @pdf_options.setter
    def pdf_options(self, value : groupdocs.conversion.options.convert.PdfOptions) -> None:
        '''Pdf specific convert options'''
        raise NotImplementedError()
    
    @property
    def rotate(self) -> groupdocs.conversion.options.convert.Rotation:
        '''Page rotation'''
        raise NotImplementedError()
    
    @rotate.setter
    def rotate(self, value : groupdocs.conversion.options.convert.Rotation) -> None:
        '''Page rotation'''
        raise NotImplementedError()
    
    @property
    def page_size(self) -> groupdocs.conversion.options.convert.PageSize:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_size`'''
        raise NotImplementedError()
    
    @page_size.setter
    def page_size(self, value : groupdocs.conversion.options.convert.PageSize) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_size`'''
        raise NotImplementedError()
    
    @property
    def page_width(self) -> float:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_width`'''
        raise NotImplementedError()
    
    @page_width.setter
    def page_width(self, value : float) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_width`'''
        raise NotImplementedError()
    
    @property
    def page_height(self) -> float:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_height`'''
        raise NotImplementedError()
    
    @page_height.setter
    def page_height(self, value : float) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_height`'''
        raise NotImplementedError()
    
    @property
    def page_orientation(self) -> groupdocs.conversion.options.convert.PageOrientation:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageOrientationConvertOptions.page_orientation`'''
        raise NotImplementedError()
    
    @page_orientation.setter
    def page_orientation(self, value : groupdocs.conversion.options.convert.PageOrientation) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageOrientationConvertOptions.page_orientation`'''
        raise NotImplementedError()
    

class PdfDirection(groupdocs.conversion.contracts.Enumeration):
    '''Describes Pdf text direction.'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
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
    
    @staticmethod
    def get_all() -> System.Collections.Generic.IEnumerable`1[[GroupDocs.Conversion.Options.Convert.PdfDirection]]:
        '''Returns all enumeration values.
        
        :returns: Enumerable of the provided type'''
        raise NotImplementedError()
    
    @property
    def L2R(self) -> groupdocs.conversion.options.convert.PdfDirection:
        '''Left to right.'''
        raise NotImplementedError()

    @property
    def R2L(self) -> groupdocs.conversion.options.convert.PdfDirection:
        '''Right to left.'''
        raise NotImplementedError()


class PdfDocumentInfo(groupdocs.conversion.contracts.ValueObject):
    '''Represents meta information of PDF document.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @property
    def author(self) -> str:
        '''Gets document author.'''
        raise NotImplementedError()
    
    @author.setter
    def author(self, value : str) -> None:
        '''Sets document author.'''
        raise NotImplementedError()
    
    @property
    def creation_date(self) -> System.Nullable`1[[System.DateTime]]:
        '''Gets the date of document creation.'''
        raise NotImplementedError()
    
    @creation_date.setter
    def creation_date(self, value : System.Nullable`1[[System.DateTime]]) -> None:
        '''Sets the date of document creation.'''
        raise NotImplementedError()
    
    @property
    def creation_time_zone(self) -> System.Nullable`1[[System.TimeSpan]]:
        '''Time zone of creation date'''
        raise NotImplementedError()
    
    @creation_time_zone.setter
    def creation_time_zone(self, value : System.Nullable`1[[System.TimeSpan]]) -> None:
        '''Time zone of creation date'''
        raise NotImplementedError()
    
    @property
    def creator(self) -> str:
        '''Gets document creator.'''
        raise NotImplementedError()
    
    @creator.setter
    def creator(self, value : str) -> None:
        '''Sets document creator.'''
        raise NotImplementedError()
    
    @property
    def keywords(self) -> str:
        '''Gets or set the keywords of the document.'''
        raise NotImplementedError()
    
    @keywords.setter
    def keywords(self, value : str) -> None:
        '''Set the keywords of the document.'''
        raise NotImplementedError()
    
    @property
    def mod_date(self) -> System.Nullable`1[[System.DateTime]]:
        '''Gets the date of document modification.'''
        raise NotImplementedError()
    
    @mod_date.setter
    def mod_date(self, value : System.Nullable`1[[System.DateTime]]) -> None:
        '''Sets the date of document modification.'''
        raise NotImplementedError()
    
    @property
    def mod_time_zone(self) -> System.Nullable`1[[System.TimeSpan]]:
        '''Time zone of modification date.'''
        raise NotImplementedError()
    
    @mod_time_zone.setter
    def mod_time_zone(self, value : System.Nullable`1[[System.TimeSpan]]) -> None:
        '''Time zone of modification date.'''
        raise NotImplementedError()
    
    @property
    def producer(self) -> str:
        '''Gets the document producer.'''
        raise NotImplementedError()
    
    @producer.setter
    def producer(self, value : str) -> None:
        '''Sets the document producer.'''
        raise NotImplementedError()
    
    @property
    def subject(self) -> str:
        '''Gets the subject of the document.'''
        raise NotImplementedError()
    
    @subject.setter
    def subject(self, value : str) -> None:
        '''Sets the subject of the document.'''
        raise NotImplementedError()
    
    @property
    def title(self) -> str:
        '''Gets document title.'''
        raise NotImplementedError()
    
    @title.setter
    def title(self, value : str) -> None:
        '''Sets document title.'''
        raise NotImplementedError()
    

class PdfFontSubsetStrategy(groupdocs.conversion.contracts.Enumeration):
    '''Specifies font subsetting strategy'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
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
    
    @staticmethod
    def set_none(value: groupdocs.conversion.options.convert.PdfFontSubsetStrategy) -> None:
        '''Do not subset fonts'''
    @property
    def none(self) -> groupdocs.conversion.options.convert.PdfFontSubsetStrategy:
        '''Do not subset fonts'''
        raise NotImplementedError()

    @staticmethod
    def set_subset_all_fonts(value: groupdocs.conversion.options.convert.PdfFontSubsetStrategy) -> None:
        '''Subset all fonts, used in a document.'''
    @property
    def subset_all_fonts(self) -> groupdocs.conversion.options.convert.PdfFontSubsetStrategy:
        '''Subset all fonts, used in a document.'''
        raise NotImplementedError()

    @staticmethod
    def set_subset_embedded_fonts_only(value: groupdocs.conversion.options.convert.PdfFontSubsetStrategy) -> None:
        '''Portrait page orientation (narrow and tall).'''
    @property
    def subset_embedded_fonts_only(self) -> groupdocs.conversion.options.convert.PdfFontSubsetStrategy:
        '''Portrait page orientation (narrow and tall).'''
        raise NotImplementedError()


class PdfFormats(groupdocs.conversion.contracts.Enumeration):
    '''Describes Pdf formats enumeration.'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
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
    
    @staticmethod
    def get_all() -> System.Collections.Generic.IEnumerable`1[[GroupDocs.Conversion.Options.Convert.PdfFormats]]:
        '''Returns all enumeration values.
        
        :returns: Enumerable of the provided type'''
        raise NotImplementedError()
    
    @property
    def DEFAULT(self) -> groupdocs.conversion.options.convert.PdfFormats:
        '''Default pdf format'''
        raise NotImplementedError()

    @property
    def PDF_A_1A(self) -> groupdocs.conversion.options.convert.PdfFormats:
        '''PDF/A-1a – Level A (accessible) conformance.'''
        raise NotImplementedError()

    @property
    def PDF_A_1B(self) -> groupdocs.conversion.options.convert.PdfFormats:
        '''PDF/A-1b – Level B (basic) conformance.'''
        raise NotImplementedError()

    @property
    def PDF_A_2A(self) -> groupdocs.conversion.options.convert.PdfFormats:
        '''PDF/A-2a conformance.'''
        raise NotImplementedError()

    @property
    def PDF_A_3A(self) -> groupdocs.conversion.options.convert.PdfFormats:
        '''PDF/A-3a conformance.'''
        raise NotImplementedError()

    @property
    def PDF_A_2B(self) -> groupdocs.conversion.options.convert.PdfFormats:
        '''PDF/A-2b conformance.'''
        raise NotImplementedError()

    @property
    def PDF_A_2U(self) -> groupdocs.conversion.options.convert.PdfFormats:
        '''PDF/A-2u conformance.'''
        raise NotImplementedError()

    @property
    def PDF_A_3B(self) -> groupdocs.conversion.options.convert.PdfFormats:
        '''PDF/A-3b conformance.'''
        raise NotImplementedError()

    @property
    def PDF_A_3U(self) -> groupdocs.conversion.options.convert.PdfFormats:
        '''PDF/A-3u conformance.'''
        raise NotImplementedError()

    @property
    def V_1_3(self) -> groupdocs.conversion.options.convert.PdfFormats:
        '''PDF version 1.3.'''
        raise NotImplementedError()

    @property
    def V_1_4(self) -> groupdocs.conversion.options.convert.PdfFormats:
        '''PDF version 1.4.'''
        raise NotImplementedError()

    @property
    def V_1_5(self) -> groupdocs.conversion.options.convert.PdfFormats:
        '''PDF version 1.5.'''
        raise NotImplementedError()

    @property
    def V_1_6(self) -> groupdocs.conversion.options.convert.PdfFormats:
        '''PDF version 1.6.'''
        raise NotImplementedError()

    @property
    def V_1_7(self) -> groupdocs.conversion.options.convert.PdfFormats:
        '''PDF version 1.7.'''
        raise NotImplementedError()

    @property
    def PDF_X_1A(self) -> groupdocs.conversion.options.convert.PdfFormats:
        '''PDF/X-1a conformance.'''
        raise NotImplementedError()

    @property
    def PDF_X_3(self) -> groupdocs.conversion.options.convert.PdfFormats:
        '''PDF/X-3 conformance.'''
        raise NotImplementedError()

    @property
    def PDF_UA_1(self) -> groupdocs.conversion.options.convert.PdfFormats:
        '''PDF/UA-1 conformance.'''
        raise NotImplementedError()


class PdfFormattingOptions(groupdocs.conversion.contracts.ValueObject):
    '''Defines Pdf formatting options.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @property
    def center_window(self) -> bool:
        '''Specifies whether position of the document\'s window will be centered on the screen. Default: false.'''
        raise NotImplementedError()
    
    @center_window.setter
    def center_window(self, value : bool) -> None:
        '''Specifies whether position of the document\'s window will be centered on the screen. Default: false.'''
        raise NotImplementedError()
    
    @property
    def direction(self) -> groupdocs.conversion.options.convert.PdfDirection:
        '''Sets reading order of text: L2R (left to right) or R2L (right to left). Default: L2R.'''
        raise NotImplementedError()
    
    @direction.setter
    def direction(self, value : groupdocs.conversion.options.convert.PdfDirection) -> None:
        '''Sets reading order of text: L2R (left to right) or R2L (right to left). Default: L2R.'''
        raise NotImplementedError()
    
    @property
    def display_doc_title(self) -> bool:
        '''Specifies whether document\'s window title bar should display document title. Default: false.'''
        raise NotImplementedError()
    
    @display_doc_title.setter
    def display_doc_title(self, value : bool) -> None:
        '''Specifies whether document\'s window title bar should display document title. Default: false.'''
        raise NotImplementedError()
    
    @property
    def fit_window(self) -> bool:
        '''Specifies whether document window must be resized to fit the first displayed page. Default: false.'''
        raise NotImplementedError()
    
    @fit_window.setter
    def fit_window(self, value : bool) -> None:
        '''Specifies whether document window must be resized to fit the first displayed page. Default: false.'''
        raise NotImplementedError()
    
    @property
    def hide_menu_bar(self) -> bool:
        '''Specifies whether menu bar should be hidden when document is active. Default: false.'''
        raise NotImplementedError()
    
    @hide_menu_bar.setter
    def hide_menu_bar(self, value : bool) -> None:
        '''Specifies whether menu bar should be hidden when document is active. Default: false.'''
        raise NotImplementedError()
    
    @property
    def hide_tool_bar(self) -> bool:
        '''Specifies whether toolbar should be hidden when document is active. Default: false.'''
        raise NotImplementedError()
    
    @hide_tool_bar.setter
    def hide_tool_bar(self, value : bool) -> None:
        '''Specifies whether toolbar should be hidden when document is active. Default: false.'''
        raise NotImplementedError()
    
    @property
    def hide_window_ui(self) -> bool:
        '''Specifies whether user interface elements should be hidden when document is active. Default: false.'''
        raise NotImplementedError()
    
    @hide_window_ui.setter
    def hide_window_ui(self, value : bool) -> None:
        '''Specifies whether user interface elements should be hidden when document is active. Default: false.'''
        raise NotImplementedError()
    
    @property
    def non_full_screen_page_mode(self) -> groupdocs.conversion.options.convert.PdfPageMode:
        '''Sets page mode, specifying how to display the document on exiting full-screen mode.'''
        raise NotImplementedError()
    
    @non_full_screen_page_mode.setter
    def non_full_screen_page_mode(self, value : groupdocs.conversion.options.convert.PdfPageMode) -> None:
        '''Sets page mode, specifying how to display the document on exiting full-screen mode.'''
        raise NotImplementedError()
    
    @property
    def page_layout(self) -> groupdocs.conversion.options.convert.PdfPageLayout:
        '''Sets page layout which shall be used when the document is opened.'''
        raise NotImplementedError()
    
    @page_layout.setter
    def page_layout(self, value : groupdocs.conversion.options.convert.PdfPageLayout) -> None:
        '''Sets page layout which shall be used when the document is opened.'''
        raise NotImplementedError()
    
    @property
    def page_mode(self) -> groupdocs.conversion.options.convert.PdfPageMode:
        '''Sets page mode, specifying how document should be displayed when opened.'''
        raise NotImplementedError()
    
    @page_mode.setter
    def page_mode(self, value : groupdocs.conversion.options.convert.PdfPageMode) -> None:
        '''Sets page mode, specifying how document should be displayed when opened.'''
        raise NotImplementedError()
    

class PdfOptimizationOptions(groupdocs.conversion.contracts.ValueObject):
    '''Defines Pdf optimization options.'''
    
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.options.convert.PdfOptimizationOptions` class.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @property
    def link_duplicate_streams(self) -> bool:
        '''Link duplicate streams'''
        raise NotImplementedError()
    
    @link_duplicate_streams.setter
    def link_duplicate_streams(self, value : bool) -> None:
        '''Link duplicate streams'''
        raise NotImplementedError()
    
    @property
    def remove_unused_objects(self) -> bool:
        '''Remove unused objects'''
        raise NotImplementedError()
    
    @remove_unused_objects.setter
    def remove_unused_objects(self, value : bool) -> None:
        '''Remove unused objects'''
        raise NotImplementedError()
    
    @property
    def remove_unused_streams(self) -> bool:
        '''Remove unused streams'''
        raise NotImplementedError()
    
    @remove_unused_streams.setter
    def remove_unused_streams(self, value : bool) -> None:
        '''Remove unused streams'''
        raise NotImplementedError()
    
    @property
    def compress_images(self) -> bool:
        '''If CompressImages set to ``true``, all images in the document are re-compressed. The compression is defined by the ImageQuality property.'''
        raise NotImplementedError()
    
    @compress_images.setter
    def compress_images(self, value : bool) -> None:
        '''If CompressImages set to ``true``, all images in the document are re-compressed. The compression is defined by the ImageQuality property.'''
        raise NotImplementedError()
    
    @property
    def image_quality(self) -> int:
        '''Value in percent where 100% is unchanged quality and image size. To decrease the image size set this property to less than 100'''
        raise NotImplementedError()
    
    @image_quality.setter
    def image_quality(self, value : int) -> None:
        '''Value in percent where 100% is unchanged quality and image size. To decrease the image size set this property to less than 100'''
        raise NotImplementedError()
    
    @property
    def unembed_fonts(self) -> bool:
        '''Make fonts not embedded if set to true'''
        raise NotImplementedError()
    
    @unembed_fonts.setter
    def unembed_fonts(self, value : bool) -> None:
        '''Make fonts not embedded if set to true'''
        raise NotImplementedError()
    
    @property
    def font_subset_strategy(self) -> groupdocs.conversion.options.convert.PdfFontSubsetStrategy:
        '''Set font subset strategy'''
        raise NotImplementedError()
    
    @font_subset_strategy.setter
    def font_subset_strategy(self, value : groupdocs.conversion.options.convert.PdfFontSubsetStrategy) -> None:
        '''Set font subset strategy'''
        raise NotImplementedError()
    

class PdfOptions(groupdocs.conversion.contracts.ValueObject):
    '''Options for conversion to Pdf file type.'''
    
    def __init__(self) -> None:
        '''ctor'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @property
    def pdf_format(self) -> groupdocs.conversion.options.convert.PdfFormats:
        '''Sets the pdf format of the converted document.'''
        raise NotImplementedError()
    
    @pdf_format.setter
    def pdf_format(self, value : groupdocs.conversion.options.convert.PdfFormats) -> None:
        '''Sets the pdf format of the converted document.'''
        raise NotImplementedError()
    
    @property
    def remove_pdf_a_compliance(self) -> bool:
        '''Removes Pdf-A Compliance'''
        raise NotImplementedError()
    
    @remove_pdf_a_compliance.setter
    def remove_pdf_a_compliance(self, value : bool) -> None:
        '''Removes Pdf-A Compliance'''
        raise NotImplementedError()
    
    @property
    def zoom(self) -> int:
        '''Specifies the zoom level in percentage. Default is 100.'''
        raise NotImplementedError()
    
    @zoom.setter
    def zoom(self, value : int) -> None:
        '''Specifies the zoom level in percentage. Default is 100.'''
        raise NotImplementedError()
    
    @property
    def linearize(self) -> bool:
        '''Linearizes PDF Document for the Web'''
        raise NotImplementedError()
    
    @linearize.setter
    def linearize(self, value : bool) -> None:
        '''Linearizes PDF Document for the Web'''
        raise NotImplementedError()
    
    @property
    def optimization_options(self) -> groupdocs.conversion.options.convert.PdfOptimizationOptions:
        '''Pdf optimization options'''
        raise NotImplementedError()
    
    @optimization_options.setter
    def optimization_options(self, value : groupdocs.conversion.options.convert.PdfOptimizationOptions) -> None:
        '''Pdf optimization options'''
        raise NotImplementedError()
    
    @property
    def grayscale(self) -> bool:
        '''Convert a PDF from RGB colorspace to grayscale'''
        raise NotImplementedError()
    
    @grayscale.setter
    def grayscale(self, value : bool) -> None:
        '''Convert a PDF from RGB colorspace to grayscale'''
        raise NotImplementedError()
    
    @property
    def formatting_options(self) -> groupdocs.conversion.options.convert.PdfFormattingOptions:
        '''Pdf formatting options'''
        raise NotImplementedError()
    
    @formatting_options.setter
    def formatting_options(self, value : groupdocs.conversion.options.convert.PdfFormattingOptions) -> None:
        '''Pdf formatting options'''
        raise NotImplementedError()
    
    @property
    def document_info(self) -> groupdocs.conversion.options.convert.PdfDocumentInfo:
        '''Meta information of PDF document.'''
        raise NotImplementedError()
    
    @document_info.setter
    def document_info(self, value : groupdocs.conversion.options.convert.PdfDocumentInfo) -> None:
        '''Meta information of PDF document.'''
        raise NotImplementedError()
    

class PdfPageLayout(groupdocs.conversion.contracts.Enumeration):
    '''Describes Pdf page layout.'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
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
    
    @staticmethod
    def get_all() -> System.Collections.Generic.IEnumerable`1[[GroupDocs.Conversion.Options.Convert.PdfPageLayout]]:
        '''Returns all enumeration values.
        
        :returns: Enumerable of the provided type'''
        raise NotImplementedError()
    
    @property
    def DEFAULT(self) -> groupdocs.conversion.options.convert.PdfPageLayout:
        '''Default layout.'''
        raise NotImplementedError()

    @property
    def SINGLE_PAGE(self) -> groupdocs.conversion.options.convert.PdfPageLayout:
        '''Single page.'''
        raise NotImplementedError()

    @property
    def ONE_COLUMN(self) -> groupdocs.conversion.options.convert.PdfPageLayout:
        '''Display pages in one column.'''
        raise NotImplementedError()

    @property
    def TWO_COLUMN_LEFT(self) -> groupdocs.conversion.options.convert.PdfPageLayout:
        '''Display the pages in two columns, with odd-numbered pages on the left.'''
        raise NotImplementedError()

    @property
    def TWO_COLUMN_RIGHT(self) -> groupdocs.conversion.options.convert.PdfPageLayout:
        '''Display the pages in two columns, with odd-numbered pages on the right.'''
        raise NotImplementedError()

    @property
    def TWO_PAGES_LEFT(self) -> groupdocs.conversion.options.convert.PdfPageLayout:
        '''Display the pages two at a time, with odd-numbered pages on the left.'''
        raise NotImplementedError()

    @property
    def TWO_PAGES_RIGHT(self) -> groupdocs.conversion.options.convert.PdfPageLayout:
        '''Display the pages two at a time, with odd-numbered pages on the right.'''
        raise NotImplementedError()


class PdfPageMode(groupdocs.conversion.contracts.Enumeration):
    '''Describes Pdf page mode'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
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
    
    @staticmethod
    def get_all() -> System.Collections.Generic.IEnumerable`1[[GroupDocs.Conversion.Options.Convert.PdfPageMode]]:
        '''Returns all enumeration values.
        
        :returns: Enumerable of the provided type'''
        raise NotImplementedError()
    
    @property
    def USE_NONE(self) -> groupdocs.conversion.options.convert.PdfPageMode:
        '''Don\'t use any components.'''
        raise NotImplementedError()

    @property
    def USE_OUTLINES(self) -> groupdocs.conversion.options.convert.PdfPageMode:
        '''Document outline visible.'''
        raise NotImplementedError()

    @property
    def USE_THUMBS(self) -> groupdocs.conversion.options.convert.PdfPageMode:
        '''Thumbnail images visible.'''
        raise NotImplementedError()

    @property
    def FULL_SCREEN(self) -> groupdocs.conversion.options.convert.PdfPageMode:
        '''FullScreenFull-screen mode, with no menu bar, window controls, or any other window visible.'''
        raise NotImplementedError()

    @property
    def USE_OC(self) -> groupdocs.conversion.options.convert.PdfPageMode:
        '''Optional content group panel visible.'''
        raise NotImplementedError()

    @property
    def USE_ATTACHMENTS(self) -> groupdocs.conversion.options.convert.PdfPageMode:
        '''Attachments panel visible.'''
        raise NotImplementedError()


class PdfRecognitionMode(groupdocs.conversion.contracts.Enumeration):
    '''Allows to control how a PDF document is converted into a word processing document.'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
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
    
    @property
    def TEXTBOX(self) -> groupdocs.conversion.options.convert.PdfRecognitionMode:
        '''This mode is fast and good for maximally preserving original look of the PDF
        file, but editability of the resulting document could be limited.
        Every visually grouped block of text int the original PDF file is converted into
        a textbox in the resulting document. This achieves maximal resemblance of the
        output document to the original PDF file. The output document will look good,
        but it will consist entirely of textboxes and it could makes further editing
        of the document in Microsoft Word quite hard.
        This is the default mode.'''
        raise NotImplementedError()

    @property
    def FLOW(self) -> groupdocs.conversion.options.convert.PdfRecognitionMode:
        '''Full recognition mode, the engine performs grouping and multi-level analysis
        to restore the original document author\'s intent and produce a maximally editable
        document. The downside is that the output document might look different from
        the original PDF file.'''
        raise NotImplementedError()


class PresentationConvertOptions(CommonConvertOptions):
    '''Describes options for conversion to Presentation file type.'''
    
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.options.convert.PresentationConvertOptions` class.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def clone(self) -> Any:
        '''Clones current options instance.'''
        raise NotImplementedError()
    
    @property
    def format(self) -> groupdocs.conversion.filetypes.FileType:
        '''Overrides the Format property to ensure it is of type PresentationFileType.'''
        raise NotImplementedError()
    
    @format.setter
    def format(self, value : groupdocs.conversion.filetypes.FileType) -> None:
        '''Overrides the Format property to ensure it is of type PresentationFileType.'''
        raise NotImplementedError()
    
    @property
    def watermark(self) -> groupdocs.conversion.options.convert.WatermarkOptions:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IWatermarkedConvertOptions.watermark`'''
        raise NotImplementedError()
    
    @watermark.setter
    def watermark(self, value : groupdocs.conversion.options.convert.WatermarkOptions) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IWatermarkedConvertOptions.watermark`'''
        raise NotImplementedError()
    
    @property
    def page_number(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @page_number.setter
    def page_number(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    
    @pages_count.setter
    def pages_count(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    
    @property
    def pages(self) -> System.Collections.Generic.List`1[[System.Int32]]:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageRangedConvertOptions.pages`'''
        raise NotImplementedError()
    
    @pages.setter
    def pages(self, value : System.Collections.Generic.List`1[[System.Int32]]) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageRangedConvertOptions.pages`'''
        raise NotImplementedError()
    
    @property
    def password(self) -> str:
        '''Set this property if you want to protect the converted document with a password.'''
        raise NotImplementedError()
    
    @password.setter
    def password(self, value : str) -> None:
        '''Set this property if you want to protect the converted document with a password.'''
        raise NotImplementedError()
    
    @property
    def zoom(self) -> int:
        '''Specifies the zoom level in percentage. Default is 100.
        Default zoom is supported till Microsoft Powerpoint 2010. Starting from Microsoft Powerpoint 2013 default zoom is no longer set to document, instead it appears to use the zoom factor of the last document that was opened.'''
        raise NotImplementedError()
    
    @zoom.setter
    def zoom(self, value : int) -> None:
        '''Specifies the zoom level in percentage. Default is 100.
        Default zoom is supported till Microsoft Powerpoint 2010. Starting from Microsoft Powerpoint 2013 default zoom is no longer set to document, instead it appears to use the zoom factor of the last document that was opened.'''
        raise NotImplementedError()
    

class ProjectManagementConvertOptions(ConvertOptions):
    '''Options for conversion to Project management file type.'''
    
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.options.convert.ProjectManagementConvertOptions` class.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def clone(self) -> Any:
        '''Clones current options instance.'''
        raise NotImplementedError()
    
    @property
    def format(self) -> groupdocs.conversion.filetypes.FileType:
        '''Overrides the Format property to ensure it is of type ProjectManagementFileType.'''
        raise NotImplementedError()
    
    @format.setter
    def format(self, value : groupdocs.conversion.filetypes.FileType) -> None:
        '''Overrides the Format property to ensure it is of type ProjectManagementFileType.'''
        raise NotImplementedError()
    

class PsdColorModes(groupdocs.conversion.contracts.Enumeration):
    '''Defines Psd color modes enumeration.'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
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
    
    @staticmethod
    def get_all() -> System.Collections.Generic.IEnumerable`1[[GroupDocs.Conversion.Options.Convert.PsdColorModes]]:
        '''Returns all enumeration values.
        
        :returns: Enumerable of the provided type'''
        raise NotImplementedError()
    
    @property
    def BITMAP(self) -> groupdocs.conversion.options.convert.PsdColorModes:
        '''Bitmap.'''
        raise NotImplementedError()

    @property
    def GRAYSCALE(self) -> groupdocs.conversion.options.convert.PsdColorModes:
        '''Grayscale.'''
        raise NotImplementedError()

    @property
    def INDEXED(self) -> groupdocs.conversion.options.convert.PsdColorModes:
        '''Indexed.'''
        raise NotImplementedError()

    @property
    def RGB(self) -> groupdocs.conversion.options.convert.PsdColorModes:
        '''RGB.'''
        raise NotImplementedError()

    @property
    def CMYK(self) -> groupdocs.conversion.options.convert.PsdColorModes:
        '''CMYK.'''
        raise NotImplementedError()

    @property
    def MULTICHANNEL(self) -> groupdocs.conversion.options.convert.PsdColorModes:
        '''Multichannel.'''
        raise NotImplementedError()

    @property
    def DUOTONE(self) -> groupdocs.conversion.options.convert.PsdColorModes:
        '''Duotone.'''
        raise NotImplementedError()

    @property
    def LAB(self) -> groupdocs.conversion.options.convert.PsdColorModes:
        '''Lab.'''
        raise NotImplementedError()


class PsdCompressionMethods(groupdocs.conversion.contracts.Enumeration):
    '''Describes Psd compression methods.'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
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
    
    @staticmethod
    def get_all() -> System.Collections.Generic.IEnumerable`1[[GroupDocs.Conversion.Options.Convert.PsdCompressionMethods]]:
        '''Returns all enumeration values.
        
        :returns: Enumerable of the provided type'''
        raise NotImplementedError()
    
    @property
    def RAW(self) -> groupdocs.conversion.options.convert.PsdCompressionMethods:
        '''RAW.'''
        raise NotImplementedError()

    @property
    def RLE(self) -> groupdocs.conversion.options.convert.PsdCompressionMethods:
        '''RLE.'''
        raise NotImplementedError()

    @property
    def ZIP_WITHOUT_PREDICTION(self) -> groupdocs.conversion.options.convert.PsdCompressionMethods:
        '''ZipWithoutPrediction.'''
        raise NotImplementedError()

    @property
    def ZIP_WITH_PREDICTION(self) -> groupdocs.conversion.options.convert.PsdCompressionMethods:
        '''ZipWithPrediction.'''
        raise NotImplementedError()


class PsdOptions(groupdocs.conversion.contracts.ValueObject):
    '''Options for converting to Psd file type.'''
    
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.options.convert.PsdOptions` class.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @property
    def channel_bits_count(self) -> int:
        '''Bits count per color channel.'''
        raise NotImplementedError()
    
    @channel_bits_count.setter
    def channel_bits_count(self, value : int) -> None:
        '''Bits count per color channel.'''
        raise NotImplementedError()
    
    @property
    def channels_count(self) -> int:
        '''Color channels count.'''
        raise NotImplementedError()
    
    @channels_count.setter
    def channels_count(self, value : int) -> None:
        '''Color channels count.'''
        raise NotImplementedError()
    
    @property
    def color_mode(self) -> groupdocs.conversion.options.convert.PsdColorModes:
        '''Psd color mode.'''
        raise NotImplementedError()
    
    @color_mode.setter
    def color_mode(self, value : groupdocs.conversion.options.convert.PsdColorModes) -> None:
        '''Psd color mode.'''
        raise NotImplementedError()
    
    @property
    def compression(self) -> groupdocs.conversion.options.convert.PsdCompressionMethods:
        '''Psd compression method.'''
        raise NotImplementedError()
    
    @compression.setter
    def compression(self, value : groupdocs.conversion.options.convert.PsdCompressionMethods) -> None:
        '''Psd compression method.'''
        raise NotImplementedError()
    
    @property
    def version(self) -> int:
        '''Psd file version.'''
        raise NotImplementedError()
    
    @version.setter
    def version(self, value : int) -> None:
        '''Psd file version.'''
        raise NotImplementedError()
    

class Rotation(groupdocs.conversion.contracts.Enumeration):
    '''Describes page rotation enumeration'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
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
    
    @staticmethod
    def get_all() -> System.Collections.Generic.IEnumerable`1[[GroupDocs.Conversion.Options.Convert.Rotation]]:
        '''Returns all enumeration values.
        
        :returns: Enumerable of the provided type'''
        raise NotImplementedError()
    
    @property
    def NONE(self) -> groupdocs.conversion.options.convert.Rotation:
        '''None.'''
        raise NotImplementedError()

    @property
    def ON90(self) -> groupdocs.conversion.options.convert.Rotation:
        '''90 degrees.'''
        raise NotImplementedError()

    @property
    def ON180(self) -> groupdocs.conversion.options.convert.Rotation:
        '''180 degrees.'''
        raise NotImplementedError()

    @property
    def ON270(self) -> groupdocs.conversion.options.convert.Rotation:
        '''270 degrees.'''
        raise NotImplementedError()


class RtfOptions(groupdocs.conversion.contracts.ValueObject):
    '''Options for conversion to RTF file type.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @property
    def export_images_for_old_readers(self) -> bool:
        '''Specifies whether the keywords for "old readers" are written to RTF or not.
        This can significantly affect the size of the RTF document. Default is False.'''
        raise NotImplementedError()
    
    @export_images_for_old_readers.setter
    def export_images_for_old_readers(self, value : bool) -> None:
        '''Specifies whether the keywords for "old readers" are written to RTF or not.
        This can significantly affect the size of the RTF document. Default is False.'''
        raise NotImplementedError()
    

class SpreadsheetConvertOptions(CommonConvertOptions):
    '''Options for conversion to Spreadsheet file type.'''
    
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.options.convert.SpreadsheetConvertOptions` class.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def clone(self) -> Any:
        '''Clones current options instance.'''
        raise NotImplementedError()
    
    @property
    def format(self) -> groupdocs.conversion.filetypes.FileType:
        '''The desired file type the input document should be converted to.'''
        raise NotImplementedError()
    
    @format.setter
    def format(self, value : groupdocs.conversion.filetypes.FileType) -> None:
        '''The desired file type the input document should be converted to.'''
        raise NotImplementedError()
    
    @property
    def watermark(self) -> groupdocs.conversion.options.convert.WatermarkOptions:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IWatermarkedConvertOptions.watermark`'''
        raise NotImplementedError()
    
    @watermark.setter
    def watermark(self, value : groupdocs.conversion.options.convert.WatermarkOptions) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IWatermarkedConvertOptions.watermark`'''
        raise NotImplementedError()
    
    @property
    def page_number(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @page_number.setter
    def page_number(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    
    @pages_count.setter
    def pages_count(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    
    @property
    def pages(self) -> System.Collections.Generic.List`1[[System.Int32]]:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageRangedConvertOptions.pages`'''
        raise NotImplementedError()
    
    @pages.setter
    def pages(self, value : System.Collections.Generic.List`1[[System.Int32]]) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageRangedConvertOptions.pages`'''
        raise NotImplementedError()
    
    @property
    def password(self) -> str:
        '''Set this property if you want to protect the converted document with a password.'''
        raise NotImplementedError()
    
    @password.setter
    def password(self, value : str) -> None:
        '''Set this property if you want to protect the converted document with a password.'''
        raise NotImplementedError()
    
    @property
    def zoom(self) -> int:
        '''Specifies the zoom level in percentage. Default is 100.'''
        raise NotImplementedError()
    
    @zoom.setter
    def zoom(self, value : int) -> None:
        '''Specifies the zoom level in percentage. Default is 100.'''
        raise NotImplementedError()
    
    @property
    def separator(self) -> System.Char:
        '''Specifies the separator to be used when convert to a delimited formats'''
        raise NotImplementedError()
    
    @separator.setter
    def separator(self, value : System.Char) -> None:
        '''Specifies the separator to be used when convert to a delimited formats'''
        raise NotImplementedError()
    
    @property
    def encoding(self) -> str:
        '''Specifies the encoding to be used when convert to a delimited formats'''
        raise NotImplementedError()
    
    @encoding.setter
    def encoding(self, value : str) -> None:
        '''Specifies the encoding to be used when convert to a delimited formats'''
        raise NotImplementedError()
    

class ThreeDConvertOptions(ConvertOptions):
    '''Options for conversion to 3D type.'''
    
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.options.convert.ThreeDConvertOptions` class.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def clone(self) -> Any:
        '''Clones current options instance.'''
        raise NotImplementedError()
    
    @property
    def format(self) -> groupdocs.conversion.filetypes.FileType:
        '''Overrides the Format property to ensure it is of type ThreeDFileType.'''
        raise NotImplementedError()
    
    @format.setter
    def format(self, value : groupdocs.conversion.filetypes.FileType) -> None:
        '''Overrides the Format property to ensure it is of type ThreeDFileType.'''
        raise NotImplementedError()
    
    @property
    def page_number(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @page_number.setter
    def page_number(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    
    @pages_count.setter
    def pages_count(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    

class TiffCompressionMethods(groupdocs.conversion.contracts.Enumeration):
    '''Describes Tiff compression methods enumeration.'''
    
    def __init__(self) -> None:
        '''Serialization constructor'''
        raise NotImplementedError()
    
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
    
    @staticmethod
    def get_all() -> System.Collections.Generic.IEnumerable`1[[GroupDocs.Conversion.Options.Convert.TiffCompressionMethods]]:
        '''Returns all enumeration values.
        
        :returns: Enumerable of the provided type'''
        raise NotImplementedError()
    
    @property
    def LZW(self) -> groupdocs.conversion.options.convert.TiffCompressionMethods:
        '''LZW compression.'''
        raise NotImplementedError()

    @property
    def NONE(self) -> groupdocs.conversion.options.convert.TiffCompressionMethods:
        '''No compression.'''
        raise NotImplementedError()

    @property
    def CCITT3(self) -> groupdocs.conversion.options.convert.TiffCompressionMethods:
        '''CCITT3 compression.'''
        raise NotImplementedError()

    @property
    def CCITT4(self) -> groupdocs.conversion.options.convert.TiffCompressionMethods:
        '''CCITT4 compression.'''
        raise NotImplementedError()

    @property
    def RLE(self) -> groupdocs.conversion.options.convert.TiffCompressionMethods:
        '''RLE compression.'''
        raise NotImplementedError()


class TiffOptions(groupdocs.conversion.contracts.ValueObject):
    '''Options for conversion to TIFF file type.'''
    
    def __init__(self) -> None:
        '''ctor'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @property
    def compression(self) -> groupdocs.conversion.options.convert.TiffCompressionMethods:
        '''Sets Tiff compression.'''
        raise NotImplementedError()
    
    @compression.setter
    def compression(self, value : groupdocs.conversion.options.convert.TiffCompressionMethods) -> None:
        '''Sets Tiff compression.'''
        raise NotImplementedError()
    

class WatermarkImageOptions(WatermarkOptions):
    '''Options for settings watermark to the converted document'''
    
    def __init__(self, image : List[int]) -> None:
        '''Create WatermarkOptions class and set watermark text
        
        :param image: The image to be used as watermark'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def clone(self) -> Any:
        '''Clone current instance'''
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''Watermark width'''
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : int) -> None:
        '''Watermark width'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''Watermark height'''
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : int) -> None:
        '''Watermark height'''
        raise NotImplementedError()
    
    @property
    def top(self) -> int:
        '''Watermark top position'''
        raise NotImplementedError()
    
    @top.setter
    def top(self, value : int) -> None:
        '''Watermark top position'''
        raise NotImplementedError()
    
    @property
    def left(self) -> int:
        '''Watermark left position'''
        raise NotImplementedError()
    
    @left.setter
    def left(self, value : int) -> None:
        '''Watermark left position'''
        raise NotImplementedError()
    
    @property
    def rotation_angle(self) -> int:
        '''Watermark rotation angle'''
        raise NotImplementedError()
    
    @rotation_angle.setter
    def rotation_angle(self, value : int) -> None:
        '''Watermark rotation angle'''
        raise NotImplementedError()
    
    @property
    def transparency(self) -> float:
        '''Watermark transparency. Value between 0 and 1. Value 0 is fully visible, value 1 is invisible.'''
        raise NotImplementedError()
    
    @transparency.setter
    def transparency(self, value : float) -> None:
        '''Watermark transparency. Value between 0 and 1. Value 0 is fully visible, value 1 is invisible.'''
        raise NotImplementedError()
    
    @property
    def background(self) -> bool:
        '''Indicates that the watermark is stamped as background. If the value is true, the watermark is laid at the bottom. By default is false and the watermark is laid on top.'''
        raise NotImplementedError()
    
    @background.setter
    def background(self, value : bool) -> None:
        '''Indicates that the watermark is stamped as background. If the value is true, the watermark is laid at the bottom. By default is false and the watermark is laid on top.'''
        raise NotImplementedError()
    
    @property
    def auto_align(self) -> bool:
        '''Auto scale the watermark. If the value is true the position and size is automatically calculated to fit the page size.'''
        raise NotImplementedError()
    
    @auto_align.setter
    def auto_align(self, value : bool) -> None:
        '''Auto scale the watermark. If the value is true the position and size is automatically calculated to fit the page size.'''
        raise NotImplementedError()
    
    @property
    def image(self) -> List[int]:
        '''Image watermark'''
        raise NotImplementedError()
    

class WatermarkOptions(groupdocs.conversion.contracts.ValueObject):
    '''Options for settings watermark to the converted document'''
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def clone(self) -> Any:
        '''Clone current instance'''
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''Watermark width'''
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : int) -> None:
        '''Watermark width'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''Watermark height'''
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : int) -> None:
        '''Watermark height'''
        raise NotImplementedError()
    
    @property
    def top(self) -> int:
        '''Watermark top position'''
        raise NotImplementedError()
    
    @top.setter
    def top(self, value : int) -> None:
        '''Watermark top position'''
        raise NotImplementedError()
    
    @property
    def left(self) -> int:
        '''Watermark left position'''
        raise NotImplementedError()
    
    @left.setter
    def left(self, value : int) -> None:
        '''Watermark left position'''
        raise NotImplementedError()
    
    @property
    def rotation_angle(self) -> int:
        '''Watermark rotation angle'''
        raise NotImplementedError()
    
    @rotation_angle.setter
    def rotation_angle(self, value : int) -> None:
        '''Watermark rotation angle'''
        raise NotImplementedError()
    
    @property
    def transparency(self) -> float:
        '''Watermark transparency. Value between 0 and 1. Value 0 is fully visible, value 1 is invisible.'''
        raise NotImplementedError()
    
    @transparency.setter
    def transparency(self, value : float) -> None:
        '''Watermark transparency. Value between 0 and 1. Value 0 is fully visible, value 1 is invisible.'''
        raise NotImplementedError()
    
    @property
    def background(self) -> bool:
        '''Indicates that the watermark is stamped as background. If the value is true, the watermark is laid at the bottom. By default is false and the watermark is laid on top.'''
        raise NotImplementedError()
    
    @background.setter
    def background(self, value : bool) -> None:
        '''Indicates that the watermark is stamped as background. If the value is true, the watermark is laid at the bottom. By default is false and the watermark is laid on top.'''
        raise NotImplementedError()
    
    @property
    def auto_align(self) -> bool:
        '''Auto scale the watermark. If the value is true the position and size is automatically calculated to fit the page size.'''
        raise NotImplementedError()
    
    @auto_align.setter
    def auto_align(self, value : bool) -> None:
        '''Auto scale the watermark. If the value is true the position and size is automatically calculated to fit the page size.'''
        raise NotImplementedError()
    

class WatermarkTextOptions(WatermarkOptions):
    '''Options for settings text watermark to the converted document'''
    
    def __init__(self, text : str) -> None:
        '''Create WatermarkOptions class and set watermark text
        
        :param text: The text to be used as watermark.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def clone(self) -> Any:
        '''Clone current instance'''
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''Watermark width'''
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : int) -> None:
        '''Watermark width'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''Watermark height'''
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : int) -> None:
        '''Watermark height'''
        raise NotImplementedError()
    
    @property
    def top(self) -> int:
        '''Watermark top position'''
        raise NotImplementedError()
    
    @top.setter
    def top(self, value : int) -> None:
        '''Watermark top position'''
        raise NotImplementedError()
    
    @property
    def left(self) -> int:
        '''Watermark left position'''
        raise NotImplementedError()
    
    @left.setter
    def left(self, value : int) -> None:
        '''Watermark left position'''
        raise NotImplementedError()
    
    @property
    def rotation_angle(self) -> int:
        '''Watermark rotation angle'''
        raise NotImplementedError()
    
    @rotation_angle.setter
    def rotation_angle(self, value : int) -> None:
        '''Watermark rotation angle'''
        raise NotImplementedError()
    
    @property
    def transparency(self) -> float:
        '''Watermark transparency. Value between 0 and 1. Value 0 is fully visible, value 1 is invisible.'''
        raise NotImplementedError()
    
    @transparency.setter
    def transparency(self, value : float) -> None:
        '''Watermark transparency. Value between 0 and 1. Value 0 is fully visible, value 1 is invisible.'''
        raise NotImplementedError()
    
    @property
    def background(self) -> bool:
        '''Indicates that the watermark is stamped as background. If the value is true, the watermark is laid at the bottom. By default is false and the watermark is laid on top.'''
        raise NotImplementedError()
    
    @background.setter
    def background(self, value : bool) -> None:
        '''Indicates that the watermark is stamped as background. If the value is true, the watermark is laid at the bottom. By default is false and the watermark is laid on top.'''
        raise NotImplementedError()
    
    @property
    def auto_align(self) -> bool:
        '''Auto scale the watermark. If the value is true the position and size is automatically calculated to fit the page size.'''
        raise NotImplementedError()
    
    @auto_align.setter
    def auto_align(self, value : bool) -> None:
        '''Auto scale the watermark. If the value is true the position and size is automatically calculated to fit the page size.'''
        raise NotImplementedError()
    
    @property
    def text(self) -> str:
        '''Watermark text'''
        raise NotImplementedError()
    
    @property
    def watermark_font(self) -> groupdocs.conversion.options.convert.Font:
        '''Watermark font if text watermark is applied'''
        raise NotImplementedError()
    
    @watermark_font.setter
    def watermark_font(self, value : groupdocs.conversion.options.convert.Font) -> None:
        '''Watermark font if text watermark is applied'''
        raise NotImplementedError()
    
    @property
    def color(self) -> aspose.pydrawing.Color:
        '''Watermark font color if text watermark is applied'''
        raise NotImplementedError()
    
    @color.setter
    def color(self, value : aspose.pydrawing.Color) -> None:
        '''Watermark font color if text watermark is applied'''
        raise NotImplementedError()
    

class WebConvertOptions(CommonConvertOptions):
    '''Options for conversion to Web file type.'''
    
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.options.convert.WebConvertOptions` class.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def clone(self) -> Any:
        '''Clones current options instance.'''
        raise NotImplementedError()
    
    @property
    def format(self) -> groupdocs.conversion.filetypes.FileType:
        '''Overrides the Format property to ensure it is of type WebFileType.'''
        raise NotImplementedError()
    
    @format.setter
    def format(self, value : groupdocs.conversion.filetypes.FileType) -> None:
        '''Overrides the Format property to ensure it is of type WebFileType.'''
        raise NotImplementedError()
    
    @property
    def watermark(self) -> groupdocs.conversion.options.convert.WatermarkOptions:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IWatermarkedConvertOptions.watermark`'''
        raise NotImplementedError()
    
    @watermark.setter
    def watermark(self, value : groupdocs.conversion.options.convert.WatermarkOptions) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IWatermarkedConvertOptions.watermark`'''
        raise NotImplementedError()
    
    @property
    def page_number(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @page_number.setter
    def page_number(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    
    @pages_count.setter
    def pages_count(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    
    @property
    def pages(self) -> System.Collections.Generic.List`1[[System.Int32]]:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageRangedConvertOptions.pages`'''
        raise NotImplementedError()
    
    @pages.setter
    def pages(self, value : System.Collections.Generic.List`1[[System.Int32]]) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageRangedConvertOptions.pages`'''
        raise NotImplementedError()
    
    @property
    def use_pdf(self) -> bool:
        '''If ``true``, the input firstly is converted to PDF and after that to desired format'''
        raise NotImplementedError()
    
    @use_pdf.setter
    def use_pdf(self, value : bool) -> None:
        '''If ``true``, the input firstly is converted to PDF and after that to desired format'''
        raise NotImplementedError()
    
    @property
    def fixed_layout(self) -> bool:
        '''If ``true`` fixed layout will be used e.g. absolutely positioned html elements
        Default:  true'''
        raise NotImplementedError()
    
    @fixed_layout.setter
    def fixed_layout(self, value : bool) -> None:
        '''If ``true`` fixed layout will be used e.g. absolutely positioned html elements
        Default:  true'''
        raise NotImplementedError()
    
    @property
    def fixed_layout_show_borders(self) -> bool:
        '''Show page borders when converting to fixed layout. Default is True.'''
        raise NotImplementedError()
    
    @fixed_layout_show_borders.setter
    def fixed_layout_show_borders(self, value : bool) -> None:
        '''Show page borders when converting to fixed layout. Default is True.'''
        raise NotImplementedError()
    
    @property
    def zoom(self) -> int:
        '''Specifies the zoom level in percentage. Default is 100.'''
        raise NotImplementedError()
    
    @zoom.setter
    def zoom(self, value : int) -> None:
        '''Specifies the zoom level in percentage. Default is 100.'''
        raise NotImplementedError()
    
    @property
    def embed_font_resources(self) -> bool:
        '''Specifies whether to embed font resources within the main HTML. Default is false.
        Note: If FixedLayout is set to true, font resources will always be embedded.'''
        raise NotImplementedError()
    
    @embed_font_resources.setter
    def embed_font_resources(self, value : bool) -> None:
        '''Specifies whether to embed font resources within the main HTML. Default is false.
        Note: If FixedLayout is set to true, font resources will always be embedded.'''
        raise NotImplementedError()
    

class WebpOptions(groupdocs.conversion.contracts.ValueObject):
    '''Options for conversion to Webp file type.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    @property
    def lossless(self) -> bool:
        '''Indicates if the compression of the converted file will be lossless.'''
        raise NotImplementedError()
    
    @lossless.setter
    def lossless(self, value : bool) -> None:
        '''Indicates if the compression of the converted file will be lossless.'''
        raise NotImplementedError()
    
    @property
    def quality(self) -> int:
        '''Gets the quality.'''
        raise NotImplementedError()
    
    @quality.setter
    def quality(self, value : int) -> None:
        '''Sets the quality.'''
        raise NotImplementedError()
    

class WordProcessingConvertOptions(CommonConvertOptions):
    '''Options for conversion to WordProcessing file type.'''
    
    def __init__(self) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.options.convert.WordProcessingConvertOptions` class.'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.conversion.contracts.ValueObject) -> bool:
        '''Determines whether two object instances are equal.
        
        :param other: The object to compare with the current object.
        :returns: ``true`` if the specified object is equal to the current object; otherwise, ``false``.'''
        raise NotImplementedError()
    
    def clone(self) -> Any:
        '''Clones current options instance.'''
        raise NotImplementedError()
    
    @property
    def format(self) -> groupdocs.conversion.filetypes.FileType:
        '''Overrides the Format property to ensure it is of type WordProcessingFileType.'''
        raise NotImplementedError()
    
    @format.setter
    def format(self, value : groupdocs.conversion.filetypes.FileType) -> None:
        '''Overrides the Format property to ensure it is of type WordProcessingFileType.'''
        raise NotImplementedError()
    
    @property
    def watermark(self) -> groupdocs.conversion.options.convert.WatermarkOptions:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IWatermarkedConvertOptions.watermark`'''
        raise NotImplementedError()
    
    @watermark.setter
    def watermark(self, value : groupdocs.conversion.options.convert.WatermarkOptions) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IWatermarkedConvertOptions.watermark`'''
        raise NotImplementedError()
    
    @property
    def page_number(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @page_number.setter
    def page_number(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.page_number`'''
        raise NotImplementedError()
    
    @property
    def pages_count(self) -> int:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    
    @pages_count.setter
    def pages_count(self, value : int) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPagedConvertOptions.pages_count`'''
        raise NotImplementedError()
    
    @property
    def pages(self) -> System.Collections.Generic.List`1[[System.Int32]]:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageRangedConvertOptions.pages`'''
        raise NotImplementedError()
    
    @pages.setter
    def pages(self, value : System.Collections.Generic.List`1[[System.Int32]]) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageRangedConvertOptions.pages`'''
        raise NotImplementedError()
    
    @property
    def rtf_options(self) -> groupdocs.conversion.options.convert.RtfOptions:
        '''RTF specific convert options'''
        raise NotImplementedError()
    
    @rtf_options.setter
    def rtf_options(self, value : groupdocs.conversion.options.convert.RtfOptions) -> None:
        '''RTF specific convert options'''
        raise NotImplementedError()
    
    @property
    def dpi(self) -> int:
        '''Desired page DPI after conversion. The default resolution is: 96 dpi.'''
        raise NotImplementedError()
    
    @dpi.setter
    def dpi(self, value : int) -> None:
        '''Desired page DPI after conversion. The default resolution is: 96 dpi.'''
        raise NotImplementedError()
    
    @property
    def password(self) -> str:
        '''Set this property if you want to protect the converted document with a password.'''
        raise NotImplementedError()
    
    @password.setter
    def password(self, value : str) -> None:
        '''Set this property if you want to protect the converted document with a password.'''
        raise NotImplementedError()
    
    @property
    def zoom(self) -> int:
        '''Specifies the zoom level in percentage. Default is 100.
        Default zoom is supported till Microsoft Word 2010. Starting from Microsoft Word 2013 default zoom is no longer set to document, instead it appears to use the zoom factor of the last document that was opened.'''
        raise NotImplementedError()
    
    @zoom.setter
    def zoom(self, value : int) -> None:
        '''Specifies the zoom level in percentage. Default is 100.
        Default zoom is supported till Microsoft Word 2010. Starting from Microsoft Word 2013 default zoom is no longer set to document, instead it appears to use the zoom factor of the last document that was opened.'''
        raise NotImplementedError()
    
    @property
    def margin_top(self) -> System.Nullable`1[[System.Single]]:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageMarginConvertOptions.margin_top`'''
        raise NotImplementedError()
    
    @margin_top.setter
    def margin_top(self, value : System.Nullable`1[[System.Single]]) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageMarginConvertOptions.margin_top`'''
        raise NotImplementedError()
    
    @property
    def margin_bottom(self) -> System.Nullable`1[[System.Single]]:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageMarginConvertOptions.margin_bottom`'''
        raise NotImplementedError()
    
    @margin_bottom.setter
    def margin_bottom(self, value : System.Nullable`1[[System.Single]]) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageMarginConvertOptions.margin_bottom`'''
        raise NotImplementedError()
    
    @property
    def margin_left(self) -> System.Nullable`1[[System.Single]]:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageMarginConvertOptions.margin_left`'''
        raise NotImplementedError()
    
    @margin_left.setter
    def margin_left(self, value : System.Nullable`1[[System.Single]]) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageMarginConvertOptions.margin_left`'''
        raise NotImplementedError()
    
    @property
    def margin_right(self) -> System.Nullable`1[[System.Single]]:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageMarginConvertOptions.margin_right`'''
        raise NotImplementedError()
    
    @margin_right.setter
    def margin_right(self, value : System.Nullable`1[[System.Single]]) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageMarginConvertOptions.margin_right`'''
        raise NotImplementedError()
    
    @property
    def pdf_recognition_mode(self) -> groupdocs.conversion.options.convert.PdfRecognitionMode:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPdfRecognitionModeOptions.pdf_recognition_mode`'''
        raise NotImplementedError()
    
    @pdf_recognition_mode.setter
    def pdf_recognition_mode(self, value : groupdocs.conversion.options.convert.PdfRecognitionMode) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPdfRecognitionModeOptions.pdf_recognition_mode`'''
        raise NotImplementedError()
    
    @property
    def page_size(self) -> groupdocs.conversion.options.convert.PageSize:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_size`'''
        raise NotImplementedError()
    
    @page_size.setter
    def page_size(self, value : groupdocs.conversion.options.convert.PageSize) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_size`'''
        raise NotImplementedError()
    
    @property
    def page_width(self) -> float:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_width`'''
        raise NotImplementedError()
    
    @page_width.setter
    def page_width(self, value : float) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_width`'''
        raise NotImplementedError()
    
    @property
    def page_height(self) -> float:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_height`'''
        raise NotImplementedError()
    
    @page_height.setter
    def page_height(self, value : float) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageSizeConvertOptions.page_height`'''
        raise NotImplementedError()
    
    @property
    def page_orientation(self) -> groupdocs.conversion.options.convert.PageOrientation:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageOrientationConvertOptions.page_orientation`'''
        raise NotImplementedError()
    
    @page_orientation.setter
    def page_orientation(self, value : groupdocs.conversion.options.convert.PageOrientation) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.IPageOrientationConvertOptions.page_orientation`'''
        raise NotImplementedError()
    
    @property
    def markdown_options(self) -> groupdocs.conversion.options.convert.MarkdownOptions:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.WordProcessingConvertOptions.markdown_options`'''
        raise NotImplementedError()
    
    @markdown_options.setter
    def markdown_options(self, value : groupdocs.conversion.options.convert.MarkdownOptions) -> None:
        '''Implements :py:attr:`groupdocs.conversion.options.convert.WordProcessingConvertOptions.markdown_options`'''
        raise NotImplementedError()
    

