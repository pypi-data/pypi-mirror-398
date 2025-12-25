#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PYQMT - 基于miniQMT进行简化的量化交易库
"""
import os
import sys
import time
import random
import datetime
import pandas as pd
import logging as log

# 添加打包的xtquant库到系统路径
def add_xtquant_path():
    """
    将当前文件所在目录下的 'libs' 文件夹添加到系统路径中。
    这允许程序找到并导入 'xtquant' 库，即使它没有被全局安装。
    """
    try:
        lib_path = os.path.join(os.path.dirname(__file__), 'libs')
        if os.path.exists(lib_path) and lib_path not in sys.path:
            sys.path.insert(0, lib_path)
            print(f"已添加库路径: {lib_path}")
    except Exception as e:
        print(f"添加库路径时出错: {str(e)}")

add_xtquant_path()

try:
    from xtquant import xttrader, xtdata, xtconstant
    from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback
    from xtquant.xttype import StockAccount
    xtdata.enable_hello = False
except ImportError:
    log.warning("警告: 无法导入xtquant模块。请确保已正确配置国金QMT环境。")
    log.info("建议: 检查QMT路径是否正确，并重启QMT终端后重试。")
    raise

# 配置日志
log.basicConfig(
    level='INFO',
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class qmtcb(XtQuantTraderCallback):
    pass

# 定义管理类
class pyqmt:
    def __init__(self, path: str, acc: str, log_level: str = 'INFO'):
        """
        初始化 pyqmt 交易管理类。

        参数:
            path (str): miniQMT 交易终端的安装路径。
            acc (str): 资金账户，用于连接和订阅交易账户。
        """
        self.path = path
        self.acc = acc
        self.log_level = log_level
        # 设置日志
        self._setup_logging(log_level)
        """可选级别 - CRITICAL （50）
        - ERROR （40）
        - WARNING （30）
        - INFO （20）
        - DEBUG （10）
        - NOTSET （0）
        """

        self._print_author_declaration()

        self.trade_rules = {
            '689': {'name': '科创板', 'min': 200, 'step': 1, 'slippage': 0.01, 'unit': '股'},
            '688': {'name': '科创板', 'min': 200, 'step': 1, 'slippage': 0.01, 'unit': '股'},
            '300': {'name': '创业板', 'min': 100, 'step': 100, 'slippage': 0.01, 'unit': '股'},
            '60': {'name': '沪市主板', 'min': 100, 'step': 100, 'slippage': 0.01, 'unit': '股'},
            '00': {'name': '深市主板', 'min': 100, 'step': 100, 'slippage': 0.01, 'unit': '股'},
            '50': {'name': '沪市ETF', 'min': 100, 'step': 100, 'slippage': 0.001, 'unit': '份'},
            '51': {'name': '沪市ETF', 'min': 100, 'step': 100, 'slippage': 0.001, 'unit': '份'},
            '52': {'name': '沪市ETF', 'min': 100, 'step': 100, 'slippage': 0.001, 'unit': '份'},
            '53': {'name': '沪市ETF', 'min': 100, 'step': 100, 'slippage': 0.001, 'unit': '份'},
            '56': {'name': '沪市ETF', 'min': 100, 'step': 100, 'slippage': 0.001, 'unit': '份'},
            '58': {'name': '沪市ETF', 'min': 100, 'step': 100, 'slippage': 0.001, 'unit': '份'},
            '15': {'name': '深市ETF', 'min': 100, 'step': 100, 'slippage': 0.001, 'unit': '份'},
            '16': {'name': '深市ETF', 'min': 100, 'step': 100, 'slippage': 0.001, 'unit': '份'},
            '11': {'name': '可转债', 'min': 10, 'step': 10, 'slippage': 0.001, 'unit': '张'},
            '12': {'name': '可转债', 'min': 10, 'step': 10, 'slippage': 0.001, 'unit': '张'},
            '4': {'name': '北京股票', 'min': 100, 'step': 100, 'slippage': 0.01, 'unit': '股'},
            '8': {'name': '北京股票', 'min': 100, 'step': 100, 'slippage': 0.01, 'unit': '股'},
            '9': {'name': '北京股票', 'min': 100, 'step': 100, 'slippage': 0.01, 'unit': '股'},
        }

        self.log.info("正在连接QMT交易终端...")
        self.xt_trader = self.connect()

        # 检查连接状态
        if self.xt_trader is None:
            self.log.error("无法连接到QMT交易终端或订阅账户失败，部分功能将不可用")
            self.log.info("建议检查以下项目:")
            self.log.info("1. miniQMT交易端是否已启动")
            self.log.info("2. 账号是否正确")
            self.log.info("3. miniqmt路径是否正确")
            self.log.info("4. QMT是否具备专业版交易权限")
        else:
            self.log.info("交易终端连接成功，可以正常使用")     

    def _print_author_declaration(self):
        """打印不可修改的作者和版权声明"""
        print("\n" + "=" * 80)
        print("作者: [量化交易汤姆猫] | 微信: QUANT0808")
        print("欢迎联系我：BUG反馈、功能完善、量化交流")
        print("风险提示: 内容仅供参考，不构成投资建议，力求但不保证代码绝对正确，使用风险需自行承担")
        print("=" * 80 + "\n")

    def _setup_logging(self, level='INFO'):
        """
        配置日志系统
        
        参数:
            level (str): 日志级别
        """
        # 清理现有处理器
        for handler in log.root.handlers[:]:
            log.root.removeHandler(handler)
        
        # 设置日志级别
        numeric_level = getattr(log, level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'无效的日志级别: {level}')
        
        # 创建formatter
        formatter = log.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 创建并配置logger
        self.log = log.getLogger('pyqmt')
        self.log.setLevel(numeric_level)
        
        # 如果没有处理器，添加一个控制台处理器
        if not self.log.handlers:
            console_handler = log.StreamHandler()
            console_handler.setLevel(numeric_level)
            console_handler.setFormatter(formatter)
            self.log.addHandler(console_handler)
        
        # 记录日志级别设置
        if numeric_level <= log.INFO:
            self.log.info(f"pyqmt日志级别已设置为: {level}")

    def connect(self) -> XtQuantTrader:
        """
        安全连接QMT交易终端。

        返回:
            XtQuantTrader: 连接成功的 XtQuantTrader 实例，如果连接失败则返回 None。
        """
        """安全连接QMT交易终端 - 错误容错版"""
        try:
            session_id = random.randint(10000000, 99999999)
            xt_trader = XtQuantTrader(self.path, session_id)
            
            # 注册回调
            callback = qmtcb()
            xt_trader.register_callback(callback)
            
            # 启动交易系统
            xt_trader.start()
            
            # 建立连接
            connect_id = xt_trader.connect()
            if connect_id != 0:
                error_msg = f"miniqmt链接失败，错误码: {connect_id}"
                self.log.warning(error_msg)
                # 改为记录错误但不抛出异常
                return None  # 返回None表示连接失败
            
            self.log.info('miniqmt连接成功')
            
            # 订阅账户
            acc_id = StockAccount(self.acc)
            sub_res = xt_trader.subscribe(acc_id)
            if sub_res != 0:
                error_msg = f"账户订阅失败，错误码: {sub_res}"
                self.log.warning(error_msg)
                # 返回None表示订阅失败
                return None
            
            self.log.info('账户订阅成功')
            return xt_trader
            
        except Exception as e:
            self.log.error(f"连接QMT时发生未预期的错误: {str(e)}")
            return None  # 在异常情况下也返回None


    def query_stock_asset(self):
        """
        查询股票资产信息。

        说明:
            使用类中保存的xt_trader实例查询指定账户的资产信息
        返回：
            pd.DataFrame: 包含资产信息的DataFrame
        """
        # 查询股票资产信息
        asset = self.xt_trader.query_stock_asset(StockAccount(self.acc))
        asset_list = []

        # 将资产信息转换为字典格式
        asset_dict = {
            '账户类型': asset.account_type,# type: ignore
            '资金账户': asset.account_id,# type: ignore
            '可用资金': asset.cash,# type: ignore
            '冻结金额': asset.frozen_cash,# type: ignore
            '持仓市值': asset.market_value,# type: ignore
            '总资产': asset.total_asset # type: ignore
        }
        asset_list.append(asset_dict)

        # 将资产信息转换为DataFrame格式并设置索引为资金账户
        asset_df = pd.DataFrame(asset_list)
        asset_df.set_index('资金账户', inplace=True)
        if asset_df.empty:
            self.log.warning("查询到空资产信息")
            return pd.DataFrame()
        # 打印资产信息
        return asset_df

    def get_available_fund(self):
        """
        获取当前账户的可用资金。

        返回:
            float: 可用资金金额
        """
        asset = self.xt_trader.query_stock_asset(StockAccount(self.acc))
        return asset.cash if asset else 0

    def get_available_pos(self, symbol):
        """
        获取指定股票代码的可用持仓数量。

        参数:
            symbol (str): 股票代码。

        返回:
            int: 可用持仓数量，如果查询失败或无持仓则返回 0。
        """
        pos = self.xt_trader.query_stock_position(StockAccount(self.acc), symbol)
        return pos.can_use_volume if pos else 0

    def query_stock_orders(self):
        """
        查询当日委托订单。

        说明:
            使用类中保存的xt_trader实例查询指定账户的股票订单
            如果没有委托订单，则返回空DataFrame。
        """

        # 委托状态映射字典
        order_status_map = {
            49: '待报',
            50: '已报',
            51: '已报待撤',
            52: '部成待撤',
            53: '部撤',
            54: '已撤',
            55: '部成',
            56: '已成',
            57: '废单'
        }

                # 价格类型映射字典
        order_price_type_map = {
            49: '市价',
            50: '限价',
            51: '最优价',
            52: '配股',
            53: '转托',
            54: '申购',
            55: '回购',
            56: '配售',
            57: '指定',
            58: '转股',
            59: '回售',
            60: '股息',
            68: '深圳配售确认',
            69: '配售放弃',
            70: '无冻质押',
            71: '冻结质押',
            72: '无冻解押',
            73: '解冻解押',
            75: '投票',
            77: '预售要约解除',
            78: '基金设红',
            79: '基金申赎',
            80: '跨市转托',
            81: 'ETF申购',
            83: '权证行权',
            84: '对手方最优价格',
            85: '最优五档即时成交剩余转限价',
            86: '本方最优价格',
            87: '即时成交剩余撤销',
            88: '最优五档即时成交剩余撤销',
            89: '全额成交并撤单',
            90: '基金拆合',
            91: '债转股',
            92: '港股通竞价限价',  # 注意：这里有冲突，92也对应"要约收购预售"，根据上下文选择
            93: '港股通增强限价',
            94: '港股通零股限价',
            101: '直接还券',
            107: '担保品划转',
            'j': '增发',
            'w': '定价（全国股转 - 挂牌公司交易 - 协议转让）',
            'x': '成交确认（全国股转 - 挂牌公司交易 - 协议转让）',
            'y': '互报成交确认（全国股转 - 挂牌公司交易 - 协议转让）',
            'z': '限价（用于挂牌公司交易 - 做市转让 - 限价买卖和两网及退市交易-限价买卖）'
        }

        # 查询股票订单
        orders = self.xt_trader.query_stock_orders(StockAccount(self.acc))
        # 检查订单列表是否为空
        if not orders:
            log.warning('没有委托')
            return pd.DataFrame()

        order_list = []
        for order in orders:
            order_dict = {
                '账户编号': order.account_id,
                '账户类型': order.account_type,
                '证券代码': order.stock_code,
                '证券名称': order.instrument_name,
                '订单编号': order.order_id,
                '柜台合同编号': order.order_sysid,
                '报单时间': order.order_time,
                '委托类型': '买入'if order.order_type == 23 else'卖出',
                '委托数量': order.order_volume,
                '报价类型': order_price_type_map.get(order.price_type,f"未知状态{order.price_type}"),
                '委托价格': order.price,
                '成交数量': order.traded_volume,
                '成交均价': order.traded_price,
                '委托状态': order_status_map.get(order.order_status,f'未知状态 {order.order_status}'),
                '委托状态描述': order.status_msg,
                '策略名称': order.strategy_name,
                '委托备注': order.order_remark,
            }
            order_list.append(order_dict)
            

        # 将列表转换为DataFrame
        orders_df = pd.DataFrame(order_list)
        return orders_df

    def query_stock_trades(self):
        """
        查询当日成交记录。

        说明:
            如果没有成交记录，则返回空DataFrame。
        """

        # 查询股票交易记录
        trades = self.xt_trader.query_stock_trades(StockAccount(self.acc))
        # 检查成交列表是否为空
        if not trades:
            log.warning('没有成交记录')
            return pd.DataFrame()

        trade_list = []
        for trade in trades:
            trade_dict = {
                '资金账号': trade.account_id,
                '证券代码': trade.stock_code,
                '证券名称': trade.instrument_name,
                '委托类型': '买入' if trade.order_type == 23 else'卖出',
                '成交时间': trade.traded_time,
                '成交数量': trade.traded_volume,
                '成交金额': trade.traded_amount,
                '成交均价': trade.traded_price,
                '成交编号': trade.traded_id,
                '委托编号':trade.order_id,
                '手续费':trade.commission,
                '策略信息':trade.strategy_name,
                '委托备注':trade.order_remark
                
            }
            trade_list.append(trade_dict)

        # 将列表转换为DataFrame
        trades_df = pd.DataFrame(trade_list)

        # 转换成交时间为本地时间
        trades_df['成交时间'] = pd.to_datetime(trades_df['成交时间'], unit='s', utc=True)
        trades_df['成交时间'] = trades_df['成交时间'].dt.tz_convert('Asia/Shanghai')
        trades_df['成交时间'] = trades_df['成交时间'].dt.strftime("%Y-%m-%d %H:%M:%S")
        trades_df['成交时间'] = pd.to_datetime(trades_df['成交时间'])

        # 设置资金账号为索引
        trades_df.reset_index(inplace=True)
        trades_df.drop(columns=['index'],inplace=True)
        return trades_df

    def query_stock_positions(self):
        """
        查询持仓。

        说明:
            使用类中保存的xt_trader实例查询指定账户的股票持仓
            如果没有持仓，则返回空DataFrame。
        """
        # 查询股票持仓
        positions = self.xt_trader.query_stock_positions(StockAccount(self.acc))
        # 检查持仓列表是否为空
        if not positions:
            log.warning('没有持仓')
            return pd.DataFrame()

        position_list = []
        for position in positions:
            position_dict = {
                '资金账号': position.account_id,
                '证券代码': position.stock_code,
                '证券名称':position.instrument_name,
                '持仓数量': position.volume,
                '可用数量': position.can_use_volume,
                '开仓价': f'{position.open_price:.3f}',
                '市值': f'{position.market_value:.2f}',
                '冻结数量': position.frozen_volume,
                '在途股份': position.on_road_volume,
                '昨夜拥股': position.yesterday_volume,
                '成本价': f'{position.open_price:.3f}',
                '持仓均价':f'{position.avg_price:.3f}',
                '最新价':f'{position.last_price:.3f}',
                '浮动盈亏':f'{position.float_profit:.3f}',
                '持仓盈亏':f'{position.position_profit:.3f}',
                '盈亏比例':f'{position.profit_rate*100:.3f}%',
            }
            position_list.append(position_dict)

        # 将列表转换为DataFrame
        pos_df = pd.DataFrame(position_list)
        return pos_df

    def _get_board(self, symbol):
        """
        根据股票代码判断所属板块。

        参数:
            symbol (str): 股票代码。

        返回:
            str: 股票所属的板块名称（如 '主板', '创业板', '科创板', '北交所', '其他'）。
        """
        prefix = symbol[:3] if symbol.startswith('688') else symbol[:2]
        rule = self.trade_rules.get(prefix)
        if rule:
            name = rule['name']
            if name in ['沪市主板', '深市主板']:
                return '主板'
            elif name == '创业板':
                return '创业板'
            elif name == '科创板':
                return '科创板'
            elif name == '北京股票':
                return '北交所'
            else:
                return '其他'
        return '其他'

    def _check_price_cage(self, symbol, order_side, order_price=None):
        """
        检查委托价格是否符合价格笼子规则。

        参数:
            symbol (str): 股票代码。
            order_side (str): 委托方向 ('buy' 或 'sell')。
            order_price (float, optional): 委托价格。如果为 None，则跳过价格检查。

        返回:
            bool: 如果价格符合规则或不需要进行价格笼子检查，则返回 True；否则返回 False。
        """
        board = self._get_board(symbol)
        if board == '其他':
            self.log.info(f"【价格笼子】{symbol} 不属于价格笼子生效范围，跳过检查。")               
            return True
        now_time = datetime.datetime.now().time()
        start_time = datetime.time(9, 25)
        end_time = datetime.time(14, 57)
        if not (start_time <= now_time <= end_time):
            self.log.info(f"【价格笼子】当前时间 {now_time.strftime('%H:%M:%S')} 不在生效时间 (09:25-14:57) 内，跳过检查。")
            return True
        reference_price = self.get_last_price(symbol)
        if reference_price is None or reference_price <= 0:
            self.log.warning(f"【价格笼子】{symbol} 参考价无效 ({reference_price})，跳过检查。")
            return True
        if board in ['主板', '创业板']:
            if order_side == 'buy':
                upper_limit = max(reference_price * 1.02, reference_price + 0.1)
                if order_price > upper_limit:
                    self.log.warning(f"【价格笼子校验失败】{symbol} 买入委托价 {order_price:.2f} 过高。")
                    return False
            elif order_side == 'sell':
                lower_limit = min(reference_price * 0.98, reference_price - 0.1)
                if order_price < lower_limit:
                    self.log.warning(f"【价格笼子校验失败】{symbol} 卖出委托价 {order_price:.2f} 过低。")
                    return False
        elif board == '北交所':
            if order_side == 'buy':
                upper_limit = max(reference_price * 1.05, reference_price + 0.1)
                if order_price > upper_limit:
                    self.log.warning(f"【价格笼子校验失败】{symbol} 买入委托价 {order_price:.2f} 过高。")
                    return False
            elif order_side == 'sell':
                lower_limit = min(reference_price * 0.95, reference_price - 0.1)
                if order_price < lower_limit:
                    self.log.warning(f"【价格笼子校验失败】{symbol} 卖出委托价 {order_price:.2f} 过低。")
                    return False
        elif board == '科创板':
            if order_side == 'buy':
                upper_limit = round(reference_price * 1.02, 2)
                if order_price > upper_limit:
                    self.log.warning(f"【价格笼子校验失败】{symbol} 买入委托价 {order_price:.2f} 过高。")
                    return False
            elif order_side == 'sell':
                lower_limit = round(reference_price * 0.98, 2)
                if order_price < lower_limit:
                    self.log.warning(f"【价格笼子校验失败】{symbol} 卖出委托价 {order_price:.2f} 过低。")
                    return False
        self.log.info(f"【价格笼子校验通过】{symbol} 委托价 {order_price:.2f} 在允许范围内。")
        return True

    def _calculate_commission(self, symbol, price, volume):
        """
        计算交易佣金。

        参数:
            symbol (str): 股票代码。
            price (float): 成交价格。
            volume (int): 成交数量。

        返回:
            float: 计算出的佣金，最低为5元。
        """
        amount = price * volume
        commission = amount * 0.0002
        return max(commission, 5)

    def get_last_price(self, symbol):
        """
        获取指定股票的最新价格。

        参数:
            symbol (str): 股票代码。

        返回:
            float: 股票的最新价格，如果获取失败则返回 None。
        """
        try:
            data = xtdata.get_full_tick([symbol])
            last_price = data[symbol]['lastPrice']
            return last_price
        except Exception as e:
            self.log.warning(f"【行情获取失败】{symbol} 错误:{str(e)}")
            return None

    def _get_security_rule(self, symbol):
        """
        根据股票代码获取对应的交易规则。

        参数:
            symbol (str): 股票代码。

        返回:
            dict: 包含股票交易规则的字典，如果未找到则返回默认规则。
        """
        code = symbol.split('.')[0] if '.' in symbol else symbol
        for prefix in self.trade_rules:
            if code.startswith(prefix):
                return self.trade_rules[prefix]
        return {'name': '默认', 'min': 100, 'step': 100, 'slippage': 0.01, 'unit': '股'}

    def _adjust_volume(self, symbol, volume):
        """
        根据交易规则调整委托数量，使其符合最小交易单位和步长。

        参数:
            symbol (str): 股票代码。
            volume (int): 原始委托数量。

        返回:
            int: 调整后的委托数量，如果该品种禁止交易则返回 0。
        """
        rule = self._get_security_rule(symbol)
        if rule['min'] == 0:
            self.log.warning(f"【交易禁止】{symbol} 北交所品种不支持交易")
            return 0
        adjusted = max(rule['min'], volume) // rule['step'] * rule['step']
        if adjusted != volume:
            self.log.info(f"【数量调整】{symbol} {volume}{rule['unit']} -> {adjusted}{rule['unit']}")
        return int(adjusted)

    def buy(self, symbol, volume, price=None, strategy_name='', order_remark=''):
        """
        买入股票。

        参数:
            symbol (str): 股票代码。
            volume (int): 委托数量。
            price (float, optional): 委托价格。如果为 None，则以最新价买入。
            strategy_name (str, optional): 策略名称。
            order_remark (str, optional): 订单备注。
            retry_count (int, optional): 重试次数，目前未使用。

        返回:
            int: 委托订单ID，如果下单失败则返回 -1。
        """
        try:
            # 规则调整委托数量
            adj_volume = self._adjust_volume(symbol, volume)
            if adj_volume <= 0:
                return -1
            if not symbol or adj_volume <= 0:
                self.log.warning("【参数错误】证券代码或数量无效,未提交委托")
                return -1
                
            # 获取规则和行情
            rule = self._get_security_rule(symbol)
            last_price = self.get_last_price(symbol)
            if last_price is None or last_price <= 0:
                self.log.warning(f"【行情无效】{symbol} 获取最新价失败，未提交委托")
                return -1
            
            # 资金检查
            # 使用参考价格计算所需资金（对于市价单使用含滑点的预估价格）
            reference_price = last_price * (1 + rule['slippage']) if price is None else price
            required_fund = reference_price * adj_volume
            commission = self._calculate_commission(symbol, reference_price, adj_volume)
            available_fund = self.get_available_fund()
            if available_fund < required_fund + commission:
                self.log.warning(f"【资金不足】可用资金:{available_fund:.2f}元，所需资金:{required_fund+commission:.2f}元(含手续费{commission:.2f}元)，未提交委托")
                return -1
            
            # 正确处理市价/限价委托
            if price is None:
                # 市价委托
                final_price = 0.0
                price_type = xtconstant.LATEST_PRICE
            else:
                # 限价委托
                final_price = round(float(price), 3)
                price_type = xtconstant.FIX_PRICE
            
            # 计算参考价格（仅限市价委托，用于日志记录）
            if price is None and rule['slippage'] != 0:
                reference_price = round(last_price * (1 + rule['slippage']), 3)
                self.log.info(f"【最新价买入】{symbol} 委托参考价:{reference_price}")
            else:
                reference_price = final_price
            
            strategy_name = str(strategy_name) if pd.notna(strategy_name) else ''
            order_remark = str(order_remark) if pd.notna(order_remark) else ''
            
            # 尝试下单
            order_id = self.xt_trader.order_stock(
                StockAccount(self.acc), symbol, xtconstant.STOCK_BUY, adj_volume,
                price_type, final_price, strategy_name, order_remark
            )
       
            # # 重写属性设置方法
            # print_author_declaration = property(
            #     lambda self: self._print_author_declaration_impl,
            #     lambda self, value: self._disable_declaration_modification()
            # )
                    
            if order_id > 0:
                # 使用不同日志描述市价/限价
                if price is None:
                    self.log.info(f"【最新价买入委托成功】{symbol} 参考价:{reference_price} 数量:{adj_volume}{rule['unit']} 委托编号:{order_id}")
                else:
                    self.log.info(f"【限价买入委托成功】{symbol} 价格:{final_price} 数量:{adj_volume}{rule['unit']} 委托编号:{order_id}")
                return order_id
            else:
                self.log.warning(f"【买入委托失败】{symbol} 错误码:{order_id}")
                return order_id
        except ConnectionError as e:
            self.log.warning(f"【网络错误】下单时发生网络连接问题: {str(e)}")
            return -1
        except ValueError as e:
            self.log.warning(f"【参数错误】下单时发生参数错误: {str(e)}")
            return -1
        except AttributeError as e:
            self.log.warning(f"【API错误】下单时发生属性错误，可能由于 QMT 返回数据异常: {str(e)}")
            return -1
        except Exception as e:
            self.log.warning(f"【下单异常】买入 {symbol} 时发生未知错误: {str(e)}")
            return -1  

    def sell(self, symbol, volume, price=None, strategy_name='', order_remark=''):
        """
        卖出股票。

        参数:
            symbol (str): 股票代码。
            volume (int): 委托数量。
            price (float, optional): 委托价格。如果为 None，则以最新价卖出。
            strategy_name (str, optional): 策略名称。
            order_remark (str, optional): 订单备注。
            retry_count (int, optional): 重试次数，目前未使用。

        返回:
            int: 委托订单ID，如果下单失败则返回 -1。
        """
        try:
            # 检查参数有效性
            if volume <= 0 or not symbol:
                self.log.warning("【参数错误】证券代码或数量无效，未提交委托")
                return -1
                
            # 获取规则和行情
            rule = self._get_security_rule(symbol)
            last_price = self.get_last_price(symbol)
            if last_price is None or last_price <= 0:
                self.log.warning(f"【行情无效】{symbol} 获取最新价失败，未提交委托")
                return -1
                
            # 检查可用持仓
            available_pos = self.get_available_pos(symbol)
            if available_pos <= 0:
                self.log.warning(f"【卖出失败】 {symbol} 可用股数为0，未提交委托")
                return -1
            
            # 调整委托数量（如果超过可用数量）
            original_volume = volume
            if volume > available_pos:
                volume = available_pos
                self.log.info(f"【委托数量调整】{symbol} | 委托数量超过可用数量，已调整为可用数量 | {original_volume} --> {volume}")
            
            # 向下取整（适配交易规则）
            adj_volume = self._adjust_volume(symbol, volume)
            if adj_volume <= 0:
                return -1
            if adj_volume != volume:
                self.log.info(f"【数量调整】{symbol} 调整后数量:{adj_volume}{rule['unit']}")
            
            # 修复：正确处理市价/限价委托
            if price is None:
                # 市价委托
                final_price = 0.0
                price_type = xtconstant.LATEST_PRICE
            else:
                # 限价委托
                final_price = round(float(price), 3)
                price_type = xtconstant.FIX_PRICE
            
            # 计算参考价格（仅限市价委托，用于日志记录）
            if price is None and rule['slippage'] != 0:
                reference_price = round(last_price * (1 - rule['slippage']), 3)
                self.log.info(f"【最新价卖出参考价】{symbol} 计算参考价:{reference_price}")
            else:
                reference_price = final_price
            
            strategy_name = str(strategy_name) if pd.notna(strategy_name) else ''
            order_remark = str(order_remark) if pd.notna(order_remark) else ''
            
            # 尝试下单
            order_id = self.xt_trader.order_stock(
                StockAccount(self.acc), symbol, xtconstant.STOCK_SELL, adj_volume,
                price_type, final_price, strategy_name, order_remark
            )
            
            if order_id > 0:
                # 使用不同日志描述市价/限价
                if price is None:
                    self.log.info(f"【最新价卖出委托成功】{symbol} 参考价:{reference_price} 数量:{adj_volume}{rule['unit']} 委托编号:{order_id}")
                else:
                    self.log.info(f"【限价卖出委托成功】{symbol} 价格:{final_price} 数量:{adj_volume}{rule['unit']} 委托编号:{order_id}")
                    
                return order_id
            else:
                self.log.warning(f"【卖出委托失败】{symbol} 错误码:{order_id}")
                return order_id
        except ConnectionError as e:
            self.log.warning(f"【网络错误】下单时发生网络连接问题: {str(e)}")
            return -1
        except ValueError as e:
            self.log.warning(f"【参数错误】下单时发生参数错误: {str(e)}")
            return -1
        except AttributeError as e:
            self.log.warning(f"【API错误】下单时发生属性错误，可能由于 QMT 返回数据异常: {str(e)}")
            return -1
        except Exception as e:
            self.log.warning(f"【下单异常】卖出 {symbol} 时发生未知错误: {str(e)}")
            return -1
    
        
    def cancel_order(self, order_id):
        """
        根据order_id撤单

        参数:
            order_id (int): 要撤销的订单ID。

        返回:
            int: True表示撤单成功，False表示撤单失败。
        """
        try:
            result = self.xt_trader.cancel_order_stock(StockAccount(self.acc), order_id)
            if result == 0:
                self.log.info(f"【撤单成功】订单 {order_id}")
                return True
            else:
                self.log.warning(f"【撤单失败】订单 {order_id} 错误码: {result}")
                return False
        except Exception as e:
            self.log.warning(f"【撤单异常】订单 {order_id} 错误: {str(e)}")
            return False

        
    def is_trading_time(self):
        """
        判断当前时间是否在A股交易时间内（包括集合竞价和连续竞价）。

        返回:
            bool: 如果是交易时间则返回 True，否则返回 False。
        """
        # 设置集合竞价时间

        # 获取当前时间
        now = datetime.datetime.now()
        weekday = now.weekday()  # 0-6，0 为星期一

        # 检查是否为交易日
        if weekday > 4:
            self.log.info(f'当前时间{now}不在A股交易时间内')
            return False

        now_time = now.time()
        start_time = datetime.time(9, 15)
        end_time = datetime.time(15, 0)
        if start_time <= now_time <= end_time:
            self.log.info(f'当前时间{now}在A股交易时间内')
            return True

        self.log.info(f'当前时间{now}不在A股交易时间内')
        return False
    
    def query_stock_is_limit_down(self, symbol):
        """
        检查标的的涨跌幅情况，判断是否涨停或跌停。
        参数:
            symbol (str): 股票代码。

        返回:
            str: 如果股票涨停则返回 '涨停'，如果股票跌停则返回 '跌停'，否则返回 '正常'。
        """
        try:
            data = xtdata.get_instrument_detail(symbol)
        except Exception as e:
            self.log.warning(f'获取标的基础信息失败：{e}')
            return None

        up_stop_price = data['UpStopPrice']
        down_stop_price = data['DownStopPrice']
        try:
            lastprice = xtdata.get_full_tick([symbol])
            lastprice = lastprice[symbol]['lastPrice']
        except Exception as e:
            self.log.warning(f'获取最新价失败：{e}')
            return None
        
        if lastprice >= up_stop_price:
            self.log.info(f'标的{symbol}涨停')
            return '涨停'
        elif lastprice <= down_stop_price:
            self.log.info(f'标的{symbol}跌停')
            return  '跌停'          
        else:
            self.log.info(f'标的{symbol}正常')
            return  '正常'

    def cancel_all_orders(self):
        """
        撤销当前账户所有未成交或部分成交的订单。
        返回:
            bool: 没有需要撤销的订单，则返回True。
            bool: 有需要撤销的订单，但有订单撤单失败，则返回False。
        """
        self.log.info("开始撤销所有未成交或部分成交的订单...")
        cancel_orders = self.xt_trader.query_stock_orders(StockAccount(self.acc),True)
        if not cancel_orders:
            self.log.info("当前没有委托订单，无需撤单")
            return True
        order_list = []
        for order in cancel_orders:
            order_dict = {
                '资金账号': order.account_id,
                '证券代码': order.stock_code,
                '订单编号': order.order_id,
                '柜台合同编号': order.order_sysid,
                '报单时间': order.order_time,
                '委托类型': order.order_type,
                '委托数量': order.order_volume,
                '报价类型': order.price_type,
                '委托价格': order.price,
                '成交数量': order.traded_volume,
                '成交均价': order.traded_price,
                '委托状态': order.order_status,
                '委托状态描述': order.status_msg,
                '策略名称': order.strategy_name,
                '委托备注': order.order_remark,
            }
            order_list.append(order_dict)
        orders_df = pd.DataFrame(order_list) #可以撤单的委托

        all_success = True
        for _,row in orders_df.iterrows():
            order_id = row['订单编号']
            stock_code = row['证券代码']
            try:
                cancel_res = self.xt_trader.cancel_order_stock(StockAccount(self.acc),order_id)
                if cancel_res == 0:
                    self.log.info(f"{stock_code} | {order_id} | 撤单成功")
                else:
                    self.log.warning(f"{stock_code} | {order_id} | 撤单失败")
                    all_success = False
            except Exception as e:
                self.log.warning(f'撤单操作失败，{str(e)}')
                all_success = False

        return all_success

    def cancel_buy_orders(self):
        """
        撤销所有买入委托订单。

        返回：
            全部撤单成功或无需撤单：返回True
            有需要撤单的订单，但有订单撤单失败：返回False
        """
        self.log.info("开始撤销所有买入委托订单...")
        try:
            orders = self.query_stock_orders()
            if orders.empty:
                self.log.info("没有找到任何委托订单，无需撤单")
                return True

            buy_pending_orders = orders[
                (orders['委托状态'].isin(['已报', '部成', '部撤'])) &
                (orders['委托类型'] == '买入')
            ]

            if buy_pending_orders.empty:
                self.log.info("没有找到'已报', '部成', '部撤'的买入订单，无需撤单")
                return True

            all_success = True
            for _, order in buy_pending_orders.iterrows():
                order_id = order['订单编号']
                symbol = order['证券代码']
                res = self.cancel_order(order_id)
                if res:
                    self.log.info(f"{symbol} | {order_id} | 撤单成功")
                else:
                    self.log.warning(f"{symbol} | {order_id} | 撤单失败")
                    all_success = False
        except Exception as e:
            self.log.error(f"撤销所有买入委托订单时发生错误: {e}")
            all_success = False
        return all_success

    def cancel_sell_orders(self):
        """
        撤销所有卖出委托订单。
        返回：
            撤单成功或无需撤单：返回True
            撤单失败，返回False
        """
        self.log.info("开始撤销所有卖出委托订单...")
        try:
            orders = self.query_stock_orders()
            if orders.empty:
                self.log.info("没有找到任何委托订单，无需撤单")
                return True

            sell_pending_orders = orders[
                (orders['委托状态'].isin(['已报', '部成', '部撤'])) &
                (orders['委托类型'] == '卖出')
            ]

            if sell_pending_orders.empty:
                self.log.info("没有找到'已报', '部成', '部撤'的卖出订单，无需撤单")
                return True

            all_success = True
            for _, order in sell_pending_orders.iterrows():
                order_id = order['订单编号']
                symbol = order['证券代码']
                res = self.cancel_order(order_id)
                if res:
                    self.log.info(f"{symbol} | {order_id} | 撤单成功")
                else:
                    self.log.warning(f"{symbol} | {order_id} | 撤单失败")
                    all_success = False
        except Exception as e:
            self.log.error(f"撤销所有卖出委托订单时发生错误: {e}")
            all_success = False
        return all_success

    def cancel_symbol_orders(self, symbol):
        """
        撤销指定股票代码的所有未成交或部分成交的订单。
        参数:
            symbol (str): 股票代码。
        返回：
            全部撤单成功或无需撤单：返回True
            有需要撤单但撤单失败，返回False
        """
        self.log.info(f"开始撤销股票 {symbol} 的所有委托订单...")
        try:
            orders = self.query_stock_orders()
            if orders.empty:
                self.log.info("没有找到任何委托订单，无需撤单")
                return True

            symbol_pending_orders = orders[
                (orders['委托状态'].isin(['已报', '部成', '部撤'])) &
                (orders['证券代码'] == symbol)
            ]

            if symbol_pending_orders.empty:
                self.log.info(f"没有找到股票 {symbol} 的'已报', '部成', '部撤'的订单，无需撤单")
                return True  
            
            all_success = True
            for _, order in symbol_pending_orders.iterrows():
                order_id = order['订单编号']
                res = self.cancel_order(order_id)
                if res:
                    self.log.info(f"{symbol} | {order_id} | 撤单成功")
                else:
                    self.log.warning(f"{symbol} | {order_id} | 撤单失败")
                    all_success = False
        except Exception as e:
            self.log.error(f"撤销股票 {symbol} 的委托订单时发生错误: {e}")
            all_success = False
        
        return all_success

    def all_sell(self):
        """
        卖出所有持仓股票。
        返回：
            卖出成功或无需卖出：返回True
            卖出失败，返回False
        """
        self.log.info("开始卖出所有持仓股票...")
        try:
            positions = self.query_stock_positions()
            if positions.empty:
                self.log.info("没有持仓股票，无需卖出。")
                return True

            for index, pos in positions.iterrows():
                symbol = pos['证券代码']
                volume = pos['可用数量']
                if volume > 0:
                    self.log.info(f"正在卖出股票: {symbol}, 数量: {volume}")
                    self.sell(symbol, volume, price=None)  # 使用 price=None 表示市价委托
                    time.sleep(0.1)  # 避免请求过于频繁
                else:
                    self.log.info(f"股票 {symbol} 可用数量为0，跳过卖出。")
            self.log.info("所有持仓股票卖出操作完成。")
            return True
        except Exception as e:
            self.log.error(f"卖出所有持仓股票时发生错误: {e}")
            return False
    
    # =============================

    def get_upl(self, symbol):
        """
        获取指定股票的涨停价。

        参数:
            symbol (str): 股票代码。

        返回:
            float: 股票的涨停价，如果获取失败则返回 None。
        """

        try:
            data = xtdata.get_instrument_detail(symbol)
            return data['UpStopPrice']
        except Exception as e:
            log.error(f"获取 {symbol} 涨停价失败: {e}")
            return None

    def get_dnl(self, symbol):
        """
        获取指定股票的跌停价。

        参数:
            symbol (str): 股票代码。

        返回:
            float: 股票的跌停价，如果获取失败则返回 None。
        """
  
        try:
            data = xtdata.get_instrument_detail(symbol)
            return data['DownStopPrice']
        except Exception as e:
            self.log.error(f"获取 {symbol} 跌停价失败: {e}")
            return None
            

    def get_full_tick(self, stock_list:list):
        """
        获取指定标的的全推tick数据

        参数:
            symbol (str): 股票代码列表，例如 ['000001.SZ', '600000.SH']

        返回:
            float: 股票的最新价格，如果获取失败则返回 None。
        """
        try:
            data = xtdata.get_full_tick(stock_list)
            return data
        except Exception as e:
            self.log.error(f"获取 {stock_list} 最新价格失败: {e}")
            return None
         
    def get_market_data_ex(self,  stock_code: str = None,start_time: str = '', end_time: str = '',  period: str = '1d', count: int = -1, field_list=None,dividend_type: str = 'none', fill_data: bool = True):
        if field_list is None:
            field_list = []
        if not stock_code:
            self.log.error("获取行情数据失败: stock_code 不能为空")
            return None

        try:
            xtdata.subscribe_quote(stock_code=stock_code, period=period, start_time=start_time, end_time=end_time, count=count)
            data = xtdata.get_market_data_ex(field_list=field_list,stock_list=[stock_code], period=period, start_time=start_time, end_time=end_time, count=count, dividend_type = dividend_type, fill_data = fill_data)
            return data
        except Exception as e:
            self.log.error(f"获取 {stock_code} 行情数据失败: {e}")
            return None


