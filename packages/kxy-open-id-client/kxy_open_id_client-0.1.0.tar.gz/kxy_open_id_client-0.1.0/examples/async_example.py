"""
异步调用示例 - 展示如何使用 kxy-open-id-client 异步分配 ID 段
"""

import asyncio
from kxy_open_id_client import (
    SegmentClient,
    OpenIdAPIError,
    OpenIdConnectionError,
    OpenIdTimeoutError
)


async def basic_async_example():
    """基础异步用法示例"""
    print("=== 基础异步用法示例 ===")

    # 创建客户端
    client = SegmentClient(base_url="http://localhost:5801")

    # 异步分配 ID 段
    segment = await client.allocate_segment_async(
        system_code="example-system",
        db_name="example_db",
        table_name="users",
        field_name="id",
        segment_count=10000
    )

    print(f"成功分配 ID 段:")
    print(f"  起始 ID: {segment.start}")
    print(f"  结束 ID: {segment.end}")
    print(f"  总数量: {segment.end - segment.start + 1}")
    print()


async def concurrent_allocation_example():
    """并发分配示例 - 同时为多个表分配 ID 段"""
    print("=== 并发分配示例 ===")

    client = SegmentClient(base_url="http://localhost:5801")

    # 定义多个分配任务
    tasks = [
        client.allocate_segment_async(
            system_code="example-system",
            db_name="example_db",
            table_name="users",
            field_name="id",
            segment_count=5000
        ),
        client.allocate_segment_async(
            system_code="example-system",
            db_name="example_db",
            table_name="orders",
            field_name="order_id",
            segment_count=3000
        ),
        client.allocate_segment_async(
            system_code="example-system",
            db_name="example_db",
            table_name="products",
            field_name="product_id",
            segment_count=2000
        ),
    ]

    # 并发执行所有任务
    print("开始并发分配 ID 段...")
    results = await asyncio.gather(*tasks)

    # 显示结果
    tables = ["users", "orders", "products"]
    for table, segment in zip(tables, results):
        print(f"{table}: {segment.start} ~ {segment.end} ({segment.end - segment.start + 1} IDs)")

    print()


async def error_handling_example():
    """异步错误处理示例"""
    print("=== 异步错误处理示例 ===")

    client = SegmentClient(base_url="http://localhost:5801", timeout=5.0)

    try:
        segment = await client.allocate_segment_async(
            system_code="example-system",
            db_name="example_db",
            table_name="transactions",
            field_name="txn_id",
            segment_count=8000
        )
        print(f"分配成功: {segment.start} ~ {segment.end}")

    except OpenIdAPIError as e:
        print(f"API 错误:")
        print(f"  错误码: {e.code}")
        print(f"  错误消息: {e.msg}")
        if e.trace_id:
            print(f"  追踪 ID: {e.trace_id}")

    except OpenIdConnectionError as e:
        print(f"连接错误: {e}")

    except OpenIdTimeoutError as e:
        print(f"请求超时: {e}")

    print()


class AsyncIDGenerator:
    """异步 ID 生成器示例"""

    def __init__(self, client: SegmentClient, system_code: str,
                 db_name: str, table_name: str, field_name: str,
                 segment_size: int = 1000):
        self.client = client
        self.system_code = system_code
        self.db_name = db_name
        self.table_name = table_name
        self.field_name = field_name
        self.segment_size = segment_size

        self.current = 0
        self.end = 0
        self._lock = asyncio.Lock()

    async def next_id(self) -> int:
        """异步获取下一个 ID"""
        async with self._lock:
            if self.current >= self.end:
                await self._allocate_new_segment()

            self.current += 1
            return self.current

    async def _allocate_new_segment(self):
        """异步分配新的 ID 段"""
        segment = await self.client.allocate_segment_async(
            system_code=self.system_code,
            db_name=self.db_name,
            table_name=self.table_name,
            field_name=self.field_name,
            segment_count=self.segment_size
        )
        self.current = segment.start - 1
        self.end = segment.end
        print(f"[异步ID生成器] 分配新段: {segment.start} ~ {segment.end}")


async def async_id_generator_example():
    """异步 ID 生成器应用示例"""
    print("=== 异步 ID 生成器应用示例 ===")

    client = SegmentClient(base_url="http://localhost:5801")

    # 创建异步 ID 生成器
    id_gen = AsyncIDGenerator(
        client=client,
        system_code="example-system",
        db_name="example_db",
        table_name="async_products",
        field_name="product_id",
        segment_size=50
    )

    # 并发生成多个 ID
    print("并发生成 20 个 ID:")
    tasks = [id_gen.next_id() for _ in range(20)]
    ids = await asyncio.gather(*tasks)

    for i, generated_id in enumerate(ids, 1):
        print(f"  ID #{i}: {generated_id}")

    print()


async def batch_allocation_example():
    """批量分配不同数量 ID 段的示例"""
    print("=== 批量分配示例 ===")

    client = SegmentClient(base_url="http://localhost:5801")

    # 为不同的场景分配不同大小的 ID 段
    allocations = [
        ("users", 10000),      # 用户表需要大量 ID
        ("orders", 5000),      # 订单表中等数量
        ("sessions", 20000),   # 会话表需要很多 ID
        ("categories", 100),   # 分类表只需少量 ID
    ]

    print(f"开始批量分配 {len(allocations)} 个 ID 段...")

    tasks = [
        client.allocate_segment_async(
            system_code="example-system",
            db_name="example_db",
            table_name=table,
            field_name="id",
            segment_count=count
        )
        for table, count in allocations
    ]

    results = await asyncio.gather(*tasks)

    print("\n分配结果:")
    for (table, count), segment in zip(allocations, results):
        actual_count = segment.end - segment.start + 1
        print(f"  {table:15} 请求: {count:6} | 分配: {actual_count:6} | 范围: {segment.start} ~ {segment.end}")

    print()


async def main():
    """主函数 - 运行所有示例"""
    print("kxy-open-id-client 异步调用示例\n")

    try:
        await basic_async_example()
        await concurrent_allocation_example()
        await error_handling_example()
        await async_id_generator_example()
        await batch_allocation_example()

        print("所有异步示例运行完成!")

    except Exception as e:
        print(f"示例运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())
