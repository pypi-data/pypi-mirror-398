# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  python-ceair-helper
# FileName:     user_login.py
# Description:  用户登录页面控制器
# Author:       ASUS
# CreateDate:   2025/12/08
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import asyncio
from logging import Logger
from typing import Dict, Any
from ceair_helper.po.login_page import LoginPage
import ceair_helper.config.url_const as url_const
from playwright.async_api import Page, BrowserContext


async def _username_login(login_po: LoginPage, logger: Logger, username: str, password: str, timeout: float = 5.0):
    # 1. 输入用户名
    username_input = await login_po.get_login_username_input(timeout=timeout)
    await username_input.fill(value=username.strip())
    logger.info(f"东方航空官网登录页面，用户名<{username}>输入完成")

    # 2. 输入密码
    password_input = await login_po.get_login_password_input(timeout=timeout)
    await password_input.fill(value=password.strip())
    logger.info(f"东方航空官网登录页面，密码<{password}>输入完成")

    # 3. 勾选【隐私政策】同意单选框
    agreed_radio = await login_po.get_agreed_radio(timeout=timeout)
    await agreed_radio.click(button="left")
    logger.info("东方航空官网登录页面，【隐私政策】单选框勾选完成")

    # 4. 点击登录
    login_btn = await login_po.get_login_btn(timeout=timeout)
    await login_btn.click(button="left")
    logger.info("东方航空官网登录页面，【立即登录】按钮点击完成")

    await asyncio.sleep(delay=timeout * 6)
    # 5. 判断是否为当前页
    if login_po.is_current_page() is True:
        raise RuntimeError(f"东方航空官网登录页面，用户：{username}, 密码：{password}登录失败")


async def username_login_callback(
        *, page: Page, logger: Logger, context: BrowserContext, protocol: str, main_domain: str, sso_domain: str,
        username: str, password: str, timeout: float = 10.0, **kwargs: Any
) -> Dict[str, Any]:
    sso_url_prefix = f"{protocol}://{sso_domain}"
    sso_url_suffix = url_const.login_url.format(protocol, main_domain)
    sso_url = sso_url_prefix + sso_url_suffix
    await page.goto(sso_url)
    await asyncio.sleep(delay=timeout)

    if LoginPage.iss_current_page(page=page, url=sso_url):
        login_po = LoginPage(page)
        await _username_login(login_po=login_po, logger=logger, username=username, password=password, timeout=timeout)
        logger.info(f"东方航空官网登录页面，用户：{username}, 密码：{password}登录成功")
    else:
        logger.info(f"用户：{username}，在东方航空官网存在登录状态，当前登录流程将跳过")
    return await context.storage_state()
