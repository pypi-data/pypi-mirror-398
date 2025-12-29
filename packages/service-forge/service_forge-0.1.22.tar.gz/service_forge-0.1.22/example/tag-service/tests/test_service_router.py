#!/usr/bin/env python3
"""
Service Router 测试脚本
用于测试 service_router 的功能：
1. 查看 service 状态
2. 启动 workflow
3. 停止 workflow
4. 上传 workflow 配置文件并加载
"""
import asyncio
import json
import sys
import argparse
from pathlib import Path
from typing import Optional
import httpx


class ServiceRouterTester:
    def __init__(self, base_url: str = "http://localhost:37200"):
        self.base_url = base_url.rstrip('/')
        # 尝试两种可能的路径格式
        self.service_base_paths = [
            f"{self.base_url}/sdk/service",  # 如果没有 root_path
            f"{self.base_url}/api/v1/tag-service-0.0.1/sdk/service",  # 如果有 root_path
        ]
        self.service_path = None
    
    async def _find_service_path(self) -> bool:
        """尝试找到正确的 service API 路径"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            for path in self.service_base_paths:
                try:
                    response = await client.get(f"{path}/status")
                    if response.status_code == 200:
                        self.service_path = path
                        print(f"✅ 找到 service API 路径: {path}")
                        return True
                except Exception as e:
                    continue
        return False
    
    async def get_service_status(self) -> Optional[dict]:
        """获取 service 状态"""
        if not self.service_path:
            if not await self._find_service_path():
                print("❌ 无法找到 service API 路径")
                return None
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(f"{self.service_path}/status")
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f"❌ HTTP 错误: {e.response.status_code} - {e.response.text}")
                return None
            except Exception as e:
                print(f"❌ 发生错误: {e}")
                return None
    
    async def start_workflow(self, workflow_name: str) -> bool:
        """启动指定的 workflow"""
        if not self.service_path:
            if not await self._find_service_path():
                print("❌ 无法找到 service API 路径")
                return False
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(f"{self.service_path}/workflow/{workflow_name}/start")
                response.raise_for_status()
                result = response.json()
                if result.get("success"):
                    print(f"✅ {result.get('message', 'Workflow started successfully')}")
                    return True
                else:
                    print(f"❌ {result.get('message', 'Failed to start workflow')}")
                    return False
            except httpx.HTTPStatusError as e:
                print(f"❌ HTTP 错误: {e.response.status_code} - {e.response.text}")
                return False
            except Exception as e:
                print(f"❌ 发生错误: {e}")
                return False
    
    async def stop_workflow(self, workflow_name: str) -> bool:
        """停止指定的 workflow"""
        if not self.service_path:
            if not await self._find_service_path():
                print("❌ 无法找到 service API 路径")
                return False
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(f"{self.service_path}/workflow/{workflow_name}/stop")
                response.raise_for_status()
                result = response.json()
                if result.get("success"):
                    print(f"✅ {result.get('message', 'Workflow stopped successfully')}")
                    return True
                else:
                    print(f"❌ {result.get('message', 'Failed to stop workflow')}")
                    return False
            except httpx.HTTPStatusError as e:
                print(f"❌ HTTP 错误: {e.response.status_code} - {e.response.text}")
                return False
            except Exception as e:
                print(f"❌ 发生错误: {e}")
                return False
    
    async def upload_workflow_config(self, config_path: str, workflow_name: Optional[str] = None) -> bool:
        """上传 workflow 配置文件并加载"""
        if not self.service_path:
            if not await self._find_service_path():
                print("❌ 无法找到 service API 路径")
                return False
        
        config_file = Path(config_path)
        if not config_file.exists():
            print(f"❌ 配置文件不存在: {config_path}")
            return False
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                with open(config_file, 'rb') as f:
                    files = {'file': (config_file.name, f, 'application/x-yaml')}
                    data = {}
                    if workflow_name:
                        data['workflow_name'] = workflow_name
                    
                    response = await client.post(
                        f"{self.service_path}/workflow/upload",
                        files=files,
                        data=data
                    )
                    response.raise_for_status()
                    result = response.json()
                    if result.get("success"):
                        print(f"✅ {result.get('message', 'Workflow uploaded and loaded successfully')}")
                        return True
                    else:
                        print(f"❌ {result.get('message', 'Failed to upload workflow')}")
                        return False
            except httpx.HTTPStatusError as e:
                print(f"❌ HTTP 错误: {e.response.status_code} - {e.response.text}")
                return False
            except Exception as e:
                print(f"❌ 发生错误: {e}")
                return False


async def test_all(tester: ServiceRouterTester):
    """运行所有测试"""
    print("=" * 60)
    print("开始测试 Service Router 功能")
    print("=" * 60)
    
    # 1. 测试获取 service 状态
    print("\n📊 测试 1: 获取 service 状态")
    print("-" * 60)
    status = await tester.get_service_status()
    if status:
        print(f"Service 名称: {status.get('name')}")
        print(f"Service 版本: {status.get('version')}")
        print(f"Service 描述: {status.get('description')}")
        print(f"\nWorkflows:")
        for workflow in status.get('workflows', []):
            status_icon = "🟢" if workflow.get('status') == 'running' else "🔴"
            print(f"  {status_icon} {workflow.get('name')}: {workflow.get('status')} (配置: {workflow.get('config_path')})")
    else:
        print("❌ 无法获取 service 状态")
        return
    
    # 2. 测试停止 workflow（如果正在运行）
    print("\n🛑 测试 2: 停止 workflow")
    print("-" * 60)
    workflow_name = "query_tags_workflow"
    print(f"尝试停止 workflow: {workflow_name}")
    await tester.stop_workflow(workflow_name)
    await asyncio.sleep(1)  # 等待一下
    
    # 3. 测试启动 workflow
    print("\n▶️  测试 3: 启动 workflow")
    print("-" * 60)
    print(f"尝试启动 workflow: {workflow_name}")
    await tester.start_workflow(workflow_name)
    await asyncio.sleep(1)  # 等待一下
    
    # 4. 再次查看状态，确认 workflow 已启动
    print("\n📊 测试 4: 再次查看 service 状态（确认 workflow 已启动）")
    print("-" * 60)
    status = await tester.get_service_status()
    if status:
        for workflow in status.get('workflows', []):
            if workflow.get('name') == workflow_name:
                status_icon = "🟢" if workflow.get('status') == 'running' else "🔴"
                print(f"  {status_icon} {workflow.get('name')}: {workflow.get('status')}")
    
    # 5. 测试上传 workflow 配置文件
    print("\n📤 测试 5: 上传 workflow 配置文件")
    print("-" * 60)
    config_path = Path(__file__).parent / "configs" / "workflow" / "query_tags_workflow.yaml"
    if config_path.exists():
        print(f"上传配置文件: {config_path}")
        await tester.upload_workflow_config(str(config_path))
    else:
        print(f"⚠️  配置文件不存在: {config_path}，跳过上传测试")
    
    # 6. 最终状态查看
    print("\n📊 测试 6: 最终状态查看")
    print("-" * 60)
    status = await tester.get_service_status()
    if status:
        print(f"Service 状态:")
        print(json.dumps(status, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Service Router 测试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 运行所有测试
  python test_service_router.py
  
  # 指定服务地址
  python test_service_router.py --base-url http://localhost:37200
  
  # 只查看状态
  python test_service_router.py --status-only
  
  # 启动特定 workflow
  python test_service_router.py --start-workflow query_tags_workflow
  
  # 停止特定 workflow
  python test_service_router.py --stop-workflow query_tags_workflow
  
  # 上传配置文件
  python test_service_router.py --upload-config configs/workflow/query_tags_workflow.yaml
        """
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:37200",
        help="Service 基础 URL (默认: http://localhost:37200)"
    )
    parser.add_argument(
        "--status-only",
        action="store_true",
        help="只查看 service 状态"
    )
    parser.add_argument(
        "--start-workflow",
        type=str,
        help="启动指定的 workflow"
    )
    parser.add_argument(
        "--stop-workflow",
        type=str,
        help="停止指定的 workflow"
    )
    parser.add_argument(
        "--upload-config",
        type=str,
        help="上传并加载 workflow 配置文件"
    )
    parser.add_argument(
        "--workflow-name",
        type=str,
        help="上传配置文件时指定的 workflow 名称（可选）"
    )
    
    args = parser.parse_args()
    
    tester = ServiceRouterTester(base_url=args.base_url)
    
    try:
        if args.status_only:
            # 只查看状态
            status = await tester.get_service_status()
            if status:
                print(json.dumps(status, indent=2, ensure_ascii=False))
        elif args.start_workflow:
            # 启动 workflow
            await tester.start_workflow(args.start_workflow)
        elif args.stop_workflow:
            # 停止 workflow
            await tester.stop_workflow(args.stop_workflow)
        elif args.upload_config:
            # 上传配置文件
            await tester.upload_workflow_config(args.upload_config, args.workflow_name)
        else:
            # 运行所有测试
            await test_all(tester)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

