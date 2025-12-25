# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.nodes.card_node.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: HTMLNode for a card representing a document.

Copyright (C) 2024-2025 Brigitte Bigi, CNRS
Laboratoire Parole et Langage, Aix-en-Provence, France

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

This banner notice must not be removed.

"""

from whakerpy.htmlmaker import HTMLNode

import whakerkit
from whakerkit import get_msg

from ..documents import ImmutableDocument
from ..uploads_manager import WhakerKitDocsManager

from .download_node import WhakerKitDownloadNode

# ---------------------------------------------------------------------------


MSG_NAME = "Name: "
MSG_TYPE = "Type: "
MSG_WHO = "From: "
MSG_DATE = "On: "
MSG_DOWNLOAD = "Download /<span name=\"download-count\">{nb}</span>"

# ---------------------------------------------------------------------------


class WhakerKitDocumentCardNode(HTMLNode):
    """Node to represents details of a document into a card.
    
    """
    doc = whakerkit.sg.path + "statics/icons/doc.png"
    xls = whakerkit.sg.path + "statics/icons/excel.png"
    ppt = whakerkit.sg.path + "statics/icons/powerpoint.png"

    FILE_ICONS = {
        "pdf": whakerkit.sg.path + "statics/icons/pdf.png",
        "doc": doc,
        "docx": doc,
        "rtf": doc,
        "odt": doc,
        "ppt": ppt,
        "pptx": ppt,
        "odp": ppt,
        "xls": xls,
        "xlsx": xls,
        "ods": xls,
        "txt": whakerkit.sg.path + "statics/icons/txt.png",
        "md": whakerkit.sg.path + "statics/icons/txt.png",
        "code": whakerkit.sg.path + "statics/icons/code.png",
        "image": whakerkit.sg.path + "statics/icons/picture.png",
        "video": whakerkit.sg.path + "statics/icons/video.png",
        "default": whakerkit.sg.path + "statics/icons/file.png",
        "": whakerkit.sg.path + "statics/icons/file.png"
    }

    EXTENSIONS = {
        "video": ["mp4", "avi", "mkv", "mov", "webm"],
        "image": ["png", "jpg", "jpeg", "gif", "tif", "webp"],
        "code": ["html", "htm", "xhtml", "xml", "py", "js", "css", "php",
                 "java", "c", "cpp", "cs", "go", "rb", "pl", "sql", "json", 
                 "yaml", "yml", "toml", "ini", "cfg", "conf", "toml", "tex", "properties"]
          }
    
    # -----------------------------------------------------------------------

    def __init__(self, parent, doc: ImmutableDocument = None, doc_file_path: str = "#"):
        """Create the card node.

        :param parent: (str) The parent node identifier
        :param doc: (ImmutableDocument) The document to show details
        :param doc_file_path: (str) The file path of the document

        """
        author = doc.author.replace(whakerkit.sg.FIELDS_NAME_SEPARATOR, " ")
        icon_path = self.get_icon_path(doc.filetype)
        attributes = WhakerKitDocsManager.data_attributes(doc)

        super(WhakerKitDocumentCardNode, self).__init__(parent, doc.folder_name, "article", attributes=attributes)
        self.add_attribute("id", doc.folder_name)
        self.add_attribute("class", "card")

        # Header of the card: an icon representing the filetype
        header_card = HTMLNode(self.identifier, "header_card", "header")
        img_card = HTMLNode(header_card.identifier, None, "img", attributes={"src": icon_path, "alt": "file extension"})
        header_card.append_child(img_card)
        self.append_child(header_card)

        # Main of the card: the document information
        main_card = HTMLNode(self.identifier, "main_card", "main")
        WhakerKitDocumentCardNode.__add_info(main_card, " ".join(["<i>", get_msg(MSG_NAME), "</i><b>", doc.filename, "</b>"]))
        WhakerKitDocumentCardNode.__add_info(main_card, "<i>" + get_msg(MSG_WHO) + "</i>" + author)
        WhakerKitDocumentCardNode.__add_info(main_card, "<i>" + get_msg(MSG_DATE) + "</i>" + doc.date.strftime('%Y-%m-%d'))
        WhakerKitDocumentCardNode.__add_info(main_card, "<i>" + get_msg(MSG_TYPE) + "</i>" + doc.filetype)
        if len(doc.description) > 0:
            WhakerKitDocumentCardNode.__add_info(main_card, doc.description)
        self.append_child(main_card)

        # Footer of the card: a download button indicating the number of downloads
        footer_card = HTMLNode(self.identifier, "footer_card", "footer")
        btn = WhakerKitDownloadNode(footer_card.identifier,
                                    href=doc_file_path,
                                    folder_name=doc.folder_name,
                                    text=get_msg(MSG_DOWNLOAD).format(nb=doc.downloads))
        btn.add_attribute("class", "btn_download")
        footer_card.append_child(btn)
        self.append_child(footer_card)

    # -----------------------------------------------------------------------

    @staticmethod
    def get_icon_path(extension: str) -> str:
        """Get the image extension for the file.

        :param extension: (str) The extension of the file without the dot
        :return: (str) The icon path

        """
        extension = extension.lower()

        if extension in WhakerKitDocumentCardNode.FILE_ICONS:
            return WhakerKitDocumentCardNode.FILE_ICONS[extension]
        if extension in WhakerKitDocumentCardNode.EXTENSIONS["image"]:
            return WhakerKitDocumentCardNode.FILE_ICONS["image"]
        if extension in WhakerKitDocumentCardNode.EXTENSIONS["code"]:
            return WhakerKitDocumentCardNode.FILE_ICONS["code"]

        return WhakerKitDocumentCardNode.FILE_ICONS["default"]

    # -----------------------------------------------------------------------

    @staticmethod
    def __add_info(parent: HTMLNode, value=""):
        """Add a paragraph to the card."""
        p = HTMLNode(parent.identifier, None, "span", value=value)
        parent.append_child(p)
