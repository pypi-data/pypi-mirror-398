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

class ApplyRevisionOptions:
    '''Allows you to update the state of revisions before they are applied to the final document.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def changes(self) -> System.Collections.Generic.List`1[[GroupDocs.Comparison.Words.Revision.RevisionInfo]]:
        '''The list of revisions processed, which will be applied to the resulting document.'''
        raise NotImplementedError()
    
    @changes.setter
    def changes(self, value : System.Collections.Generic.List`1[[GroupDocs.Comparison.Words.Revision.RevisionInfo]]) -> None:
        '''The list of revisions processed, which will be applied to the resulting document.'''
        raise NotImplementedError()
    
    @property
    def common_handler(self) -> groupdocs.comparison.words.revision.RevisionAction:
        '''Indicates whether to apply one action for all revisions'''
        raise NotImplementedError()
    
    @common_handler.setter
    def common_handler(self, value : groupdocs.comparison.words.revision.RevisionAction) -> None:
        '''Indicates whether to apply one action for all revisions'''
        raise NotImplementedError()
    

class RevisionHandler:
    '''Represents the main class that controls revision handling.'''
    
    @overload
    def __init__(self, file_path : str) -> None:
        '''Initializes new instance of :py:class:`groupdocs.comparison.words.revision.RevisionHandler` class with the path to the file with revisions.
        
        :param file_path: File path'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, file : io._IOBase) -> None:
        '''Initializes new instance of :py:class:`groupdocs.comparison.words.revision.RevisionHandler` class with a file stream with revisions.
        
        :param file: Source document stream'''
        raise NotImplementedError()
    
    @overload
    def apply_revision_changes(self, changes : groupdocs.comparison.words.revision.ApplyRevisionOptions) -> None:
        '''Processes changes in revisions and applies them to the same file from which the revisions were taken.
        
        :param changes: List of changed revisions'''
        raise NotImplementedError()
    
    @overload
    def apply_revision_changes(self, file_path : str, changes : groupdocs.comparison.words.revision.ApplyRevisionOptions) -> None:
        '''Processes changes in revisions, and the result is written to the specified file by path.
        
        :param file_path: Result file path
        :param changes: List of changed revisions'''
        raise NotImplementedError()
    
    @overload
    def apply_revision_changes(self, document : io._IOBase, changes : groupdocs.comparison.words.revision.ApplyRevisionOptions) -> None:
        '''Processes changes in revisions and the result is written to the document stream.
        
        :param document: Result document
        :param changes: List of changed revisions'''
        raise NotImplementedError()
    
    def get_revisions(self) -> System.Collections.Generic.List`1[[GroupDocs.Comparison.Words.Revision.RevisionInfo]]:
        '''Gets list of all revisions.'''
        raise NotImplementedError()
    

class RevisionInfo:
    '''Provides information about one revision.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def action(self) -> groupdocs.comparison.words.revision.RevisionAction:
        '''Action (accept or reject). This field allows you to influence the display of the revision.'''
        raise NotImplementedError()
    
    @action.setter
    def action(self, value : groupdocs.comparison.words.revision.RevisionAction) -> None:
        '''Action (accept or reject). This field allows you to influence the display of the revision.'''
        raise NotImplementedError()
    
    @property
    def text(self) -> str:
        '''The text that is in revision.'''
        raise NotImplementedError()
    
    @property
    def author(self) -> str:
        '''Author of revision.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> groupdocs.comparison.words.revision.RevisionType:
        '''RevisionHandler type, depending on the type the Action (accept or reject) logic changes.'''
        raise NotImplementedError()
    

class RevisionAction:
    '''Action that can be applied to a revision.'''
    
    NONE : RevisionAction
    '''Nothing to do.'''
    ACCEPT : RevisionAction
    '''The revision will be displayed if it is of type INSERTION or will be removed if the type is DELETION.'''
    REJECT : RevisionAction
    '''The revision will be removed if it is of type INSERTION or will be displayed if the type is DELETION.'''

class RevisionType:
    '''Specifies the type of change being tracked.'''
    
    INSERTION : RevisionType
    '''New content was inserted in the document.'''
    DELETION : RevisionType
    '''Content was removed from the document.'''
    FORMAT_CHANGE : RevisionType
    '''Change of formatting was applied to the parent node.'''
    STYLE_DEFINITION_CHANGE : RevisionType
    '''Change of formatting was applied to the parent style.'''
    MOVING : RevisionType
    '''Content was moved in the document.'''

