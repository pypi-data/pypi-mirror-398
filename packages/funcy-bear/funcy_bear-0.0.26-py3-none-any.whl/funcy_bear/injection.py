"""Dependency Injection framework for Funcy Bear."""

from typing import TYPE_CHECKING

from lazy_bear import lazy

if TYPE_CHECKING:
    from funcy_bear.context.di.container import DeclarativeContainer
    from funcy_bear.context.di.plugin_containers import LifecycleContainer, ToolContainer
    from funcy_bear.context.di.plugins import Deleter, Factory, Getter, Setter, ToolContext, inject_tools
    from funcy_bear.context.di.provides import Provide, Provider
    from funcy_bear.context.di.resources import Resource, Singleton
    from funcy_bear.context.di.wiring import inject, parse_params
else:
    DeclarativeContainer = lazy("funcy_bear.context.di.container", "DeclarativeContainer")
    containers = lazy("funcy_bear.context.di.plugin_containers")
    LifecycleContainer, ToolContainer = containers.to("LifecycleContainer", "ToolContainer")
    plugins = lazy("funcy_bear.context.di.plugins")
    Deleter, Factory, Getter, Setter = plugins.to("Deleter", "Factory", "Getter", "Setter")
    ToolContext, inject_tools = plugins.to("ToolContext", "inject_tools")
    Provide, Provider = lazy("funcy_bear.context.di.provides", "Provide", "Provider")
    Resource, Singleton = lazy("funcy_bear.context.di.resources", "Resource", "Singleton")
    inject, parse_params = lazy("funcy_bear.context.di.wiring", "inject", "parse_params")

__all__ = [
    "DeclarativeContainer",
    "Deleter",
    "Factory",
    "Getter",
    "LifecycleContainer",
    "Provide",
    "Provider",
    "Resource",
    "Setter",
    "Singleton",
    "ToolContainer",
    "ToolContext",
    "inject",
    "inject_tools",
    "parse_params",
]
