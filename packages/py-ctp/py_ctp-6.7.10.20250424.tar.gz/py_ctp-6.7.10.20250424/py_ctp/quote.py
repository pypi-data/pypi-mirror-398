#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'HaiFeng'
__mtime__ = '2016/9/23'
"""


import threading
import ctypes
from .quote_ctp import Quote
from .structs import *
from .structs_py import *

# CThostFtdcRspUserLoginField, CThostFtdcRspInfoField, CThostFtdcDepthMarketDataField, CThostFtdcSpecificInstrumentField


class CtpQuote(object):
    """"""

    def __init__(self) -> None:
        self.q = Quote()
        self.inst_tick: dict[str, Tick] = {}
        self.logined: bool = False
        self.nRequestID: int = 0

    def ReqConnect(self, pAddress: str) -> None:
        """连接行情前置

        :param pAddress:
        """
        self.q.CreateApi()
        spi = self.q.CreateSpi()
        self.q.RegisterSpi(spi)

        self.q.OnFrontConnected = self._OnFrontConnected
        self.q.OnFrontDisconnected = self._OnFrontDisConnected
        self.q.OnRspUserLogin = self._OnRspUserLogin
        self.q.OnRtnDepthMarketData = self._OnRtnDepthMarketData
        self.q.OnRspSubMarketData = self._OnRspSubMarketData

        self.q.RegisterFront(pAddress)
        self.q.Init()

        print("quote connect ...")

    def ReqUserLogout(self) -> None:
        """退出接口(正常退出,不会触发OnFrontDisconnected)"""
        self.q.Release()
        # 确保隔夜或重新登录时的第1个tick不被发送到客户端
        self.inst_tick.clear()
        self.logined = False
        threading.Thread(target=self.OnDisConnected, args=(self, 0)).start()

    def ReqUserLogin(self, user: str, pwd: str, broker: str) -> None:
        """登录

        :param user:
        :param pwd:
        :param broker:
        """
        f = CThostFtdcReqUserLoginField()
        f.BrokerID = bytes(broker, encoding="ascii")
        f.UserID = bytes(user, encoding="ascii")
        f.Password = bytes(pwd, encoding="ascii")
        f.UserProductInfo = bytes("@hf", encoding="ascii")
        self.nRequestID += 1
        self.q.ReqUserLogin(f, self.nRequestID)

    def ReqSubscribeMarketData(self, pInstrument: list[str]) -> None:
        """订阅合约行情

        :param pInstrument: 行情列表
        """
        inst_p = (ctypes.c_char_p * len(pInstrument))()
        for x in range(len(pInstrument)):
            inst_p[x] = bytes(pInstrument[x], encoding="ascii")
        self.q.SubscribeMarketData(inst_p, len(pInstrument))

    def _OnFrontConnected(self) -> None:
        """"""
        threading.Thread(target=self.OnConnected, args=(self,)).start()

    def _OnFrontDisConnected(self, nReason: int) -> None:
        """"""
        # 确保隔夜或重新登录时的第1个tick不被发送到客户端
        self.inst_tick.clear()
        self.logined = False
        threading.Thread(target=self.OnDisConnected, args=(self, nReason)).start()

    def _OnRspUserLogin(
        self,
        pRspUserLogin: CThostFtdcRspUserLoginField,
        pRspInfo: CThostFtdcRspInfoField,
        nRequestID: int,
        bIsLast: bool,
    ):
        """"""
        info = InfoField()
        info.ErrorID = pRspInfo.getErrorID()
        info.ErrorMsg = pRspInfo.getErrorMsg()
        self.logined = True
        threading.Thread(target=self.OnUserLogin, args=(self, info)).start()

    def _OnRspSubMarketData(
        self,
        pSpecificInstrument: CThostFtdcSpecificInstrumentField,
        pRspInfo: CThostFtdcRspInfoField,
        nRequestID: int,
        bIsLast: bool,
    ):
        pass

    def _OnRtnDepthMarketData(self, pDepthMarketData: CThostFtdcDepthMarketDataField):
        """"""
        # 这个逻辑交由应用端处理更合理 ==> 第一个tick不送给客户端(以处理隔夜早盘时收到夜盘的数据的问题)
        inst = pDepthMarketData.getInstrumentID()
        tick = self.inst_tick.get(inst, Tick())

        # 基本字段映射
        tick.TradingDay = pDepthMarketData.getTradingDay()
        tick.reserve1 = pDepthMarketData.getreserve1()
        tick.ExchangeID = pDepthMarketData.getExchangeID()
        tick.reserve2 = pDepthMarketData.getreserve2()
        tick.LastPrice = pDepthMarketData.getLastPrice()
        tick.PreSettlementPrice = pDepthMarketData.getPreSettlementPrice()
        tick.PreClosePrice = pDepthMarketData.getPreClosePrice()
        tick.PreOpenInterest = pDepthMarketData.getPreOpenInterest()
        tick.OpenPrice = pDepthMarketData.getOpenPrice()
        tick.HighestPrice = pDepthMarketData.getHighestPrice()
        tick.LowestPrice = pDepthMarketData.getLowestPrice()
        tick.Volume = pDepthMarketData.getVolume()
        tick.Turnover = pDepthMarketData.getTurnover()
        tick.OpenInterest = pDepthMarketData.getOpenInterest()
        tick.ClosePrice = pDepthMarketData.getClosePrice()
        tick.SettlementPrice = pDepthMarketData.getSettlementPrice()
        tick.UpperLimitPrice = pDepthMarketData.getUpperLimitPrice()
        tick.LowerLimitPrice = pDepthMarketData.getLowerLimitPrice()
        tick.PreDelta = pDepthMarketData.getPreDelta()
        tick.CurrDelta = pDepthMarketData.getCurrDelta()
        tick.UpdateTime = pDepthMarketData.getUpdateTime()
        tick.UpdateMillisec = pDepthMarketData.getUpdateMillisec()
        tick.ActionDay = pDepthMarketData.getActionDay()
        tick.InstrumentID = pDepthMarketData.getInstrumentID()
        tick.ExchangeInstID = pDepthMarketData.getExchangeInstID()
        tick.BandingUpperPrice = pDepthMarketData.getBandingUpperPrice()
        tick.BandingLowerPrice = pDepthMarketData.getBandingLowerPrice()
        tick.AveragePrice = pDepthMarketData.getAveragePrice()

        # 买卖盘价格和数量映射
        tick.BidPrice1 = pDepthMarketData.getBidPrice1()
        tick.BidVolume1 = pDepthMarketData.getBidVolume1()
        tick.AskPrice1 = pDepthMarketData.getAskPrice1()
        tick.AskVolume1 = pDepthMarketData.getAskVolume1()
        tick.BidPrice2 = pDepthMarketData.getBidPrice2()
        tick.BidVolume2 = pDepthMarketData.getBidVolume2()
        tick.AskPrice2 = pDepthMarketData.getAskPrice2()
        tick.AskVolume2 = pDepthMarketData.getAskVolume2()
        tick.BidPrice3 = pDepthMarketData.getBidPrice3()
        tick.BidVolume3 = pDepthMarketData.getBidVolume3()
        tick.AskPrice3 = pDepthMarketData.getAskPrice3()
        tick.AskVolume3 = pDepthMarketData.getAskVolume3()
        tick.BidPrice4 = pDepthMarketData.getBidPrice4()
        tick.BidVolume4 = pDepthMarketData.getBidVolume4()
        tick.AskPrice4 = pDepthMarketData.getAskPrice4()
        tick.AskVolume4 = pDepthMarketData.getAskVolume4()
        tick.BidPrice5 = pDepthMarketData.getBidPrice5()
        tick.BidVolume5 = pDepthMarketData.getBidVolume5()
        tick.AskPrice5 = pDepthMarketData.getAskPrice5()
        tick.AskVolume5 = pDepthMarketData.getAskVolume5()

        # 用线程会导入多数据入库时报错
        # threading.Thread(target=self.OnTick, args=(self, tick))
        self.OnTick(self, tick)

    def OnDisConnected(self, obj: "CtpQuote", error: int) -> None:
        """"""
        print(f"=== [QUOTE] OnDisConnected===\nerror: {str(error)}")

    def OnConnected(self, obj: "CtpQuote") -> None:
        """"""
        print("=== [QUOTE] OnConnected ===")

    def OnUserLogin(self, obj: "CtpQuote", info: InfoField) -> None:
        """"""
        print(f"=== [QUOTE] OnUserLogin ===\n{info}")

    def OnTick(self, obj: "CtpQuote", f: Tick) -> None:
        """"""
        print(f"=== [QUOTE] OnTick ===\n{f.__dict__}")
