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

class ApplyChangeOptions:
    '''Allows to update the list of changes before applying them to the resulting document.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def changes(self) -> List[groupdocs.comparison.result.ChangeInfo]:
        '''List of changes that must be applied to the resulting document.'''
        raise NotImplementedError()
    
    @changes.setter
    def changes(self, value : List[groupdocs.comparison.result.ChangeInfo]) -> None:
        '''List of changes that must be applied to the resulting document.'''
        raise NotImplementedError()
    
    @property
    def save_original_state(self) -> bool:
        '''After applying the changes, keep the original state of the compared result.'''
        raise NotImplementedError()
    
    @save_original_state.setter
    def save_original_state(self, value : bool) -> None:
        '''After applying the changes, keep the original state of the compared result.'''
        raise NotImplementedError()
    

class CompareOptions:
    '''Allows to set different compare options.'''
    
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`groupdocs.comparison.options.CompareOptions` class.'''
        raise NotImplementedError()
    
    @property
    def paper_size(self) -> groupdocs.comparison.options.PaperSize:
        '''Gets the result document paper size.'''
        raise NotImplementedError()
    
    @paper_size.setter
    def paper_size(self, value : groupdocs.comparison.options.PaperSize) -> None:
        '''Sets the result document paper size.'''
        raise NotImplementedError()
    
    @property
    def show_deleted_content(self) -> bool:
        '''Indicates whether to show deleted components in resultant document or not.'''
        raise NotImplementedError()
    
    @show_deleted_content.setter
    def show_deleted_content(self, value : bool) -> None:
        '''Indicates whether to show deleted components in resultant document or not.'''
        raise NotImplementedError()
    
    @property
    def show_inserted_content(self) -> bool:
        '''Indicates whether to show inserted components in resultant document or not.'''
        raise NotImplementedError()
    
    @show_inserted_content.setter
    def show_inserted_content(self, value : bool) -> None:
        '''Indicates whether to show inserted components in resultant document or not.'''
        raise NotImplementedError()
    
    @property
    def generate_summary_page(self) -> bool:
        '''Indicates whether to add summary page with detected changes statistics to resultant document or not.'''
        raise NotImplementedError()
    
    @generate_summary_page.setter
    def generate_summary_page(self, value : bool) -> None:
        '''Indicates whether to add summary page with detected changes statistics to resultant document or not.'''
        raise NotImplementedError()
    
    @property
    def extended_summary_page(self) -> bool:
        '''Indicates whether to add extended file comparison information to the summary page or not.'''
        raise NotImplementedError()
    
    @extended_summary_page.setter
    def extended_summary_page(self, value : bool) -> None:
        '''Indicates whether to add extended file comparison information to the summary page or not.'''
        raise NotImplementedError()
    
    @property
    def show_only_summary_page(self) -> bool:
        '''Indicates whether to leave in the resulting document only a page with statistics of detected changes in the resulting document or not.'''
        raise NotImplementedError()
    
    @show_only_summary_page.setter
    def show_only_summary_page(self, value : bool) -> None:
        '''Indicates whether to leave in the resulting document only a page with statistics of detected changes in the resulting document or not.'''
        raise NotImplementedError()
    
    @property
    def detect_style_changes(self) -> bool:
        '''Indicates whether to detect style changes or not.'''
        raise NotImplementedError()
    
    @detect_style_changes.setter
    def detect_style_changes(self, value : bool) -> None:
        '''Indicates whether to detect style changes or not.'''
        raise NotImplementedError()
    
    @property
    def mark_nested_content(self) -> bool:
        '''Gets a value indicating whether to mark the children of the deleted or inserted element as deleted or inserted.'''
        raise NotImplementedError()
    
    @mark_nested_content.setter
    def mark_nested_content(self, value : bool) -> None:
        '''Sets a value indicating whether to mark the children of the deleted or inserted element as deleted or inserted.'''
        raise NotImplementedError()
    
    @property
    def calculate_coordinates(self) -> bool:
        '''Indicates whether to calculate coordinates for changed components.'''
        raise NotImplementedError()
    
    @calculate_coordinates.setter
    def calculate_coordinates(self, value : bool) -> None:
        '''Indicates whether to calculate coordinates for changed components.'''
        raise NotImplementedError()
    
    @property
    def calculate_coordinates_mode(self) -> groupdocs.comparison.options.CalculateCoordinatesModeEnumeration:
        '''Specifies the coordinate calculation for changed components mode.'''
        raise NotImplementedError()
    
    @calculate_coordinates_mode.setter
    def calculate_coordinates_mode(self, value : groupdocs.comparison.options.CalculateCoordinatesModeEnumeration) -> None:
        '''Specifies the coordinate calculation for changed components mode.'''
        raise NotImplementedError()
    
    @property
    def header_footers_comparison(self) -> bool:
        '''Control to turn on comparison of header/footer contents.'''
        raise NotImplementedError()
    
    @header_footers_comparison.setter
    def header_footers_comparison(self, value : bool) -> None:
        '''Control to turn on comparison of header/footer contents.'''
        raise NotImplementedError()
    
    @property
    def detalisation_level(self) -> groupdocs.comparison.options.DetalisationLevel:
        '''Gets the comparison detail level.'''
        raise NotImplementedError()
    
    @detalisation_level.setter
    def detalisation_level(self, value : groupdocs.comparison.options.DetalisationLevel) -> None:
        '''Sets the comparison detail level.'''
        raise NotImplementedError()
    
    @property
    def mark_changed_content(self) -> bool:
        '''Indicates whether to use frames for shapes in Word Processing and for rectangles in Image documents.'''
        raise NotImplementedError()
    
    @mark_changed_content.setter
    def mark_changed_content(self, value : bool) -> None:
        '''Indicates whether to use frames for shapes in Word Processing and for rectangles in Image documents.'''
        raise NotImplementedError()
    
    @property
    def inserted_item_style(self) -> groupdocs.comparison.options.StyleSettings:
        '''Describes style for inserted components.'''
        raise NotImplementedError()
    
    @inserted_item_style.setter
    def inserted_item_style(self, value : groupdocs.comparison.options.StyleSettings) -> None:
        '''Describes style for inserted components.'''
        raise NotImplementedError()
    
    @property
    def deleted_item_style(self) -> groupdocs.comparison.options.StyleSettings:
        '''Describes style for deleted components.'''
        raise NotImplementedError()
    
    @deleted_item_style.setter
    def deleted_item_style(self, value : groupdocs.comparison.options.StyleSettings) -> None:
        '''Describes style for deleted components.'''
        raise NotImplementedError()
    
    @property
    def changed_item_style(self) -> groupdocs.comparison.options.StyleSettings:
        '''Describes style for changed components.'''
        raise NotImplementedError()
    
    @changed_item_style.setter
    def changed_item_style(self, value : groupdocs.comparison.options.StyleSettings) -> None:
        '''Describes style for changed components.'''
        raise NotImplementedError()
    
    @property
    def mark_line_breaks(self) -> bool:
        '''Gets a value indicating whether to mark line breaks.'''
        raise NotImplementedError()
    
    @mark_line_breaks.setter
    def mark_line_breaks(self, value : bool) -> None:
        '''Sets a value indicating whether to mark line breaks.'''
        raise NotImplementedError()
    
    @property
    def compare_images_pdf(self) -> bool:
        '''Control to turn on comparison of images in PDF format.'''
        raise NotImplementedError()
    
    @compare_images_pdf.setter
    def compare_images_pdf(self, value : bool) -> None:
        '''Control to turn on comparison of images in PDF format.'''
        raise NotImplementedError()
    
    @property
    def images_inheritance_mode(self) -> groupdocs.comparison.options.ImagesInheritance:
        '''Specifies the source of images inheritance when image comparison is disabled.'''
        raise NotImplementedError()
    
    @images_inheritance_mode.setter
    def images_inheritance_mode(self, value : groupdocs.comparison.options.ImagesInheritance) -> None:
        '''Specifies the source of images inheritance when image comparison is disabled.'''
        raise NotImplementedError()
    
    @property
    def compare_bookmarks(self) -> bool:
        '''Control to turn on comparison of bookmarks in Word format.'''
        raise NotImplementedError()
    
    @compare_bookmarks.setter
    def compare_bookmarks(self, value : bool) -> None:
        '''Control to turn on comparison of bookmarks in Word format.'''
        raise NotImplementedError()
    
    @property
    def compare_variable_property(self) -> bool:
        '''Control to turn on comparison of variables properties in Word format.'''
        raise NotImplementedError()
    
    @compare_variable_property.setter
    def compare_variable_property(self, value : bool) -> None:
        '''Control to turn on comparison of variables properties in Word format.'''
        raise NotImplementedError()
    
    @property
    def compare_document_property(self) -> bool:
        '''Control to turn on comparison of built and custom properties in Word format.'''
        raise NotImplementedError()
    
    @compare_document_property.setter
    def compare_document_property(self, value : bool) -> None:
        '''Control to turn on comparison of built and custom properties in Word format.'''
        raise NotImplementedError()
    
    @property
    def word_track_changes(self) -> bool:
        '''Control to turn on comparison of Words Track Revisions.'''
        raise NotImplementedError()
    
    @word_track_changes.setter
    def word_track_changes(self, value : bool) -> None:
        '''Control to turn on comparison of Words Track Revisions.'''
        raise NotImplementedError()
    
    @property
    def show_only_changed(self) -> bool:
        '''Controls to enable the display of only changed items.'''
        raise NotImplementedError()
    
    @show_only_changed.setter
    def show_only_changed(self, value : bool) -> None:
        '''Controls to enable the display of only changed items.'''
        raise NotImplementedError()
    
    @property
    def directory_compare(self) -> bool:
        '''Control to turn on comparison of folders.'''
        raise NotImplementedError()
    
    @directory_compare.setter
    def directory_compare(self, value : bool) -> None:
        '''Control to turn on comparison of folders.'''
        raise NotImplementedError()
    
    @property
    def user_master_path(self) -> str:
        '''Path to user master\'s template for Diagrams.'''
        raise NotImplementedError()
    
    @user_master_path.setter
    def user_master_path(self, value : str) -> None:
        '''Path to user master\'s template for Diagrams.'''
        raise NotImplementedError()
    
    @property
    def folder_comparison_extension(self) -> groupdocs.comparison.options.FolderComparisonExtension:
        '''Gets the format of the resulting folder comparison file.'''
        raise NotImplementedError()
    
    @folder_comparison_extension.setter
    def folder_comparison_extension(self, value : groupdocs.comparison.options.FolderComparisonExtension) -> None:
        '''Sets the format of the resulting folder comparison file.'''
        raise NotImplementedError()
    
    @property
    def revision_author_name(self) -> str:
        '''Gets revision author name. Enabled if not null.'''
        raise NotImplementedError()
    
    @revision_author_name.setter
    def revision_author_name(self, value : str) -> None:
        '''Sets revision author name. Enabled if not null.'''
        raise NotImplementedError()
    
    @property
    def sensitivity_of_comparison(self) -> int:
        '''Gets a sensitivity of comparison.'''
        raise NotImplementedError()
    
    @sensitivity_of_comparison.setter
    def sensitivity_of_comparison(self, value : int) -> None:
        '''Sets a sensitivity of comparison.'''
        raise NotImplementedError()
    
    @property
    def sensitivity_of_comparison_for_tables(self) -> System.Nullable`1[[System.Int32]]:
        '''Gets a sensitivity of comparison for tables.'''
        raise NotImplementedError()
    
    @sensitivity_of_comparison_for_tables.setter
    def sensitivity_of_comparison_for_tables(self, value : System.Nullable`1[[System.Int32]]) -> None:
        '''Sets a sensitivity of comparison for tables.'''
        raise NotImplementedError()
    
    @property
    def ignore_change_settings(self) -> groupdocs.comparison.options.IgnoreChangeSensitivitySettings:
        '''Gets settings to ignore changes based on similarity.'''
        raise NotImplementedError()
    
    @ignore_change_settings.setter
    def ignore_change_settings(self, value : groupdocs.comparison.options.IgnoreChangeSensitivitySettings) -> None:
        '''Sets settings to ignore changes based on similarity.'''
        raise NotImplementedError()
    
    @property
    def password_save_option(self) -> groupdocs.comparison.options.PasswordSaveOption:
        '''Gets the password save option.'''
        raise NotImplementedError()
    
    @password_save_option.setter
    def password_save_option(self, value : groupdocs.comparison.options.PasswordSaveOption) -> None:
        '''Sets the password save option.'''
        raise NotImplementedError()
    
    @property
    def original_size(self) -> groupdocs.comparison.options.OriginalSize:
        '''Get the original sizes of compared documents.'''
        raise NotImplementedError()
    
    @original_size.setter
    def original_size(self, value : groupdocs.comparison.options.OriginalSize) -> None:
        '''Get or sets the original sizes of compared documents.'''
        raise NotImplementedError()
    
    @property
    def diagram_master_setting(self) -> groupdocs.comparison.options.DiagramMasterSetting:
        '''Gets the path value for master or use compare without path of master. This option only for Diagram.'''
        raise NotImplementedError()
    
    @diagram_master_setting.setter
    def diagram_master_setting(self, value : groupdocs.comparison.options.DiagramMasterSetting) -> None:
        '''Sets the path value for master or use compare without path of master. This option only for Diagram.'''
        raise NotImplementedError()
    
    @property
    def show_revisions(self) -> bool:
        '''Indicates whether to display others revisions in the resulting document or not.'''
        raise NotImplementedError()
    
    @show_revisions.setter
    def show_revisions(self, value : bool) -> None:
        '''Indicates whether to display others revisions in the resulting document or not.'''
        raise NotImplementedError()
    
    @property
    def leave_gaps(self) -> bool:
        '''Indicates whether to display empty lines instead of inserted / deleted components in the final document or not (used with ShowInsertedContent or ShowDeletedContent properties).'''
        raise NotImplementedError()
    
    @leave_gaps.setter
    def leave_gaps(self, value : bool) -> None:
        '''Indicates whether to display empty lines instead of inserted / deleted components in the final document or not (used with ShowInsertedContent or ShowDeletedContent properties).'''
        raise NotImplementedError()
    

class DiagramMasterSetting:
    '''Diagram master settings.'''
    
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`groupdocs.comparison.options.DiagramMasterSetting` class.'''
        raise NotImplementedError()
    
    @property
    def use_source_master(self) -> bool:
        '''Set true for use master with source document or use false value for use Master with Path .'''
        raise NotImplementedError()
    
    @use_source_master.setter
    def use_source_master(self, value : bool) -> None:
        '''Set true for use master with source document or use false value for use Master with Path .'''
        raise NotImplementedError()
    
    @property
    def master_path(self) -> str:
        '''Path for Master. Set this value or use default Comparison Master. MasterPath is needed to create a document result from a set of default shapes.'''
        raise NotImplementedError()
    
    @master_path.setter
    def master_path(self, value : str) -> None:
        '''Path for Master. Set this value or use default Comparison Master. MasterPath is needed to create a document result from a set of default shapes.'''
        raise NotImplementedError()
    

class FileAuthorMetadata:
    '''Information about document\'s author metadata.'''
    
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`groupdocs.comparison.options.FileAuthorMetadata` class.'''
        raise NotImplementedError()
    
    @property
    def author(self) -> str:
        '''Gets the author.'''
        raise NotImplementedError()
    
    @author.setter
    def author(self, value : str) -> None:
        '''Sets the author.'''
        raise NotImplementedError()
    
    @property
    def last_save_by(self) -> str:
        '''Gets the last save by.'''
        raise NotImplementedError()
    
    @last_save_by.setter
    def last_save_by(self, value : str) -> None:
        '''Sets the last save by.'''
        raise NotImplementedError()
    
    @property
    def company(self) -> str:
        '''Gets the company.'''
        raise NotImplementedError()
    
    @company.setter
    def company(self, value : str) -> None:
        '''Sets the company.'''
        raise NotImplementedError()
    

class GetChangeOptions:
    '''The option allows to filter changes by type.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def filter(self) -> groupdocs.comparison.options.ChangeType:
        '''Type of changes.'''
        raise NotImplementedError()
    
    @filter.setter
    def filter(self, value : groupdocs.comparison.options.ChangeType) -> None:
        '''Type of changes.'''
        raise NotImplementedError()
    

class IgnoreChangeSensitivitySettings:
    '''The option allows to ignore changes by similarity percentage.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def ignore(self) -> bool:
        '''Set ignore option to true or false.'''
        raise NotImplementedError()
    
    @ignore.setter
    def ignore(self, value : bool) -> None:
        '''Set ignore option to true or false.'''
        raise NotImplementedError()
    
    @property
    def ignore_percent(self) -> int:
        '''Gets a sensitivity for ignoring changes.
        Ignores the change if the similarity is less than the specified value.'''
        raise NotImplementedError()
    
    @ignore_percent.setter
    def ignore_percent(self, value : int) -> None:
        '''Sets a sensitivity for ignoring changes.
        Ignores the change if the similarity is less than the specified value.'''
        raise NotImplementedError()
    

class LoadOptions:
    '''Allows to specify additional options when loading a document.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def password(self) -> str:
        '''Password of document.'''
        raise NotImplementedError()
    
    @password.setter
    def password(self, value : str) -> None:
        '''Password of document.'''
        raise NotImplementedError()
    
    @property
    def font_directories(self) -> System.Collections.Generic.List`1[[System.String]]:
        '''List of font directories to load.'''
        raise NotImplementedError()
    
    @font_directories.setter
    def font_directories(self, value : System.Collections.Generic.List`1[[System.String]]) -> None:
        '''List of font directories to load.'''
        raise NotImplementedError()
    
    @property
    def load_text(self) -> bool:
        '''Indicates that the strings passed are comparison text, not file paths (For Text Comparison only).'''
        raise NotImplementedError()
    
    @load_text.setter
    def load_text(self, value : bool) -> None:
        '''Indicates that the strings passed are comparison text, not file paths (For Text Comparison only).'''
        raise NotImplementedError()
    
    @property
    def file_type(self) -> groupdocs.comparison.result.FileType:
        '''Manually set the file type for comparison to override automatic file type detection.'''
        raise NotImplementedError()
    
    @file_type.setter
    def file_type(self, value : groupdocs.comparison.result.FileType) -> None:
        '''Manually set the file type for comparison to override automatic file type detection.'''
        raise NotImplementedError()
    

class OriginalSize:
    '''Represents original page size. Used only for comparing image with different formats.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''Width of original document'''
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : int) -> None:
        '''Width of original document'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''Height of original document'''
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : int) -> None:
        '''Height of original document'''
        raise NotImplementedError()
    

class PreviewOptions:
    '''Represents document preview options.'''
    
    @property
    def width(self) -> int:
        '''Preview width.'''
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : int) -> None:
        '''Preview width.'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''Preview height.'''
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : int) -> None:
        '''Preview height.'''
        raise NotImplementedError()
    
    @property
    def page_numbers(self) -> List[int]:
        '''Page numbers that will be previewed.'''
        raise NotImplementedError()
    
    @page_numbers.setter
    def page_numbers(self, value : List[int]) -> None:
        '''Page numbers that will be previewed.'''
        raise NotImplementedError()
    
    @property
    def preview_format(self) -> groupdocs.comparison.options.PreviewFormats:
        '''Preview image format.'''
        raise NotImplementedError()
    
    @preview_format.setter
    def preview_format(self, value : groupdocs.comparison.options.PreviewFormats) -> None:
        '''Preview image format.'''
        raise NotImplementedError()
    

class SaveOptions:
    '''Allows to specify additional options (such as password) when saving a document.'''
    
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`groupdocs.comparison.options.SaveOptions` class.'''
        raise NotImplementedError()
    
    @property
    def clone_metadata_type(self) -> groupdocs.comparison.options.MetadataType:
        '''Gets a value indicating whether to clone metadata to target document or not.'''
        raise NotImplementedError()
    
    @clone_metadata_type.setter
    def clone_metadata_type(self, value : groupdocs.comparison.options.MetadataType) -> None:
        '''Sets a value indicating whether to clone metadata to target document or not.'''
        raise NotImplementedError()
    
    @property
    def file_author_metadata(self) -> groupdocs.comparison.options.FileAuthorMetadata:
        '''Used when MetadataType is set to FileAuthor.'''
        raise NotImplementedError()
    
    @file_author_metadata.setter
    def file_author_metadata(self, value : groupdocs.comparison.options.FileAuthorMetadata) -> None:
        '''Used when MetadataType is set to FileAuthor.'''
        raise NotImplementedError()
    
    @property
    def password(self) -> str:
        '''Gets the password for result document.'''
        raise NotImplementedError()
    
    @password.setter
    def password(self, value : str) -> None:
        '''Sets the password for result document.'''
        raise NotImplementedError()
    
    @property
    def folder_path(self) -> str:
        '''Gets the folder path for saving result images(For Imaging Comparison only).'''
        raise NotImplementedError()
    
    @folder_path.setter
    def folder_path(self, value : str) -> None:
        '''Sets the folder path for saving result images(For Imaging Comparison only).'''
        raise NotImplementedError()
    

class Size:
    '''Document size.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def width(self) -> int:
        '''Width of original document.'''
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : int) -> None:
        '''Width of original document.'''
        raise NotImplementedError()
    
    @property
    def height(self) -> int:
        '''Height of original document.'''
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : int) -> None:
        '''Height of original document.'''
        raise NotImplementedError()
    

class StyleSettings:
    '''Style settings. Allows to define style rules for changes. Used in :py:class:`groupdocs.comparison.options.CompareOptions` class.'''
    
    def __init__(self) -> None:
        '''Initializes a new instance of the :py:class:`groupdocs.comparison.options.StyleSettings` class.'''
        raise NotImplementedError()
    
    @property
    def font_color(self) -> aspose.pydrawing.Color:
        '''Gets the font color.'''
        raise NotImplementedError()
    
    @font_color.setter
    def font_color(self, value : aspose.pydrawing.Color) -> None:
        '''Sets the font color.'''
        raise NotImplementedError()
    
    @property
    def shape_color(self) -> aspose.pydrawing.Color:
        '''Gets the shape color. If not set, then the FontColor color is used.'''
        raise NotImplementedError()
    
    @shape_color.setter
    def shape_color(self, value : aspose.pydrawing.Color) -> None:
        '''Sets the shape color. If not set, then the FontColor color is used.'''
        raise NotImplementedError()
    
    @property
    def boarder_color(self) -> aspose.pydrawing.Color:
        '''Gets the boarder color. If not set, then the FontColor color is used.'''
        raise NotImplementedError()
    
    @boarder_color.setter
    def boarder_color(self, value : aspose.pydrawing.Color) -> None:
        '''Sets the boarder color. If not set, then the FontColor color is used.'''
        raise NotImplementedError()
    
    @property
    def highlight_color(self) -> aspose.pydrawing.Color:
        '''Gets the highlight color.'''
        raise NotImplementedError()
    
    @highlight_color.setter
    def highlight_color(self, value : aspose.pydrawing.Color) -> None:
        '''Sets the highlight color.'''
        raise NotImplementedError()
    
    @property
    def is_bold(self) -> bool:
        '''Gets a value indicating whether this is bold.'''
        raise NotImplementedError()
    
    @is_bold.setter
    def is_bold(self, value : bool) -> None:
        '''Sets a value indicating whether this is bold.'''
        raise NotImplementedError()
    
    @property
    def is_underline(self) -> bool:
        '''Gets a value indicating whether this is underline.'''
        raise NotImplementedError()
    
    @is_underline.setter
    def is_underline(self, value : bool) -> None:
        '''Sets a value indicating whether this is underline.'''
        raise NotImplementedError()
    
    @property
    def is_italic(self) -> bool:
        '''Gets a value indicating whether this is italic.'''
        raise NotImplementedError()
    
    @is_italic.setter
    def is_italic(self, value : bool) -> None:
        '''Sets a value indicating whether this is italic.'''
        raise NotImplementedError()
    
    @property
    def is_strikethrough(self) -> bool:
        '''Gets a value indicating whether strike through.'''
        raise NotImplementedError()
    
    @is_strikethrough.setter
    def is_strikethrough(self, value : bool) -> None:
        '''Sets a value indicating whether strike through.'''
        raise NotImplementedError()
    
    @property
    def start_string_separator(self) -> str:
        '''Gets the begin separator string.'''
        raise NotImplementedError()
    
    @start_string_separator.setter
    def start_string_separator(self, value : str) -> None:
        '''Sets the begin separator string.'''
        raise NotImplementedError()
    
    @property
    def end_string_separator(self) -> str:
        '''Gets the end separator string.'''
        raise NotImplementedError()
    
    @end_string_separator.setter
    def end_string_separator(self, value : str) -> None:
        '''Sets the end separator string.'''
        raise NotImplementedError()
    
    @property
    def original_size(self) -> groupdocs.comparison.options.Size:
        '''Get the original sizes of comparing documents.'''
        raise NotImplementedError()
    
    @original_size.setter
    def original_size(self, value : groupdocs.comparison.options.Size) -> None:
        '''Get or sets the original sizes of comparing documents.'''
        raise NotImplementedError()
    
    @property
    def words_separators(self) -> List[System.Char]:
        '''Gets the words separator chars.'''
        raise NotImplementedError()
    
    @words_separators.setter
    def words_separators(self, value : List[System.Char]) -> None:
        '''Sets the words separator chars.'''
        raise NotImplementedError()
    

class CalculateCoordinatesModeEnumeration:
    '''Enumerates the type of coordinates calculation.'''
    
    SOURCE : CalculateCoordinatesModeEnumeration
    '''Calculate coordinates of source elements.'''
    TARGET : CalculateCoordinatesModeEnumeration
    '''Calculate coordinates of target elements.'''
    RESULT : CalculateCoordinatesModeEnumeration
    '''Calculate coordinates of result elements (default).'''

class ChangeType:
    '''Specifies change type.'''
    
    NONE : ChangeType
    '''The none.'''
    MODIFIED : ChangeType
    '''The modified.'''
    INSERTED : ChangeType
    '''The inserted.'''
    DELETED : ChangeType
    '''The deleted.'''
    ADDED : ChangeType
    '''The added.'''
    NOT_MODIFIED : ChangeType
    '''The not modified.'''
    STYLE_CHANGED : ChangeType
    '''Style changed.'''
    RESIZED : ChangeType
    '''Resized.'''
    MOVED : ChangeType
    '''Moved.'''
    MOVED_AND_RESIZED : ChangeType
    '''The moved and resized.'''
    SHIFTED_AND_RESIZED : ChangeType
    '''The shifted and resized.'''

class DetalisationLevel:
    '''Specifies the level of comparison details.'''
    
    LOW : DetalisationLevel
    '''Low level. Provides the best speed comparison sacrificing comparison quality.
    Comparison is perfromed per-word.'''
    MIDDLE : DetalisationLevel
    '''Middle level. A reasonable compromise between comparison speed and quality.
    Comparison is perfromed per-character, but ignoring character case and spaces count.'''
    HIGH : DetalisationLevel
    '''High level. The best comparison quality, but the lowest speed.
    Comparison is perfromed per-character considering character case and spaces count.'''

class FolderComparisonExtension:
    '''Folder extensions.'''
    
    HTML : FolderComparisonExtension
    '''HTML.'''
    TXT : FolderComparisonExtension
    '''TXT.'''

class ImagesInheritance:
    '''Source of images inheritance when image comparison is disabled.'''
    
    SOURCE : ImagesInheritance
    '''Inherit images from source document.'''
    TARGET : ImagesInheritance
    '''Inherit images from target document.'''

class MetadataType:
    '''Determines from where result document will take metadata information'''
    
    DEFAULT : MetadataType
    '''Default'''
    SOURCE : MetadataType
    '''Metedata takes from source document'''
    TARGET : MetadataType
    '''Metadata takes from target document'''
    FILE_AUTHOR : MetadataType
    '''Metadata sets by user'''

class PaperSize:
    '''The option to set the Paper size of the result document after comparison.'''
    
    DEFAULT : PaperSize
    '''Default'''
    A0 : PaperSize
    '''A0'''
    A1 : PaperSize
    '''A1'''
    A2 : PaperSize
    '''A2'''
    A3 : PaperSize
    '''A3'''
    A4 : PaperSize
    '''A4'''
    A5 : PaperSize
    '''A5'''
    A6 : PaperSize
    '''A6'''
    A7 : PaperSize
    '''A7'''
    A8 : PaperSize
    '''A8'''

class PasswordSaveOption:
    '''Specifies the password save option.'''
    
    NONE : PasswordSaveOption
    '''Default password.'''
    SOURCE : PasswordSaveOption
    '''Source password.'''
    TARGET : PasswordSaveOption
    '''Target password.'''
    USER : PasswordSaveOption
    '''The user password.'''

class PreviewFormats:
    '''Document preview supported formats.'''
    
    PNG : PreviewFormats
    '''Png (by default), can be take a lot of disc space / traffic if page contains a lot of color graphics.'''
    JPEG : PreviewFormats
    '''Jpeg - faster processing, small disc space using / traffic, but can be worst quality.'''
    BMP : PreviewFormats
    '''BMP - slow processing, high disc space usage / traffic, but best quality.'''

