# qpa_core.py
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import (
    Any,
    Generic,
    TypeVar,
)
from collections.abc import Awaitable, Callable, Iterable, Sequence

from ._common import _topo_sort

# Type variables for generic specs and state
SPEC = TypeVar("SPEC")
STATE = TypeVar("STATE")


###############################################################################
# Resource & Config definitions
###############################################################################


@dataclass(frozen=True)
class ResourceConfig(Generic[SPEC]):
    """The desired configuration of a resource (the desired state)."""

    name: str
    spec: SPEC


class ResourceType(ABC):
    """ResourceType acts as an identity & dependency provider for a resource category.
    Concrete implementations must provide `name` and `dependencies`.
    """

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def dependencies(self) -> Sequence[ResourceType]: ...

    # For using instances as keys in dict / set, we use object identity by default.
    # If implementors want value-equality, they should implement __hash__ and __eq__.


class ResourceInstance(Generic[STATE]):
    """Actual resource instance discovered/created in cloud.
    - holds provider-specific state (STATE)
    - delegates delete action to owning ResourceService
    """

    def __init__(self, resource_service: ResourceService[Any, STATE], name: str, state: STATE) -> None:
        self._resource_service = resource_service
        self.name = name
        self.state = state
        self.resource_type = resource_service.resource_type

    async def delete(self) -> None:
        # delete by delegating to the service
        await self._resource_service.delete([self])

    def to_json(self) -> str:
        import json

        # Attempt to JSON-serialize, fall back to repr for non-serializable fields
        try:
            return json.dumps({"name": self.name, "state": self.state}, default=repr, ensure_ascii=False)
        except Exception:
            return repr({"name": self.name, "state": self.state})


class Resource(Generic[SPEC, STATE], ABC):
    @property
    @abstractmethod
    def actual_instance(self) -> ResourceInstance[STATE]: ...

    @property
    @abstractmethod
    def state(self) -> STATE: ...


###############################################################################
# Concrete "complete" Resource class (Resource_)
###############################################################################


class Resource_(Resource[SPEC, STATE]):
    """A complete managed resource: expected config + one-or-more actual instances (normally 1).
    Raises when no actual instances are provided.
    """

    def __init__(self, expected: ResourceConfig[SPEC], actual: Sequence[ResourceInstance[STATE]]) -> None:
        if len(actual) == 0:
            raise ValueError("Resource is not lazy: creating Resource requires at least one actual instance")
        for inst in actual:
            if inst.name != expected.name:
                raise ValueError(f"expected.name({expected.name}) must equal actual instance name({inst.name})")
        self._expected = expected
        self._actual: list[ResourceInstance[STATE]] = list(actual)

    @property
    def spec(self) -> SPEC:
        return self._expected.spec

    @property
    def name(self) -> str:
        return self._expected.name

    @property
    def actual_instance(self) -> ResourceInstance[STATE]:
        if len(self._actual) != 1:
            raise ValueError(
                f"Normal resource should have exactly 1 actual instance; found {len(self._actual)}: "
                f"{[i.to_json() for i in self._actual]}"
            )
        return self._actual[0]

    @property
    def state(self) -> STATE:
        return self.actual_instance.state


###############################################################################
# Project / Vendor / Provider / ResourceService / ResourceServices
###############################################################################


@dataclass
class ProjectConfig:
    name: str


UpFunc = Callable[["Project"], Awaitable[None]]


class ResourceServices(dict[ResourceType, "ResourceService[Any, Any]"]):
    """Map ResourceType -> ResourceService"""

    def register(self, service: ResourceService[Any, Any]) -> None:
        t = service.resource_type
        if t in self:
            raise RuntimeError(f"resource service[{t}] already registered")
        self[t] = service


class Provider(ABC):
    """Stateless provider SPI. Provider implementations supply:
    - find_resource_instances(): current actual instances within the scope
    - a ResourceServices registry (for creation/load/delete of resource types)
    """

    def __init__(self) -> None:
        self.resource_services: ResourceServices = ResourceServices()

    @abstractmethod
    async def find_resource_instances(self) -> list[ResourceInstance[Any]]:
        """Query all existing resource instances under this provider's scope.
        Should return a list of ResourceInstance objects (stateful).
        """
        ...


class _ResourceInstances(list[ResourceInstance[Any]]):
    """Specialized list with convenience delete-by-instance method."""

    def delete(self, instance: ResourceInstance[Any]) -> None:
        try:
            self.remove(instance)
        except ValueError:
            pass


class Vendor:
    """Vendor composes a Provider to maintain stateful collections:
      - _resource_instances: current actual resource instances discovered
      - _resources: declared Resource_ instances
    Implements refresh(), cleanup(), down(), up() as in TS code.
    """

    def __init__(self, provider: Provider) -> None:
        self._provider = provider
        self._resource_instances: _ResourceInstances = _ResourceInstances()
        self._resources: dict[str, Resource_[Any, Any]] = {}
        self._sorted_resource_types_cache: list[ResourceType] | None = None

    @property
    def resource_services(self) -> ResourceServices:
        return self._provider.resource_services

    @property
    def resource_instances(self) -> Sequence[ResourceInstance[Any]]:
        return tuple(self._resource_instances)

    @staticmethod
    def _create(provider: Provider) -> Vendor:
        return Vendor(provider)

    @property
    def sorted_resource_types(self) -> list[ResourceType]:
        if self._sorted_resource_types_cache is None:
            resource_type_dependencies: dict[ResourceType, Sequence[ResourceType]] = {}
            for t in self.resource_services.keys():
                resource_type_dependencies[t] = list(t.dependencies)
            self._sorted_resource_types_cache = _topo_sort(resource_type_dependencies)
        return self._sorted_resource_types_cache

    async def refresh(self) -> None:
        instances = await self._provider.find_resource_instances()
        self._resource_instances = _ResourceInstances(*instances)

    async def cleanup(self) -> None:
        # Refresh first
        await self.refresh()
        undeclared = [inst for inst in self._resource_instances if inst.name not in self._resources]
        await self._remove_resource_instances(undeclared)

    async def down(self) -> None:
        await self.refresh()
        safe_copy = list(self._resource_instances)
        await self._remove_resource_instances(safe_copy)
        self._resources.clear()

    async def _remove_resource_instances(self, instances: Iterable[ResourceInstance[Any]]) -> None:
        instances_list = list(instances)
        unique_types_to_delete: set[ResourceType] = set(inst.resource_type for inst in instances_list)

        # Filter sorted types and keep order (topo_sort returns deps before dependents),
        # We want to delete dependents before dependencies => reverse order
        deletion_order_types = [t for t in reversed(self.sorted_resource_types) if t in unique_types_to_delete]

        for type_to_delete in deletion_order_types:
            instances_of_type = [i for i in instances_list if i.resource_type is type_to_delete]
            print(f"--- Deleting {type_to_delete} resources: {len(instances_of_type)} ---")
            for inst in instances_of_type:
                print(f"Deleting instance: {inst.name} (type: {type_to_delete})")
                await inst.delete()
                self._resource_instances.delete(inst)
                print(f"Deleted instance: {inst.name} (type: {type_to_delete})")
        print("All specified resources deleted.")

    async def up(self, resource_type: ResourceType, expected: ResourceConfig[SPEC]) -> Resource_[SPEC, STATE]:
        service = self.resource_services.get(resource_type)
        if service is None:
            raise RuntimeError(f"No resource service registered for type {resource_type}")

        actual = await service.load(expected)
        if len(actual) == 0:
            actual = [await service.create(expected)]

        if len(actual) == 0:
            raise RuntimeError(f"bug: resource {expected.name} should not have 0 actual instances after create/load")

        if len(actual) > 1:
            raise RuntimeError(
                f"Duplicate/Conflicting resources for name {expected.name}: {[a.to_json() for a in actual]}"
            )

        result = Resource_(expected, actual)
        self._resources[result.name] = result
        self._resource_instances.extend(actual)
        return result


###############################################################################
# Vendors collection & Project
###############################################################################


class Vendors(list[Vendor]):
    @staticmethod
    def _create() -> Vendors:
        return Vendors()

    def register(self, provider: Provider) -> Vendor:
        v = Vendor._create(provider)
        self.append(v)
        return v


class Project:
    def __init__(self, config: ProjectConfig) -> None:
        self.name = config.name
        self.vendors: Vendors = Vendors._create()

    @staticmethod
    def of(config: ProjectConfig) -> Project:
        return Project(config)

    @property
    def resource_instances(self) -> list[ResourceInstance[Any]]:
        return [ri for v in self.vendors for ri in v.resource_instances]

    @property
    def resources(self) -> list[Resource_[Any, Any]]:
        return [r for v in self.vendors for r in v._resources.values()]

    async def up(self, up_fn: UpFunc) -> None:
        await self.refresh()
        await up_fn(self)
        # cleanup
        for vendor in self.vendors:
            await vendor.cleanup()

    async def refresh(self) -> None:
        for vendor in self.vendors:
            await vendor.refresh()

    async def down(self) -> None:
        for vendor in self.vendors:
            await vendor.down()


###############################################################################
# Abstract ResourceService
###############################################################################


class ResourceService(Generic[SPEC, STATE], ABC):
    @property
    @abstractmethod
    def resource_type(self) -> ResourceType: ...

    @abstractmethod
    async def create(self, config: ResourceConfig[SPEC]) -> ResourceInstance[STATE]: ...

    @abstractmethod
    async def delete(self, instances: Sequence[ResourceInstance[STATE]]) -> None: ...

    @abstractmethod
    async def load(self, config: ResourceConfig[SPEC]) -> list[ResourceInstance[STATE]]: ...


###############################################################################
# Minimal runnable example (mocks)
###############################################################################

if __name__ == "__main__":
    # Provide a small demo to show usage.
    class SimpleType(ResourceType):
        def __init__(self, name: str, deps: list[ResourceType] | None = None):
            self._name = name
            self._deps = deps or []

        @property
        def name(self) -> str:
            return self._name

        @property
        def dependencies(self) -> Sequence[ResourceType]:
            return self._deps

        def __repr__(self):
            return f"SimpleType({self._name})"

        # by default object identity used for hashing; that's acceptable for demo

    class MockResourceService(ResourceService[dict, dict]):
        def __init__(self, resource_type: ResourceType):
            self._type = resource_type
            # in-memory store of instances by name
            self._store: dict[str, ResourceInstance[dict]] = {}

        @property
        def resource_type(self) -> ResourceType:
            return self._type

        async def create(self, config: ResourceConfig[dict]) -> ResourceInstance[dict]:
            state = {"created": True, "spec": config.spec}
            inst = ResourceInstance(self, config.name, state)
            self._store[config.name] = inst
            print(f"[MockService] Created {config.name}")
            return inst

        async def delete(self, instances: Sequence[ResourceInstance[dict]]) -> None:
            for inst in instances:
                if inst.name in self._store:
                    del self._store[inst.name]
                    print(f"[MockService] Deleted {inst.name}")
                else:
                    print(f"[MockService] Instance {inst.name} not found")

        async def load(self, config: ResourceConfig[dict]) -> list[ResourceInstance[dict]]:
            inst = self._store.get(config.name)
            return [inst] if inst else []

    class MockProvider(Provider):
        def __init__(self):
            super().__init__()
            # register a resource service for SimpleType("vm")
            self.vm_type = SimpleType("vm")
            self.net_type = SimpleType("net")
            self.resource_services.register(MockResourceService(self.vm_type))
            self.resource_services.register(MockResourceService(self.net_type))
            # We'll keep instances in the services' stores (as seen above)

        async def find_resource_instances(self) -> list[ResourceInstance[Any]]:
            # Aggregate all instances from registered services
            res: list[ResourceInstance[Any]] = []
            for srv in self.resource_services.values():
                # access protected store for demo (not ideal in production)
                store = getattr(srv, "_store", {})
                res.extend(store.values())
            return res

    async def demo():
        # Build project and provider
        project = Project.of(ProjectConfig(name="demo"))
        provider = MockProvider()
        vendor = project.vendors.register(provider)

        # create a resource via vendor.up
        vm_type = provider.vm_type
        await vendor.up(vm_type, ResourceConfig(name="vm-1", spec={"cpu": 2}))
        # show resources
        print("Resources after up:", [r.name for r in vendor._resources.values()])

        # now call down (delete everything)
        await vendor.down()
        print("Resource instances after down:", vendor.resource_instances)

    asyncio.run(demo())
