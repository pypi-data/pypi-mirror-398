from setuptools import setup, find_packages

setup(
    name="agentpay-sdk-python",
    version="0.1.0",
    description="Infraestructura financiera universal para Agentes de IA",
    author="Jairo Gelpi",
    author_email="jairo.gelpi@agentpay.io",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",  # Instalará requests automáticamente
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)