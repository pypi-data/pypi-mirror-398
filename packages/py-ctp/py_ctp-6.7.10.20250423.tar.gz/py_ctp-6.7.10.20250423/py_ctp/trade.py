#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'HaiFeng'
__mtime__ = '2016/9/22'
"""


from copy import deepcopy
import threading
import time
from time import sleep
from .structs_py import *
from .trade_ctp import Trade
from .structs import *
from .datatype import *


class CtpTrade:
    """"""

    def __init__(self):
        self.front_address: str = ""
        self.investor: str = ""
        self.password: str = ""
        self.broker: str = ""
        self.pub_ip: str = ""
        self.port: str = ""
        self.is_login: bool = False
        self.tradingday: str = ""
        self.qry_finish: bool = False

        self.instruments: dict[str, InstrumentField] = {}
        self.orders: dict[str, OrderField] = {}
        self.trades: dict[str, TradeField] = {}
        self.account: TradingAccount = TradingAccount()
        self.accounts: dict[str, TradingAccount] = {}
        self.positions: list[PositionField] = []
        self.position_details: list[PositionDetail] = []
        self.instrument_status: dict[str, TThostFtdcInstrumentStatusType] = {}

        self.session: int = 0
        self._orderid_sysid: dict[str, str] = {}
        self._posi: list[CThostFtdcInvestorPositionField] = []
        self._posi_dtl: list[CThostFtdcInvestorPositionDetailField] = []

        self.trd: Trade = Trade()
        self.nRequestID: int = 0
        print(self.trd.GetVersion())

    def getReqID(self):
        self.nRequestID += 1
        return self.nRequestID

    def strToBytes(self, msg: str):
        return bytes(msg, encoding="ascii")

    def enumToBytes(self, enumVar: Enum):
        return bytes(chr(enumVar.value), encoding="ascii")

    def _OnFrontConnected(self):
        threading.Thread(target=self.OnConnected, args=(self,)).start()

    def _OnFrontDisconnected(self, nReason: int):
        self.is_login = False
        print(nReason)
        # 下午收盘后会不停断开再连接 4097错误
        if nReason == 4097 or nReason == 4098:
            threading.Thread(target=self._reconnect).start()
        else:
            threading.Thread(target=self.OnDisConnected, args=(self, nReason)).start()

    def _reconnect(self):
        if sum([1 if stat == TThostFtdcInstrumentStatusType.THOST_FTDC_IS_Continous else 0 for _, stat in self.instrument_status.items()]) == 0:
            print(time.strftime("%Y%m%d %H:%M:%S", time.localtime()))
            self.trd.Release()
            time.sleep(600)
            self.ReqConnect(self.front_address)

    def _OnRspAuthenticate(
        self,
        pRspAuthenticateField: CThostFtdcRspAuthenticateField,
        pRspInfo: CThostFtdcRspInfoField,
        nRequestID: int,
        bIsLast: bool,
    ):
        if pRspInfo.getErrorID() == 0:
            if pRspAuthenticateField.getAppType() == TThostFtdcAppTypeType.THOST_FTDC_APP_TYPE_InvestorRelay:
                self.trd.RegisterUserSystemInfo(
                    CThostFtdcUserSystemInfoField(self.broker, self.investor, 0, "", self.pub_ip, self.port, time.strftime("%H:%M:%S"))
                )
            elif pRspAuthenticateField.getAppType() == TThostFtdcAppTypeType.THOST_FTDC_APP_TYPE_OperatorRelay:
                self.trd.SubmitUserSystemInfo(
                    CThostFtdcUserSystemInfoField(self.broker, self.investor, 0, "", self.pub_ip, self.port, time.strftime("%H:%M:%S"))
                )
            f = CThostFtdcReqUserLoginField()
            f.BrokerID = self.strToBytes(self.broker)
            f.UserID = self.strToBytes(self.investor)
            f.Password = self.strToBytes(self.password)
            f.UserProductInfo = self.strToBytes("@hf")
            self.trd.ReqUserLogin(f, self.getReqID())
        else:
            info = InfoField()
            info.ErrorID = pRspInfo.getErrorID()
            info.ErrorMsg = f"认证错误:{pRspInfo.getErrorMsg()}"
            threading.Thread(target=self.OnUserLogin, args=(self, info)).start()

    def _OnRspUserLogin(
        self,
        pRspUserLogin: CThostFtdcRspUserLoginField,
        pRspInfo: CThostFtdcRspInfoField,
        nRequestID: int,
        bIsLast: bool,
    ):
        """"""
        if pRspInfo.getErrorID() == 0:
            self.session = pRspUserLogin.getSessionID()
            self.tradingday = pRspUserLogin.getTradingDay()
            f = CThostFtdcSettlementInfoConfirmField()
            f.BrokerID = self.strToBytes(self.broker)
            f.InvestorID = self.strToBytes(self.investor)
            self.trd.ReqSettlementInfoConfirm(f, self.getReqID())
        elif self.is_login:
            threading.Thread(target=self._relogin).start()
        else:
            info = InfoField()
            info.ErrorID = pRspInfo.getErrorID()
            info.ErrorMsg = pRspInfo.getErrorMsg()
            threading.Thread(target=self.OnUserLogin, args=(self, info)).start()

    def _relogin(self):
        # 隔夜重连=>处理'初始化'错误
        time.sleep(60 * 10)
        f = CThostFtdcReqUserLoginField()
        f.BrokerID = self.strToBytes(self.broker)
        f.UserID = self.strToBytes(self.investor)
        f.Password = self.strToBytes(self.password)
        f.UserProductInfo = self.strToBytes("@hf")
        self.trd.ReqUserLogin(f, self.getReqID())

    def _OnRspSettlementInfoConfirm(
        self,
        pSettlementInfoConfirm: CThostFtdcSettlementInfoConfirmField,
        pRspInfo: CThostFtdcRspInfoField,
        nRequestID: int,
        bIsLast: bool,
    ):
        if not self.is_login:
            time.sleep(0.5)
            f = CThostFtdcQryClassifiedInstrumentField()
            f.TradingType = TThostFtdcTradingTypeType.THOST_FTDC_TD_TRADE.value
            f.ClassType = TThostFtdcClassTypeType.THOST_FTDC_INS_ALL.value
            print(time.strftime("%Y%m%d %H:%M:%S", time.localtime()), "qry instrument")
            self.trd.ReqQryClassifiedInstrument(f, self.getReqID())

    def _qry(self):
        """查询帐号相关信息"""
        # restart 模式, 待rtnorder 处理完毕后再进行查询,否则会造成position混乱
        ord_cnt = 0
        trd_cnt = 0
        while True:
            time.sleep(0.5)
            if len(self.orders) == ord_cnt and len(self.trades) == trd_cnt:
                break
            ord_cnt = len(self.orders)
            trd_cnt = len(self.trades)
        time.sleep(1.1)
        self.trd.ReqQryInvestorPosition(CThostFtdcQryInvestorPositionField(), self.getReqID())
        time.sleep(1.1)
        self.trd.ReqQryTradingAccount(CThostFtdcQryTradingAccountField(), self.getReqID())
        time.sleep(1.1)

        self.is_login = True

        info = InfoField()
        info.ErrorID = 0
        info.ErrorMsg = "正确"
        threading.Thread(target=self.OnUserLogin, args=(self, info)).start()
        # 调用Release后程序异常退出,但不报错误:接口断开了仍然调用了查询指令
        # while self.logined:
        # """查询持仓与权益"""
        # self.trd.ReqQryInvestorPosition(CThostFtdcQryInvestorPositionField(), self.getReqID())

    def _OnRtnInstrumentStatus(self, pInstrumentStatus: CThostFtdcInstrumentStatusField):
        if pInstrumentStatus.getInstrumentID() == "":
            return
        self.instrument_status[pInstrumentStatus.getInstrumentID()] = pInstrumentStatus.getInstrumentStatus()
        self.OnInstrumentStatus(self, pInstrumentStatus.getInstrumentID(), pInstrumentStatus.getInstrumentStatus())

    def _OnRspQryInstrument(
        self,
        pInstrument: CThostFtdcInstrumentField,
        pRspInfo: CThostFtdcRspInfoField,
        nRequestID: int,
        bIsLast: bool,
    ):
        """"""
        inst = InstrumentField()
        # 基本属性
        inst.InstrumentID = pInstrument.getInstrumentID()
        inst.InstrumentName = pInstrument.getInstrumentName()
        inst.ExchangeID = pInstrument.getExchangeID()
        inst.ProductID = pInstrument.getProductID()
        inst.ExchangeInstID = pInstrument.getExchangeInstID()
        inst.UnderlyingInstrID = pInstrument.getUnderlyingInstrID()

        # 合约乘数和价格
        inst.VolumeMultiple = pInstrument.getVolumeMultiple()
        inst.PriceTick = pInstrument.getPriceTick()
        inst.UnderlyingMultiple = pInstrument.getUnderlyingMultiple()

        # 订单限制
        inst.MaxMarketOrderVolume = pInstrument.getMaxMarketOrderVolume()
        inst.MinMarketOrderVolume = pInstrument.getMinMarketOrderVolume()
        inst.MaxLimitOrderVolume = pInstrument.getMaxLimitOrderVolume()
        inst.MinLimitOrderVolume = pInstrument.getMinLimitOrderVolume()
        inst.MaxOrderVolume = pInstrument.getMaxLimitOrderVolume()  # 使用限价单最大下单量作为默认值

        # 日期相关
        inst.CreateDate = pInstrument.getCreateDate()
        inst.OpenDate = pInstrument.getOpenDate()
        inst.ExpireDate = pInstrument.getExpireDate()
        inst.StartDelivDate = pInstrument.getStartDelivDate()
        inst.EndDelivDate = pInstrument.getEndDelivDate()

        # 交割信息
        inst.DeliveryYear = pInstrument.getDeliveryYear()
        inst.DeliveryMonth = pInstrument.getDeliveryMonth()

        # 状态和类型
        inst.ProductClass = pInstrument.getProductClass()
        inst.InstLifePhase = pInstrument.getInstLifePhase()
        inst.IsTrading = pInstrument.getIsTrading()
        inst.PositionType = pInstrument.getPositionType()
        inst.PositionDateType = pInstrument.getPositionDateType()
        inst.MaxMarginSideAlgorithm = pInstrument.getMaxMarginSideAlgorithm()

        # 期权相关
        inst.StrikePrice = pInstrument.getStrikePrice()
        inst.OptionsType = pInstrument.getOptionsType()
        inst.CombinationType = pInstrument.getCombinationType()

        # 保证金率
        inst.LongMarginRatio = pInstrument.getLongMarginRatio()
        inst.ShortMarginRatio = pInstrument.getShortMarginRatio()

        self.instruments[inst.InstrumentID] = inst

        if bIsLast:
            sleep(1.1)
            """查询合约/持仓/权益"""
            print(f"{time.strftime('%Y%m%d %H:%M:%S', time.localtime())}: qrt qry thread")
            threading.Thread(target=self._qry).start()  # 开启查询

    def _OnRspQryClassifiedInstrument(
        self,
        pInstrument: CThostFtdcInstrumentField,
        pRspInfo: CThostFtdcRspInfoField,
        nRequestID: int,
        bIsLast: bool,
    ):
        """"""
        self._OnRspQryInstrument(pInstrument, pRspInfo, nRequestID, bIsLast)

    def _OnRspQryPosition(
        self,
        pInvestorPosition: CThostFtdcInvestorPositionField,
        pRspInfo: CThostFtdcRspInfoField,
        nRequestID: int,
        bIsLast: bool,
    ):
        """"""
        if pInvestorPosition.getInstrumentID() != "":  # 偶尔出现NULL的数据导致数据转换错误
            if pInvestorPosition.getInstrumentID() in self.instruments:  # 解决交易所自主合成某些不可交易的套利合约的问题如 SPC y2005&p2001
                self._posi.append(pInvestorPosition)  # Struct(**f.__dict__)) #dict -> object

        if bIsLast:
            self.positions.clear()
            for p in self._posi:
                pf: PositionField = PositionField()
                # 基本属性
                pf.InstrumentID = p.getInstrumentID()
                pf.Direction = p.getPosiDirection()
                pf.BrokerID = p.getBrokerID()
                pf.InvestorID = p.getInvestorID()
                pf.HedgeFlag = p.getHedgeFlag()
                pf.PositionDate = p.getPositionDate()
                pf.ExchangeID = p.getExchangeID()
                pf.TradingDay = p.getTradingDay()
                pf.SettlementID = p.getSettlementID()
                pf.InvestUnitID = p.getInvestUnitID()

                # 持仓数量相关
                pf.Position = p.getPosition()
                pf.YdPosition = p.getYdPosition()
                pf.TdPosition = pf.Position - pf.YdPosition
                pf.TodayPosition = p.getTodayPosition()
                pf.CombPosition = p.getCombPosition()

                # 冻结相关
                pf.LongFrozen = p.getLongFrozen()
                pf.ShortFrozen = p.getShortFrozen()
                pf.LongFrozenAmount = p.getLongFrozenAmount()
                pf.ShortFrozenAmount = p.getShortFrozenAmount()
                pf.CombLongFrozen = p.getCombLongFrozen()
                pf.CombShortFrozen = p.getCombShortFrozen()
                pf.StrikeFrozen = p.getStrikeFrozen()
                pf.StrikeFrozenAmount = p.getStrikeFrozenAmount()
                pf.YdStrikeFrozen = p.getYdStrikeFrozen()
                pf.AbandonFrozen = p.getAbandonFrozen()

                # 开平仓相关
                pf.OpenVolume = p.getOpenVolume()
                pf.CloseVolume = p.getCloseVolume()
                pf.OpenAmount = p.getOpenAmount()
                pf.CloseAmount = p.getCloseAmount()

                # 价格相关
                pf.Price = p.getSettlementPrice()  # 使用结算价作为持仓价格
                pf.PreSettlementPrice = p.getPreSettlementPrice()
                pf.SettlementPrice = p.getSettlementPrice()

                # 盈亏相关
                pf.CloseProfit = p.getCloseProfit()
                pf.PositionProfit = p.getPositionProfit()
                pf.CloseProfitByDate = p.getCloseProfitByDate()
                pf.CloseProfitByTrade = p.getCloseProfitByTrade()

                # 保证金和成本
                pf.Commission = p.getCommission()
                pf.Margin = p.getUseMargin()
                pf.PreMargin = p.getPreMargin()
                pf.UseMargin = p.getUseMargin()
                pf.FrozenMargin = p.getFrozenMargin()
                pf.FrozenCash = p.getFrozenCash()
                pf.FrozenCommission = p.getFrozenCommission()
                pf.CashIn = p.getCashIn()
                pf.PositionCost = p.getPositionCost()
                pf.OpenCost = p.getOpenCost()
                pf.PositionCostOffset = p.getPositionCostOffset()
                pf.ExchangeMargin = p.getExchangeMargin()

                # 保证金率
                pf.MarginRateByMoney = p.getMarginRateByMoney()
                pf.MarginRateByVolume = p.getMarginRateByVolume()

                # TAS相关
                pf.TasPosition = p.getTasPosition()
                pf.TasPositionCost = p.getTasPositionCost()

                # 期权相关
                pf.OptionValue = p.getOptionValue()

                self.positions.append(pf)
            self._posi.clear()
            self.qry_finish = True

    def _OnRspQryPositionDetail(
        self,
        pInvestorPositionDetail: CThostFtdcInvestorPositionDetailField,
        pRspInfo: CThostFtdcRspInfoField,
        nRequestID: int,
        bIsLast: bool,
    ):
        """持仓明细"""
        if pInvestorPositionDetail.getInstrumentID() != "":
            self._posi_dtl.append(pInvestorPositionDetail)

        if bIsLast:
            for p in self._posi_dtl:
                detail = PositionDetail()
                # 基本信息
                detail.reserve1 = p.getreserve1()
                detail.InstrumentID = p.getInstrumentID()
                detail.BrokerID = p.getBrokerID()
                detail.InvestorID = p.getInvestorID()
                detail.ExchangeID = p.getExchangeID()
                detail.TradingDay = p.getTradingDay()
                detail.SettlementID = p.getSettlementID()
                detail.InvestUnitID = p.getInvestUnitID()
                detail.TradeID = p.getTradeID()
                detail.CombInstrumentID = p.getCombInstrumentID()

                # 持仓相关
                detail.Direction = p.getDirection()
                detail.HedgeFlag = p.getHedgeFlag()
                detail.TradeType = p.getTradeType()
                detail.SpecPosiType = p.getSpecPosiType()
                detail.Volume = p.getVolume()
                detail.OpenPrice = p.getOpenPrice()
                detail.OpenDate = p.getOpenDate()
                detail.reserve2 = p.getreserve2()
                detail.CloseVolume = p.getCloseVolume()
                detail.CloseAmount = p.getCloseAmount()
                detail.TimeFirstVolume = p.getTimeFirstVolume()

                # 盈亏相关
                detail.CloseProfitByDate = p.getCloseProfitByDate()
                detail.CloseProfitByTrade = p.getCloseProfitByTrade()
                detail.PositionProfitByDate = p.getPositionProfitByDate()
                detail.PositionProfitByTrade = p.getPositionProfitByTrade()
                detail.PositionProfit = p.getPositionProfitByDate()
                detail.CloseProfit = p.getCloseProfitByDate()

                # 保证金相关
                detail.Margin = p.getMargin()
                detail.ExchMargin = p.getExchMargin()
                detail.MarginRateByMoney = p.getMarginRateByMoney()
                detail.MarginRateByVolume = p.getMarginRateByVolume()

                # 价格相关
                detail.LastSettlementPrice = p.getLastSettlementPrice()
                detail.SettlementPrice = p.getSettlementPrice()

                self.position_details.append(detail)
            self._posi_dtl.clear()
            self.qry_finish = True

    def _OnRspQryAccount(
        self,
        pTradingAccount: CThostFtdcTradingAccountField,
        pRspInfo: CThostFtdcRspInfoField,
        nRequestID: int,
        bIsLast: bool,
    ):
        """"""
        if pTradingAccount.getAccountID():
            if not self.account:
                self.account = TradingAccount()

            # 基本信息
            self.account.BrokerID = pTradingAccount.getBrokerID()
            self.account.AccountID = pTradingAccount.getAccountID()
            self.account.TradingDay = pTradingAccount.getTradingDay()
            self.account.SettlementID = pTradingAccount.getSettlementID()
            self.account.CurrencyID = pTradingAccount.getCurrencyID()
            self.account.BizType = pTradingAccount.getBizType()

            # 资金相关 - 昨日数据
            self.account.PreMortgage = pTradingAccount.getPreMortgage()
            self.account.PreCredit = pTradingAccount.getPreCredit()
            self.account.PreDeposit = pTradingAccount.getPreDeposit()
            self.account.PreMargin = pTradingAccount.getPreMargin()
            self.account.PreFundMortgageIn = pTradingAccount.getPreFundMortgageIn()
            self.account.PreFundMortgageOut = pTradingAccount.getPreFundMortgageOut()

            # 利息相关
            self.account.InterestBase = pTradingAccount.getInterestBase()
            self.account.Interest = pTradingAccount.getInterest()

            # 资金变动
            self.account.Deposit = pTradingAccount.getDeposit()
            self.account.Withdraw = pTradingAccount.getWithdraw()
            self.account.CashIn = pTradingAccount.getCashIn()

            # 冻结资金
            self.account.FrozenMargin = pTradingAccount.getFrozenMargin()
            self.account.FrozenCash = pTradingAccount.getFrozenCash()
            self.account.FrozenCommission = pTradingAccount.getFrozenCommission()

            # 核心资金数据
            self.account.CurrMargin = pTradingAccount.getCurrMargin()
            self.account.Commission = pTradingAccount.getCommission()
            self.account.CloseProfit = pTradingAccount.getCloseProfit()
            self.account.PositionProfit = pTradingAccount.getPositionProfit()
            self.account.Balance = pTradingAccount.getBalance()
            self.account.Available = pTradingAccount.getAvailable()
            self.account.WithdrawQuota = pTradingAccount.getWithdrawQuota()
            self.account.Reserve = pTradingAccount.getReserve()

            # 质押相关
            self.account.Credit = pTradingAccount.getCredit()
            self.account.Mortgage = pTradingAccount.getMortgage()
            self.account.FundMortgageIn = pTradingAccount.getFundMortgageIn()
            self.account.FundMortgageOut = pTradingAccount.getFundMortgageOut()
            self.account.FundMortgageAvailable = pTradingAccount.getFundMortgageAvailable()
            self.account.MortgageableFund = pTradingAccount.getMortgageableFund()

            # 保证金相关
            self.account.ExchangeMargin = pTradingAccount.getExchangeMargin()
            self.account.DeliveryMargin = pTradingAccount.getDeliveryMargin()
            self.account.ExchangeDeliveryMargin = pTradingAccount.getExchangeDeliveryMargin()

            # 特殊产品相关
            self.account.SpecProductMargin = pTradingAccount.getSpecProductMargin()
            self.account.SpecProductFrozenMargin = pTradingAccount.getSpecProductFrozenMargin()
            self.account.SpecProductCommission = pTradingAccount.getSpecProductCommission()
            self.account.SpecProductFrozenCommission = pTradingAccount.getSpecProductFrozenCommission()
            self.account.SpecProductPositionProfit = pTradingAccount.getSpecProductPositionProfit()
            self.account.SpecProductCloseProfit = pTradingAccount.getSpecProductCloseProfit()
            self.account.SpecProductPositionProfitByAlg = pTradingAccount.getSpecProductPositionProfitByAlg()
            self.account.SpecProductExchangeMargin = pTradingAccount.getSpecProductExchangeMargin()

            # 互换和期权相关
            self.account.FrozenSwap = pTradingAccount.getFrozenSwap()
            self.account.OptionValue = pTradingAccount.getOptionValue()

            # 余额相关
            self.account.ReserveBalance = pTradingAccount.getReserveBalance()

            # 计算字段
            self.account.PreBalance = pTradingAccount.getPreBalance() + pTradingAccount.getDeposit() - pTradingAccount.getWithdraw()
            self.account.Fund = self.account.PreBalance + self.account.CloseProfit + self.account.PositionProfit - self.account.Commission
            self.account.Risk = 0 if self.account.Fund == 0 else self.account.CurrMargin / self.account.Fund

            self.accounts[self.account.AccountID] = deepcopy(self.account)  # 支持多账号
        if bIsLast:
            """查询持仓与权益"""
            self.qry_finish = True

    def _OnRtnOrder(self, pOrder: CThostFtdcOrderField):
        """"""
        id = "{0}|{1}|{2}".format(pOrder.getSessionID(), pOrder.getFrontID(), pOrder.getOrderRef())
        of = self.orders.get(id)
        if not of:
            of = OrderField()
            if pOrder.getOrderRef().isdigit():
                of.Custom = int(pOrder.getOrderRef()) % 1000000
            of.InstrumentID = pOrder.getInstrumentID()
            of.ExchangeID = pOrder.getExchangeID()
            of.Direction = pOrder.getDirection()
            of.Offset = pOrder.getCombOffsetFlag()
            of.LimitPrice = pOrder.getLimitPrice()
            of.Volume = pOrder.getVolumeTotalOriginal()
            of.VolumeTotalOriginal = pOrder.getVolumeTotalOriginal()
            of.VolumeLeft = of.Volume
            of.VolumeTraded = pOrder.getVolumeTraded()
            of.VolumeTotal = pOrder.getVolumeTotal()
            of.AvgPrice = 0.0  # 初始化，后续会在成交回调中更新

            # 时间相关属性
            of.InsertTime = pOrder.getInsertTime()
            of.InsertDate = pOrder.getInsertDate()
            of.ActiveTime = pOrder.getActiveTime()
            of.SuspendTime = pOrder.getSuspendTime()
            of.UpdateTime = pOrder.getUpdateTime()
            of.CancelTime = pOrder.getCancelTime()
            of.TradeTime = ""  # 将在成交回调中设置
            of.TradingDay = pOrder.getTradingDay()

            # 状态相关属性
            of.Status = pOrder.getOrderStatus()
            of.StatusMsg = pOrder.getStatusMsg()
            of.OrderSubmitStatus = pOrder.getOrderSubmitStatus()
            of.IsLocal = pOrder.getSessionID() == self.session

            # 标识相关属性
            if pOrder.getOrderRef().isdigit():
                of.Custom = int(pOrder.getOrderRef()) % 1000000
            of.OrderRef = pOrder.getOrderRef()
            of.SysID = pOrder.getOrderSysID() if pOrder.getOrderSysID() else ""
            of.OrderLocalID = pOrder.getOrderLocalID()

            # 报单详细属性
            of.OrderPriceType = pOrder.getOrderPriceType()
            of.CombOffsetFlag = pOrder.getCombOffsetFlag()
            of.CombHedgeFlag = pOrder.getCombHedgeFlag()
            of.TimeCondition = pOrder.getTimeCondition()
            of.GTDDate = pOrder.getGTDDate()
            of.VolumeCondition = pOrder.getVolumeCondition()
            of.MinVolume = pOrder.getMinVolume()
            of.ContingentCondition = pOrder.getContingentCondition()
            of.StopPrice = pOrder.getStopPrice()
            of.ForceCloseReason = pOrder.getForceCloseReason()
            of.IsAutoSuspend = pOrder.getIsAutoSuspend()
            of.OrderSource = pOrder.getOrderSource()
            of.OrderType = pOrder.getOrderType()

            # 用户和机构信息
            of.BrokerID = pOrder.getBrokerID()
            of.InvestorID = pOrder.getInvestorID()
            of.UserID = pOrder.getUserID()
            of.ParticipantID = pOrder.getParticipantID()
            of.ClientID = pOrder.getClientID()
            of.TraderID = pOrder.getTraderID()

            # 业务和系统信息
            of.BusinessUnit = pOrder.getBusinessUnit()
            of.RequestID = pOrder.getRequestID()
            of.NotifySequence = pOrder.getNotifySequence()
            of.SettlementID = pOrder.getSettlementID()
            of.SequenceNo = pOrder.getSequenceNo()
            of.FrontID = pOrder.getFrontID()
            of.SessionID = pOrder.getSessionID()
            of.InstallID = pOrder.getInstallID()
            of.BrokerOrderSeq = pOrder.getBrokerOrderSeq()
            of.BranchID = pOrder.getBranchID()
            of.InvestUnitID = pOrder.getInvestUnitID()
            of.AccountID = pOrder.getAccountID()
            of.CurrencyID = pOrder.getCurrencyID()
            of.ExchangeInstID = pOrder.getExchangeInstID()
            of.IPAddress = pOrder.getIPAddress()
            of.MacAddress = pOrder.getMacAddress()
            of.OrderMemo = pOrder.getOrderMemo()
            of.SessionReqSeq = pOrder.getSessionReqSeq()

            # 高级属性
            of.ClearingPartID = pOrder.getClearingPartID()
            of.RelativeOrderSysID = pOrder.getRelativeOrderSysID()
            of.ZCETotalTradedVolume = pOrder.getZCETotalTradedVolume()
            of.IsSwapOrder = pOrder.getIsSwapOrder()
            of.UserForceClose = pOrder.getUserForceClose()
            of.UserProductInfo = pOrder.getUserProductInfo()

            self.orders[id] = of
            threading.Thread(target=self.OnOrder, args=(self, of)).start()
        elif pOrder.getOrderStatus() == TThostFtdcOrderStatusType.THOST_FTDC_OST_Canceled:
            # 更新状态和消息
            of.Status = pOrder.getOrderStatus()
            of.StatusMsg = pOrder.getStatusMsg()
            of.UpdateTime = pOrder.getUpdateTime()
            of.CancelTime = pOrder.getCancelTime()

            if of.StatusMsg.find("被拒绝") >= 0:
                info = InfoField()
                info.ErrorID = -1
                info.ErrorMsg = of.StatusMsg
                threading.Thread(target=self.OnErrOrder, args=(self, of, info)).start()
            else:
                threading.Thread(target=self.OnCancel, args=(self, of)).start()
        else:
            # 更新报单状态和相关信息
            of.Status = pOrder.getOrderStatus()
            of.StatusMsg = pOrder.getStatusMsg()
            of.VolumeTraded = pOrder.getVolumeTraded()
            of.VolumeTotal = pOrder.getVolumeTotal()
            of.VolumeLeft = of.VolumeTotal - of.VolumeTraded
            of.AvgPrice = pOrder.getLimitPrice()  # 简单处理，实际应从成交数据计算
            of.UpdateTime = pOrder.getUpdateTime()

            if pOrder.getOrderSysID():
                of.SysID = pOrder.getOrderSysID()
                self._orderid_sysid[pOrder.getOrderSysID()] = id  # 记录sysid与orderid关联,方便Trade时查找处理

    def _OnRtnTrade(self, pTrade: CThostFtdcTradeField):
        """"""
        tf = TradeField()
        # 基本属性
        tf.InvestorID = pTrade.getInvestorID()
        tf.Hedge = pTrade.getHedgeFlag()
        tf.Direction = pTrade.getDirection()
        tf.ExchangeID = pTrade.getExchangeID()
        tf.InstrumentID = pTrade.getInstrumentID()
        tf.Offset = pTrade.getOffsetFlag()
        tf.Price = pTrade.getPrice()
        tf.SysID = pTrade.getOrderSysID()
        tf.TradeID = pTrade.getTradeID()
        tf.TradeTime = pTrade.getTradeTime()
        tf.TradingDay = pTrade.getTradingDay()
        tf.Volume = pTrade.getVolume()
        # 添加所有其他属性
        tf.BrokerID = pTrade.getBrokerID()
        tf.OrderRef = pTrade.getOrderRef()
        tf.UserID = pTrade.getUserID()
        tf.ParticipantID = pTrade.getParticipantID()
        tf.ClientID = pTrade.getClientID()
        tf.TradingRole = pTrade.getTradingRole()
        tf.TradeType = pTrade.getTradeType()
        tf.PriceSource = pTrade.getPriceSource()
        tf.TraderID = pTrade.getTraderID()
        tf.OrderLocalID = pTrade.getOrderLocalID()
        tf.ClearingPartID = pTrade.getClearingPartID()
        tf.BusinessUnit = pTrade.getBusinessUnit()
        tf.SequenceNo = pTrade.getSequenceNo()
        tf.SettlementID = pTrade.getSettlementID()
        tf.BrokerOrderSeq = pTrade.getBrokerOrderSeq()
        tf.TradeSource = pTrade.getTradeSource()
        tf.InvestUnitID = pTrade.getInvestUnitID()
        tf.ExchangeInstID = pTrade.getExchangeInstID()
        tf.TradeDate = pTrade.getTradeDate()

        self.trades[f"{tf.TradeID}_{str(tf.Direction).split('_')[-1]}"] = tf

        id = self._orderid_sysid[tf.SysID]
        of = self.orders[id]
        tf.OrderID = id  # tradeid 与 orderid 关联
        of.TradeTime = tf.TradeTime
        of.AvgPrice = (of.AvgPrice * (of.Volume - of.VolumeLeft) + tf.Price * tf.Volume) / (of.Volume - of.VolumeLeft + tf.Volume)
        of.TradeVolume = tf.Volume
        of.VolumeLeft -= tf.Volume
        if of.VolumeLeft == 0:
            of.Status = TThostFtdcOrderStatusType.THOST_FTDC_OST_AllTraded
            of.StatusMsg = "全部成交"
        else:
            of.Status = TThostFtdcOrderStatusType.THOST_FTDC_OST_PartTradedQueueing
            of.StatusMsg = "部分成交"
        threading.Thread(target=self._onRtn, args=(of, tf)).start()

    def _onRtn(self, of: OrderField, tf: TradeField):
        self.OnOrder(self, of)
        self.OnTrade(self, tf)

    def _OnRspOrder(
        self,
        pInputOrder: CThostFtdcInputOrderField,
        pRspInfo: CThostFtdcRspInfoField,
        nRequestID: int,
        bIsLast: bool,
    ):
        """"""
        info = InfoField()
        info.ErrorID = pRspInfo.getErrorID()
        info.ErrorMsg = pRspInfo.getErrorMsg()

        id = "{0}|{1}|{2}".format(self.session, "0", pInputOrder.getOrderRef())
        of = self.orders.get(id)
        if not of:
            of = OrderField()
            l = int(pInputOrder.getOrderRef())
            of.Custom = l % 1000000
            of.InstrumentID = pInputOrder.getInstrumentID()
            of.InsertTime = time.strftime("%H:%M:%S", time.localtime())
            # 对direction需特别处理（具体见ctp_struct）
            of.Direction = pInputOrder.getDirection()
            of.Offset = pInputOrder.getCombOffsetFlag()
            # of.Status = OrderStatus.Normal
            # of.StatusMsg = f.getStatusMsg()
            of.IsLocal = True
            of.LimitPrice = pInputOrder.getLimitPrice()
            of.OrderID = id
            of.Volume = pInputOrder.getVolumeTotalOriginal()
            of.VolumeLeft = of.Volume
            self.orders[id] = of

        of.Status = of.Status
        of.StatusMsg = "{0}:{1}".format(info.ErrorID, info.ErrorMsg)
        threading.Thread(target=self.OnErrOrder, args=(self, of, info)).start()

    def _OnErrOrder(self, pInputOrder: CThostFtdcInputOrderField, pRspInfo: CThostFtdcRspInfoField):
        """"""
        id = "{0}|{1}|{2}".format(self.session, "0", pInputOrder.getOrderRef())
        of = self.orders.get(id)

        info = InfoField()
        info.ErrorID = pRspInfo.getErrorID()
        info.ErrorMsg = pRspInfo.getErrorMsg()

        if of and of.IsLocal:
            of.Status = TThostFtdcOrderStatusType.THOST_FTDC_OST_Canceled
            of.StatusMsg = "{0}:{1}".format(pRspInfo.getErrorID(), pRspInfo.getErrorMsg())
            threading.Thread(target=self.OnErrOrder, args=(self, of, info)).start()

    def _OnRspOrderAction(
        self,
        pInputOrderAction: CThostFtdcInputOrderActionField,
        pRspInfo: CThostFtdcRspInfoField,
        nRequestID: int,
        bIsLast: bool,
    ):
        id = "{0}|{1}|{2}".format(
            pInputOrderAction.getSessionID(),
            pInputOrderAction.getFrontID(),
            pInputOrderAction.getOrderRef(),
        )
        if self.is_login and id in self.orders:
            info = InfoField()
            info.ErrorID = pRspInfo.ErrorID
            info.ErrorMsg = pRspInfo.ErrorMsg
            threading.Thread(target=self.OnErrCancel, args=(self, self.orders[id], info)).start()

    def _OnRtnNotice(self, pTradingNoticeInfo: CThostFtdcTradingNoticeInfoField):
        """交易提醒"""
        msg = pTradingNoticeInfo.getFieldContent()
        if len(msg) > 0:
            threading.Thread(
                target=self.OnRtnNotice,
                args=(self, pTradingNoticeInfo.getSendTime(), msg),
            ).start()

    def _OnRtnQuote(self, pQuote: CThostFtdcQuoteField):
        threading.Thread(target=self.OnRtnQuote, args=(self, pQuote)).start()

    def _OnErrRtnQuote(self, pInputQuote: CThostFtdcInputQuoteField, pRspInfo: CThostFtdcRspInfoField):
        info = InfoField()
        info.ErrorID = pRspInfo.getErrorID()
        info.ErrorMsg = pRspInfo.getErrorMsg()
        threading.Thread(target=self.OnErrRtnQuote, args=(self, pInputQuote, info)).start()

    def _OnErrForQuoteInsert(
        self,
        pInputForQuote: CThostFtdcInputForQuoteField,
        pRspInfo: CThostFtdcRspInfoField,
    ):
        info = InfoField()
        info.ErrorID = pRspInfo.getErrorID()
        info.ErrorMsg = pRspInfo.getErrorMsg()
        threading.Thread(target=self.OnErrRtnForQuoteInsert, args=(self, pInputForQuote, info)).start()

    def _OnRspError(self, pRspInfo: CThostFtdcRspInfoField, nRequestID: int, bIsLast: bool):
        info = InfoField()
        info.ErrorID = pRspInfo.getErrorID()
        info.ErrorMsg = pRspInfo.getErrorMsg()
        threading.Thread(target=self.OnRspError, args=(self, info)).start()

    def GetVersion(self):
        return self.trd.GetVersion()

    def ReqConnect(self, front: str):
        """连接交易前置

        :param front:
        """
        self.trd.CreateApi()
        spi = self.trd.CreateSpi()
        self.trd.RegisterSpi(spi)

        self.trd.OnFrontConnected = self._OnFrontConnected
        self.trd.OnRspUserLogin = self._OnRspUserLogin
        self.trd.OnRspAuthenticate = self._OnRspAuthenticate
        self.trd.OnFrontDisconnected = self._OnFrontDisconnected
        # self.t.OnRspUserLogout = self._OnRspUserLogout
        self.trd.OnRspSettlementInfoConfirm = self._OnRspSettlementInfoConfirm
        self.trd.OnRtnOrder = self._OnRtnOrder
        self.trd.OnRtnTrade = self._OnRtnTrade
        self.trd.OnRspOrderInsert = self._OnRspOrder
        self.trd.OnErrRtnOrderInsert = self._OnErrOrder
        self.trd.OnErrRtnOrderAction = lambda pOrderAction, pRspInfo: None
        self.trd.OnRspOrderAction = self._OnRspOrderAction
        self.trd.OnRtnInstrumentStatus = self._OnRtnInstrumentStatus
        self.trd.OnRspQryInstrument = self._OnRspQryInstrument
        self.trd.OnRspQryClassifiedInstrument = self._OnRspQryClassifiedInstrument
        self.trd.OnRspQryTradingAccount = self._OnRspQryAccount
        self.trd.OnRspQryInvestorPosition = self._OnRspQryPosition
        self.trd.OnRspQryInvestorPositionDetail = self._OnRspQryPositionDetail
        self.trd.OnRtnTradingNotice = self._OnRtnNotice
        self.trd.OnRtnQuote = self._OnRtnQuote
        self.trd.OnErrRtnQuoteInsert = self._OnErrRtnQuote
        self.trd.OnErrRtnForQuoteInsert = self._OnErrForQuoteInsert
        self.trd.OnRspError = self._OnRspError

        self.front_address = front

        print(f"trade connect {front}...")
        self.trd.RegisterFront(front)
        self.trd.SubscribePrivateTopic(THOST_TE_RESUME_TYPE.TERT_RESTART)  # restart 同步处理order trade
        self.trd.SubscribePublicTopic(THOST_TE_RESUME_TYPE.TERT_RESTART)
        self.trd.Init()
        # self.t.Join()

    def ReqUserLogin(self, user: str, pwd: str, broker: str, appid: str, auth_code: str):
        """登录

        :param user:
        :param pwd:
        :param broker:
        """
        self.broker = broker
        self.investor = user
        self.password = pwd
        f = CThostFtdcReqAuthenticateField()
        f.UserID = self.strToBytes(user)
        f.AppID = self.strToBytes(appid)
        f.BrokerID = self.strToBytes(broker)
        f.AuthCode = self.strToBytes(auth_code)
        print(f.getBrokerID(), f.getAppID(), f.getAuthCode())
        self.trd.ReqAuthenticate(f, self.getReqID())

    def ReqOrderInsert(
        self,
        pInstrument: str,
        pDirection: TThostFtdcDirectionType,
        pOffset: TThostFtdcOffsetFlagType,
        pPrice: float = 0.0,
        pVolume: int = 1,
        pType: OrderType = OrderType.Limit,
        pCustom: int = 0,
    ):
        """委托

        Args:
            pInstrument (str): 合约代码
            pDirection (TThostFtdcDirectionEnType): 买卖方向
            pOffset (TThostFtdcOffsetFlagType): 开平标志
            pPrice (float, optional): 价格. Defaults to 0.0.
            pVolume (int, optional): 数量. Defaults to 1.
            pType (OrderType, optional): 委托类型. Defaults to OrderType.Limit.
            pCustom (int, optional): 自定义编号. Defaults to 0.
        """
        OrderPriceType = TThostFtdcOrderPriceTypeType.THOST_FTDC_OPT_AnyPrice
        TimeCondition = TThostFtdcTimeConditionType.THOST_FTDC_TC_IOC
        LimitPrice: float = 0.0
        VolumeCondition = TThostFtdcVolumeConditionType.THOST_FTDC_VC_AV

        if pType == OrderType.Market:  # 市价
            OrderPriceType = TThostFtdcOrderPriceTypeType.THOST_FTDC_OPT_AnyPrice
            TimeCondition = TThostFtdcTimeConditionType.THOST_FTDC_TC_IOC
            LimitPrice = 0.0
            VolumeCondition = TThostFtdcVolumeConditionType.THOST_FTDC_VC_AV
        elif pType == OrderType.Limit:  # 限价
            OrderPriceType = TThostFtdcOrderPriceTypeType.THOST_FTDC_OPT_LimitPrice
            TimeCondition = TThostFtdcTimeConditionType.THOST_FTDC_TC_GFD
            LimitPrice = pPrice
            VolumeCondition = TThostFtdcVolumeConditionType.THOST_FTDC_VC_AV
        elif pType == OrderType.FAK:  # FAK
            OrderPriceType = TThostFtdcOrderPriceTypeType.THOST_FTDC_OPT_LimitPrice
            TimeCondition = TThostFtdcTimeConditionType.THOST_FTDC_TC_IOC
            LimitPrice = pPrice
            VolumeCondition = TThostFtdcVolumeConditionType.THOST_FTDC_VC_AV
        elif pType == OrderType.FOK:  # FOK
            OrderPriceType = TThostFtdcOrderPriceTypeType.THOST_FTDC_OPT_LimitPrice
            TimeCondition = TThostFtdcTimeConditionType.THOST_FTDC_TC_IOC
            LimitPrice = pPrice
            VolumeCondition = TThostFtdcVolumeConditionType.THOST_FTDC_VC_CV  # 全部数量

        f = CThostFtdcInputOrderField()
        f.BrokerID = self.strToBytes(self.broker)
        f.InvestorID = self.strToBytes(self.investor)
        f.InstrumentID = self.strToBytes(pInstrument)
        f.OrderRef = self.strToBytes("%06d%06d" % (self.getReqID(), pCustom % 1000000))
        f.UserID = self.strToBytes(self.investor)
        f.ExchangeID = self.strToBytes(self.instruments[pInstrument].ExchangeID)
        # 此处ctp_enum与at_struct名称冲突
        f.Direction = self.enumToBytes(pDirection)
        f.CombOffsetFlag = self.enumToBytes(pOffset)
        f.CombHedgeFlag = self.enumToBytes(TThostFtdcHedgeFlagType.THOST_FTDC_HF_Speculation)
        f.IsAutoSuspend = 0
        f.ForceCloseReason = TThostFtdcForceCloseReasonType.THOST_FTDC_FCC_NotForceClose.value
        f.IsSwapOrder = 0
        f.ContingentCondition = TThostFtdcContingentConditionType.THOST_FTDC_CC_Immediately.value
        f.VolumeCondition = VolumeCondition.value
        f.MinVolume = 1
        f.VolumeTotalOriginal = pVolume
        f.OrderPriceType = OrderPriceType.value
        f.TimeCondition = TimeCondition.value
        f.LimitPrice = LimitPrice
        self.trd.ReqOrderInsert(f, self.getReqID())

    def ReqOrderAction(self, OrderID: str):
        """撤单

        :param OrderID:
        """
        of = self.orders[OrderID]

        if not of:
            return -1
        else:
            pOrderId = of.OrderID
            f = CThostFtdcInputOrderActionField()
            f.BrokerID = self.strToBytes(self.broker)
            f.InvestorID = self.strToBytes(self.investor)
            f.OrderRef = self.strToBytes(pOrderId.split("|")[2])
            f.FrontID = int(pOrderId.split("|")[1])
            f.SessionID = int(pOrderId.split("|")[0])
            f.InstrumentID = self.strToBytes(of.InstrumentID)
            f.ExchangeID = self.strToBytes(of.ExchangeID)
            f.ActionFlag = TThostFtdcActionFlagType.THOST_FTDC_AF_Delete.value

            return self.trd.ReqOrderAction(f, self.getReqID())

    def ReqQryPosition(self) -> list[PositionField]:
        """查持仓"""
        self.qry_finish = False
        start_time = time.time()
        self.trd.ReqQryInvestorPosition(CThostFtdcQryInvestorPositionField(), self.getReqID())
        while not self.qry_finish and time.time() - start_time < 6:
            time.sleep(1)
        return self.positions

    def ReqQryPositionDetail(self) -> list[PositionDetail]:
        """查持仓明细"""
        self.qry_finish = False
        start_time = time.time()
        self.trd.ReqQryInvestorPositionDetail(CThostFtdcQryInvestorPositionDetailField(), self.getReqID())
        while not self.qry_finish and time.time() - start_time < 6:
            time.sleep(1)
        return self.position_details

    def ReqQryAccount(self) -> TradingAccount | dict[str, TradingAccount]:
        """查权益"""
        self.qry_finish = False
        start_time = time.time()
        self.trd.ReqQryTradingAccount(CThostFtdcQryTradingAccountField(), self.getReqID())
        while not self.qry_finish and time.time() - start_time < 6:
            time.sleep(1)
        return self.accounts if len(self.accounts) > 1 else self.account

    def ReqUserLogout(self):
        """退出接口"""
        self.is_login = False
        time.sleep(3)
        f = CThostFtdcUserLogoutField()
        f.BrokerID = self.strToBytes(self.broker)
        f.InvestorID = self.strToBytes(self.investor)
        self.trd.ReqUserLogout(f, self.getReqID())
        self.trd.RegisterSpi(None)  # 传入空的 c_void_p 实例以解除 SPI 注册
        self.trd.Release()
        threading.Thread(target=self.OnDisConnected, args=(self, 0)).start()

    def OnConnected(self, obj: "CtpTrade"):
        """接口连接

        :param obj:
        """
        print("=== [TRADE] OnConnected ===".format(""))

    def OnDisConnected(self, obj: "CtpTrade", reason: int):
        """接口断开

        :param obj:
        :param reason:
        """
        print("=== [TRADE] OnDisConnected === \nreason: {0}".format(reason))

    def OnUserLogin(self, obj: "CtpTrade", info: InfoField):
        """登录响应

        :param obj:
        :param info:
        """
        print("=== [TRADE] OnUserLogin === \n{0}".format(info))

    def OnOrder(self, obj: "CtpTrade", f: OrderField):
        """委托响应

        :param obj:
        :param f:
        """
        print("=== [TRADE] OnOrder === \n{0}".format(f.__dict__))

    def OnTrade(self, obj: "CtpTrade", f: TradeField):
        """成交响应

        :param obj:
        :param f:
        """
        print("=== [TRADE] OnTrade === \n{0}".format(f.__dict__))

    def OnCancel(self, obj: "CtpTrade", f: OrderField):
        """
        撤单响应
            :param self:
            :param obj:
            :param f:OrderField:
        """
        print("=== [TRADE] OnCancel === \n{0}".format(f.__dict__))

    def OnErrCancel(self, obj: "CtpTrade", f: OrderField, info: InfoField):
        """
        撤单失败
            :param self:
            :param obj:
            :param f:OrderField:
            :param info:InfoField:
        """
        print("=== [TRADE] OnErrCancel ===\n{0}".format(f.__dict__))
        print(info)

    def OnRspError(self, obj: "CtpTrade", info: InfoField):
        """
        撤单失败
            :param self:
            :param obj:
            :param f:OrderField:
            :param info:InfoField:
        """
        print("=== [TRADE] OnRspError ===\n{0}".format(info.__dict__))

    def OnErrOrder(self, obj: "CtpTrade", f: OrderField, info: InfoField):
        """
        委托错误
            :param self:
            :param obj:
            :param f:OrderField:
            :param info:InfoField:
        """
        print("=== [TRADE] OnErrOrder ===\n{0}".format(f.__dict__))
        print(info)

    def OnInstrumentStatus(self, obj: "CtpTrade", inst: str, status: TThostFtdcInstrumentStatusType):
        """
        交易状态
            :param self:
            :param obj:
            :param inst:str:
            :param status:TThostFtdcInstrumentStatusType:
        """
        print("{}:{}".format(inst, str(status).split("_")[-1]))

    def OnRtnNotice(self, obj: "CtpTrade", time: str, msg: str):
        """交易提醒

        :param obj:
        :param time:
        :param msg:
        :return:
        """
        print(f"=== OnRtnNotice===\n {time}:{msg}")

    def OnRtnQuote(self, obj: "CtpTrade", quote: CThostFtdcQuoteField):
        """报价通知

        :param obj:
        :param quote:
        :return:
        """
        print("=== [TRADE] OnRtnQuote ===\n{0}".format(quote.__dict__))

    def OnErrRtnQuote(self, obj: "CtpTrade", quote: CThostFtdcInputQuoteField, info: InfoField):
        """

        :param obj:
        :param quote:
        :return:
        """
        print("=== [TRADE] OnErrRtnQuote ===\n{0}".format(quote.__dict__))
        print(info)

    def OnErrRtnForQuoteInsert(self, obj: "CtpTrade", quote: CThostFtdcInputQuoteField, info: InfoField):
        """询价录入错误回报

        :param obj:
        :param quote:
        :return:
        """
        print("=== [TRADE] OnErrRtnForQuoteInsert ===\n{0}".format(quote.__dict__))
        print(info)
