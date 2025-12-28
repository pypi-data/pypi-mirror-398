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

class MergeType:
    '''Enumerates the type of cell merge.'''
    
    NONE : MergeType
    '''Cell does not merge.'''
    HORIZONTAL : MergeType
    '''Cell merges along row.'''
    VERTICAL : MergeType
    '''Cell merges along column.'''
    RANGE : MergeType
    '''Cell merges along row and column creating area.'''

