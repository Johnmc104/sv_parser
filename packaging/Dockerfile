# syntax=docker/dockerfile:1

# packaging/Dockerfile — manylinux2014 (CentOS 7, glibc 2.17) 构建环境
#
# 基于 manylinux2014 镜像，自带 Python 3.11 + 低版本 glibc。
# 确保产出二进制兼容：
#   - CentOS 7  (glibc 2.17)
#   - RHEL 8+   (glibc 2.28)
#   - 其他 glibc >= 2.17 的 Linux
#
# 用法:
#   docker build -t rtl-scan-builder -f packaging/Dockerfile .
#   docker run --rm -v $PWD/dist:/out rtl-scan-builder
#
# 产出: dist/rtl_scan (单一可执行文件)

FROM quay.io/pypa/manylinux2014_x86_64

# 使用镜像自带的 Python 3.11 (cpython-3.11 in /opt/python/)
ENV PYTHON=/opt/python/cp311-cp311/bin/python3
ENV PATH=/opt/python/cp311-cp311/bin:${PATH}

# 验证 Python
RUN ${PYTHON} --version && ${PYTHON} -c "import ssl; print('SSL OK:', ssl.OPENSSL_VERSION)"

# 升级 pip
RUN --mount=type=cache,target=/root/.cache/pip \
    ${PYTHON} -m pip install --upgrade pip setuptools wheel

# 配置 pip 镜像
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple/
ARG PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

# 安装 PyInstaller + antlr4 运行时
RUN --mount=type=cache,target=/root/.cache/pip \
    ${PYTHON} -m pip install pyinstaller==6.13.0 antlr4-python3-runtime==4.13.1

# 复制项目源码
WORKDIR /build
COPY src/ src/
COPY verilog/VerilogLexer.py   verilog/VerilogLexer.py
COPY verilog/VerilogParser.py  verilog/VerilogParser.py
COPY verilog/VerilogParserVisitor.py verilog/VerilogParserVisitor.py
# verilog 包需要 __init__.py（如不存在则创建空文件）
RUN touch verilog/__init__.py

# 复制打包配置
COPY packaging/rtl_scan.spec packaging/rtl_scan.spec

# 构建
RUN ${PYTHON} -m PyInstaller --noconfirm --log-level WARN packaging/rtl_scan.spec

# 默认命令: 复制产出到挂载的 /out
CMD cp /build/dist/rtl_scan /out/ && \
    chmod +x /out/rtl_scan && \
    echo "Output: /out/rtl_scan ($(du -h /out/rtl_scan | cut -f1))"
