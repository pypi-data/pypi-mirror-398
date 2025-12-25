"""
AI Bridge SDK 使用示例

展示所有可用的输入参数和调用方式
"""

from pathlib import Path
from aib import AIBridge, Response, VendorType
from aib.batch import QwenBatchManager, GeminiBatchManager


# ============================================================
# 1. 基础用法 - AIBridge 初始化参数
# ============================================================

def example_basic():
    """
    AIBridge 构造函数参数:
    
    - vendor: str           # 厂商名称 (gemini, kimi, qwen, openai)
    - api_key: str          # API 密钥 (可选，从配置或环境变量读取)
    - model: str            # 模型名称 (可选，从配置读取)
    - base_url: str         # 自定义 API 端点 (可选，用于中转站)
    - config_path: str      # 配置文件路径 (可选)
    - **kwargs              # 其他厂商特定参数
    """
    
    # 方式 1: 最简调用 (从 ~/.aib/config.yaml 或环境变量读取配置)
    bridge = AIBridge(vendor="gemini")
    
    # 方式 2: 完整参数
    bridge = AIBridge(
        vendor="gemini",                    # 必须: 厂商
        api_key="AIza...",                  # API 密钥
        model="gemini-2.0-flash",           # 模型名称
        base_url=None,                      # 自定义端点 (默认官方)
        config_path="./config.yaml",        # 配置文件
    )
    
    # 方式 3: 使用 API 中转站
    bridge = AIBridge(
        vendor="openai",
        api_key="sk-xxx",
        model="gpt-4o",
        base_url="https://your-relay.com/v1",  # 中转站地址
    )
    
    return bridge


# ============================================================
# 2. Chat 方法 - 对话请求参数
# ============================================================

def example_chat(bridge: AIBridge):
    """
    bridge.chat() 方法参数:
    
    - prompt: str                   # 必须: 提示词
    - files: List[str | Path]       # 可选: 文件路径列表 (自动通过 File API 上传)
    - temperature: float            # 可选: 采样温度 (默认 0.7)
    - max_tokens: int               # 可选: 最大输出 token 数
    - **kwargs                      # 其他厂商特定参数
    
    返回值 Response:
    - content: str      # AI 原始返回内容 (不做任何处理)
    - usage: Usage      # Token 用量统计
    - raw: Any          # 原始 SDK 响应对象
    """
    
    # 纯文本对话
    response = bridge.chat(prompt="你好，介绍一下你自己")
    print(f"Content: {response.content}")
    print(f"Tokens: {response.usage.total_tokens}")
    
    # 带参数的对话
    response = bridge.chat(
        prompt="写一首短诗",
        temperature=0.9,        # 更高的创造性
        max_tokens=200,         # 限制输出长度
    )
    
    # 带文件的对话 (多模态)
    response = bridge.chat(
        prompt="总结这个文档的要点",
        files=["./document.pdf"],           # 单个文件
    )
    
    response = bridge.chat(
        prompt="比较这两张图片的区别",
        files=["./image1.png", "./image2.jpg"],  # 多个文件
    )
    
    # 混合文件类型
    response = bridge.chat(
        prompt="根据这份报告和图表，给出分析",
        files=[
            "./report.pdf",
            "./chart.png",
            Path("./data.csv"),  # 也支持 Path 对象
        ],
        temperature=0.3,
    )
    
    return response


# ============================================================
# 3. Response 对象结构
# ============================================================

def example_response(response: Response):
    """
    Response 对象属性:
    
    - content: str          # AI 返回的原始内容
    - usage: Usage          # Token 用量
        - prompt_tokens: int
        - completion_tokens: int
        - total_tokens: int
    - raw: Any              # 原始 SDK 响应 (用于高级场景)
    """
    
    # 获取内容
    print(response.content)
    
    # 也可以直接 str() 转换
    print(str(response))
    
    # Token 统计
    print(f"输入 tokens: {response.usage.prompt_tokens}")
    print(f"输出 tokens: {response.usage.completion_tokens}")
    print(f"总计 tokens: {response.usage.total_tokens}")
    
    # 访问原始响应 (高级用法)
    raw = response.raw
    # - Gemini: google.genai.types.GenerateContentResponse
    # - OpenAI/Kimi: openai.types.ChatCompletion
    # - Qwen: dashscope.Generation response


# ============================================================
# 4. 不同厂商示例
# ============================================================

def example_vendors():
    """各厂商配置示例"""
    
    # Gemini (Google)
    gemini = AIBridge(
        vendor="gemini",
        api_key="AIza...",
        model="gemini-2.0-flash",  # 可选: gemini-1.5-pro, gemini-2.0-flash-exp
    )
    
    # Kimi (Moonshot)
    kimi = AIBridge(
        vendor="kimi",
        api_key="sk-...",
        model="moonshot-v1-auto",  # 可选: moonshot-v1-8k, moonshot-v1-32k, moonshot-v1-128k
    )
    
    # Qwen (阿里云)
    qwen = AIBridge(
        vendor="qwen",
        api_key="sk-...",
        model="qwen-plus",  # 可选: qwen-turbo, qwen-max, qwen-vl-plus (多模态)
    )
    
    # OpenAI
    openai = AIBridge(
        vendor="openai",
        api_key="sk-...",
        model="gpt-4o",  # 可选: gpt-4o-mini, gpt-4-turbo, o1-preview
    )
    
    # OpenAI 兼容的中转站
    relay = AIBridge(
        vendor="openai",
        api_key="your-relay-key",
        model="claude-3-5-sonnet",  # 通过中转调用其他模型
        base_url="https://your-relay.com/v1",
    )


# ============================================================
# 5. Batch API 示例 (半价离线处理)
# ============================================================

def example_batch():
    """
    Batch API 参数:
    
    manager.submit(requests, model) 参数:
    - requests: List[Dict]  # 请求列表
        - prompt: str       # 提示词
        - files: List[str]  # 可选: 文件列表
    - model: str            # 模型名称
    
    返回值 BatchJob:
    - id: str               # 任务 ID
    - vendor: str           # 厂商
    - status: BatchStatus   # 状态 (pending, running, completed, failed)
    """
    
    # Qwen Batch
    qwen_batch = QwenBatchManager(
        api_key="sk-...",
        base_url=None,  # 可选: 自定义端点
    )
    
    job = qwen_batch.submit(
        requests=[
            {"prompt": "问题1"},
            {"prompt": "问题2"},
            {"prompt": "分析这个文档", "files": ["./doc.pdf"]},
        ],
        model="qwen-plus",
    )
    
    print(f"Job ID: {job.id}")
    print(f"Status: {job.status}")
    
    # 查询状态
    status = qwen_batch.get_status(job.id)
    
    # 获取结果 (完成后)
    if status.status.value == "completed":
        results = qwen_batch.get_results(job.id)
        for req_id, content in results.items():
            print(f"{req_id}: {content}")
    
    # Gemini Batch (类似)
    gemini_batch = GeminiBatchManager(api_key="AIza...")
    job = gemini_batch.submit(
        requests=[{"prompt": "Hello"}],
        model="gemini-1.5-flash",
    )


# ============================================================
# 6. 完整运行示例
# ============================================================

if __name__ == "__main__":
    import os
    
    # 确保设置了环境变量或配置文件
    # export AIB_GEMINI_API_KEY="AIza..."
    
    api_key = os.getenv("AIB_GEMINI_API_KEY")
    if not api_key:
        print("请先设置 AIB_GEMINI_API_KEY 环境变量")
        print("例如: export AIB_GEMINI_API_KEY='AIza...'")
        exit(1)
    
    # 初始化
    bridge = AIBridge(
        vendor="gemini",
        api_key=api_key,
        model="gemini-2.0-flash",
    )
    
    # 发送请求
    print("发送请求...")
    response = bridge.chat(
        prompt="用一句话介绍你自己",
        temperature=0.7,
    )
    
    # 输出结果
    print("\n=== 响应内容 ===")
    print(response.content)
    
    print("\n=== Token 统计 ===")
    print(f"输入: {response.usage.prompt_tokens}")
    print(f"输出: {response.usage.completion_tokens}")
    print(f"总计: {response.usage.total_tokens}")
