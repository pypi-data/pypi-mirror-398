# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     order_detail.py
# Description:  订单详情页面控制器
# Author:       ASUS
# CreateDate:   2025/11/29
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import aiohttp
import asyncio
from logging import Logger
from datetime import datetime
import qlv_helper.config.url_const as url_const
from typing import Dict, Any, List, cast, Optional
from qlv_helper.po.order_detail_page import OrderDetailPage
from qlv_helper.http.order_page import parser_order_info, get_order_page_html, parser_order_flight_table, \
    fill_procurement_info_with_http, fill_itinerary_info_with_http
from playwright.async_api import Page, Locator, Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError


async def get_order_info_with_http(
        *, order_id: int, domain: str, protocol: str = "http", retry: int = 1, timeout: int = 5,
        enable_log: bool = True, cookie_jar: Optional[aiohttp.CookieJar] = None, playwright_state: Dict[str, Any] = None
) -> Dict[str, Any]:
    response = await get_order_page_html(
        order_id=order_id, domain=domain, protocol=protocol, retry=retry, timeout=timeout, enable_log=enable_log,
        cookie_jar=cookie_jar, playwright_state=playwright_state
    )
    if response.get("code") != 200:
        return response

    html = response.get("data")
    order_info = parser_order_info(html=html)
    flight_info = parser_order_flight_table(html=html)
    if flight_info:
        order_info["flights"] = flight_info
        order_info["peoples"] = flight_info
    response["data"] = order_info
    return response


async def open_order_detail_page(
        *, page: Page, logger: Logger, protocol: str, domain: str, order_id: int, timeout: float = 20.0
) -> OrderDetailPage:
    url_prefix = f"{protocol}://{domain}"
    current_dtstr: str = datetime.now().strftime("%Y%m%d%H%M%S")
    order_detail_url_suffix = url_const.order_detail_url.format(order_id, current_dtstr)
    order_detail_url = url_prefix + order_detail_url_suffix
    await page.goto(order_detail_url)

    order_detail_po = OrderDetailPage(page=page, url=order_detail_url)
    await order_detail_po.url_wait_for(url=order_detail_url, timeout=timeout)
    logger.info(f"即将劲旅订单详情页面，页面URL<{order_detail_url}>")

    try:
        confirm_btn = await order_detail_po.get_message_notice_dialog_confirm_btn(timeout=1)
        await confirm_btn.click(button="left")
        logger.info("订单详情页面，消息提醒弹框，【确认】按钮点击完成")
    except (PlaywrightTimeoutError, PlaywrightError, RuntimeError, Exception):
        pass
    return order_detail_po


async def add_custom_remark(*, logger: Logger, page: OrderDetailPage, remark: str, timeout: float = 5.0) -> None:
    # 1. 添加自定义备注
    custom_remark_input = await page.get_custom_remark_input(timeout=timeout)
    await custom_remark_input.fill(value=remark)
    logger.info(f"订单详情页面，日志记录栏，自定义备注：{remark}，输入完成")

    # 2. 点击【保存备注】按钮
    custom_remark_save_btn = await page.get_custom_remark_save_btn(timeout=timeout)
    await custom_remark_save_btn.click(button="left")
    logger.info(f"订单详情页面，日志记录栏，【保存备注】按钮点击完成")


async def update_order_policy(
        *, page: OrderDetailPage, logger: Logger, policy: str, order_id: int, timeout: float = 5.0
) -> None:
    # 1. 修改政策代码
    policy_input = await page.get_policy_input(timeout=timeout)
    await policy_input.fill(value=policy)

    # 2. 执行回车按键
    await policy_input.press("Enter")
    logger.info(f"订单<{order_id}>，政策代码已更新成<{policy}>完成")


async def order_unlock(
        *, logger: Logger, page: OrderDetailPage, remark: str, order_id: int, is_force: bool = False,
        qlv_user_id: Optional[str] = None, timeout: float = 5.0
) -> None:
    # 1. 获取订单操作锁的状态
    lock_state, lock_btn = await page.get_order_lock_state_btn(timeout=timeout)
    if "强制解锁" in lock_state:
        if is_force is False:
            raise EnvironmentError(f"被他人锁定，无需解锁处理")
        await lock_btn.click(button="left")
        logger.info(f"订单详情页面，用户操作【{lock_state}】按钮点击完成")
        try:
            confirm_btn = await page.get_message_notice_dialog_confirm_btn(timeout=1)
            await confirm_btn.click(button="left")
            logger.info("订单详情页面，强制解锁弹框确认，【确认】按钮点击完成")
            await asyncio.sleep(2)
        except (PlaywrightTimeoutError, PlaywrightError, RuntimeError, Exception):
            pass
        logger.warning(f"订单<{order_id}>，已被用户<{qlv_user_id or '无记录'}>强制解锁")
        # 再次获取订单操作锁的状态
        lock_state, lock_btn = await page.get_order_lock_state_btn(timeout=timeout)
    elif "锁定" in lock_state:
        logger.info(f"订单<{order_id}>，处于无锁状态，无需解锁处理")
        return
    elif "操作" in lock_state:
        await lock_btn.click(button="left")
        await asyncio.sleep(2)
        lock_state_temp = lock_state
        lock_state, lock_btn = await page.get_order_lock_state_btn(timeout=timeout)
        logger.info(f"订单详情页面，日志记录栏，【{lock_state_temp}】按钮点击完成")
    if remark:
        # 2. 添加解锁备注
        await add_custom_remark(logger=logger, page=page, remark=remark, timeout=timeout)

    # 3. 点击【解锁返回】按钮
    await lock_btn.click(button="left")
    await asyncio.sleep(2)
    logger.info(f"订单详情页面，日志记录栏，【{lock_state}】按钮点击完成")


async def order_locked(
        *, logger: Logger, page: OrderDetailPage, order_id: int, is_force: bool = False, timeout: float = 5.0,
        qlv_user_id: Optional[str] = None
) -> None:
    # 1. 获取订单操作锁的状态
    lock_state, lock_btn = await page.get_order_lock_state_btn(timeout=timeout)
    if "强制解锁" in lock_state:
        if is_force is False:
            raise EnvironmentError(f"被他人锁定，不做加锁处理")
        await lock_btn.click(button="left")
        logger.info(f"订单详情页面，用户操作【{lock_state}】按钮点击完成")
        try:
            confirm_btn = await page.get_message_notice_dialog_confirm_btn(timeout=1)
            await confirm_btn.click(button="left")
            logger.info("订单详情页面，强制解锁弹框确认，【确认】按钮点击完成")
            await asyncio.sleep(2)
        except (PlaywrightTimeoutError, PlaywrightError, RuntimeError, Exception):
            pass
        logger.warning(f"订单<{order_id}>，已被用户<{qlv_user_id or '无记录'}>强制解锁")
        return
    elif "解锁返回" in lock_state:
        logger.warning(f"订单<{order_id}>，处于锁定状态，不做加锁处理")
        return
    # 2. 点击【锁定|操作】按钮
    await lock_btn.click(button="left")
    logger.info(f"订单详情页面，日志记录栏，【{lock_state}】按钮点击完成")


async def first_open_page_order_locked(
        *, logger: Logger, page: Page, protocol: str, domain: str, order_id: int, is_force: bool = False,
        qlv_user_id: Optional[str] = None, timeout: float = 5.0, **kwargs
) -> OrderDetailPage:
    # 1. 打开页面
    order_detail_po = await open_order_detail_page(
        page=page, logger=logger, protocol=protocol, domain=domain, order_id=order_id, timeout=timeout
    )

    # 2. 锁定订单
    await order_locked(
        logger=logger, page=order_detail_po, order_id=order_id, timeout=timeout, is_force=is_force,
        qlv_user_id=qlv_user_id
    )
    return order_detail_po


async def first_open_page_order_unlock(
        *, logger: Logger, page: Page, protocol: str, domain: str, order_id: int, is_force: bool = False,
        qlv_user_id: Optional[str] = None, timeout: float = 5.0, remark: Optional[str] = None, **kwargs
) -> OrderDetailPage:
    # 1. 打开页面
    order_detail_po = await open_order_detail_page(
        page=page, logger=logger, protocol=protocol, domain=domain, order_id=order_id, timeout=timeout
    )

    # 2. 解锁订单
    await order_unlock(
        logger=logger, page=order_detail_po, order_id=order_id, timeout=timeout, is_force=is_force,
        qlv_user_id=qlv_user_id, remark=remark
    )
    return order_detail_po


async def fill_procurement_info(
        *, logger: Logger, page: OrderDetailPage, order_id: int, out_ticket_platform_type: str, purchase_amount: float,
        out_ticket_platform: str, out_ticket_account: str, purchase_account_type: str, purchase_account: str,
        ceair_user_id: str, ceair_password: str, payment_id: str, platform_order_id: str, timeout: float = 5.0
) -> None:
    # 1. 出票地类型选择【out_ticket_platform_type】
    out_ticket_platform_type_dropdown = await page.get_out_ticket_platform_type_dropdown(timeout=timeout)
    await out_ticket_platform_type_dropdown.select_option(label=out_ticket_platform_type)
    # await out_ticket_platform_type_dropdown.click(button="left")
    # out_ticket_platform_type_select_option = await page.get_out_ticket_platform_type_select_option(
    #     select_option=out_ticket_platform_type, timeout=timeout
    # )
    # await out_ticket_platform_type_select_option.click(button="left")
    logger.info(f"订单详情页面，采购信息栏，出票地类型选择<{out_ticket_platform_type}>已完成")
    await asyncio.sleep(1)

    # 2. 出票平台选择【out_ticket_platform】
    out_ticket_platform_dropdown = await page.get_out_ticket_platform_dropdown(timeout=timeout)
    await out_ticket_platform_dropdown.select_option(label=out_ticket_platform)
    # await out_ticket_platform_dropdown.click(button="left")
    # out_ticket_platform_select_option = await page.get_out_ticket_platform_select_option(
    #     select_option=out_ticket_platform, timeout=timeout
    # )
    # await out_ticket_platform_select_option.click(button="left")
    logger.info(f"订单详情页面，采购信息栏，出票平台选择<{out_ticket_platform}>已完成")
    await asyncio.sleep(1)

    # 3. 出票账号选择【out_ticket_account】
    out_ticket_account_dropdown = await page.get_out_ticket_account_dropdown(timeout=timeout)
    await out_ticket_account_dropdown.select_option(label=out_ticket_account)
    # await out_ticket_account_dropdown.click(button="left")
    # out_ticket_account_select_option = await page.get_out_ticket_account_select_option(
    #     select_option=out_ticket_account, timeout=timeout
    # )
    # await out_ticket_account_select_option.click(button="left")
    logger.info(f"订单详情页面，采购信息栏，出票账号选择<{out_ticket_account}>已完成")
    await asyncio.sleep(1)

    # 4. 采购账号类型选择【purchase_account_type】
    purchase_account_type_dropdown = await page.get_purchase_account_type_dropdown(timeout=timeout)
    await purchase_account_type_dropdown.select_option(label=purchase_account_type)
    # await purchase_account_type_dropdown.click(button="left")
    # purchase_account_type_select_option = await page.get_purchase_account_type_select_option(
    #     select_option=purchase_account_type, timeout=timeout
    # )
    # await purchase_account_type_select_option.click(button="left")
    logger.info(f"订单详情页面，采购信息栏，采购账号类型选择<{purchase_account_type}>已完成")
    await asyncio.sleep(1)

    # 5. 采购账号选择【purchase_account】
    purchase_account_dropdown = await page.get_purchase_account_dropdown(timeout=timeout)
    await purchase_account_dropdown.select_option(label=purchase_account)
    # await purchase_account_dropdown.click(button="left")
    # purchase_account_select_option = await page.get_purchase_account_select_option(
    #     select_option=purchase_account, timeout=timeout
    # )
    # await purchase_account_select_option.click(button="left")
    logger.info(f"订单详情页面，采购信息栏，采购账号选择<{purchase_account}>已完成")
    await asyncio.sleep(1)

    # 6. 填写采购金额
    purchase_amount_input = await page.get_purchase_amount_input(timeout=timeout)
    await purchase_amount_input.fill(value=str(purchase_amount))
    logger.info(f"订单详情页面，采购信息栏，采购金额<{purchase_amount}>输入完成")

    # 7. 填写备注
    remark_input = await page.get_remark_input(timeout=timeout)
    value = f"{ceair_user_id}/{ceair_password}"
    await remark_input.fill(value=value)
    logger.info(f"订单详情页面，采购信息栏，备注<{value}>输入完成")

    # 8. 填写对账标识
    main_check_input = await page.get_main_check_input(timeout=timeout)
    await main_check_input.fill(value=payment_id)
    logger.info(f"订单详情页面，采购信息栏，对账标识<{payment_id}>输入完成")

    # 9. 填写官网订单号
    air_comp_order_id_input = await page.get_air_comp_order_id_input(timeout=timeout)
    await air_comp_order_id_input.fill(value=platform_order_id)
    logger.info(f"订单详情页面，采购信息栏，官网订单号<{platform_order_id}>输入完成")

    # 10. 点击【保存采购】按钮
    procurement_info_save_btn = await page.get_procurement_info_save_btn(timeout=timeout)
    await procurement_info_save_btn.click(button="left")
    logger.info(f"订单详情页面，采购信息栏，【保存采购】按钮点击完成")


async def first_open_page_fill_procurement_info(
        *, logger: Logger, page: Page, order_id: int, protocol: str, domain: str, out_ticket_platform_type: str,
        purchase_amount: float, out_ticket_platform: str, out_ticket_account: str, purchase_account_type: str,
        purchase_account: str, ceair_user_id: str, ceair_password: str, payment_id: str, platform_order_id: str,
        is_force: bool = False, qlv_user_id: Optional[str] = None, timeout: float = 5.0, **kwargs: Any
) -> OrderDetailPage:
    # 1. 打开页面
    order_detail_po = await open_order_detail_page(
        page=page, logger=logger, protocol=protocol, domain=domain, order_id=order_id, timeout=timeout
    )

    # 2. 锁定订单
    await order_locked(
        logger=logger, page=order_detail_po, order_id=order_id, is_force=is_force, timeout=timeout,
        qlv_user_id=qlv_user_id
    )

    # 3. 回填采购信息
    await fill_procurement_info(
        out_ticket_platform_type=out_ticket_platform_type, out_ticket_account=out_ticket_account, payment_id=payment_id,
        purchase_amount=purchase_amount, out_ticket_platform=out_ticket_platform, purchase_account=purchase_account,
        purchase_account_type=purchase_account_type, ceair_user_id=ceair_user_id, ceair_password=ceair_password,
        platform_order_id=platform_order_id, timeout=timeout, logger=logger, page=order_detail_po, order_id=order_id
    )
    return order_detail_po


async def fill_itinerary(
        *, logger: Logger, page: OrderDetailPage, order_id: int, passengers_itinerary: Dict[str, Any],
        timeout: float = 5.0
) -> None:
    # 1. 获取订单操作锁的状态
    passenger_itinerary_locators: List[Dict[str, Any]] = await page.get_passenger_itinerary_locators(timeout=timeout)
    if not passenger_itinerary_locators:
        logger.warning(f"订单<{order_id}>，没有需要填写票号的乘客，直接跳过")
        return
    current_passengers = set([x.get("username") for x in passenger_itinerary_locators])
    kwargs_passengers = set(passengers_itinerary.keys())
    diff = kwargs_passengers.difference(current_passengers)
    if diff:
        raise RuntimeError(
            f"传递回填票号的乘客证件信息<{kwargs_passengers}>与订单实际乘客信息<{current_passengers}>不一致"
        )
    passenger_itinerary_locator = cast(Locator, None)
    for passenger_locator in passenger_itinerary_locators:
        current_passenger = passenger_locator.get("username")
        passenger_itinerary = passengers_itinerary.get(current_passenger)
        if passenger_itinerary:
            passenger_itinerary_locator: Locator = passenger_locator.get("locator")
            await passenger_itinerary_locator.fill(value=passenger_itinerary)
            logger.info(f"订单<{order_id}>，乘客<{current_passenger}>的票号<{passenger_itinerary}>填写完成")
        else:
            logger.warning(f"订单<{order_id}>，乘客<{current_passenger}>的票号没有获取到，本次回填跳过，等待下一次")
    if passenger_itinerary_locator:
        await passenger_itinerary_locator.press("Enter")
        logger.info(f"订单<{order_id}>，本次的票号回填完成")
    else:
        raise RuntimeError(f"回填票号过程异常，回填失败")


async def first_open_page_fill_itinerary(
        *, page: Page, logger: Logger, protocol: str, domain: str, order_id: int,
        passengers_itinerary: Dict[str, Any], timeout: float = 20.0, **kwargs: Any
) -> OrderDetailPage:
    # 1. 开发页面
    order_detail_po = await open_order_detail_page(
        page=page, logger=logger, protocol=protocol, domain=domain, order_id=order_id, timeout=timeout
    )

    # 2. 回填票号
    await fill_itinerary(
        logger=logger, page=order_detail_po, order_id=order_id, timeout=timeout,
        passengers_itinerary=passengers_itinerary
    )
    logger.info(f"订单<{order_id}>，票号回填流程结束")
    await order_unlock(logger=logger, page=order_detail_po, order_id=order_id, timeout=timeout, remark="")
    logger.info(f"订单<{order_id}>，订单解锁成功")
    return order_detail_po


async def first_open_page_update_policy(
        *, page: Page, logger: Logger, protocol: str, domain: str, order_id: int, policy: str, timeout: float = 20.0,
        **kwargs: Any
) -> OrderDetailPage:
    # 1. 打开页面
    order_detail_po = await open_order_detail_page(
        page=page, logger=logger, protocol=protocol, domain=domain, order_id=order_id, timeout=timeout
    )

    # 2. 更新订单政策代码
    await update_order_policy(
        logger=logger, page=order_detail_po, order_id=order_id, timeout=timeout, policy=policy
    )

    return order_detail_po


async def first_open_page_my_order_unlock(
        *, page: Page, logger: Logger, protocol: str, domain: str, order_id: int, qlv_user_id: str,
        policy: Optional[str] = None, remark: Optional[str] = None, timeout: float = 20.0, is_force: bool = False,
        **kwargs: Any
) -> OrderDetailPage:
    # 1. 打开页面
    order_detail_po = await open_order_detail_page(
        page=page, logger=logger, protocol=protocol, domain=domain, order_id=order_id, timeout=timeout
    )

    if policy:
        # 2. 更新订单政策代码
        await update_order_policy(
            logger=logger, page=order_detail_po, order_id=order_id, timeout=timeout, policy=policy
        )

    if remark:
        # 3. 添加解锁备注
        await add_custom_remark(logger=logger, page=order_detail_po, remark=remark, timeout=timeout)

    # 4. 获取订单操作锁的状态
    lock_state, lock_btn = await order_detail_po.get_order_lock_state_btn(timeout=timeout)
    if "强制解锁" in lock_state:
        if is_force is False:
            logger.warning(f"订单<{order_id}>，非本账号<{qlv_user_id}>的锁单，暂不处理，即将跳过")
            return order_detail_po
        await lock_btn.click(button="left")
        logger.info(f"订单详情页面，用户操作【{lock_state}】按钮点击完成")
        try:
            confirm_btn = await order_detail_po.get_message_notice_dialog_confirm_btn(timeout=1)
            await confirm_btn.click(button="left")
            logger.info("订单详情页面，强制解锁弹框确认，【确认】按钮点击完成")
            await asyncio.sleep(2)
        except (PlaywrightTimeoutError, PlaywrightError, RuntimeError, Exception):
            pass
        logger.warning(f"订单<{order_id}>，已被用户<{qlv_user_id or '无记录'}>强制解锁")
        # 再次获取订单操作锁的状态
        lock_state, lock_btn = await order_detail_po.get_order_lock_state_btn(timeout=timeout)
    elif "锁定" in lock_state:
        logger.info(f"订单<{order_id}>，处于无锁状态，无需解锁处理")
        return order_detail_po
    elif "操作" in lock_state:
        await lock_btn.click(button="left")
        await asyncio.sleep(2)
        lock_state_temp = lock_state
        lock_state, lock_btn = await order_detail_po.get_order_lock_state_btn(timeout=timeout)
        logger.info(f"订单详情页面，日志记录栏，【{lock_state_temp}】按钮点击完成")

    # 5. 点击【解锁返回】按钮
    await lock_btn.click(button="left")
    await asyncio.sleep(2)
    logger.info(f"订单详情页面，日志记录栏，【{lock_state}】按钮点击完成")
    return order_detail_po


async def fill_procurement_with_http(
        *, order_id: int, qlv_domain: str, amount: float, pre_order_id: str, platform_user_id: str, user_password: str,
        passengers: List[str], fids: str, pids: List[str], transaction_id: str, qlv_protocol: str = "http",
        retry: int = 1, timeout: int = 5, enable_log: bool = True, cookie_jar: Optional[aiohttp.CookieJar] = None,
        playwright_state: Dict[str, Any] = None, data_list: Optional[List[Dict[str, Any]]] = None, **kwargs: Any
) -> Dict[str, Any]:
    return await fill_procurement_info_with_http(
        order_id=order_id, qlv_domain=qlv_domain, amount=amount, pre_order_id=pre_order_id,
        platform_user_id=platform_user_id, user_password=user_password, passengers=passengers, fids=fids, pids=pids,
        transaction_id=transaction_id, qlv_protocol=qlv_protocol, retry=retry, timeout=timeout, enable_log=enable_log,
        cookie_jar=cookie_jar, playwright_state=playwright_state, data_list=data_list
    )


async def fill_itinerary_with_http(
        *, page: Page, logger: Logger, qlv_protocol: str, qlv_domain: str, order_id: int, retry: int = 1,
        passengers: List[Dict[str, Any]], timeout: float = 20.0, cookie_jar: Optional[aiohttp.CookieJar] = None,
        playwright_state: Dict[str, Any] = None, enable_log: bool = True, **kwargs: Any
) -> bool:
    # 1. 打开页面
    order_detail_po = await open_order_detail_page(
        page=page, logger=logger, protocol=qlv_protocol, domain=qlv_domain, order_id=order_id, timeout=timeout
    )

    # 2. 获取采购信息的流水id
    purchase_transaction_ids = await order_detail_po.get_purchase_info_transaction_id(timeout=timeout)
    purchase_transaction_ids = [x for x in purchase_transaction_ids if x != "0"]
    if purchase_transaction_ids:
        flag = True
        purchase_transaction_ids.sort()
        purchase_transaction_id = purchase_transaction_ids[0]
        for passenger in passengers:
            pid = passenger.get("pid")
            tid = passenger.get("tid")
            p_name = passenger.get("p_name")
            itinerary_id = passenger.get("itinerary_id")
            try:
                response = await fill_itinerary_info_with_http(
                    order_id=order_id, qlv_domain=qlv_domain, pid=pid, tid=tid, transaction_id=purchase_transaction_id,
                    itinerary_id=itinerary_id, retry=retry, qlv_protocol=qlv_protocol, timeout=int(timeout),
                    enable_log=enable_log, cookie_jar=cookie_jar, playwright_state=playwright_state
                )
                if response == 200 or "OK" in response.get("data"):
                    logger.info(f"订单<{order_id}>，乘客<{p_name}>票号<{itinerary_id}>回填成功")
                else:
                    logger.warning(f'订单<{order_id}>，乘客<{p_name}>票号<{itinerary_id}>回填失败：{response.get("data")}')
                    flag = False
            except (Exception,):
                flag = False
        return flag
    else:
        raise EnvironmentError("还未填写采购信息，暂时不能回填票号")
