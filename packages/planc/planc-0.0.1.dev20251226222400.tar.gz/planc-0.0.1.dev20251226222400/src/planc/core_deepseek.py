from __future__ import annotations
from typing import TypeVar, Generic, Protocol, runtime_checkable, Any
from abc import ABC, abstractmethod
import json
from ._common import _topo_sort

# 类型变量定义
SPEC = TypeVar("SPEC")
STATE = TypeVar("STATE")


class ResourceInstance(Generic[STATE]):
    """实际资源实例，包含状态信息"""

    def __init__(self, resource_service: ResourceService[Any, STATE], name: str, state: STATE):
        self._resource_service = resource_service
        self.resource_type = resource_service.resource_type
        self.name = name
        self.state = state

    async def delete(self) -> None:
        """删除资源实例"""
        await self._resource_service.delete([self])

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps({"name": self.name, "state": self.state})


class ResourceConfig(Generic[SPEC]):
    """资源配置，定义期望状态"""

    def __init__(self, name: str, spec: SPEC):
        self.name = name
        self.spec = spec


@runtime_checkable
class ResourceType(Protocol):
    """资源类型协议"""

    @property
    def name(self) -> str:
        """资源类型名称"""
        ...

    @property
    def dependencies(self) -> list[ResourceType]:
        """依赖的资源类型"""
        ...


class Resource(Generic[SPEC, STATE]):
    """完整的受管理资源接口"""

    @property
    def name(self) -> str:
        """资源名称"""
        ...

    @property
    def spec(self) -> SPEC:
        """资源配置规格"""
        ...

    @property
    def actual_instance(self) -> ResourceInstance[STATE]:
        """实际资源实例"""
        ...

    @property
    def state(self) -> STATE:
        """资源状态"""
        ...


class Resource_(Resource[SPEC, STATE]):
    """完整的受管理资源实现"""

    def __init__(self, expected: ResourceConfig[SPEC], actual: list[ResourceInstance[STATE]]):
        if not actual:
            raise ValueError("Resource为非惰性资源，创建Resource必须提供对应云上实例")

        for instance in actual:
            if expected.name != instance.name:
                raise ValueError(f"expected.name({expected.name})必须和实际资源实例的name({instance.name})一致")

        self._expected = expected
        self._actual = actual

    @property
    def spec(self) -> SPEC:
        return self._expected.spec

    @property
    def name(self) -> str:
        return self._expected.name

    @property
    def actual_instance(self) -> ResourceInstance[STATE]:
        if len(self._actual) != 1:
            instances_json = [instance.to_json() for instance in self._actual]
            raise ValueError(
                f"正常资源应该对应云上1个云上实际实例，但现在有{len(self._actual)}个,请检查:{instances_json}"
            )
        return self._actual[0]

    @property
    def state(self) -> STATE:
        return self.actual_instance.state


class ProjectConfig:
    """项目配置"""

    def __init__(self, name: str):
        self.name = name


UpFunc = Any  # 简化定义，实际应为可调用类型


class Vendors(list["Vendor"]):
    """供应商集合"""

    def __init__(self):
        super().__init__()

    @classmethod
    def _create(cls) -> Vendors:
        return cls()

    def register(self, provider: Provider) -> Vendor:
        """注册供应商"""
        result = Vendor._create(provider)
        self.append(result)
        return result


class Project:
    """项目管理器"""

    def __init__(self, config: ProjectConfig):
        self.name = config.name
        self.vendors = Vendors._create()

    @property
    def resource_instances(self) -> list[ResourceInstance[Any]]:
        """获取所有资源实例"""
        return [instance for vendor in self.vendors for instance in vendor.resource_instances]

    @property
    def resources(self) -> list[Resource[Any, Any]]:
        """获取所有资源"""
        return [resource for vendor in self.vendors for resource in vendor._resources.values()]

    @classmethod
    def of(cls, config: ProjectConfig) -> Project:
        """创建项目实例"""
        return cls(config)

    async def up(self, up_func: UpFunc) -> None:
        """配置部署上线"""
        await self.refresh()
        await up_func(self)

        # 清理
        for vendor in self.vendors:
            await vendor.cleanup()

    async def refresh(self) -> None:
        """刷新资源状态"""
        for vendor in self.vendors:
            await vendor.refresh()

    async def down(self) -> None:
        """删除所有资源"""
        for vendor in self.vendors:
            await vendor.down()


class Provider(ABC):
    """无状态服务提供者抽象类"""

    def __init__(self):
        self.resource_services = ResourceServices()

    @abstractmethod
    async def find_resource_instances(self) -> list[ResourceInstance[Any]]:
        """查询资源实例"""
        ...


class _Resources(dict[str, Resource_[Any, Any]]):
    """内部资源字典类"""

    pass


class _ResourceInstances(list[ResourceInstance[Any]]):
    """内部资源实例列表类"""

    def remove_instance(self, instance: ResourceInstance[Any]) -> None:
        """删除指定的资源实例"""
        if instance in self:
            self.remove(instance)


class Vendor:
    """供应商管理器"""

    def __init__(self, provider: Provider):
        self._provider = provider
        self._resource_instances = _ResourceInstances()
        self._resources = _Resources()
        self._sorted_resource_types_cache: list[ResourceType] | None = None

    @property
    def resource_services(self):
        return self._provider.resource_services

    @property
    def resource_instances(self) -> list[ResourceInstance[Any]]:
        return self._resource_instances

    @classmethod
    def _create(cls, provider: Provider) -> Vendor:
        return cls(provider)

    @property
    def _sorted_resource_types(self) -> list[ResourceType]:
        """获取拓扑排序后的资源类型"""
        if self._sorted_resource_types_cache is None:
            resource_type_dependencies = {}
            for resource_type, _ in self.resource_services.items():
                resource_type_dependencies[resource_type] = resource_type.dependencies
            self._sorted_resource_types_cache = _topo_sort(resource_type_dependencies)
        return self._sorted_resource_types_cache

    async def refresh(self) -> None:
        """刷新资源状态"""
        self._resource_instances = _ResourceInstances(*await self._provider.find_resource_instances())

    async def cleanup(self) -> None:
        """清理待删除资源"""
        await self.refresh()

        undeclared_resources = [
            instance for instance in self._resource_instances if instance.name not in self._resources
        ]
        await self._remove_resource_instances(undeclared_resources)

    async def down(self) -> None:
        """销毁所有资源实例"""
        await self.refresh()
        safe_copy = self._resource_instances.copy()
        await self._remove_resource_instances(safe_copy)
        self._resources.clear()

    async def _remove_resource_instances(self, instances: list[ResourceInstance[Any]]) -> None:
        """删除指定的资源实例"""
        # 1. 获取所有待删除实例涉及的资源类型
        unique_resource_types = {instance.resource_type for instance in instances}

        # 2. 过滤出只包含待删除实例类型的排序结果，并反转顺序
        deletion_order_types = [
            resource_type
            for resource_type in reversed(self._sorted_resource_types)
            if resource_type in unique_resource_types
        ]

        # 3. 按类型顺序逐批删除资源
        for resource_type in deletion_order_types:
            instances_of_type = [instance for instance in instances if instance.resource_type == resource_type]

            print(f"--- 正在删除 {resource_type} 类型的资源 {len(instances_of_type)} 个 ---")
            for instance in instances_of_type:
                print(f"正在删除实例: {instance.name} (类型: {instance.resource_type})")

                # 实际删除
                await instance.delete()
                self._resource_instances.remove(instance)

                print(f"实例 {instance.name} (类型: {instance.resource_type}) 删除完成。")

        print("所有指定资源删除完成。")

    async def up(self, resource_type: ResourceType, expected: ResourceConfig[SPEC]) -> Resource_[SPEC, STATE]:
        """声明资源上线"""
        service = self._provider.resource_services.get(resource_type)

        actual = await service.load(expected)
        if not actual:
            actual = [await service.create(expected)]

        if not actual:
            raise ValueError(
                f"bug: 应该不会发生, 可能是QPA的bug, 资源{expected.name}的实际资源实例数量应该不为0, 但是目前为0"
            )

        if len(actual) > 1:
            instances_json = [instance.to_json() for instance in actual]
            raise ValueError(f"名为({expected.name})的资源, 发现重复/冲突资源实例: {instances_json}")

        result = Resource_(expected, actual)
        self._resources[result.name] = result
        self._resource_instances.extend(actual)
        return result


class ResourceService(ABC, Generic[SPEC, STATE]):
    """资源服务抽象类"""

    @property
    @abstractmethod
    def resource_type(self) -> ResourceType:
        """资源类型"""
        ...

    @abstractmethod
    async def create(self, config: ResourceConfig[SPEC]) -> ResourceInstance[STATE]:
        """创建资源"""
        ...

    @abstractmethod
    async def delete(self, instances: list[ResourceInstance[STATE]]) -> None:
        """删除资源"""
        ...

    @abstractmethod
    async def load(self, config: ResourceConfig[SPEC]) -> list[ResourceInstance[STATE]]:
        """加载资源"""
        ...


class ResourceServices(dict[ResourceType, ResourceService[Any, Any]]):
    """资源服务字典类"""

    def register(self, service: ResourceService[Any, Any]) -> None:
        """注册资源服务"""
        resource_type = service.resource_type
        if resource_type in self:
            raise ValueError(f"resource service[{resource_type}] already registered")
        self[resource_type] = service


# 导出主要类型
__all__ = [
    "ResourceInstance",
    "ResourceConfig",
    "ResourceType",
    "Resource",
    "Resource_",
    "ProjectConfig",
    "UpFunc",
    "Vendors",
    "Project",
    "Provider",
    "Vendor",
    "ResourceService",
    "ResourceServices",
]
