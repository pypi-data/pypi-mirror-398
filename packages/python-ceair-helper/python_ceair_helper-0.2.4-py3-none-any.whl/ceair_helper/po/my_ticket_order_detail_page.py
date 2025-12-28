# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  python-ceair-helper
# FileName:     my_ticket_order_detail_page.py
# Description:  我的订单详情页面对象
# Author:       ASUS
# CreateDate:   2025/12/20
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import re
from typing import List
from playwright.async_api import Page, Locator
from playwright_helper.libs.base_po import BasePo
from ceair_helper.config.url_const import my_ticket_order_detail_url


class MyTicketOrderDetailPage(BasePo):
    url: str = my_ticket_order_detail_url
    __page: Page

    def __init__(self, page: Page, url: str = my_ticket_order_detail_url) -> None:
        super().__init__(page, url)
        self.url = url
        self.__page = page

    async def get_passenger_tabs_nav(self, timeout: float = 5.0) -> List[Locator]:
        """
        我的机票订单详情页获取乘客【姓名】页签
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="ceair-tabs-nav"]//div[@class="ceair-poptip-rel"]//span'
        locator: Locator = await self.get_locator(selector=selector, timeout=timeout)
        return await locator.all()

    async def get_itinerary_text(self, timeout: float = 5.0) -> str:
        """
        我的机票订单详情页获取乘客票号，例如：781-2127107354
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@id="pax-item0"]/span[@class="pax-info-sub"]'
        locator: Locator = await self.get_locator(selector=selector, timeout=timeout)
        text: str = (await locator.inner_text()).strip()
        if text.find("-") != -1:
            return text
        else:
            raise RuntimeError(f"我的机票订单详情页获取乘客票号<{text}>非法")

    async def get_id_number_text(self, timeout: float = 5.0) -> str:
        """
        我的机票订单详情页获取乘客证件号码，例如：342524**********25
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@id="pax-item1"]/span[@class="pax-info-sub"]'
        locator: Locator = await self.get_locator(selector=selector, timeout=timeout)
        return (await locator.inner_text()).strip()

    async def get_query_pre_order_id(self, timeout: float = 5.0) -> str:
        selector: str = '(//div[@class="order-detail-left flex-col"]/div/span)[2]'
        locator: Locator = await self.get_locator(selector=selector, timeout=timeout)
        return (await locator.inner_text()).strip()
