
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

class Comparer:
    '''Represents main class that controls the documents comparison process.'''
    
    @overload
    def __init__(self, file_path : str) -> None:
        '''Initializes new instance of :py:class:`groupdocs.comparison.Comparer` class with source file path.
        
        :param file_path: File path'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, folder_path : str, compare_options : groupdocs.comparison.options.CompareOptions) -> None:
        '''Initializes new instance of :py:class:`groupdocs.comparison.Comparer` with source folder path and :py:class:`groupdocs.comparison.options.CompareOptions`.
        
        :param folder_path: Folder path
        :param compare_options: Compare options'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_path : str, load_options : groupdocs.comparison.options.LoadOptions) -> None:
        '''Initializes new instance of :py:class:`groupdocs.comparison.Comparer` with source file path and :py:class:`groupdocs.comparison.options.LoadOptions`.
        
        :param file_path: File path
        :param load_options: Load options'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_path : str, settings : groupdocs.comparison.ComparerSettings) -> None:
        '''Initializes new instance of :py:class:`groupdocs.comparison.Comparer` class with source file path and :py:class:`groupdocs.comparison.ComparerSettings`.
        
        :param file_path: File path
        :param settings: Settings for comparison'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_path : str, load_options : groupdocs.comparison.options.LoadOptions, settings : groupdocs.comparison.ComparerSettings) -> None:
        '''Initializes new instance of :py:class:`groupdocs.comparison.Comparer` class with source file path, :py:class:`groupdocs.comparison.options.LoadOptions` and :py:class:`groupdocs.comparison.ComparerSettings`.
        
        :param file_path: File path
        :param load_options: Load options
        :param settings: Settings for comparison'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, document : io._IOBase) -> None:
        '''Initializes new instance of :py:class:`groupdocs.comparison.Comparer` class with source document stream.
        
        :param document: Source document stream'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, document : io._IOBase, load_options : groupdocs.comparison.options.LoadOptions) -> None:
        '''Initializes new instance of :py:class:`groupdocs.comparison.Comparer` with source document stream and :py:class:`groupdocs.comparison.options.LoadOptions`.
        
        :param document: Source document stream
        :param load_options: Load options'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, document : io._IOBase, settings : groupdocs.comparison.ComparerSettings) -> None:
        '''Initializes new instance of :py:class:`groupdocs.comparison.Comparer` class with source document stream and :py:class:`groupdocs.comparison.ComparerSettings`.
        
        :param document: Source document stream
        :param settings: Settings for comparison'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, document : io._IOBase, load_options : groupdocs.comparison.options.LoadOptions, settings : groupdocs.comparison.ComparerSettings) -> None:
        '''Initializes new instance of :py:class:`groupdocs.comparison.Comparer` class with document stream, :py:class:`groupdocs.comparison.options.LoadOptions` and :py:class:`groupdocs.comparison.ComparerSettings`.
        
        :param document: Source document stream
        :param load_options: Load options
        :param settings: Settings for comparison'''
        raise NotImplementedError()
    
    @overload
    def compare(self) -> groupdocs.comparison.Document:
        '''Compares documents without saving result with default options'''
        raise NotImplementedError()
    
    @overload
    def compare(self, file_path : str) -> groupdocs.comparison.Document:
        '''Compares documents and saves result to file path
        
        :param file_path: Result document path'''
        raise NotImplementedError()
    
    @overload
    def compare(self, stream : io._IOBase) -> groupdocs.comparison.Document:
        '''Compares documents and saves result to file stream'''
        raise NotImplementedError()
    
    @overload
    def compare(self, file_path : str, compare_options : groupdocs.comparison.options.CompareOptions) -> groupdocs.comparison.Document:
        '''Compares documents and saves result to file path
        
        :param file_path: Result document file path
        :param compare_options: Compare options'''
        raise NotImplementedError()
    
    @overload
    def compare(self, document : io._IOBase, compare_options : groupdocs.comparison.options.CompareOptions) -> groupdocs.comparison.Document:
        '''Compares documents and saves result to file stream
        
        :param document: Result document stream
        :param compare_options: Compare options'''
        raise NotImplementedError()
    
    @overload
    def compare(self, save_options : groupdocs.comparison.options.SaveOptions, compare_options : groupdocs.comparison.options.CompareOptions) -> groupdocs.comparison.Document:
        '''Compares documents without saving result.
        
        :param save_options: Save options
        :param compare_options: Compare options'''
        raise NotImplementedError()
    
    @overload
    def compare(self, file_path : str, save_options : groupdocs.comparison.options.SaveOptions) -> groupdocs.comparison.Document:
        '''Compares documents and save result to file path
        
        :param file_path: Result document file path
        :param save_options: Save options'''
        raise NotImplementedError()
    
    @overload
    def compare(self, document : io._IOBase, save_options : groupdocs.comparison.options.SaveOptions) -> groupdocs.comparison.Document:
        '''Compares documents and save result to file stream
        
        :param document: Result document stream
        :param save_options: Save options'''
        raise NotImplementedError()
    
    @overload
    def compare(self, compare_options : groupdocs.comparison.options.CompareOptions) -> groupdocs.comparison.Document:
        '''Compares documents without saving result.
        
        :param compare_options: Compare options'''
        raise NotImplementedError()
    
    @overload
    def compare(self, stream : io._IOBase, save_options : groupdocs.comparison.options.SaveOptions, compare_options : groupdocs.comparison.options.CompareOptions) -> groupdocs.comparison.Document:
        '''Compares documents and saves result to a stream.
        
        :param stream: Result document stream
        :param save_options: Save options
        :param compare_options: Compare options'''
        raise NotImplementedError()
    
    @overload
    def compare(self, file_path : str, save_options : groupdocs.comparison.options.SaveOptions, compare_options : groupdocs.comparison.options.CompareOptions) -> groupdocs.comparison.Document:
        '''Compares documents and saves result to file path
        
        :param file_path: Result document file path
        :param save_options: Save options
        :param compare_options: Compare options'''
        raise NotImplementedError()
    
    @overload
    def add(self, file_path : str) -> None:
        '''Adds file to comparison.
        
        :param file_path: Compared file path'''
        raise NotImplementedError()
    
    @overload
    def add(self, file_path : str, compare_options : groupdocs.comparison.options.CompareOptions) -> None:
        '''Adds folder to comparison.'''
        raise NotImplementedError()
    
    @overload
    def add(self, file_path : str, load_options : groupdocs.comparison.options.LoadOptions) -> None:
        '''Adds file to comparison with loading options specified.
        
        :param file_path: Compared file path
        :param load_options: Load options'''
        raise NotImplementedError()
    
    @overload
    def add(self, document : io._IOBase) -> None:
        '''Adds document stream to comparison.
        
        :param document: Compared document stream'''
        raise NotImplementedError()
    
    @overload
    def add(self, document : io._IOBase, load_options : groupdocs.comparison.options.LoadOptions) -> None:
        '''Adds document stream to comparison with loading options specified.
        
        :param document: Compared document stream
        :param load_options: Load options'''
        raise NotImplementedError()
    
    @overload
    def get_changes(self) -> List[groupdocs.comparison.result.ChangeInfo]:
        '''Gets list of changes between source and target file(s).'''
        raise NotImplementedError()
    
    @overload
    def get_changes(self, get_change_options : groupdocs.comparison.options.GetChangeOptions) -> List[groupdocs.comparison.result.ChangeInfo]:
        '''Gets list of changes between source and target file(s).
        
        :param get_change_options: Get change options'''
        raise NotImplementedError()
    
    @overload
    def apply_changes(self, file_path : str, apply_change_options : groupdocs.comparison.options.ApplyChangeOptions) -> None:
        '''Accepts or rejects changes and applies them to resultant document.
        
        :param file_path: Result file path
        :param apply_change_options: Apply change options'''
        raise NotImplementedError()
    
    @overload
    def apply_changes(self, stream : io._IOBase, apply_change_options : groupdocs.comparison.options.ApplyChangeOptions) -> None:
        '''Accepts or rejects changes and applies them to resultant document.
        
        :param apply_change_options: Apply change options'''
        raise NotImplementedError()
    
    @overload
    def apply_changes(self, file_path : str, save_options : groupdocs.comparison.options.SaveOptions, apply_change_options : groupdocs.comparison.options.ApplyChangeOptions) -> None:
        '''Accepts or rejects changes and applies them to resultant document.
        
        :param file_path: Result file path
        :param save_options: Save options
        :param apply_change_options: Apply change options'''
        raise NotImplementedError()
    
    @overload
    def apply_changes(self, stream : io._IOBase, save_options : groupdocs.comparison.options.SaveOptions, apply_change_options : groupdocs.comparison.options.ApplyChangeOptions) -> None:
        '''Accepts or rejects changes and applies them to resultant document.
        
        :param save_options: Save options
        :param apply_change_options: Apply change options'''
        raise NotImplementedError()
    
    def get_result_document_stream(self) -> io._IOBase:
        '''Gets the stream of result document, returns null if stream does not exist'''
        raise NotImplementedError()
    
    def compare_directory(self, file_path : str, compare_options : groupdocs.comparison.options.CompareOptions) -> None:
        '''Compares directory and saves result to file path'''
        raise NotImplementedError()
    
    def get_result_string(self) -> str:
        '''Get result string after comparison (For Text Comparison only).'''
        raise NotImplementedError()
    
    @property
    def source(self) -> groupdocs.comparison.Document:
        '''Source file that is being compared.'''
        raise NotImplementedError()
    
    @property
    def source_folder(self) -> str:
        '''Source folder that is being compared.'''
        raise NotImplementedError()
    
    @property
    def targets(self) -> System.Collections.Generic.List`1[[GroupDocs.Comparison.Document]]:
        '''List of target files to compare with source file.'''
        raise NotImplementedError()
    
    @property
    def target_folder(self) -> str:
        '''Target folder that is being compared.'''
        raise NotImplementedError()
    
    @target_folder.setter
    def target_folder(self, value : str) -> None:
        '''Target folder that is being compared.'''
        raise NotImplementedError()
    
    @property
    def result(self) -> groupdocs.comparison.Document:
        '''Result document.'''
        raise NotImplementedError()
    

class ComparerSettings:
    '''Defines settings for customizing :py:class:`groupdocs.comparison.Comparer` behaviour.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def logger(self) -> groupdocs.comparison.logging.ILogger:
        '''Logger implementation.'''
        raise NotImplementedError()
    
    @logger.setter
    def logger(self, value : groupdocs.comparison.logging.ILogger) -> None:
        '''Logger implementation.'''
        raise NotImplementedError()
    

class Document:
    '''Represents compared document.'''
    
    @overload
    def __init__(self, stream : io._IOBase) -> None:
        '''Initializes new instance of :py:class:`groupdocs.comparison.Document` class.
        
        :param stream: Document stream'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_path : str) -> None:
        '''Initializes new instance of :py:class:`groupdocs.comparison.Document` class.
        
        :param file_path: Document path'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file_path : str, password : str) -> None:
        '''Initializes new instance of :py:class:`groupdocs.comparison.Document` class.
        
        :param file_path: Document path
        :param password: Document password'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, stream : io._IOBase, password : str) -> None:
        '''Initializes new instance of :py:class:`groupdocs.comparison.Document` class.
        
        :param stream: Document stream
        :param password: Document password'''
        raise NotImplementedError()
    
    def generate_preview(self, preview_options : groupdocs.comparison.options.PreviewOptions) -> None:
        '''Generates document pages preview.
        
        :param preview_options: The document preview options'''
        raise NotImplementedError()
    
    def get_document_info(self) -> groupdocs.comparison.interfaces.IDocumentInfo:
        '''Gets information about document - document type, pages count, page sizes etc.'''
        raise NotImplementedError()
    
    @property
    def changes(self) -> System.Collections.Generic.List`1[[GroupDocs.Comparison.Result.ChangeInfo]]:
        '''List of changes. Contains extensive description about change type, position, content etc.'''
        raise NotImplementedError()
    
    @changes.setter
    def changes(self, value : System.Collections.Generic.List`1[[GroupDocs.Comparison.Result.ChangeInfo]]) -> None:
        '''List of changes. Contains extensive description about change type, position, content etc.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Document name.'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Document name.'''
        raise NotImplementedError()
    
    @property
    def file_type(self) -> groupdocs.comparison.result.FileType:
        '''Document file type.'''
        raise NotImplementedError()
    
    @property
    def stream(self) -> io._IOBase:
        '''Document stream.'''
        raise NotImplementedError()
    
    @property
    def password(self) -> str:
        '''Document password.'''
        raise NotImplementedError()
    

class License:
    '''Provides methods to license the component.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @overload
    def set_license(self, license_stream : io._IOBase) -> None:
        '''Licenses the component using license stream.
        
        :param license_stream: The license stream.'''
        raise NotImplementedError()
    
    @overload
    def set_license(self, license_path : str) -> None:
        '''Licenses the component using license path.
        
        :param license_path: The license path.'''
        raise NotImplementedError()
    

class Metered:
    '''Provides methods for applying Metered license.'''
    
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`groupdocs.comparison.Metered` class.'''
        raise NotImplementedError()
    
    def set_metered_key(self, public_key : str, private_key : str) -> None:
        '''Sets metered public and private key
        
        :param public_key: public key
        :param private_key: private key'''
        raise NotImplementedError()
    
    @staticmethod
    def get_consumption_quantity() -> System.Decimal:
        '''Gets consumption quantity
        
        :returns: consumption quantity'''
        raise NotImplementedError()
    
    @staticmethod
    def get_consumption_credit() -> System.Decimal:
        '''Retrieves amount of used credits
        
        :returns: Number of already used credits'''
        raise NotImplementedError()
    

