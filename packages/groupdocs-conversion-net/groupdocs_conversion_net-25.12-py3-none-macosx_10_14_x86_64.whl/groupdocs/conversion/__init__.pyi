
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

class Converter:
    '''Represents main class that controls document conversion process.'''
    
    @overload
    def __init__(self, document : io._IOBase) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.Converter` class.
        
        :param document: Readable stream.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, document : io._IOBase, settings : groupdocs.conversion.ConverterSettings) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.Converter` class.
        
        :param document: Readable stream.
        :param settings: The Converter settings.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, document : io._IOBase, load_options : groupdocs.conversion.options.load.LoadOptions) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.Converter` class.
        
        :param document: Readable stream.
        :param load_options: Document load options.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, document : io._IOBase, load_options : groupdocs.conversion.options.load.LoadOptions, settings : groupdocs.conversion.ConverterSettings) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.Converter` class.
        
        :param document: Readable stream.
        :param load_options: Document load options.
        :param settings: The Converter settings.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_path : str) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.Converter` class.
        
        :param file_path: The file path to the source document.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_path : str, settings : groupdocs.conversion.ConverterSettings) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.Converter` class.
        
        :param file_path: The file path to the source document.
        :param settings: The Converter settings.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_path : str, load_options : groupdocs.conversion.options.load.LoadOptions) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.Converter` class.
        
        :param file_path: The file path to the source document.
        :param load_options: Document load options.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_path : str, load_options : groupdocs.conversion.options.load.LoadOptions, settings : groupdocs.conversion.ConverterSettings) -> None:
        '''Initializes new instance of :py:class:`groupdocs.conversion.Converter` class.
        
        :param file_path: The file path to the source document.
        :param load_options: Document load options.
        :param settings: The Converter settings.'''
        raise NotImplementedError()
    
    @overload
    def convert(self, document : io._IOBase, convert_options : groupdocs.conversion.options.convert.ConvertOptions) -> None:
        '''Converts source document. Saves the whole converted document.
        
        :param document: Output stream.
        :param convert_options: The convert options specific to desired target file type.'''
        raise NotImplementedError()
    
    @overload
    def convert(self, file_path : str, convert_options : groupdocs.conversion.options.convert.ConvertOptions) -> None:
        '''Converts source document. Saves the whole converted document.
        
        :param file_path: The file path to the output document.
        :param convert_options: The convert options specific to desired target file type.'''
        raise NotImplementedError()
    
    @overload
    def convert_by_page(self, output_folder : str, convert_options : groupdocs.conversion.options.convert.ConvertOptions) -> None:
        '''Converts source document. Saves the converted document page by page.
        
        :param output_folder: Output folder to save converted pages. File name template is converted-page-{0}.ext.
        :param convert_options: The convert options specific to desired target file type.'''
        raise NotImplementedError()
    
    @overload
    def convert_by_page(self, file_path : str, page_number : int, convert_options : groupdocs.conversion.options.convert.ConvertOptions) -> None:
        '''Converts source document. Saves the converted document page to a stream
        
        :param file_path: Output file path.
        :param page_number: Page number to convert.
        :param convert_options: The convert options specific to desired target file type.'''
        raise NotImplementedError()
    
    @overload
    def convert_by_page(self, page_stream : io._IOBase, page_number : int, convert_options : groupdocs.conversion.options.convert.ConvertOptions) -> None:
        '''Converts source document. Saves the converted document page to a stream
        
        :param page_stream: Output page stream.
        :param page_number: Page number to convert.
        :param convert_options: The convert options specific to desired target file type.'''
        raise NotImplementedError()
    
    def convert_multiple(self, output_folder : str, convert_options : groupdocs.conversion.options.convert.ConvertOptions) -> None:
        '''Converts source document to multiple documents of the output format.
        
        :param output_folder: Output folder path. File
        :param convert_options: The convert options specific to desired target file type.'''
        raise NotImplementedError()
    
    def get_document_info(self) -> groupdocs.conversion.contracts.IDocumentInfo:
        '''Gets source document info - pages count and other document properties specific to the file type.'''
        raise NotImplementedError()
    
    def is_document_password_protected(self) -> bool:
        '''Checks is source document is password protected
        
        :returns: true if document is password protected'''
        raise NotImplementedError()
    
    def get_possible_conversions(self) -> groupdocs.conversion.contracts.PossibleConversions:
        '''Gets possible conversions for the source document.'''
        raise NotImplementedError()
    
    @staticmethod
    def get_all_possible_conversions() -> System.Collections.Generic.IEnumerable`1[[GroupDocs.Conversion.Contracts.PossibleConversions]]:
        '''Gets all supported conversions'''
        raise NotImplementedError()
    
    @staticmethod
    def get_possible_conversions_by_extension(extension : str) -> groupdocs.conversion.contracts.PossibleConversions:
        '''Gets supported conversions for provided document extension
        
        :param extension: Document extension'''
        raise NotImplementedError()
    

class ConverterSettings:
    '''Defines settings for customizing :py:class:`groupdocs.conversion.Converter` behaviour.'''
    
    def __init__(self) -> None:
        '''Default constructor'''
        raise NotImplementedError()
    
    @property
    def cache(self) -> groupdocs.conversion.caching.ICache:
        '''The cache implementation used for storing conversion results.'''
        raise NotImplementedError()
    
    @cache.setter
    def cache(self, value : groupdocs.conversion.caching.ICache) -> None:
        '''The cache implementation used for storing conversion results.'''
        raise NotImplementedError()
    
    @property
    def logger(self) -> groupdocs.conversion.logging.ILogger:
        '''The logger implementation used for logging conversion process.'''
        raise NotImplementedError()
    
    @logger.setter
    def logger(self, value : groupdocs.conversion.logging.ILogger) -> None:
        '''The logger implementation used for logging conversion process.'''
        raise NotImplementedError()
    
    @property
    def font_directories(self) -> System.Collections.Generic.List`1[[System.String]]:
        '''The custom font directories paths'''
        raise NotImplementedError()
    
    @property
    def temp_folder(self) -> str:
        '''Temp folder used for conversion'''
        raise NotImplementedError()
    
    @temp_folder.setter
    def temp_folder(self, value : str) -> None:
        '''Temp folder used for conversion'''
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
        
        :param license_path: The license path.'''
        raise NotImplementedError()
    
    @property
    def is_licensed(self) -> bool:
        '''Returns true if a valid license has been applied; false if the component is running in evaluation mode.'''
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
    

