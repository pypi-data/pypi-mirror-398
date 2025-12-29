from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar
from collections.abc import Mapping, Sequence


class ResourceType(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def dependencies(self) -> Sequence[ResourceType]: ...


@dataclass(frozen=True)
class ResourceConfig:
    name: str
    spec: Any


class ResourceInstance:
    def __init__(self, resource_service: ResourceService, name: str, state: Any) -> None:
        self._resource_service = resource_service
        self.resource_type: ResourceType = resource_service.resource_type
        self.name: str = name
        self.state: Any = state

    async def delete(self) -> None:
        await self._resource_service.delete([self])

    def to_json(self) -> str:
        import json

        return json.dumps({"name": self.name, "state": self.state}, default=str)


SPEC = TypeVar("SPEC")
STATE = TypeVar("STATE")


class Resource(Generic[SPEC, STATE]):
    @property
    def actual_instance(self) -> ResourceInstance: ...

    @property
    def state(self) -> Any: ...


class Resource_:
    def __init__(self, expected: ResourceConfig, actual: list[ResourceInstance]):
        if not actual:
            raise ValueError("Resource为非惰性资源，创建Resource必须提供对应云上实例")
        for inst in actual:
            if expected.name != inst.name:
                raise ValueError(f"expected.name({expected.name})必须和实际资源实例的name({inst.name})一致")
        self._expected = expected
        self._actual = actual

    @property
    def spec(self) -> Any:
        return self._expected.spec

    @property
    def name(self) -> str:
        return self._expected.name

    @property
    def actual_instance(self) -> ResourceInstance:
        if len(self._actual) != 1:
            details = ",".join(inst.to_json() for inst in self._actual)
            raise RuntimeError(f"正常资源应该对应云上1个云上实际实例，但现在有{len(self._actual)}个,请检查:{details}")
        return self._actual[0]

    @property
    def state(self) -> Any:
        return self.actual_instance.state


class ResourceService:
    @property
    def resource_type(self) -> ResourceType:
        raise NotImplementedError

    async def create(self, config: ResourceConfig) -> ResourceInstance:
        raise NotImplementedError

    async def delete(self, instances: Sequence[ResourceInstance]) -> None:
        raise NotImplementedError

    async def load(self, config: ResourceConfig) -> list[ResourceInstance]:
        raise NotImplementedError


class ResourceServices:
    def __init__(self) -> None:
        self._services: dict[str, ResourceService] = {}

    def register(self, service: ResourceService) -> None:
        self._services[service.resource_type.name] = service

    @property
    def services(self) -> Mapping[str, ResourceService]:
        return self._services


class Provider:
    def __init__(self) -> None:
        self.resource_services = ResourceServices()

    async def find_resource_instances(self) -> list[ResourceInstance[Any]]:
        raise NotImplementedError


class Vendor:
    def __init__(self, provider: Provider) -> None:
        self._provider = provider
        self._resource_services: ResourceServices = provider.resource_services
        self._resources: dict[str, list[Resource]] = {}
        self._resource_instances: list[ResourceInstance] = []

    @classmethod
    def _create(cls, provider: Provider) -> Vendor:
        return cls(provider)

    @property
    def resource_services(self) -> ResourceServices:
        return self._resource_services

    @property
    def resource_instances(self) -> list[ResourceInstance[Any]]:
        return self._resource_instances

    def sorted_resource_types(self) -> list[ResourceType]:
        # Keep insertion order; no complex topo sort for now
        return [svc.resource_type for svc in self._resource_services.services.values()]

    async def refresh(self) -> None:
        self._resource_instances = await self._provider.find_resource_instances()

    async def cleanup(self) -> None:
        # noop in core; providers can override behavior via up()
        return None

    async def down(self) -> None:
        # Best-effort delete by resource type order reversed
        # Group by resource type
        by_type: dict[str, list[ResourceInstance]] = {}
        for inst in self._resource_instances:
            by_type.setdefault(inst.resource_type.name, []).append(inst)
        for type_name in reversed(list(by_type.keys())):
            svc = self._resource_services.services.get(type_name)
            if not svc:
                continue
            await svc.delete(by_type[type_name])

    async def up(self, resource_type: ResourceType, expected: ResourceConfig):
        svc = self._resource_services.services.get(resource_type.name)
        if not svc:
            raise KeyError(f"No service for resource type: {resource_type.name}")
        actual = await svc.load(expected)
        if not actual:
            one = await svc.create(expected)
            actual = [one]
        # record resource
        res = Resource_(expected, actual)
        self._resources.setdefault(resource_type.name, []).append(res)
        return res


class Vendors(list[Vendor]):
    @classmethod
    def _create(cls) -> Vendors:
        return cls()

    def register(self, provider: Provider) -> Vendor:
        vendor = Vendor._create(provider)
        self.append(vendor)
        return vendor


class Project:
    def __init__(self, name: str) -> None:
        self.vendors: Vendors = Vendors._create()
        self.name = name

    @classmethod
    def of(cls, config: dict[str, Any]) -> Project:
        return cls(name=config["name"])

    @property
    def resource_instances(self) -> list[ResourceInstance[Any]]:
        return [inst for v in self.vendors for inst in v.resource_instances]

    @property
    def resources(self) -> list[Resource[Any, Any]]:
        return [r for v in self.vendors for rs in v._resources.values() for r in rs]

    async def up(self, up_func: callable) -> None:
        await self.refresh()
        await up_func(self)
        for v in self.vendors:
            await v.cleanup()

    async def refresh(self) -> None:
        for v in self.vendors:
            await v.refresh()

    async def down(self) -> None:
        # delete in registration reverse order
        for v in self.vendors[::-1]:
            await v.down()


__all__ = [
    "ResourceType",
    "ResourceConfig",
    "ResourceInstance",
    "Resource",
    "Resource_",
    "ResourceService",
    "ResourceServices",
    "Provider",
    "Vendor",
    "Vendors",
    "Project",
]
