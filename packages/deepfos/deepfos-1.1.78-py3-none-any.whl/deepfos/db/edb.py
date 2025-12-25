import asyncio
from typing import Dict

from edgedb import AsyncIOClient, errors, enums, describe, abstract
from edgedb.abstract import (
    DescribeContext, QueryContext, QueryWithArgs,
    _query_opts    # noqa
)
from edgedb.asyncio_client import (
    AsyncIOConnection, AsyncIOIteration,    # noqa
    AsyncIORetry
)

from deepfos import OPTION

__all__ = ['create_async_client']


def collect_output_frame(ele_desc: describe.AnyType):
    if isinstance(ele_desc, describe.ObjectType):
        return {
            (field, element.is_implicit == 0): collect_output_frame(element.type)
            for field, element in ele_desc.elements.items()
        }
    if isinstance(ele_desc, describe.ArrayType):
        return collect_output_frame(ele_desc.element_type)
    if isinstance(ele_desc, describe.NamedTupleType):
        return {
            field: collect_output_frame(ele_type)
            for field, ele_type in ele_desc.element_types.items()
        }
    if isinstance(ele_desc, describe.TupleType):
        return [collect_output_frame(ele_type) for ele_type in ele_desc.element_types]
    return ele_desc.name


def normalize_kw(query: str, kw: Dict):
    from deepfos.lib.edb_lexer import EdgeQLLexer
    lexer = EdgeQLLexer()
    lexer.setinputstr(query)
    expected_args = list(
        map(
            lambda t: t.text[1::],
            filter(lambda x: x.type == 'ARGUMENT', lexer.lex())
        )
    )
    result = {}
    for arg_name in expected_args:
        if arg_name in kw:
            result[arg_name] = kw[arg_name]
        else:
            result.setdefault(arg_name)
    return result


class _AsyncEdgeDBConnection(AsyncIOConnection):
    async def raw_query(self, query_context, capabilities=enums.Capability.NONE):
        if self.is_closed():
            await self.connect()

        reconnect = False
        i = 0
        query = query_context.query.query
        kwargs = query_context.query.kwargs
        query_context = query_context._replace(
            query=query_context.query._replace(
                kwargs=normalize_kw(query, kwargs)
            )
        )
        args = dict(
            query=query_context.query.query,
            args=query_context.query.args,
            kwargs=query_context.query.kwargs,
            reg=query_context.cache.codecs_registry,
            qc=query_context.cache.query_cache,
            output_format=query_context.query_options.output_format,
            expect_one=query_context.query_options.expect_one,
            required_one=query_context.query_options.required_one,
            allow_capabilities=capabilities,
        )
        if query_context.state is not None:
            args["state"] = query_context.state.as_dict()
        while True:
            i += 1
            try:
                if reconnect:
                    await self.connect(single_attempt=True)
                result = await self._protocol.query(**args)
                codecs = query_context.cache.query_cache.get(
                    args['query'],
                    args['output_format'],
                    # implicit_limit
                    0,
                    # inline_typenames
                    False,
                    # inline_typeids
                    False,
                    args['expect_one'],
                )
                if codecs is not None:
                    out_dc = codecs[2]
                    frame_desc = collect_output_frame(out_dc.make_type(
                        DescribeContext(
                            query='',
                            state=query_context.state,
                            inject_type_names=False
                        )
                    ))
                else:
                    frame_desc = None
                return frame_desc, result
            except errors.EdgeDBError as e:
                if query_context.retry_options is None:
                    raise
                if not e.has_tag(errors.SHOULD_RETRY):
                    raise e
                if capabilities is None:
                    cache_item = query_context.cache.query_cache.get(
                        query_context.query.query,
                        query_context.query_options.output_format,
                        implicit_limit=0,
                        inline_typenames=False,
                        inline_typeids=False,
                        expect_one=query_context.query_options.expect_one,
                    )
                    if cache_item is not None:
                        _, _, _, capabilities = cache_item
                # A query is read-only if it has no capabilities i.e.
                # capabilities == 0. Read-only queries are safe to retry.
                # Explicit transaction conflicts as well.
                if (
                    capabilities != 0
                    and not isinstance(e, errors.TransactionConflictError)
                ):
                    raise e
                rule = query_context.retry_options.get_rule_for_exception(e)
                if i >= rule.attempts:
                    raise e
                await self.sleep(rule.backoff(i))
                reconnect = self.is_closed()


class _AsyncIOIteration(AsyncIOIteration):
    async def _execute(self, query_context: abstract.QueryContext):
        with self._exclusive():
            await self._ensure_transaction()
            return await self._connection.raw_query(
                query_context, enums.Capability.MODIFICATIONS
            )

    async def execute(self, commands: str, *args, **kwargs):
        return await self._execute(QueryContext(
            query=QueryWithArgs(commands, args, kwargs),
            cache=self._get_query_cache(),
            query_options=_query_opts,
            retry_options=self._get_retry_options(),
            state=self._get_state(),
        ))


class _AsyncIORetry(AsyncIORetry):
    async def __anext__(self):
        # Note: when changing this code consider also
        # updating Retry.__next__.
        if self._done:
            raise StopAsyncIteration
        if self._next_backoff:
            await asyncio.sleep(self._next_backoff)
        self._done = True
        iteration = _AsyncIOIteration(self, self._owner, self._iteration)
        self._iteration += 1
        return iteration


class _AsyncIOClient(AsyncIOClient):
    def transaction(self) -> _AsyncIORetry:
        return _AsyncIORetry(self)


# All deprecated space in v3dev & v3test & alpha
deprecated_space = [
    'ulqtqb',
    'zauoyn',
    'ocixjo',
    'kqgboa',
    'xnthjj',
    'itarfd',
    'thugts',
    'atadqj',
    'cfzqdn',
    'bwpxhl',
    'znjcye',
    'chhwqs',
    'zguhhs',
    'svaakp',
]


def create_async_client(default_module=None, dbname=None):
    if dbname is None:
        space = OPTION.api.header['space']
        dbname = None if space in deprecated_space else f"deepmodel_space{space}"
    cli = _AsyncIOClient(
        connection_class=_AsyncEdgeDBConnection,
        max_concurrency=None,
        dsn=OPTION.edgedb.dsn,
        database=dbname,
        tls_security='insecure',
        wait_until_available=30,
        timeout=OPTION.edgedb.timeout,
    )
    if default_module:
        cli = cli.with_default_module(default_module)
    return cli
