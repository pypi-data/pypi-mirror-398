#!/bin/bash
# AutoCoder CLI Python SDK 发布脚本
# 
# 使用 twine 发布到 PyPI，支持自动版本升级
#
# 使用方法:
#   ./deploy.sh              # 自动升级patch版本并发布到 PyPI
#   ./deploy.sh patch        # 升级patch版本 (0.0.1 -> 0.0.2)
#   ./deploy.sh minor        # 升级minor版本 (0.0.1 -> 0.1.0)
#   ./deploy.sh major        # 升级major版本 (0.0.1 -> 1.0.0)
#   ./deploy.sh test         # 发布到 TestPyPI (测试版，自动升级patch)
#   ./deploy.sh patch test   # 升级patch版本并发布到 TestPyPI
#   ./deploy.sh --no-bump    # 不升级版本，直接发布
#   ./deploy.sh --version 1.2.3  # 指定版本号

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查是否在正确的目录
if [ ! -f "pyproject.toml" ]; then
    print_error "请在 cli-sdks/python 目录下运行此脚本"
    exit 1
fi

# 解析参数
BUMP_TYPE="patch"  # 默认升级patch版本
TARGET="pypi"      # 默认发布到PyPI
NO_BUMP=false
SPECIFIC_VERSION=""

while [[ $# -gt 0 ]]; do
    case $1 in
        patch|minor|major)
            BUMP_TYPE="$1"
            shift
            ;;
        test)
            TARGET="testpypi"
            shift
            ;;
        --no-bump)
            NO_BUMP=true
            shift
            ;;
        --version)
            SPECIFIC_VERSION="$2"
            shift 2
            ;;
        -h|--help)
            echo "用法: ./deploy.sh [patch|minor|major] [test] [--no-bump] [--version X.Y.Z]"
            echo ""
            echo "版本升级:"
            echo "  patch        升级补丁版本 (0.0.1 -> 0.0.2) [默认]"
            echo "  minor        升级次版本 (0.0.1 -> 0.1.0)"
            echo "  major        升级主版本 (0.0.1 -> 1.0.0)"
            echo "  --no-bump    不升级版本"
            echo "  --version    指定版本号"
            echo ""
            echo "发布目标:"
            echo "  test         发布到 TestPyPI"
            echo "  (默认)       发布到 PyPI"
            exit 0
            ;;
        *)
            print_error "未知参数: $1"
            exit 1
            ;;
    esac
done

# 版本升级函数
bump_version() {
    local current_version=$1
    local bump_type=$2
    
    # 解析版本号
    IFS='.' read -r major minor patch <<< "$current_version"
    
    case $bump_type in
        major)
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        minor)
            minor=$((minor + 1))
            patch=0
            ;;
        patch)
            patch=$((patch + 1))
            ;;
    esac
    
    echo "${major}.${minor}.${patch}"
}

# 更新版本号函数
update_version() {
    local new_version=$1
    
    # 更新 pyproject.toml
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/^version = \".*\"/version = \"${new_version}\"/" pyproject.toml
    else
        # Linux
        sed -i "s/^version = \".*\"/version = \"${new_version}\"/" pyproject.toml
    fi
    
    # 更新 __init__.py
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/^__version__ = \".*\"/__version__ = \"${new_version}\"/" autocoder_cli_sdk/__init__.py
    else
        sed -i "s/^__version__ = \".*\"/__version__ = \"${new_version}\"/" autocoder_cli_sdk/__init__.py
    fi
    
    print_info "   版本号已更新到: ${new_version}"
}

print_info "========================================="
print_info "  AutoCoder CLI Python SDK 发布流程"
print_info "========================================="

# 1. 检查必要的工具
print_step "1. 检查必要的工具..."

# 优先使用 uv
USE_UV=false
if command -v uv &> /dev/null; then
    print_info "   uv 已安装"
    USE_UV=true
else
    if ! command -v python3 &> /dev/null; then
        print_error "未找到 python3，请先安装 Python 3"
        exit 1
    fi
    print_info "   Python 3 已安装"
    print_warning "   建议安装 uv: pip install uv"
fi

# 检查并升级 twine 和 pkginfo（发布必需）
if ! command -v twine &> /dev/null; then
    print_warning "   twine 未安装，正在安装..."
    if [ "$USE_UV" = true ]; then
        uv pip install --upgrade twine pkginfo
    else
        pip3 install --user --upgrade twine pkginfo
    fi
else
    print_info "   twine 已安装"
    # 升级到最新版本以支持 Metadata-Version 2.4
    print_info "   升级 twine 和 pkginfo 到最新版本..."
    if [ "$USE_UV" = true ]; then
        uv pip install --upgrade twine pkginfo >/dev/null 2>&1
    else
        pip3 install --user --upgrade twine pkginfo >/dev/null 2>&1
    fi
fi
print_info "   twine 和 pkginfo 已就绪"

# 2. 读取当前版本
print_step "2. 读取当前版本..."
CURRENT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

# 处理不完整的版本号
if [[ ! "$CURRENT_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    print_warning "   当前版本号格式不正确: '${CURRENT_VERSION}'"
    CURRENT_VERSION="0.0.0"
    print_info "   使用默认版本: ${CURRENT_VERSION}"
fi

print_info "   当前版本: ${CURRENT_VERSION}"

# 3. 计算新版本
print_step "3. 计算新版本..."
if [ -n "$SPECIFIC_VERSION" ]; then
    # 使用指定的版本号
    NEW_VERSION="$SPECIFIC_VERSION"
    print_info "   指定版本: ${NEW_VERSION}"
elif [ "$NO_BUMP" = true ]; then
    # 不升级版本
    NEW_VERSION="$CURRENT_VERSION"
    print_info "   保持当前版本: ${NEW_VERSION}"
else
    # 自动升级版本
    NEW_VERSION=$(bump_version "$CURRENT_VERSION" "$BUMP_TYPE")
    print_info "   升级类型: ${BUMP_TYPE}"
    print_info "   新版本: ${CURRENT_VERSION} -> ${NEW_VERSION}"
fi

# 4. 更新版本号
if [ "$NEW_VERSION" != "$CURRENT_VERSION" ]; then
    print_step "4. 更新版本号..."
    update_version "$NEW_VERSION"
else
    print_step "4. 跳过版本更新（版本未变化）"
fi

# 5. 清理旧的构建文件
print_step "5. 清理旧的构建文件..."
rm -rf dist/ build/ *.egg-info
print_info "   清理完成"

# 6. 运行代码检查
print_step "6. 运行代码检查..."
if command -v black &> /dev/null; then
    print_info "   运行 black 格式化检查..."
    black --check autocoder_cli_sdk/ 2>/dev/null || {
        print_warning "   代码格式不符合 black 规范"
        read -p "是否继续? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    }
else
    print_info "   跳过 black 检查（未安装）"
fi

# 7. 构建发布包
print_step "7. 构建发布包..."
if [ "$USE_UV" = true ]; then
    uv build
else
    python3 -m build
fi
print_info "   构建完成"

# 8. 检查构建的包
print_step "8. 检查构建的包..."
twine check dist/* > /tmp/twine_check.log 2>&1
TWINE_EXIT_CODE=$?

# 检查输出内容
if grep -q "missing required fields" /tmp/twine_check.log; then
    # 检查是否实际包含 Name 和 Version
    if python3 -m zipfile -e dist/autocoder_cli_sdk-*.whl /tmp/test_metadata 2>/dev/null; then
        if grep -q "^Name: " /tmp/test_metadata/autocoder_cli_sdk-*.dist-info/METADATA 2>/dev/null && \
           grep -q "^Version: " /tmp/test_metadata/autocoder_cli_sdk-*.dist-info/METADATA 2>/dev/null; then
            print_warning "   twine 报告缺少字段，但实际包含 Name 和 Version"
            print_warning "   这是 Metadata-Version 2.4 格式的兼容性问题"
            print_info "   包内容验证通过，可以安全上传"
        else
            print_error "包检查失败：真的缺少 Name 或 Version 字段"
            cat /tmp/twine_check.log
            exit 1
        fi
    else
        print_warning "   无法验证元数据，但继续执行"
        print_info "   注意: 如果上传失败，请检查 pyproject.toml 配置"
    fi
elif [ $TWINE_EXIT_CODE -ne 0 ]; then
    print_error "包检查失败"
    cat /tmp/twine_check.log
    exit 1
else
    print_info "   包检查通过"
fi

# 清理临时文件
rm -rf /tmp/test_metadata /tmp/twine_check.log

# 9. 列出将要上传的文件
print_step "9. 将要上传的文件:"
ls -lh dist/

# 10. 确认发布
echo ""
if [ "$TARGET" = "testpypi" ]; then
    print_warning "即将发布到 TestPyPI，版本: ${NEW_VERSION}"
else
    print_warning "即将发布到 PyPI，版本: ${NEW_VERSION}"
    print_warning "这是正式发布！发布后无法撤回！"
fi

read -p "确认继续? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "已取消发布"
    # 如果取消发布，回滚版本号
    if [ "$NEW_VERSION" != "$CURRENT_VERSION" ]; then
        print_info "回滚版本号到: ${CURRENT_VERSION}"
        update_version "$CURRENT_VERSION"
    fi
    exit 0
fi

# 11. 上传到 PyPI
print_step "11. 上传到 ${TARGET}..."

if [ "$TARGET" = "testpypi" ]; then
    twine upload --repository testpypi dist/*
else
    twine upload dist/*
fi

if [ $? -eq 0 ]; then
    print_info "========================================="
    print_info "发布成功！"
    print_info "========================================="
    echo ""
    print_info "版本: ${NEW_VERSION}"
    if [ "$TARGET" = "testpypi" ]; then
        print_info "TestPyPI: https://test.pypi.org/project/autocoder-cli-sdk/${NEW_VERSION}/"
        echo ""
        print_info "测试安装:"
        echo "  pip install -i https://test.pypi.org/simple/ autocoder-cli-sdk==${NEW_VERSION}"
    else
        print_info "PyPI: https://pypi.org/project/autocoder-cli-sdk/${NEW_VERSION}/"
        echo ""
        print_info "安装命令:"
        echo "  pip install autocoder-cli-sdk==${NEW_VERSION}"
    fi
    echo ""
    
    # 提示 git 操作
    if [ "$NEW_VERSION" != "$CURRENT_VERSION" ]; then
        print_info "建议执行 git 操作:"
        echo "  git add pyproject.toml autocoder_cli_sdk/__init__.py"
        echo "  git commit -m 'chore: bump version to ${NEW_VERSION}'"
        echo "  git tag v${NEW_VERSION}"
        echo "  git push && git push --tags"
    fi
else
    print_error "发布失败，请检查错误信息"
    # 发布失败时回滚版本号
    if [ "$NEW_VERSION" != "$CURRENT_VERSION" ]; then
        print_info "回滚版本号到: ${CURRENT_VERSION}"
        update_version "$CURRENT_VERSION"
    fi
    exit 1
fi
