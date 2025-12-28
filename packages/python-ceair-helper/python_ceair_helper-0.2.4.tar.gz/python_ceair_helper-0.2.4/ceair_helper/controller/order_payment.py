# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  python-ceair-helper
# FileName:     order_payment.py
# Description:  订单支付控制器模块
# Author:       ASUS
# CreateDate:   2025/12/11
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import inspect
from logging import Logger
from typing import Callable, Dict, Any, Tuple
import ceair_helper.config.url_const as url_const
from ceair_helper.po.payment_page import PaymentPage
from playwright_helper.utils.browser_utils import switch_for_table_window
from ceair_helper.po.cashier_desk_web_page_detail_page import CVVPaymentPage
from ceair_helper.controller.my_order_query import first_open_page_query_order_payment_state
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError


async def _select_world_pay_type(payment_po: PaymentPage, logger: Logger, timeout: float = 10.0) -> str:
    # 1. 获取待支付的订单号
    pre_order_number = await payment_po.get_pre_order_number(timeout=timeout)
    logger.info(f'支付页面，官网订单号<{pre_order_number}>获取成功')

    # 2. 选择【VISA】支付方式
    world_pay_icon = await payment_po.get_world_pay_icon(timeout=timeout)
    await world_pay_icon.click(button="left")
    logger.info(f"支付页面，支付方式：【VISA】已选中")

    # 3. 点击【确认支付】
    submit_pay_btn = await payment_po.get_submit_pay_btn(timeout=timeout)
    await submit_pay_btn.click(button="left")
    logger.info(f"支付页面，【确认支付】按钮点击完成")

    return pre_order_number


async def _fill_cvv_payment(
        cvv_po: CVVPaymentPage, logger: Logger, create_pay_card_callback: Callable, payment_info: Dict[str, Any],
        order_id: int, flight_no: str, timeout: float = 10.0
) -> float:
    """
    填写虚拟卡支付信息
    :param cvv_po: cvv码
    :param logger: 日志对象
    :param create_pay_card_callback: 创建虚拟卡回调方法
    :param payment_info: 支付详情页面的其他信息，格式：{"first_name":"HanLin", "last_name":"Zhou", "id_number": "12123123123132", "email": "ckf10000@sina.com","mobile":"19339393939", "id_type":"身份证", "country": "Z-中国", "city":"长沙", "street":"洋湖街道", "house_number": "晚安家居", "postal_code": "518000"}
    :param timeout: 超时时长
    :return: str
    """
    # 1. 获取待支付的订单号
    pre_order_number = await cvv_po.get_pre_order_number(timeout=timeout)
    logger.info(f'支付详情页面，收银台编号<{pre_order_number}>获取成功')

    if inspect.iscoroutinefunction(create_pay_card_callback):
        callback_result: Dict[str, Any] = await create_pay_card_callback()
    else:
        callback_result: Dict[str, Any] = create_pay_card_callback()
    if not callback_result.get("data"):
        raise RuntimeError(f"支付详情页面，空中云付接口返回的数据异常：{str(callback_result)}")
    card_info = callback_result.get("data")
    logger.info(f"支付详情页面，空中云付接口返回虚拟卡信息：{card_info}")
    card_number: str = card_info.get("card_number")
    cvv: str = card_info.get("cvv")
    expiry_month: int = card_info.get("expiry_month")
    expiry_year: int = card_info.get("expiry_year")
    # name_on_card: str = card_info.get("name_on_card")

    # 2. 填写支付卡信息
    bank_card_id_number_input = await cvv_po.get_form_bank_card_id_number_input(timeout=timeout)
    await bank_card_id_number_input.fill(value=card_number)
    logger.info(f"支付详情页面，卡片信息区域，卡号<{card_number}>输入完成")

    # 3. 填写CVV信息
    cvv_input = await cvv_po.get_form_cvv_input(timeout=timeout)
    await cvv_input.fill(value=cvv)
    logger.info(f"支付详情页面，卡片信息区域，CVV<{cvv}>输入完成")

    # 4. 填写有效期年份信息
    expiration_year_dropdown = await cvv_po.get_expiration_year_dropdown(timeout=timeout)
    await expiration_year_dropdown.click(button="left")
    dropdown_with_expiration_year = await cvv_po.get_dropdown_with_expiration_year(
        expiration_year=str(expiry_year), timeout=timeout
    )
    await dropdown_with_expiration_year.click(button="left")
    logger.info(f"支付详情页面，卡片信息区域，有效期年份<{expiry_year}>选择完成")

    # 5. 填写有效期月份信息
    expiration_month_dropdown = await cvv_po.get_expiration_month_dropdown(timeout=timeout)
    await expiration_month_dropdown.click(button="left")
    dropdown_with_expiration_month = await cvv_po.get_dropdown_with_expiration_month(
        expiration_month=str(expiry_month), timeout=timeout
    )
    await dropdown_with_expiration_month.click(button="left")
    logger.info(f"支付详情页面，卡片信息区域，有效期月份<{expiry_month}>选择完成")

    # 6. 填写持卡人名
    first_name_input = await cvv_po.get_form_first_name_input(timeout=timeout)
    await first_name_input.fill(value=payment_info.get("first_name"))
    logger.info(f"支付详情页面，个人信息区域，持卡人名<{payment_info.get("first_name")}>输入完成")

    # 7. 填写持卡人姓
    last_name_input = await cvv_po.get_form_last_name_input(timeout=timeout)
    await last_name_input.fill(value=payment_info.get("last_name"))
    logger.info(f"支付详情页面，个人信息区域，持卡人姓<{payment_info.get("last_name")}>输入完成")

    # 8. 填写证件号
    id_number_input = await cvv_po.get_form_id_number_input(timeout=timeout)
    await id_number_input.fill(value=payment_info.get("id_number"))
    logger.info(f"支付详情页面，个人信息区域，证件号<{payment_info.get("id_number")}>输入完成")

    # 9. 填写电子邮箱
    email_input = await cvv_po.get_form_email_input(timeout=timeout)
    await email_input.fill(value=payment_info.get("email"))
    logger.info(f"支付详情页面，个人信息区域，电子邮箱<{payment_info.get("email")}>输入完成")

    # 10. 填写银行预留号码
    mobile_input = await cvv_po.get_form_mobile_input(timeout=timeout)
    await mobile_input.fill(value=payment_info.get("mobile"))
    logger.info(f"支付详情页面，个人信息区域，银行预留号码<{payment_info.get("mobile")}>输入完成")

    # 11. 证件类型选择【身份证】
    id_type_dropdown = await cvv_po.get_id_type_dropdown(timeout=timeout)
    await id_type_dropdown.click(button="left")
    dropdown_with_id_type = await cvv_po.get_dropdown_with_id_type(id_type=payment_info.get("id_type"), timeout=timeout)
    await dropdown_with_id_type.click(button="left")
    logger.info(f"支付详情页面，个人信息区域，证件类型选择<{payment_info.get("id_type")}>已完成")

    # 12.国家/地区选择【M-美国】
    country_dropdown = await cvv_po.get_country_dropdown(timeout=timeout)
    await country_dropdown.click(button="left")
    dropdown_with_country = await cvv_po.get_dropdown_with_country(country=payment_info.get("country"), timeout=timeout)
    await dropdown_with_country.click(button="left")
    logger.info(f"支付详情页面，联系地址区域，国家/地区选择<{payment_info.get("country")}>已完成")

    # 13. 省/州选择【加尼福利亚州】
    state_dropdown = await cvv_po.get_state_dropdown(timeout=timeout)
    await state_dropdown.click(button="left")
    dropdown_with_state = await cvv_po.get_dropdown_with_state(state=payment_info.get("state"), timeout=timeout)
    await dropdown_with_state.click(button="left")
    logger.info(f"支付详情页面，联系地址区域，省/州<{payment_info.get("state")}>输入完成")

    # 14. 填写城市
    city_input = await cvv_po.get_form_city_input(timeout=timeout)
    await city_input.fill(value=payment_info.get("city"))
    logger.info(f"支付详情页面，联系地址区域，城市<{payment_info.get("city")}>输入完成")

    # 15. 填写街道名称
    street_input = await cvv_po.get_form_street_input(timeout=timeout)
    await street_input.fill(value=payment_info.get("street"))
    logger.info(f"支付详情页面，联系地址区域，街道名称<{payment_info.get("street")}>输入完成")

    # 16. 填写门牌号吗
    house_number_input = await cvv_po.get_form_house_number_input(timeout=timeout)
    await house_number_input.fill(value=payment_info.get("house_number"))
    logger.info(f"支付详情页面，联系地址区域，门牌号吗<{payment_info.get("house_number")}>输入完成")

    # 17. 填写邮政编码
    postal_code_input = await cvv_po.get_form_postal_code_input(timeout=timeout)
    await postal_code_input.fill(value=payment_info.get("postal_code"))
    logger.info(f"支付详情页面，联系地址区域，邮政编码<{payment_info.get("postal_code")}>输入完成")

    # 18. 点击【下一步】
    submit_pay_btn = await cvv_po.get_submit_pay_btn(timeout=timeout)
    await submit_pay_btn.click(button="left")
    logger.info(f"支付详情页面，支付区域，【下一步】按钮点击完成")

    # 19. 点击系统提示【确认】
    system_prompt_dialog: Dict[str, Any] = await cvv_po.get_system_prompt_dialog(timeout=timeout)
    confirm_btn_locator = system_prompt_dialog.get("confirm_btn_locator")
    prompt_msg = system_prompt_dialog.get("prompt_msg")
    if confirm_btn_locator:
        if prompt_msg:
            logger.info(f"支付详情页面，系统提示弹框内容：{prompt_msg}")
        await confirm_btn_locator.click(button="left")
        logger.info(f"支付详情页面，系统提示弹框，【确认】按钮点击完成")
    logger.info(
        f"劲旅订单<{order_id}>，航班<{flight_no}>，收银台编号<{pre_order_number}>，采用空中云汇卡<{card_number}>支付完成"
    )

    try:
        # 20. 点击评价框中的10分
        rating_ten_checkbox = await cvv_po.get_rating_ten_checkbox(timeout=timeout)
        await rating_ten_checkbox.click(button="left")
        logger.info(f"支付详情页面，支付成功，评价分【10】单选icom点击完成")

        # 21. 点击评价框中的10分
        rating_dialog_submit_btn = await cvv_po.get_rating_dialog_submit_btn(timeout=timeout)
        await rating_dialog_submit_btn.click(button="left")
        logger.info(f"支付详情页面，支付成功，【提交】按钮点击完成")

        # 22. 点击评价框中的【不，谢谢】按钮
        rating_dialog_no_thanks_btn = await cvv_po.get_rating_dialog_no_thanks_btn(timeout=timeout)
        await rating_dialog_no_thanks_btn.click(button="left")
        logger.info(f"支付详情页面，支付成功，【不，谢谢】按钮点击完成")

        # 23. 支付成功后，获取实际支付金额
        actual_payment_amount = await cvv_po.get_actual_payment_amount(timeout=timeout)
        logger.info(f"支付详情页面，支付成功，实际支付金额<{actual_payment_amount}>已获取")
        return actual_payment_amount.get("amount")
    except (PlaywrightError, PlaywrightTimeoutError, RuntimeError, Exception) as e:
        logger.error(e)
        return 0


async def order_payment_callback(
        *, page: Page, logger: Logger, protocol: str, pay_domain: str, uc_domain: str, order_id: int, flight_no: str,
        create_pay_card_callback: Callable, payment_info: Dict[str, Any], timeout: float = 10.0, **kwargs: Any
) -> Tuple[str, float]:
    payment_url_prefix = f"{protocol}://{pay_domain}"
    payment_url_suffix = url_const.pay_url
    payment_url = payment_url_prefix + payment_url_suffix
    payment_page = PaymentPage(page)
    await payment_page.url_wait_for(url=payment_url, timeout=timeout)
    logger.info(f"即将进入支付页面，页面URL<{payment_url}>")
    pre_order_id: str = await _select_world_pay_type(payment_po=payment_page, logger=logger, timeout=timeout)

    desk_web_pay_url_prefix = f"{protocol}://{uc_domain}"
    desk_web_pay_details_url_suffix = url_const.desk_web_pay_details_url
    desk_web_pay_details_url = desk_web_pay_url_prefix + desk_web_pay_details_url_suffix
    desk_web_pay_page = await switch_for_table_window(
        browser=kwargs.get("context"), url_keyword=desk_web_pay_details_url_suffix, wait_time=int(timeout)
    )
    desk_web_pay_details_po = CVVPaymentPage(desk_web_pay_page)
    await desk_web_pay_details_po.url_wait_for(url=desk_web_pay_details_url, timeout=timeout)
    logger.info(f"即将进入支付详情页面，页面URL<{desk_web_pay_details_url}>")
    actual_payment_amount = await _fill_cvv_payment(
        cvv_po=desk_web_pay_details_po, logger=logger, create_pay_card_callback=create_pay_card_callback,
        order_id=order_id, flight_no=flight_no, payment_info=payment_info, timeout=timeout
    )
    if actual_payment_amount == 0:
        # {"currency": "¥", "amount": 2008, "order_state": "交易成功|交易成功(有退票)|交易取消|等待支付", "detail_btn_locator": Locator对象}
        order_payment_state: Dict[str, Any] = await first_open_page_query_order_payment_state(
            page=page, logger=logger, ceair_protocol=protocol, ceair_domain=pay_domain, pre_order_id=pre_order_id,
            timeout=timeout
        )
        actual_payment_amount = order_payment_state.get("amount")
        if order_payment_state.get("order_state"):
            if "交易成功" not in order_payment_state.get("order_state"):
                raise RuntimeError(
                    f'支付失败，支付完成后，订单状态还处于：<{order_payment_state.get("order_state")}>'
                )
        else:
            raise RuntimeError(f"支付失败，支付完成后，查询订单状态异常: <{order_payment_state}>")
    logger.info(f"订单：<{order_id}>，航班<{flight_no}>支付流程结束")
    return pre_order_id, actual_payment_amount
