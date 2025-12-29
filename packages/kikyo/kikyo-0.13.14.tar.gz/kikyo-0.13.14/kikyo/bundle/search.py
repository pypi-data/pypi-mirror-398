from typing import List, Optional, Any, Sequence, Dict

from elasticsearch import Elasticsearch, helpers
from elasticsearch import RequestsHttpConnection
from pydantic import BaseModel

from kikyo import Kikyo
from kikyo.search import Search, Index


class BaseResponse:
    def __init__(self, resp: dict):
        self.response = resp

    def __getitem__(self, key):
        return self.response.get(key)


class SearchResponse(BaseResponse):
    def hits_total(self) -> Optional[int]:
        total = self['hits'].get('total')
        if total:
            return total['value']

    def hits(self) -> List[dict]:
        return [h['_source'] for h in self['hits']['hits']]

    def raw_hits(self) -> List[dict]:
        return self['hits']['hits']

    def count(self) -> int:
        return self['count']

    def buckets(self, name: str) -> List[dict]:
        return self['aggregations'][name]['buckets']


class BulkResponse(BaseResponse):
    def errors(self) -> dict:
        return self['errors']

    def success(self) -> int:
        return self['success']


class EsBasedSearch(Search):
    def __init__(self, client: Kikyo):
        settings = client.settings.deep('elasticsearch')

        if not settings:
            return

        kwargs = {
            'connection_class': RequestsHttpConnection,
            'hosts': settings['hosts']
        }
        if 'username' in settings:
            kwargs['http_auth'] = (settings['username'], settings['password'])
        if 'timeout' in settings:
            kwargs['timeout'] = settings['timeout']
        if 'extra_params' in settings:
            kwargs.update(settings['extra_params'])
        if 'use_ssl' in settings:
            kwargs['use_ssl'] = settings['use_ssl']
            kwargs['ssl_show_warn'] = False
        if 'verify_certs' in settings:
            kwargs['verify_certs'] = settings['verify_certs']

        self.es = Elasticsearch(**kwargs)
        self.index_prefix = settings.get('index_prefix', default='')

        client.add_component('es_search', self)

    def get_index_of_topic(self, topic):
        if ',' in topic:
            topics = topic.split(',')
            topic = ','.join([t if t.startswith(self.index_prefix) else f'{self.index_prefix}{t}' for t in topics])
            return topic
        if topic.startswith(self.index_prefix):
            return topic
        return f'{self.index_prefix}{topic}'

    def index(self, topic: str) -> 'EsIndex':
        return EsIndex(topic, self)

    def search(self, index: str) -> 'IndexedQuery':
        """
        指定索引

        :param index: index名称
        """
        return IndexedQuery(index, self)


class EsIndex(Index):
    def __init__(self, topic: str, client: EsBasedSearch):
        self.topic = topic
        self.es = client.es
        self.client = client

    def exists(self, id: str) -> bool:
        return self.es.exists(
            self.client.get_index_of_topic(self.topic),
            id,
        )

    def get(self, id: str) -> dict:
        resp = self.es.get(
            self.client.get_index_of_topic(self.topic),
            id,
        )
        return resp['_source']

    def mget(self, *ids: List[str]) -> List[dict]:
        resp = self.es.mget(
            index=self.client.get_index_of_topic(self.topic),
            body={
                'ids': ids,
            }
        )
        return [(i['_source'] if i['found'] else None) for i in resp['docs']]

    def put(self, id: str, data: dict, refresh: bool = None):
        """
        更新指定数据，指定ID不存在时自动创建数据

        :param id: 数据ID
        :param data: 数据内容
        :param refresh: 强制刷新索引
        """
        kwargs = {}
        if refresh is not None:
            kwargs['refresh'] = refresh

        self.es.index(
            self.client.get_index_of_topic(self.topic),
            body=data,
            id=id,
            **kwargs,
        )

    def delete(self, id: str, refresh: bool = None):
        """
        删除指定数据

        :param id: 数据ID
        :param refresh: 强制刷新索引
        """
        kwargs = {}
        if refresh is not None:
            kwargs['refresh'] = refresh

        self.es.delete(
            self.client.get_index_of_topic(self.topic),
            id,
            **kwargs,
        )

    def update(self, id: str, data: dict = None, refresh: bool = None):
        """
        更新数据的指定字段

        :param id: 数据ID
        :param data: 更新的数据内容
        :param refresh: 强制刷新索引
        """
        kwargs = {}
        if refresh is not None:
            kwargs['refresh'] = refresh

        self.es.update(
            self.client.get_index_of_topic(self.topic),
            id=id,
            body={
                'doc': data,
            },
            **kwargs,
        )

    def search_by_dsl(self, query_body: dict) -> 'SearchResponse':
        resp = self.es.search(
            index=self.client.get_index_of_topic(self.topic),
            body=query_body,
        )
        return SearchResponse(resp)

    def count_by_dsl(self, query_body: dict) -> 'SearchResponse':
        resp = self.es.count(
            index=self.client.get_index_of_topic(self.topic),
            body=query_body,
        )
        return SearchResponse(resp)

    def update_by_dsl(self, query_body: dict, refresh: bool = None) -> 'BaseResponse':
        kwargs = {}
        if refresh is not None:
            kwargs['refresh'] = refresh

        resp = self.es.update_by_query(
            self.client.get_index_of_topic(self.topic),
            body=query_body,
            **kwargs,
        )
        return BaseResponse(resp)

    def bulk(self, actions: List[dict], refresh: bool = None, **kwargs) -> 'BulkResponse':
        if refresh is not None:
            kwargs['refresh'] = refresh

        success, errors = helpers.bulk(
            self.es,
            index=self.client.get_index_of_topic(self.topic),
            actions=actions,
            **kwargs,
        )
        return BulkResponse(dict(success=success, errors=errors))

    def query(self, name: str = None) -> 'QueryBuilder':
        """
        基于筛选表达式检索数据，影响评分

        :param name: 筛选的字段名称
        """

        q = IndexedQuery(self.topic, self.client)
        return QueryBuilder(name, q, q._queries)

    def filter(self, name: str = None) -> 'QueryBuilder':
        """
        基于筛选表达式检索数据，不影响评分

        :param name: 筛选的字段名称
        """

        q = IndexedQuery(self.topic, self.client)
        return QueryBuilder(name, q, q._filters)


class IndexedQuery(EsIndex):
    def __init__(self, index: str, client: EsBasedSearch):
        super().__init__(index, client)

        self._queries: List[NamedClause] = []
        self._filters: List[NamedClause] = []
        self._page = None
        self._size = None
        self._sort_by = []

    def query(self, name: str = None) -> 'QueryBuilder':
        return QueryBuilder(name, self, self._queries)

    def filter(self, name: str = None) -> 'QueryBuilder':
        return QueryBuilder(name, self, self._filters)

    def paginate(self, page: int = 0, size: int = 10) -> 'IndexedQuery':
        """
        分页查询

        :param page: 分页的页码，从0开始
        :param size: 分页的大小
        """

        self._page = page
        self._size = size
        return self

    def sort_by(self, name: str = None, order: str = None) -> 'IndexedQuery':
        if order is None:
            order = 'ASC'
        order = order.upper()
        self._sort_by.append({
            name: order
        })
        return self

    def hits(self) -> List[dict]:
        """
        返回命中查询的所有数据，默认进行了分页。
        """

        body = self._body_for_search()
        return self.search_by_dsl(body).hits()

    def raw_hits(self) -> List[dict]:
        body = self._body_for_search()
        return self.search_by_dsl(body).raw_hits()

    def count(self) -> int:
        """
        返回命中查询的数据量
        """

        body = {
            'query': self._build_query(),
        }
        return self.count_by_dsl(body).count()

    def _build_query(self) -> dict:
        query = BoolQuery()
        for q in self._queries:
            q.build(query.must, query.must_not)
        for f in self._filters:
            f.build(query.filter, query.must_not)
        return {
            'bool': query.model_dump()
        }

    def _body_for_search(self) -> dict:
        body = {
            'query': self._build_query(),
        }
        if self._size is not None:
            body['size'] = self._size
            if self._page is not None:
                body['from'] = self._page * self._size
        if self._sort_by:
            body['sort'] = self._sort_by
        return body


class BoolQuery(BaseModel):
    must: List[Dict] = []
    filter: List[Dict] = []
    must_not: List[Dict] = []
    should: List[Dict] = []


class ClauseType:
    IS = object()
    IS_NOT = object()
    IS_ONE_OF = object()
    IS_ONE_OF_TERMS = object()
    IS_BETWEEN = object()
    IS_NOT_BETWEEN = object()
    EXISTS = object()
    DOES_NOT_EXIST = object()
    MATCH = object()
    MUST = object()


class NamedClause(BaseModel):
    type: Any
    name: Optional[str]
    value: Any = None

    def build(self, must: list, must_not: list):
        if self.type == ClauseType.IS:
            assert isinstance(self.value, Sequence)
            if self.name is None:
                must.append({
                    'simple_query_string': {
                        'query': ' '.join([f'"{i}"' for i in self.value]),
                        'default_operator': 'and',
                    }
                })
            else:
                for i in self.value:
                    must.append(self._match_phrase(self.name, i))
        elif self.type == ClauseType.IS_NOT:
            assert isinstance(self.value, Sequence)
            if self.name is None:
                must_not.append({
                    'simple_query_string': {
                        'query': ' '.join([f'"{i}"' for i in self.value]),
                    }
                })
            else:
                for i in self.value:
                    must_not.append(self._match_phrase(self.name, i))
        elif self.type == ClauseType.IS_ONE_OF:
            assert isinstance(self.value, Sequence)
            b = BoolQuery()
            if self.name is None:
                for v in self.value:
                    b.should.append({
                        'simple_query_string': {
                            'query': f'"{v}"',
                        }
                    })
            else:
                for v in self.value:
                    b.should.append(self._match_phrase(self.name, v))
            must.append({
                'bool': b.model_dump(),
            })
        elif self.type == ClauseType.IS_ONE_OF_TERMS:
            assert isinstance(self.value, Sequence)
            must.append({
                'terms': {
                    self.name: self.value
                }
            })
        elif self.type in (ClauseType.IS_BETWEEN, ClauseType.IS_NOT_BETWEEN):
            assert isinstance(self.value, tuple)
            if self.name is not None:
                q = {}
                if self.value[0] is not None:
                    q['gte'] = self.value[0]
                if self.value[1] is not None:
                    q['lte'] = self.value[1]
                if q:
                    _q = {
                        'range': {
                            self.name: q
                        }
                    }
                    if self.type == ClauseType.IS_BETWEEN:
                        must.append(_q)
                    else:
                        must_not.append(_q)
        elif self.type == ClauseType.EXISTS:
            if self.name is not None:
                must.append(self._exists(self.name))
        elif self.type == ClauseType.DOES_NOT_EXIST:
            if self.name is not None:
                must_not.append(self._exists(self.name))
        elif self.type == ClauseType.MATCH:
            assert isinstance(self.value, Sequence)
            if self.name is None:
                must.append({
                    'simple_query_string': {
                        'query': ' '.join([i for i in self.value]),
                    }
                })
            else:
                for i in self.value:
                    must.append(self._match(self.name, i))
        elif self.type == ClauseType.MUST:
            assert isinstance(self.value, dict)
            must.append(self.value)

    @staticmethod
    def _match_phrase(name: str, value: Any) -> dict:
        if ',' in name:
            s = name.split(',')
            return {
                "multi_match": {
                    "type": "phrase",
                    "query": value,
                    "fields": [i.strip() for i in s]
                }
            }
        return {
            'match_phrase': {
                name: value
            }
        }

    @staticmethod
    def _match(name: str, value: Any) -> dict:
        if ',' in name:
            s = name.split(',')
            return {
                "multi_match": {
                    "query": value,
                    "fields": [i.strip() for i in s]
                }
            }
        return {
            'match': {
                name: value,
            }
        }

    @staticmethod
    def _exists(name: str) -> dict:
        return {
            'exists': {
                'field': name
            }
        }


class QueryBuilder:
    def __init__(self, name: Optional[str], query: IndexedQuery, query_set: list):
        self._name = name
        self._query = query
        self._query_set = query_set

    def is_(self, *values: Any) -> IndexedQuery:
        """
        是某个值

        :param values: 具体值的列表
        """

        self._query_set.append(
            NamedClause(
                type=ClauseType.IS,
                name=self._name,
                value=values,
            )
        )
        return self._query

    def is_not(self, *values: Any) -> IndexedQuery:
        """
        不是某个值

        :param values: 具体值的列表
        """

        self._query_set.append(
            NamedClause(
                type=ClauseType.IS_NOT,
                name=self._name,
                value=values
            )
        )
        return self._query

    def is_one_of(self, *values: Any, terms: bool = False) -> IndexedQuery:
        """
        是其中某个值

        :param values: 具体值的列表
        :param terms: 是否使用terms查询
        """

        self._query_set.append(
            NamedClause(
                type=ClauseType.IS_ONE_OF_TERMS if terms else ClauseType.IS_ONE_OF,
                name=self._name,
                value=values,
            )
        )
        return self._query

    def is_between(self, lower_bound: Any = None, upper_bound: Any = None) -> IndexedQuery:
        """
        在区间范围内

        :param lower_bound: 最低值
        :param upper_bound: 最高值
        """

        self._query_set.append(
            NamedClause(
                type=ClauseType.IS_BETWEEN,
                name=self._name,
                value=(lower_bound, upper_bound),
            )
        )
        return self._query

    def is_not_between(self, lower_bound: Any = None, upper_bound: Any = None) -> IndexedQuery:
        """
        不在区间范围内

        :param lower_bound: 最低值
        :param upper_bound: 最高值
        """

        self._query_set.append(
            NamedClause(
                type=ClauseType.IS_NOT_BETWEEN,
                name=self._name,
                value=(lower_bound, upper_bound),
            )
        )
        return self._query

    def exists(self) -> IndexedQuery:
        """
        字段存在
        """

        self._query_set.append(
            NamedClause(
                type=ClauseType.EXISTS,
                name=self._name,
            )
        )
        return self._query

    def does_not_exists(self) -> IndexedQuery:
        """
        字段不存在
        """

        self._query_set.append(
            NamedClause(
                type=ClauseType.DOES_NOT_EXIST,
                name=self._name,
            )
        )
        return self._query

    def match(self, *values: Any) -> IndexedQuery:
        """
        模糊匹配

        :param values: 具体值的列表
        """

        self._query_set.append(
            NamedClause(
                type=ClauseType.MATCH,
                name=self._name,
                value=values,
            )
        )
        return self._query

    def must(self, query: dict) -> IndexedQuery:
        """
        must表达式

        :param query: 表达式
        """

        self._query_set.append(
            NamedClause(
                type=ClauseType.MUST,
                name=self._name,
                value=query,
            )
        )
        return self._query
