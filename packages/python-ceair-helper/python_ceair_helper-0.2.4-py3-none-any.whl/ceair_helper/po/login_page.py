# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  python-ceair-helper
# FileName:     login_page.py
# Description:  登录页
# Author:       ASUS
# CreateDate:   2025/12/08
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from playwright.async_api import Page, Locator
from playwright_helper.libs.base_po import BasePo
from ceair_helper.config.url_const import login_url


class LoginPage(BasePo):
    url: str = login_url
    __page: Page

    def __init__(self, page: Page, url: str = login_url) -> None:
        super().__init__(page, url)
        self.__page = page

    async def get_login_username_input(self, timeout: float = 5.0) -> Locator:
        """
        获取登录页面的会员卡号输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//input[contains(@class, "global-input__append") and contains(@placeholder, "12位会员卡号")]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_login_password_input(self, timeout: float = 5.0) -> Locator:
        """
        获取登录页面的密码输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//input[@autocomplete="new-password" and @type="password"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_agreed_radio(self, timeout: float = 5.0) -> Locator:
        """
        获取登录页面的【隐私政策】同意单选框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//span[@class="privay-check"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_login_btn(self, timeout: float = 5.0) -> Locator:
        """
        获取登录页面的【立即登录】按钮
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[contains(@class, "global-login-btn") and contains(text(), "立即登录")]'
        return await self.get_locator(selector=selector, timeout=timeout)
