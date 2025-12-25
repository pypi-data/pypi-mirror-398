import inspect
import types
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any, Literal


def dict_has_key(source: dict,
                 key_chain: str | list[Any]) -> bool:
    """
    Indicate the existence of an element in *source*, pointed to by the nested key chain *[keys[0]: ... :keys[n]*.

    The key chain may be provided in flat (*key1.key2...keyN*) or list (*[key1, key2, ..., keyN]*) format.
    The path up to he last key in the chain must point to an existing element.
    A given key may indicate the element's position within a *list*, using the format *<key>[<pos>]*.

    :param source: the reference *dict*
    :param key_chain: the nested key chain
    :return: whether the element exists
    """
    # initialize the return variable
    result: bool = False

    # unflatten the key chain
    if isinstance(key_chain, str):
        from .list_pomes import list_unflatten
        key_chain = list_unflatten(source=key_chain)

    # define the parent element
    parent: dict | None = None

    # does the key chain contain just 1 element ?
    if len(key_chain) == 1:
        # yes, use the provided dict
        parent = source

    # does the key chain contain more than 1 element ?
    elif len(key_chain) > 1:
        # yes, obtain the parent element of the last key in the chain
        parent = dict_get_value(source=source,
                                key_chain=key_chain[:-1])

    # is the parent element a dict ?
    if isinstance(parent, dict):
        # yes, proceed
        key = key_chain[-1]

        # is the element denoted by the last key in the chain a list ?
        if key[-1] == "]":
            # yes, recover it
            pos: int = key.find("[")
            inx: int = int(key[pos+1:-1])
            key = key[:pos]
            child = parent.get(key)
            # success, if the element in question is a list with more than 'inx' elements
            result = isinstance(child, list) and len(child) > inx

        # success, if the parent element contains the last key in the chain
        else:
            result = key in parent

    return result


def dict_has_value(source: dict,
                   value: Any) -> Any:
    """
    Indicate the existence in *source*, of a key/value pair with *value* as its value.

    No recursion is attempted; only the first-level attributes in *source* are inspected.

    :param source: the reference *dict*
    :param value: the reference value
    :return: *True* if *value* exists in *source*, or *False* otherwise
    """
    # initialize the return variable
    result: bool = False

    for _, val in (source or {}).items():
        if val == value:
            result = True
            break

    return result


def dict_get_value(source: dict,
                   key_chain: str | list[Any]) -> Any:
    """
    Obtain the value of the element in *source*, pointed to by the nested key chain *[keys[0]: ... :keys[n]*.

    The key chain may be provided in flat (*key1.key2...keyN*) or list (*[key1, key2, ..., keyN]*) format.
    The path up to the last key in the chain must point to an existing element.
    A given key may indicate the element's position within a *list*, using the format *<key>[<pos>]*.
    Return *None* if the sought after value is not found.
    Note that returning *None* might not be indicative of the absence of the element in *source*,
    since that element might exist therein with the value *None*. To determine whether this is the case,
    use the operation *dict_has_key()*.

    :param source: the reference *dict*
    :param key_chain: the key chain
    :return: the value obtained
    """
    # initialize the return variable
    result: Any = source

    # unflatten the key chain
    if isinstance(key_chain, str):
        from .list_pomes import list_unflatten
        key_chain = list_unflatten(source=key_chain)

    # traverse the keys in the chain
    for key in key_chain:

        # is it possible to proceed ?
        if not isinstance(result, dict):
            # no, terminate the operation
            result = None
            break

        if key[-1] == "]":
            # the key refers to an element in a list, retrieve it
            pos: int = key.find("[")
            inx: int = int(key[pos+1:-1])
            result = result.get(key[:pos])

            result = result[inx] if isinstance(result, list) and len(result) > inx else None

            # is it possible to proceed ?
            if isinstance(result, list) and len(result) > inx:
                # yes, proceed
                result = result[inx]
            else:
                # no, abort the operation
                result = None
        else:
            # proceeding is not possible, the element corresponding to 'key' in the dictionary
            result = result.get(key)

    return result


def dict_set_value(target: dict,
                   key_chain: str | list[Any],
                   value: Any) -> dict:
    """
    Assign to an element of *source* the value *value*.

    The key chain may be provided in flat (*key1.key2...keyN*) or list (*[key1, key2, ..., keyN]*) format.
    The element in question is pointed to by the key chain *[keys[0]: ... :keys[n]*.
    If the element does not exist, it is created with the specified value.
    Any non-existing intermediate elements are created with the value of an empty *dict*.
    A key might indicate the position of the element within a list, using the format *<key>[<pos>]*.
    In such a case, that element must exist.
    For convenience, the possibly modified *target* itself is returned.

    :param target: the reference *dict*
    :param key_chain: the key chain
    :param value: the value to be assigned
    :return: the modified input *dict*
    """
    # unflatten the key chain
    if isinstance(key_chain, str):
        from .list_pomes import list_unflatten
        key_chain = list_unflatten(source=key_chain)

    dict_item: Any = target
    # traverse the chain, up to end including its penultimate element
    for key in (key_chain[:-1] or []):

        # is it possible to proceed ?
        if not isinstance(dict_item, dict):
            # no, abort the operation
            break

        # does 'key' refer to a list element ?
        if key[-1] == "]":
            # yes, retrieve it
            pos: int = key.find("[")
            inx: int = int(key[pos+1:-1])
            dict_item = dict_item.get(key[:pos])
            # is it possible to proceed ?
            if isinstance(dict_item, list) and len(dict_item) > inx:
                # yes, proceed
                dict_item = dict_item[inx]
            else:
                # no, abort the operation
                dict_item = None
        else:
            # no, does 'dict_item' have 'key' as one of its elements ?
            if key not in dict_item:
                # não, assign to 'dict_item' the element 'key', with an empty dict as value
                dict_item[key] = {}
            dict_item = dict_item.get(key)

    # does a key exist and is 'dict_item'a dict ?
    if len(key_chain) > 0 and isinstance(dict_item, dict):
        # yes, proceed
        key: str = key_chain[-1]
        # does 'key' refer to a list element ?
        if key[-1] == "]":
            # yes, retrieve it
            pos: int = key.find("[")
            inx: int = int(key[pos+1:-1])
            dict_item = dict_item.get(key[:pos])
            # is the assignment possible ?
            if isinstance(dict_item, list) and len(dict_item) > inx:
                # yes, do it
                dict_item[inx] = value
        else:
            # no, assign 'value' to the element 'key' in the dictionary
            dict_item[key] = value

    return target


def dict_pop(target: dict,
             key_chain: str | list[Any]) -> Any:
    """
    Remove the element in *source* pointed to by *key_chain*, and return its value.

    The key chain may be provided in flat (*key1.key2...keyN*) or list (*[key1, key2, ..., keyN]*) format.
    The path up to the last key in the chain must point to an existing element.
    A given key may indicate the element's position within a *list*, using the format *<key>[<pos>]*.

    Return *None* if the sought after value is not found.
    Note that returning *None* might not be indicative of the absence of the element in *source*,
    since that element might exist therein with the value *None*. To determine whether this is the case,
    use the operation *dict_has_key()*.

    :param target: the reference *dict*
    :param key_chain: the key chain
    :return: the value removed, or *None* if not found
    """
    # initialize the return variable
    result: Any = None

    # unflatten the key chain
    if isinstance(key_chain, str):
        from .list_pomes import list_unflatten
        key_chain = list_unflatten(source=key_chain)

    # obtain the element pointed to by the las key in the chain
    parent: dict | None = None

    # does the key chain contain just 1 element ?
    if len(key_chain) == 1:
        # yes, use the provided dict
        parent = target

    # does the key chain contain more than 1 element ?
    elif len(key_chain) > 1:
        # yes, retrieve the parent element of the last key in the chain
        parent = dict_get_value(source=target,
                                key_chain=key_chain[:-1])

    # is the parent element a dict ?
    if isinstance(parent, dict):
        # yes, proceed
        key: str = key_chain[-1]

        # does the last key un the chain refer to a list element ?
        if key[-1] == "]":
            # sim, retrieve the list
            pos: int = key.find("[")
            inx: int = int(key[pos+1:-1])
            key = key[:pos]
            child: Any = parent.get(key)

            # is the element pointed to by the last key in the chain a list with more than 'inx' elements ?
            if isinstance(child, list) and len(child) > inx:
                # yes, remove that element and return its value
                result = child.pop(inx)

        # does the parent item contain the last key in the chain ?
        elif key in parent:
            # yes, remove that element and return its value
            result = parent.pop(key)

    return result


def dict_pop_all(target: dict,
                 key: Any) -> dict:
    """
    Remove all elements in *source* associated with *key*, at all levels.

    Values of type *dict* found while traversing *target* are recursively processed for removal.
    For convenience the, possibly modified, input dict *target* is returned.

    :param target: the reference *dict*
    :param key: the key chain
    :return: the possibly modified input *dict*
    """
    # traverse the input dictionary
    for k, v in target.copy().items():
        if k == key:
            target.pop(k)
        elif v and isinstance(v, dict):
            # 'v' is a nonempty 'dict'
            target[k] = dict_pop_all(target=v,
                                     key=key)
    return target


def dict_replace_value(target: dict,
                       old_value: Any,
                       new_value: Any) -> dict:
    """
    Replace, in *target*, all occurrences of *old_value* with *new_value*.

    For convenience, the possibly modified *target* itself is returned.

    :param target: the reference *dict*
    :param old_value: the value to be replaced
    :param new_value: the new value
    :return: the modified input *dict*
    """
    def list_replace_value(items: list,
                           old_val: Any,
                           new_val: Any) -> None:
        # traverse the list
        for item in items:
            # is 'item' a dict ?
            if isinstance(item, dict):
                # yes, process it recursively
                dict_replace_value(target=item,
                                   old_value=old_val,
                                   new_value=new_val)
            # is 'item' a list ?
            elif isinstance(item, list):
                # yes, process it recursively
                list_replace_value(items=item,
                                   old_val=old_val,
                                   new_val=new_val)
    # traverse the dict
    for curr_key, curr_value in target.items():

        # is 'curr_value' the value to be replaced ?
        if curr_value == old_value:
            # yes, replace it
            target[curr_key] = new_value

        # is 'curr_value' a dict ?
        elif isinstance(curr_value, dict):
            # yes, process it recursively
            dict_replace_value(target=curr_value,
                               old_value=old_value,
                               new_value=new_value)

        # is 'curr_value' a list ?
        elif isinstance(curr_value, list):
            # yes, process it recursively
            list_replace_value(items=curr_value,
                               old_val=old_value,
                               new_val=new_value)
    return target


def dict_unique_values(source: dict) -> list:
    """
    Return a list with the values in *source*, pruned of duplicates.

    The elements in the returned list maintain the original insertion order in *source*.

    :param source: the dict to retrieve the values from
    :return: list the values in the source *dict*, pruned of duplicated
    """
    # a 'dict' maintains the insertion order of its elements
    uniques: dict[Any, None] = dict.fromkeys(source.values())
    return list(uniques.keys())


def dict_get_key(source: dict,
                 value: Any) -> Any:
    """
    Return the key in *source*, mapping the first occurrence of *value* found.

    No recursion is attempted; only the first-level attributes in *source* are inspected.

    :param source: dict to search
    :param value: the reference value
    :return: first key mapping the reference value, or *None* if a mapping is not found
    """
    # initialize the return variable
    result: Any = None

    for key, val in (source or {}).items():
        if val == value:
            result = key
            break

    return result


def dict_get_keys(source: dict,
                  value: Any) -> list[Any]:
    """
    Return all keys in *source*, mapping the value *value*.

    The search is done recursively. Note that *dict*s in *list*s are not searched.
    The order of the keys returned should not be taken as relevant.
    Return *[]* if no key is found.

    :param source: dict to search
    :param value: the reference value
    :return: list containing all keys mapping the reference value (might be empty)
    """
    # initialize the return variable
    result: list[str] = []

    for item_key, item_value in (source or {}).items():
        if item_value == value:
            result.append(item_key)
        elif isinstance(item_value, dict):
            result.extend(dict_get_keys(source=item_value,
                                        value=value))
    return result


def dict_merge(target: dict,
               source: dict) -> dict:
    """
    Traverse the elements in *source* to update *target*, according to the criteria presented herein.

    The criteria to be followed are:
      - add the element to *target*, if it does not exist
      - if the element exists in *target*:
        - recursively process both elements, if both are type *dict*
        - add the missing items, if both are type *list*
        - replace the element in *target* if it is a different type, ou if both elements are not of the same type
    For convenience, the possibly modified *target* itself is returned.

    :param target: the dictionary to be updated
    :param source: the dictionary with the new elements
    :return: the modified target *dict*
    """
    # traverse the dictionary with the new elements
    for skey, svalue in (source or {}).items():

        # is the item in target ?
        if skey in target:
            # yes, proceed
            tvalue: Any = target.get(skey)

            # are both elements dictionaries  ?
            if isinstance(svalue, dict) and isinstance(tvalue, dict):
                # yes, recursively process them
                dict_merge(target=tvalue,
                           source=svalue)

            # are both elements lists ?
            elif isinstance(svalue, list) and isinstance(tvalue, list):
                # yes, add the missing elements
                for item in svalue:
                    if item not in tvalue:
                        tvalue.append(item)
            else:
                # both elements are not lists or dictionaries, replace the value in target
                target[skey] = svalue
        else:
            # the item is not in target, add it
            target[skey] = svalue

    return target


def dict_coalesce(target: dict,
                  key_chain: str | list[Any]) -> dict:
    """
    Coalesce the element of type *list* in *target* at the level *n* with the list at the level immediately above.

    The key chain may be provided in flat (*key1.key2...keyN*) or list (*[key1, key2, ..., keyN]*) format.
    This element is pointed to by the key chain *[keys[0]: ... :keys[n]*, and is processed as a sequence
    of multiple elements. The two last keys in *key_chain* must be associated with values of type *list*.
    For convenience, the possibly modified *target* itself is returned.

    :param target: the *dict* to be coalesced
    :param key_chain: the chain of nested keys
    :return: the modified input *dict*
    """
    # unflatten the key chain
    if isinstance(key_chain, str):
        from .list_pomes import list_unflatten
        key_chain = list_unflatten(source=key_chain)

    # traverse the kay chain up to its penultimate element
    curr_dict: dict | None = target
    # 'key_chain[:-2]' returns an empy list if it has less the 3 elements
    for inx, key in enumerate(key_chain[:-2]):

        # is 'curr_dict' a dictionary ?
        if not isinstance(curr_dict, dict):
            # no, abort the operation
            break

        # is 'key' associated to a list ?
        in_list: list = curr_dict.get(key)
        if isinstance(in_list, list):
            # yes, recursively invoke the coalescing of the dictionaries in the list
            for in_dict in in_list:
                # is 'in_dict' a dictionary ?
                if isinstance(in_dict, dict):
                    # yes, recursively coalesce it
                    dict_coalesce(target=in_dict,
                                  key_chain=key_chain[inx + 1:])
            # finalize the operation
            curr_dict = None
            break

        # proceed, with the value associated to 'key'
        curr_dict = curr_dict.get(key)

    # is 'curr_dict' a dictionary containing the penultimate key ?
    if isinstance(curr_dict, dict) and \
       isinstance(curr_dict.get(key_chain[-2]), list):
        # yes, proceed with the operation
        penultimate_elem: list[dict] = curr_dict.pop(key_chain[-2])
        penultimate_list: list[dict] = []

        # traverse the penultimate element
        for last_elem in penultimate_elem:

            # is 'last_elem' a dictionary ?
            if isinstance(last_elem, dict):
                # yes, proceed
                outer_dict: dict = {}
                last_list: list[dict] = []

                # traverse the last element
                for k, v in last_elem.items():
                    # if 'k' the last key, and is it a list ?
                    if k == key_chain[-1] and isinstance(v, list):
                        # yes, obtain its items for further coalescing
                        for in_dict in v:
                            # is 'in_dict' a dictionary ?
                            if isinstance(in_dict, dict):
                                # yes, coalesce and save it
                                inner_dict: dict = dict(in_dict.items())
                                last_list.append(inner_dict)
                            else:
                                # no, save it as is
                                last_list.append(in_dict)
                    else:
                        # no, coalesce it
                        outer_dict[k] = v

                # are there items to be coalesced ?
                if len(last_list) > 0:
                    # yes, do it
                    for in_dict in last_list:
                        # is 'in_dict' a dictionary ?
                        if isinstance(in_dict, dict):
                            # yes, add the saved data to it
                            in_dict.update(outer_dict)
                        # save the item
                        penultimate_list.append(in_dict)
                else:
                    # no, save the already coalesced items
                    penultimate_list.append(outer_dict)
            else:
                # no, save it
                penultimate_list.append(last_elem)

        # replace the original list with the coalesced new list
        curr_dict[key_chain[-2]] = penultimate_list

    return target


def dict_reduce(target: dict,
                key_chain: str | list[Any]) -> dict:
    """
    Relocate the elements from *target* at level *n*, to the level immediately above.

    The key chain may be provided in flat (*key1.key2...keyN*) or list (*[key1, key2, ..., keyN]*) format.
    These elements are pointed to by the nested key chain *[keys[0]: ... :keys[n]*.
    The element at level *n* is removed at the end.
    For convenience, the possibly modified *target* itself is returned.

    :param target: the *dict* to be reduced
    :param key_chain: the key chain
    :return: the modified input *dict*
    """
    # unflatten the key chain
    if isinstance(key_chain, str):
        from .list_pomes import list_unflatten
        key_chain = list_unflatten(source=key_chain)

    curr_dict: dict | None = target
    # traverse the chain up to its penultimate key
    for inx, key in enumerate(key_chain[:-1]):

        # is it possible to proceed?
        if not isinstance(curr_dict, dict):
            # no, abort the operation
            break

        # is 'key' associated with a list ?
        in_list: list = curr_dict.get(key)
        if isinstance(in_list, list):
            # yes, recursively invoke reduction of the dictionaries in 'in_list'
            for in_dict in in_list:
                # Is the list item a dictionary ?
                if isinstance(in_dict, dict):
                    # sim, recursively reduce it
                    dict_reduce(target=in_dict,
                                key_chain=key_chain[inx + 1:])
            # terminate the operation
            curr_dict = None
            break

        # proceed with the value associated with 'key'
        curr_dict = curr_dict.get(key)

    last_key: str = key_chain[-1]
    # does 'curr_dict' contain a dictionary associated with 'last_key' ?
    if isinstance(curr_dict, dict) and \
       isinstance(curr_dict.get(last_key), dict):
        # yes, proceed with the reduction
        last: dict = curr_dict.pop(last_key)
        for key, value in last.items():
            curr_dict[key] = value

    return target


def dict_from_list(source: list[dict],
                   key_chain: str | list[Any],
                   value: Any) -> dict | None:
    """
    Locate in *source*, and return, the element of type *dict* having the attribute *key_chain* with value *value*.

    The key chain may be provided in flat (*key1.key2...keyN*) or list (*[key1, key2, ..., keyN]*) format.

    :param source: the list to be inspected
    :param key_chain: the key chain used in the search process
    :param value: the value of the element pointed to by the key chain
    :return: the *dict* wanted, or *None* if not found
    """
    # initialize the return variable
    result: dict | None = None

    for item in source:
        if isinstance(item, dict) and \
           value == dict_get_value(source=item,
                                   key_chain=key_chain):
            result = item
            break

    return result


def dict_from_object(source: object) -> dict:
    """
    Create a *dict* and populate it with the attributes in *source* containing non-None values.

    The input *source* might be any *object*, specially those decorated with *@dataclass*.

    :param source: the reference object
    :return: *dict* structurally similar to the reference object
    """
    # initialize the return variable
    result: dict = {}

    # obtain the object's source module
    source_module: types.ModuleType = inspect.getmodule(object=source)
    # obtain the source module's dictionary
    source_dict: dict = source.__dict__
    # traverse it
    for key, value in source_dict.items():
        # is 'value' None or an empty list ?
        if not (value is None or (isinstance(value, list) and len(value) == 0)):
            # no, proceed
            name: str = key

            # is 'value' a list ?
            if isinstance(value, list):
                # es, traverse it
                result[name] = []
                for list_item in value:
                    # is 'list_item' an object of the same module ?
                    if source_module == inspect.getmodule(object=list_item):
                        # yes, proceed recursively
                        result[name].append(dict_from_object(source=list_item))
                    else:
                        # no, proceed linearly
                        result[name].append(list_item)

            # is 'value' an object of the same module ?
            elif source_module == inspect.getmodule(object=value):
                # yes, proceed recursively
                result[name] = dict_from_object(source=value)
            else:
                # no, proceed linearly
                result[name] = value

    return result


def dict_transform(source: dict,
                   from_to_keys: list[tuple[str, Any]],
                   prefix_from: str = None,
                   prefix_to: str = None,
                   add_missing: bool = False) -> dict:
    """
    Build a new *dict*, according to the rules presented herein.

    This dictionary is constructed by creating, for each element of the list of tuples in
    *from_to_keys*, the element indicated by the second term of the tuple, assigning to it
    the value of the *source* element indicated by the first term of the tuple. Both terms
    of the tuples are represented by a chain of nested keys.

    For existing *dict* values, *dict_transform()* is recursively invoked. Fo existing *list* values,
    *list_transform()* is invoked.

    If defined, the prefixes *prefix_from* and *prefix_to*, respectively for the source and
    destination keys, have different treatments: *prefix-from* is added when searching
    for values in *source*, and *prefix-to* is removed when assigning values to the return *dict*.
    If *add_missing* is *True*, the entries in *source* whose keys are missing in *from_to_keys*
    are added to the new *dict*.

    :param source: the source *dict* for the transformation
    :param from_to_keys: the list of tuples containing the source and destination key sequences
    :param prefix_from: prefix to be added to source keys
    :param prefix_to: prefix to be removed from target keys
    :param add_missing: whether to add entries in *source* missing in *from_to_keys* (defaults to *False*)
    :return: the new *dict*
    """
    # import the needed functions
    from .list_pomes import list_get_coupled, list_transform, list_unflatten

    # initialize the return variable
    result: dict = {}

    # traverse the source dictionary
    for key, value in source.items():

        # define the source key chain
        if prefix_from:
            from_keys: str = f"{prefix_from}.{key}"
        else:
            from_keys: str = key

        # get the target key chain
        to_keys: str = list_get_coupled(coupled_elements=from_to_keys,
                                        primary_element=from_keys,
                                        couple_to_same=add_missing)

        # has the destination been defined ?
        if to_keys:
            # yes, get the target value
            if isinstance(value, dict):
                # 'value' is a dictionary, transform it
                to_value: dict = dict_transform(source=value,
                                                from_to_keys=from_to_keys,
                                                prefix_from=from_keys,
                                                prefix_to=to_keys,
                                                add_missing=add_missing)
            elif isinstance(value, list):
                # 'value' is a list, transform it
                to_value: list = list_transform(source=value,
                                                from_to_keys=from_to_keys,
                                                prefix_from=from_keys,
                                                prefix_to=to_keys,
                                                add_missing=add_missing)
            else:
                # 'value' is neither a dictionary nor a list
                to_value: Any = value

            # has the target prefix been defined and does it occur in the target string ?
            if prefix_to and to_keys.startswith(prefix_to):
                # yes, remove the prefix
                to_keys = to_keys[len(prefix_to)+1:]
            to_keys_deep: list[str] = list_unflatten(source=to_keys)

            # assign the transformed value to the result
            dict_set_value(target=result,
                           key_chain=to_keys_deep,
                           value=to_value)
    return result


def dict_clone(source: dict,
               from_to_keys: list[tuple[Any, Any] | Any],
               omit_missing: bool = True) -> dict:
    """
    Build a new *dict*, according to the rules presented herein.

    This dictionary is constructed by creating a new element for each element in the list
    *from_to_keys*. When the element of this list is a tuple, the name indicated by its
    second term is used, and the value of the *source* element indicated by the tuple's
    first term is assigned. This first term can be represented by a chain of  nested keys.
    The name of the element to be created can be omitted, in which case the name of the term
    indicative of the value to be assigned is used. If the corresponding value is not found
    in *source*, *None* is assigned.

    :param source: the source *dict*
    :param from_to_keys: list of elements indicative of the source and target keys
    :param omit_missing: omit the elements not found in the source *dict* (defaults to *True*)
    :return: the new *dict*
    """
    # initialize the return variable
    result: dict = {}

    # traverse the list of elements and add to the target dict
    for elem in from_to_keys:
        from_key: str = elem[0] if isinstance(elem, tuple) else elem
        to_key: str = (elem[1] if isinstance(elem, tuple) and len(elem) > 1 else None) or from_key
        has_key: bool = dict_has_key(source=source,
                                     key_chain=from_key)
        if has_key or not omit_missing:
            value: Any = dict_get_value(source=source,
                                        key_chain=from_key)
            result[to_key] = value

    return result


def dict_listify(target: dict,
                 key_chain: str | list[Any]) -> dict:
    """
    Insert the value of the item pointed to by the key chain *[keys[0]: ... :keys[n]* in a list.

    The key chain may be provided in flat (*key1.key2...keyN*) or list (*[key1, key2, ..., keyN]*) format.
    This insertion will happen only if such a value is not itself a list.
    All lists eventually found, up to the penultimate key in the chain, will be processed recursively.
    For convenience, the possibly modified *target* itself is returned.

    :param target: the dictionary to be modified
    :param key_chain: the chain of nested keys pointing to the item in question
    :return: the modified input *dict*
    """
    def items_listify(in_targets: list,
                      in_keys: list[str]) -> None:
        # traverse the list
        for in_target in in_targets:
            # is the element a dictionary ?
            if isinstance(in_target, dict):
                # yes, process it
                dict_listify(target=in_target,
                             key_chain=in_keys)
            # is the element a list ?
            elif isinstance(in_target, list):
                # yes, recursively process it
                # (key chain is also applicable to lists directly nested in lists)
                items_listify(in_targets=in_target,
                              in_keys=in_keys)

    # unflatten the key chain
    if isinstance(key_chain, str):
        from .list_pomes import list_unflatten
        key_chain = list_unflatten(source=key_chain)

    # traverse the chain up to its penultimate key
    parent: Any = target
    for inx, key in enumerate(key_chain[:-1]):
        parent = parent.get(key)
        if isinstance(parent, list):
            # process the list and close the operation
            items_listify(in_targets=parent,
                          in_keys=key_chain[inx+1:])
            parent = None

            # cannot proceed, exit the loop
            break

    if isinstance(parent, dict) and len(key_chain) > 0:
        key: str = key_chain[-1]
        # does the item exist and is not a list ?
        if key in parent and not isinstance(parent.get(key), list):
            # yes, insert it in a list
            item: Any = parent.pop(key)
            parent[key] = [item]

    return target


def dict_jsonify(source: dict,
                 jsonify_keys: bool = True,
                 jsonify_values: bool = True,
                 jsonify_enums: Literal["names", "values"] | None = "values") -> dict:
    """
    Convert the *(key, value)* pairs in *source* into values that can be serialized to JSON, thus avoiding *TypeError*.

    The parameters *jsonify_keys* and *jsonify_values* specify whether keys and values in *source* should be
    *jsonified*, respectively. No action is taken if both *jsonify_keys* and *jsonify_values* are set to *None*.

    The parameter *jsonify_enums* specify how *enums* are to be *jsonified*:
      - *None*: do not jsonify *enums*
      - *names*: use names
      - *value*: use values (the default)

    Possible transformations of keys and values:
      - *Enums* are changed to their values or names, or left unchanged (as per *jsonify_enums*)
      - *bytes* and *bytearray* values are changed with *str()*
      - *date* and *datetime* are changed to their *ISO* representations
      - *Path* is changed to its *POSIX* representation
      - *dict* is recursively *jsonified* with *dict_jsonify()* (values, only)
      - *list* is recursively *jsonified* with *list_jsonify()* (values, only)
      - all other types are left unchanged

    Note that retrieving the original values through a reversal of this process is not deterministic.
    The transformation is recursively carried out, that is, any *dict* or *list* set as value will be
    *jsonified* accordingly. For convenience, the possibly modified *source* itself is returned.

    *HAZARD*: depending on the type of object contained in *source*, the final result may still
    not be fully serializable.

    :param source: the dict to be made serializable
    :param jsonify_keys: whether the keys in *source* should be *jsonified* (defaults to *True*)
    :param jsonify_values: whether the values in *source* should be *jsonified* (defaults to *True*)
    :param jsonify_enums: whether to *jsonify* enums, using their values (the default) or names
    :return: the modified input *dict*
    """
    # traverse the input 'dict'
    keys: list[Any] = []
    for key, value in source.items():

        # values transformations
        if jsonify_values:
            if isinstance(value, Enum):
                if jsonify_enums == "values":
                    source[key] = value.value
                elif jsonify_enums == "names":
                    source[key] = value.name
            elif isinstance(value, bytes | bytearray):
                source[key] = str(value)
            elif isinstance(value, date):
                source[key] = value.isoformat()
            elif isinstance(value, Path):
                source[key] = value.as_posix()
            elif isinstance(value, dict):
                dict_jsonify(source=value,
                             jsonify_keys=jsonify_keys,
                             jsonify_values=jsonify_values)
            elif isinstance(value, list):
                from .list_pomes import list_jsonify
                source[key] = list_jsonify(source=value,
                                           jsonify_enums=jsonify_enums)
        # mark for key transformation
        if jsonify_keys and \
                isinstance(key, Enum | Path | bytes | bytearray | date):
            keys.append(key)

    # transform the keys
    for key in keys:
        if isinstance(key, Enum):
            if jsonify_enums == "values":
                source[key.value] = source.pop(key)
            elif jsonify_enums == "names":
                source[key.name] = source.pop(key)
        elif isinstance(key, bytes | bytearray):
            source[str(key)] = source.pop(key)
        elif isinstance(key, date):
            source[key.isoformat()] = source.pop(key)
        elif isinstance(key, Path):
            source[key.as_posix()] = source.pop(key)

    return source


def dict_hexify(source: dict,
                hexify_keys: bool = False,
                hexify_values: bool = True) -> dict:
    """
    Convert the *[key, value]* pairs in *source* to their hexadecimal representantions.

    The parameters *hexify_keys* and *hexify_values* specify whether keys and values are to be *hexified*,
    respectively. It is expected that either *hexify_keys* or *hexify_values*, or both, is set to *True*.

    Possible transformations of keys and values:
      - *str* is changed with *<value>.encode().hex()*
      - *int* is changed with *float(<value>).hex()*
      - *float*, *bytes*, and *bytearray* are changed using their built-in *hex()* method
      - *date* and *datetime* are changed using their ISO representations
      - *Path* is changed using its POSIX representation
      - *dict* is recursively *hexified* with *dict_hexify()*
      - *list* is recursively *hexified* with *list_hexify()*
      - all other types are left unchanged

    Note that retrieving the original values through a reversal of this process is not deterministic.
    The transformation is recursively carried out, that is, any *dict* or *list* set as value will be
    *hexified* accordingly. For convenience, the possibly modified *source* itself is returned.

    :param source: the dict to be made serializable
    :param hexify_keys: whether the keys in *source* should be *hexified* (defaults to *False*)
    :param hexify_values: whether the values in *source* should be *hexified* (defaults to *True*)
    :return: the modified input *dict*
    """
    # needed imports
    from .list_pomes import list_hexify

    # traverse the input 'dict'
    keys: list[Any] = []
    for key, value in source.items():

        # values transformations
        if hexify_values:
            if isinstance(value, dict):
                dict_hexify(source=value,
                            hexify_keys=hexify_keys,
                            hexify_values=hexify_values)
            elif isinstance(value, list):
                source[key] = list_hexify(source=value)
            elif isinstance(value, str):
                source[key] = value.encode().hex()
            elif isinstance(value, int):
                source[key] = float(value).hex()
            elif isinstance(value, float | bytes | bytearray):
                source[key] = value.hex()
            elif isinstance(value, Path):
                source[key] = value.as_posix().encode().hex()
            elif isinstance(value, date):
                source[key] = value.isoformat().encode().hex()

        # key transformations
        if hexify_keys and \
                isinstance(key, dict | list | int | float | str | Path | bytes | bytearray | date):
            keys.append(key)

    # transform the keys
    for key in keys:
        if isinstance(key, str):
            source[key.encode().hex()] = source.pop(key)
        elif isinstance(key, int):
            source[float(key).hex()] = source.pop(key)
        elif isinstance(key, float | bytes | bytearray):
            source[key.hex()] = source.pop(key)
        elif isinstance(key, Path):
            source[key.as_posix().encode().hex()] = source.pop(key)
        elif isinstance(key, date):
            source[key.isoformat().encode().hex()] = source.pop(key)

    return source


def dict_stringify(source: dict) -> str:
    """
    Return a string with the key-value pairs from *source* listed as *{<k1> = <v1>, ..., <kn> = <vn>}*.

    The *stringification* is done recursively, with *dict* and *list* as values handled accordingly.

    :param source: the source *dict*
    :return: the string listing the *key-value* pairs in *source*
    """
    from .list_pomes import list_stringify
    # initialize the return variable
    result: str = "{"

    if source:
        # traverse the source 'dict'
        for key, value in source.items():
            result += f"{key} = "
            if isinstance(value, dict):
                result += f"{dict_stringify(source=value)}"
            elif isinstance(value, list):
                result += f"{list_stringify(source=value)}"
            elif isinstance(value, str):
                result += f"'{value}'"
            else:
                result += f"{value}"
            result += ", "
        result = result[:-2]

    return result + "}"
