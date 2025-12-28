__all__ = [
    'AbstractNodeWrapper',
    'generate_wrapper', 'composite_markup',
    'validate', 'getter', 'modifier'
]

from ._decorator import MethodType, NodeWrapperDecorator
from ._interface import AbstractNodeWrapper

generate_wrapper = NodeWrapperDecorator.generate_wrapper
composite_markup = NodeWrapperDecorator.composite_markup
validate = NodeWrapperDecorator.validate
post_process = NodeWrapperDecorator.post_process

getter = NodeWrapperDecorator.set_method_type(MethodType.getter)
modifier = NodeWrapperDecorator.set_method_type(MethodType.modifier)
