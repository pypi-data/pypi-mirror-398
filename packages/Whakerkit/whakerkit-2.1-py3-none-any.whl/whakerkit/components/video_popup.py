# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.components.video_popup.py
:author: Brigitte Bigi
:contributor: Florian Lopitaux
:contact: contact@sppas.org
:summary: Class to create a custom video player with an image pre-visualization and video opened in a pop-up.

.. _This file is part of WhakerKit: https://whakerkit.sourceforge.io
.. _This file was originally part of SPPAS  - by Brigitte Bigi, CNRS.
    Integrated into WhakerKit 1.2.

    Copyright (C) 2011-2025  Brigitte Bigi, CNRS
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

    -------------------------------------------------------------------------

"""

import os
import logging
from whakerpy.htmlmaker import HTMLNode

# ---------------------------------------------------------------------------

image_extensions = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".ico"
)

# ---------------------------------------------------------------------------


class VideoPopupNode(HTMLNode):

    REQUIRED = ["dialog.css"]


    def __init__(self, parent_id: str, video_path: str, identifier: str, img_path: str = ""):
        """Create the VideoPopup html element and initialize all values.
        The video popup is a figure that contains an image and a play button to launch the video.
        When the user click on the button, open a popup (dialog element) with the video.
        This component allows us to manage the video files flow to avoid to load all files at the page loading.

        :param parent_id: The identifier of the parent
        :param video_path: The path of the video
        :param identifier: The identifier of this element (important to be different of other VideoPlayer identifiers in the same page)
        :param img_path: Optional, the file path of the image pre-visualization.
                         By default, search in the same path of the video, example :
                            - video_path : /example/demo_video.webm
                            - image_path search by default : /example/demo_video.{file_extension}

        :raises FileNotFoundError: If the video path doesn't exist

        """
        super(VideoPopupNode, self).__init__(parent_id, identifier, "figure")
        self.set_attribute("class", "img-video-visualization")

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"The video : {video_path} doesn't exists !")

        self.__video_path = video_path
        if img_path == "":
            self.__img_path = ""
            if not self.__find_image_preload():
                logging.warning("No given image path and the default image path doesn't exist")
        else:
            self.__img_path = img_path

        self.__width = None
        self.__height = None
        self.__create_elements()

    # -----------------------------------------------------------------------
    # SETTERS
    # -----------------------------------------------------------------------

    def set_img_path(self, img_path: str) -> None:
        """Set the image path of the video pre-visualization.
        If the image doesn't found raise a 'FileNotFoundError'.

        :param img_path: (str) The path of the video

        :raises FileNotFoundError: if the image on the given path doesn't exist

        """
        if os.path.exists(img_path):
            self.__img_path = img_path
            self.__img.set_attribute("src", self.__img_path)
        else:
            raise FileNotFoundError(f"The image pre-visualization : {img_path} doesn't exists !")

    # -----------------------------------------------------------------------

    def set_alt_description(self, description: str) -> None:
        """Set the alternative text description image pre-visualization.
        The text appear when the image can't display or if the user actives the narrator.

        :param description: (str) The alternative text description image

        """
        self.set_attribute("alt", description)

    # -----------------------------------------------------------------------

    def set_img_width(self, width: float, unit: str) -> None:
        """Set the width of the image pre-visualization.
        If the height is not defined set to auto.

        :param width: The value of the image width
        :param unit: The unit of the width (vw, %, em, rem, cm, mm, ...)

        """
        self.__width = (width, unit)
        size_css_value = f"width: {width}{unit};"

        if self.__height is None:
            size_css_value += " height: auto;"
        else:
            size_css_value += f" height: {self.__height[0]}{self.__height[1]};"

        self.set_attribute("style", size_css_value)

    # -----------------------------------------------------------------------

    def set_img_height(self, height: float, unit: str) -> None:
        """Set the height of the image pre-visualization.
        If the width is not defined set to auto.

        :param height: The value of the image height
        :param unit: The unit of the height (vh, %, em, rem, cm, mm, ...)

        """
        self.__height = (height, unit)
        size_css_value = f"height: {height}{unit};"

        if self.__width is None:
            size_css_value += " width: auto;"
        else:
            size_css_value += f" width: {self.__width[0]}{self.__width[1]};"

        self.set_attribute("style", size_css_value)

    # -----------------------------------------------------------------------
    # PRIVATE METHODS
    # -----------------------------------------------------------------------

    def __create_elements(self) -> None:
        """Create every html elements for the video : the play button and the popup with the video.

        """
        # create image pre-visualisation
        self.__img = HTMLNode(self.identifier, None, "img", attributes={"src": self.__img_path})
        self.append_child(self.__img)

        play_button = HTMLNode(self.identifier, None, "button", value="&#9658;",
                               attributes={"name": "play-btn", "onclick": f"play_popup_video('{self.identifier}')"})
        self.append_child(play_button)

        # create popup widget
        id_modal = f"popup-{self.identifier}"
        modal = HTMLNode(self.identifier, id_modal, "dialog", attributes={
            "id": id_modal,
            "class": "popup-video"
        })

        id_video = f"popup-video-{self.identifier}"
        video = HTMLNode(id_modal, id_video, "video", attributes={
            "id": id_video,
            "controls": "true",
            "preload": "none"
        })

        _, file_extension = os.path.splitext(self.__video_path)
        source = HTMLNode(id_video, None, "source", attributes={
            "src": self.__video_path,
            "type": f"video/{file_extension[1:]}"
        })

        video.append_child(source)
        modal.append_child(video)
        self.append_child(modal)

    # -----------------------------------------------------------------------

    def __find_image_preload(self) -> bool:
        """Search the default image pre-visualization for the video.

        For example, if the video has this path:
            'assets/video_example.mp4',
        then we attempt to find an image with this following path:
            'assets/video_example.jpg' (or other image formats).

        The image extension must be in the defined list.

        """
        path, _ = os.path.splitext(self.__video_path)

        for extension in image_extensions:
            final_path = path + extension

            if os.path.exists(final_path):
                self.__img_path = final_path
                return True

        return False
