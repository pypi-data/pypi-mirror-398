import contextlib
from collections import defaultdict
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any, Literal


def list_compare(list1: list,
                 list2: list) -> bool:
    """
    Compare the contents of the two lists *list1* e *list2*.

    Return *True* if all the elements in *list1* are also in *list2*, and vice versa, with the same cardinality.
    The input list need not be sorted.

    :param list1: the first list
    :param list2: the second list
    :return: True if the two lists contain the same elements, in the same quantity, in any order
    """
    # initialize the return variable
    result: bool = True

    # are the input parameters lists containing the same number of elements ?
    if isinstance(list1, list) and \
       isinstance(list2, list) and \
       len(list1) == len(list2):
        # yes, verify whether all elements in 'list1' are also in 'list2', in the same quantity
        for elem in list1:
            # is 'elem' in both lists, in the same quantity ?
            if list1.count(elem) != list2.count(elem):
                # no, the lists are not equal
                result = False
                break
    else:
        # no, the lists are not equal
        result = False

    return result


def list_correlate(list_first: list,
                   list_second: list,
                   only_in_first: bool = False,
                   only_in_second: bool = False,
                   in_both: bool = False,
                   is_sorted: bool = False) -> tuple:
    """
    Correlate *list_first* and *list_second* by computing their differences.

    A tuple containing up to three lists is returned, with contents based on the parameters:
      - *only_in_first*: items existing in *list_first* but not in *list_second*
      - *only_in_second*: items existing in *list_second* but not in *list_first*
      - *in_both*: items existing in both lists
    If none of these parameters have been specified, no correlation is carried out and an empty tuple is returned.

    The parameter *is_sorted* indicates that both *list_first* and *list_second* are ascendingly or
    descendingly sorted, and binary search is used in the correlation process.

    Note that, depending on the context, a returning list might be the same object as *list_first*
    or *list_second*. The input lists need not be sorted.

    :param list_first: the first list to consider
    :param list_second: the second list to consider
    :param only_in_first: include list of items existing in *list_first* but not in *list_second*
    :param only_in_second: include list of items existing in *list_second* but not in *list_first*
    :param in_both: include list of items existing in both lists
    :param is_sorted: *list_first* and *list_second* are both ascendingly or descendingly sorted
    :return: a tuple containing up to three lists, resulting from correlating the input lists
    """
    # initialize the return variable
    result: tuple = ()

    if only_in_first or only_in_second or in_both:
        result_first: list = []
        result_second: list = []
        result_both: list = []

        if list_first and list_second:
            if is_sorted:
                if in_both or only_in_first:
                    for item in list_first:
                        if list_bin_search(source=list_second,
                                           item=item) < 0:
                            if only_in_first:
                                result_first.append(item)
                        elif in_both:
                            result_both.append(item)
                if only_in_second:
                    result_second = [item for item in list_second if list_bin_search(source=list_first,
                                                                                     item=item) < 0]
            else:
                if in_both or only_in_first:
                    for item in list_first:
                        if item in list_second:
                            if in_both:
                                result_both.append(item)
                        elif only_in_first:
                            result_first.append(item)
                if only_in_second:
                    result_second = [item for item in list_second if item not in list_first]
        elif list_first and only_in_first:
            result_first = list_first
        elif list_second and only_in_second:
            result_second = list_second

        # assemble the return tuple
        correlations: list[list] = []
        if only_in_first:
            correlations.append(result_first)
        if only_in_second:
            correlations.append(result_second)
        if in_both:
            correlations.append(result_both)
        result = tuple(correlations)

    return result


def list_bin_search(source: list,
                    item: Any) -> int:
    """
    Find the index of *item* in the sorted list *source*, using binary search.

    If *source* is not ascendingly or descendingly sorted, the return value is not valid.

    :param source: the sorted list to inspect
    :param item: the item to find
    :return: the position of *item* in *source*, or "-1" if not found
    """
    # initialize the return variable
    result: int = -1

    low: int = 0
    high: int = len(source) - 1
    is_ascending: bool = source[low] < source[high]

    while result < 0 and low <= high:
        mid: int = (low + high) // 2
        if source[mid] == item:
            result = mid
        elif is_ascending:
            if item < source[mid]:
                high = mid - 1
            else:
                low = mid + 1
        elif item > source[mid]:
            high = mid - 1
        else:
            low = mid + 1

    return result


def list_flatten(source: list[str]) -> str:
    """
    Build and return a *str* by concatenating with "." the elements in *source*.

    Examples:
        - ['1', '2', '']     -> '1.2.'
        - ['', 'a', 'b']     -> '.a.b'
        - ['x', '', '', 'y'] -> 'x...y'
        - ['z']              -> 'z'

    :param source: the source list
    :return: the concatenated elements of the source list
    """
    result: str = ""
    for item in source:
        result += "." + item
    return result[1:]


def list_unflatten(source: str) -> list[str]:
    """
    Build and return a *list*, by splitting *source* into its components separated by ".".

    This *list* will contain the extracted components. Examples:
        - '1.2.'  -> ['1', '2', '']
        - '.a.b'  -> ['', 'a', 'b']
        - 'x...y' -> ['x', '', '', 'y']
        - 'z'     -> ['z']

    :param source: string with components concatenated by "."
    :return: the list of strings containing the concatenated components
    """
    from .str_pomes import str_split_on_mark

    return str_split_on_mark(source, ".")


def list_get_coupled(coupled_elements: list[tuple[str, Any]],
                     primary_element: str,
                     couple_to_same: bool = False) -> Any:
    """
    Retrieve from *coupled_elements*, and return, the element coupled to *primary_element*.

    A coupled element is the second element in the tuple whose first element is *primary_element*.

    If *primary_element* contains an index indication (denoted by *[<pos>]*), this indication is removed.
    This function is used in the transformation of *dicts* (*dict_transform*) and *lists* (*list_transform*),
    from sequences of key pairs.

    If *couple_to_same* is *True* and *primary_element* is missing from *coupled_elements*, then
    it is coupled to itself. Note that *primary_element* may be coupled to *None* in *coupled_elements*,
    in which case it is not considered to be missing.

    :param coupled_elements: list of tuples containing the pairs of elements
    :param primary_element: the primary element
    :param couple_to_same: whether to couple *primary_element* to itself if missing in *coupled_elements*
    :return: the coupled element, or *None* if it is not found and *couple_to_same* is *False*
    """
    # initialize the return variable
    result: Any = None

    # remove the list element indication
    pos1: int = primary_element.find("[")
    while pos1 > 0:
        pos2: int = primary_element.find("]", pos1)
        primary_element = primary_element[:pos1] + primary_element[pos2+1:]
        pos1 = primary_element.find("[")

    # traverse the list of coupled elements
    is_coupled: bool = False
    for coupled_element in coupled_elements:
        # has the primary element been found ?
        if coupled_element[0] == primary_element:
            # yes, return the corresponding coupled element
            result = coupled_element[1]
            is_coupled = True
            break
    if couple_to_same and not is_coupled:
        result = primary_element

    return result


def list_transform(source: list,
                   from_to_keys: list[tuple[str, Any]],
                   prefix_from: str = None,
                   prefix_to: str = None,
                   add_missing: bool = False) -> list:
    """
    Construct a new *list*, recursively transforming elements of type *list* and *dict* found in *source*.

    The conversion of *dict* type elements is documented in the *dict_transform* function.

    The prefixes for the source and destination keys, if defined, have different treatments.
    They are added when searching for values in *Source*, and removed when assigning values
    to the return *dict*.
    If *add_missing* is *True*, the entries in *source* whose keys are missing in *from_to_keys*
    are added to the new *list*.

    :param source: the source *dict* of the values
    :param from_to_keys: the list of tuples containing the source and destination key sequences
    :param prefix_from: prefix to be added to the source keys
    :param prefix_to: prefix to be removed from the target keys
    :param add_missing: whether to add entries in *source* missing in *from_to_keys* (defaults to *False*)
    :return: the new list
    """
    from .dict_pomes import dict_transform

    # initialize the return variable
    result: list = []

    # traverse the source list
    for inx, value in enumerate(source):
        from_keys: str | None = None
        if prefix_from:
            from_keys: str = f"{prefix_from}[{inx}]"

        # obtain the target value
        if isinstance(value, dict):
            to_value: dict = dict_transform(source=value,
                                            from_to_keys=from_to_keys,
                                            prefix_from=from_keys,
                                            prefix_to=prefix_to,
                                            add_missing=add_missing)
        elif isinstance(value, list):
            to_value: list = list_transform(source=value,
                                            from_to_keys=from_to_keys,
                                            prefix_from=from_keys,
                                            prefix_to=prefix_to,
                                            add_missing=add_missing)
        else:
            to_value: Any = value

        # added the value transformed to 'result'
        result.append(to_value)

    return result


def list_elem_with_attr(source: list,
                        attr: str,
                        value: Any) -> Any:
    """
    Locate and return the first element in *source* having an attribute named *attr* with value *value*.

    Values obtained by invoking *get* on the element are also considered. *None* is a valid value for *value*.

    :param source: The list to search for the element
    :param attr: the name of the reference attribute
    :param value: the reference value
    :return: The element in *source* having an attribute *attr* with *value*, or *None*
    """
    # initialize the return variable
    result: Any = None

    # traverse the source list
    for element in source:
        if hasattr(element, attr) and getattr(element, attr) == value:
            result = element
            break
        with contextlib.suppress(Exception):
            if element.get(attr) == value:
                result = element
                break

    return result


def list_elem_starting_with(source: list[str | bytes],
                            prefix: str | bytes,
                            keep_prefix: bool = True) -> str | bytes | None:
    """
    Locate and return the first element in *source* prefixed by *prefix*.

    Retorn *None* if this element is not found.

    :param source: the list to be inspected
    :param prefix: the data prefixing the element to be returned
    :param keep_prefix: defines whether the found element should be returned with the prefix
    :return: the prefixed element, with or without the prefix, or *None* if not found
    """
    # initialize the return variable
    result: str | bytes | None = None

    # traverse the source list
    for elem in source:
        if elem.startswith(prefix):
            if keep_prefix:
                result = elem
            else:
                result = elem[len(prefix)+1:]
            break

    return result


def list_prune_duplicates(target: list,
                          is_sorted: bool = False) -> list:
    """
    Remove duplicate elements from *target*.

    The parameter *is_sorted* indicates that *target* is ascendingly or descendingly sorted.
    In both cases, the original order of the elements in *target* is maintained.
    For convenience, the pruned input list is returned.

    :param target: the target list
    :param is_sorted: *target* is ascendingly or descendingly sorted
    :return: *target* with its duplicate elements removed
    """
    # mark the boundary of the unique segment in the list
    write_index: int = 1

    # traverse the list
    if is_sorted:
        # remove duplicates by comparing each element with the last unique one
        for read_index in range(1, len(target)):
            if target[read_index] != target[write_index - 1]:
                # add this element to the unique segment in the list
                if write_index != read_index:
                    target[write_index] = target[read_index]
                write_index += 1
    else:
        # remove duplicates by verifying if each element is in the unique segment in the list
        for read_index in range(1, len(target)):
            if target[read_index] not in target[:write_index]:
                # add this element to the unique segment in the list
                if write_index != read_index:
                    target[write_index] = target[read_index]
                write_index += 1

    # delete the remaining tail of the list
    del target[write_index:]

    # return the input list for convenience
    return target


def list_prune_in(target: list,
                  ref: list) -> list:
    """
    Remove from *target* all its elements that are also in *ref*.

    The pruned input list is returned, for convenience.

    :param target: the target list
    :param ref: the reference list
    :return: the target list without the elements also in the reference list
    """
    # initialize the return variable
    result: list = target

    removals: list = [item for item in result if item in ref]
    for item in removals:
        result.remove(item)

    return result


def list_prune_not_in(target: list,
                      ref: list) -> list:
    """
    Remove from *target* all of its elements that are not also in *ref*.

    The pruned input list is returned, for convenience.

    :param target: the target list
    :param ref: the reference list
    :return: the target list without the elements not in the reference list
    """
    # initialize the return variable
    result: list = target

    removals: list = [item for item in result if item not in ref]
    for item in removals:
        result.remove(item)

    return result


def list_jsonify(source: list,
                 jsonify_enums: Literal["names", "values"] | None = "values") -> list:
    """
    Return a new *list* containing the values in *source*, made serializable if necessary.

    Possible transformations:
      - *Enum* is changed to its value or name, as per *jsonify_enums* (defaults to value)
      - *bytes* and *bytearray* are changed with *str()*
      - *date* and *datetime* are changed to their *ISO* representations
      - *Path* is changed to its *POSIX* representation
      - *dict* is recursively *jsonified* with *dict_jsonify()*, unless *jsonify_enums* is *None*
      - *list* is recursively *jsonified* with *list_jsonify()*
      - all other types are left unchanged

    Note that retrieving the original values through a reversal of this process is not deterministic.
    The transformation is recursively carried out, that is, any *dict* or *list* set as a list item
    will be *jsonified* accordingly.

    *HAZARD*: depending on the type of object contained in *source*, the final result may still
    not be fully serializable.

    :param source: the *dict* to be *jsonified*
    :param jsonify_enums: whether to *jsonify* enums, using their values (the default) or names
    :return: a new *jsonified* list
    """
    # initialize the return variable
    result: list = []

    # traverse the input list
    for value in source:
        if isinstance(value, Enum):
            result.append(value.value if jsonify_enums == "values" else value.name)
        elif isinstance(value, bytes | bytearray):
            result.append(str(value))
        elif isinstance(value, date):
            result.append(value.isoformat())
        elif isinstance(value, Path):
            result.append(value.as_posix())
        elif isinstance(value, dict):
            if jsonify_enums:
                from .dict_pomes import dict_jsonify
                result.append(dict_jsonify(source=value,
                                           jsonify_keys=jsonify_enums == "names",
                                           jsonify_values=jsonify_enums == "values"))
        elif isinstance(value, list):
            result.append(list_jsonify(source=value,
                                       jsonify_enums=jsonify_enums))
        else:
            result.append(value)

    return result


def list_hexify(source: list) -> list:
    """
    Return a new *list* containing the values in *source* changed to their hexadecimal representations.

    Possible transformations:
      - *str* is changed with *<value>.encode().hex()*
      - *int* is changed with *float(<value>).hex()*
      - *float*, *bytes*, and *bytearray* are changed using their built-in *hex()* method
      - *date* and *datetime* are changed using their ISO representations
      - *Path* is changed using its POSIX representation
      - *dict* is recursively *hexified* with *dict_hexify()*
      - *list* is recursively *hexified* with *list_hexify()*
      - all other types are left unchanged

    Note that retrieving the original values through a reversal of this process is not deterministic.
    The transformation is recursively carried out, that is, any *dict* or *list* set as a list item
    will be *hexified* accordingly.

    :param source: the list to be *hexified*
    :return: a list with *hexified* values
    """
    from .dict_pomes import dict_hexify

    # initialize the return variable
    result: list = []

    # traverse the input list
    for value in source:
        if isinstance(value, dict):
            dict_hexify(source=value,
                        hexify_keys=False,
                        hexify_values=True)
            result.append(value)
        elif isinstance(value, list):
            result.append(list_hexify(source=value))
        elif isinstance(value, str):
            result.append(value.encode().hex())
        elif isinstance(value, int):
            result.append(float(value).hex())
        elif isinstance(value, float | bytes | bytearray):
            result.append(value.hex())
        elif isinstance(value, Path):
            result.append(value.as_posix().encode().hex())
        elif isinstance(value, date):
            result.append(value.isoformat().encode().hex())
        else:
            result.append(value)

    return result


def list_hierarchize(source: list[list | tuple]) -> list:
    """
    Hierarchize a fully sorted list of tuples or list of lists by aggregating common values at all levels.

    To illustrate, let us assume *source* is the input list:
    ::
      [
        ('John', 'parent Fred', 'old age', 'indifferent'),
        ('John', 'parent Fred', 'old age', 'unaffected'),
        ('John', 'parent Fred', 'poor health', 'broken'),
        ('John', 'parent Fred', 'poor health', 'constrained'),
        ('John', 'parent Fred', 'poor health', 'dependent'),
        ('John', 'parent Kate', 'happy soul'),
        ('John', 'parent Kate', 'very intelligent'),
        ('Mary', 'child John', 'brown eyes'),
        ('Mary', 'child John', 'red hair'),
        ('Mary', 'child Susan', 'blue eyes'),
        ('Mary', 'child Susan', 'median height'),
        ('Mary', 'sibling Joan', 'charming dude'),
        ('Mary', 'sibling Joan', 'smart girl')
     ]

    The resulting hierarchization would yield the list:
    ::
      [
        ['John',
          ['parent Fred',
            ['old age', ['indifferent', 'unaffected']],
            ['poor health', ['broken', 'constrained', 'dependent']]],
          ['parent Kate', ['happy soul', 'very intelligent']]],
        ['Mary',
          ['child John', ['brown eyes', 'red hair']],
          ['child Susan', ['blue eyes', 'median height']],
          ['sibling Joan', ['charming dude', 'smart girl']]]
      ]

    Notes:
      - the elements in *source* must not contain embedded lists or tuples
      - once an aggregation has been given a value, another aggregation cannot be added to it, such as:

        ('John', 'parent Fred', 'poor health', 'dependent'),

        ('John', 'parent Fred', 'poor health', 'constrained', 'simple'),

        ('John', 'parent Fred', 'poor health', 'constrained', 'complex'),

    :param source: the fully sorted list of tuples or list of lists to be hierarchized
    :return: the hierarchized list

    """
    def add_to_hierarchy(hierarchy: dict,
                         keys: list,
                         value: list | tuple) -> None:
        for key in keys[:-1]:
            hierarchy.setdefault(key, {})
        # if isinstance(l_hierarchy.get(keys[-1]), dict):
        hierarchy.setdefault(keys[-1], []).append(value)

    def convert_to_list(item: Any) -> list:
        result: list
        if isinstance(item, dict):
            result = []
            for k, v in item.items():
                if isinstance(v, dict):
                    result.append([k, *convert_to_list(item=v)])
                else:
                    result.append([k, v] if len(v) > 1 else [k, *v])
        elif isinstance(item, list):
            result = item
        else:
            result = [item]
        return result

    l_hierarchy: dict = defaultdict(dict)
    for l_item in source:
        add_to_hierarchy(hierarchy=l_hierarchy,
                         keys=l_item[:-1],
                         value=l_item[-1])

    return convert_to_list(item=l_hierarchy)


def list_stringify(source: list) -> str:
    """
    Return a string with the items from *source* listed as *[<i1>, ..., <in>]*.

    The *stringification* is done recursively, with *dict* and *list* as values handled accordingly.

    :param source: the source *list*
    :return: the string listing the items in *source*
    """
    from .dict_pomes import dict_stringify

    # initialize the return variable
    result: str = "["

    if source:
        # traverse the source 'list'
        for item in source:
            if isinstance(item, dict):
                result += f"{dict_stringify(source=item)}"
            elif isinstance(item, list):
                result += f"{list_stringify(source=item)}"
            elif isinstance(item, str):
                result += f"'{item}'"
            else:
                result += f"{item}"
            result += ", "
        result = result[:-2]

    return result + "]"
