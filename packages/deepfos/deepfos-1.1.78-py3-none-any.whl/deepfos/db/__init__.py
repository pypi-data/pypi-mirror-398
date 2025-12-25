from typing import TYPE_CHECKING

from deepfos.lazy import lazify

if TYPE_CHECKING:  # pragma: no cover
    from .mysql import MySQLClient, AsyncMySQLClient
    from .clickhouse import ClickHouseClient, AsyncClickHouseClient
    from .oracle import OracleClient, AsyncOracleClient, OracleDFSQLConvertor
    from .sqlserver import SQLServerClient, AsyncSQLServerClient
    from .kingbase import KingBaseClient, AsyncKingBaseClient
    from .gauss import GaussClient, AsyncGaussClient
    from .dameng import DaMengClient, AsyncDaMengClient
    from .postgresql import PostgreSQLClient, AsyncPostgreSQLClient
    from .deepengine import DeepEngineClient, AsyncDeepEngineClient
    from .deepmodel import DeepModelClient, AsyncDeepModelClient
    from .deepmodel_kingbase import DeepModelKingBaseClient, AsyncDeepModelKingBaseClient


lazify(
    {
        'deepfos.db.mysql': ('MySQLClient', 'AsyncMySQLClient'),
        'deepfos.db.clickhouse': ('ClickHouseClient', 'AsyncClickHouseClient'),
        'deepfos.db.oracle': (
            'OracleClient', 'AsyncOracleClient', 'OracleDFSQLConvertor'
        ),
        'deepfos.db.sqlserver': ('SQLServerClient', 'AsyncSQLServerClient'),
        'deepfos.db.kingbase': ('KingBaseClient', 'AsyncKingBaseClient'),
        'deepfos.db.gauss': ('GaussClient', 'AsyncGaussClient'),
        'deepfos.db.dameng': ('DaMengClient', 'AsyncDaMengClient'),
        'deepfos.db.postgresql': ('PostgreSQLClient', 'AsyncPostgreSQLClient'),
        'deepfos.db.deepengine': ('DeepEngineClient', 'AsyncDeepEngineClient'),
        'deepfos.db.deepmodel': ('DeepModelClient', 'AsyncDeepModelClient'),
        'deepfos.db.deepmodel_kingbase': ('DeepModelKingBaseClient', 'AsyncDeepModelKingBaseClient'),
    },
    globals()
)
