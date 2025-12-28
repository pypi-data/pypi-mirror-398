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

class SupportedLocales:
    '''Class that provides methods for checking supported locales of GroupDocs.Comparison.'''
    
    @staticmethod
    def is_locale_supported(culture : str) -> bool:
        '''Determines whether the locale is supported.
        
        :param culture: The culture.'''
        raise NotImplementedError()
    

