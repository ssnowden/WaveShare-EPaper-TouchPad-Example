def display_refresh(
    e_paper,
    refresh_display,
    user_refresh,
    touch_count_since_refresh,
    loop_count_since_refresh,
    full_update_refresh_count,
):
    if refresh_display:
        # print(f"In first if refresh_display: {refresh_display}")
        if page_selected == 1 and not user_refresh:
            e_paper.displayPartial(e_paper.getbuffer(image))
        else:
            e_paper.displayPartial_Wait(e_paper.getbuffer(image))
        touch_count_since_refresh = 0
        loop_count_since_refresh = 0
        full_update_refresh_count += 1
        refresh_display = 0
        logging.info("*** Draw Refresh ***\r\n")
        # print(f"Exit first if refresh_display: {refresh_display}")
    elif touch_count_since_refresh > MAX_TOUCH_COUNT_SINCE_REFRESH:
        # print(f"In first if refresh_display: {refresh_display}")
        if page_selected == 1 and not user_refresh:
            e_paper.displayPartial(e_paper.getbuffer(image))
        else:
            e_paper.displayPartial_Wait(e_paper.getbuffer(image))
        touch_count_since_refresh = 0
        loop_count_since_refresh = 0
        full_update_refresh_count += 1
        refresh_display = 0
        logging.info("*** Max Touch Refresh ***\r\n")
        # print(f"Exit first if refresh_display: {refresh_display}")
    elif (
        loop_count_since_refresh > MAX_LOOPS_SINCE_REFRESH
        and touch_count_since_refresh > 0
        and page_selected == 1
    ):
        e_paper.displayPartial(e_paper.getbuffer(image))
        touch_count_since_refresh = 0
        loop_count_since_refresh = 0
        full_update_refresh_count += 1
        logging.info("*** Max Loops Refresh ***\r\n")
    elif full_update_refresh_count > MAX_REFRESH_BEFORE_FULL_UPDATE:
        full_update_refresh_count = 0
        e_paper.init(e_paper.FULL_UPDATE)
        e_paper.displayPartBaseImage(e_paper.getbuffer(image))
        e_paper.init(e_paper.PART_UPDATE)
        logging.info("--- Auto Full Refresh ---\r\n")
    elif user_refresh:
        user_refresh = False
        full_update_refresh_count = 0
        e_paper.init(e_paper.FULL_UPDATE)
        e_paper.displayPartBaseImage(e_paper.getbuffer(image))
        e_paper.init(e_paper.PART_UPDATE)
        logging.info("--- User Full Refresh ---\r\n")
    else:
        loop_count_since_refresh += 1

    return (
        refresh_display,
        user_refresh,
        touch_count_since_refresh,
        loop_count_since_refresh,
        full_update_refresh_count,
    )
