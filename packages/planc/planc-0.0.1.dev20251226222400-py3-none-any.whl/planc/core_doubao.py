from __future__ import annotations
from typing import TypeVar, Generic, Any, Protocol
from collections.abc import Callable
from abc import ABC, abstractmethod
import json
from ._common import _topo_sort

# 类型变量定义
SPEC = TypeVar("SPEC")
STATE = TypeVar("STATE")


class ResourceInstance(Generic[STATE]):
    """实际资源实例类

    包含：
    - state字段: 特定于云厂商的实际资源状态信息
    - 其他字段：云上资源从tag等提取出的QPA元信息
    """

    def __init__(self, resource_service: ResourceService[Any, STATE], name: str, state: STATE):
        """初始化资源实例

        Args:
            resource_service: 资源服务实例
            name: 资源名称
            state: 资源状态
        """
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
    """资源配置类，定义资源的期望状态

    Args:
        name: 资源名称，在资源类型内唯一
        spec: 特定于厂商的资源规格定义
    """

    def __init__(self, name: str, spec: SPEC):
        self.name = name
        self.spec = spec


class ResourceType(Protocol):
    """资源类型接口

    Properties:
        name: 唯一的资源类型名称
        dependencies: 依赖的资源类型列表
    """

    @property
    def name(self) -> str: ...

    @property
    def dependencies(self) -> list[ResourceType]: ...


class Resource(Protocol, Generic[SPEC, STATE]):
    """资源接口，继承自ResourceConfig

    Properties:
        actual_instance: 资源的实际实例
        state: 资源状态
    """

    @property
    def name(self) -> str: ...

    @property
    def spec(self) -> SPEC: ...

    @property
    def actual_instance(self) -> ResourceInstance[STATE]: ...

    @property
    def state(self) -> STATE: ...


class Resource_(Resource, Generic[SPEC, STATE]):
    """完整的受管理资源实现类

    包含：
    - expected: 资源配置(定义期望的规格状态)
    - actual: 对应的以资源名为映射关系的的多个同名实际资源实例
    """

    def __init__(self, expected: ResourceConfig[SPEC], actual: list[ResourceInstance[STATE]]):
        """初始化资源

        Args:
            expected: 资源配置
            actual: 实际资源实例列表

        Raises:
            ValueError: 如果实际资源实例列表为空或名称不匹配
        """
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
        """资源名称，是区分资源的关键

        会把name用tag的形式打在每个实际的资源上，以此对齐声明的资源配置和实际资源实例
        """
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
    """项目配置类

    Args:
        name: 项目名称
    """

    def __init__(self, name: str):
        self.name = name


# 定义UpFunc类型


class Vendors(list["Vendor"]):
    """供应商列表类，继承自list"""

    def __init__(self):
        super().__init__()

    @classmethod
    def _create(cls) -> Vendors:
        """创建Vendors实例（内部方法）"""
        return cls()

    def register(self, provider: Provider) -> Vendor:
        """注册供应商

        Args:
            provider: 供应商实例

        Returns:
            Vendor: 新创建的Vendor实例
        """
        vendor = Vendor._create(provider)
        self.append(vendor)
        return vendor


class Project:
    """项目类，管理资源和供应商"""

    def __init__(self, config: ProjectConfig):
        """初始化项目

        Args:
            config: 项目配置
        """
        self.name = config.name
        self.vendors = Vendors._create()

    @property
    def resource_instances(self) -> list[ResourceInstance[Any]]:
        """获取所有资源实例"""
        instances = []
        for vendor in self.vendors:
            instances.extend(vendor.resource_instances)
        return instances

    @property
    def resources(self) -> list[Resource[Any, Any]]:
        """获取所有资源"""
        resources = []
        for vendor in self.vendors:
            resources.extend(vendor._resources.values())
        return resources

    @classmethod
    def of(cls, config: ProjectConfig) -> Project:
        """创建项目实例的工厂方法

        Args:
            config: 项目配置

        Returns:
            Project: 新创建的项目实例
        """
        return cls(config)

    async def up(self, up_func: UpFunc) -> None:
        """配置部署上线

        Args:
            up_func: 上线函数
        """
        await self.refresh()
        await up_func(self)

        # 清理
        for vendor in self.vendors:
            await vendor.cleanup()

    async def refresh(self) -> None:
        """刷新所有资源状态"""
        for vendor in self.vendors:
            await vendor.refresh()

    async def down(self) -> None:
        """删除所有资源

        按Provider注册到Project的后注册先删除的顺序依次删除所有Provider资源
        各Provider按资源类型固定的顺序进行删除
        """
        for vendor in self.vendors:
            await vendor.down()


UpFunc = Callable[[Project], Any]  # Python中通常用Any表示awaitable


class Provider(ABC):
    """无状态服务提供者抽象类

    状态由每个Provider对应的Vendor维护
    """

    def __init__(self):
        self.resource_services = ResourceServices()

    @abstractmethod
    async def find_resource_instances(self) -> list[ResourceInstance[Any]]:
        """SPI方法：查询最新的ResourceScope内的所有已存在资源的状态信息

        Returns:
            List[ResourceInstance]: 查询出的所有资源实例
        """
        pass


class _ResourceInstances(list[ResourceInstance[Any]]):
    """内部资源实例列表类

    用于存储和管理资源实例
    """

    def remove(self, instance: ResourceInstance[Any]) -> None:
        """删除指定的资源实例

        Args:
            instance: 要删除的资源实例
        """
        if instance in self:
            super().remove(instance)


class _Resources(dict[str, Resource_[Any, Any]]):
    """内部资源字典类

    用于存储和管理资源实例
    """

    pass


class Vendor:
    """供应商类，管理资源服务和资源实例"""

    def __init__(self, provider: Provider):
        """初始化供应商

        Args:
            provider: 供应商实例
        """
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
        """创建Vendor实例（内部方法）

        Args:
            provider: 供应商实例

        Returns:
            Vendor: 新创建的Vendor实例
        """
        return cls(provider)

    @property
    def _sorted_resource_types(self) -> list[ResourceType]:
        """获取拓扑排序后的资源类型

        Returns:
            List[ResourceType]: 排序后的资源类型列表
        """
        if self._sorted_resource_types_cache is None:
            resource_type_dependencies = {}
            for resource_type, _ in self.resource_services.items():
                resource_type_dependencies[resource_type] = resource_type.dependencies
            self._sorted_resource_types_cache = _topo_sort(resource_type_dependencies)
        return self._sorted_resource_types_cache

    async def refresh(self) -> None:
        """刷新资源实例"""
        instances = await self._provider.find_resource_instances()
        self._resource_instances = _ResourceInstances(*instances)

    async def cleanup(self) -> None:
        """清理待删除资源

        清理逻辑：删除所有未在_declared_resources中的资源实例
        """
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
        """删除指定的资源实例

        Args:
            instances: 要删除的资源实例列表
        """
        # 1. 获取所有待删除实例涉及的资源类型
        unique_resource_types = {instance.resource_type for instance in instances}

        # 2. 过滤出只包含待删除实例类型的排序结果，并且是反向排序
        # 拓扑排序结果：被依赖者在前，依赖者在后
        # 删除顺序需要：依赖者在前，被依赖者在后
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

                # 实际删除操作
                await instance.delete()
                self._resource_instances.remove(instance)

                print(f"实例 {instance.name} (类型: {instance.resource_type}) 删除完成。")

        print("所有指定资源删除完成。")

    async def up(self, resource_type: ResourceType, expected: ResourceConfig[SPEC]) -> Resource_[SPEC, STATE]:
        """声明资源上线

        Args:
            resource_type: 资源类型
            expected: 资源配置

        Returns:
            Resource_: 资源实例

        Raises:
            ValueError: 当资源实例数量异常时抛出
        """
        service = self._provider.resource_services.get(resource_type)

        actual = await service.load(expected)
        if not actual:
            actual = [await service.create(expected)]

        if not actual:
            raise ValueError(f"bug: 资源{expected.name}的实际资源实例数量应该不为0, 但是目前为0")

        if len(actual) > 1:
            instances_json = [instance.to_json() for instance in actual]
            raise ValueError(f"名为({expected.name})的资源, 发现重复/冲突资源实例: {instances_json}")

        result = Resource_(expected, actual)
        self._resources[result.name] = result
        self._resource_instances.extend(actual)
        return result


class ResourceService(ABC, Generic[SPEC, STATE]):
    """资源服务抽象类

    定义了资源的创建、删除和加载方法
    """

    @property
    @abstractmethod
    def resource_type(self) -> ResourceType:
        """资源类型"""
        pass

    @abstractmethod
    async def create(self, config: ResourceConfig[SPEC]) -> ResourceInstance[STATE]:
        """创建资源

        Args:
            config: 资源配置

        Returns:
            ResourceInstance: 新创建的资源实例
        """
        pass

    @abstractmethod
    async def delete(self, instances: list[ResourceInstance[STATE]]) -> None:
        """删除资源

        Args:
            instances: 要删除的资源实例列表
        """
        pass

    @abstractmethod
    async def load(self, config: ResourceConfig[SPEC]) -> list[ResourceInstance[STATE]]:
        """加载资源

        Args:
            config: 资源配置

        Returns:
            List[ResourceInstance]: 加载到的资源实例列表
        """
        pass


class ResourceServices(dict[ResourceType, ResourceService[Any, Any]]):
    """资源服务字典类

    用于存储和管理资源服务实例
    """

    def register(self, service: ResourceService[Any, Any]) -> None:
        """注册资源服务

        Args:
            service: 资源服务实例

        Raises:
            ValueError: 当资源服务已存在时抛出
        """
        resource_type = service.resource_type
        if resource_type in self:
            raise ValueError(f"resource service[{resource_type}] already registered")
        self[resource_type] = service


# 导出主要类和接口
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
