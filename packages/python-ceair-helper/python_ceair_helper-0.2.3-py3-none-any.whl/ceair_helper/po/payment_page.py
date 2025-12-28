# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  python-ceair-helper
# FileName:     payment_page.py
# Description:  航班预定支付面对象
# Author:       ASUS
# CreateDate:   2025/12/10
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from typing import Dict, Any
from playwright.async_api import Page, Locator
from ceair_helper.config.url_const import pay_url
from playwright_helper.libs.base_po import BasePo
from playwright_helper.utils.type_utils import convert_order_amount_text


class PaymentPage(BasePo):
    url: str = pay_url
    __page: Page

    def __init__(self, page: Page, url: str = pay_url) -> None:
        super().__init__(page, url)
        self.url = url
        self.__page = page

    async def get_pre_order_number(self, timeout: float = 5.0) -> str:
        """
        支付页面获取待支付订单号
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//span[@class="order-number"]'
        locator = await self.get_locator(selector=selector, timeout=timeout)
        return (await locator.inner_text()).strip()

    async def get_pre_order_total_amount(self, timeout: float = 5.0) -> Dict[str, Any]:
        """
        支付页面获取待支付订单总金额
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="refund-change-msg-sizes right right"]'
        locator = await self.get_locator(selector=selector, timeout=timeout)
        total_amount: str = (await locator.inner_text()).strip()
        return convert_order_amount_text(amount_text=total_amount)

    async def get_world_pay_icon(self, timeout: float = 5.0) -> Locator:
        """
        支付页面获取 world_pay 支付方式的 icon，完整的url： https://www.ceair.com/_nuxt/img/ico_worldpay.33e9568.png
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="ceair-tooltip-rel"]//img[contains(@src, "ico_worldpay")]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_submit_pay_btn(self, timeout: float = 5.0) -> Locator:
        """
        支付页面获取【确认支付】按钮
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="payment-submit"]/button'
        return await self.get_locator(selector=selector, timeout=timeout)
