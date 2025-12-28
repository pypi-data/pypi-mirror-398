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

class ChangeInfo:
    '''Represents information about change.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        '''Id of change.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : int) -> None:
        '''Id of change.'''
        raise NotImplementedError()
    
    @property
    def comparison_action(self) -> groupdocs.comparison.result.ComparisonAction:
        '''Action (accept or reject). This field tells comparison what to do with this change.'''
        raise NotImplementedError()
    
    @comparison_action.setter
    def comparison_action(self, value : groupdocs.comparison.result.ComparisonAction) -> None:
        '''Action (accept or reject). This field tells comparison what to do with this change.'''
        raise NotImplementedError()
    
    @property
    def page_info(self) -> groupdocs.comparison.result.PageInfo:
        '''Page where current change is placed.'''
        raise NotImplementedError()
    
    @page_info.setter
    def page_info(self, value : groupdocs.comparison.result.PageInfo) -> None:
        '''Page where current change is placed.'''
        raise NotImplementedError()
    
    @property
    def box(self) -> groupdocs.comparison.result.Rectangle:
        '''Coordinates of changed element.'''
        raise NotImplementedError()
    
    @box.setter
    def box(self, value : groupdocs.comparison.result.Rectangle) -> None:
        '''Coordinates of changed element.'''
        raise NotImplementedError()
    
    @property
    def text(self) -> str:
        '''Text value of change.'''
        raise NotImplementedError()
    
    @text.setter
    def text(self, value : str) -> None:
        '''Text value of change.'''
        raise NotImplementedError()
    
    @property
    def style_changes(self) -> List[groupdocs.comparison.result.StyleChangeInfo]:
        '''Array of style changes.'''
        raise NotImplementedError()
    
    @style_changes.setter
    def style_changes(self, value : List[groupdocs.comparison.result.StyleChangeInfo]) -> None:
        '''Array of style changes.'''
        raise NotImplementedError()
    
    @property
    def authors(self) -> System.Collections.Generic.List`1[[System.String]]:
        '''List of Authors.'''
        raise NotImplementedError()
    
    @authors.setter
    def authors(self, value : System.Collections.Generic.List`1[[System.String]]) -> None:
        '''List of Authors.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> groupdocs.comparison.options.ChangeType:
        '''Type of change.'''
        raise NotImplementedError()
    
    @property
    def target_text(self) -> str:
        '''Changed text of target document.'''
        raise NotImplementedError()
    
    @target_text.setter
    def target_text(self, value : str) -> None:
        '''Changed text of target document.'''
        raise NotImplementedError()
    
    @property
    def source_text(self) -> str:
        '''Changed text of source document.'''
        raise NotImplementedError()
    
    @source_text.setter
    def source_text(self, value : str) -> None:
        '''Changed text of source document.'''
        raise NotImplementedError()
    
    @property
    def component_type(self) -> str:
        '''Type of changed component.'''
        raise NotImplementedError()
    
    @component_type.setter
    def component_type(self, value : str) -> None:
        '''Type of changed component.'''
        raise NotImplementedError()
    

class FileType:
    '''Represents file type. Provides methods to obtain list of all file types supported by GroupDocs.Comparison, detect file type by extension etc.'''
    
    @staticmethod
    def from_file_name_or_extension(file_name_or_extension : str) -> groupdocs.comparison.result.FileType:
        '''Return FileType based on file name or extension
        
        :param file_name_or_extension: File name or extension'''
        raise NotImplementedError()
    
    @staticmethod
    def get_supported_file_types() -> System.Collections.Generic.IEnumerable`1[[GroupDocs.Comparison.Result.FileType]]:
        '''Get supported file types enumeration
        
        :returns: Enumeration of FileType'''
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.comparison.result.FileType) -> bool:
        '''File type equivalence check
        
        :param other: FileType object
        :returns: True if file types are equivalent, false if not'''
        raise NotImplementedError()
    
    @property
    def file_format(self) -> str:
        '''File format'''
        raise NotImplementedError()
    
    @property
    def extension(self) -> str:
        '''File extention'''
        raise NotImplementedError()
    
    @property
    def UNKNOWN(self) -> groupdocs.comparison.result.FileType:
        '''Unknown type'''
        raise NotImplementedError()

    @property
    def AS(self) -> groupdocs.comparison.result.FileType:
        '''ActionScript Programming Language format'''
        raise NotImplementedError()

    @property
    def AS3(self) -> groupdocs.comparison.result.FileType:
        '''ActionScript Programming Language format'''
        raise NotImplementedError()

    @property
    def ASM(self) -> groupdocs.comparison.result.FileType:
        '''ASM format'''
        raise NotImplementedError()

    @property
    def BAT(self) -> groupdocs.comparison.result.FileType:
        '''Script file in DOS, OS/2 and Microsoft Windows'''
        raise NotImplementedError()

    @property
    def CMD(self) -> groupdocs.comparison.result.FileType:
        '''Script file in DOS, OS/2 and Microsoft Windows'''
        raise NotImplementedError()

    @property
    def C(self) -> groupdocs.comparison.result.FileType:
        '''C-Based Programming Language format'''
        raise NotImplementedError()

    @property
    def H(self) -> groupdocs.comparison.result.FileType:
        '''C-Based header files contain definitions of Functions and Variables'''
        raise NotImplementedError()

    @property
    def PDF(self) -> groupdocs.comparison.result.FileType:
        '''Adobe Portable Document format'''
        raise NotImplementedError()

    @property
    def DOC(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft Word 97-2003 Document'''
        raise NotImplementedError()

    @property
    def DOCM(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft Word Macro-Enabled Document'''
        raise NotImplementedError()

    @property
    def DOCX(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft Word Document'''
        raise NotImplementedError()

    @property
    def DOT(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft Word 97-2003 Template'''
        raise NotImplementedError()

    @property
    def DOTM(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft Word Macro-Enabled Template'''
        raise NotImplementedError()

    @property
    def DOTX(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft Word Template'''
        raise NotImplementedError()

    @property
    def XLS(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft Excel 97-2003 Worksheet'''
        raise NotImplementedError()

    @property
    def XLT(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft Excel template'''
        raise NotImplementedError()

    @property
    def XLSX(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft Excel Worksheet'''
        raise NotImplementedError()

    @property
    def XLTM(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft Excel macro-enabled template'''
        raise NotImplementedError()

    @property
    def XLSB(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft Excel Binary Worksheet'''
        raise NotImplementedError()

    @property
    def XLSM(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft Excel Macro-Enabled Worksheet'''
        raise NotImplementedError()

    @property
    def POT(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft PowerPoint template'''
        raise NotImplementedError()

    @property
    def POTX(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft PowerPoint Template'''
        raise NotImplementedError()

    @property
    def PPS(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft PowerPoint 97-2003 Slide Show'''
        raise NotImplementedError()

    @property
    def PPSX(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft PowerPoint Slide Show'''
        raise NotImplementedError()

    @property
    def PPTX(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft PowerPoint Presentation'''
        raise NotImplementedError()

    @property
    def PPT(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft PowerPoint 97-2003 Presentation'''
        raise NotImplementedError()

    @property
    def VSDX(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft Visio Drawing'''
        raise NotImplementedError()

    @property
    def VSD(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft Visio 2003-2010 Drawing'''
        raise NotImplementedError()

    @property
    def VSS(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft Visio 2003-2010 Stencil'''
        raise NotImplementedError()

    @property
    def VST(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft Visio 2003-2010 Template'''
        raise NotImplementedError()

    @property
    def VDX(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft Visio 2003-2010 XML Drawing'''
        raise NotImplementedError()

    @property
    def ONE(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft OneNote Document'''
        raise NotImplementedError()

    @property
    def ODT(self) -> groupdocs.comparison.result.FileType:
        '''OpenDocument Text'''
        raise NotImplementedError()

    @property
    def ODP(self) -> groupdocs.comparison.result.FileType:
        '''OpenDocument Presentation'''
        raise NotImplementedError()

    @property
    def OTP(self) -> groupdocs.comparison.result.FileType:
        '''OpenDocument Presentation Template'''
        raise NotImplementedError()

    @property
    def ODS(self) -> groupdocs.comparison.result.FileType:
        '''OpenDocument Spreadsheet'''
        raise NotImplementedError()

    @property
    def OTT(self) -> groupdocs.comparison.result.FileType:
        '''OpenDocument Text Template'''
        raise NotImplementedError()

    @property
    def RTF(self) -> groupdocs.comparison.result.FileType:
        '''Rich Text Document'''
        raise NotImplementedError()

    @property
    def TXT(self) -> groupdocs.comparison.result.FileType:
        '''Plain Text Document'''
        raise NotImplementedError()

    @property
    def CSV(self) -> groupdocs.comparison.result.FileType:
        '''Comma Separated Values File'''
        raise NotImplementedError()

    @property
    def HTML(self) -> groupdocs.comparison.result.FileType:
        '''HyperText Markup Language'''
        raise NotImplementedError()

    @property
    def MHTML(self) -> groupdocs.comparison.result.FileType:
        '''Mime HTML'''
        raise NotImplementedError()

    @property
    def MOBI(self) -> groupdocs.comparison.result.FileType:
        '''Mobipocket e-book format'''
        raise NotImplementedError()

    @property
    def DCM(self) -> groupdocs.comparison.result.FileType:
        '''Digital Imaging and Communications in Medicine'''
        raise NotImplementedError()

    @property
    def DJVU(self) -> groupdocs.comparison.result.FileType:
        '''Deja Vu format'''
        raise NotImplementedError()

    @property
    def DWG(self) -> groupdocs.comparison.result.FileType:
        '''Autodesk Design Data Formats'''
        raise NotImplementedError()

    @property
    def DXF(self) -> groupdocs.comparison.result.FileType:
        '''AutoCAD Drawing Interchange'''
        raise NotImplementedError()

    @property
    def BMP(self) -> groupdocs.comparison.result.FileType:
        '''Bitmap Picture'''
        raise NotImplementedError()

    @property
    def GIF(self) -> groupdocs.comparison.result.FileType:
        '''Graphics Interchange Format'''
        raise NotImplementedError()

    @property
    def JPEG(self) -> groupdocs.comparison.result.FileType:
        '''Joint Photographic Experts Group'''
        raise NotImplementedError()

    @property
    def PNG(self) -> groupdocs.comparison.result.FileType:
        '''Portable Network Graphics'''
        raise NotImplementedError()

    @property
    def SVG(self) -> groupdocs.comparison.result.FileType:
        '''Scalar Vector Graphics'''
        raise NotImplementedError()

    @property
    def EML(self) -> groupdocs.comparison.result.FileType:
        '''E-mail Message'''
        raise NotImplementedError()

    @property
    def EMLX(self) -> groupdocs.comparison.result.FileType:
        '''Apple Mail E-mail File'''
        raise NotImplementedError()

    @property
    def MSG(self) -> groupdocs.comparison.result.FileType:
        '''Microsoft Outlook E-mail Message'''
        raise NotImplementedError()

    @property
    def CAD(self) -> groupdocs.comparison.result.FileType:
        '''CAD file format'''
        raise NotImplementedError()

    @property
    def CPP(self) -> groupdocs.comparison.result.FileType:
        '''C-Based Programming Language format'''
        raise NotImplementedError()

    @property
    def CC(self) -> groupdocs.comparison.result.FileType:
        '''C-Based Programming Language format'''
        raise NotImplementedError()

    @property
    def CXX(self) -> groupdocs.comparison.result.FileType:
        '''C-Based Programming Language format'''
        raise NotImplementedError()

    @property
    def HXX(self) -> groupdocs.comparison.result.FileType:
        '''Header Files that are written in the C++ programming language'''
        raise NotImplementedError()

    @property
    def HH(self) -> groupdocs.comparison.result.FileType:
        '''Header information referenced by a C++ source code file'''
        raise NotImplementedError()

    @property
    def HPP(self) -> groupdocs.comparison.result.FileType:
        '''Header Files that are written in the C++ programming language'''
        raise NotImplementedError()

    @property
    def CMAKE(self) -> groupdocs.comparison.result.FileType:
        '''Tool for managing the build process of software'''
        raise NotImplementedError()

    @property
    def CS(self) -> groupdocs.comparison.result.FileType:
        '''CSharp Programming Language format'''
        raise NotImplementedError()

    @property
    def CSX(self) -> groupdocs.comparison.result.FileType:
        '''CSharp script file format'''
        raise NotImplementedError()

    @property
    def CAKE(self) -> groupdocs.comparison.result.FileType:
        '''CSharp cross-platform build automation system format'''
        raise NotImplementedError()

    @property
    def DIFF(self) -> groupdocs.comparison.result.FileType:
        '''Data comparison tool format'''
        raise NotImplementedError()

    @property
    def PATCH(self) -> groupdocs.comparison.result.FileType:
        '''List of differences format'''
        raise NotImplementedError()

    @property
    def REJ(self) -> groupdocs.comparison.result.FileType:
        '''Rejected files format'''
        raise NotImplementedError()

    @property
    def GROOVY(self) -> groupdocs.comparison.result.FileType:
        '''Source code file written in Groovy format'''
        raise NotImplementedError()

    @property
    def GVY(self) -> groupdocs.comparison.result.FileType:
        '''Source code file written in Groovy format'''
        raise NotImplementedError()

    @property
    def GRADLE(self) -> groupdocs.comparison.result.FileType:
        '''Build-automation system format'''
        raise NotImplementedError()

    @property
    def HAML(self) -> groupdocs.comparison.result.FileType:
        '''Markup language for simplified HTML generation'''
        raise NotImplementedError()

    @property
    def JS(self) -> groupdocs.comparison.result.FileType:
        '''JavaScript Programming Language format'''
        raise NotImplementedError()

    @property
    def ES6(self) -> groupdocs.comparison.result.FileType:
        '''JavaScript standardised scripting language format'''
        raise NotImplementedError()

    @property
    def MJS(self) -> groupdocs.comparison.result.FileType:
        '''Extension for EcmaScript (ES) module files'''
        raise NotImplementedError()

    @property
    def PAC(self) -> groupdocs.comparison.result.FileType:
        '''Proxy Auto-Configuration file for JavaScript function format'''
        raise NotImplementedError()

    @property
    def JSON(self) -> groupdocs.comparison.result.FileType:
        '''Lightweight format for storing and transporting data'''
        raise NotImplementedError()

    @property
    def BOWERRC(self) -> groupdocs.comparison.result.FileType:
        '''Configuration file for package control on the server-side'''
        raise NotImplementedError()

    @property
    def JSHINTRC(self) -> groupdocs.comparison.result.FileType:
        '''JavaScript code quality tool'''
        raise NotImplementedError()

    @property
    def JSCSRC(self) -> groupdocs.comparison.result.FileType:
        '''JavaScript configuration file format'''
        raise NotImplementedError()

    @property
    def WEBMANIFEST(self) -> groupdocs.comparison.result.FileType:
        '''Manifest file includes information about the app'''
        raise NotImplementedError()

    @property
    def JSMAP(self) -> groupdocs.comparison.result.FileType:
        '''JSON file that contains information on how to translate code back to source code'''
        raise NotImplementedError()

    @property
    def HAR(self) -> groupdocs.comparison.result.FileType:
        '''The HTTP Archive format'''
        raise NotImplementedError()

    @property
    def JAVA(self) -> groupdocs.comparison.result.FileType:
        '''Java Programming Language format'''
        raise NotImplementedError()

    @property
    def LESS(self) -> groupdocs.comparison.result.FileType:
        '''Dynamic preprocessor style sheet language format'''
        raise NotImplementedError()

    @property
    def LOG(self) -> groupdocs.comparison.result.FileType:
        '''Logging keeps a registry of events, processes, messages and communication'''
        raise NotImplementedError()

    @property
    def MAKE(self) -> groupdocs.comparison.result.FileType:
        '''Makefile is a file containing a set of directives used by a make build automation tool to generate a target/goal'''
        raise NotImplementedError()

    @property
    def MK(self) -> groupdocs.comparison.result.FileType:
        '''Makefile is a file containing a set of directives used by a make build automation tool to generate a target/goal'''
        raise NotImplementedError()

    @property
    def MD(self) -> groupdocs.comparison.result.FileType:
        '''Markdown Language format'''
        raise NotImplementedError()

    @property
    def MKD(self) -> groupdocs.comparison.result.FileType:
        '''Markdown Language format'''
        raise NotImplementedError()

    @property
    def MDWN(self) -> groupdocs.comparison.result.FileType:
        '''Markdown Language format'''
        raise NotImplementedError()

    @property
    def MDOWN(self) -> groupdocs.comparison.result.FileType:
        '''Markdown Language format'''
        raise NotImplementedError()

    @property
    def MARKDOWN(self) -> groupdocs.comparison.result.FileType:
        '''Markdown Language format'''
        raise NotImplementedError()

    @property
    def MARKDN(self) -> groupdocs.comparison.result.FileType:
        '''Markdown Language format'''
        raise NotImplementedError()

    @property
    def MDTXT(self) -> groupdocs.comparison.result.FileType:
        '''Markdown Language format'''
        raise NotImplementedError()

    @property
    def MDTEXT(self) -> groupdocs.comparison.result.FileType:
        '''Markdown Language format'''
        raise NotImplementedError()

    @property
    def ML(self) -> groupdocs.comparison.result.FileType:
        '''Caml Programming Language format'''
        raise NotImplementedError()

    @property
    def MLI(self) -> groupdocs.comparison.result.FileType:
        '''Caml Programming Language format'''
        raise NotImplementedError()

    @property
    def OBJC(self) -> groupdocs.comparison.result.FileType:
        '''Objective-C Programming Language format'''
        raise NotImplementedError()

    @property
    def OBJCP(self) -> groupdocs.comparison.result.FileType:
        '''Objective-C++ Programming Language format'''
        raise NotImplementedError()

    @property
    def PHP(self) -> groupdocs.comparison.result.FileType:
        '''PHP Programming Language format'''
        raise NotImplementedError()

    @property
    def PHP4(self) -> groupdocs.comparison.result.FileType:
        '''PHP Programming Language format'''
        raise NotImplementedError()

    @property
    def PHP5(self) -> groupdocs.comparison.result.FileType:
        '''PHP Programming Language format'''
        raise NotImplementedError()

    @property
    def PHTML(self) -> groupdocs.comparison.result.FileType:
        '''Standard file extension for PHP 2 programs format'''
        raise NotImplementedError()

    @property
    def CTP(self) -> groupdocs.comparison.result.FileType:
        '''CakePHP Template format'''
        raise NotImplementedError()

    @property
    def PL(self) -> groupdocs.comparison.result.FileType:
        '''Perl Programming Language format'''
        raise NotImplementedError()

    @property
    def PM(self) -> groupdocs.comparison.result.FileType:
        '''Perl module format'''
        raise NotImplementedError()

    @property
    def POD(self) -> groupdocs.comparison.result.FileType:
        '''Perl lightweight markup language format'''
        raise NotImplementedError()

    @property
    def T(self) -> groupdocs.comparison.result.FileType:
        '''Perl test file format'''
        raise NotImplementedError()

    @property
    def PSGI(self) -> groupdocs.comparison.result.FileType:
        '''Interface between web servers and web applications and frameworks written in the Perl programming'''
        raise NotImplementedError()

    @property
    def P6(self) -> groupdocs.comparison.result.FileType:
        '''Perl Programming Language format'''
        raise NotImplementedError()

    @property
    def PL6(self) -> groupdocs.comparison.result.FileType:
        '''Perl Programming Language format'''
        raise NotImplementedError()

    @property
    def PM6(self) -> groupdocs.comparison.result.FileType:
        '''Perl module format'''
        raise NotImplementedError()

    @property
    def NQP(self) -> groupdocs.comparison.result.FileType:
        '''Intermediate language used to build the Rakudo Perl 6 compiler'''
        raise NotImplementedError()

    @property
    def PROP(self) -> groupdocs.comparison.result.FileType:
        '''Properties file format'''
        raise NotImplementedError()

    @property
    def CFG(self) -> groupdocs.comparison.result.FileType:
        '''Configuration file used for storing settings'''
        raise NotImplementedError()

    @property
    def CONF(self) -> groupdocs.comparison.result.FileType:
        '''Configuration file used on Unix and Linux based systems'''
        raise NotImplementedError()

    @property
    def DIR(self) -> groupdocs.comparison.result.FileType:
        '''Directory is a location for storing files on computer'''
        raise NotImplementedError()

    @property
    def PY(self) -> groupdocs.comparison.result.FileType:
        '''Python Programming Language format'''
        raise NotImplementedError()

    @property
    def RPY(self) -> groupdocs.comparison.result.FileType:
        '''Python-based file engine to create and run games'''
        raise NotImplementedError()

    @property
    def PYW(self) -> groupdocs.comparison.result.FileType:
        '''Files used in Windows to indicate a script needs to be run'''
        raise NotImplementedError()

    @property
    def CPY(self) -> groupdocs.comparison.result.FileType:
        '''Controller Python Script format'''
        raise NotImplementedError()

    @property
    def GYP(self) -> groupdocs.comparison.result.FileType:
        '''Build automation tool format'''
        raise NotImplementedError()

    @property
    def GYPI(self) -> groupdocs.comparison.result.FileType:
        '''Build automation tool format'''
        raise NotImplementedError()

    @property
    def PYI(self) -> groupdocs.comparison.result.FileType:
        '''Python Interface file format'''
        raise NotImplementedError()

    @property
    def IPY(self) -> groupdocs.comparison.result.FileType:
        '''IPython Script format'''
        raise NotImplementedError()

    @property
    def RST(self) -> groupdocs.comparison.result.FileType:
        '''Lightweight markup language'''
        raise NotImplementedError()

    @property
    def RB(self) -> groupdocs.comparison.result.FileType:
        '''Ruby Programming Language format'''
        raise NotImplementedError()

    @property
    def ERB(self) -> groupdocs.comparison.result.FileType:
        '''Ruby Programming Language format'''
        raise NotImplementedError()

    @property
    def RJS(self) -> groupdocs.comparison.result.FileType:
        '''Ruby Programming Language format'''
        raise NotImplementedError()

    @property
    def GEMSPEC(self) -> groupdocs.comparison.result.FileType:
        '''Developer file that specifies the attributes of a RubyGems'''
        raise NotImplementedError()

    @property
    def RAKE(self) -> groupdocs.comparison.result.FileType:
        '''Ruby build automation tool'''
        raise NotImplementedError()

    @property
    def RU(self) -> groupdocs.comparison.result.FileType:
        '''Rack configuration file format'''
        raise NotImplementedError()

    @property
    def PODSPEC(self) -> groupdocs.comparison.result.FileType:
        '''Ruby build settings format'''
        raise NotImplementedError()

    @property
    def RBI(self) -> groupdocs.comparison.result.FileType:
        '''Ruby Interface file format'''
        raise NotImplementedError()

    @property
    def SASS(self) -> groupdocs.comparison.result.FileType:
        '''Style sheet language format'''
        raise NotImplementedError()

    @property
    def SCSS(self) -> groupdocs.comparison.result.FileType:
        '''Style sheet language format'''
        raise NotImplementedError()

    @property
    def SCALA(self) -> groupdocs.comparison.result.FileType:
        '''Scala Programming Language format'''
        raise NotImplementedError()

    @property
    def SBT(self) -> groupdocs.comparison.result.FileType:
        '''SBT build tool for Scala format'''
        raise NotImplementedError()

    @property
    def SC(self) -> groupdocs.comparison.result.FileType:
        '''Scala worksheet format'''
        raise NotImplementedError()

    @property
    def SH(self) -> groupdocs.comparison.result.FileType:
        '''Script programmed for bash format'''
        raise NotImplementedError()

    @property
    def BASH(self) -> groupdocs.comparison.result.FileType:
        '''Type of interpreter that processes shell commands'''
        raise NotImplementedError()

    @property
    def BASHRC(self) -> groupdocs.comparison.result.FileType:
        '''File determines the behavior of interactive shells'''
        raise NotImplementedError()

    @property
    def EBUILD(self) -> groupdocs.comparison.result.FileType:
        '''Specialized bash script which automates compilation and installation procedures for software packages'''
        raise NotImplementedError()

    @property
    def SQL(self) -> groupdocs.comparison.result.FileType:
        '''Structured Query Language format'''
        raise NotImplementedError()

    @property
    def DSQL(self) -> groupdocs.comparison.result.FileType:
        '''Dynamic Structured Query Language format'''
        raise NotImplementedError()

    @property
    def VIM(self) -> groupdocs.comparison.result.FileType:
        '''Vim source code file format'''
        raise NotImplementedError()

    @property
    def YAML(self) -> groupdocs.comparison.result.FileType:
        '''Human-readable data-serialization language format'''
        raise NotImplementedError()

    @property
    def YML(self) -> groupdocs.comparison.result.FileType:
        '''Human-readable data-serialization language format'''
        raise NotImplementedError()


class PageInfo:
    '''Represents information about page\'s size and number.'''
    
    def __init__(self, page_number : int, width : int, height : int) -> None:
        '''Create new Instance of PageInfo
        
        :param page_number: The Page Number
        :param width: Width of Page
        :param height: Height of Page'''
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''Page width'''
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : int) -> None:
        '''Page width'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''Page height'''
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : int) -> None:
        '''Page height'''
        raise NotImplementedError()
    
    @property
    def page_number(self) -> int:
        '''Page number'''
        raise NotImplementedError()
    
    @page_number.setter
    def page_number(self, value : int) -> None:
        '''Page number'''
        raise NotImplementedError()
    

class Rectangle:
    '''Rectangle model.'''
    
    @overload
    def __init__(self, x : float, y : float, width : float, height : float) -> None:
        '''Creates a new instance of Rectangle
        
        :param x: X position of rectangle
        :param y: Y position of Rectangle
        :param width: Width of Rectangle
        :param height: Height of Rectangle'''
        raise NotImplementedError()
    
    @overload
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        '''Height'''
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : float) -> None:
        '''Height'''
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        '''Width'''
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : float) -> None:
        '''Width'''
        raise NotImplementedError()
    
    @property
    def x(self) -> float:
        '''X coordinate'''
        raise NotImplementedError()
    
    @x.setter
    def x(self, value : float) -> None:
        '''X coordinate'''
        raise NotImplementedError()
    
    @property
    def y(self) -> float:
        '''Y coordinate'''
        raise NotImplementedError()
    
    @y.setter
    def y(self, value : float) -> None:
        '''Y coordinate'''
        raise NotImplementedError()
    

class StyleChangeInfo:
    '''Represents information about style change.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def equals(self, other : groupdocs.comparison.result.StyleChangeInfo) -> bool:
        '''Style change equivalence check.
        
        :param other: StyleChangeInfo object'''
        raise NotImplementedError()
    
    @property
    def property_name(self) -> str:
        '''Gets or Sets the name of the property that was changed.'''
        raise NotImplementedError()
    
    @property_name.setter
    def property_name(self, value : str) -> None:
        '''Gets or Sets the name of the property that was changed.'''
        raise NotImplementedError()
    
    @property
    def new_value(self) -> Any:
        '''Gets or Sets the new value of property.'''
        raise NotImplementedError()
    
    @new_value.setter
    def new_value(self, value : Any) -> None:
        '''Gets or Sets the new value of property.'''
        raise NotImplementedError()
    
    @property
    def old_value(self) -> Any:
        '''Gets or Sets the old value of property.'''
        raise NotImplementedError()
    
    @old_value.setter
    def old_value(self, value : Any) -> None:
        '''Gets or Sets the old value of property.'''
        raise NotImplementedError()
    

class ComparisonAction:
    '''An action that can be applied to change.'''
    
    NONE : ComparisonAction
    '''Nothing to do'''
    ACCEPT : ComparisonAction
    '''Change will be visible on result file'''
    REJECT : ComparisonAction
    '''Reject will be invisible on result file'''

