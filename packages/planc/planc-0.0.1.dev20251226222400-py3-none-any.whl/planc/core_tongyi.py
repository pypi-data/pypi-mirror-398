from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from collections.abc import Callable, Awaitable
import json

# 泛型定义
SPEC = TypeVar("SPEC")
STATE = TypeVar("STATE")


class ResourceInstance(Generic[STATE]):
    """实际资源，包含
    - state字段: 特定于云厂商的实际资源状态信息，数据结构以云api资源数据结构为基础,可能会增加一些字段,比如region
    - 其他字段：云上资源从tag等提取出的QPA元信息，比如resource_name等
    """

    def __init__(self, resource_service: "ResourceService", name: str, state: STATE):
        self.resource_service = resource_service
        self.resource_type = resource_service.resource_type
        self.name = name
        self.state = state

    async def delete(self) -> None:
        await self.resource_service.delete([self])

    def to_json(self) -> str:
        return json.dumps({"name": self.name, "state": self.state})


class ResourceConfig(Generic[SPEC]):
    """Resource Config is a resource's configuration part, which is the desired state

    指资源的配置部分，即渴望的状态 (Desired State)
    """

    def __init__(self, name: str, spec: SPEC):
        self.name = name
        self.spec = spec


class ResourceType(ABC):
    """资源类型接口"""

    @property
    @abstractmethod
    def name(self) -> str:
        """CN: 唯一的资源类型名
        EN: unique resource type name
        """
        pass

    @property
    @abstractmethod
    def dependencies(self) -> list["ResourceType"]:
        """CN: 依赖项，比如 vm 依赖 vpc,subnet
        EN: dependencies, examples: vm dependencies is vpc,subnet
        """
        pass


class Resource(Generic[SPEC, STATE], ResourceConfig[SPEC]):
    """一个完整的受管理资源"""

    @property
    @abstractmethod
    def actual_instance(self) -> ResourceInstance[STATE]:
        pass

    @property
    @abstractmethod
    def state(self) -> STATE:
        pass


class Resource_(Resource[SPEC, STATE]):
    """一个完整的受管理资源，包括
    - expected: 资源配置(定义期望的规格状态)
    - actual: 对应的以资源名为映射关系的的多个同名实际资源实例(正常应该只有一个,但可能有重复create的问题资源)

    资源的最终状态，LazyResource加载后也会变成完全体的Resource
    """

    def __init__(self, expected: ResourceConfig[SPEC], actual: list[ResourceInstance[STATE]]):
        if len(actual) == 0:
            raise Exception("Resource为非惰性资源，创建Resource必须提供对应云上实例")

        for instance in actual:
            if expected.name != instance.name:
                raise Exception(f"expected.name({expected.name})必须和实际资源实例的name({instance.name})一致")

        self.expected = expected
        self.actual = actual

    @property
    def spec(self) -> SPEC:
        return self.expected.spec

    @property
    def name(self) -> str:
        """Name 是区分资源的关键, 我们会把name 用tag的形式打在每个实际的资源上, 以此对齐声明的资源配置和实际资源实例"""
        return self.expected.name

    @property
    def actual_instance(self) -> ResourceInstance[STATE]:
        if len(self.actual) != 1:
            raise Exception(
                f"正常资源应该对应云上1个云上实际实例，但现在有{len(self.actual)}个,请检查:{[it.to_json() for it in self.actual]}"
            )
        return self.actual[0]

    @property
    def state(self) -> STATE:
        return self.actual_instance.state


class ProjectConfig:
    def __init__(self, name: str):
        self.name = name


UpFunc = Callable[["Project"], Awaitable[None]]


class Vendors(list["Vendor"]):
    def __init__(self):
        super().__init__()

    @staticmethod
    def _create() -> "Vendors":
        return Vendors()

    def register(self, provider: "Provider") -> "Vendor":
        result = Vendor._create(provider)
        self.append(result)
        return result


class Project:
    def __init__(self, config: ProjectConfig):
        self.vendors = Vendors._create()
        self.name = config.name

    @property
    def resource_instances(self) -> list[ResourceInstance]:
        result = []
        for vendor in self.vendors:
            result.extend(vendor.resource_instances)
        return result

    @property
    def resources(self) -> list[Resource]:
        result = []
        for vendor in self.vendors:
            result.extend(list(vendor._resources.values()))
        return result

    @staticmethod
    def of(config: ProjectConfig) -> "Project":
        return Project(config)

    async def up(self, up_func: UpFunc) -> None:
        await self.refresh()
        await up_func(self)

        # cleanup
        for vendor in self.vendors:
            await vendor.cleanup()

    async def refresh(self) -> None:
        for vendor in self.vendors:
            await vendor.refresh()

    async def down(self) -> None:
        """因为非惰性执行的资源，配置以过程性脚本存在，所以无法按某种依赖图去删除资源，只能挨个从固定资源顺序删除
        - 按Provider注册到Project的后注册先删除的顺序依次删除所有Provider资源
        - 各Provider按资源类型固定的顺序进行删除，比如先删除虚拟机、再删除网络等等。
        """
        for vendor in self.vendors:
            await vendor.down()


class Provider(ABC):
    """无状态服务提供者, 状态由每个Provider对应的 Vendor 维护"""

    def __init__(self):
        self.resource_services = ResourceServices()

    @abstractmethod
    async def find_resource_instances(self) -> list[ResourceInstance]:
        """SPI方法，不应被客户程序直接调用，客户程序应通过@qpa/core的Project使用

        查询最新的 ResourceScope 内的所有的已存在资源的状态信息

        @return 获取查询出ResourceScope内的所有的资源状态
        """
        pass


class Vendor:
    """SPI 接口，并不直接暴露给api客户程序。

    实现Provider的公共逻辑有2种方式：
    1. 使用继承：用父类型实现对资源的管理公共逻辑
    2. 使用隔离的组合composite模型

    Vendor的逻辑原先用继承实现，由Provider父类型提供公共逻辑，我们拆离为组合模式，这样SPI实现者只关注Provider的接口实现即可
    避免SPI客户面对Vendor和云实现无关的接口，减少信息过载
    """

    def __init__(self, provider: Provider):
        self._resource_instances: _ResourceInstances = _ResourceInstances()
        self._resources: _Resources = _Resources()
        self.sorted_resource_types_cache: list[ResourceType] | None = None
        self.provider = provider

    @property
    def resource_services(self):
        return self.provider.resource_services

    @property
    def resource_instances(self) -> list[ResourceInstance]:
        return list(self._resource_instances)

    @staticmethod
    def _create(provider: Provider) -> "Vendor":
        return Vendor(provider)

    @property
    def sorted_resource_types(self) -> list[ResourceType]:
        # init
        if not self.sorted_resource_types_cache:
            resource_type_dependencies: dict[ResourceType, list[ResourceType]] = {}
            for resource_type, _ in self.resource_services.items():
                resource_type_dependencies[resource_type] = resource_type.dependencies
            self.sorted_resource_types_cache = topo_sort(resource_type_dependencies)

        return self.sorted_resource_types_cache

    async def refresh(self) -> None:
        """SPI方法，不应被客户程序直接调用，客户程序应通过@qpa/core的Project使用"""
        instances = await self.provider.find_resource_instances()
        self._resource_instances = _ResourceInstances(*instances)

    async def cleanup(self) -> None:
        """SPI方法，不应被客户程序直接调用，客户程序应通过@qpa/core的Project使用

        因为清理方法是up的最后一步，此方法必须在外部调用完up后才能使用。

        清理待删除资源(Pending Deletion Instances)
        服务提供者Provider应确保此方法内部先获取最新的实际资源实例，再删除所有Pending Deletion Instances
        不应期待外部调用者获取最新状态
        """
        await self.refresh()

        undeclared_resource_pending_to_delete = [e for e in self._resource_instances if not self._resources.get(e.name)]
        await self.remove_resource_instances(undeclared_resource_pending_to_delete)

    async def down(self) -> None:
        """SPI方法，不应被客户程序直接调用，客户程序应通过@qpa/core的Project使用

        销毁所有实际存在的资源实例
        """
        await self.refresh()
        safe_copy = list(self._resource_instances)
        await self.remove_resource_instances(safe_copy)
        self._resources.clear()

    async def remove_resource_instances(self, instances: list[ResourceInstance]) -> None:
        # 1. 获取所有待删除实例涉及的资源类型
        unique_resource_types_to_delete: set[ResourceType] = set(res.resource_type for res in instances)

        # 2. 过滤出只包含待删除实例类型的排序结果，并且是反向排序（先删除依赖者，后删除被依赖者）
        # 因为拓扑排序的结果是：被依赖者在前，依赖者在后。
        # 而删除顺序需要：依赖者在前，被依赖者在后。
        # 所以需要反转 sortedGlobalTypes，并过滤出要删除的类型。
        deletion_order_types = [t for t in self.sorted_resource_types if t in unique_resource_types_to_delete]

        # 3. 按类型顺序逐批删除资源
        for type_to_delete in deletion_order_types:
            instances_of_type = [res for res in instances if res.resource_type == type_to_delete]

            print(f"--- 正在删除 {type_to_delete.name} 类型的资源 {len(instances_of_type)} 个 ---")
            for instance in instances_of_type:
                print(f"正在删除实例: {instance.name} (类型: {instance.resource_type.name})")

                # real delete
                await instance.delete()
                self._resource_instances.remove(instance)

                print(f"实例 {instance.name} (类型: {instance.resource_type.name}) 删除完成。")

        print("所有指定资源删除完成。")

    async def up(self, resource_type: ResourceType, expected: ResourceConfig[SPEC]) -> Resource_[SPEC, STATE]:
        """声明资源(Declared Resources)上线，以便提供服务"""
        service = self.provider.resource_services[resource_type]

        actual = await service.load(expected)
        # todo 已存在的应该删除？
        if len(actual) == 0:
            actual = [await service.create(expected)]

        if len(actual) == 0:
            raise Exception(
                f"bug: 应该不会发生, 可能是QPA的bug, 资源{expected.name}的实际资源实例数量应该不为0, 但是目前为0 "
            )

        if len(actual) > 1:
            raise Exception(
                f"名为({expected.name})的资源, 发现重复/冲突资源实例(Duplicate/Conflicting Resources): 可能是重复创建等故障导致同名冲突实例，需要您手工清除或执行down后up重建,冲突实例：{[e.to_json() for e in actual]}"
            )

        result = Resource_(expected, actual)
        self._resources[result.name] = result
        self._resource_instances.extend(actual)
        return result


class ResourceService(ABC, Generic[SPEC, STATE]):
    @property
    @abstractmethod
    def resource_type(self) -> ResourceType:
        pass

    @abstractmethod
    async def create(self, config: ResourceConfig[SPEC]) -> ResourceInstance[STATE]:
        pass

    @abstractmethod
    async def delete(self, instances: list[ResourceInstance[STATE]]) -> None:
        pass

    @abstractmethod
    async def load(self, config: ResourceConfig[SPEC]) -> list[ResourceInstance[STATE]]:
        """@return 可能返回多个实际的同名云资源，因为一个资源可能被非正常的多次创建，重复问题留给上层程序判断解决"""
        pass


class _Resources(dict[str, Resource_]):
    pass


class _ResourceInstances(list[ResourceInstance]):
    def remove(self, instance: ResourceInstance) -> None:
        if instance in self:
            self.remove(instance)


class ResourceServices(dict[ResourceType, ResourceService]):
    def register(self, service: ResourceService) -> None:
        resource_type = service.resource_type
        if resource_type in self:
            raise Exception(f"resource service[{resource_type.name}] already registered")
        self[resource_type] = service


def topo_sort(dependencies: dict[ResourceType, list[ResourceType]]) -> list[ResourceType]:
    """拓扑排序实现"""
    # 这里需要根据具体需求实现拓扑排序算法
    # 为了简化，这里返回所有key的列表
    # 在实际应用中，需要实现真正的拓扑排序
    return list(dependencies.keys())
