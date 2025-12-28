#!/usr/bin/python
# -*- coding: utf8 -*-
#
# Create on: 20240126
#    Author: fasiondog

import sys

if sys.version_info[1] == 10:
    from .pycheck310 import *
elif sys.version_info[1] == 11:
    from .pycheck311 import *
elif sys.version_info[1] == 12:
    from .pycheck312 import *
elif sys.version_info[1] == 13:
    from .pycheck313 import *
elif sys.version_info[1] == 14:
    from .pycheck314 import *
else:
    from .pycheck import *

can_use_pyarrow = support_arrow()

if can_use_pyarrow:
    try:
        import pyarrow as pa
    except Exception as e:
        print("依赖 pyarrow >= 19.0 库, 请检查pyarrow安装")
        raise e

    try:
        import hikyuu as _hku
    except Exception as e:
        print("依赖 hikyuu 库, 请检查hikyuu安装")
        raise e

    try:
        if sys.version_info[1] == 10:
            from .pyextra310 import *
        elif sys.version_info[1] == 11:
            from .pyextra311 import *
        elif sys.version_info[1] == 12:
            from .pyextra312 import *
        elif sys.version_info[1] == 13:
            from .pyextra313 import *
        elif sys.version_info[1] == 14:
            from .pyextra314 import *
        else:
            from .pyextra import *
    except Exception as e:
        print("缺失pyextra模块, 仅支持Python3.10以上版本")
        raise e

    _hku.KData.to_pyarrow = lambda data: kdata_to_pa(data)
    _hku.Indicator.to_pyarrow = lambda data: indicator_to_pa(data)
    _hku.Indicator.value_to_pyarrow = lambda data: indicator_value_to_pa(data)
    _hku.DatetimeList.to_pyarrow = lambda data: dates_to_pa(data)
    _hku.TimeLineList.to_pyarrow = lambda data: timeline_to_pa(data)
    _hku.TransList.to_pyarrow = lambda data: translist_to_pa(data)
    _hku.StockWeightList.to_pyarrow = lambda data: weights_to_pa(data)
    _hku.KRecordList.to_pyarrow = lambda data: krecords_to_pa(data)
    _hku.TradeRecordList.to_pyarrow = lambda self: trades_to_pa(self)
    _hku.PositionRecordList.to_pyarrow = lambda self: positions_to_pa(self)

    del _hku

else:
    print("当前Python版本不支持pyarrow, 无法使用扩展功能")
