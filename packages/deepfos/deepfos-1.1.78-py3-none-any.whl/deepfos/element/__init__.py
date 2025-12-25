from typing import TYPE_CHECKING

from deepfos.lazy import lazify

if TYPE_CHECKING:  # pragma: no cover
    from .accounting import (
        AccountingEngines, AsyncAccountingEngines, 
        BillEngines, AsyncBillEngines, CallbackInfo
    )
    from .apvlprocess import AsyncApprovalProcess, ApprovalProcess
    from .bizmodel import BusinessModel, AsyncBusinessModel, CopyConfig
    from .datatable import (
        Datatable, AsyncDataTableMySQL, DataTableMySQL,
        AsyncDataTableClickHouse, DataTableClickHouse,
        AsyncDataTableOracle, DataTableOracle,
        AsyncDataTableSQLServer, DataTableSQLServer,
        AsyncDataTableKingBase, DataTableKingBase,
        AsyncDataTableGauss, DataTableGauss,
        AsyncDataTableDaMeng, DataTableDaMeng,
        AsyncDataTablePostgreSQL, DataTablePostgreSQL,
        AsyncDataTableDeepEngine, DataTableDeepEngine,
        AsyncDataTableDeepModel, DataTableDeepModel,
        AsyncDataTableDeepModelKingBase, DataTableDeepModelKingBase,
    )
    from .dimension import AsyncDimension, Dimension
    from .fact_table import AsyncFactTable, FactTable
    from .finmodel import AsyncFinancialCube, FinancialCube
    from .journal_template import (
        AsyncJournalTemplate, JournalTemplate, FullPostingParameter
    )
    from .rolestrategy import AsyncRoleStrategy, RoleStrategy
    from .smartlist import AsyncSmartList, SmartList
    from .variable import AsyncVariable, Variable
    from .workflow import AsyncWorkFlow, WorkFlow
    from .journal import AsyncJournalModel, JournalModel
    from .deepmodel import AsyncDeepModel, DeepModel
    from .deepconnector import AsyncDeepConnector, DeepConnector
    from .deep_pipeline import AsyncDeepPipeline, DeepPipeline


lazify(
    {
        'deepfos.element.finmodel': (
            'AsyncFinancialCube', 'FinancialCube'
        ),
        'deepfos.element.accounting': (
            'AccountingEngines', 'AsyncAccountingEngines', 
            'BillEngines', 'AsyncBillEngines', 'CallbackInfo'
        ),
        'deepfos.element.apvlprocess': (
            'AsyncApprovalProcess', 'ApprovalProcess'
        ),
        'deepfos.element.bizmodel': (
            'BusinessModel', 'AsyncBusinessModel', 'CopyConfig'
        ),
        'deepfos.element.datatable': (
            'Datatable',
            'AsyncDataTableMySQL', 'DataTableMySQL',
            'AsyncDataTableClickHouse', 'DataTableClickHouse',
            'AsyncDataTableOracle', 'DataTableOracle',
            'AsyncDataTableSQLServer', 'DataTableSQLServer',
            'AsyncDataTableKingBase', 'DataTableKingBase',
            'AsyncDataTableGauss', 'DataTableGauss',
            'AsyncDataTableDaMeng', 'DataTableDaMeng',
            'AsyncDataTablePostgreSQL', 'DataTablePostgreSQL',
            'AsyncDataTableDeepEngine', 'DataTableDeepEngine',
            'AsyncDataTableDeepModel', 'DataTableDeepModel',
            'AsyncDataTableDeepModelKingBase', 'DataTableDeepModelKingBase',
        ),
        'deepfos.element.dimension': ('AsyncDimension', 'Dimension'),
        'deepfos.element.fact_table': ('AsyncFactTable', 'FactTable'),
        'deepfos.element.journal_template': (
            'AsyncJournalTemplate', 'JournalTemplate', 'FullPostingParameter'
        ),
        'deepfos.element.rolestrategy': ('AsyncRoleStrategy', 'RoleStrategy'),
        'deepfos.element.smartlist': ('AsyncSmartList', 'SmartList'),
        'deepfos.element.variable': ('AsyncVariable', 'Variable'),
        'deepfos.element.workflow': ('AsyncWorkFlow', 'WorkFlow'),
        'deepfos.element.reconciliation': (
            'AsyncReconciliationEngine', 'AsyncReconciliationMsEngine',
            'ReconciliationEngine', 'ReconciliationMsEngine',
        ),
        'deepfos.element.journal': ('AsyncJournalModel', 'JournalModel'),
        'deepfos.element.deepmodel': ('AsyncDeepModel', 'DeepModel'),
        'deepfos.element.deepconnector': ('AsyncDeepConnector', 'DeepConnector'),
        'deepfos.element.deep_pipeline': ('AsyncDeepPipeline', 'DeepPipeline'),
    },
    globals()
)
