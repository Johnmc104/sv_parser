# syntax=docker/dockerfile:1

# packaging/Dockerfile — manylinux2014 (CentOS 7, glibc 2.17) 构建环境
#
# 在 manylinux2014 上从源码编译 OpenSSL 3.0 + Python 3.11 (--enable-shared)
# 确保产出二进制兼容：
#   - CentOS 7  (glibc 2.17)
#   - RHEL 8+   (glibc 2.28)
#   - 其他 glibc >= 2.17 的 Linux
#
# 前置条件: packaging/src/ 下需要预下载源码包
#   - packaging/src/openssl-3.0.15.tar.gz
#   - packaging/src/Python-3.11.9.tgz
#
# 用法:
#   docker build -t rtl-scan-builder -f packaging/Dockerfile .
#   docker run --rm -v $PWD/dist:/out rtl-scan-builder
#
# 产出: dist/rtl_scan (单一可执行文件)

FROM quay.io/pypa/manylinux2014_x86_64

# OpenSSL 需要 perl-IPC-Cmd；Python 需要 libffi-devel (_ctypes)
RUN yum -y install perl-IPC-Cmd libffi-devel && yum clean all

# ── 阶段 1: 从源码编译 OpenSSL 3.0 ──────────────────────
ARG OPENSSL_VERSION=3.0.15
COPY packaging/src/openssl-${OPENSSL_VERSION}.tar.gz /tmp/
RUN tar xzf /tmp/openssl-${OPENSSL_VERSION}.tar.gz -C /tmp && \
    cd /tmp/openssl-${OPENSSL_VERSION} && \
    ./config --prefix=/opt/openssl --openssldir=/opt/openssl/ssl \
        shared no-tests && \
    make -j"$(nproc)" && \
    make install_sw && \
    rm -rf /tmp/openssl-${OPENSSL_VERSION}*

ENV LD_LIBRARY_PATH=/opt/openssl/lib64:/opt/openssl/lib

# ── 阶段 2: 从源码编译 Python 3.11 (--enable-shared) ────
ARG PYTHON_VERSION=3.11.9
ENV PKG_CONFIG_PATH=/opt/openssl/lib64/pkgconfig:/opt/openssl/lib/pkgconfig
COPY packaging/src/Python-${PYTHON_VERSION}.tgz /tmp/
RUN tar xzf /tmp/Python-${PYTHON_VERSION}.tgz -C /tmp && \
    cd /tmp/Python-${PYTHON_VERSION} && \
    LD_LIBRARY_PATH=/opt/openssl/lib64:/opt/openssl/lib \
    ./configure --enable-shared --prefix=/opt/cpython \
        --with-openssl=/opt/openssl \
        --with-openssl-rpath=auto \
        LDFLAGS="-Wl,-rpath,/opt/cpython/lib -L/opt/openssl/lib64 -L/opt/openssl/lib" \
        CPPFLAGS="-I/opt/openssl/include" && \
    LD_LIBRARY_PATH=/opt/openssl/lib64:/opt/openssl/lib \
    make -j"$(nproc)" && \
    make install && \
    rm -rf /tmp/Python-${PYTHON_VERSION}*

ENV PYTHON=/opt/cpython/bin/python3
ENV LD_LIBRARY_PATH=/opt/cpython/lib:/opt/openssl/lib64:/opt/openssl/lib
ENV PATH=/opt/cpython/bin:${PATH}

# 验证 ssl 模块可用
RUN ${PYTHON} -c "import ssl; print('SSL OK:', ssl.OPENSSL_VERSION)"

# 配置 pip 镜像（放在所有 pip install 之前）
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple/
ARG PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

# 升级 pip
RUN --mount=type=cache,target=/root/.cache/pip \
    ${PYTHON} -m pip install --upgrade pip setuptools wheel

# 安装 PyInstaller + antlr4 运行时
RUN --mount=type=cache,target=/root/.cache/pip \
    ${PYTHON} -m pip install pyinstaller==6.13.0 antlr4-python3-runtime==4.13.1

# ── 阶段 3: 复制项目源码并打包 ──────────────────────────
WORKDIR /build
COPY src/ src/
COPY verilog/VerilogLexer.py   verilog/VerilogLexer.py
COPY verilog/VerilogParser.py  verilog/VerilogParser.py
COPY verilog/VerilogParserVisitor.py verilog/VerilogParserVisitor.py
RUN touch verilog/__init__.py

COPY packaging/rtl_scan.spec packaging/rtl_scan.spec

# 构建
RUN ${PYTHON} -m PyInstaller --noconfirm --log-level WARN packaging/rtl_scan.spec

# 默认命令: 复制产出到挂载的 /out
CMD ["sh", "-c", "cp /build/dist/rtl_scan /out/ && chmod +x /out/rtl_scan && echo \"Output: /out/rtl_scan ($(du -h /out/rtl_scan | cut -f1))\""]
