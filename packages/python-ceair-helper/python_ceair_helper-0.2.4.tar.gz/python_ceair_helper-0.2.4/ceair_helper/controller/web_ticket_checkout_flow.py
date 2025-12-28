# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  python-ceair-helper
# FileName:     web_ticket_checkout_flow.py
# Description:  web端出票流程
# Author:       ASUS
# CreateDate:   2025/12/16
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from logging import Logger
from typing import Tuple
from playwright.async_api import Page
from typing import List, Dict, Any, Callable
from ceair_helper.controller.order_payment import order_payment_callback
from ceair_helper.controller.booking_flight import booking_flight_callback


async def web_ticket_checkout_flow(
        *, page: Page, logger: Logger, dep_city: str, arr_city: str, flight_no: str, cabin_class: str,
        price_sell: float, prodcut_name: str, passengers: List[Dict[str, Any]], email: str, mobile: str,
        price_std: float, order_cabin_code: str, dep_date: str, protocol: str, main_domain: str, timeout: float = 10.0,
        price_increase_threshold: float = 20.0, price_reduction_threshold: float = 10.0, uc_domain: str, order_id: int,
        create_pay_card_callback: Callable, payment_info: Dict[str, Any], **kwargs: Any
) -> Tuple[str, float]:
    await booking_flight_callback(
        page=page, logger=logger, dep_city=dep_city, arr_city=arr_city, flight_no=flight_no, cabin_class=cabin_class,
        price_std=price_std, price_sell=price_sell, prodcut_name=prodcut_name, passengers=passengers, email=email,
        mobile=mobile, order_cabin_code=order_cabin_code, dep_date=dep_date, protocol=protocol, domain=main_domain,
        timeout=timeout, price_increase_threshold=price_increase_threshold,
        price_reduction_threshold=price_reduction_threshold, **kwargs
    )
    return await order_payment_callback(
        page=page, logger=logger, protocol=protocol, pay_domain=main_domain, uc_domain=uc_domain, order_id=order_id,
        flight_no=flight_no, payment_info=payment_info, create_pay_card_callback=create_pay_card_callback,
        timeout=timeout, **kwargs
    )
