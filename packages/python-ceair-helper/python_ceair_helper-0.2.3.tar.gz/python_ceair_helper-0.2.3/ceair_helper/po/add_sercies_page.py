# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  python-ceair-helper
# FileName:     add_sercies_page.py
# Description:  航班预定添加服务页面对象
# Author:       ASUS
# CreateDate:   2025/12/10
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from typing import Dict, Any, Optional
from playwright.async_api import Page,Locator
from playwright_helper.libs.base_po import BasePo
from ceair_helper.config.url_const import add_services_url
from playwright_helper.utils.type_utils import convert_order_amount_text


class AddServicesPage(BasePo):
    url: str = add_services_url
    __page: Page

    def __init__(self, page: Page, url: str = add_services_url) -> None:
        super().__init__(page, url)
        self.url = url
        self.__page = page

    async def get_rule_box_checkbox(self, timeout: float = 5.0) -> Optional[Locator]:
        """
        添加服务页面获取购票须知【已阅读】单选框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="services-content"]//div[@class="rule-box"]//span[@class="ceair-checkbox__inner"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_cabin_code(self, timeout: float = 5.0) -> str:
        """
        添加服务页面获取舱位类型
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="flex choose-list-container"]//div[@class="cabin-code"]'
        locator = await self.get_locator(selector=selector, timeout=timeout)
        return (await locator.inner_text()).strip()

    async def get_price_amount(self, timeout: float = 5.0) -> Dict[str, Any]:
        """
        添加服务页面获取订单价格
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="price-amount"]'
        locator = await self.get_locator(selector=selector, timeout=timeout)
        price_amount: str = (await locator.inner_text()).strip()
        return convert_order_amount_text(amount_text=price_amount)

    async def get_add_services_next_btn(self, timeout: float = 5.0) -> Optional[Locator]:
        """
        添加服务页面获取【下一步】按钮
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="content-bottom"]//button'
        return await self.get_locator(selector=selector, timeout=timeout)
