from setuptools import setup, find_packages

setup(
    name="briefcase-ai",
    version="0.1.0",
    description="Deterministic observability & replay for AI systems",
    author="briefcase-ai Contributors",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "sqlalchemy>=2.0.0",
        "alembic>=1.11.0",
        "httpx>=0.24.0",
        "click>=8.1.0",
        "python-multipart>=0.0.6",
        "websockets>=11.0.0",
        "aiofiles>=23.0.0",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "email-validator>=2.0.0",
        "lz4>=4.0.0",
        "cryptography>=41.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "ruff>=0.0.270",
        ],
        "enterprise": [
            "python-saml>=1.15.0",
            "ldap3>=2.9.0",
        ]
    },
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "briefcase-ai=briefcase.cli:main",
        ],
    },
)
