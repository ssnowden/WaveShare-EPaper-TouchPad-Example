#!/usr/bin/python
# -*- coding:utf-8 -*-
from collections import namedtuple
from itertools import zip_longest
import os
from typing import Tuple
from PIL import Image, ImageDraw, ImageFont
import sys
import threading
import time
import traceback

from lib.TP_lib import gt1151
from lib.TP_lib import epd2in13_V2

import logging

logging.basicConfig(level=logging.DEBUG)
logging.info("############### epd2in13_V2 Touch Demo #######################")

# Functions -------------------------------------------------------
def pthread_irq():
    logging.debug("pthread running")
    while thread_running:
        touch_current.Touch = 1 if touch_pad.digital_read(touch_pad.INT) == 0 else 0
    logging.debug("pthread:exit")


def show_photo_small(image, start_index):
    """This function displays a set of images

    attributes:
        image: the image that has a new image posted into it. Strange way of doing it
        but may prove quick
        start_index: the images_small index to start the display from
    """
    image_positions = photo_list_view[5:]
    display_images = SMALL_IMAGES[start_index + 1 :]

    for image_position, display_image in zip_longest(image_positions, display_images):
        if image_position:
            try:
                newimage = Image.open(os.path.join(PICTURE_DIRECTORY, display_image))
            except IOError as exception:
                logging.info(exception)
                newimage = Image.open(os.path.join(PICTURE_DIRECTORY, SMALL_IMAGES[0]))

            image.paste(newimage, (image_position[0], image_position[1]))


def show_photo_large(image, index):
    """This function displays a single image

    attributes:
        image: the image that has a new image posted into it. Strange way of doing it
        but may prove quick
        index: the images_large index of the image to be displayed from the list of images
    """
    try:
        newimage = Image.open(os.path.join(PICTURE_DIRECTORY, LARGE_IMAGES[index]))
    except IOError as exception:
        logging.info(exception)
        newimage = Image.open(os.path.join(PICTURE_DIRECTORY, LARGE_IMAGES[0]))
    except KeyError:
        newimage = Image.open(os.path.join(PICTURE_DIRECTORY, LARGE_IMAGES[0]))

    image.paste(newimage, (2, 2))


def display_menu(File, x, y):
    """This function displays a menu

    attributes:
        File: the base image for the menu
        x, y: position for the image
    """
    newimage = Image.open(os.path.join(PICTURE_DIRECTORY, File))
    image.paste(newimage, (x, y))


def perform_partial_refresh(page, user_refresh):
    """This function does a partial refresh on the display

    attributes:
        page: Current page
        user_refresh: User refresh required.
    """
    if page == WHITE_BOARD_MENU and not user_refresh:
        e_paper.display_partial_image(e_paper.get_buffer(image))
    else:
        e_paper.display_partial_image_wait(e_paper.get_buffer(image))
    e_paper.touch_count_since_refresh = 0
    e_paper.loop_count_since_refresh = 0
    e_paper.refresh = False
    e_paper.full_update_refresh_count += 1


def perform_full_refresh():
    """This function does a full refresh on the display

    attributes:
    """
    e_paper.update()
    e_paper.display_full_page_image(e_paper.get_buffer(image))
    e_paper.full_update_refresh_count = 0
    e_paper.update(True)


def whiteboard_draw(touch_current, draw_context):
    """This function draws on the display on the display

    attributes:
        touch_current: Current touch event
        draw_context: Where the drawing will be performed.
    """
    draw_context.rectangle(
        [
            (touch_current.X[0], touch_current.Y[0]),
            (
                touch_current.X[0] + touch_current.S[0] / 8 + 1,
                touch_current.Y[0] + touch_current.S[0] / 8 + 1,
            ),
        ],
        fill=0,
    )


def display_refresh(page, user_refresh):
    if e_paper.refresh:
        perform_partial_refresh(page, user_refresh)
        logging.info("*** Draw Refresh ***\r\n")
    elif e_paper.touch_count_since_refresh > MAX_TOUCH_COUNT_SINCE_REFRESH:
        perform_partial_refresh(page, user_refresh)
        logging.info("*** Max Touch Refresh ***\r\n")
    elif (
        e_paper.loop_count_since_refresh > MAX_LOOPS_SINCE_REFRESH
        and e_paper.touch_count_since_refresh
        and page == WHITE_BOARD_MENU
    ):
        perform_partial_refresh(page, user_refresh)
        logging.info("*** Whiteboard Max Loops Refresh ***\r\n")
    elif e_paper.full_update_refresh_count > MAX_REFRESH_BEFORE_FULL_UPDATE:
        perform_full_refresh()
        logging.info("--- Auto Full Refresh ---\r\n")
    elif user_refresh:
        perform_full_refresh()
        user_refresh = False
        logging.info("--- User Full Refresh ---\r\n")
    else:
        e_paper.loop_count_since_refresh += 1

    return user_refresh


# Menu Options --------------------------------------------------------
def main_menu_event(current_view):
    """This function manages the main menu

    attributes:
        current_view: The current view that defines the touch hotspots
    """
    if (
        current_view[0].bottom > touch_current.X[0] > current_view[0].top
        and current_view[0].left > touch_current.Y[0] > current_view[0].right
    ):
        logging.info(f"{current_view[0].name} ...\r\n")
        display_menu(MENUS[PHOTO_LIST_MENU], 0, 0)
        show_photo_small(image, small_photo_to_display)
        e_paper.refresh = True
        return PHOTO_LIST_MENU
    elif (
        current_view[1].bottom > touch_current.X[0] > current_view[1].top
        and current_view[1].left > touch_current.Y[0] > current_view[1].right
    ):
        logging.info(f"{current_view[1].name} ...\r\n")
        display_menu(MENUS[WHITE_BOARD_MENU], 0, 0)
        e_paper.refresh = True
        return WHITE_BOARD_MENU


def whiteboard_menu_event(current_view):
    """This function manages the whiteboard menu

    attributes:
        current_view: The current view that defines the touch hotspots
    """
    user_refresh = False

    if (
        current_view[0].bottom > touch_current.X[0] > current_view[0].top
        and current_view[0].left > touch_current.Y[0] > current_view[0].right
    ):
        logging.info(f"{current_view[0].name} ...\r\n")
        display_menu(MENUS[WHITE_BOARD_MENU], 0, 0)
        e_paper.refresh = True
    elif (
        current_view[1].bottom > touch_current.X[0] > current_view[1].top
        and current_view[1].left > touch_current.Y[0] > current_view[1].right
    ):
        logging.info(f"{current_view[1].name} ...\r\n")
        display_menu(MENUS[MAIN_MENU], 0, 0)
        e_paper.refresh = True
        return MAIN_MENU, user_refresh
    elif (
        current_view[2].bottom > touch_current.X[0] > current_view[2].top
        and current_view[2].left > touch_current.Y[0] > current_view[2].right
    ):
        logging.info(f"{current_view[2].name} ...\r\n")
        user_refresh = True
        e_paper.refresh = True

    return WHITE_BOARD_MENU, user_refresh


def photo_list_menu_event(current_view):
    """This function manages the photo list menu

    attributes:
        current_view: The current view that defines the touch hotspots
    """
    global large_photo_to_display
    global small_photo_to_display

    user_refresh = False
    display_photo_list = False

    if (
        current_view[2].bottom > touch_current.X[0] > current_view[2].top
        and current_view[2].left > touch_current.Y[0] > current_view[2].right
    ):
        logging.info(f"{current_view[2].name=} ...\r\n")
        display_menu(MENUS[MAIN_MENU], 0, 0)
        e_paper.refresh = True
        return MAIN_MENU, user_refresh
    elif (
        current_view[1].bottom > touch_current.X[0] > current_view[1].top
        and current_view[1].left > touch_current.Y[0] > current_view[1].right
    ):
        logging.info(f"{current_view[1].name=} ...\r\n")
        small_photo_to_display += 1
        if small_photo_to_display > 2:
            small_photo_to_display = 0
        display_photo_list = True
    elif (
        current_view[3].bottom > touch_current.X[0] > current_view[3].top
        and current_view[3].left > touch_current.Y[0] > current_view[3].right
    ):
        logging.info(f"{current_view[3].name=} ...\r\n")
        if small_photo_to_display == 0:
            logging.info("Top page ...\r\n")
        else:
            small_photo_to_display -= 1
            display_photo_list = True
    elif (
        current_view[4].bottom > touch_current.X[0] > current_view[4].top
        and current_view[4].left > touch_current.Y[0] > current_view[4].right
    ):
        logging.info(f"{current_view[4].name=} ...\r\n")
        user_refresh = True
        logging.info(f"{user_refresh=} ...\r\n")
        e_paper.refresh = True
    elif (
        current_view[0].bottom > touch_current.X[0] > current_view[0].top
        and current_view[0].left > touch_current.Y[0] > current_view[0].right
    ):
        logging.info(f"{current_view[0].name=} ...\r\n")
        display_menu(MENUS[PHOTO_MENU], 0, 0)
        large_photo_to_display = int(
            touch_current.X[0] / 46 * 2
            + 2
            - touch_current.Y[0] / 124
            + small_photo_to_display
        )
        show_photo_large(image, large_photo_to_display)
        e_paper.refresh = True
        return PHOTO_MENU, user_refresh

    if display_photo_list:
        e_paper.refresh = True
        display_menu(MENUS[PHOTO_LIST_MENU], 0, 0)
        show_photo_small(image, small_photo_to_display)  # show small photo
        display_photo_list = False

    return PHOTO_LIST_MENU, user_refresh


def photo_menu_event(current_view):
    """This function manages the photo menu

    attributes:
        current_view: The current view that defines the touch hotspots
    """
    global large_photo_to_display
    global small_photo_to_display

    user_refresh = False
    refresh_photo = False

    if (
        current_view[0].bottom > touch_current.X[0] > current_view[0].top
        and current_view[0].left > touch_current.Y[0] > current_view[0].right
    ):
        logging.info(f"{current_view[0].name=} ...\r\n")
        display_menu(MENUS[PHOTO_LIST_MENU], 0, 0)
        show_photo_small(image, small_photo_to_display)
        e_paper.refresh = True
        return PHOTO_LIST_MENU, user_refresh
    elif (
        current_view[1].bottom > touch_current.X[0] > current_view[1].top
        and current_view[1].left > touch_current.Y[0] > current_view[1].right
    ):
        logging.info(f"{current_view[1].name=} ...\r\n")
        large_photo_to_display += 1
        if large_photo_to_display > 6:
            large_photo_to_display = 1
        refresh_photo = True
    elif (
        current_view[2].bottom > touch_current.X[0] > current_view[2].top
        and current_view[2].left > touch_current.Y[0] > current_view[2].right
    ):
        logging.info(f"{current_view[2].name=} ...\r\n")
        display_menu(MENUS[MAIN_MENU], 0, 0)
        e_paper.refresh = True
        return MAIN_MENU, user_refresh
    elif (
        current_view[3].bottom > touch_current.X[0] > current_view[3].top
        and current_view[3].left > touch_current.Y[0] > current_view[3].right
    ):
        logging.info(f"{current_view[3].name=} ...\r\n")
        if large_photo_to_display == 1:
            logging.info("Top photo ...\r\n")
        else:
            large_photo_to_display -= 1
            refresh_photo = True
    elif (
        current_view[4].bottom > touch_current.X[0] > current_view[4].top
        and current_view[4].left > touch_current.Y[0] > current_view[4].right
    ):
        logging.info(f"{current_view[4].name=} ...\r\n")
        user_refresh = True
        logging.info(f"{user_refresh=} ...\r\n")
        e_paper.refresh = True

    if refresh_photo:
        e_paper.refresh = True
        show_photo_large(image, large_photo_to_display)
        refresh_photo = False

    return PHOTO_MENU, user_refresh


def close_app(app_thread):
    global thread_running

    logging.info("Clear the display")
    e_paper.update()
    e_paper.clear(0xFF)
    e_paper.sleep()

    logging.info("Exit app thread")
    thread_running = False
    time.sleep(2)
    app_thread.join()
    e_paper.exit()
    logging.info("Exit script")
    exit()


Hotspot = namedtuple("Hotspot", "top bottom right left name")

# Constants --------------------------------------------------------------------
PICTURE_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)), "pic/2in13")
SMALL_IMAGES = [
    "Photo_1_0.bmp",
    "Photo_1_1.bmp",
    "Photo_1_2.bmp",
    "Photo_1_3.bmp",
    "Photo_1_4.bmp",
    "Photo_1_5.bmp",
    "Photo_1_6.bmp",
]
LARGE_IMAGES = [
    "Photo_2_0.bmp",
    "Photo_2_1.bmp",
    "Photo_2_2.bmp",
    "Photo_2_3.bmp",
    "Photo_2_4.bmp",
    "Photo_2_5.bmp",
    "Photo_2_6.bmp",
]
MENUS = ["Menu.bmp", "White_board.bmp", "Photo_1.bmp", "Photo_2.bmp"]
MAIN_MENU = 0
WHITE_BOARD_MENU = 1
PHOTO_LIST_MENU = 2
PHOTO_MENU = 3

FONT_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)), "pic")
FONT_15PT = ImageFont.truetype(os.path.join(FONT_DIRECTORY, "Font.ttc"), 15)
FONT_24PT = ImageFont.truetype(os.path.join(FONT_DIRECTORY, "Font.ttc"), 24)
logging.info(f"The resource paths: {PICTURE_DIRECTORY}, {FONT_DIRECTORY}")

MAX_TOUCH_COUNT_SINCE_REFRESH = 12
MAX_LOOPS_SINCE_REFRESH = 50000
MAX_REFRESH_BEFORE_FULL_UPDATE = 50

# Initialisation -----------------------------------------------------------
logging.info("Setting up display and touch screen")

e_paper = epd2in13_V2.EPaperDisplay()
# logging.info(f"e_paper attributes: {dir(e_paper)}")

touch_pad = gt1151.TouchPad()
touch_current = gt1151.TouchEvent()
touch_old = gt1151.TouchEvent()
logging.debug(f"touch_current: {touch_current} touch_old {touch_old}")
# logging.info(f"touch_current attributes: {dir(touch_current)}")

# Initialise Views
home_view = [
    Hotspot(29, 92, 56, 95, "Photo"),
    Hotspot(29, 92, 153, 193, "Whiteboard"),
]

whiteboard_view = [
    Hotspot(96, 120, 6, 30, "Clear"),
    Hotspot(96, 120, 113, 136, "Home"),
    Hotspot(96, 120, 220, 242, "Refresh"),
]

photo_list_view = [
    Hotspot(2, 90, 2, 248, "The whole list area"),
    Hotspot(96, 120, 57, 78, "Next Page"),
    Hotspot(96, 120, 113, 136, "Home"),
    Hotspot(96, 120, 169, 190, "Last Page"),
    Hotspot(96, 120, 220, 242, "Refresh"),
    (2, 126),
    (2, 2),
    (47, 126),
    (47, 2),
]

photo_view = [
    Hotspot(96, 120, 4, 25, "Photo menu"),
    Hotspot(96, 120, 57, 78, "Next Page"),
    Hotspot(96, 120, 113, 136, "Home"),
    Hotspot(96, 120, 169, 190, "Last Page"),
    Hotspot(96, 120, 220, 242, "Refresh"),
]

views = [
    home_view,
    whiteboard_view,
    photo_list_view,
    photo_view,
]
# logging.info(f"{views}")
logging.info("Initialise global variables")
thread_running = True
page = MAIN_MENU
image = Image.open(os.path.join(PICTURE_DIRECTORY, MENUS[page]))
large_photo_to_display = 0
small_photo_to_display = 0


def main():
    global thread_running
    global page
    global image
    global large_photo_to_display
    global small_photo_to_display

    logging.info(
        "Initialise e_paper FULL_UPDATE, clear the screen, initialise the touch pad"
    )
    e_paper.update()
    e_paper.clear(0xFF)
    touch_pad.initialise()

    logging.info("Initialise app threading")
    app_thread = threading.Thread(target=pthread_irq)
    app_thread.setDaemon(True)
    app_thread.start()
    logging.debug(f"app_thread: {app_thread}")

    logging.info("Initialise start page and home menu")
    draw_context = ImageDraw.Draw(image)
    e_paper.display_full_page_image(e_paper.get_buffer(image))
    e_paper.update(True)

    logging.info("Initialise refresh variables")
    user_refresh = False

    try:
        logging.info("--------------- MAIN LOOP ------------------")
        while True:
            user_refresh = display_refresh(page, user_refresh)
            touch_pad.get_touch_events(touch_current, touch_old)

            # Touch Actions:
            if touch_old == touch_current:
                # logging.debug("touch_old == touch_current")
                continue

            if touch_current.TouchpointFlag:
                e_paper.touch_count_since_refresh += 1
                touch_current.TouchpointFlag = 0
                current_view = views[page]

                if page == MAIN_MENU and not e_paper.refresh:
                    page = main_menu_event(current_view)

                if page == WHITE_BOARD_MENU and not e_paper.refresh:
                    whiteboard_draw(touch_current, draw_context)
                    page, user_refresh = whiteboard_menu_event(current_view)

                if page == PHOTO_LIST_MENU and not e_paper.refresh:
                    page, user_refresh = photo_list_menu_event(current_view)

                if page == PHOTO_MENU and not e_paper.refresh:
                    page, user_refresh = photo_menu_event(current_view)

    except IOError as exception:
        logging.info(exception)

    except KeyboardInterrupt:
        logging.info("ctrl + c:")
        close_app(app_thread)


if __name__ == "__main__":
    main()
