# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  python-ceair-helper
# FileName:     booking_flight.py
# Description:  预订航班控制器模块
# Author:       ASUS
# CreateDate:   2025/12/11
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import re
from logging import Logger
from typing import List, Dict, Any
from playwright.async_api import Page, Locator
import ceair_helper.config.url_const as url_const
from ceair_helper.po.one_way_page import OneWayPage
from ceair_helper.po.booking_new_page import BookingNewPage
from ceair_helper.po.add_sercies_page import AddServicesPage
from playwright_helper.utils.po_utils import on_click_locator


async def _search_flight(
        logger: Logger, one_way_po: OneWayPage, flight_no: str, cabin_class: str, price_sell: float, prodcut_name: str,
        price_std: float, passengers: List[Dict[str, Any]], timeout: float = 10.0,
        price_increase_threshold: float = 20.0, price_reduction_threshold: float = 10.0
) -> None:
    try:
        # 1. 判断是否存在出行提醒
        i_known_btn = await one_way_po.get_i_known_btn(timeout=timeout)
        await i_known_btn.click(button="left")
        logger.info("单航程航班查询页面，出现通知弹框，【确认】按钮点击完成")
    except (Exception,):
        pass

    await one_way_po.handle_po_cookie_tip(page=one_way_po, logger=logger, timeout=timeout)

    # 2. 获取航班 Locator
    flight_locator = await one_way_po.get_flight(flight_no=flight_no, timeout=timeout)
    logger.info(f"单航程航班查询页面，航班<{flight_no}>Locator信息获取完成")

    # 3. 获取航班订票入口信息
    prices_block = await one_way_po.get_flight_prices_block(
        locator=flight_locator, flight_no=flight_no
    )
    logger.info(f"单航程航班查询页面，航班<{flight_no}>订票入口信息获取完成")
    cabin_class_info = prices_block.get(cabin_class) or dict()
    cabin_class_locator = cabin_class_info.get("locator")
    # currency = cabin_class_info.get("currency")
    # amount = cabin_class_info.get("amount")
    if isinstance(cabin_class_locator, Locator) is False:
        raise RuntimeError(f"单航程航班查询页面，航班<{flight_no}>舱类型<{cabin_class}>订票点击入口没有找到")
    await cabin_class_locator.click(button="left")
    logger.info(f"单航程航班查询页面，航班<{flight_no}>舱类型<{cabin_class}>订票入口点击展开完成")

    # 4. 获取航班舱类型下的【prodcut_name】产品
    cabin_class_products = await one_way_po.get_flight_cabin_class_products(
        locator=flight_locator, flight_no=flight_no, timeout=timeout
    )
    logger.info(f"单航程航班查询页面，航班<{flight_no}>舱类型<{cabin_class}>下的所有产品获取完成")
    select_prodcuts = [x for x in cabin_class_products if x.get("title") == prodcut_name]
    if len(select_prodcuts) == 0:
        raise RuntimeError(
            f"单航程航班查询页面，航班<{flight_no}>舱类型<{cabin_class}>下所合适的<{prodcut_name}>产品没有找到")
    logger.info(f"单航程航班查询页面，航班<{flight_no}>舱类型<{cabin_class}>下所合适的<{prodcut_name}>产品获取完成")
    select_prodcuts.sort(key=lambda x: x["amount"])
    # currency = select_prodcuts[0].get("currency")
    amount = select_prodcuts[0].get("amount")
    seats_status = select_prodcuts[0].get("seats_status")
    logger.info(f"单航程航班查询页面，航班<{flight_no}>产品<{prodcut_name}>的座位情况：{seats_status}")
    m = re.search(r'\d+', seats_status)
    if m:
        count = int(m.group())
        if count < len(passengers):
            raise EnvironmentError(f"航班<{flight_no}>的余票: {count}，数量不足")
    booking_btn_locator = select_prodcuts[0].get("booking_btn")
    if not booking_btn_locator:
        raise RuntimeError(f"单航程航班查询页面，航班<{flight_no}>产品<{prodcut_name}>的订购按钮没有找到")
    # 5. 判断价格是否在上浮，下降阈值区间内
    if amount > price_std + price_increase_threshold:
        raise EnvironmentError(
            f"单航程航班查询页面，航班<{flight_no}>官网价：{amount} 高于：订单销售价[{price_std}] + 上浮阈值[{price_increase_threshold}]，损失过高")
    if amount < price_std - price_reduction_threshold:
        raise EnvironmentError(
            f"单航程航班查询页面，航班<{flight_no}>官网价：{amount} 低于：订单销售价[{price_std}] - 下降阈值[{price_reduction_threshold}]，收益过高")
    logger.info(f"单航程航班查询页面，航班<{flight_no}>产品<{prodcut_name}>的订购按钮获取完成")

    # 6. 判断货币符号，是否为 ¥(人民币结算)
    # 目前都为国内航班，暂不考虑货币种类

    # 7. 点击【订购】按钮，进入一下个页面
    await on_click_locator(locator=booking_btn_locator)
    logger.info(f"单航程航班查询页面，航班<{flight_no}>产品<{prodcut_name}>的【订购】按钮点击完成")


async def _add_passengers(
        booking_new_page: BookingNewPage, logger: Logger, passengers: List[Dict[str, Any]], email: str, mobile: str,
        timeout: float = 10.0
) -> None:
    """遍历方式，完成乘客的添加"""
    for passenger in passengers:
        # 1. 获取添加乘客按钮
        add_passenger_btn = await booking_new_page.get_add_passenger_btn(timeout=timeout * 5)
        await add_passenger_btn.click(button="left")
        logger.info(f"乘客添加页面，【新增】按钮点击完成")

        # 2. 输入乘客名
        username_input = await booking_new_page.get_modal_username_input(timeout=timeout)
        p_name = passenger.get("p_name").strip()
        await username_input.fill(value=p_name)
        logger.info(f"乘客添加页面，新增乘机人弹框，乘客名<{p_name}>输入完成")

        # 3. 输入证件号码
        id_no_input = await booking_new_page.get_modal_id_no_input(timeout=timeout)
        id_no = passenger.get("id_no").strip()
        await id_no_input.fill(value=id_no)
        logger.info(f"乘客添加页面，新增乘机人弹框，证件号码<{id_no}>输入完成")

        # 4. 输入手机号码
        mobile_input = await booking_new_page.get_modal_mobile_input(timeout=timeout)
        mobile = mobile.strip()
        await mobile_input.fill(value=mobile)
        logger.info(f"乘客添加页面，新增乘机人弹框，手机号码<{mobile}>输入完成")

        # 5. 输入电子邮箱
        email_input = await booking_new_page.get_modal_email_input(timeout=timeout)
        email = email.strip()
        await email_input.fill(value=email)
        logger.info(f"乘客添加页面，新增乘机人弹框，电子邮箱<{email}>输入完成")

        # 6. 点击【确认】按钮
        add_passenger_submit_btn = await booking_new_page.get_add_passenger_submit_btn(timeout=timeout)
        await add_passenger_submit_btn.click(button="left")
        logger.info(f"乘客添加页面，新增乘机人弹框，【确定】按钮点击完成")

    # 7. "点击"【下一步】按钮
    booking_new_next_btn = await booking_new_page.get_booking_new_next_btn(timeout=timeout)
    await booking_new_next_btn.click(button="left")
    logger.info(f"乘客添加页面，【下一步】按钮点击完成")

    # 8. "勾选"锂电池及危险品安全须知协议【已同意】单选框
    check_statements_checkbox = await booking_new_page.get_check_statements_checkbox(timeout=timeout)
    await check_statements_checkbox.click(button="left")
    logger.info(f"乘客添加页面，锂电池及危险品安全须知协议【已同意】单选框勾选完成")

    # 9. "点击"锂电池及危险品安全须知协议【下一步】按钮
    check_statements_next_btn = await booking_new_page.get_check_statements_next_btn(timeout=timeout)
    await check_statements_next_btn.click(button="left")
    logger.info(f"乘客添加页面，锂电池及危险品安全须知协议【下一步】按钮点击完成")


async def _add_services(
        add_service_po: AddServicesPage, logger: Logger, flight_no: str, order_cabin_code: str, timeout: float = 10.0
) -> None:
    # 1. "勾选"购票须知【已阅读】单选框
    rule_box_checkbox = await add_service_po.get_rule_box_checkbox(timeout=timeout)
    await rule_box_checkbox.click(button="left")
    logger.info(f"添加服务页面，购票须知【已阅读】单选框勾选完成")

    # 2. 校验预订的舱位信息，暂时不考虑升，降舱的情况
    cabin_code = await add_service_po.get_cabin_code(timeout=timeout)
    if not cabin_code:
        raise RuntimeError(f"添加服务页面，航班<{flight_no}>舱位信息没有获取到")
    if cabin_code[0] != order_cabin_code:
        raise EnvironmentError(
            f"添加服务页面，航班<{flight_no}>舱位信息没有获取到的是[{cabin_code}]，与订单乘客舱位信息[{order_cabin_code}]不一致")

    # 4. 点击【下一步】
    next_btn = await add_service_po.get_add_services_next_btn(timeout=timeout)
    await next_btn.click(button="left")
    logger.info(f"添加服务页面，【下一步】按钮点击完成")


async def booking_flight_callback(
        *, page: Page, logger: Logger, dep_city: str, arr_city: str, flight_no: str, cabin_class: str,
        price_sell: float, prodcut_name: str, passengers: List[Dict[str, Any]], email: str, mobile: str,
        price_std: float, order_cabin_code: str, dep_date: str, protocol: str, domain: str, timeout: float = 10.0,
        price_increase_threshold: float = 20.0, price_reduction_threshold: float = 10.0, **kwargs: Any
) -> None:
    url_prefix = f"{protocol}://{domain}"
    one_way_url_suffix = url_const.one_way_url.format(dep_city, arr_city, dep_date[:10])
    one_way_url = url_prefix + one_way_url_suffix
    await page.goto(one_way_url)

    one_way_po = OneWayPage(page=page, url=one_way_url)
    await one_way_po.url_wait_for(url=one_way_url, timeout=timeout)
    logger.info(f"即将进入单航程航班查询页面，页面URL<{one_way_url}>")
    await _search_flight(
        logger=logger, one_way_po=one_way_po, flight_no=flight_no, cabin_class=cabin_class, price_sell=price_sell,
        prodcut_name=prodcut_name, price_increase_threshold=price_increase_threshold, passengers=passengers,
        price_reduction_threshold=price_reduction_threshold, timeout=timeout, price_std=price_std,
    )

    booking_new_url_suffix = url_const.booking_new_url
    booking_new_url = url_prefix + booking_new_url_suffix
    booking_new_page = BookingNewPage(page)
    await booking_new_page.url_wait_for(url=booking_new_url, timeout=timeout)
    logger.info(f"即将进入乘客添加页面，页面URL<{booking_new_url}>")
    await _add_passengers(
        booking_new_page=booking_new_page, logger=logger, passengers=passengers, email=email, mobile=mobile,
        timeout=timeout
    )

    add_service_url_suffix = url_const.add_services_url
    add_service_url = url_prefix + add_service_url_suffix
    add_service_po = AddServicesPage(page)
    await add_service_po.url_wait_for(url=add_service_url, timeout=timeout)
    logger.info(f"即将进入添加服务页面，页面URL<{add_service_url}>")
    await _add_services(
        add_service_po=add_service_po, logger=logger, flight_no=flight_no, order_cabin_code=order_cabin_code,
        timeout=timeout
    )
    logger.info(f"航班<{flight_no}>预订完成")
