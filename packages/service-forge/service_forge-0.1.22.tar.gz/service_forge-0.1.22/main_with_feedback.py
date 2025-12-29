"""
演示如何启用自动反馈收集
"""

import asyncio
from dotenv import load_dotenv
from service_forge.service import Service
from service_forge.sft.config.sf_metadata import SfMetadata

async def main():
    load_dotenv()

    metadata = SfMetadata(
        name="example_service",
        version="0.0.1",
        description="Example service with auto feedback",
        service_config="./configs/service/test_service.yaml",
        config_only=False,
        env=[],
    )

    service = Service.from_config(metadata, service_env={})
    await service.start()

if __name__ == "__main__":
    asyncio.run(main())
