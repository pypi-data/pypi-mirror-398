import mysql.connector
from mysql.connector import Error
import multiprocessing
import time

def get_table_definition(process_id):
    """
    每个进程执行SHOW CREATE TABLE
    """
    try:
        # 每个进程创建自己的连接
        connection = mysql.connector.connect(
            host='localhost',
            port=9030,
            user='root',
            password='',
            database='test'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # 执行SHOW CREATE TABLE
            cursor.execute("SHOW CREATE TABLE inner_product_approximate768")
            result = cursor.fetchone()
            
            print(f"进程 {process_id} 执行成功:")
            print(f"表结构: {result[1] if result else 'No result'}")
            
            cursor.close()
            connection.close()
            return result[1] if result else None
            
    except Error as e:
        print(f"进程 {process_id} 错误: {e}")
        return None

def main():
    start_time = time.time()
    
    # 创建10个进程
    with multiprocessing.Pool(processes=10) as pool:
        # 使用map方法分配任务
        results = pool.map(get_table_definition, range(10))
    
    end_time = time.time()
    print(f"\n所有进程执行完成，耗时: {end_time - start_time:.2f}秒")
    
    # 打印成功的结果数量
    successful_results = [r for r in results if r is not None]
    print(f"成功执行: {len(successful_results)}/{10}")

if __name__ == "__main__":
    main()
