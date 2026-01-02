"""
并发ID生成测试
测试IdGenerator和AsyncIdGenerator在并发场景下的正确性
"""

import threading
import asyncio
from unittest.mock import Mock, MagicMock
from typing import List, Set
import time

from kxy_open_id_client import SegmentClient, IdGenerator, AsyncIdGenerator
from kxy_open_id_client.models import SegmentResponse


def create_mock_client() -> SegmentClient:
    """创建一个模拟的SegmentClient"""
    client = Mock(spec=SegmentClient)

    # 模拟计数器,用于生成连续的号段
    counter = {"value": 0}

    def mock_allocate_segment(*args, **kwargs):
        """模拟分配号段"""
        segment_count = kwargs.get('segment_count', 10000)
        start = counter["value"]
        end = start + segment_count - 1
        counter["value"] = end + 1

        # 添加小延迟模拟网络请求
        time.sleep(0.001)

        return SegmentResponse(start=start, end=end)

    client.allocate_segment = Mock(side_effect=mock_allocate_segment)
    return client


def test_single_thread_id_generation():
    """测试单线程ID生成"""
    print("\n=== 测试单线程ID生成 ===")

    client = create_mock_client()
    id_gen = IdGenerator(
        segment_client=client,
        system_code="test",
        db_name="test_db",
        table_name="test_table",
        field_name="id",
        segment_count=100
    )

    # 生成100个ID
    ids = [id_gen.next_id() for _ in range(100)]

    # 验证ID唯一性
    assert len(ids) == len(set(ids)), "存在重复的ID"

    # 验证ID连续性
    assert ids == list(range(0, 100)), "ID不连续"

    print(f"✓ 成功生成 {len(ids)} 个唯一ID")
    print(f"✓ ID范围: {min(ids)} - {max(ids)}")


def test_multi_thread_id_generation():
    """测试多线程并发ID生成"""
    print("\n=== 测试多线程并发ID生成 ===")

    client = create_mock_client()
    id_gen = IdGenerator(
        segment_client=client,
        system_code="test",
        db_name="test_db",
        table_name="test_table",
        field_name="id",
        segment_count=100
    )

    # 用于收集所有线程生成的ID
    all_ids: List[int] = []
    ids_lock = threading.Lock()

    def generate_ids(thread_id: int, count: int):
        """每个线程生成指定数量的ID"""
        thread_ids = []
        for _ in range(count):
            id_value = id_gen.next_id()
            thread_ids.append(id_value)

        with ids_lock:
            all_ids.extend(thread_ids)

        print(f"  线程 {thread_id}: 生成 {count} 个ID, 范围 {min(thread_ids)} - {max(thread_ids)}")

    # 创建10个线程,每个线程生成100个ID
    num_threads = 10
    ids_per_thread = 100
    threads = []

    start_time = time.time()

    for i in range(num_threads):
        t = threading.Thread(target=generate_ids, args=(i, ids_per_thread))
        threads.append(t)
        t.start()

    # 等待所有线程完成
    for t in threads:
        t.join()

    elapsed_time = time.time() - start_time

    # 验证结果
    total_ids = num_threads * ids_per_thread
    assert len(all_ids) == total_ids, f"ID数量不匹配: 期望 {total_ids}, 实际 {len(all_ids)}"

    # 验证ID唯一性
    unique_ids = set(all_ids)
    assert len(unique_ids) == total_ids, f"存在重复的ID: 期望 {total_ids} 个唯一ID, 实际 {len(unique_ids)} 个"

    print(f"\n✓ 总共生成 {len(all_ids)} 个ID")
    print(f"✓ 唯一ID数量: {len(unique_ids)}")
    print(f"✓ ID范围: {min(all_ids)} - {max(all_ids)}")
    print(f"✓ 耗时: {elapsed_time:.3f}s")
    print(f"✓ 吞吐量: {total_ids / elapsed_time:.0f} IDs/s")


def test_segment_exhaustion():
    """测试号段耗尽后自动申请新号段"""
    print("\n=== 测试号段耗尽自动申请 ===")

    client = create_mock_client()
    id_gen = IdGenerator(
        segment_client=client,
        system_code="test",
        db_name="test_db",
        table_name="test_table",
        field_name="id",
        segment_count=10  # 小号段,方便测试
    )

    # 生成25个ID,应该申请3个号段
    ids = [id_gen.next_id() for _ in range(25)]

    # 验证ID唯一性和连续性
    assert len(ids) == len(set(ids)), "存在重复的ID"
    assert ids == list(range(0, 25)), "ID不连续"

    # 验证申请了3次号段
    assert client.allocate_segment.call_count == 3, \
        f"应该申请3次号段,实际 {client.allocate_segment.call_count} 次"

    print(f"✓ 生成 {len(ids)} 个ID,申请了 {client.allocate_segment.call_count} 次号段")
    print(f"✓ ID连续性正确: {ids[:5]}...{ids[-5:]}")


async def test_async_multi_coroutine_id_generation():
    """测试多协程并发ID生成"""
    print("\n=== 测试多协程并发ID生成 ===")

    # 创建异步mock
    client = Mock(spec=SegmentClient)
    counter = {"value": 0}

    async def mock_allocate_segment_async(*args, **kwargs):
        """模拟异步分配号段"""
        segment_count = kwargs.get('segment_count', 10000)
        start = counter["value"]
        end = start + segment_count - 1
        counter["value"] = end + 1

        # 添加小延迟模拟网络请求
        await asyncio.sleep(0.001)

        return SegmentResponse(start=start, end=end)

    client.allocate_segment_async = mock_allocate_segment_async

    id_gen = AsyncIdGenerator(
        segment_client=client,
        system_code="test",
        db_name="test_db",
        table_name="test_table",
        field_name="id",
        segment_count=100
    )

    # 用于收集所有协程生成的ID
    all_ids: List[int] = []

    async def generate_ids(coroutine_id: int, count: int):
        """每个协程生成指定数量的ID"""
        coroutine_ids = []
        for _ in range(count):
            id_value = await id_gen.next_id()
            coroutine_ids.append(id_value)

        all_ids.extend(coroutine_ids)
        print(f"  协程 {coroutine_id}: 生成 {count} 个ID, 范围 {min(coroutine_ids)} - {max(coroutine_ids)}")

    # 创建10个协程,每个协程生成100个ID
    num_coroutines = 10
    ids_per_coroutine = 100

    start_time = time.time()

    # 并发运行所有协程
    await asyncio.gather(*[
        generate_ids(i, ids_per_coroutine)
        for i in range(num_coroutines)
    ])

    elapsed_time = time.time() - start_time

    # 验证结果
    total_ids = num_coroutines * ids_per_coroutine
    assert len(all_ids) == total_ids, f"ID数量不匹配: 期望 {total_ids}, 实际 {len(all_ids)}"

    # 验证ID唯一性
    unique_ids = set(all_ids)
    assert len(unique_ids) == total_ids, f"存在重复的ID: 期望 {total_ids} 个唯一ID, 实际 {len(unique_ids)} 个"

    print(f"\n✓ 总共生成 {len(all_ids)} 个ID")
    print(f"✓ 唯一ID数量: {len(unique_ids)}")
    print(f"✓ ID范围: {min(all_ids)} - {max(all_ids)}")
    print(f"✓ 耗时: {elapsed_time:.3f}s")
    print(f"✓ 吞吐量: {total_ids / elapsed_time:.0f} IDs/s")


def test_high_concurrency():
    """高并发压力测试"""
    print("\n=== 高并发压力测试 ===")

    client = create_mock_client()
    id_gen = IdGenerator(
        segment_client=client,
        system_code="test",
        db_name="test_db",
        table_name="test_table",
        field_name="id",
        segment_count=1000
    )

    all_ids: List[int] = []
    ids_lock = threading.Lock()

    def generate_ids(thread_id: int, count: int):
        thread_ids = []
        for _ in range(count):
            id_value = id_gen.next_id()
            thread_ids.append(id_value)

        with ids_lock:
            all_ids.extend(thread_ids)

    # 50个线程,每个线程生成1000个ID
    num_threads = 50
    ids_per_thread = 1000
    threads = []

    print(f"启动 {num_threads} 个线程,每个生成 {ids_per_thread} 个ID...")
    start_time = time.time()

    for i in range(num_threads):
        t = threading.Thread(target=generate_ids, args=(i, ids_per_thread))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    elapsed_time = time.time() - start_time
    total_ids = num_threads * ids_per_thread
    unique_ids = set(all_ids)

    # 验证
    assert len(all_ids) == total_ids
    assert len(unique_ids) == total_ids, \
        f"发现重复ID! 期望 {total_ids} 个唯一ID, 实际 {len(unique_ids)} 个"

    print(f"✓ 成功! 生成 {len(all_ids)} 个唯一ID")
    print(f"✓ 耗时: {elapsed_time:.3f}s")
    print(f"✓ 吞吐量: {total_ids / elapsed_time:.0f} IDs/s")
    print(f"✓ 申请号段次数: {client.allocate_segment.call_count}")


if __name__ == "__main__":
    print("=" * 60)
    print("ID生成器并发测试套件")
    print("=" * 60)

    # 运行所有测试
    try:
        test_single_thread_id_generation()
        test_multi_thread_id_generation()
        test_segment_exhaustion()

        # 异步测试
        asyncio.run(test_async_multi_coroutine_id_generation())

        # 高并发测试
        test_high_concurrency()

        print("\n" + "=" * 60)
        print("✓ 所有测试通过!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n✗ 测试出错: {e}")
        raise


# PYTHONPATH=/myspace/source/workspace/yudao-python/kxy-open-id-client:$PYTHONPATH python tests/test_concurrent_id_generation.py