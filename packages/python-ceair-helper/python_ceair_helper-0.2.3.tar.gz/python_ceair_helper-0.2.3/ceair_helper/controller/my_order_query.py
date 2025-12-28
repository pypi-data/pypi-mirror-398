# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  python-ceair-helper
# FileName:     my_order_query.py
# Description:  我的订单查询控制器
# Author:       ASUS
# CreateDate:   2025/12/20
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import asyncio
from logging import Logger
from playwright.async_api import Page, Locator
import ceair_helper.config.url_const as url_const
from typing import Dict, Any, List, Optional, cast
from ceair_helper.po.my_ticket_order_page import MyTicketOrderPage
from ceair_helper.po.my_ticket_order_detail_page import MyTicketOrderDetailPage


async def open_my_order_page(
        *, page: Page, logger: Logger, ceair_protocol: str, ceair_domain: str, timeout: float = 20.0
) -> MyTicketOrderPage:
    url_prefix = f"{ceair_protocol}://{ceair_domain}"
    my_order_url = url_prefix + url_const.my_ticket_order_url
    await page.goto(my_order_url)

    my_order_po = MyTicketOrderPage(page=page, url=my_order_url)
    await my_order_po.url_wait_for(url=my_order_url, timeout=timeout)
    logger.info(f"即将东方航空官网我的订单页面，页面URL<{my_order_url}>")
    return my_order_po


async def query_order_payment_state(
        *, logger: Logger, page: MyTicketOrderPage, pre_order_id: str, timeout: float = 20.0
) -> Dict[str, Any]:
    # 0. 小插曲，要等待页面中的第一条记录出现，再起输入搜索内容，否则速度太快，搜索了个寂寞
    await page.get_order_list(timeout=timeout)

    # 1. 订单搜索输入订单号
    text_input = await page.get_order_query_type_text_input()
    await text_input.fill(value=pre_order_id)
    logger.info(f"我的机票订单页，按订单号查询，搜索框内容<{pre_order_id}>输入完成")

    # 2. 点击【查询】
    query_btn = await page.get_query_btn(timeout=timeout)
    await query_btn.click(button="left")
    logger.info(f"我的机票订单页，按订单号查询，【查询】按钮点击完成")

    # 3. 获取订单的locator对象
    order_locator: Locator = await page.get_order_locator(pre_order_id=pre_order_id, timeout=timeout)
    logger.info(f"东航官网订单<{pre_order_id}>，获取查询列表中订单Locator对象完成")

    # 4. 获取订单状态
    order_state = await page.get_order_state_text(locator=order_locator, timeout=timeout)
    logger.info(f"我的机票订单页，按订单号查询，获取订单状态<{order_state}>已完成")

    # 4. 获取订单支付金额
    order_amount_dict = await page.get_order_amount_text(locator=order_locator, timeout=timeout)
    logger.info(f"我的机票订单页，按订单号查询，获取订单支付金额<{order_state}>已完成")

    # 5. 获取【订单详情】按钮
    order_detail_btn = await page.get_order_detail_btn(locator=order_locator, timeout=timeout)
    logger.info(f"我的机票订单页，按订单号查询，【订单详情】按钮获取完成")

    order_amount_dict.update(dict(order_state=order_state, detail_btn_locator=order_detail_btn))
    return order_amount_dict


async def query_order_itinerary(
        *, page: MyTicketOrderDetailPage, logger: Logger, timeout: float = 20.0
) -> List[Dict[str, Any]]:
    # 1. 获取我的机票订单详情页获取乘客【姓名】页签
    tabs_items = await page.get_passenger_tabs_nav(timeout=timeout)
    data = list()
    for passenger_locator in tabs_items:
        passenger = (await passenger_locator.inner_text()).strip()
        await passenger_locator.click(button="left")
        await asyncio.sleep(1)
        order_itinerary = await page.get_itinerary_text(timeout=timeout)
        id_number = await page.get_id_number_text(timeout=timeout)
        pre_order_id = await page.get_query_pre_order_id(timeout=timeout)
        data.append(dict(
            passenger=passenger, order_itinerary=order_itinerary, id_number=id_number, pre_order_id=pre_order_id
        ))
    logger.info(f"获取当前订单的票号信息：{data}")
    return data


async def first_open_page_query_order_payment_state(
        *, page: Page, logger: Logger, ceair_protocol: str, ceair_domain: str, pre_order_id: str, timeout: float = 20.0,
        **kwargs: Any
) -> Dict[str, Any]:
    # 1. 打开页面
    my_order_po = await open_my_order_page(
        page=page, logger=logger, ceair_protocol=ceair_protocol, ceair_domain=ceair_domain, timeout=timeout
    )

    # 2. 查询订单支付状态信息
    return await query_order_payment_state(logger=logger, page=my_order_po, pre_order_id=pre_order_id, timeout=timeout)


async def first_open_page_query_order_itinerary(
        *, page: Page, logger: Logger, ceair_protocol: str, ceair_domain: str, pre_order_id: str, timeout: float = 20.0,
        **kwargs: Any
) -> List[Optional[Dict[str, Any]]]:
    # 1. 打开页面
    my_order_po = await open_my_order_page(
        page=page, logger=logger, ceair_protocol=ceair_protocol, ceair_domain=ceair_domain, timeout=timeout
    )

    order_payment_state: Dict[str, Any] = await query_order_payment_state(
        logger=logger, page=my_order_po, pre_order_id=pre_order_id, timeout=timeout
    )
    order_state = order_payment_state.get("order_state")
    if "交易成功" in order_state:
        detail_btn_locator: Locator = order_payment_state.get("detail_btn_locator")
        await detail_btn_locator.click(button="left")

        order_detail_url_prefix = f"{ceair_protocol}://{ceair_domain}"
        order_detail_url = order_detail_url_prefix + url_const.my_ticket_order_detail_url
        order_detail_page = my_order_po.get_page().context.pages[0]
        order_detail_po = MyTicketOrderDetailPage(page=order_detail_page, url=order_detail_url)
        await order_detail_po.url_wait_for(url=order_detail_url, timeout=timeout)
        logger.info(f"即将进入东方航空官网我的机票订单详情页面，页面URL<{order_detail_url}>")
        return await query_order_itinerary(logger=logger, timeout=timeout, page=order_detail_po)
    else:
        logger.warning(f"东方航空官网订单<{pre_order_id}>，当前状态是<{order_state}>，不满足出票条件，不需要查询票号")
        return list()
