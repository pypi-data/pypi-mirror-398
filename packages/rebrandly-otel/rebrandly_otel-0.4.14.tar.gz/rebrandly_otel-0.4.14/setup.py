import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="rebrandly_otel",
    version="0.4.14",
    author="Antonio Romano",
    author_email="antonio@rebrandly.com",
    description="Python OTEL wrapper by Rebrandly",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.rebrandly.com/rebrandly/instrumentation/rebrandly-otel-python",
    packages=["rebrandly_otel"],
    package_dir={"rebrandly_otel": "src"},
    install_requires=[
        "opentelemetry-api>=1.35.0",
        "opentelemetry-sdk>=1.35.0",
        "opentelemetry-exporter-otlp>=1.35.0",
        "opentelemetry-semantic-conventions>=0.60b0",
        "opentelemetry-instrumentation-redis>=0.60b0",
        "opentelemetry-instrumentation-botocore>=0.48b0",
        "psutil>=5.0.0",
    ],
    extras_require={
        "flask": [
            "flask>=2.0.0",
            "werkzeug>=2.0.0"
        ],
        "fastapi": [
            "fastapi>=0.118.0",
            "starlette>=0.32.0",
            "uvicorn>=0.20.0"
        ],
        "all": [
            "flask>=2.0.0",
            "werkzeug>=2.0.0",
            "fastapi>=0.118.0",
            "starlette>=0.32.0",
            "uvicorn>=0.20.0"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
