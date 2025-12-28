# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  python-ceair-helper
# FileName:     booking_new_page.py
# Description:  航班预定页面对象
# Author:       ASUS
# CreateDate:   2025/12/10
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from typing import Optional
from playwright.async_api import Page, Locator
from playwright_helper.libs.base_po import BasePo
from ceair_helper.config.url_const import booking_new_url


class BookingNewPage(BasePo):
    url: str = booking_new_url
    __page: Page

    def __init__(self, page: Page, url: str = booking_new_url) -> None:
        super().__init__(page, url)
        self.url = url
        self.__page = page

    async def get_add_passenger_btn(self, timeout: float = 5.0) -> Optional[Locator]:
        """
        获取预订页面乘客【新增】按钮
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[contains(@class, "add-psg-button")]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_modal_username_input(self, timeout: float = 5.0) -> Optional[Locator]:
        """
        获取新增乘机人弹框中的【姓名】输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="passenger-forms"]//div[@class="ceair-modal-content"]//input[@placeholder="与登机证件姓名保持一致"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_modal_id_no_input(self, timeout: float = 5.0) -> Optional[Locator]:
        """
        获取新增乘机人弹框中的【证件号码】输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="passenger-forms"]//div[@class="ceair-modal-content"]//input[@placeholder="登机证件号码"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_modal_mobile_input(self, timeout: float = 5.0) -> Optional[Locator]:
        """
        获取新增乘机人弹框中的【手机】输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="passenger-forms"]//div[@class="ceair-modal-content"]//input[@placeholder="手机"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_modal_email_input(self, timeout: float = 5.0) -> Optional[Locator]:
        """
        获取新增乘机人弹框中的【邮箱地址】输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="passenger-forms"]//div[@class="ceair-modal-content"]//input[@placeholder="邮箱地址"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_credential_type_dropdown(self, timeout: float = 5.0) -> Optional[Locator]:
        """
        获取新增乘机人弹框中的【证件类型】下拉框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="passenger-forms"]//div[@class="ceair-modal-content"]//div[@class="ceair-select-selection"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_dropdown_with_credential_type(self, credential_type: str, timeout: float = 5.0) -> Optional[Locator]:
        """
        获取新增乘机人弹框中证件类型中的【credential_type】下拉选项
        :param credential_type: 证件类型
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = f'//div[@class="passenger-forms"]//div[@class="ceair-modal-content"]//div[@class="ceair-select-dropdown"]//p[normalize-space(text())="{credential_type}"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_add_passenger_submit_btn(self, timeout: float = 5.0) -> Optional[Locator]:
        """
        获取新增乘机人弹框中【确定】按钮
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="passenger-forms"]//div[@class="ceair-modal-content"]//div[@class="submit"]/button'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_booking_new_next_btn(self, timeout: float = 5.0) -> Optional[Locator]:
        """
        获取预订页面【下一步】按钮
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="content-bottom"]//button/span[normalize-space(text())="下一步"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_check_statements_checkbox(self, timeout: float = 5.0) -> Optional[Locator]:
        """
        获取锂电池及危险品安全须知协议【已同意】单选框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="tip-container"]//span[@class="ceair-checkbox__inner"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_check_statements_next_btn(self, timeout: float = 5.0) -> Optional[Locator]:
        """
        获取锂电池及危险品安全须知协议【下一步】按钮
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="tip-container"]//button//span[normalize-space(text())="下一步"]'
        return await self.get_locator(selector=selector, timeout=timeout)