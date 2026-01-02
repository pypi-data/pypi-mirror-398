"""
同步调用示例 - 展示如何使用 kxy-open-id-client 同步分配 ID 段
"""

from kxy_open_id_client import (
    SegmentClient,
    OpenIdAPIError,
    OpenIdConnectionError,
    OpenIdTimeoutError
)


def basic_example():
    """基础用法示例"""
    print("=== 基础用法示例 ===")

    # 创建客户端
    client = SegmentClient(base_url="http://localhost:5801")

    # 分配 ID 段
    segment = client.allocate_segment(
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


def error_handling_example():
    """错误处理示例"""
    print("=== 错误处理示例 ===")

    client = SegmentClient(base_url="http://localhost:5801", timeout=5.0)

    try:
        segment = client.allocate_segment(
            system_code="example-system",
            db_name="example_db",
            table_name="orders",
            field_name="order_id",
            segment_count=5000
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


class IDGenerator:
    """ID 生成器示例 - 基于分段分配实现连续 ID 生成"""

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

    def next_id(self) -> int:
        """获取下一个 ID"""
        if self.current >= self.end:
            self._allocate_new_segment()

        self.current += 1
        return self.current

    def _allocate_new_segment(self):
        """分配新的 ID 段"""
        segment = self.client.allocate_segment(
            system_code=self.system_code,
            db_name=self.db_name,
            table_name=self.table_name,
            field_name=self.field_name,
            segment_count=self.segment_size
        )
        self.current = segment.start - 1
        self.end = segment.end
        print(f"[ID生成器] 分配新段: {segment.start} ~ {segment.end}")


def id_generator_example():
    """ID 生成器应用示例"""
    print("=== ID 生成器应用示例 ===")

    client = SegmentClient(base_url="http://localhost:5801")

    # 创建 ID 生成器
    id_gen = IDGenerator(
        client=client,
        system_code="example-system",
        db_name="example_db",
        table_name="products",
        field_name="product_id",
        segment_size=100  # 每次分配 100 个 ID
    )

    # 生成一些 ID
    print("生成 10 个 ID:")
    for i in range(10):
        generated_id = id_gen.next_id()
        print(f"  ID #{i + 1}: {generated_id}")

    print()


def custom_headers_example():
    """自定义请求头示例"""
    print("=== 自定义请求头示例 ===")

    # 创建带自定义请求头的客户端
    client = SegmentClient(
        base_url="http://localhost:5801",
        headers={
            "X-Request-ID": "example-request-123",
            "X-Client-Version": "1.0.0"
        }
    )

    segment = client.allocate_segment(
        system_code="example-system",
        db_name="example_db",
        table_name="transactions",
        field_name="txn_id"
    )

    print(f"分配成功: {segment.start} ~ {segment.end}")
    print()


if __name__ == "__main__":
    print("kxy-open-id-client 同步调用示例\n")

    try:
        # 运行各个示例
        basic_example()
        error_handling_example()
        id_generator_example()
        custom_headers_example()

        print("所有示例运行完成!")

    except Exception as e:
        print(f"示例运行失败: {e}")
        import traceback
        traceback.print_exc()
