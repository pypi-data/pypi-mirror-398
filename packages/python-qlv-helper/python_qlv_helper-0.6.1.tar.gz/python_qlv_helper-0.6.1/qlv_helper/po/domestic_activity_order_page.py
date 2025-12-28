# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     domestic_activity_order_page.py
# Description:  国内活动订单页面对象
# Author:       ASUS
# CreateDate:   2025/11/25
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from bs4 import BeautifulSoup
from typing import Tuple, Union, List, Any, Dict
from playwright_helper.libs.base_po import BasePo
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError, Locator


class DomesticActivityOrderPage(BasePo):
    __table_selector: str = '//tbody'
    __page: Page

    def __init__(self, page: Page, url: str = "/OrderList/GuoNei_ActivityOrders") -> None:
        super().__init__(page, url)
        self.__page = page

    async def get_flight_table_locator(self, timeout: float = 5.0) -> Locator:
        """
        获取table
        :param timeout:
        :return:
        """
        selecor: str = 'xpath=//table[@class="table table_hover table_border  table_center"]//tbody'
        return await self.get_locator(selector=selecor, timeout=timeout)

    async def get_flight_table_trs_locator(self, timeout: float = 5.0) -> Locator:
        """
        获取table所有tr locator对象
        :param timeout:
        :return:
        """
        selecor: str = 'xpath=//table[@class="table table_hover table_border  table_center"]/tbody/tr'
        return await self.get_locator(selector=selecor, timeout=timeout)

    async def get_flight_table_tds_th(self, locator: Locator, timeout: float = 5.0) -> Locator:
        """
        获取table所有tr下的th locator对象
        :param locator:
        :param timeout:
        :return:
        """
        selecor: str = 'xpath=./th'
        return await self.get_sub_locator(locator=locator, selector=selecor, timeout=timeout)

    async def get_flight_table_trs_td(self, locator: Locator, timeout: float = 5.0) -> Locator:
        """
        获取table所有tr下的td locator对象
        :param locator:
        :param timeout:
        :return:
        """
        selecor: str = 'xpath=./td'
        return await self.get_sub_locator(locator=locator, selector=selecor, timeout=timeout)

    async def get_flight_table_td_order_id(self, locator: Locator, timeout: float = 5.0) -> str:
        """
        获取table 行中的订单id
        :param locator:
        :param timeout:
        :return:
        """
        selecor: str = 'xpath=./a'
        locator = await self.get_sub_locator(locator=locator, selector=selecor, timeout=timeout)
        return (await locator.inner_text()).strip()

    async def get_flight_table_td_urgant(self, locator: Locator, timeout: float = 5.0) -> str:
        """
        获取table 行中的紧急状态
        :param locator:
        :param timeout:
        :return:
        """
        selecor: str = 'xpath=./font'
        locator = await self.get_sub_locator(locator=locator, selector=selecor, timeout=timeout)
        return (await locator.inner_text()).strip()

    async def get_flight_table_td_operation_lock_btn(self, locator: Locator, timeout: float = 5.0) -> Locator:
        """
        获取table 行中的锁单按钮
        :param locator:
        :param timeout:
        :return:
        """
        selecor: str = 'xpath=./a'
        return await self.get_sub_locator(locator=locator, selector=selecor, timeout=timeout)

    async def get_flight_table_td_operation_pop_btn(self, locator: Locator, timeout: float = 5.0) -> Locator:
        """
        获取table 行中的剔出按钮
        :param locator:
        :param timeout:
        :return:
        """
        selecor: str = 'xpath=./button'
        return await self.get_sub_locator(locator=locator, selector=selecor, timeout=timeout)

    async def get_flight_table_td_operation_substitute_btn(self, locator: Locator, timeout: float = 5.0) -> Locator:
        """
        获取table 行中的补位按钮
        :param locator:
        :param timeout:
        :return:
        """
        selecor: str = 'xpath=./a'
        return await self.get_sub_locator(locator=locator, selector=selecor, timeout=timeout)

    async def get_flight_table(self, timeout: float = 5.0) -> Tuple[bool, Union[Locator, str]]:
        try:
            locator = self.__page.locator(self.__table_selector)
            if locator:
                await locator.wait_for(state='visible', timeout=timeout * 1000)
                return True, locator
            else:
                return False, '没有找到国内活动订单页面中的【航班Table】列表'
        except PlaywrightTimeoutError:
            return False, f"元素 '{self.__table_selector}' 未在 {timeout} 秒内找到"
        except Exception as e:
            return False, f"检查元素时发生错误: {str(e)}"

    """
    ------------------------------------------------------------
    1. 解析 TH（表头）
    ------------------------------------------------------------
    """

    @staticmethod
    def parse_tbody_headers(tbody_html: str):
        soup = BeautifulSoup(tbody_html, "html.parser")
        first_row = soup.find("tr")

        if not first_row:
            return []

        headers = [th.get_text(strip=True) for th in first_row.find_all("th")]
        return headers

    """
    ------------------------------------------------------------
    2. 解析 TR/TD（数据行）
    ------------------------------------------------------------
    """

    @staticmethod
    def parse_tbody_rows(tbody_html: str, headers: List[str]) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(tbody_html, "html.parser")
        rows = []

        for tr in soup.find_all("tr"):
            tds = tr.find_all("td")
            if not tds:
                continue

            values = [td.get_text(strip=True) for td in tds]

            if headers and len(headers) == len(values):
                row = dict(zip(headers, values))
            else:
                row = values  # 无 th 或数量不一致，使用 list
            rows.append(row)

        return rows

    """
    ------------------------------------------------------------
    3. 主流程：分页 + 每页解析 tbody
    ------------------------------------------------------------
    """

    async def parse_table_with_pagination(self, refresh_wait_time: float = 10.0) -> List[Dict[str, Any]]:
        """
        refresh_wait_time: 翻页后等待时间
        """

        all_rows = []
        headers = None
        next_button_locator: str = '//a[@id="A_NextPage_1"]'
        while True:
            try:
                # --- 1. 解析 tbody ---
                tbody = self.__page.locator(self.__table_selector)
                tbody_html = await tbody.inner_html()

                # 首次解析表头
                if headers is None:
                    headers = self.parse_tbody_headers(tbody_html=tbody_html)

                # 解析当前页的数据
                rows = self.parse_tbody_rows(tbody_html=tbody_html, headers=headers)
                all_rows.extend(rows)

                # --- 2. 获取当前页数与总页数 ---
                current_page: int = int(await self.__page.locator('//label[@id="Lab_PageIndex"][1]').inner_text())
                pages: int = int(await self.__page.locator('//label[@id="Lab_PageCount"][1]').inner_text())

                # --- 3. 如果到最后一页，退出 ---
                if current_page >= pages:
                    break

                # --- 4. 点击下一页 ---
                await self.__page.locator(selector=next_button_locator).click()

                # 等待页面刷新（简单但稳）
                await self.__page.wait_for_timeout(timeout=refresh_wait_time)
            except PlaywrightTimeoutError:
                all_rows.append(dict(error_message=f"元素 '{self.__table_selector}' 未在 {refresh_wait_time} 秒内找到"))
            except Exception as e:
                all_rows.append(dict(error_message=f"检查元素时发生错误: {str(e)}"))

        return all_rows
