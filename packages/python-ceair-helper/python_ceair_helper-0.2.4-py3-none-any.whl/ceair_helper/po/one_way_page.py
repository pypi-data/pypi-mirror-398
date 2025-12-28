# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  python-ceair-helper
# FileName:     one_way_page.py
# Description:  单程航班查询页面对象
# Author:       ASUS
# CreateDate:   2025/12/09
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from typing import Optional, List, Any, Dict
from playwright_helper.libs.base_po import BasePo
from ceair_helper.config.url_const import one_way_url
from playwright_helper.utils.type_utils import safe_convert_advanced
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError, Locator


class OneWayPage(BasePo):
    url: str = one_way_url
    __page: Page

    def __init__(self, page: Page, url: str = one_way_url) -> None:
        super().__init__(page, url)
        self.url = url
        self.__page = page

    async def get_i_known_btn(self, timeout: float = 5.0) -> Locator:
        """
        获取单程航班页面通知中的【我知道了】按钮
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//button[contains(@class, "btn-confirm")]/span[contains(text(), "我知道了")]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_flight_items(self, timeout: float = 5.0) -> List[Locator]:
        """
        获取航班Locator列表
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="shopping-parent-item-container flex-col"]'
        locator = await self.get_locator(selector=selector, timeout=timeout)
        return await locator.all()

    async def get_flight(self, flight_no: str, timeout: float = 5.0) -> Locator:
        """
        获取航班Locator
        :param flight_no: 航班号
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        flight_selector: str = f'xpath=.//span[@class="title-flight-no" and contains(text(), "{flight_no}")]'
        locators = await self.get_flight_items(timeout=timeout)
        for locator in locators:
            try:
                await self.get_sub_locator(locator=locator, selector=flight_selector, timeout=1)
                return locator
            except (PlaywrightTimeoutError, Exception):
                pass
        raise RuntimeError(f'单程航班页面航班Locator列表中没有找到【{flight_no}】航班')

    async def get_flight_prices_block(self, locator: Locator, flight_no: str) -> Dict[str, Any]:
        """
        获取航班<flight_no>的【经济舱|超级经济舱|公务舱/头等舱】订票入口
        :param locator: 航班 Locator
        :param flight_no: 航班号
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = 'xpath=.//div[starts-with(@class, "cabin-level-item")]'
        locator_inner = await self.get_sub_locator(locator=locator, selector=selector, timeout=1)
        locators = await locator_inner.all()
        prices_block = dict()
        no_price_selector: str = 'xpath=.//span[@class="no-price"]'
        for index, item in enumerate(locators):
            if index == 0:
                cabin_class = "economy"
            elif index == 1:
                cabin_class = "economy_plus"
            elif index == 2:
                cabin_class = "business"
            else:
                cabin_class = "undefined"
            try:
                # 如果有 no-price，则直接取文本, 不需要等待太长时间
                await self.get_sub_locator(locator=item, selector=no_price_selector, timeout=1)
                currency: str = ""
                amount: int = -1
            except (Exception,):
                # 正常价格格式：货币标识 + 数字
                currency: str = (await item.locator("xpath=.//span").nth(0).inner_text()).strip()
                amount: str = (await item.locator("xpath=.//span").nth(1).inner_text()).strip()
                amount: str = safe_convert_advanced(value=amount)
            prices_block[cabin_class] = {
                "locator": item,
                "cabin_class": cabin_class,
                "currency": currency,
                "amount": amount
            }
        if prices_block:
            return prices_block
        else:
            raise RuntimeError(
                f'单程航班页面中解析航班<{flight_no}>的【经济舱|超级经济舱|公务舱/头等舱】订票入口失败')

    async def _get_product_title_info(self, locator: Locator) -> Dict[str, Any]:
        """
        获取产品中的 标题信息
        :param locator: 产品 Locator
        :return: (是否存在, 错误信息|元素对象)
        """
        title_selector: str = 'xpath=.//div[@class="fare-title"]/div[@class="fare-title-text"]'
        seats_status_selector: str = 'xpath=.//div[@class="fare-title"]//div[@class="fare-title-seat"]/span'
        title_info = dict(title="", seats_status="")
        try:
            title_locator = await self.get_sub_locator(locator=locator, selector=title_selector, timeout=1)
            title_info["title"] = (await title_locator.inner_text()).strip()
        except (Exception,):
            pass
        try:
            seats_status_locator = await self.get_sub_locator(
                locator=locator, selector=seats_status_selector, timeout=1
            )
            title_info["seats_status"] = (await seats_status_locator.inner_text()).strip()
        except (Exception,):
            pass
        return title_info

    async def _get_product_fare_tips(self, locator: Locator) -> List[str]:
        """
        获取产品中的 tips
        :param locator: 产品 Locator
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = 'xpath=.//div[@class="fare-tip"]//div[@class="flex al-center"]'
        fare_tips = list()
        try:
            locator = await self.get_sub_locator(locator=locator, selector=selector, timeout=1)
            locators = await locator.all()
            poptip_selector: str = 'xpath=.//div[@class="ceair-poptip"]//span[contains(@class,"title-item")]'
            for item in locators:
                try:
                    tip_item = await self.get_sub_locator(locator=item, selector=poptip_selector, timeout=1)
                    tip: str = (await tip_item.inner_text()).strip()
                    fare_tips.append(tip)
                except (Exception,):
                    pass
        except (Exception,):
            pass
        return fare_tips

    async def _get_product_fare_rights(self, locator: Locator) -> List[str]:
        """
        获取产品中的 rights
        :param locator: 产品 Locator
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = 'xpath=.//div[@class="fare-rights"]//span[@class="fare-rights-text" or @class="more-rights-text"]'
        fare_rights = list()
        try:
            locator = await self.get_sub_locator(locator=locator, selector=selector, timeout=1)
            locators = await locator.all()
            for rights_item in locators:
                try:
                    fare_right: str = (await rights_item.inner_text()).strip()
                    if fare_right:
                        fare_rights.append(fare_right)
                except (PlaywrightTimeoutError, Exception):
                    pass
        except (Exception,):
            pass
        return fare_rights

    async def _get_product_booking_info(self, locator: Locator) -> Dict[str, Any]:
        """
        获取产品中的【订购】信息
        :param locator: 产品 Locator
        :return: (是否存在, 错误信息|元素对象)
        """
        tax_tip_selector: str = 'xpath=.//div[@class="fare-btn"]//div[@class="tax-tip"]'
        currency_selector: str = 'xpath=(.//div[@class="fare-btn"]//div[@class="fare-btn-amt"]//div[@class="price-shopping-info-container al-base"]/span)[1]'
        amount_selector: str = 'xpath=(.//div[@class="fare-btn"]//div[@class="fare-btn-amt"]//div[@class="price-shopping-info-container al-base"]/span)[2]'
        booking_btn_selector: str = 'xpath=.//div[@class="fare-btn"]//button'
        booking_info = dict(tax_tip="", amount=-1, currency="")
        try:
            tax_tip_locator = await self.get_sub_locator(locator=locator, selector=tax_tip_selector, timeout=1)
            booking_info["tax_tip"] = (await tax_tip_locator.inner_text()).strip()
        except (Exception,):
            pass
        try:
            currency_locator = await self.get_sub_locator(locator=locator, selector=currency_selector, timeout=1)
            currency: str = (await currency_locator.inner_text()).strip()
            booking_info["currency"] = currency
        except (Exception,):
            pass
        try:
            amount_locator = await self.get_sub_locator(locator=locator, selector=amount_selector, timeout=1)
            amount: str = (await amount_locator.inner_text()).strip()
            if amount.find(",") != -1:
                amount = amount.replace(",", "")
            booking_info["amount"] = safe_convert_advanced(value=amount)
        except (Exception,):
            pass
        try:
            booking_btn_locator = await self.get_sub_locator(locator=locator, selector=booking_btn_selector, timeout=1)
            booking_info["booking_btn"] = booking_btn_locator
        except (Exception,):
            pass
        return booking_info

    async def get_flight_cabin_class_products(
            self, locator: Locator, flight_no: str, timeout: float = 5.0
    ) -> List[Optional[Dict[str, Any]]]:
        """
        获取航班<flight_no>的产品Locator列表
        :param locator: 航班 Locator
        :param flight_no: 航班号
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = 'xpath=.//div[contains(@id, "threeFareInfoItem")]'
        locator = await self.get_sub_locator(locator=locator, selector=selector, timeout=timeout)
        locators = await locator.all()
        products = list()
        for item in locators:
            try:
                # 让元素滚动可见 → 聚焦
                await item.scroll_into_view_if_needed()
                await item.first.wait_for(state='visible', timeout=timeout * 1000)
                title_info = await self._get_product_title_info(locator=item)
                if title_info.get("title"):
                    fare_tips = await self._get_product_fare_tips(locator=item)
                    fare_rights = await self._get_product_fare_rights(locator=item)
                    booking_info = await self._get_product_booking_info(locator=item)
                    title_info.update(booking_info)
                    title_info["fare_tips"] = fare_tips
                    title_info["fare_rights"] = fare_rights
                    products.append(title_info)
            except (PlaywrightTimeoutError, Exception):
                pass
        if products:
            return products
        else:
            raise RuntimeError(f'单程航班页面中解析航班<{flight_no}>的产品Locator列表失败')
