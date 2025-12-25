"""
protobuf生成的Python代码包
"""

# 按顺序导入所有模块，确保依赖关系正确
# 必须先导入 common_pb2，因为其他模块依赖它
from . import common_pb2
from . import common_pb2_grpc
from . import market_data_pb2
from . import market_data_pb2_grpc
from . import trading_pb2
from . import trading_pb2_grpc

# 尝试导入auth相关代码（如果已生成）
try:
    from . import auth_pb2
    from . import auth_pb2_grpc
    __all__ = [
        'common_pb2',
        'common_pb2_grpc',
        'market_data_pb2',
        'market_data_pb2_grpc',
        'trading_pb2',
        'trading_pb2_grpc',
        'auth_pb2',
        'auth_pb2_grpc',
    ]
except ImportError:
    __all__ = [
        'common_pb2',
        'common_pb2_grpc',
        'market_data_pb2',
        'market_data_pb2_grpc',
        'trading_pb2',
        'trading_pb2_grpc',
    ]
