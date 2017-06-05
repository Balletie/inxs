from typing import Callable

from lxml import builder, etree

from inxs.xml_utils import is_root_element, remove_element


def cleanup_namespaces(root):
    """ Cleanup the namespaces of the root element. """
    etree.cleanup_namespaces(root)


def concatenate(*parts):
    """ Concatenate the given parts which may be strings or callables returning such. """
    def evaluator(transformation):
        result = ''
        for part in parts:
            if callable(part):
                _part = part(transformation)
            elif isinstance(part, str):
                _part = part
            else:
                raise RuntimeError(f'Unhandled type: {type(part)}')
            result += _part
        return result
    return evaluator


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


def f(func, *args, **kwargs):
    """ Wraps the callable ``func`` which will be called as ``func(element, *args, **kwargs)``. """
    def wrapper(element):
        return func(element, *args, **kwargs)
    return wrapper


def get_attribute(name):
    """ Gets the value of the element's attribute named ``name``. """
    def evaluator(element):
        return element.attrib.get(name)
    return evaluator


def get_localname(element):
    """ Gets the element's local tag name. """
    return etree.QName(element).localname


def has_tail(element, _) -> bool:
    """ Returns whether the element has a tail. """
    return bool(element.tail)


def lowercase(previous_result):
    """ Processes ``previous_result`` to be all lower case. """
    return previous_result.lower()


def pop_attribute(name):
    """ Pops the element's attribute named ``name``. """
    def handler(element):
        return element.attrib.pop(name)
    return handler


def put_variable(name):
    """ Puts the ``previous_result`` as ``name`` to the context namespace. """
    def handler(context, previous_result):
        setattr(context, name, previous_result)
    return handler


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


def set_localname(name):
    """ Sets the element's localname to ``name``. """
    def handler(element):
        element.tag = etree.QName(element, name).text
    return handler


def sorter(object_name: str, key: Callable):
    """ Sorts the object referenced by ``name`` using ``key``. """
    def wrapped(transformation):
        return sorted(transformation._available_dependencies[object_name], key=key)
    return wrapped


def strip_attributes(*names):
    """ Strips all attributes with the keys provided as ``names`` from the element. """
    def handler(element):
        for name in names:
            element.attrib.pop(name)
    return handler


def strip_namespace(element):
    """ Removes the namespace from the element.
        When used, :func:`cleanup_namespaces` should be applied at the end of the transformation.
    """
    element.tag = etree.QName(element).localname
