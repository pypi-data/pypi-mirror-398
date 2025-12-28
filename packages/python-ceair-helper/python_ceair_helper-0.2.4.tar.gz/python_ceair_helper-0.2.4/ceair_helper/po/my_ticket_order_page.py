# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  python-ceair-helper
# FileName:     my_ticket_order.py
# Description:  我的机票订单页面对象
# Author:       ASUS
# CreateDate:   2025/12/20
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from typing import Dict, Any, List
from playwright.async_api import Page, Locator
from playwright_helper.libs.base_po import BasePo
from ceair_helper.config.url_const import my_ticket_order_url
from playwright_helper.utils.type_utils import convert_order_amount_text


class MyTicketOrderPage(BasePo):
    url: str = my_ticket_order_url
    __page: Page

    def __init__(self, page: Page, url: str = my_ticket_order_url) -> None:
        super().__init__(page, url)
        self.url = url
        self.__page = page

    async def get_order_query_type_text_input(self, timeout: float = 5.0) -> Locator:
        """
        我的机票订单页获取【订单号】输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//input[@placeholder="请输入您的订单号"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_query_btn(self, timeout: float = 5.0) -> Locator:
        """
        我的机票订单页获取【查询】按钮
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="order-list-search"and not(contains(@style,"display: none"))]//span[@class="ceair-button-text"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_order_detail_btn(self, locator: Locator, timeout: float = 5.0) -> Locator:
        """
        我的机票订单页获取【订单详情】按钮
        :param locator: Locator对象
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = 'xpath=.//div[@class="all-order-content-but"]/button/span[contains(text(), "订单详情")]'
        return await self.get_sub_locator(locator=locator, selector=selector, timeout=timeout)

    async def get_order_state_text(self, locator: Locator, timeout: float = 5.0) -> str:
        """
        我的机票订单页获取【订单状态】文本
        :param locator: Locator对象
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = 'xpath=.//div[@class="ticket-order-status"]/span'
        sub_locator: Locator = await self.get_sub_locator(locator=locator, selector=selector, timeout=timeout)
        return (await sub_locator.inner_text()).strip()

    async def get_order_amount_text(self, locator: Locator, timeout: float = 5.0) -> Dict[str, Any]:
        """
        我的机票订单页获取【支付金额】文本
        :param locator: Locator对象
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = 'xpath=.//div[@class="item-top-price fr"]/div[@class="price-total"]'
        sub_locator: Locator = await self.get_sub_locator(locator=locator, selector=selector, timeout=timeout)
        text: str = (await sub_locator.inner_text()).strip()
        return convert_order_amount_text(amount_text=text)

    async def get_first_order(self, timeout: float = 5.0) -> Locator:
        selector: str = '(//div[@class="ticket-order-list-new"]//div[@class="order-list-item order-list-item-new"])[1]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_order_list(self, timeout: float = 5.0) -> List[Locator]:
        selector: str = '//div[@class="ticket-order-list-new"]//div[@class="order-list-item order-list-item-new"]'
        locator: Locator = await self.get_locator(selector=selector, timeout=timeout)
        return await locator.all()

    async def get_order_locator(self, pre_order_id: str, timeout: float = 5.0) -> Locator:
        selector: str = f'//div[@class="order-list-item order-list-item-new"]//div[@class="status-num-date"]/span[contains(text(), "{pre_order_id}")]/ancestor::div[@class="order-list-item order-list-item-new"]'
        return await self.get_locator(selector=selector, timeout=timeout)
