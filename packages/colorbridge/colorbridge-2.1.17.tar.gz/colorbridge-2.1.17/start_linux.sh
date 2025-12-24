#!/bin/bash
# ColorBridge Linux启动脚本
# 用法: ./start_linux.sh [选项]

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Python
check_python() {
    if command -v python3 &>/dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &>/dev/null; then
        # 检查Python版本
        python_version=$(python -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
        if [ "$(python -c "import sys; print(sys.version_info >= (3, 8))")" = "True" ]; then
            PYTHON_CMD="python"
        else
            log_error "Python版本过低 (需要 >= 3.8，当前: $python_version)"
            return 1
        fi
    else
        log_error "未找到Python 3.8+"
        return 1
    fi
    log_info "使用Python: $($PYTHON_CMD --version)"
    return 0
}

# 检查依赖
check_dependencies() {
    log_info "检查Python依赖..."
    if $PYTHON_CMD -c "import PyQt6, serial, dateutil" 2>/dev/null; then
        log_success "所有依赖已安装"
    else
        log_warning "缺少依赖，正在安装..."
        if [ -f "requirements.txt" ]; then
            $PYTHON_CMD -m pip install -r requirements.txt
            if [ $? -eq 0 ]; then
                log_success "依赖安装成功"
            else
                log_error "依赖安装失败"
                return 1
            fi
        else
            log_error "未找到requirements.txt"
            return 1
        fi
    fi
    return 0
}

# 检查串口权限
check_serial_permissions() {
    log_info "检查串口权限..."
    
    # 方法1: 使用groups命令
    if groups $USER 2>/dev/null | grep -q "dialout"; then
        log_success "用户已在dialout组中"
        return 0
    fi
    
    # 方法2: 检查/etc/group文件
    if grep -q "^dialout:.*$USER" /etc/group 2>/dev/null; then
        log_success "用户已在dialout组中"
        return 0
    fi
    
    # 方法3: 检查用户组ID
    if id -nG "$USER" 2>/dev/null | grep -q "dialout"; then
        log_success "用户已在dialout组中"
        return 0
    fi
    
    # 用户不在dialout组中
    log_warning "用户不在dialout组中，串口访问可能受限"
    log_warning "请运行以下命令添加用户到dialout组:"
    log_warning "  sudo usermod -a -G dialout $USER"
    log_warning "然后注销并重新登录以使权限生效"
    log_warning ""
    log_warning "或者临时使用sudo运行程序:"
    log_warning "  sudo $0 $@"
    log_warning ""
    log_warning "注意: 使用sudo运行可能会影响文件权限"
    
    # 询问用户是否继续
    read -p "是否继续运行程序? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "用户选择退出"
        exit 1
    fi
    
    log_warning "继续运行程序，串口连接可能失败"
    return 1
}

# 主函数
main() {
    log_info "启动 ColorBridge v2.1.17..."
    
    # 检查Python
    if ! check_python; then
        exit 1
    fi
    
    # 检查依赖
    if ! check_dependencies; then
        exit 1
    fi
    
    # 检查串口权限
    check_serial_permissions
    
    # 创建logs目录
    if [ ! -d "logs" ]; then
        mkdir -p logs
        log_info "创建logs目录"
    fi
    
    # 运行ColorBridge
    log_info "启动ColorBridge..."
    log_info "使用命令: $PYTHON_CMD main.py $@"
    echo "========================================"
    exec $PYTHON_CMD main.py "$@"
}

# 解析参数
while [ $# -gt 0 ]; do
    case $1 in
        -h|--help)
            echo "ColorBridge Linux启动脚本"
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  -h, --help     显示此帮助信息"
            echo "  -d, --debug    调试模式"
            echo "  -q, --quiet    静默模式"
            echo "  -v, --version  版本信息"
            echo ""
            echo "示例:"
            echo "  $0              # 正常启动"
            echo "  $0 --debug     # 调试模式"
            echo "  $0 --quiet     # 静默模式"
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

# 运行主函数
main "$@"