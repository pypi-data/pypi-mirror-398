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

class ConsoleLogger(ILogger):
    '''Represents logger implementation which sends all messages to console.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def warning(self, message : str) -> None:
        '''Logs warning message.
        
        :param message: Warning message'''
        raise NotImplementedError()
    
    def trace(self, message : str) -> None:
        '''Logs the process of comparison.
        
        :param message: Log message'''
        raise NotImplementedError()
    

class ILogger:
    '''Logger interface.'''
    
    def warning(self, message : str) -> None:
        '''Warning message.
        
        :param message: The warning message'''
        raise NotImplementedError()
    
    def trace(self, message : str) -> None:
        '''Trace message.
        
        :param message: The message'''
        raise NotImplementedError()
    

