#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'HaiFeng'
__mtime__ = '2016/9/21'
"""

from typing import Literal
from enum import Enum
from typing_extensions import override
from py_ctp.datatype import (
    TThostFtdcBizTypeType,
    TThostFtdcContingentConditionType,
    TThostFtdcDirectionType,
    TThostFtdcForceCloseReasonType,
    TThostFtdcHedgeFlagType,
    TThostFtdcInstLifePhaseType,
    TThostFtdcMaxMarginSideAlgorithmType,
    TThostFtdcOffsetFlagType,
    TThostFtdcOptionsTypeType,
    TThostFtdcOrderPriceTypeType,
    TThostFtdcOrderSourceType,
    TThostFtdcOrderStatusType,
    TThostFtdcOrderSubmitStatusType,
    TThostFtdcOrderTypeType,
    TThostFtdcPosiDirectionType,
    TThostFtdcPositionDateType,
    TThostFtdcPositionDateTypeType,
    TThostFtdcPositionTypeType,
    TThostFtdcPriceSourceType,
    TThostFtdcProductClassType,
    TThostFtdcSpecPosiTypeType,
    TThostFtdcTimeConditionType,
    TThostFtdcTradeSourceType,
    TThostFtdcTradeTypeType,
    TThostFtdcCombinationTypeType,
    TThostFtdcTradingRoleType,
    TThostFtdcVolumeConditionType,
)


class OrderType(Enum):
    """委托类型"""

    Limit = 0
    """限价单"""
    Market = 1
    """市价单"""
    FAK = 2
    """部成立撤"""
    FOK = 3
    """全成立撤"""

    def __int__(self) -> Literal[0, 1, 2, 3]:
        return self.value


class InfoField:
    """返回信息"""

    def __init__(self) -> None:
        """Constructor"""
        self.ErrorID: int = 0
        """错误号"""
        self.ErrorMsg: str = "正确"
        """错误描述"""

    @override
    def __str__(self) -> str:
        return f"ErrorID:{self.ErrorID}, ErrorMsg:{self.ErrorMsg}"


class OrderField:
    """报单响应"""

    def __init__(self) -> None:
        """initionalize"""
        self.OrderID: str = ""
        """委托标识"""
        self.InstrumentID: str = ""
        """合约"""
        self.ExchangeID: str = ""
        """交易所"""
        self.Direction: TThostFtdcDirectionType = TThostFtdcDirectionType.THOST_FTDC_D_Buy
        """买卖"""
        self.Offset: TThostFtdcOffsetFlagType = TThostFtdcOffsetFlagType.THOST_FTDC_OF_Open
        """开平"""
        self.LimitPrice: float = 0.0
        """限价单价格"""
        self.AvgPrice: float = 0.0
        """报单均价"""
        self.InsertTime: str = ""
        """委托时间"""
        self.TradeTime: str = ""
        """成交时间"""
        self.TradeVolume: int = 0
        """成交数量(本次)"""
        self.Volume: int = 0
        """委托数量"""
        self.VolumeLeft: int = 0
        """未成交数量"""
        self.Status: TThostFtdcOrderStatusType = TThostFtdcOrderStatusType.THOST_FTDC_OST_Unknown
        """委托状态"""
        self.StatusMsg: str = ""
        """状态描述"""
        self.IsLocal: bool = False
        """是否本地委托"""
        self.Custom: int = 0
        """委托自定义标识"""
        self.SysID: str = ""
        """系统(交易所)ID"""
        self.BrokerID: str = ""
        """经纪公司代码"""
        self.InvestorID: str = ""
        """投资者代码"""
        self.OrderRef: str = ""
        """报单引用"""
        self.UserID: str = ""
        """用户代码"""
        self.OrderPriceType: TThostFtdcOrderPriceTypeType = TThostFtdcOrderPriceTypeType.THOST_FTDC_OPT_AnyPrice
        """报单价格条件"""
        self.CombOffsetFlag: TThostFtdcOffsetFlagType = TThostFtdcOffsetFlagType.THOST_FTDC_OF_Open
        """组合开平标志"""
        self.CombHedgeFlag: TThostFtdcHedgeFlagType = TThostFtdcHedgeFlagType.THOST_FTDC_HF_Speculation
        """组合投机套保标志"""
        self.VolumeTotalOriginal: int = 0
        """原始委托数量"""
        self.TimeCondition: TThostFtdcTimeConditionType = TThostFtdcTimeConditionType.THOST_FTDC_TC_GFD
        """有效期类型"""
        self.GTDDate: str = ""
        """GTD日期"""
        self.VolumeCondition: TThostFtdcVolumeConditionType = TThostFtdcVolumeConditionType.THOST_FTDC_VC_AV
        """成交量类型"""
        self.MinVolume: int = 0
        """最小成交量"""
        self.ContingentCondition: TThostFtdcContingentConditionType = TThostFtdcContingentConditionType.THOST_FTDC_CC_Immediately
        """触发条件"""
        self.StopPrice: float = 0.0
        """止损价"""
        self.ForceCloseReason: TThostFtdcForceCloseReasonType = TThostFtdcForceCloseReasonType.THOST_FTDC_FCC_NotForceClose
        """强平原因"""
        self.IsAutoSuspend: bool = False
        """是否自动挂起"""
        self.BusinessUnit: str = ""
        """业务单元"""
        self.RequestID: int = 0
        """请求编号"""
        self.OrderLocalID: str = ""
        """本地报单编号"""
        self.ParticipantID: str = ""
        """会员号"""
        self.ClientID: str = ""
        """客户端编号"""
        self.TraderID: str = ""
        """交易员代码"""
        self.InstallID: int = 0
        """安装编号"""
        self.BrokerOrderSeq: str = ""
        """经纪公司报单序号"""
        self.OrderSubmitStatus: TThostFtdcOrderSubmitStatusType = TThostFtdcOrderSubmitStatusType.THOST_FTDC_OSS_Accepted
        """报单提交状态"""
        self.NotifySequence: int = 0
        """通知序号"""
        self.TradingDay: str = ""
        """交易日"""
        self.SettlementID: int = 0
        """结算编号"""
        self.SequenceNo: int = 0
        """报单序号"""
        self.OrderSource: TThostFtdcOrderSourceType = TThostFtdcOrderSourceType.THOST_FTDC_OSRC_Participant
        """报单来源"""
        self.OrderType: TThostFtdcOrderTypeType = TThostFtdcOrderTypeType.THOST_FTDC_ORDT_Normal
        """报单类型"""
        self.VolumeTraded: int = 0
        """成交数量"""
        self.VolumeTotal: int = 0
        """总数量"""
        self.InsertDate: str = ""
        """插入日期"""
        self.ActiveTime: str = ""
        """激活时间"""
        self.SuspendTime: str = ""
        """挂起时间"""
        self.UpdateTime: str = ""
        """更新时间"""
        self.CancelTime: str = ""
        """撤销时间"""
        # 添加缺失的字段
        self.reserve1: str = ""
        """保留字段1"""
        self.reserve2: str = ""
        """保留字段2"""
        self.ExchangeInstID: str = ""
        """交易所合约ID"""
        self.FrontID: int = 0
        """前置编号"""
        self.SessionID: int = 0
        """会话编号"""
        self.UserProductInfo: str = ""
        """用户产品信息"""
        self.UserForceClose: bool = False
        """是否用户强平"""
        self.ActiveUserID: str = ""
        """激活用户代码"""
        self.RelativeOrderSysID: str = ""
        """相关报单系统ID"""
        self.ZCETotalTradedVolume: int = 0
        """郑商所总成交数量"""
        self.IsSwapOrder: bool = False
        """是否交换报单"""
        self.BranchID: str = ""
        """分支机构代码"""
        self.InvestUnitID: str = ""
        """投资单元代码"""
        self.AccountID: str = ""
        """账户代码"""
        self.CurrencyID: str = ""
        """货币代码"""
        self.reserve3: str = ""
        """保留字段3"""
        self.MacAddress: str = ""
        """Mac地址"""
        self.IPAddress: str = ""
        """IP地址"""
        self.OrderMemo: str = ""
        """报单备注"""
        self.SessionReqSeq: int = 0
        """会话请求序号"""
        self.ClearingPartID: str = ""
        """清算会员代码"""
        self.ActiveTraderID: str = ""
        """激活交易员代码"""

    @override
    def __str__(self) -> str:
        """"""
        return f"OrderID: {self.OrderID}, InstrumentID: {self.InstrumentID}, ExchangeID: {self.ExchangeID}, Direction: {self.Direction}, Offset: {self.Offset}, LimitPrice: {self.LimitPrice}, AvgPrice: {self.AvgPrice}, InsertTime: {self.InsertTime}, TradeTime: {self.TradeTime}, TradeVolume: {self.TradeVolume}, Volume: {self.Volume}, VolumeLeft: {self.VolumeLeft}, Status: {self.Status}, StatusMsg: {self.StatusMsg}, IsLocal: {self.IsLocal}, Custom: {self.Custom}, SysID: {self.SysID}, BrokerID: {self.BrokerID}, InvestorID: {self.InvestorID}, OrderRef: {self.OrderRef}, UserID: {self.UserID}, OrderPriceType: {self.OrderPriceType}, CombOffsetFlag: {self.CombOffsetFlag}, CombHedgeFlag: {self.CombHedgeFlag}, VolumeTotalOriginal: {self.VolumeTotalOriginal}, TimeCondition: {self.TimeCondition}, GTDDate: {self.GTDDate}, VolumeCondition: {self.VolumeCondition}, MinVolume: {self.MinVolume}, ContingentCondition: {self.ContingentCondition}, StopPrice: {self.StopPrice}, ForceCloseReason: {self.ForceCloseReason}, IsAutoSuspend: {self.IsAutoSuspend}, BusinessUnit: {self.BusinessUnit}, RequestID: {self.RequestID}, OrderLocalID: {self.OrderLocalID}, ParticipantID: {self.ParticipantID}, ClientID: {self.ClientID}, TraderID: {self.TraderID}, InstallID: {self.InstallID}, OrderSubmitStatus: {self.OrderSubmitStatus}, NotifySequence: {self.NotifySequence}, TradingDay: {self.TradingDay}, SettlementID: {self.SettlementID}, OrderSource: {self.OrderSource}, OrderType: {self.OrderType}, VolumeTraded: {self.VolumeTraded}, VolumeTotal: {self.VolumeTotal}, InsertDate: {self.InsertDate}, ActiveTime: {self.ActiveTime}, SuspendTime: {self.SuspendTime}, UpdateTime: {self.UpdateTime}, CancelTime: {self.CancelTime}, reserve1: {self.reserve1}, reserve2: {self.reserve2}, ExchangeInstID: {self.ExchangeInstID}, FrontID: {self.FrontID}, SessionID: {self.SessionID}, UserProductInfo: {self.UserProductInfo}, UserForceClose: {self.UserForceClose}, ActiveUserID: {self.ActiveUserID}, RelativeOrderSysID: {self.RelativeOrderSysID}, ZCETotalTradedVolume: {self.ZCETotalTradedVolume}, IsSwapOrder: {self.IsSwapOrder}, BranchID: {self.BranchID}, InvestUnitID: {self.InvestUnitID}, AccountID: {self.AccountID}, CurrencyID: {self.CurrencyID}, reserve3: {self.reserve3}, MacAddress: {self.MacAddress}, IPAddress: {self.IPAddress}, OrderMemo: {self.OrderMemo}, SessionReqSeq: {self.SessionReqSeq}, ClearingPartID: {self.ClearingPartID}, ActiveTraderID: {self.ActiveTraderID}"


class TradeField:
    """成交响应"""

    def __init__(self) -> None:
        """Constructor"""
        self.TradeID: str = ""
        """成交标识"""
        self.InvestorID: str = ""
        """投资者ID"""
        self.InstrumentID: str = ""
        """合约"""
        self.ExchangeID: str = ""
        """交易所"""
        self.Direction: TThostFtdcDirectionType = TThostFtdcDirectionType.THOST_FTDC_D_Buy
        """买卖"""
        self.Offset: TThostFtdcOffsetFlagType = TThostFtdcOffsetFlagType.THOST_FTDC_OF_Open
        """开平"""
        self.Hedge: TThostFtdcHedgeFlagType = TThostFtdcHedgeFlagType.THOST_FTDC_HF_Speculation
        """投机套保"""
        self.Price: float = 0.0
        """成交价"""
        self.Volume: int = 0
        """成交数量"""
        self.TradeTime: str = ""
        """成交时间"""
        self.TradingDay: str = ""
        """交易日"""
        self.OrderID: str = ""
        """'对应的委托标识"""
        self.SysID: str = ""
        """对应的系统(交易所)ID"""
        self.BrokerID: str = ""
        """经纪公司代码"""
        self.OrderRef: str = ""
        """报单引用"""
        self.UserID: str = ""
        """用户代码"""
        self.ParticipantID: str = ""
        """会员号"""
        self.ClientID: str = ""
        """客户端编号"""
        self.TradingRole: TThostFtdcTradingRoleType = TThostFtdcTradingRoleType.THOST_FTDC_ER_Broker
        """交易角色"""
        self.TradeType: TThostFtdcTradeTypeType = TThostFtdcTradeTypeType.THOST_FTDC_TRDT_Common
        """成交类型"""
        self.PriceSource: TThostFtdcPriceSourceType = TThostFtdcPriceSourceType.THOST_FTDC_PSRC_Buy
        """价格来源"""
        self.TraderID: str = ""
        """交易员代码"""
        self.OrderLocalID: str = ""
        """本地报单编号"""
        self.ClearingPartID: str = ""
        """清算会员号"""
        self.BusinessUnit: str = ""
        """业务单元"""
        self.SequenceNo: int = 0
        """序号"""
        self.SettlementID: int = 0
        """结算编号"""
        self.BrokerOrderSeq: int = 0
        """经纪公司报单序号"""
        self.TradeSource: TThostFtdcTradeSourceType = TThostFtdcTradeSourceType.THOST_FTDC_TSRC_NORMAL
        """成交来源"""
        self.InvestUnitID: str = ""
        """投资单元代码"""
        self.ExchangeInstID: str = ""
        """交易所合约ID"""
        self.TradeDate: str = ""
        """成交日期"""
        # 添加缺失的保留字段
        self.reserve1: str = ""
        """保留字段1"""
        self.reserve2: str = ""
        """保留字段2"""

    @override
    def __str__(self) -> str:
        """"""
        return f"TradeID: {self.TradeID}, InstrumentID: {self.InstrumentID}, ExchangeID: {self.ExchangeID}, Direction: {self.Direction}, Offset: {self.Offset}, Price: {self.Price}, Volume: {self.Volume}, TradeTime: {self.TradeTime}, TradingDay: {self.TradingDay}, OrderID: {self.OrderID}, SysID: {self.SysID}, BrokerID: {self.BrokerID}, OrderRef: {self.OrderRef}, UserID: {self.UserID}, ParticipantID: {self.ParticipantID}, ClientID: {self.ClientID}, TradingRole: {self.TradingRole}, TradeType: {self.TradeType}, PriceSource: {self.PriceSource}, TraderID: {self.TraderID}, OrderLocalID: {self.OrderLocalID}, ClearingPartID: {self.ClearingPartID}, BusinessUnit: {self.BusinessUnit}, SequenceNo: {self.SequenceNo}, SettlementID: {self.SettlementID}, BrokerOrderSeq: {self.BrokerOrderSeq}, TradeSource: {self.TradeSource}, InvestUnitID: {self.InvestUnitID}, ExchangeInstID: {self.ExchangeInstID}, TradeDate: {self.TradeDate}, reserve1: {self.reserve1}, reserve2: {self.reserve2}"


class InstrumentField:
    """合约"""

    def __init__(self) -> None:
        """Constructor"""
        self.InstrumentID: str = ""
        """合约"""
        self.InstrumentName: str = ""
        """名称"""
        self.ProductID: str = ""
        """品种"""
        self.ExchangeID: str = ""
        """交易所"""
        self.VolumeMultiple: int = 0
        """合约乘数"""
        self.PriceTick: float = 0.0
        """每跳价格变动"""
        self.MaxOrderVolume: int = 9999
        """最大单笔下单量"""
        self.ProductClass: TThostFtdcProductClassType = TThostFtdcProductClassType.THOST_FTDC_PC_Futures
        """产品类别"""
        self.DeliveryYear: int = 0
        """交割年份"""
        self.DeliveryMonth: int = 0
        """交割月"""
        self.MaxMarketOrderVolume: int = 0
        """市价单最大下单量"""
        self.MinMarketOrderVolume: int = 0
        """市价单最小下单量"""
        self.MaxLimitOrderVolume: int = 0
        """限价单最大下单量"""
        self.MinLimitOrderVolume: int = 0
        """限价单最小下单量"""
        self.CreateDate: str = ""
        """创建日"""
        self.OpenDate: str = ""
        """上市日"""
        self.ExpireDate: str = ""
        """到期日"""
        self.StartDelivDate: str = ""
        """开始交割日"""
        self.EndDelivDate: str = ""
        """结束交割日"""
        self.InstLifePhase: TThostFtdcInstLifePhaseType = TThostFtdcInstLifePhaseType.THOST_FTDC_IP_NotStart
        """合约生命周期状态"""
        self.IsTrading: bool = False
        """是否交易"""
        self.PositionType: TThostFtdcPositionTypeType = TThostFtdcPositionTypeType.THOST_FTDC_PT_Net
        """持仓类型"""
        self.PositionDateType: TThostFtdcPositionDateTypeType = TThostFtdcPositionDateTypeType.THOST_FTDC_PDT_NoUseHistory
        """持仓日期类型"""
        self.LongMarginRatio: float = 0.0
        """多头保证金率"""
        self.ShortMarginRatio: float = 0.0
        """空头保证金率"""
        self.MaxMarginSideAlgorithm: TThostFtdcMaxMarginSideAlgorithmType = TThostFtdcMaxMarginSideAlgorithmType.THOST_FTDC_MMSA_YES
        """单向大边保证金算法"""
        self.StrikePrice: float = 0.0
        """行权价"""
        self.OptionsType: TThostFtdcOptionsTypeType = TThostFtdcOptionsTypeType.THOST_FTDC_CP_CallOptions
        """期权类型"""
        self.UnderlyingMultiple: int = 0
        """标的合约乘数"""
        self.CombinationType: TThostFtdcCombinationTypeType = TThostFtdcCombinationTypeType.THOST_FTDC_COMBT_Future
        """组合类型"""
        self.ExchangeInstID: str = ""
        """交易所合约ID"""
        self.UnderlyingInstrID: str = ""
        """标的合约"""
        # 添加缺失的保留字段
        self.reserve1: str = ""
        """保留字段1"""
        self.reserve2: str = ""
        """保留字段2"""
        self.reserve3: str = ""
        """保留字段3"""
        self.reserve4: str = ""
        """保留字段4"""

    @override
    def __str__(self) -> str:
        """"""
        return f"InstrumentID:{self.InstrumentID}, InstrumentName:{self.InstrumentName}, ProductID:{self.ProductID}, ExchangeID:{self.ExchangeID}, VolumeMultiple:{self.VolumeMultiple}, PriceTick:{self.PriceTick}, MaxOrderVolume:{self.MaxOrderVolume}, ProductClass:{self.ProductClass},DeliveryYear:{self.DeliveryYear}, DeliveryMonth:{self.DeliveryMonth}, MaxMarketOrderVolume:{self.MaxMarketOrderVolume}, MinMarketOrderVolume:{self.MinMarketOrderVolume}, MaxLimitOrderVolume:{self.MaxLimitOrderVolume}, MinLimitOrderVolume:{self.MinLimitOrderVolume}, CreateDate:{self.CreateDate}, OpenDate:{self.OpenDate}, ExpireDate:{self.ExpireDate}, StartDelivDate:{self.StartDelivDate}, EndDelivDate:{self.EndDelivDate}, InstLifePhase:{self.InstLifePhase}, IsTrading:{self.IsTrading}, PositionType:{self.PositionType}, PositionDateType:{self.PositionDateType}, LongMarginRatio:{self.LongMarginRatio}, ShortMarginRatio:{self.ShortMarginRatio}, MaxMarginSideAlgorithm:{self.MaxMarginSideAlgorithm}, StrikePrice:{self.StrikePrice}, OptionsType:{self.OptionsType}, UnderlyingMultiple:{self.UnderlyingMultiple}, CombinationType:{self.CombinationType}, ExchangeInstID:{self.ExchangeInstID}, UnderlyingInstrID:{self.UnderlyingInstrID}, reserve1:{self.reserve1}, reserve2:{self.reserve2}, reserve3:{self.reserve3}, reserve4:{self.reserve4}"


class TradingAccount:
    """交易帐户"""

    def __init__(self) -> None:
        """Constructor"""
        """账户ID"""
        self.PreBalance: float = 0.0
        """昨日结算"""
        self.PositionProfit: float = 0.0
        """持仓盈亏"""
        self.CloseProfit: float = 0.0
        """平仓盈亏"""
        self.Commission: float = 0.0
        """手续费"""
        self.CurrMargin: float = 0.0
        """保证金"""
        self.FrozenCash: float = 0.0
        """冻结"""
        self.Available: float = 0.0
        """可用"""
        self.Fund: float = 0.0
        """动态权益"""
        self.Risk: float = 0.0
        """风险度"""
        self.BrokerID: str = ""
        """经纪公司代码"""
        self.AccountID: str = ""
        """账户ID"""
        self.PreMortgage: float = 0.0
        """昨质押金"""
        self.PreCredit: float = 0.0
        """昨信用额度"""
        self.PreDeposit: float = 0.0
        """昨入金"""
        self.PreMargin: float = 0.0
        """昨保证金"""
        self.InterestBase: float = 0.0
        """利息基数"""
        self.Interest: float = 0.0
        """利息"""
        self.Deposit: float = 0.0
        """入金"""
        self.Withdraw: float = 0.0
        """出金"""
        self.CashIn: float = 0.0
        """资金差额"""
        self.FrozenMargin: float = 0.0
        """冻结保证金"""
        self.FrozenCommission: float = 0.0
        """冻结手续费"""
        self.Balance: float = 0.0
        """资金余额"""
        self.WithdrawQuota: float = 0.0
        """可取资金"""
        self.Reserve: float = 0.0
        """保留资金"""
        self.TradingDay: str = ""
        """交易日"""
        self.SettlementID: int = 0
        """结算编号"""
        self.Credit: float = 0.0
        """信用额度"""
        self.Mortgage: float = 0.0
        """质押金"""
        self.ExchangeMargin: float = 0.0
        """交易所保证金"""
        self.DeliveryMargin: float = 0.0
        """交割保证金"""
        self.ExchangeDeliveryMargin: float = 0.0
        """交易所交割保证金"""
        self.ReserveBalance: float = 0.0
        """保留余额"""
        self.CurrencyID: str = ""
        """币种代码"""
        self.PreFundMortgageIn: float = 0.0
        """昨资金质押入"""
        self.PreFundMortgageOut: float = 0.0
        """昨资金质押出"""
        self.FundMortgageIn: float = 0.0
        """资金质押入"""
        self.FundMortgageOut: float = 0.0
        """资金质押出"""
        self.FundMortgageAvailable: float = 0.0
        """可用资金质押"""
        self.MortgageableFund: float = 0.0
        """可质押资金"""
        self.SpecProductMargin: float = 0.0
        """特殊产品保证金"""
        self.SpecProductFrozenMargin: float = 0.0
        """特殊产品冻结保证金"""
        self.SpecProductCommission: float = 0.0
        """特殊产品手续费"""
        self.SpecProductFrozenCommission: float = 0.0
        """特殊产品冻结手续费"""
        self.SpecProductPositionProfit: float = 0.0
        """特殊产品持仓盈亏"""
        self.SpecProductCloseProfit: float = 0.0
        """特殊产品平仓盈亏"""
        self.SpecProductPositionProfitByAlg: float = 0.0
        """特殊产品算法持仓盈亏"""
        self.SpecProductExchangeMargin: float = 0.0
        """特殊产品交易所保证金"""
        self.BizType: TThostFtdcBizTypeType = TThostFtdcBizTypeType.THOST_FTDC_BZTP_None
        """业务类型"""
        self.FrozenSwap: float = 0.0
        """冻结互换保证金"""
        self.RemainSwap: float = 0.0
        """剩余换汇额度"""
        self.OptionValue: float = 0.0
        """期权市值"""

    @override
    def __str__(self) -> str:
        """"""
        return f"PreBalance: {self.PreBalance}, PositionProfit: {self.PositionProfit}, CloseProfit: {self.CloseProfit}, Commission: {self.Commission}, CurrMargin: {self.CurrMargin}, FrozenCash: {self.FrozenCash}, Available: {self.Available}, Fund: {self.Fund}, Risk: {self.Risk}, BrokerID: {self.BrokerID}, AccountID: {self.AccountID}, PreMortgage: {self.PreMortgage}, PreCredit: {self.PreCredit}, PreDeposit: {self.PreDeposit}, PreMargin: {self.PreMargin}, InterestBase: {self.InterestBase}, Interest: {self.Interest}, Deposit: {self.Deposit}, Withdraw: {self.Withdraw}, CashIn: {self.CashIn}, FrozenMargin: {self.FrozenMargin}, FrozenCommission: {self.FrozenCommission}, Balance: {self.Balance}, WithdrawQuota: {self.WithdrawQuota}, Reserve: {self.Reserve}, TradingDay: {self.TradingDay}, SettlementID: {self.SettlementID}, Credit: {self.Credit}, Mortgage: {self.Mortgage}, ExchangeMargin: {self.ExchangeMargin}, DeliveryMargin: {self.DeliveryMargin}, ExchangeDeliveryMargin: {self.ExchangeDeliveryMargin}, ReserveBalance: {self.ReserveBalance}, CurrencyID: {self.CurrencyID}, PreFundMortgageIn: {self.PreFundMortgageIn}, PreFundMortgageOut: {self.PreFundMortgageOut}, FundMortgageIn: {self.FundMortgageIn}, FundMortgageOut: {self.FundMortgageOut}, FundMortgageAvailable: {self.FundMortgageAvailable}, MortgageableFund: {self.MortgageableFund}, SpecProductMargin: {self.SpecProductMargin}, SpecProductFrozenMargin: {self.SpecProductFrozenMargin}, SpecProductCommission: {self.SpecProductCommission}, SpecProductFrozenCommission: {self.SpecProductFrozenCommission}, SpecProductPositionProfit: {self.SpecProductPositionProfit}, SpecProductCloseProfit: {self.SpecProductCloseProfit}, SpecProductPositionProfitByAlg: {self.SpecProductPositionProfitByAlg}, SpecProductExchangeMargin: {self.SpecProductExchangeMargin}, BizType: {self.BizType}, FrozenSwap: {self.FrozenSwap}, RemainSwap: {self.RemainSwap}, OptionValue: {self.OptionValue}"


class PositionField:
    """持仓"""

    def __init__(self) -> None:
        """Constructor"""
        self.reserve1: str = ""
        """保留的无效字段"""
        self.InstrumentID: str = ""
        """合约"""
        self.Direction: TThostFtdcPosiDirectionType = TThostFtdcPosiDirectionType.THOST_FTDC_PD_Net
        """多空"""
        self.Price: float = 0.0
        """持仓价格"""
        self.Position: int = 0
        """持仓量"""
        self.YdPosition: int = 0
        """昨持仓"""
        self.TdPosition: int = 0
        """今持仓"""
        self.CloseProfit: float = 0.0
        """平仓盈亏"""
        self.PositionProfit: float = 0.0
        """持仓盈亏"""
        self.Commission: float = 0.0
        """手续费"""
        self.Margin: float = 0.0
        """保证金"""
        self.BrokerID: str = ""
        """经纪公司代码"""
        self.InvestorID: str = ""
        """投资者代码"""
        self.InvestUnitID: str = ""
        """投资单元代码"""
        self.HedgeFlag: TThostFtdcHedgeFlagType = TThostFtdcHedgeFlagType.THOST_FTDC_HF_Speculation
        """投机套保标志"""
        self.PositionDate: TThostFtdcPositionDateType = TThostFtdcPositionDateType.THOST_FTDC_PSD_Today
        """持仓日期"""
        self.LongFrozen: int = 0
        """多头冻结"""
        self.ShortFrozen: int = 0
        """空头冻结"""
        self.LongFrozenAmount: float = 0.0
        """多头冻结金额"""
        self.ShortFrozenAmount: float = 0.0
        """空头冻结金额"""
        self.OpenVolume: int = 0
        """开仓数量"""
        self.CloseVolume: int = 0
        """平仓数量"""
        self.OpenAmount: float = 0.0
        """开仓金额"""
        self.CloseAmount: float = 0.0
        """平仓金额"""
        self.PositionCost: float = 0.0
        """持仓成本"""
        self.PreMargin: float = 0.0
        """昨保证金"""
        self.UseMargin: float = 0.0
        """使用保证金"""
        self.FrozenMargin: float = 0.0
        """冻结保证金"""
        self.FrozenCash: float = 0.0
        """冻结资金"""
        self.FrozenCommission: float = 0.0
        """冻结手续费"""
        self.CashIn: float = 0.0
        """入金金额"""
        self.PreSettlementPrice: float = 0.0
        """昨结算价"""
        self.SettlementPrice: float = 0.0
        """结算价"""
        self.TradingDay: str = ""
        """交易日"""
        self.SettlementID: int = 0
        """结算编号"""
        self.OpenCost: float = 0.0
        """开仓成本"""
        self.PositionCostOffset: float = 0.0
        """持仓成本偏移"""
        self.ExchangeMargin: float = 0.0
        """交易所保证金"""
        self.CombPosition: int = 0
        """组合持仓量"""
        self.CombLongFrozen: int = 0
        """组合多头冻结"""
        self.CombShortFrozen: int = 0
        """组合空头冻结"""
        self.CloseProfitByDate: float = 0.0
        """按日期平仓盈亏"""
        self.CloseProfitByTrade: float = 0.0
        """按成交平仓盈亏"""
        self.TodayPosition: int = 0
        """今日持仓"""
        self.MarginRateByMoney: float = 0.0
        """按金额保证金率"""
        self.MarginRateByVolume: float = 0.0
        """按手数保证金率"""
        self.TasPosition: int = 0
        """持仓量"""
        self.TasPositionCost: float = 0.0
        """持仓成本"""
        self.OptionValue: float = 0.0
        """期权价值"""
        self.StrikeFrozen: int = 0
        """行权冻结"""
        self.StrikeFrozenAmount: float = 0.0
        """行权冻结金额"""
        self.AbandonFrozen: int = 0
        """放弃冻结"""
        self.ExchangeID: str = ""
        """交易所代码"""
        self.YdStrikeFrozen: int = 0
        """昨行权冻结"""

    @override
    def __str__(self) -> str:
        """"""
        return f"reserve1: {self.reserve1}, InstrumentID: {self.InstrumentID}, Direction: {self.Direction}, Price: {self.Price}, Position: {self.Position}, TdPosition: {self.TdPosition}, YdPosition: {self.YdPosition}, CloseProfit: {self.CloseProfit}, PositionProfit: {self.PositionProfit}, Commission: {self.Commission}, Margin: {self.Margin}, BrokerID: {self.BrokerID}, InvestorID: {self.InvestorID}, InvestUnitID: {self.InvestUnitID}, HedgeFlag: {self.HedgeFlag}, PositionDate: {self.PositionDate}, LongFrozen: {self.LongFrozen}, ShortFrozen: {self.ShortFrozen}, LongFrozenAmount: {self.LongFrozenAmount}, ShortFrozenAmount: {self.ShortFrozenAmount}, OpenVolume: {self.OpenVolume}, CloseVolume: {self.CloseVolume}, OpenAmount: {self.OpenAmount}, CloseAmount: {self.CloseAmount}, PositionCost: {self.PositionCost}, PreMargin: {self.PreMargin}, UseMargin: {self.UseMargin}, FrozenMargin: {self.FrozenMargin}, FrozenCash: {self.FrozenCash}, FrozenCommission: {self.FrozenCommission}, CashIn: {self.CashIn}, PreSettlementPrice: {self.PreSettlementPrice}, SettlementPrice: {self.SettlementPrice}, TradingDay: {self.TradingDay}, SettlementID:{self.SettlementID}, OpenCost: {self.OpenCost}, PositionCostOffset: {self.PositionCostOffset}, ExchangeMargin: {self.ExchangeMargin}, CombPosition: {self.CombPosition}, CombLongFrozen: {self.CombLongFrozen}, CombShortFrozen: {self.CombShortFrozen}, CloseProfitByDate: {self.CloseProfitByDate}, CloseProfitByTrade: {self.CloseProfitByTrade}, TodayPosition: {self.TodayPosition}, MarginRateByMoney: {self.MarginRateByMoney}, MarginRateByVolume: {self.MarginRateByVolume}, TasPosition: {self.TasPosition}, TasPositionCost: {self.TasPositionCost}, OptionValue: {self.OptionValue}, StrikeFrozen: {self.StrikeFrozen}, StrikeFrozenAmount: {self.StrikeFrozenAmount}, AbandonFrozen: {self.AbandonFrozen}, ExchangeID: {self.ExchangeID}, YdStrikeFrozen: {self.YdStrikeFrozen}"


class PositionDetail:
    """持仓明细"""

    def __init__(self) -> None:
        """"""
        self.reserve1: str = ""
        """保留的无效字段"""
        self.InstrumentID: str = ""
        """合约ID"""
        self.HedgeFlag: TThostFtdcHedgeFlagType = TThostFtdcHedgeFlagType.THOST_FTDC_HF_Speculation
        """投保"""
        self.Direction: TThostFtdcDirectionType = TThostFtdcDirectionType.THOST_FTDC_D_Buy
        """持仓方向"""
        self.TradeID: str = ""
        """交易ID"""
        self.Volume: int = 0
        """持仓量"""
        self.OpenPrice: float = 0.0
        """开仓价格"""
        self.OpenDate: str = ""
        """开仓日期"""
        self.TradeType: TThostFtdcTradeTypeType = TThostFtdcTradeTypeType.THOST_FTDC_TRDT_Common
        """交易类型"""
        self.reserve2: str = ""
        """保留的无效字段"""
        self.PositionProfit: float = 0.0
        """盯市持仓盈亏"""
        self.CloseProfit: float = 0.0
        """盯市平仓盈亏"""
        self.BrokerID: str = ""
        """经纪公司代码"""
        self.InvestorID: str = ""
        """投资者代码"""
        self.TradingDay: str = ""
        """交易日"""
        self.SettlementID: int = 0
        """结算编号"""
        self.ExchangeID: str = ""
        """交易所代码"""
        self.CloseProfitByDate: float = 0.0
        """按日期平仓盈亏"""
        self.CloseProfitByTrade: float = 0.0
        """按成交平仓盈亏"""
        self.PositionProfitByDate: float = 0.0
        """按日期持仓盈亏"""
        self.PositionProfitByTrade: float = 0.0
        """按成交持仓盈亏"""
        self.Margin: float = 0.0
        """保证金"""
        self.ExchMargin: float = 0.0
        """交易所保证金"""
        self.MarginRateByMoney: float = 0.0
        """按金额保证金率"""
        self.MarginRateByVolume: float = 0.0
        """按手数保证金率"""
        self.LastSettlementPrice: float = 0.0
        """上次结算价"""
        self.SettlementPrice: float = 0.0
        """结算价"""
        self.CloseVolume: int = 0
        """平仓数量"""
        self.CloseAmount: float = 0.0
        """平仓金额"""
        self.TimeFirstVolume: int = 0
        """逐笔持仓剩余数量"""
        self.InvestUnitID: str = ""
        """投资单元代码"""
        self.SpecPosiType: TThostFtdcSpecPosiTypeType = TThostFtdcSpecPosiTypeType.THOST_FTDC_SPOST_Common
        """特殊持仓类型"""
        self.CombInstrumentID: str = ""
        """组合合约ID"""

    @override
    def __str__(self) -> str:
        return f"reserve1: {self.reserve1}, InstrumentID: {self.InstrumentID}, HedgeFlag: {self.HedgeFlag}, Direction: {self.Direction}, TradeID: {self.TradeID}, Volume: {self.Volume}, OpenPrice: {self.OpenPrice}, OpenDate: {self.OpenDate}, TradeType: {self.TradeType}, reserve2: {self.reserve2}, PositionProfit: {self.PositionProfit}, CloseProfit: {self.CloseProfit}, BrokerID: {self.BrokerID}, InvestorID: {self.InvestorID}, TradingDay: {self.TradingDay}, SettlementID: {self.SettlementID}, ExchangeID: {self.ExchangeID}, CloseProfitByDate: {self.CloseProfitByDate}, CloseProfitByTrade: {self.CloseProfitByTrade}, PositionProfitByDate: {self.PositionProfitByDate}, PositionProfitByTrade: {self.PositionProfitByTrade}, Margin: {self.Margin}, ExchMargin: {self.ExchMargin}, MarginRateByMoney: {self.MarginRateByMoney}, MarginRateByVolume: {self.MarginRateByVolume}, LastSettlementPrice: {self.LastSettlementPrice}, SettlementPrice: {self.SettlementPrice}, CloseVolume: {self.CloseVolume}, CloseAmount: {self.CloseAmount}, TimeFirstVolume: {self.TimeFirstVolume}, InvestUnitID: {self.InvestUnitID}, SpecPosiType: {self.SpecPosiType}, CombInstrumentID: {self.CombInstrumentID}"


class Tick:
    """分笔数据"""

    def __init__(self) -> None:
        """初始化"""
        self.TradingDay: str = ""
        """交易日"""
        self.reserve1: str = ""
        """保留的无效字段"""
        self.ExchangeID: str = ""
        """交易所代码"""
        self.reserve2: str = ""
        """保留的无效字段"""
        self.LastPrice: float = 0.0
        """最新价"""
        self.PreSettlementPrice: float = 0.0
        """昨结算价"""
        self.PreClosePrice: float = 0.0
        """昨收盘价"""
        self.PreOpenInterest: float = 0.0
        """昨持仓量"""
        self.OpenPrice: float = 0.0
        """开盘价"""
        self.HighestPrice: float = 0.0
        """最高价"""
        self.LowestPrice: float = 0.0
        """最低价"""
        self.Volume: int = 0
        """成交量"""
        self.Turnover: float = 0.0
        """成交额"""
        self.OpenInterest: float = 0.0
        """持仓量"""
        self.ClosePrice: float = 0.0
        """收盘价"""
        self.SettlementPrice: float = 0.0
        """本次结算价"""
        self.UpperLimitPrice: float = 0.0
        """涨板价"""
        self.LowerLimitPrice: float = 0.0
        """跌板价"""
        self.PreDelta: float = 0.0
        """昨虚实度"""
        self.CurrDelta: float = 0.0
        """今虚实度"""
        self.UpdateTime: str = ""
        """时间"""
        self.UpdateMillisec: int = 0
        """毫秒"""
        self.BidPrice1: float = 0.0
        """挂买价1"""
        self.BidVolume1: int = 0
        """挂买量1"""
        self.AskPrice1: float = 0.0
        """挂卖价1"""
        self.AskVolume1: int = 0
        """挂卖量1"""
        self.BidPrice2: float = 0.0
        """挂买价2"""
        self.BidVolume2: int = 0
        """挂买量2"""
        self.AskPrice2: float = 0.0
        """挂卖价2"""
        self.AskVolume2: int = 0
        """挂卖量2"""
        self.BidPrice3: float = 0.0
        """挂买价3"""
        self.BidVolume3: int = 0
        """挂买量3"""
        self.AskPrice3: float = 0.0
        """挂卖价3"""
        self.AskVolume3: int = 0
        """挂卖量3"""
        self.BidPrice4: float = 0.0
        """挂买价4"""
        self.BidVolume4: int = 0
        """挂买量4"""
        self.AskPrice4: float = 0.0
        """挂卖价4"""
        self.AskVolume4: int = 0
        """挂卖量4"""
        self.BidPrice5: float = 0.0
        """挂买价5"""
        self.BidVolume5: int = 0
        """挂买量5"""
        self.AskPrice5: float = 0.0
        """挂卖价5"""
        self.AskVolume5: int = 0
        """挂卖量5"""
        self.AveragePrice: float = 0.0
        """均价"""
        self.ActionDay: str = ""
        """业务日期"""
        self.InstrumentID: str = ""
        """合约ID"""
        self.ExchangeInstID: str = ""
        """合约在交易所的代码"""
        self.BandingUpperPrice: float = 0.0
        """上带价"""
        self.BandingLowerPrice: float = 0.0
        """下带价"""

        # 验证初始化数据
        self.validate()

    def validate(self) -> None:
        """验证所有字段的类型和值范围是否符合要求"""
        # 验证字符串类型字段
        string_fields = ["TradingDay", "reserve1", "ExchangeID", "reserve2", "UpdateTime", "ActionDay", "InstrumentID", "ExchangeInstID"]
        for field in string_fields:
            value = getattr(self, field)
            if not isinstance(value, str):
                raise TypeError(f"Field {field} must be a string, got {type(value).__name__}")

        # 验证整数类型字段
        int_fields = [
            "Volume",
            "UpdateMillisec",
            "BidVolume1",
            "BidVolume2",
            "BidVolume3",
            "BidVolume4",
            "BidVolume5",
            "AskVolume1",
            "AskVolume2",
            "AskVolume3",
            "AskVolume4",
            "AskVolume5",
        ]
        for field in int_fields:
            value = getattr(self, field)
            if not isinstance(value, int):
                raise TypeError(f"Field {field} must be an integer, got {type(value).__name__}")
            # 验证数量字段不能为负数
            if "Volume" in field or "volume" in field:
                if value < 0:
                    raise ValueError(f"Field {field} cannot be negative")

        # 验证浮点数类型字段
        float_fields = [
            "LastPrice",
            "PreSettlementPrice",
            "PreClosePrice",
            "PreOpenInterest",
            "OpenPrice",
            "HighestPrice",
            "LowestPrice",
            "Turnover",
            "OpenInterest",
            "ClosePrice",
            "SettlementPrice",
            "UpperLimitPrice",
            "LowerLimitPrice",
            "PreDelta",
            "CurrDelta",
            "BidPrice1",
            "BidPrice2",
            "BidPrice3",
            "BidPrice4",
            "BidPrice5",
            "AskPrice1",
            "AskPrice2",
            "AskPrice3",
            "AskPrice4",
            "AskPrice5",
            "AveragePrice",
            "BandingUpperPrice",
            "BandingLowerPrice",
        ]
        for field in float_fields:
            value = getattr(self, field)
            if not isinstance(value, (float, int)):  # 允许整数赋值给浮点数字段
                raise TypeError(f"Field {field} must be a float, got {type(value).__name__}")

        # 验证毫秒字段的范围
        if not (0 <= self.UpdateMillisec <= 999):
            raise ValueError(f"UpdateMillisec must be between 0 and 999, got {self.UpdateMillisec}")

    def __setattr__(self, name: str, value):
        """在设置属性时进行验证"""
        # 先设置值，再验证
        super().__setattr__(name, value)

        # 只验证已知字段
        known_fields = {
            "TradingDay",
            "reserve1",
            "ExchangeID",
            "reserve2",
            "LastPrice",
            "PreSettlementPrice",
            "PreClosePrice",
            "PreOpenInterest",
            "OpenPrice",
            "HighestPrice",
            "LowestPrice",
            "Volume",
            "Turnover",
            "OpenInterest",
            "ClosePrice",
            "SettlementPrice",
            "UpperLimitPrice",
            "LowerLimitPrice",
            "PreDelta",
            "CurrDelta",
            "UpdateTime",
            "UpdateMillisec",
            "BidPrice1",
            "BidVolume1",
            "AskPrice1",
            "AskVolume1",
            "BidPrice2",
            "BidVolume2",
            "AskPrice2",
            "AskVolume2",
            "BidPrice3",
            "BidVolume3",
            "AskPrice3",
            "AskVolume3",
            "BidPrice4",
            "BidVolume4",
            "AskPrice4",
            "AskVolume4",
            "BidPrice5",
            "BidVolume5",
            "AskPrice5",
            "AskVolume5",
            "AveragePrice",
            "ActionDay",
            "InstrumentID",
            "ExchangeInstID",
            "BandingUpperPrice",
            "BandingLowerPrice",
        }

        if name in known_fields:
            # 对单个字段进行快速验证
            if name in {"TradingDay", "reserve1", "ExchangeID", "reserve2", "UpdateTime", "ActionDay", "InstrumentID", "ExchangeInstID"}:
                if not isinstance(value, str):
                    raise TypeError(f"Field {name} must be a string, got {type(value).__name__}")
            elif name in {
                "Volume",
                "UpdateMillisec",
                "BidVolume1",
                "BidVolume2",
                "BidVolume3",
                "BidVolume4",
                "BidVolume5",
                "AskVolume1",
                "AskVolume2",
                "AskVolume3",
                "AskVolume4",
                "AskVolume5",
            }:
                if not isinstance(value, int):
                    raise TypeError(f"Field {name} must be an integer, got {type(value).__name__}")
                if "Volume" in name or "volume" in name:
                    if value < 0:
                        raise ValueError(f"Field {name} cannot be negative")
            else:  # 浮点数字段
                if not isinstance(value, (float, int)):
                    raise TypeError(f"Field {name} must be a float, got {type(value).__name__}")

            # 特殊验证
            if name == "UpdateMillisec":
                if not (0 <= value <= 999):
                    raise ValueError(f"UpdateMillisec must be between 0 and 999, got {value}")

    @override
    def __str__(self) -> str:
        """"""
        return f"InstrumentID:{self.InstrumentID}, LastPrice:{self.LastPrice}, AskPrice1:{self.AskPrice1}, BidPrice1:{self.BidPrice1}, AskVolume1:{self.AskVolume1}, BidVolume1:{self.BidVolume1}, UpdateTime:{self.UpdateTime}, UpdateMillisec:{self.UpdateMillisec}, Volume:{self.Volume}, OpenInterest:{self.OpenInterest}, AveragePrice:{self.AveragePrice}, UpperLimitPrice:{self.UpperLimitPrice}, LowerLimitPrice:{self.LowerLimitPrice}, PreOpenInterest:{self.PreOpenInterest}, TradingDay:{self.TradingDay}, ExchangeID:{self.ExchangeID}, PreSettlementPrice:{self.PreSettlementPrice}, PreClosePrice:{self.PreClosePrice}, OpenPrice:{self.OpenPrice}, HighestPrice:{self.HighestPrice}, LowestPrice:{self.LowestPrice}, Turnover:{self.Turnover}, ClosePrice:{self.ClosePrice}, SettlementPrice:{self.SettlementPrice}, PreDelta:{self.PreDelta}, CurrDelta:{self.CurrDelta}, ActionDay:{self.ActionDay}, ExchangeInstID:{self.ExchangeInstID}, BandingUpperPrice:{self.BandingUpperPrice}, BandingLowerPrice:{self.BandingLowerPrice}"
