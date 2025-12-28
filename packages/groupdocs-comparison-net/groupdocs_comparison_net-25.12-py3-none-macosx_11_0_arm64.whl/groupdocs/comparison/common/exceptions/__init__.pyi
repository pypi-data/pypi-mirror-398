from typing import List, Optional, Dict, Iterable, Any, overload
import io
import collections.abc
from collections.abc import Sequence
from datetime import datetime
from aspose.pyreflection import Type
import aspose.pycore
import aspose.pydrawing
from uuid import UUID
import groupdocs.comparison
import groupdocs.comparison.cells
import groupdocs.comparison.cells.style
import groupdocs.comparison.common
import groupdocs.comparison.common.exceptions
import groupdocs.comparison.interfaces
import groupdocs.comparison.localization
import groupdocs.comparison.logging
import groupdocs.comparison.options
import groupdocs.comparison.result
import groupdocs.comparison.words
import groupdocs.comparison.words.revision

class ComparisonException:
    '''Base class for all comparison process exceptions.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`groupdocs.comparison.common.exceptions.ComparisonException` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, message : str) -> None:
        '''Initializes a new instance of the :py:class:`groupdocs.comparison.common.exceptions.ComparisonException` class with a specified error message.
        
        :param message: The exception message'''
        raise NotImplementedError()
    

class DocumentComparisonException(ComparisonException):
    '''The exception that is thrown when an error occurs while comparing documents.'''
    
    def __init__(self, message : str) -> None:
        '''Initializes a new instance of :py:class:`groupdocs.comparison.common.exceptions.DocumentComparisonException` class.'''
        raise NotImplementedError()
    

class FileFormatException(ComparisonException):
    '''The exception that is thrown when comparing files with different formats.'''
    
    def __init__(self, source_path : str, target_path : str) -> None:
        '''Initializes a new instance of :py:class:`groupdocs.comparison.common.exceptions.FileFormatException` class.
        
        :param source_path: The source file path
        :param target_path: The target file path'''
        raise NotImplementedError()
    

class InvalidPasswordException(ComparisonException):
    '''The exception that is thrown when specified password is incorrect.'''
    
    def __init__(self) -> None:
        '''Initializes a new instance of :py:class:`groupdocs.comparison.common.exceptions.InvalidPasswordException` class.'''
        raise NotImplementedError()
    

class PasswordProtectedFileException(ComparisonException):
    '''The exception that is thrown when the document is protected by password.'''
    
    def __init__(self) -> None:
        '''Initializes a new instance of :py:class:`groupdocs.comparison.common.exceptions.PasswordProtectedFileException` class.'''
        raise NotImplementedError()
    

class UnsupportedFileFormatException(ComparisonException):
    '''The exception that is thrown when file of this format doesn\'t support comparison.'''
    
    @overload
    def __init__(self) -> None:
        '''Initializes a new instance of :py:class:`groupdocs.comparison.common.exceptions.UnsupportedFileFormatException` class.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, path_file : str) -> None:
        '''Initializes a new instance of :py:class:`groupdocs.comparison.common.exceptions.UnsupportedFileFormatException` class.'''
        raise NotImplementedError()
    

