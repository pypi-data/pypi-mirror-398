"""
Collection+JSON representor. It converts a WeSTL document into Collection+JSON form. The Collection+JSON spec is at
http://amundsen.com/media-types/collection/. HEA implements the spec with the following exceptions:
* Data array:
** A section property. When going to/from nvpjson, the nvpjson object will have properties for each section,
each of which will have a nested object with the properties in that section.
** A sectionPrompt property for displaying a section name.
** Periods are reserved and should not be used in name property values.
"""

import uritemplate
import logging
import operator
from itertools import groupby
from heaobject import root
from heaobject.user import NONE_USER
from heaobject.root import is_heaobject_dict, is_heaobject_dict_list, is_primitive_list, is_primitive, DesktopObjectDict, are_permissions_read_only, desktop_object_type_for_name, Permission
from orjson import JSONDecodeError

import uritemplate.variable
from .error import ParseException, FormatException
from .. import jsonschemavalidator
from ..oidcclaimhdrs import SUB
from aiohttp.web import Request
from typing import Any, Union, Optional, Type
from collections.abc import Callable, Mapping, Sequence, Iterable, Mapping, MutableMapping, Iterator, AsyncIterator
from .representor import Representor, Link
from ..wstl import get_section, has_section, get_extended_property_value, has_extended_property_value
from heaserver.service.expression import get_eval_for

MIME_TYPE = 'application/vnd.collection+json'


class CJ(Representor):
    MIME_TYPE = MIME_TYPE

    @classmethod
    def supports_links(cls) -> bool:
        """
        The CJ representor supports links.

        :return: True
        """
        return True

    async def formats(self, request: Request,
                      wstl_obj: Union[Iterable[Mapping[str, Any]], Mapping[str, Any]],
                      dumps=root.json_dumps,
                      link_callback: Callable[[int, Link], None] | None = None,
                      include_data=True) -> bytes:
        """
        Formats a run-time WeSTL document as a Collection+JSON document.

        The Collection+JSON document will contain a template generated from the first action in the WeSTL document with
        a cj-template target, skipping such actions if its itemif expression evaluates to False.

        :param request: the HTTP request.
        :param wstl_obj: dict with run-time WeSTL JSON, or a list of run-time WeSTL JSON dicts.
        :param dumps: any callable that accepts dict with JSON and outputs str. Cannot be None. By default, it uses
        the heaobject.root.json_dumps function, which dumps HEAObjects and their attributes to JSON objects. Cannot
        be None.
        :param link_callback: a callable that will be invoked whenever a link is created. Links can be
        specific to a data item in the wstl_obj's data list or "global" to the entire data list. The
        first parameter contains the index of the data item from the WeSTL document, or None if the link is global. The
        second parameter contains the link as a heaserver.service.representor.Link object. The purpose of this
        callback is to access parameterized links after their parameters have been filled in.
        :param include_data: whether to include the data from the WSTL document in the response. Links are included in
        the response body regardless. Ensure that the request parameters and the WSTL data contain any information
        needed to generate the links.
        :return: a bytes object containing Collection+JSON collection JSON.
        :raises ValueError: if an error occurs formatting the WeSTL document as Collection+JSON.
        """

        async def cj_generator() -> AsyncIterator[dict[str, Any]]:
            for w in (wstl_obj if not isinstance(wstl_obj, Mapping) else [wstl_obj]):
                yield await self.__format(request, w, link_callback, include_data=include_data)
        l = list()
        async for c in cj_generator():
            l.append(c)
        return dumps(l).encode('utf-8')

    async def parse(self, request: Request) -> dict[str, Any]:
        """
        Parses an HTTP request containing a Collection+JSON template JSON document body into a dict-like object.

        :param request: the HTTP request. Cannot be None.
        :return: the data section of the Collection+JSON document transformed into a dict.
        :raises ParseException: if an error occurs parsing Collection+JSON into a dict-like object.
        """
        try:
            return to_nvpjson(await request.json())
        except (JSONDecodeError, jsonschemavalidator.ValidationError) as e:
            raise ParseException() from e

    @staticmethod
    async def __format(request: Request, wstl_obj: Mapping[str, Any],
                 link_callback: Callable[[int, Link], None] | None = None, include_data = True) -> dict[str, Any]:
        """
        Formats a run-time WeSTL document as a Collection+JSON document.

        :param request: the HTTP request.
        :param wstl_obj: dict with run-time WeSTL JSON.
        :param coll_url: the URL of the collection.
        :param link_callback: a callable that will be called whenever a link is created. The first
        parameter contains the index of the item from the WeSTL document, or None if the link is global. The second
        parameter contains the link as a heaserver.service.representor.Link object.
        :param include_data: whether to include the data from the WSTL document in the response. Links are included in
        the response body regardless. Ensure that the request parameters and the WSTL data contain any information
        needed to generate the links.
        :return: a Collection+JSON dict.
        """
        sub = request.headers.get(SUB, NONE_USER)
        wstl = wstl_obj['wstl']
        collection: dict[str, Any] = {}
        collection['version'] = '1.0'
        wstl_hea = wstl.get('hea', {})
        collection['href'] = wstl_hea.get('href', '#')
        collection['permissions'] = wstl_hea.get('permissions', [[]] * len(wstl.get('data', [])))

        content = _get_content(wstl)
        if content:
            collection['content'] = content
        tvars: uritemplate.variable.VariableValueDict = {}
        items = tuple(item for item in _get_items(request, wstl, tvars, link_callback=link_callback,
                                                  include_data=include_data,
                                                  permissions=wstl_hea.get('permissions')))
        if items:
            collection['items'] = items
        links = tuple(link for link in _get_links(wstl.get('actions', []), tvars, link_callback=link_callback))
        if links:
            collection['links'] = links
        if 'template' not in collection:
            template = await _get_template(sub, wstl.get('actions', []), tvars if len(wstl.get('data', [])) <= 1 else {}, wstl.get('data', []), wstl_hea.get('permissions'), wstl_hea.get('attribute_permissions'))
            if template:
                collection['template'] = template
        queries = tuple(query for query in _get_queries(wstl.get('actions', []), tvars))
        if queries:
            collection['queries'] = queries
        if 'error' in wstl:
            collection['error'] = _get_error(wstl['error'])

        return {'collection': collection}


def to_nvpjson(cj_template: Mapping[str, Mapping[str, Any]]) -> DesktopObjectDict:
    """
    Converts a Collection+JSON template dict into a nvpjson object dict.

    :param cj_template: a dict
    :return: nvpjson
    :raises jsonschemavalidator.ValidationError if invalid Collection+JSON was passed in.
    """
    jsonschemavalidator.CJ_TEMPLATE_SCHEMA_VALIDATOR.validate(cj_template)
    data = cj_template['template'].get('data', [])
    result: dict[str, Any] = {}
    triplets = []
    for d in data:
        nm = d['name']
        val = d.get('value', None)
        section = d.get('section', None)
        index = d.get('index', None)
        if section is not None and index is not None:
            triplets.append((section, index, nm, val))
        elif section is not None:
            result.setdefault(section, {})[nm] = val
        else:
            result[nm] = val
    if triplets:
        triplets.sort(key=operator.itemgetter(0, 1))
        for nm, val in groupby(triplets, operator.itemgetter(0)):  # by section
            result[nm] = [dict(x[2:] for x in e) for _, e in groupby(val, operator.itemgetter(1))]  # by index
    return result


def _get_content(obj):
    return obj.get('content', {})


def _get_links(actions: list[Mapping[str, Any]], tvars: uritemplate.variable.VariableValueDict,
               link_callback: Callable[[int, Link], None] | None = None) -> Iterator[dict[str, Any]]:
    """
    Get top-level links, with hrefs parameterized by the attribute values of the given tvars mapping.

    :param actions: list of actions.
    :param tvars: a mapping of variable names to values, populated from the request URL's path parameters, the headers,
    and for WeSTL documents with a single desktop object the desktop object's attribute values.
    :param link_callback: a callable that is invoked whenever a link is created. Arguments are the index of the item
    from the WeSTL object or None if the link is global, and the link as a heaserver.service.representor.Link object.
    (optional)
    :return: iterator of links as a dict of href, rel, and prompt.
    """
    for i, link in enumerate(actions):
        if link['type'] == 'safe' \
            and 'app' in link['target'] \
            and 'cj' in link['target'] \
            and ('inputs' not in link or not link['inputs']):
            url = uritemplate.expand(link['href'], tvars)
            l = {
                'href': url,
                'rel': ' '.join(link['rel']) or '',
                'prompt': link.get('prompt', '')
            }
            yield l
            if link_callback:
                link_callback(i, Link(href=url, rel=link['rel'], prompt=link.get('prompt')))


def _get_items(request: Request, wstl_obj: dict[str, Any], tvars: uritemplate.variable.VariableValueDict,
               link_callback: Callable[[int, Link], None] | None = None, include_data = True,
               permissions: Sequence[Sequence[str]] | None = None) -> Iterator[dict[str, Any]]:
    """
    Generates the Collection+JSON document's items array, which contain data objects, permissions, and links, from the
    given WeSTL document.

    To populate links' hrefs that are parameterized, this function collects attribute-value pairs from the request's
    match_info mapping and then the objects' attribute values, overwriting any previously populated values. It uses
    those attribute-value pairs to construct the links.

    For WeSTL documents with one data object, this function also populates a mapping, tvars, that is used to set
    default values for the Collection+JSON template. For ordinary objects. it populates the keys as the object's
    attribute names. For nested objects, it populates the keys as 'object_attribute.nested_object_attribute'. For
    arrays of nested objects, it populates the names as 'object_attribute.nested_object_attribute.index' with zero-
    based indices. Next, it populates attribute values from any headata-* actions, where the attribute is the string
    after headata-, and the values is the link's href. Third, it populates the mapping with attribute-value pairs from
    the request's match_info mapping, overwriting any previously populated values. Lastly, it populates the mapping
    with attribute-value pairs from the request's headers, overwriting any previously populated values.

    :param request: the HTTP request (required).
    :param wstl_obj: the WeSTL object (required).
    :param tvars: a mapping of variable names to values (required).
    :param link_callback: a callable that is invoked whenever a link is created. Arguments are the index of the item
    from the WeSTL object or None if the link is global, and the link as a heaserver.service.representor.Link object.
    (optional)
    :param include_data: whether to include the data from the WSTL document in the items.
    :return: the items array as an iterator of dicts.
    """
    wstl_data = wstl_obj.get('data', [])
    data_len = len(wstl_data)
    logger = logging.getLogger(__package__)
    logger.debug('%d item(s)', data_len)
    for wstl_data_obj_index, wstl_data_obj in enumerate(wstl_data):
        item: dict[str, Any] = {}
        type_str: Optional[str] = wstl_data_obj.get('type', None)
        if type_str:
            type_: Optional[Type[root.HEAObject]] = root.type_for_name(type_str)
        else:
            type_ = None
        local_tvars: dict[str, Any] = dict(request.match_info)
        def items_():
            for k, v in wstl_data_obj.items():
                if is_heaobject_dict(v) and len(v) > 0:
                    for kprime, vprime in v.items():
                        if kprime not in ('meta'):
                            yield {
                                'section': k,
                                'name': kprime,
                                'value': vprime,
                                'prompt': type_.get_prompt(kprime) if type_ else None,
                                'display': type_.is_displayed(kprime) if type_ else None
                            }
                            if data_len == 1:
                                tvars[f'{k}.{kprime}'] = vprime
                            local_tvars[f'{k}.{kprime}'] = vprime
                    if data_len == 1:
                        tvars[f'{k}'] = v
                    local_tvars[f'{k}'] = v
                elif is_heaobject_dict_list(v) and len(v) > 0:
                    v__ = False
                    v__prime = False
                    if len(v) == 0:
                        v__ = True
                    else:
                        for i, v_ in enumerate(v):
                            if isinstance(v_, dict):
                                v__prime = True
                                for kprime, vprime in v_.items():
                                    if kprime != 'meta':
                                        yield {
                                            'section': k,
                                            'index': i,
                                            'name': kprime,
                                            'value': vprime,
                                            'prompt': type_.get_prompt(kprime) if type_ else None,
                                            'display': type_.is_displayed(kprime) if type_ else None
                                        }
                                        if data_len == 1:
                                            tvars[f'{k}.{kprime}.{i}'] = vprime
                                        local_tvars[f'{k}.{kprime}.{i}'] = vprime
                            else:
                                v__ = True
                    if v__ and v__prime:
                        raise FormatException('List may not have a mixture of values and objects')
                    if v__:
                        yield {
                            'name': k,
                            'value': v,
                            'prompt': type_.get_prompt(k) if type_ else None,
                            'display': type_.is_displayed(k) if type_ else None
                        }
                    if data_len == 1:
                        tvars[f'{k}'] = v
                    local_tvars[f'{k}'] = v
                elif is_primitive(v) or is_primitive_list(v):
                    if k != 'meta':
                        yield {
                            'name': k,
                            'value': v,
                            'prompt': type_.get_prompt(k) if type_ else None,
                            'display': type_.is_displayed(k) if type_ else None
                        }
                        if data_len == 1:
                            tvars[k] = v
                        local_tvars[k] = v
                else:
                    raise ValueError(
                        f'Primitive property {k}={v} of type {type(v)} is not allowed; allowed types are {", ".join(str(s) for s in root.PRIMITIVE_ATTRIBUTE_TYPES)}')
        data_ = tuple(cjd for cjd in items_())
        if include_data:
            item['data'] = data_
        logger.debug('local_tvars=%s', local_tvars)

        link = _get_item_link(wstl_data_obj, wstl_obj['actions'], link_callback=link_callback, permissions=permissions[wstl_data_obj_index] if permissions else None)
        if link:
            if isinstance(link['rel'], list):
                item['rel'] = ' '.join(link['rel'])
            else:
                item['rel'] = link['rel']
            if 'href' in link:
                item['href'] = uritemplate.expand(link['href'], local_tvars)

        item['links'] = tuple(link_ for link_ in _get_item_links(wstl_data_obj, wstl_obj['actions'], local_tvars, link_callback=link_callback, permissions=permissions[wstl_data_obj_index] if permissions else None))
        for link in item['links']:
            for rel_value in link['rel'].split():
                if rel_value.startswith('headata-'):
                    headata_value = rel_value.removeprefix('headata-')
                    for data_part in data_:
                        if data_part['name'] == headata_value:
                            data_part['value'] = link.href
                            break
                    if data_len == 1:
                        tvars[headata_value] = link['href']
                    break
        yield item
    tvars.update(request.match_info)
    for k in set(request.headers.keys()):
        k_values = request.headers.getall(k)
        if len(k_values) == 1:
            tvars[k] = k_values[0]
        else:
            tvars[k] = k_values
    tvars.update(request.headers)
    logger.debug('tvars=%s', tvars)


def _get_queries(actions: list[dict[str, Any]], tvars: uritemplate.variable.VariableValueDict) -> Iterator[dict[str, Any]]:
    for action in actions:
        if 'inputs' in action and action['type'] == 'safe' and \
            _is_in_target('list', action) and _is_in_target('cj', action):
            q = {'rel': ' '.join(action['rel']), 'href': action['href'], 'prompt': action.get('prompt', ''), 'data': []}
            inputs_ = action['inputs']
            for i in range(len(inputs_)):
                d = inputs_[i]
                nm = d.get('name', 'input' + str(i))
                data_ = {
                    'name': nm,
                    'value': d.get('value'),
                    'prompt': d.get('prompt', nm),
                    'required': d.get('required', False),
                    'readOnly': d.get('readOnly', False),
                    'pattern': d.get('pattern')
                }
                q['data'].append(data_)
                add_extended_property_values(d, data_, tvars)
            yield q


async def _get_template(sub: str, wstl_actions: list[Mapping[str, Any]], tvars: uritemplate.variable.VariableValueDict,
                  data: Sequence[DesktopObjectDict] | None = None,
                  permissions: Sequence[Sequence[str]] | None = None,
                  attribute_permissions: Sequence[dict[str, Sequence[str]]] | None = None) -> dict:
    """
    Generates a template from the first action with a cj-template target, skipping such actions when there are multiple
    desktop objects in the data. Additionally, for any action with a cj-template target and when there is one desktop
    object in the data, the action will be skipped if its itemif expression evaluates to False.
    """
    cj_template = {}
    if attribute_permissions and len(data or []) == 1:
        attribute_permissions_ = attribute_permissions[0]
    elif data:
        empty_obj: root.DesktopObject = desktop_object_type_for_name(str(data[0]['type']))()
        empty_obj.owner = sub
        # PermissionContext may not be the right context for the type of object, strictly speaking, but since all we're
        # doing is getting attribute permissions assuming the current user owns the object, it is fine.
        attribute_permissions_ = {attr: [perm.name for perm in perms]
                                  for attr, perms in (await empty_obj.get_all_attribute_permissions(root.PermissionContext(sub))).items()}
    else:
        attribute_permissions_ = {}
    for wstl_action in wstl_actions:
        if _is_in_target('cj-template', wstl_action):
            if data and ((len(data) == 1 and not _item_if_matches(data[0], permissions[0] if permissions else None, wstl_action)) or len(set(d['type'] for d in data)) > 1):
                continue
            is_add = _is_in_target('add', wstl_action)

            cj_template['prompt'] = wstl_action.get('prompt', wstl_action['name'])
            cj_template['rel'] = ' '.join(wstl_action['rel'])

            cj_template['data'] = []
            for input_ in wstl_action['inputs']:
                nm = input_['name']
                read_only = are_permissions_read_only(attribute_permissions_.get(nm) or [])
                if is_add:
                    value_ = input_.get('value', None)
                elif has_section(input_):
                    value_ = tvars.get(f'{get_section(input_)}')
                else:
                    value_ = tvars.get(nm, None)
                if is_heaobject_dict_list(value_) and len(value_) > 0:
                    if not has_section(input_):
                        data_ = {
                            'name': input_['name'],
                            'value': value_,
                            'prompt': input_.get('prompt', nm),
                            'required': input_.get('required', False),
                            'readOnly': read_only or input_.get('readOnly', False),
                            'pattern': input_.get('pattern')
                        }
                        add_extended_property_values(input_, data_, tvars)
                        cj_template['data'].append(data_)
                    else:
                        template_val = {
                            'section': get_section(input_),
                            'index': -1,
                            'name': nm,
                            'value': input_.get('value') if has_section(input_) else (
                                value_ if value_ is not None else input_.get('value')),
                            'prompt': input_.get('prompt', nm),
                            'required': input_.get('required', False),
                            'readOnly': read_only or input_.get('readOnly', False),
                            'pattern': input_.get('pattern')
                        }
                        if has_extended_property_value('sectionPrompt', input_):
                            template_val['sectionPrompt'] = get_extended_property_value('sectionPrompt', input_)
                        add_extended_property_values(input_, template_val, tvars)
                        cj_template['data'].append(template_val)
                        for i, v in enumerate(value_):
                            data_ = {
                                'section': get_section(input_),
                                'index': i,
                                'name': input_['name'],
                                'value': v.get(input_['name']),
                                'prompt': input_.get('prompt', nm),
                                'required': input_.get('required', False),
                                'readOnly': read_only or input_.get('readOnly', False),
                                'pattern': input_.get('pattern')
                            }
                            if has_extended_property_value('sectionPrompt', input_):
                                data_['sectionPrompt'] = get_extended_property_value('sectionPrompt', input_)
                            add_extended_property_values(input_, data_, tvars)
                            cj_template['data'].append(data_)
                elif is_heaobject_dict(value_) and len(value_) > 0:
                    data_ = {
                        'section': get_section(input_),
                        'name': input_['name'],
                        'value': value_[input_['name']],
                        'prompt': input_.get('prompt', nm),
                        'required': input_.get('required', False),
                        'readOnly': input_.get('readOnly', read_only),
                        'pattern': input_.get('pattern')
                    }
                    if has_extended_property_value('sectionPrompt', input_):
                        input_['sectionPrompt'] = get_extended_property_value('sectionPrompt', input_)
                    add_extended_property_values(input_, data_, tvars)
                    cj_template['data'].append(data_)
                elif is_primitive(value_) or is_primitive_list(value_):
                    data_ = {}
                    if has_section(input_):
                        data_['section'] = get_section(input_)
                        data_['index'] = -1  # -1 means there are no rows in the section yet. The value property contains the default value.
                    if has_extended_property_value('sectionPrompt', input_):
                        data_['sectionPrompt'] = get_extended_property_value('sectionPrompt', input_)
                    data_ = data_ | {
                        'name': nm,
                        'value': input_.get('value') if has_section(input_) else (value_ if value_ is not None else input_.get('value')),  # this is the line
                        'prompt': input_.get('prompt', nm),
                        'required': input_.get('required', False),
                        'readOnly': input_.get('readOnly', read_only),
                        'pattern': input_.get('pattern')
                    }
                    add_extended_property_values(input_, data_, tvars)
                    cj_template['data'].append(data_)
                else:
                    raise ValueError(value_)
            resorted = []
            for k, g in groupby(cj_template['data'], key=lambda x: x.get('section')):
                if k is not None:
                    resorted.extend(sorted(g, key=lambda x: x.get('index', 0)))
                else:
                    resorted.extend(g)
            cj_template['data'] = resorted
            break
    return cj_template


def add_extended_property_values(wstl_action: Mapping[str, Any], template_input: MutableMapping[str, Any],
                                 tvars: uritemplate.variable.VariableValueDict | None = None):
    if tvars is not None:
        tvars_ = tvars
    else:
        tvars_ = {}
    if has_extended_property_value('type', wstl_action):
        template_input['type'] = get_extended_property_value('type', wstl_action)
    if has_extended_property_value('cardinality', wstl_action):
        template_input['cardinality'] = get_extended_property_value('cardinality', wstl_action)
    if has_extended_property_value('display', wstl_action):
        template_input['display'] = get_extended_property_value('display', wstl_action)
    if has_extended_property_value('objectUrlTargetTypesInclude', wstl_action):
        template_input['objectUrlTargetTypesInclude'] = get_extended_property_value('objectUrlTargetTypesInclude', wstl_action)
    if get_extended_property_value('type', wstl_action) == 'select':
        if has_extended_property_value('suggest', wstl_action):
            suggest = get_extended_property_value('suggest', wstl_action)
            if isinstance(suggest, list):
                template_input['options'] = suggest
            elif isinstance(suggest, dict) and 'related' in suggest and 'related' in wstl_action and suggest[
                'related'] in wstl_action['related']:
                template_input['options'] = [{'value': r[suggest['value']], 'text': r[suggest['text']]} for r in
                                             wstl_action['related'][suggest['related']] if
                                             suggest['value'] in r and suggest['text'] in r]
        elif optionsFromUrl := get_extended_property_value('optionsFromUrl', wstl_action):
            template_input.setdefault('options', {})['href'] = uritemplate.expand(optionsFromUrl['href'], tvars_)
            template_input['options']['text'] = optionsFromUrl['text']
            template_input['options']['value'] = optionsFromUrl['value']


def _get_item_links(item: DesktopObjectDict, actions: Sequence[Mapping[str, Any]], tvars: uritemplate.variable.VariableValueDict,
                    link_callback: Callable[[int, Link], None] | None = None,
                    permissions: Sequence[str] | None = None) -> Iterator[dict[str, Any]]:
    for i, action in enumerate(actions):
        target = action['target']
        if 'item' in target and 'read' in target and 'cj' in target:
            if not _item_if_matches(item, permissions, action):
                continue
            href = uritemplate.expand(action['href'], tvars)
            if link_callback:
                link_callback(i, Link(href=href, rel=action['rel'], prompt=action['prompt']))
            yield {
                'prompt': action['prompt'],
                'rel': ' '.join(action['rel']),
                'href': href
            }


def _get_item_link(item: DesktopObjectDict, actions: Sequence[Mapping[str, Any]], link_callback: Callable[[int, Link], None] | None = None, permissions: Sequence[str] | None = None) -> dict[str, Any]:
    rtn = {}
    for i, action in enumerate(actions):
        target = action['target']
        if 'item' in target and 'href' in target and 'cj' in target:
            if not _item_if_matches(item, permissions, action):
                continue
            rtn['rel'] = ' '.join(action['rel'])
            rtn['href'] = action['href']
            if link_callback:
                link_callback(i, Link(href=action['href'], rel=action['rel']))
            break
    return rtn


def _item_if_matches(item: DesktopObjectDict, permissions: Sequence[str] | None, action: Mapping[str, Any]) -> bool:
    """
    Checks if the action's item-if expression returns True for the given item.

    :param item: the item (required).
    :param action: the action (required).
    :return: True or False.
    """
    if (itemIf := action.get('hea', {}).get('itemIf', None)) is not None:
        if permissions is None:
            permissions = [p.name for p in Permission]
        def has_read_only_permission() -> bool:
            return not are_permissions_read_only(permissions)
        def has_editor_permission() -> bool:
            return any(p in permissions for p in (Permission.COOWNER.name, Permission.EDITOR.name))
        def has_deleter_permission() -> bool:
            return any(p in permissions for p in (Permission.COOWNER.name, Permission.DELETER.name))
        def has_sharer_permission() -> bool:
            return any(p in permissions for p in (Permission.COOWNER.name, Permission.SHARER.name))
        if not get_eval_for(item, extra_functions={
            'has_read_only_permission': has_read_only_permission,
            'has_editor_permission': has_editor_permission,
            'has_deleter_permission': has_deleter_permission,
            'has_sharer_permission': has_sharer_permission
        }).eval(itemIf):
            return False
    return True

def _get_error(obj):
    return {'title': 'Error', 'message': obj.message or '', 'code': obj.code or '', 'url': obj.url or ''}


def _is_in_target(str_: str, action: Mapping[str, Any]) -> bool:
    return str_ in action['target'].split(' ')
