from setuptools import setup, find_packages

setup(
    name="qris-payment",
    version="1.1.6",
    packages=find_packages(),
    install_requires=[
        "qrcode>=7.4.2",
        "Pillow>=9.0.0",
        "requests>=2.28.0",
    ],
    author="AutoFtBot",
    author_email="autoftbot@gmail.com",
    description="Package Python untuk generate QRIS dan cek status pembayaran",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/AutoFtBot/qris-payment-py",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
) 