from setuptools import setup, find_packages

setup(
    name="tamar-model-client",
    version="0.4.6",
    description="A Python SDK for interacting with the Model Manager gRPC service",
    author="Oscar Ou",
    author_email="oscar.ou@tamaredge.ai",
    packages=find_packages(),
    include_package_data=True,  # 包含非 .py 文件
    package_data={
        "tamar_model_client": ["generated/*.py"],  # 包含 gRPC 生成文件
    },
    install_requires=[
        "grpcio~=1.67.1",
        "grpcio-tools~=1.67.1",
        "pydantic",
        "PyJWT",
        "nest_asyncio",
        "openai==2.8.1",
        "google-genai>=1.51.0",
        "anthropic>=0.68.0",
        "requests>=2.25.0",  # HTTP降级功能（同步）
        "aiohttp>=3.7.0",    # HTTP降级功能（异步）
    ],
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="http://gitlab.tamaredge.top/project-tap/AgentOS/model-manager-client",
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
