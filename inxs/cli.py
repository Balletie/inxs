# TODO error handling
# TODO documentation
# TODO tests
# TODO allow passing arguments


from argparse import ArgumentParser
from traceback import print_exc
import importlib.util
import logging
from pathlib import Path
from shutil import copy2 as copy_file
import sys

from lxml import etree

from inxs import Transformation
from inxs.lib import logger


console_log_handler = logging.StreamHandler(sys.stdout)
console_log_handler.setLevel(logging.DEBUG)
logger.addHandler(console_log_handler)
logger.setLevel(logging.DEBUG)


def parse_args():
    parser = ArgumentParser()

    parser.add_argument('transformation')
    parser.add_argument('target')

    return parser.parse_args()


def get_transformation(location: str):
    if ':' in location:
        module_path, transformation_name = location.split(':')
    else:
        module_path, transformation_name = location, None

    if not module_path.endswith('.py'):
        module_path += '.py'
    module_path = (Path.cwd() / module_path).resolve()

    module_spec = importlib.util.spec_from_file_location('transformation_file', module_path)
    _module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(_module)

    transformation_objects = {k: v for k, v in vars(_module).items()
                              if isinstance(v, Transformation)}

    if transformation_name is None:
        if 'main' in transformation_objects:
            return transformation_objects['main']
        else:
            return next(x for x in transformation_objects.values())

    for obj in transformation_objects.values():
        if obj.name == transformation_name:
            return obj

    return transformation_objects[transformation_name]


def apply_transformation(transformation: Transformation, target: str):
    document = etree.parse(target)
    copy_file(target, target + '.orig')
    root = transformation(document.getroot())
    document._setroot(root)
    document.write(target,
                   encoding='utf-8',  # TODO obtain options from source
                   xml_declaration=True)


def main():
    try:
        args = parse_args()
        transformation = get_transformation(args.transformation)
        apply_transformation(transformation, args.target)
    except Exception as e:
        print_exc(e)
        raise SystemExit(2)


if __name__ == '__main__':
    main()


__all__ = []
