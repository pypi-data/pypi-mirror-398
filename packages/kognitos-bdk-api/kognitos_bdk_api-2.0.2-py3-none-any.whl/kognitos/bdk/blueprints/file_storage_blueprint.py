# type: ignore [reportReturnType]
from dataclasses import dataclass
from typing import IO, List, Optional, Union

from kognitos.bdk.api import FilterExpression
from kognitos.bdk.decorators import blueprint, blueprint_procedure, concept


@dataclass
@concept(is_a="file reference")
class FileReference:
    """
    Contains all information required to identify a file within a storage system
    """


@dataclass
@concept(is_a="folder reference")
class FolderReference:
    """
    Contains all information required to identify a folder within a storage system
    """


@blueprint
class FileStorageBlueprint:
    """
    A blueprint for files.
    """

    @blueprint_procedure("to get a (root folder)")
    def get_root_folder(self) -> FolderReference:
        """
        Gets a reference to the root folder.

        Returns:
            a folder reference
        """

    @blueprint_procedure("to get a (folder) at a path")
    def get_folder(self, path: str) -> FolderReference:
        """
        Gets a reference to a folder.

        Input Concepts:
            the path: The path to the folder

        Returns:
            a folder reference
        """

    @blueprint_procedure("to get some (folder's items)")
    def list_items(self, folder: FolderReference, filter_expression: Optional[FilterExpression] = None) -> List[Union[FileReference, FolderReference]]:
        """
        Lists items from a folder reference

        Input Concepts:
            the folder: The folder reference from which to list the items
            the filter expression: A filter expression to filter the items in the folder

        Returns:
            a list of Items (file or folder) containing the items in the folder
        """

    @blueprint_procedure("to rename an item to a name")
    def rename_item(self, item: Union[FileReference, FolderReference], name: str, conflict_behavior: Optional[str] = "fail") -> None:
        """
        Rename an item (file or folder) to a given name

        Input Concepts:
            the item: The item (file or folder) to rename
            the name: The new name of the item
            the conflict behavior: The behavior to use on conflict scenarios. It should be one of the following values: ('fail', 'replace', 'rename')
        """

    @blueprint_procedure("to delete an item")
    def delete_an_item(self, item: Union[FileReference, FolderReference]) -> None:
        """
        Delete an item (file or folder)

        Input Concepts:
            the item: The item (file or folder) to delete
        """

    @blueprint_procedure("to download a file")
    def download_item(self, file: FileReference) -> IO:
        """
        Download a file

        Input Concepts:
            the file: The file reference to the file to download

        Returns:
            the file as an IO object
        """

    @blueprint_procedure("to create a (folder) in another folder")
    def create_folder(self, another_folder: FolderReference, folder_name: str, conflict_behavior: Optional[str] = "fail") -> FolderReference:
        """
        Create a (folder) in another folder

        Input Concepts:
            the another folder: The folder to create the (folder) in
            the folder name: The name of the (folder) to create
            the conflict behavior: The behavior to use on conflict scenarios. It should be one of the following values: ('fail', 'replace', 'rename')

        Returns:
            a folder reference to the created folder
        """

    @blueprint_procedure("to upload a (file) to a folder")
    def upload_file_to_folder(self, file: IO, folder: FolderReference, file_name: str, conflict_behavior: Optional[str] = "fail") -> FileReference:
        """
        Upload a file to a folder

        Input Concepts:
            the file: The file to upload
            the folder: The folder to upload the file to
            the file name: The name of the file to upload
            the conflict behavior: The behavior to use on conflict scenarios. It should be one of the following values: ('fail', 'replace', 'rename')

        Returns:
            a file reference to the uploaded file
        """

    @blueprint_procedure("to copy an item to a folder")
    def copy_item(self, item: Union[FileReference, FolderReference], folder: FolderReference, conflict_behavior: Optional[str] = "fail") -> None:
        """
        Copy an item to a folder

        Input Concepts:
            the item: The item (file or folder) to copy
            the folder: The folder to copy the item to
            the conflict behavior: The behavior to use on conflict scenarios. It should be one of the following values: ('fail', 'replace', 'rename')
        """

    @blueprint_procedure("to move an item to a folder")
    def move_item(self, item: Union[FileReference, FolderReference], folder: FolderReference, conflict_behavior: Optional[str] = "fail") -> None:
        """
        Move an item to a folder

        Input Concepts:
            the item: The item (file or folder) to move
            the folder: The folder to move the item to
            the conflict behavior: The behavior to use on conflict scenarios. It should be one of the following values: ('fail', 'replace', 'rename')
        """
