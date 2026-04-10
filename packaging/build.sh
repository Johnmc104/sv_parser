#!/usr/bin/env bash
# packaging/build.sh — 构建 rtl_scan 单一二进制
#
# 用法:
#   ./packaging/build.sh          # Docker 构建（推荐，确保 CentOS 7 兼容）
#   ./packaging/build.sh --local  # 本地构建（仅当前 glibc 兼容）
#
# 产出: dist/rtl_scan
#
# 兼容性:
#   Docker 构建: CentOS 7+ / RHEL 8+ (glibc >= 2.17)
#   本地构建:    仅当前系统 glibc 及以上

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
IMAGE_NAME="rtl-scan-builder"
OUTPUT_DIR="${PROJECT_ROOT}/dist"

cd "${PROJECT_ROOT}"

# ----------------------------------------------------------------
# 颜色输出
# ----------------------------------------------------------------
info()  { printf '\033[1;34m[INFO]\033[0m  %s\n' "$*"; }
ok()    { printf '\033[1;32m[OK]\033[0m    %s\n' "$*"; }
err()   { printf '\033[1;31m[ERR]\033[0m   %s\n' "$*" >&2; }

# ----------------------------------------------------------------
# Docker 构建（默认）
# ----------------------------------------------------------------
build_docker() {
    info "检查 Docker..."
    if ! command -v docker &>/dev/null; then
        err "Docker 未安装。请安装 Docker 或使用 --local 模式。"
        exit 1
    fi

    info "构建 Docker 镜像 (manylinux2014 / CentOS 7 / glibc 2.17)..."
    docker build \
        -t "${IMAGE_NAME}" \
        -f packaging/Dockerfile \
        .

    mkdir -p "${OUTPUT_DIR}"
    rm -f "${OUTPUT_DIR}/rtl_scan" 2>/dev/null || true

    info "提取二进制..."
    docker run --rm \
        -u "$(id -u):$(id -g)" \
        -v "${OUTPUT_DIR}:/out" \
        "${IMAGE_NAME}"

    if [[ -f "${OUTPUT_DIR}/rtl_scan" ]]; then
        chmod +x "${OUTPUT_DIR}/rtl_scan"
        local size
        size=$(du -h "${OUTPUT_DIR}/rtl_scan" | cut -f1)
        ok "构建成功: dist/rtl_scan (${size})"
        info "兼容: CentOS 7+ / RHEL 8+ (glibc >= 2.17)"

        # 显示 glibc 需求
        local max_glibc
        max_glibc=$(objdump -T "${OUTPUT_DIR}/rtl_scan" 2>/dev/null \
            | grep -oP 'GLIBC_[0-9.]+' | sort -V | tail -1 || true)
        if [[ -n "${max_glibc}" ]]; then
            info "二进制 glibc 需求: ${max_glibc}"
        fi
    else
        err "构建失败：dist/rtl_scan 未生成"
        exit 1
    fi
}

# ----------------------------------------------------------------
# 本地构建
# ----------------------------------------------------------------
build_local() {
    info "本地构建模式（仅兼容当前系统 glibc 及以上）"

    local glibc_ver
    glibc_ver=$(ldd --version 2>&1 | head -1 | grep -oP '[0-9]+\.[0-9]+$' || echo "unknown")
    info "当前系统 glibc: ${glibc_ver}"

    # 查找 Python
    local py=""
    for candidate in python3.11 python3 python; do
        if command -v "${candidate}" &>/dev/null; then
            py="${candidate}"
            break
        fi
    done
    if [[ -z "${py}" ]]; then
        err "未找到 Python 3。请安装 Python 3.6+。"
        exit 1
    fi
    info "Python: $(${py} --version 2>&1)"

    # 确保 PyInstaller 已安装
    if ! ${py} -m PyInstaller --version &>/dev/null 2>&1; then
        info "安装 PyInstaller..."
        ${py} -m pip install pyinstaller
    fi

    # 确保 antlr4 运行时已安装
    if ! ${py} -c "import antlr4" &>/dev/null 2>&1; then
        info "安装 antlr4-python3-runtime..."
        ${py} -m pip install antlr4-python3-runtime==4.13.1
    fi

    info "开始打包 rtl_scan..."
    ${py} -m PyInstaller --noconfirm --log-level WARN packaging/rtl_scan.spec

    if [[ -f "${OUTPUT_DIR}/rtl_scan" ]]; then
        chmod +x "${OUTPUT_DIR}/rtl_scan"
        local size
        size=$(du -h "${OUTPUT_DIR}/rtl_scan" | cut -f1)
        ok "构建成功: dist/rtl_scan (${size})"

        local max_glibc
        max_glibc=$(objdump -T "${OUTPUT_DIR}/rtl_scan" 2>/dev/null \
            | grep -oP 'GLIBC_[0-9.]+' | sort -V | tail -1 || true)
        if [[ -n "${max_glibc}" ]]; then
            info "二进制 glibc 需求: ${max_glibc}"
        fi
    else
        err "构建失败：dist/rtl_scan 未生成"
        exit 1
    fi
}

# ----------------------------------------------------------------
# 入口
# ----------------------------------------------------------------
case "${1:-}" in
    --local)
        build_local
        ;;
    *)
        build_docker
        ;;
esac
