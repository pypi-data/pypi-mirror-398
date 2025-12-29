#!/usr/bin/env python3
"""
流式输出性能测试脚本

测试同步和异步客户端的流式输出性能，重点关注：
1. 第一个token的延迟时间
2. 总体流式输出完成时间
3. 简单问句 vs 复杂问句的性能差异
4. 同步 vs 异步客户端的性能对比
"""

import asyncio
import logging
import os
import sys
import time
from typing import List, Dict, Union, Iterator, AsyncIterator

# 配置测试脚本专用的日志
test_logger = logging.getLogger('test_streaming_performance')
test_logger.setLevel(logging.INFO)
test_logger.propagate = False

# 创建测试脚本专用的handler
test_handler = logging.StreamHandler()
test_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
test_logger.addHandler(test_handler)

logger = test_logger

# 设置环境变量
os.environ['MODEL_MANAGER_SERVER_GRPC_USE_TLS'] = "false"
os.environ['MODEL_MANAGER_SERVER_ADDRESS'] = "localhost:50051"
os.environ['MODEL_MANAGER_SERVER_JWT_SECRET_KEY'] = "model-manager-server-jwt-key"

# OpenAI API Key (如果需要测试OpenAI SDK)
# os.environ['OPENAI_API_KEY'] = "your-openai-api-key-here"

# 导入客户端模块
try:
    from tamar_model_client import TamarModelClient, AsyncTamarModelClient
    from tamar_model_client.schemas import ModelRequest, UserContext
    from tamar_model_client.enums import ProviderType, InvokeType, Channel

    # 启用客户端日志以便调试
    os.environ['TAMAR_MODEL_CLIENT_LOG_LEVEL'] = 'INFO'

except ImportError as e:
    logger.error(f"导入模块失败: {e}")
    sys.exit(1)

# 导入OpenAI SDK
try:
    import openai
    from openai import OpenAI, AsyncOpenAI
except ImportError as e:
    logger.warning(f"OpenAI SDK导入失败: {e}")
    openai = None


class StreamingPerformanceMetrics:
    """流式输出性能指标收集器"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = None
        self.first_token_time = None
        self.end_time = None
        self.total_chunks = 0
        self.total_content_length = 0
        self.chunk_times = []
        self.error_occurred = False
        self.error_message = ""
        
    def start_test(self):
        """开始测试计时"""
        self.start_time = time.perf_counter()
        
    def record_first_token(self):
        """记录第一个token到达时间"""
        if self.first_token_time is None:
            self.first_token_time = time.perf_counter()
            
    def record_chunk(self, content: str):
        """记录每个数据块"""
        current_time = time.perf_counter()
        if content:
            self.total_chunks += 1
            self.total_content_length += len(content)
            if self.start_time:
                self.chunk_times.append(current_time - self.start_time)
            
    def end_test(self):
        """结束测试计时"""
        self.end_time = time.perf_counter()
        
    def record_error(self, error_msg: str):
        """记录错误"""
        self.error_occurred = True
        self.error_message = error_msg
        
    def get_results(self) -> Dict:
        """获取测试结果"""
        if not self.start_time:
            return {
                "test_name": self.test_name,
                "success": False,
                "error_message": "测试未开始",
                "total_duration": 0,
                "first_token_delay": None,
                "first_token_delay_ms": None,
                "total_chunks": 0,
                "total_content_length": 0,
                "avg_chunk_interval": 0,
                "tokens_per_second": 0,
                "chunks_per_second": 0
            }
            
        total_duration = (self.end_time or time.perf_counter()) - self.start_time
        first_token_delay = (self.first_token_time - self.start_time) if self.first_token_time else None
        
        return {
            "test_name": self.test_name,
            "success": not self.error_occurred,
            "error_message": self.error_message if self.error_occurred else None,
            "total_duration": total_duration,
            "first_token_delay": first_token_delay,
            "first_token_delay_ms": first_token_delay * 1000 if first_token_delay else None,
            "total_chunks": self.total_chunks,
            "total_content_length": self.total_content_length,
            "avg_chunk_interval": sum(self.chunk_times) / len(self.chunk_times) if self.chunk_times else 0,
            "tokens_per_second": self.total_content_length / total_duration if total_duration > 0 else 0,
            "chunks_per_second": self.total_chunks / total_duration if total_duration > 0 else 0
        }
        
    def print_results(self):
        """打印测试结果"""
        results = self.get_results()
        
        print(f"\n📊 {results['test_name']} - 性能测试结果:")
        print("=" * 60)
        
        if results['success']:
            print(f"✅ 测试状态: 成功")
            print(f"🕐 总耗时: {results['total_duration']:.3f} 秒")
            
            if results['first_token_delay_ms']:
                print(f"⚡ 首Token延迟: {results['first_token_delay_ms']:.1f} ms")
            else:
                print(f"⚡ 首Token延迟: 未检测到")
                
            print(f"📦 数据块数量: {results['total_chunks']}")
            print(f"📝 内容总长度: {results['total_content_length']} 字符")
            
            if results['chunks_per_second'] > 0:
                print(f"🚀 数据块速度: {results['chunks_per_second']:.2f} 块/秒")
            if results['tokens_per_second'] > 0:
                print(f"⌨️ 字符速度: {results['tokens_per_second']:.2f} 字符/秒")
                
        else:
            print(f"❌ 测试状态: 失败")
            print(f"💥 错误信息: {results['error_message']}")
            
        print("=" * 60)


def test_sync_simple_streaming():
    """测试同步客户端 - 简单问句流式输出"""
    from google.genai import types
    metrics = StreamingPerformanceMetrics("同步客户端 - 简单问句")
    
    try:
        client = TamarModelClient()
        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_budget=0,
            )
        )
        # 简单问句
        request = ModelRequest(
            provider=ProviderType.GOOGLE,
            #channel=Channel.AI_STUDIO,
            #invoke_type=InvokeType.GENERATION,
            model="tamar-google-gemini-flash",
            contents=[
                {"role": "user", "parts": [{"text": "1+1等于几？"}]}
            ],
            user_context=UserContext(
                user_id="test_sync_simple",
                org_id="test_org",
                client_type="sync_performance_test"
            ),
            stream=True,
            config = generate_content_config,
        )
        
        print(f"🔍 开始测试: {metrics.test_name}")
        metrics.start_test()
        
        response_gen = client.invoke(request)
        
        # 检查返回类型是否为迭代器
        if not hasattr(response_gen, '__iter__'):
            raise Exception("响应不是流式迭代器")
            
        for chunk in response_gen:
            if chunk.content:
                if metrics.first_token_time is None:
                    metrics.record_first_token()
                    print(f"⚡ 收到首个数据块: '{chunk.content[:20]}...'")
                metrics.record_chunk(chunk.content)
                
        metrics.end_test()
        
    except Exception as e:
        metrics.record_error(str(e))
        metrics.end_test()
        logger.error(f"同步简单问句测试失败: {e}")
        
    finally:
        if hasattr(client, 'close'):
            client.close()
            
    metrics.print_results()
    return metrics.get_results()


def test_sync_complex_streaming():
    """测试同步客户端 - 复杂问句流式输出"""
    from google.genai import types
    metrics = StreamingPerformanceMetrics("同步客户端 - 复杂问句")
    
    try:
        client = TamarModelClient()
        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_budget=0,
            )
        )
        
        # 复杂问句
        request = ModelRequest(
            provider=ProviderType.GOOGLE,
            #channel=Channel.AI_STUDIO,
            #invoke_type=InvokeType.GENERATION,
            model="tamar-google-gemini-flash",
            contents=[
                {"role": "user", "parts": [{"text": "请详细解释人工智能的发展历史，包括关键里程碑、重要人物和技术突破，并分析其对现代社会的影响。"}]}
            ],
            user_context=UserContext(
                user_id="test_sync_complex",
                org_id="test_org", 
                client_type="sync_performance_test"
            ),
            stream=True,
            config=generate_content_config
        )
        
        print(f"🔍 开始测试: {metrics.test_name}")
        metrics.start_test()
        
        response_gen = client.invoke(request)
        
        # 检查返回类型是否为迭代器
        if not hasattr(response_gen, '__iter__'):
            raise Exception("响应不是流式迭代器")
            
        for chunk in response_gen:
            if chunk.content:
                if metrics.first_token_time is None:
                    metrics.record_first_token()
                    print(f"⚡ 收到首个数据块: '{chunk.content[:20]}...'")
                metrics.record_chunk(chunk.content)
                
        metrics.end_test()
        
    except Exception as e:
        metrics.record_error(str(e))
        metrics.end_test()
        logger.error(f"同步复杂问句测试失败: {e}")
        
    finally:
        if hasattr(client, 'close'):
            client.close()
            
    metrics.print_results()
    return metrics.get_results()


async def test_async_simple_streaming():
    """测试异步客户端 - 简单问句流式输出"""
    metrics = StreamingPerformanceMetrics("异步客户端 - 简单问句")
    
    try:
        async with AsyncTamarModelClient() as client:
            # 简单问句
            request = ModelRequest(
                provider=ProviderType.GOOGLE,
                #channel=Channel.AI_STUDIO,
                #invoke_type=InvokeType.GENERATION,
                model="tamar-google-gemini-flash",
                contents=[
                    {"role": "user", "parts": [{"text": "2+2等于几？"}]}
                ],
                user_context=UserContext(
                    user_id="test_async_simple",
                    org_id="test_org",
                    client_type="async_performance_test"
                ),
                stream=True,
                config={
                    "temperature": 0.1,
                    "maxOutputTokens": 50
                }
            )
            
            print(f"🔍 开始测试: {metrics.test_name}")
            metrics.start_test()
            
            response_gen = await client.invoke(request)
            
            # 检查返回类型是否为异步迭代器
            if not hasattr(response_gen, '__aiter__'):
                raise Exception("响应不是异步流式迭代器")
                
            async for chunk in response_gen:
                if chunk.content:
                    if metrics.first_token_time is None:
                        metrics.record_first_token()
                        print(f"⚡ 收到首个数据块: '{chunk.content[:20]}...'")
                    metrics.record_chunk(chunk.content)
                    
            metrics.end_test()
            
    except Exception as e:
        metrics.record_error(str(e))
        metrics.end_test()
        logger.error(f"异步简单问句测试失败: {e}")
        
    metrics.print_results()
    return metrics.get_results()


async def test_async_complex_streaming():
    """测试异步客户端 - 复杂问句流式输出"""
    metrics = StreamingPerformanceMetrics("异步客户端 - 复杂问句")
    
    try:
        async with AsyncTamarModelClient() as client:
            # 复杂问句
            request = ModelRequest(
                provider=ProviderType.GOOGLE,
                # channel=Channel.AI_STUDIO,
                # invoke_type=InvokeType.GENERATION,
                model="tamar-google-gemini-flash",
                contents=[
                    {"role": "user", "parts": [{"text": "请详细介绍区块链技术的工作原理，包括去中心化、共识机制、加密算法等核心概念，并分析其在金融、供应链管理等领域的应用前景。"}]}
                ],
                user_context=UserContext(
                    user_id="test_async_complex",
                    org_id="test_org",
                    client_type="async_performance_test"
                ),
                stream=True,
                config={
                    "temperature": 0.3,
                    "maxOutputTokens": 500
                }
            )
            
            print(f"🔍 开始测试: {metrics.test_name}")
            metrics.start_test()
            
            response_gen = await client.invoke(request)
            
            # 检查返回类型是否为异步迭代器
            if not hasattr(response_gen, '__aiter__'):
                raise Exception("响应不是异步流式迭代器")
                
            async for chunk in response_gen:
                if chunk.content:
                    if metrics.first_token_time is None:
                        metrics.record_first_token()
                        print(f"⚡ 收到首个数据块: '{chunk.content[:20]}...'")
                    metrics.record_chunk(chunk.content)
                    
            metrics.end_test()
            
    except Exception as e:
        metrics.record_error(str(e))
        metrics.end_test()
        logger.error(f"异步复杂问句测试失败: {e}")
        
    metrics.print_results()
    return metrics.get_results()


def test_sync_azure_simple_streaming():
    """测试同步客户端 - Azure OpenAI 简单问句流式输出"""
    metrics = StreamingPerformanceMetrics("同步客户端 - Azure 简单问句")
    
    try:
        client = TamarModelClient()
        
        # Azure OpenAI 简单问句
        request = ModelRequest(
            provider=ProviderType.AZURE,
            invoke_type=InvokeType.CHAT_COMPLETIONS,
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "3+3等于几？"}
            ],
            user_context=UserContext(
                user_id="test_sync_azure_simple",
                org_id="test_org",
                client_type="sync_azure_performance_test"
            ),
            stream=True
        )
        
        print(f"🔍 开始测试: {metrics.test_name}")
        metrics.start_test()
        
        response_gen = client.invoke(request)
        
        # 检查返回类型是否为迭代器
        if not hasattr(response_gen, '__iter__'):
            raise Exception("响应不是流式迭代器")
            
        for chunk in response_gen:
            if chunk.content:
                if metrics.first_token_time is None:
                    metrics.record_first_token()
                    print(f"⚡ 收到首个数据块: '{chunk.content[:20]}...'")
                metrics.record_chunk(chunk.content)
                
        metrics.end_test()
        
    except Exception as e:
        metrics.record_error(str(e))
        metrics.end_test()
        logger.error(f"同步Azure简单问句测试失败: {e}")
        
    finally:
        if hasattr(client, 'close'):
            client.close()
            
    metrics.print_results()
    return metrics.get_results()


async def test_async_azure_complex_streaming():
    """测试异步客户端 - Azure OpenAI 复杂问句流式输出"""
    metrics = StreamingPerformanceMetrics("异步客户端 - Azure 复杂问句")
    
    try:
        async with AsyncTamarModelClient() as client:
            # Azure OpenAI 复杂问句
            request = ModelRequest(
                provider=ProviderType.AZURE,
                invoke_type=InvokeType.CHAT_COMPLETIONS,
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": "请详细解释云计算的核心架构，包括IaaS、PaaS、SaaS三种服务模式的特点和应用场景，并分析其对企业数字化转型的价值。"}
                ],
                user_context=UserContext(
                    user_id="test_async_azure_complex", 
                    org_id="test_org",
                    client_type="async_azure_performance_test"
                ),
                stream=True
            )
            
            print(f"🔍 开始测试: {metrics.test_name}")
            metrics.start_test()
            
            response_gen = await client.invoke(request)
            
            # 检查返回类型是否为异步迭代器
            if not hasattr(response_gen, '__aiter__'):
                raise Exception("响应不是异步流式迭代器")
                
            async for chunk in response_gen:
                if chunk.content:
                    if metrics.first_token_time is None:
                        metrics.record_first_token()
                        print(f"⚡ 收到首个数据块: '{chunk.content[:20]}...'")
                    metrics.record_chunk(chunk.content)
                    
            metrics.end_test()
            
    except Exception as e:
        metrics.record_error(str(e))
        metrics.end_test()
        logger.error(f"异步Azure复杂问句测试失败: {e}")
        
    metrics.print_results()
    return metrics.get_results()


def test_sync_openai_chat_completions():
    """测试同步OpenAI SDK - Chat Completions 流式输出"""
    metrics = StreamingPerformanceMetrics("同步OpenAI SDK - Chat")
    
    if not openai:
        metrics.record_error("OpenAI SDK 未安装")
        metrics.print_results()
        return metrics.get_results()
    
    try:
        # 使用OpenAI官方SDK
        client = OpenAI(
            base_url=os.environ.get("OPENAI_API_URL", "http://localhost:8000/v1"),
            api_key=os.environ.get("OPENAI_API_KEY", "call-model:user_id:data_scientist_agent")
        )
        
        print(f"🔍 开始测试: {metrics.test_name}")
        metrics.start_test()
        
        # OpenAI Chat Completions 流式请求
        stream = client.chat.completions.create(
            model="tamar-google-gemini-flash",
            messages=[
                {"role": "user", "content": "请简要介绍人工智能在医疗领域的应用，包括诊断、治疗和药物研发等方面。"}
            ],
            stream=True,
            max_tokens=300,
            temperature=0.4
        )
        
        # 处理流式响应
        for chunk in stream:
            try:
                # 添加调试信息
                if chunk is None:
                    print(f"🔍 调试：收到 None chunk")
                    continue
                    
                if not hasattr(chunk, 'choices'):
                    print(f"🔍 调试：chunk 没有 choices 属性，类型: {type(chunk)}")
                    continue
                    
                if not chunk.choices:
                    print(f"🔍 调试：chunk.choices 为空")
                    continue
                    
                if len(chunk.choices) == 0:
                    print(f"🔍 调试：chunk.choices 长度为0")
                    continue
                    
                choice = chunk.choices[0]
                if not hasattr(choice, 'delta'):
                    print(f"🔍 调试：choice 没有 delta 属性，类型: {type(choice)}")
                    continue
                    
                if not hasattr(choice.delta, 'content'):
                    print(f"🔍 调试：choice.delta 没有 content 属性，类型: {type(choice.delta)}")
                    continue
                    
                if choice.delta.content:
                    content = choice.delta.content
                    if metrics.first_token_time is None:
                        metrics.record_first_token()
                        print(f"⚡ 收到首个数据块: '{content[:20]}...'")
                    metrics.record_chunk(content)
                else:
                    print(f"🔍 调试：choice.delta.content 为空或None")
                    
            except Exception as chunk_error:
                print(f"🔍 调试：处理chunk时出错: {chunk_error}")
                print(f"🔍 调试：chunk类型: {type(chunk)}")
                raise chunk_error
                
        metrics.end_test()
        
    except Exception as e:
        metrics.record_error(str(e))
        metrics.end_test()
        logger.error(f"同步OpenAI SDK测试失败: {e}")
        
    metrics.print_results()
    return metrics.get_results()


async def test_async_openai_chat_completions():
    """测试异步OpenAI SDK - Chat Completions 流式输出"""
    metrics = StreamingPerformanceMetrics("异步OpenAI SDK - Chat")
    
    if not openai:
        metrics.record_error("OpenAI SDK 未安装")
        metrics.print_results()
        return metrics.get_results()
    
    try:
        # 使用OpenAI官方异步SDK
        client = AsyncOpenAI(
            base_url=os.environ.get("OPENAI_API_URL", "http://localhost:8000/v1"),
            api_key=os.environ.get("OPENAI_API_KEY", "call-model:user_id:data_scientist_agent")
        )
        
        print(f"🔍 开始测试: {metrics.test_name}")
        metrics.start_test()
        
        # OpenAI Chat Completions 异步流式请求
        stream = await client.chat.completions.create(
            model="tamar-google-gemini-flash",
            messages=[
                {"role": "user", "content": "详细解释机器学习的主要算法类型，包括监督学习、无监督学习和强化学习的特点、应用场景和优缺点。"}
            ],
            stream=True,
            max_tokens=400,
            temperature=0.3
        )
        
        # 处理异步流式响应
        async for chunk in stream:
            if chunk and chunk.choices and len(chunk.choices) > 0 and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                if metrics.first_token_time is None:
                    metrics.record_first_token()
                    print(f"⚡ 收到首个数据块: '{content[:20]}...'")
                metrics.record_chunk(content)
                
        metrics.end_test()
        
    except Exception as e:
        metrics.record_error(str(e))
        metrics.end_test()
        logger.error(f"异步OpenAI SDK测试失败: {e}")
        
    finally:
        # 关闭异步客户端
        if 'client' in locals():
            await client.close()
        
    metrics.print_results()
    return metrics.get_results()


def test_sync_openai_simple_streaming():
    """测试同步OpenAI SDK - 简单问句流式输出"""
    metrics = StreamingPerformanceMetrics("同步OpenAI SDK - 简单问句")
    
    if not openai:
        metrics.record_error("OpenAI SDK 未安装")
        metrics.print_results()
        return metrics.get_results()
    
    try:
        # 使用OpenAI官方SDK
        client = OpenAI(
            base_url=os.environ.get("OPENAI_API_URL", "http://localhost:8000/v1"),
            api_key=os.environ.get("OPENAI_API_KEY", "call-model:user_id:data_scientist_agent")
        )
        
        print(f"🔍 开始测试: {metrics.test_name}")
        metrics.start_test()
        
        # OpenAI Chat Completions 简单问句流式请求
        stream = client.chat.completions.create(
            model="tamar-google-gemini-flash",
            messages=[
                {"role": "user", "content": "5+5等于多少？"}
            ],
            stream=True,
            max_tokens=50,
            temperature=0.1
        )
        
        # 处理流式响应
        for chunk in stream:
            if chunk and chunk.choices and len(chunk.choices) > 0 and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                if metrics.first_token_time is None:
                    metrics.record_first_token()
                    print(f"⚡ 收到首个数据块: '{content[:20]}...'")
                metrics.record_chunk(content)
                
        metrics.end_test()
        
    except Exception as e:
        metrics.record_error(str(e))
        metrics.end_test()
        logger.error(f"同步OpenAI SDK简单问句测试失败: {e}")
        
    metrics.print_results()
    return metrics.get_results()


async def test_async_openai_simple_streaming():
    """测试异步OpenAI SDK - 简单问句流式输出"""
    metrics = StreamingPerformanceMetrics("异步OpenAI SDK - 简单问句")
    
    if not openai:
        metrics.record_error("OpenAI SDK 未安装")
        metrics.print_results()
        return metrics.get_results()
    
    try:
        # 使用OpenAI官方异步SDK
        client = AsyncOpenAI(
            base_url=os.environ.get("OPENAI_API_URL", "http://localhost:8000/v1"),
            api_key=os.environ.get("OPENAI_API_KEY", "call-model:user_id:data_scientist_agent")
        )
        
        print(f"🔍 开始测试: {metrics.test_name}")
        metrics.start_test()
        
        # OpenAI Chat Completions 简单问句异步流式请求
        stream = await client.chat.completions.create(
            model="tamar-google-gemini-flash",
            messages=[
                {"role": "user", "content": "10-3等于多少？"}
            ],
            stream=True,
            max_tokens=50,
            temperature=0.1
        )
        
        # 处理异步流式响应
        async for chunk in stream:
            if chunk and chunk.choices and len(chunk.choices) > 0 and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                if metrics.first_token_time is None:
                    metrics.record_first_token()
                    print(f"⚡ 收到首个数据块: '{content[:20]}...'")
                metrics.record_chunk(content)
                
        metrics.end_test()
        
    except Exception as e:
        metrics.record_error(str(e))
        metrics.end_test()
        logger.error(f"异步OpenAI SDK简单问句测试失败: {e}")
        
    finally:
        # 关闭异步客户端
        if 'client' in locals():
            await client.close()
        
    metrics.print_results()
    return metrics.get_results()


class ImageGenerationMetrics:
    """图像生成性能指标收集器"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = None
        self.end_time = None
        self.image_generated = False
        self.image_size = 0
        self.error_occurred = False
        self.error_message = ""
        
    def start_test(self):
        """开始测试计时"""
        self.start_time = time.perf_counter()
        
    def record_image(self, image_data: str):
        """记录生成的图像"""
        if image_data:
            self.image_generated = True
            self.image_size = len(str(image_data))
            
    def end_test(self):
        """结束测试计时"""
        self.end_time = time.perf_counter()
        
    def record_error(self, error_msg: str):
        """记录错误"""
        self.error_occurred = True
        self.error_message = error_msg
        
    def get_results(self) -> Dict:
        """获取测试结果"""
        if not self.start_time:
            return {
                "test_name": self.test_name,
                "success": False,
                "error_message": "测试未开始",
                "total_duration": 0,
                "image_generated": False,
                "image_size": 0,
                "generation_speed": 0
            }
            
        total_duration = (self.end_time or time.perf_counter()) - self.start_time
        
        return {
            "test_name": self.test_name,
            "success": not self.error_occurred and self.image_generated,
            "error_message": self.error_message if self.error_occurred else None,
            "total_duration": total_duration,
            "image_generated": self.image_generated,
            "image_size": self.image_size,
            "generation_speed": self.image_size / total_duration if total_duration > 0 and self.image_size > 0 else 0
        }
        
    def print_results(self):
        """打印测试结果"""
        results = self.get_results()
        
        print(f"\n🖼️ {results['test_name']} - 图像生成测试结果:")
        print("=" * 60)
        
        if results['success']:
            print(f"✅ 测试状态: 成功")
            print(f"🕐 总耗时: {results['total_duration']:.3f} 秒")
            print(f"🖼️ 图像生成: {'是' if results['image_generated'] else '否'}")
            if results['image_size'] > 0:
                print(f"📦 图像数据大小: {results['image_size']} 字符")
                print(f"🚀 生成速度: {results['generation_speed']:.2f} 字符/秒")
        else:
            print(f"❌ 测试状态: 失败")
            print(f"💥 错误信息: {results['error_message']}")
            
        print("=" * 60)



async def test_async_google_vertex_image_generation():
    """测试异步客户端 - Google Vertex AI 图像生成"""
    metrics = ImageGenerationMetrics("异步客户端 - Google Vertex 图像生成")
    
    try:
        async with AsyncTamarModelClient() as client:
            # Google Vertex AI 图像生成请求
            request = ModelRequest(
                provider=ProviderType.GOOGLE,
                channel=Channel.VERTEXAI,
                invoke_type=InvokeType.IMAGE_GENERATION,
                model="imagen-3.0-fast-generate-001",
                prompt="壮丽的雪山峰顶在夕阳余晖下呈现金色光芒，山下是宁静的湖泊倒映着山景",
                user_context=UserContext(
                    user_id="test_async_vertex_image",
                    org_id="test_org",
                    client_type="async_vertex_image_performance_test"
                )
            )
            
            print(f"🔍 开始测试: {metrics.test_name}")
            metrics.start_test()
            
            response = await client.invoke(request)
            
            # 检查是否生成了图像
            if response.error:
                raise Exception(f"图像生成失败: {response.error}")
            elif response.content:
                metrics.record_image(response.content)
                print(f"🖼️ 图像生成成功，数据大小: {len(str(response.content))} 字符")
            elif hasattr(response, 'raw_response') and response.raw_response:
                # 检查原始响应中是否包含图像数据
                image_data = None
                if isinstance(response.raw_response, list):
                    # 检查 image_bytes (新格式) 或 _image_bytes (旧格式)
                    for r in response.raw_response:
                        if isinstance(r, dict):
                            image_data = r.get("image_bytes") or r.get("_image_bytes")
                            if image_data:
                                print(f"🖼️ Vertex AI 图像生成成功，Base64数据大小: {len(str(image_data))} 字符")
                                break
                elif isinstance(response.raw_response, dict):
                    # 其他格式：直接使用整个响应
                    image_data = str(response.raw_response)
                else:
                    image_data = str(response.raw_response)
                
                if image_data:
                    metrics.record_image(image_data)
                    print(f"🖼️ 图像生成成功（来自raw_response），数据大小: {len(str(image_data))} 字符")
                else:
                    raise Exception("raw_response 中未找到图像数据")
            else:
                # 输出响应的详细信息用于调试
                print(f"🔍 Vertex AI 响应调试信息:")
                print(f"   content: {response.content}")
                print(f"   error: {response.error}")
                print(f"   raw_response 类型: {type(response.raw_response)}")
                print(f"   raw_response 内容: {getattr(response, 'raw_response', 'None')}")
                print(f"   usage: {getattr(response, 'usage', 'None')}")
                raise Exception("未收到任何图像数据")
                    
            metrics.end_test()
            
    except Exception as e:
        metrics.record_error(str(e))
        metrics.end_test()
        logger.error(f"异步Google Vertex图像生成测试失败: {e}")
        
    metrics.print_results()
    return metrics.get_results()


def compare_results(results: List[Dict]):
    """对比不同测试的结果"""
    print("\n🔀 性能对比分析")
    print("=" * 80)
    
    # 过滤掉无效的结果
    valid_results = []
    for r in results:
        if isinstance(r, dict) and 'test_name' in r:
            valid_results.append(r)
        else:
            print(f"⚠️ 发现无效测试结果: {r}")
    
    if not valid_results:
        print("😞 没有有效的测试结果可供对比")
        return
        
    # 按测试类型分类
    streaming_tests = [r for r in valid_results if 'first_token_delay_ms' in r]
    image_tests = [r for r in valid_results if 'image_generated' in r]
    
    # 按成功/失败分类
    successful_streaming = [r for r in streaming_tests if r['success']]
    failed_streaming = [r for r in streaming_tests if not r['success']]
    successful_image = [r for r in image_tests if r['success']]
    failed_image = [r for r in image_tests if not r['success']]
    
    all_failed = failed_streaming + failed_image
    
    if all_failed:
        print(f"❌ 失败的测试 ({len(all_failed)}):")
        for test in all_failed:
            print(f"   - {test['test_name']}: {test['error_message']}")
        print()
    
    # 流式输出测试对比
    if successful_streaming:
        print(f"📡 流式输出测试结果 ({len(successful_streaming)}):")
        print("=" * 70)
        
        # 首Token延迟对比
        print("⚡ 首Token延迟对比:")
        print(f"{'测试名称':<30} {'延迟(ms)':<12} {'总耗时(s)':<12} {'数据块数':<10}")
        print("-" * 70)
        
        for test in successful_streaming:
            delay_ms = f"{test['first_token_delay_ms']:.1f}" if test['first_token_delay_ms'] else "N/A"
            total_time = f"{test['total_duration']:.3f}"
            chunks = str(test['total_chunks'])
            
            print(f"{test['test_name']:<30} {delay_ms:<12} {total_time:<12} {chunks:<10}")
        
        print()
        
        # 性能指标对比
        print("🚀 流式输出性能指标:")
        print(f"{'测试名称':<30} {'字符/秒':<12} {'块/秒':<12} {'内容长度':<10}")
        print("-" * 70)
        
        for test in successful_streaming:
            chars_per_sec = f"{test['tokens_per_second']:.1f}"
            chunks_per_sec = f"{test['chunks_per_second']:.1f}"
            content_len = str(test['total_content_length'])
            
            print(f"{test['test_name']:<30} {chars_per_sec:<12} {chunks_per_sec:<12} {content_len:<10}")
        
        print()
    
    # 图像生成测试对比
    if successful_image:
        print(f"🖼️ 图像生成测试结果 ({len(successful_image)}):")
        print("=" * 70)
        print(f"{'测试名称':<30} {'总耗时(s)':<12} {'图像大小':<12} {'生成速度':<15}")
        print("-" * 70)
        
        for test in successful_image:
            total_time = f"{test['total_duration']:.3f}"
            image_size = f"{test['image_size']}" if test['image_size'] > 0 else "N/A"
            gen_speed = f"{test['generation_speed']:.1f} 字符/秒" if test['generation_speed'] > 0 else "N/A"
            
            print(f"{test['test_name']:<30} {total_time:<12} {image_size:<12} {gen_speed:<15}")
        
        print()
    
    # 综合分析结论
    if successful_streaming or successful_image:
        print("📈 分析结论:")
        
        # 流式输出分析
        if successful_streaming:
            # 找出最快的首Token
            valid_first_token_tests = [t for t in successful_streaming if t['first_token_delay_ms']]
            if valid_first_token_tests:
                fastest_first_token = min(valid_first_token_tests, key=lambda x: x['first_token_delay_ms'])
                print(f"   🏆 首Token最快: {fastest_first_token['test_name']} ({fastest_first_token['first_token_delay_ms']:.1f}ms)")
            
            # 找出最快的总体完成时间
            fastest_total = min(successful_streaming, key=lambda x: x['total_duration'])
            print(f"   🏆 流式输出最快: {fastest_total['test_name']} ({fastest_total['total_duration']:.3f}s)")
            
            # 同步vs异步对比
            sync_streaming = [t for t in successful_streaming if '同步' in t['test_name']]
            async_streaming = [t for t in successful_streaming if '异步' in t['test_name']]
            
            if sync_streaming and async_streaming:
                sync_delays = [t['first_token_delay_ms'] for t in sync_streaming if t['first_token_delay_ms']]
                async_delays = [t['first_token_delay_ms'] for t in async_streaming if t['first_token_delay_ms']]
                
                if sync_delays and async_delays:
                    avg_sync_delay = sum(sync_delays) / len(sync_delays)
                    avg_async_delay = sum(async_delays) / len(async_delays)
                    
                    print(f"   📊 同步客户端平均首Token延迟: {avg_sync_delay:.1f}ms")
                    print(f"   📊 异步客户端平均首Token延迟: {avg_async_delay:.1f}ms")
                    
                    if avg_async_delay < avg_sync_delay:
                        print(f"   ✨ 异步客户端首Token延迟平均快 {avg_sync_delay - avg_async_delay:.1f}ms")
                    else:
                        print(f"   ✨ 同步客户端首Token延迟平均快 {avg_async_delay - avg_sync_delay:.1f}ms")
            
            # 简单vs复杂问句对比
            simple_streaming = [t for t in successful_streaming if '简单' in t['test_name']]
            complex_streaming = [t for t in successful_streaming if '复杂' in t['test_name']]
            
            if simple_streaming and complex_streaming:
                simple_delays = [t['first_token_delay_ms'] for t in simple_streaming if t['first_token_delay_ms']]
                complex_delays = [t['first_token_delay_ms'] for t in complex_streaming if t['first_token_delay_ms']]
                
                if simple_delays and complex_delays:
                    avg_simple_delay = sum(simple_delays) / len(simple_delays)
                    avg_complex_delay = sum(complex_delays) / len(complex_delays)
                    
                    print(f"   📊 简单问句平均首Token延迟: {avg_simple_delay:.1f}ms")
                    print(f"   📊 复杂问句平均首Token延迟: {avg_complex_delay:.1f}ms")
                    
                    if avg_complex_delay > avg_simple_delay:
                        print(f"   💡 复杂问句首Token延迟平均多 {avg_complex_delay - avg_simple_delay:.1f}ms")
                    else:
                        print(f"   💡 简单问句首Token延迟平均多 {avg_simple_delay - avg_complex_delay:.1f}ms")
        
        # 图像生成分析
        if successful_image:
            fastest_image = min(successful_image, key=lambda x: x['total_duration'])
            print(f"   🏆 图像生成最快: {fastest_image['test_name']} ({fastest_image['total_duration']:.3f}s)")
            
            # 同步vs异步图像生成对比
            sync_image = [t for t in successful_image if '同步' in t['test_name']]
            async_image = [t for t in successful_image if '异步' in t['test_name']]
            
            if sync_image and async_image:
                avg_sync_image_time = sum(t['total_duration'] for t in sync_image) / len(sync_image)
                avg_async_image_time = sum(t['total_duration'] for t in async_image) / len(async_image)
                
                print(f"   📊 同步客户端平均图像生成时间: {avg_sync_image_time:.3f}s")
                print(f"   📊 异步客户端平均图像生成时间: {avg_async_image_time:.3f}s")
                
                if avg_async_image_time < avg_sync_image_time:
                    print(f"   ✨ 异步客户端图像生成平均快 {avg_sync_image_time - avg_async_image_time:.3f}s")
                else:
                    print(f"   ✨ 同步客户端图像生成平均快 {avg_async_image_time - avg_sync_image_time:.3f}s")


async def main():
    """主测试函数"""
    print("🚀 流式输出性能测试")
    print("=" * 50)
    print("目标：测试第一个token延迟和总体完成时间")
    print("场景：简单问句 vs 复杂问句，同步 vs 异步客户端")
    print("=" * 50)
    
    all_results = []
    
    try:
        # 1. 同步客户端测试
        print("\n🔄 同步客户端测试")
        print("-" * 30)
        
        # 同步简单问句
        result1 = test_sync_simple_streaming()
        all_results.append(result1)
        
        # 等待一下再进行下一个测试
        await asyncio.sleep(1)

        # 同步复杂问句
        result2 = test_sync_complex_streaming()
        all_results.append(result2)

        await asyncio.sleep(1)

        # 同步Azure简单问句
        result3 = test_sync_azure_simple_streaming()
        all_results.append(result3)

        await asyncio.sleep(1)

        # 2. 异步客户端测试
        print("\n🔄 异步客户端测试")
        print("-" * 30)

        # 异步简单问句
        result4 = await test_async_simple_streaming()
        all_results.append(result4)

        await asyncio.sleep(1)

        # 异步复杂问句
        result5 = await test_async_complex_streaming()
        all_results.append(result5)

        await asyncio.sleep(1)

        # 异步Azure复杂问句
        result6 = await test_async_azure_complex_streaming()
        all_results.append(result6)
        
        # 3. OpenAI Chat Completions 测试
        print("\n🔄 OpenAI Chat Completions 测试")
        print("-" * 30)

        # 同步OpenAI简单问句
        result7 = test_sync_openai_simple_streaming()
        all_results.append(result7)

        await asyncio.sleep(1)

        # 异步OpenAI简单问句
        result8 = await test_async_openai_simple_streaming()
        all_results.append(result8)

        await asyncio.sleep(1)

        # 同步OpenAI复杂问句
        result9 = test_sync_openai_chat_completions()
        all_results.append(result9)

        await asyncio.sleep(1)

        # 异步OpenAI复杂问句
        result10 = await test_async_openai_chat_completions()
        all_results.append(result10)

        await asyncio.sleep(1)
        
        # 4. Google 图像生成测试
        print("\n🔄 Google 图像生成测试")
        print("-" * 30)
        
        # 异步Google Vertex图像生成
        result13 = await test_async_google_vertex_image_generation()
        all_results.append(result13)
        
        # 5. 结果对比分析
        compare_results(all_results)
        
        print("\n✅ 所有测试完成")
        
    except Exception as e:
        logger.error(f"测试执行出错: {e}")
        print(f"\n❌ 测试执行出错: {e}")


if __name__ == "__main__":
    try:
        # 设置asyncio日志级别，减少噪音
        asyncio_logger = logging.getLogger('asyncio')
        original_level = asyncio_logger.level
        asyncio_logger.setLevel(logging.WARNING)
        
        try:
            asyncio.run(main())
        finally:
            asyncio_logger.setLevel(original_level)
            
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
    finally:
        print("🏁 程序已退出")