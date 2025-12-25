import concurrent.futures
import time
from doris_vector_search import DorisVectorClient, AuthOptions

def get_table_definition(process_id):
    """
    每个进程执行SHOW CREATE TABLE
    """
    try:
        # 创建客户端连接
        client = DorisVectorClient(database='test', auth_options=AuthOptions(host='localhost', query_port=9030, user='root', password=''))

        # 获取游标并执行查询
        cursor = client.connection.cursor()
        cursor.execute("SHOW CREATE TABLE inner_product_approximate768")
        result = cursor.fetchone()

        print(f"进程 {process_id} 执行成功:")
        print(f"表结构: {result[1] if result else 'No result'}")

        cursor.close()
        client.close()
        return result[1] if result else None

    except Exception as e:
        print(f"进程 {process_id} 错误: {e}")
        return None

def main():
    start_time = time.time()

    # 创建10个线程执行任务
    with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:
        # 使用map方法分配任务
        results = list(executor.map(get_table_definition, range(10)))

    end_time = time.time()
    print(f"\n所有进程执行完成，耗时: {end_time - start_time:.2f}秒")

    # 打印成功的结果数量
    successful_results = [r for r in results if r is not None]
    print(f"成功执行: {len(successful_results)}/{10}")

if __name__ == "__main__":
    main()
