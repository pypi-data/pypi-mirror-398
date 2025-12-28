# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  python-ceair-helper
# FileName:     cashier_desk_web_page_detail_page.py
# Description:  支付详情页面对象
# Author:       ASUS
# CreateDate:   2025/12/10
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from typing import Dict, Any
from datetime import datetime
from playwright_helper.libs.base_po import BasePo
from ceair_helper.config.url_const import desk_web_pay_details_url
from playwright_helper.utils.type_utils import convert_order_amount_text
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError, Locator, Error as PlaywrightError


class CVVPaymentPage(BasePo):
    url: str = desk_web_pay_details_url
    __page: Page

    def __init__(self, page: Page, url: str = desk_web_pay_details_url) -> None:
        super().__init__(page, url)
        self.url = url
        self.__page = page

    async def get_pre_order_number(self, timeout: float = 5.0) -> str:
        """
        支付详情页获取待支付订单号
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="order-title"]/span'
        locator = await self.get_locator(selector=selector, timeout=timeout)
        return (await locator.inner_text()).strip()

    """ 卡片信息区域 """

    async def get_form_bank_card_id_number_input(self, timeout: float = 5.0) -> Locator:
        """
        支付详情页获取【卡号】输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//form[@class="ceair-form ceair-form--label-top"]//input[@placeholder="请填写卡号"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_form_cvv_input(self, timeout: float = 5.0) -> Locator:
        """
        支付详情页获取【CVV】输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//form[@class="ceair-form ceair-form--label-top"]//input[@placeholder="请填写CVV"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_expiration_year_dropdown(self, timeout: float = 5.0) -> Locator:
        """
        支付详情页获取【有效期年份】下拉框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        year: int = datetime.now().year
        selector: str = f'//form[@class="ceair-form ceair-form--label-top"]//div[@class="ceair-select-selection"]//span[contains(text(), "{year}")]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_dropdown_with_expiration_year(self, expiration_year: str, timeout: float = 5.0) -> Locator:
        """
        支付详情页获取有效期下拉框选项中的【expiration_year】
        :param expiration_year: 有效期截止年份
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = f'//form[@class="ceair-form ceair-form--label-top"]//div[@class="ceair-select-dropdown"]//span[contains(text(), "{expiration_year}")]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_expiration_month_dropdown(self, timeout: float = 5.0) -> Locator:
        """
        支付详情页获取【有效期月份】下拉框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '(//form[@class="ceair-form ceair-form--label-top"]//div[@class="ceair-select-selection"]//span[@class="ceair-select-selected-value"])[3]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_dropdown_with_expiration_month(self, expiration_month: str, timeout: float = 5.0) -> Locator:
        """
        支付详情页获取有效期下拉框选项中的【expiration_month】
        :param expiration_month: 有效期截止月份，格式：1,2,3...11,12
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = f'//form[@class="ceair-form ceair-form--label-top"]//li[@class="ceair-select-item"]//span[normalize-space(text())="{expiration_month}"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    """ 个人信息区域 """

    async def get_form_first_name_input(self, timeout: float = 5.0) -> Locator:
        """
        支付详情页获取【持卡人名】输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//form[@class="ceair-form ceair-form--label-top"]//input[@placeholder="请填写持卡人名"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_form_last_name_input(self, timeout: float = 5.0) -> Locator:
        """
        支付详情页获取【持卡人姓】输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//form[@class="ceair-form ceair-form--label-top"]//input[@placeholder="请填写持卡人姓"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_form_id_number_input(self, timeout: float = 5.0) -> Locator:
        """
        支付详情页获取【证件号】输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//form[@class="ceair-form ceair-form--label-top"]//input[@placeholder="请填写证件号"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_form_email_input(self, timeout: float = 5.0) -> Locator:
        """
        支付详情页获取【电子邮箱】输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//form[@class="ceair-form ceair-form--label-top"]//div[@class="ceair-input"]//input[@placeholder="电子邮箱"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_form_mobile_input(self, timeout: float = 5.0) -> Locator:
        """
        支付详情页获取【银行预留号码】输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//form[@class="ceair-form ceair-form--label-top"]//input[@placeholder="请填写银行预留号码"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_id_type_dropdown(self, timeout: float = 5.0) -> Locator:
        """
        支付详情页获取【证件类型】下拉框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '(//form[@class="ceair-form ceair-form--label-top"]//div[@class="ceair-select-selection"]//span[@class="ceair-select-selected-value" and normalize-space(text())="-"])[1]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_dropdown_with_id_type(self, id_type: str, timeout: float = 5.0) -> Locator:
        """
        支付详情页获取证件类型下拉框选项中的【id_type】
        :param id_type: 证件类型，例如：身份证，护照，军官证
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = f'//form[@class="ceair-form ceair-form--label-top"]//li[@class="ceair-select-item"]//span[normalize-space(text())="{id_type}"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    """ 联系地址区域 """

    async def get_country_dropdown(self, timeout: float = 5.0) -> Locator:
        """
        支付详情页获取【国家/地区】下拉框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '(//div[@class="ceair-select-selection"])[5]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_dropdown_with_country(self, country: str, timeout: float = 5.0) -> Locator:
        """
        支付详情页获取国家/地区下拉框选项中的【id_type】
        :param country: 国家名称，例如：A-埃及，A-埃塞俄比亚，Z-中国
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = f'//form[@class="ceair-form ceair-form--label-top"]//li[@class="ceair-select-item"]//span[normalize-space(text())="{country}"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_state_dropdown(self, timeout: float = 5.0) -> Locator:
        """
        支付详情页获取【省/州】下拉框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '(//div[@class="ceair-select-selection"]//span[@class="ceair-select-selected-value"])[6]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_dropdown_with_state(self, state: str, timeout: float = 5.0) -> Locator:
        """
        支付详情页获取证件类型下拉框选项中的【id_type】
        :param state: 省/州，例如：湖北省，加尼福利亚州
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = f'//ul[@class="ceair-select-dropdown-list dropdown-list"]/li[@class="ceair-select-item"]/span[normalize-space(text())="{state}"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_form_city_input(self, timeout: float = 5.0) -> Locator:
        """
        支付详情页获取【城市】输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//form[@class="ceair-form ceair-form--label-top"]//input[@placeholder="请填写城市"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_form_street_input(self, timeout: float = 5.0) -> Locator:
        """
        支付详情页获取【街道名称】输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//form[@class="ceair-form ceair-form--label-top"]//input[@placeholder="街道名称"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_form_house_number_input(self, timeout: float = 5.0) -> Locator:
        """
        支付详情页获取【门牌号吗】输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//form[@class="ceair-form ceair-form--label-top"]//input[@placeholder="请填写门牌号码"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_form_postal_code_input(self, timeout: float = 5.0) -> Locator:
        """
        支付详情页获取【邮政编码】输入框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//form[@class="ceair-form ceair-form--label-top"]//input[@placeholder="请填写邮编"]'
        return await self.get_locator(selector=selector, timeout=timeout)

    """ 支付区域 """

    async def get_payment_total_amount(self, timeout: float = 5.0) -> Dict[str, Any]:
        """
        支付详情页获取待支付总金额
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="side-wrapper fr clear"]//div[@class="fr total-price-red"]'
        locator = await self.get_locator(selector=selector, timeout=timeout)
        total_amount: str = (await locator.inner_text()).strip()
        return convert_order_amount_text(amount_text=total_amount)

    async def get_submit_pay_btn(self, timeout: float = 5.0) -> Locator:
        """
        支付详情页获取【下一步】按钮
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="side-wrapper fr clear"]/button'
        return await self.get_locator(selector=selector, timeout=timeout)

    """ 系统提示 """

    async def get_system_prompt_dialog(self, timeout: float = 5.0) -> Dict[str, Any]:
        """
        支付详情页获取【系统提示】弹框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        prompt_msg_selector: str = '//div[@class="ceair-modal-confirm-body-confirm flex ju-center"]/div'
        confirm_btn_selector: str = '//div[@class="ceair-modal-confirm"]//span[normalize-space(text())="确认"]'
        dialog_info = dict()
        try:
            confirm_btn_locator = await self.get_locator(selector=confirm_btn_selector, timeout=timeout)
            dialog_info["confirm_btn_locator"] = confirm_btn_locator
            try:
                prompt_msg_locator = await self.get_locator(prompt_msg_selector, timeout=timeout)
                dialog_info["prompt_msg"] = (await prompt_msg_locator.inner_text()).strip()
            except (PlaywrightTimeoutError, PlaywrightError, Exception):
                pass
        except (PlaywrightTimeoutError, PlaywrightError, Exception):
            pass

        return dialog_info

    async def get_rating_ten_checkbox(self, timeout: float = 5.0) -> Locator:
        """
        支付详情页支付成功后，获取评价弹框中10分单选框
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//div[@class="img-select"]//div[@class="img-box" and contains(text(), 10)]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_rating_dialog_submit_btn(self, timeout: float = 5.0) -> Locator:
        """
        支付详情页支付成功后，获取评价弹框中的【提交】按钮
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//span[@class="ceair-button-text" and contains(text(), "提交")]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_rating_dialog_no_thanks_btn(self, timeout: float = 5.0) -> Locator:
        """
        支付详情页支付成功后，获取评价弹框中的【不，谢谢】按钮
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//span[@class="ceair-button-text" and contains(text(), "不，谢谢")]'
        return await self.get_locator(selector=selector, timeout=timeout)

    async def get_actual_payment_amount(self, timeout: float = 5.0) -> Dict[str, Any]:
        """
        支付详情页支付成功后，获取页面中的实际支付金额
        :param timeout: 超时时间（秒）
        :return: (是否存在, 错误信息|元素对象)
        """
        selector: str = '//span[contains(@class, "payment-result-order-detail-money")]'
        locator = await self.get_locator(selector=selector, timeout=timeout)
        actual_payment_amount: str = (await locator.inner_text()).strip()
        return convert_order_amount_text(amount_text=actual_payment_amount)
