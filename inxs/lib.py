from typing import Callable

from lxml import builder

from inxs.xml_utils import is_root_element, remove_element


def drop_siblings(left_or_right):
    """ Removes all elements left or right of the processed element depending which keyword was given.
        The same is applied to all ancestors. Think of it like cutting a hedge from one side.
    """
    if left_or_right == 'left':
        preceding = True
    elif left_or_right == 'right':
        preceding = False
    else:
        raise RuntimeError("'left_or_right' must be 'left' or …")

    def processor(element):
        if is_root_element(element):
            return

        for sibling in element.itersiblings(preceding=preceding):
            remove_element(sibling)

        parent = element.getparent()
        if parent is not None:
            processor(parent)
    return processor


def has_tail(element, _) -> bool:
    """ Returns whether the element has a tail. """
    return bool(element.tail)


def resolve_xpath_to_element(*names):
    """ Resolves the objects from the context (which are supposed to be XPath expressions) referenced by ``names`` with
        the *one* element that the XPaths yield or ``None``. This is useful when a copied tree is processed and it hence
        makes no sense to pass Element objects to a transformation.
    """
    def resolver(element, transformation):
        context = transformation.context
        for name in names:
            xpath = getattr(context, name)
            if not xpath:
                setattr(context, name, None)
                continue
            resolved_elements = transformation.xpath_evaluator(xpath)
            if not resolved_elements:
                setattr(context, name, None)
            elif len(resolved_elements) == 1:
                setattr(context, name, resolved_elements[0])
            else:
                raise RuntimeError('More than one element matched {}'.format(xpath))
    return resolver


def set_elementmaker(name: str = 'e', **kwargs):
    """ Adds a :class:`lxml.builder.ElementMaker` with as ``name`` to the context. ``kwargs`` for its initialization
        can be passed.
    """
    if 'namespace' in kwargs and 'nsmap' not in kwargs:
        kwargs['nsmap'] = {None: kwargs['namespace']}

    def wrapped(context):
        setattr(context, name, builder.ElementMaker(**kwargs))
    return wrapped


def sorter(object_name: str, key: Callable):
    """ Sorts the object referenced by ``name`` using ``key``. """
    def wrapped(transformation):
        return sorted(transformation._available_dependencies[object_name], key=key)
    return wrapped
