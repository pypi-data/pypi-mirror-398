"""Define some utils relative to larch"""

from larch.symboltable import Group


def group_to_dict(group):
    """Convert the larch group to a serializable dictionary

    :param group: the group to convert to a serializable dictionary
    :type: larch.symboltable.Group
    :returns: dictionary corresponding to the given larch.symboltable.Group
    :rtype: dictionary
    """
    res = {}
    for key in group._members():
        if isinstance(group._members()[key], Group):
            res[key] = group_to_dict(group._members()[key])
        else:
            res[key] = group._members()[key]
    return res


def dict_to_group(dict_, group):
    """Update the given larch group with the content of the dictionary

    :param dict_:
    :type: dict
    :param group:
    :type: larch.symboltable.Group
    """
    for key in dict_:
        group._members()[key] = dict_[key]
