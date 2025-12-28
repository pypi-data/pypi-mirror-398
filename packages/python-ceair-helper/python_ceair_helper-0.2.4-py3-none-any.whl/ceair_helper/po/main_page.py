# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  python-ceair-helper
# FileName:     main_page.py
# Description:  首页页面对象
# Author:       ASUS
# CreateDate:   2025/12/09
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from playwright.async_api import Page, Locator
from playwright_helper.libs.base_po import BasePo
from ceair_helper.config.url_const import main_url


class MainPage(BasePo):
    url: str = main_url
    __page: Page

    def __init__(self, page: Page, url: str = main_url) -> None:
        super().__init__(page, url)
        self.url = url
        self.__page = page

    async def get_departure_city_search_input(self, timeout: float = 5.0) -> Locator:
        """
        获取【出发城市】搜索输入框
        :param timeout: 超时时间（秒）
        :return:
        """
        selector: str = '//div[@class="search-form"]//input[@aria-label="出发"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_arrival_city_search_input(self, timeout: float = 5.0) -> Locator:
        """
        获取【抵达城市】搜索输入框
        :param timeout: 超时时间（秒）
        :return:
        """
        selector: str = '//div[@class="search-form"]//input[@aria-label="到达"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_departure_date_search_input(self, timeout: float = 5.0) -> Locator:
        """
        获取【出发时间】搜索输入框
        :param timeout: 超时时间（秒）
        :return:
        """
        selector: str = '//div[@id="datepicker0"]//input[@aria-label="出发"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_calendar_next_page_icon(self, timeout: float = 5.0) -> Locator:
        """
        获取日历选择器【下一页】icon图标
        :param timeout: 超时时间（秒）
        :return:
        """
        selector: str = '(//div[contains(@class, "poptip-right-single")]//div[@id="next"]/img[@alt="detail-seat"])[1]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_calendar_left_date_value(self, date_value: str, timeout: float = 5.0) -> Locator:
        """
        获取左边日历选择器日期元素
        :param date_value: 日期字符串
        :param timeout: 超时时间（秒）
        :return:
        """
        if len(date_value) > 2:
            day_value = date_value[-2:]
        else:
            day_value = date_value
        selector: str = f'(//div[@id="ceair-group"]//div[@class="date-value" and contains(text(), {day_value})])[1]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_calendar_right_date_value(self, date_value: str, timeout: float = 5.0) -> Locator:
        """
        获取右边日历选择器日期元素
        :param date_value: 日期字符串
        :param timeout: 超时时间（秒）
        :return:
        """
        if len(date_value) > 2:
            day_value = date_value[-2:]
        else:
            day_value = date_value
        selector: str = f'(//div[@id="ceair-group-right"]//div[@class="date-value" and contains(text(), {day_value})])[1]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_flight_search_btn(self, timeout: float = 5.0) -> Locator:
        """
        获取航班【搜索】按钮
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="city-search"]//button[@type="button"]/span[contains(text(), "搜索")]'
        return await self.get_locator(selector=selector, timeout=timeout)
