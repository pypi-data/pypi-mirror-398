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

class ConversionNotSupportedException(GroupDocsConversionException):
    '''GroupDocs exception thrown when the conversion from source file to target file type is not supported'''
    
    def __init__(self, message : str) -> None:
        '''Creates an exception instance with a message
        
        :param message: The message'''
        raise NotImplementedError()
    

class CorruptOrDamagedFileException(GroupDocsConversionException):
    '''GroupDocs exception thrown when the file is corrupt or damaged'''
    
    @overload
    def __init__(self) -> None:
        '''Default constructor'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_type : groupdocs.conversion.filetypes.FileType) -> None:
        '''Creates an exception instance with a FileType
        
        :param file_type: The file type'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, message : str) -> None:
        '''Creates an exception instance with a message
        
        :param message: The message'''
        raise NotImplementedError()
    

class FileTypeNotSupportedException(GroupDocsConversionException):
    '''GroupDocs exception thrown when the file type is not supported'''
    
    @overload
    def __init__(self) -> None:
        '''Default constructor'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_type : groupdocs.conversion.filetypes.FileType) -> None:
        '''Creates an exception instance with a FileType
        
        :param file_type: The file type'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, message : str) -> None:
        '''Creates an exception instance with a message
        
        :param message: The message'''
        raise NotImplementedError()
    

class FontSubstituteException(GroupDocsConversionException):
    '''Thrown if font substitute is illegal'''
    
    @overload
    def __init__(self) -> None:
        '''Default constructor'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, message : str) -> None:
        '''Creates an exception with a specific message
        
        :param message: The message'''
        raise NotImplementedError()
    

class GroupDocsConversionException:
    '''GroupDocs.Conversion general exception'''
    
    @overload
    def __init__(self) -> None:
        '''Default constructor'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, message : str) -> None:
        '''Creates an exception with a specific message
        
        :param message: The message'''
        raise NotImplementedError()
    

class IncorrectPasswordException(GroupDocsConversionException):
    '''GroupDocs exception thrown when the file is password protected, password is provided but is incorrect'''
    
    @overload
    def __init__(self) -> None:
        '''Default constructor'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_type : groupdocs.conversion.filetypes.FileType) -> None:
        '''Creates an exception instance with a FileType
        
        :param file_type: The file type'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, message : str) -> None:
        '''Creates an exception instance with a message
        
        :param message: The message'''
        raise NotImplementedError()
    

class InvalidConvertOptionsException(GroupDocsConversionException):
    '''Thrown if provided convert options are invalid'''
    
    @overload
    def __init__(self) -> None:
        '''Default constructor'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, message : str) -> None:
        '''Creates an exception with a specific message
        
        :param message: The message'''
        raise NotImplementedError()
    

class InvalidConverterSettingsException(GroupDocsConversionException):
    '''Thrown if provided converter settings are invalid'''
    
    @overload
    def __init__(self) -> None:
        '''Default constructor'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, message : str) -> None:
        '''Creates an exception with a specific message
        
        :param message: The message'''
        raise NotImplementedError()
    

class PasswordRequiredException(GroupDocsConversionException):
    '''GroupDocs exception thrown when the file is password protected and password is not provided'''
    
    @overload
    def __init__(self) -> None:
        '''Default constructor'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_type : groupdocs.conversion.filetypes.FileType) -> None:
        '''Creates an exception instance with a FileType
        
        :param file_type: The file type'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, message : str) -> None:
        '''Creates an exception instance with a message
        
        :param message: The message'''
        raise NotImplementedError()
    

class SourceDocumentFactoryNotProvidedException(GroupDocsConversionException):
    '''GroupDocs exception thrown when the source document factory is not provided'''
    
    def __init__(self) -> None:
        '''Creates an exception instance with a message'''
        raise NotImplementedError()
    

