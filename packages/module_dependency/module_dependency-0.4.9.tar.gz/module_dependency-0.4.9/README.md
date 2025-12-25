# module-dependency

A Dependency Injection Framework for Modular Embedded Python Applications.

## Overview

The goal of this project is to provide a comprehensive framework for managing structure for complex Python applications. The framework is designed to be modular, allowing developers to define components, interfaces, and instances that can be easily managed and injected throughout the application.

Declare components with interfaces, provide multiple implementations of them, and manage which implementation to use at runtime. Multiple components can be organized and composed together to form complex behaviors using modular design principles.

This repository includes a working example of a simple application that demonstrates these concepts in action. Based on a real-world use case, the example showcases how to effectively manage dependencies and implement modular design patterns in an embedded Python environment.

## Install

This project is available on PyPI on [module_dependency](https://pypi.org/project/module_dependency/). It can be installed using pip:

```bash
pip install module-dependency
```

## Core Components

The project is built around three components that implement different aspects of dependency management:

### 1. Module
- Acts as a container for organizing and grouping related dependencies
- Facilitates modular design and hierarchical structuring of application components

```python
from dependency.core import Module, module
from ...plugin.........module import ParentModule

@module(
    module=ParentModule,  # Declares the parent module (leave empty for plugins)
)
class SomeModule(Module):
    """This is a module class. Use this to group related components.
    """
    pass
```

### 2. Component
- Defines abstract interfaces or contracts for dependencies
- Promotes loose coupling and enables easier testing and maintenance

```python
from abc import ABC, abstractmethod
from dependency.core import Component, component
from ...plugin.........module import SomeModule

class SomeService(ABC):
    """This is the interface for a new component.
    """
    @abstractmethod
    def method(self, ...) -> ...:
        pass

@component(
    module=SomeModule,     # Declares the module or plugin this component belongs to
    interface=SomeService, # Declares the interface used by the component
)
class SomeServiceComponent(Component):
    """This is the component class. A instance will be injected here.
       Components are only started when provided or bootstrapped.
    """
    pass
```

### 3. Instance
- Delivers concrete implementations of Components
- Manages the lifecycle and injection of dependency objects

```python
from dependency_injector.wiring import inject
from dependency.core import instance, providers
from dependency.core.injection import LazyProvide
from ...plugin.........component import SomeService, SomeServiceComponent
from ...plugin...other_component import OtherService, OtherServiceComponent
from ...plugin...........product import SomeProduct

@instance(
    component=SomeServiceComponent, # Declares the component to be provided
    imports=[OtherService, ...],    # List of dependencies (components) that are needed
    products=[SomeProduct, ...],    # List of products that this instance will create
    provider=providers.Singleton,   # Provider type (Singleton, Factory)
    bootstrap=False,                # Whether to bootstrap on application start
)
class ImplementedSomeService(SomeService):
    """This is a instance class. Here the component is implemented.
       Instances are injected into the respective components when provided.
    """
    def __init__(self) -> None:
        """Init method will be called when the instance is started.
           This will happen once for singleton and every time for factories.
        """
        # Once declared, i can use the dependencies for the class
        self.dependency: OtherService = OtherServiceComponent.provide()

    @inject
    def method(self,
        # Dependencies also can be provided using @inject decorator with LazyProvide
        # With @inject always use LazyProvide, to avoid deferred evaluation issues.
        dependency: OtherService = LazyProvide(OtherServiceComponent.reference),
    ...) -> ...:
        """Methods declared in the interface must be implemented.
        """
        # Once declared, i can safely create any product
        # Products are just normal classes (see next section)
        product = SomeProduct()

        # You can do anything here
        do_something()
```

These components work together to create a powerful and flexible dependency injection system, allowing for more maintainable and testable Python applications.

## Extra Components

The project has additional components that enhance its functionality and organization. These components include:

### 1. Entrypoint
- Represents a entrypoint for the application
- Responsible for initializing and starting the application

```python
from dependency.core import Entrypoint, Container
from ...plugin...... import SomePlugin

class SomeApplication(Entrypoint):
    """This is an application entry point.
       Plugins included here will be loaded and initialized.
    """
    def __init__(self) -> None:
        # Import all the instances that will be used on the application
        # You can apply some logic to determine which instances to import
        # This will automatically generate the internal provider structure
        import ...plugin.........instance

        # Declare all the plugins that will be used in the application
        # Its recommended to declare the plugins list them in a separate file
        # You can also include in the same file all the instances imports
        PLUGINS = [
            SomePlugin,
            ...
        ]

        # This is the main container, it will hold all the containers and providers
        # Requires to have a valid configuration that will be used to initialize plugins
        container = Container.from_dict(config={...}, required=True)
        super().__init__(container, PLUGINS)
```

### 2. Plugin
- Represents a special module that can be included in the application
- Provides additional functionality and features to the application

```python
from pydantic import BaseModel
from dependency.core import Plugin, PluginMeta, module

class SomePluginConfig(BaseModel):
    """Include configuration options for the plugin.
    """
    pass

@module()
class SomePlugin(Plugin):
    """This is a plugin class. Plugins can be included in the application.
       Plugins are modules that provide additional functionality.
    """
    # Meta information about the plugin (only affects logging)
    meta = PluginMeta(name="SomePlugin", version="0.0.1")

    # Type hint for the plugin configuration
    # On startup, config will be instantiated using the container config
    config: SomePluginConfig
```

### 3. Product
- Represents a class that requires dependencies injected from the framework
- Allows to provide standalone classes without the need to define new providers

```python
from dependency.core import Product, product, providers
from dependency.core.injection import LazyProvide
from ...plugin.........component import SomeService, SomeServiceComponent
from ...plugin.....other_product import OtherProduct

@product(
    imports=[SomeServiceComponent, ...], # List of dependencies (components) that are needed
    products=[OtherProduct, ...],        # List of products that this product will create
    provider=providers.Singleton,        # Provider type (Singleton, Factory)
)
class SomeProduct(Interface, Product):
    """This is the product class. This class will check for its dependencies.
       Products must be declared in some instance and can be instantiated as normal classes.
    """
    def __init__(self, ...) -> None:
        # Dependencies can be used in the same way as before
        self.dependency: SomeService = SomeServiceComponent.provide()

    @inject
    def method(self,
        # Dependencies also can be provided using @inject decorator with LazyProvide
        # With @inject always use LazyProvide, to avoid deferred evaluation issues.
        dependency: SomeService = LazyProvide(SomeServiceComponent.reference),
    ...) -> ...:
        """Product interface can be defined using normal inheritance.
        """
        # Once declared, i can safely create any sub-product
        # Products are just normal classes (see next section)
        product = OtherProduct()

        # You can do anything here
        do_something()
```

## Important Notes

- Declare all the dependencies (components) on Instances and Products to avoid injection issues.
- Read the documentation carefully and refer to the examples to understand the framework's behavior.

## Usage Examples

This repository includes a practical example demonstrating how to use the framework. You can find this example in the `example` directory. It showcases the implementation of the core components and how they interact to manage dependencies effectively in a sample application.

This example requires the `module-injection` package to be installed and the `library` folder to be present in the project root.

## Future Work

This project is a work in progress, and there are several improvements and enhancements planned for the future.

Some planned features are:
- Enhance documentation and examples for better understanding
- Implement framework API and extension points for customization
- Improve injection resolution and initialization process
- Provide injection scopes and strategies for flexibility
- Testing framework integration for better test coverage
- Visualization tools for dependency graphs and relationships

Some of the areas that will be explored in the future include:
- Add some basic components and plugins for common use cases
- Dependency CLI support for easier interaction with the framework
- Explore more advanced dependency injection patterns and use cases
- Improve testing and validation for projects using this framework

Pending issues that eventually will be addressed:
- Class Decorator are not being properly type checked by mypy and other type checkers
- Migration guide from previous versions (some breaking changes were introduced)

## Aknowledgements

This project depends on:
- [dependency-injector](https://python-dependency-injector.ets-labs.org/introduction/di_in_python.html) a robust and flexible framework for dependency injection in Python.
- [pydantic](https://docs.pydantic.dev/latest/) a data validation and settings management library using Python type annotations.
- [jinja2](https://jinja.palletsprojects.com/) a modern and designer-friendly templating engine for Python.

Thanks to [Reite](https://reite.cl/) for providing inspiration and guidance throughout the development of this project.
