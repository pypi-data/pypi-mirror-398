#!/bin/bash
# ColorBridge Linux安装脚本
# 用法: ./install_linux.sh [--user|--system]

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
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

# 检查root权限
check_root() {
    if [[ $EUID -eq 0 ]]; then
        IS_ROOT=true
    else
        IS_ROOT=false
    fi
}

# 安装方式选择
select_install_mode() {
    INSTALL_MODE="user"
    if [[ "$1" == "--system" ]]; then
        if [[ "$IS_ROOT" == "false" ]]; then
            log_error "系统安装需要root权限"
            log_error "请使用sudo或切换到root用户"
            exit 1
        fi
        INSTALL_MODE="system"
        log_info "选择系统安装模式"
    elif [[ "$1" == "--user" ]]; then
        INSTALL_MODE="user"
        log_info "选择用户安装模式"
    else
        if [[ "$IS_ROOT" == "true" ]]; then
            log_warning "检测到root权限，默认使用系统安装模式"
            log_warning "如需用户安装，请使用 --user 参数"
            INSTALL_MODE="system"
        else
            log_info "使用用户安装模式（默认）"
        fi
    fi
}

# 检查Python
check_python() {
    if command -v python3 &>/dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &>/dev/null; then
        python_version=$(python -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
        if [[ $(python -c "import sys; print(sys.version_info >= (3, 8))") == "True" ]]; then
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

# 安装系统依赖（Linux）
install_system_dependencies() {
    log_info "安装系统依赖..."
    
    # 检测包管理器
    if command -v apt &>/dev/null; then
        # Debian/Ubuntu
        log_info "检测到APT包管理器"
        sudo apt update
        
        # 基础依赖
        log_info "安装基础依赖..."
        sudo apt install -y python3-pip python3-venv python3-pyqt6 python3-serial
        
        # 游戏模块额外依赖（Qt6运行时库）
        log_info "安装游戏模块Qt6运行时依赖..."
        sudo apt install -y libqt6gui6 libqt6widgets6 libqt6core6 libqt6network6 qt6-qpa-plugins
        
        # 字体支持（游戏界面需要）
        log_info "安装字体支持..."
        sudo apt install -y fonts-liberation || log_warning "字体安装失败，游戏界面可能显示异常"
        
        # 尝试安装微软字体（可选）
        if [ -f /etc/debian_version ]; then
            log_info "尝试安装微软字体（游戏界面更好看）..."
            sudo apt install -y ttf-mscorefonts-installer || log_warning "微软字体安装失败，使用替代字体"
        fi
        
        log_success "系统依赖安装完成（包含游戏模块支持）"
        
    elif command -v yum &>/dev/null; then
        # RHEL/CentOS
        log_info "检测到YUM包管理器"
        sudo yum install -y python3-pip python3-venv python3-qt6 pyserial
        log_warning "RHEL/CentOS系统：游戏模块可能需要额外Qt6库，请手动安装"
        
    elif command -v dnf &>/dev/null; then
        # Fedora
        log_info "检测到DNF包管理器"
        sudo dnf install -y python3-pip python3-venv python3-qt6 pyserial
        log_warning "Fedora系统：游戏模块可能需要额外Qt6库，请手动安装"
        
    elif command -v pacman &>/dev/null; then
        # Arch Linux
        log_info "检测到Pacman包管理器"
        sudo pacman -S --noconfirm python-pip python-virtualenv python-pyqt6 pyserial qt6-base
        log_success "Arch Linux系统：已安装Qt6基础包"
        
    else
        log_warning "无法检测包管理器，跳过系统依赖安装"
        log_warning "请手动安装依赖:"
        log_warning "  Debian/Ubuntu: python3-pip python3-venv python3-pyqt6 python3-serial"
        log_warning "  游戏模块额外: libqt6gui6 libqt6widgets6 libqt6core6 libqt6network6 qt6-qpa-plugins"
        log_warning "  字体: fonts-liberation ttf-mscorefonts-installer"
    fi
    
    # 显示环境检查
    log_info "检查显示环境..."
    if [ -z "$DISPLAY" ]; then
        log_warning "未设置DISPLAY环境变量（无图形显示环境）"
        log_warning "游戏模块需要图形界面，请设置DISPLAY:"
        log_warning "  export DISPLAY=:0"
        log_warning "或安装虚拟显示服务器:"
        log_warning "  sudo apt install xvfb"
        log_warning "然后使用: xvfb-run python main.py"
    else
        log_success "显示环境正常: DISPLAY=$DISPLAY"
    fi
}

# 安装Python包
install_python_packages() {
    log_info "安装Python依赖包..."
    
    # 检查是否在虚拟环境中
    if [[ -n "$VIRTUAL_ENV" ]]; then
        log_info "检测到虚拟环境，使用虚拟环境安装模式"
        $PYTHON_CMD -m pip install .
    elif [[ "$INSTALL_MODE" == "system" ]]; then
        # 系统安装
        $PYTHON_CMD -m pip install .
    else
        # 用户安装
        $PYTHON_CMD -m pip install --user .
    fi
    
    if [ $? -eq 0 ]; then
        log_success "ColorBridge安装成功"
    else
        log_error "安装失败"
        return 1
    fi
}

# 配置串口权限
configure_serial_permissions() {
    log_info "配置串口权限..."
    
    # 检查用户是否在dialout组
    if groups $USER | grep -q "dialout"; then
        log_success "用户已在dialout组中"
    else
        log_warning "添加用户到dialout组..."
        if command -v sudo &>/dev/null; then
            sudo usermod -a -G dialout $USER
            if [ $? -eq 0 ]; then
                log_success "已添加用户到dialout组"
                log_warning "请注销并重新登录以使权限生效"
            else
                log_error "添加用户到dialout组失败"
            fi
        else
            log_error "未找到sudo命令，请手动添加用户到dialout组:"
            log_error "  usermod -a -G dialout $USER"
        fi
    fi
}

# 创建桌面快捷方式（Linux）
create_desktop_shortcut() {
    log_info "创建桌面快捷方式..."
    
    if [[ -d "/usr/share/applications" ]]; then
        DESKTOP_FILE="/usr/share/applications/colorbridge.desktop"
    elif [[ -d "$HOME/.local/share/applications" ]]; then
        DESKTOP_FILE="$HOME/.local/share/applications/colorbridge.desktop"
    else
        log_warning "未找到applications目录，跳过桌面快捷方式创建"
        return 0
    fi
    
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=ColorBridge
Comment=AI8051U串口助手
Exec=colorbridge
Icon=$SCRIPT_DIR/themes/icon.png
Categories=Development;Electronics;
Terminal=false
StartupNotify=true
EOF
    
    if [ $? -eq 0 ]; then
        log_success "桌面快捷方式创建成功: $DESKTOP_FILE"
    else
        log_warning "桌面快捷方式创建失败"
    fi
}

# 显示安装完成信息
show_completion_info() {
    echo ""
    log_success "🎉 ColorBridge 安装完成!"
    echo ""
    echo "📋 使用方式:"
    echo "  1. 命令行启动: colorbridge"
    echo "  2. 带参数启动: colorbridge --debug"
    echo "  3. 获取帮助: colorbridge --help"
    echo ""
    
    if [[ "$INSTALL_MODE" == "system" ]]; then
        echo "⚠️  注意: 串口权限需要重新登录才能生效"
    fi
    
    echo ""
    echo "🔧 故障排除:"
    echo "  - 如果提示'命令未找到'，请重新打开终端或运行: source ~/.bashrc"
    echo "  - 串口连接问题: 确保用户已在dialout组中"
    echo "  - GUI显示问题: 检查PyQt6安装"
    echo ""
}

# 主函数
main() {
    log_info "开始安装 ColorBridge v2.1.17..."
    
    # 检查root权限
    check_root
    
    # 选择安装模式
    select_install_mode "$1"
    
    # 检查Python
    if ! check_python; then
        exit 1
    fi
    
    # 安装系统依赖
    install_system_dependencies
    
    # 安装Python包
    if ! install_python_packages; then
        exit 1
    fi
    
    # 配置串口权限
    configure_serial_permissions
    
    # 创建桌面快捷方式
    create_desktop_shortcut
    
    # 显示完成信息
    show_completion_info
}

# 解析参数
case "$1" in
    -h|--help)
        echo "ColorBridge Linux安装脚本"
        echo "用法: $0 [选项]"
        echo "选项:"
        echo "  --user      用户安装（默认）"
        echo "  --system    系统安装（需要root权限）"
        echo "  -h, --help  显示此帮助信息"
        echo ""
        echo "示例:"
        echo "  $0           # 用户安装"
        echo "  sudo $0 --system  # 系统安装"
        exit 0
        ;;
esac

# 运行主函数
main "$@"