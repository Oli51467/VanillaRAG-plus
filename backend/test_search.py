import requests
import json
import sys

def test_search(query, top_k=5):
    """测试搜索API"""
    url = "http://localhost:8080/api/v1/search/"
    
    # 构建请求数据
    data = {
        "query": query,
        "top_k": top_k
    }
    
    try:
        # 发送POST请求
        response = requests.post(url, json=data)
        
        # 检查响应状态码
        if response.status_code == 200:
            # 解析响应数据
            result = response.json()
            
            print(f"查询: {result['query']}")
            print(f"找到 {len(result['results'])} 个结果\n")
            
            # 显示搜索结果
            for i, item in enumerate(result['results']):
                print(f"结果 {i+1} (相似度得分: {item['score']:.4f}):")
                content_preview = item['content'][:150] + "..." if len(item['content']) > 150 else item['content']
                print(f"  内容: {content_preview}")
                print(f"  文件名: {item['metadata'].get('file_name', 'N/A')}")
                print(f"  文件路径: {item['metadata'].get('file_path', 'N/A')}")
                print()
                
            return True
        else:
            print(f"错误: HTTP状态码 {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"请求失败: {str(e)}")
        return False

if __name__ == "__main__":
    # 获取命令行参数
    query = "测试查询"
    top_k = 5
    
    if len(sys.argv) > 1:
        query = sys.argv[1]
    
    if len(sys.argv) > 2:
        try:
            top_k = int(sys.argv[2])
        except:
            pass
    
    # 执行测试
    test_search(query, top_k) 