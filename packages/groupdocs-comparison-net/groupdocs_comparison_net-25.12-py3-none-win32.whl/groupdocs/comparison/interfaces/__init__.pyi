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

class IDocumentInfo:
    '''Defines document description properties.'''
    
    @property
    def file_type(self) -> groupdocs.comparison.result.FileType:
        '''Represents file type. Provides methods to obtain list of all file types supported by GroupDocs.Comparison, detect file type by extension etc.'''
        raise NotImplementedError()
    
    @file_type.setter
    def file_type(self, value : groupdocs.comparison.result.FileType) -> None:
        '''Represents file type. Provides methods to obtain list of all file types supported by GroupDocs.Comparison, detect file type by extension etc.'''
        raise NotImplementedError()
    
    @property
    def page_count(self) -> int:
        '''Number of pages in document.'''
        raise NotImplementedError()
    
    @page_count.setter
    def page_count(self, value : int) -> None:
        '''Number of pages in document.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''File size.'''
        raise NotImplementedError()
    
    @size.setter
    def size(self, value : int) -> None:
        '''File size.'''
        raise NotImplementedError()
    
    @property
    def pages_info(self) -> System.Collections.Generic.List`1[[GroupDocs.Comparison.Result.PageInfo]]:
        '''Pages Information (Page Number, Width, Height).'''
        raise NotImplementedError()
    
    @pages_info.setter
    def pages_info(self, value : System.Collections.Generic.List`1[[GroupDocs.Comparison.Result.PageInfo]]) -> None:
        '''Pages Information (Page Number, Width, Height).'''
        raise NotImplementedError()
    

