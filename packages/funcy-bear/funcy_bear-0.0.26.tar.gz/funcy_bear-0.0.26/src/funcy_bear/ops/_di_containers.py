from funcy_bear.context.di.plugin_containers import FactoryContainerBase, ToolContainer
from funcy_bear.context.di.plugins import Deleter, Factory, Getter, Setter, ToolContext
from funcy_bear.context.di.resources import Singleton


class CurryingContainer(ToolContainer):
    """A container for the Ops services."""

    getter: Singleton[Getter] = Singleton(Getter)
    setter: Singleton[Setter] = Singleton(Setter)
    deleter: Singleton[Deleter] = Singleton(Deleter)
    ctx: Singleton[ToolContext] = Singleton(ToolContext, getter=getter, setter=setter, deleter=deleter)


class FactoryContainer(FactoryContainerBase):
    """A container for the Factory service."""

    getter: Singleton[Getter] = Singleton(Getter)
    setter: Singleton[Setter] = Singleton(Setter)
    deleter: Singleton[Deleter] = Singleton(Deleter)
    factory: Singleton[Factory] = Singleton(Factory)
