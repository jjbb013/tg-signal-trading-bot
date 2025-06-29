#!/bin/bash

# 手动启动supervisor程序脚本
echo "=== 手动启动Telegram机器人 ==="
echo "时间: $(date)"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查supervisor是否运行
check_supervisor() {
    if ! pgrep supervisord > /dev/null; then
        log_error "Supervisor未运行，请先启动supervisor"
        exit 1
    fi
    log_info "Supervisor正在运行"
}

# 检查程序状态
check_status() {
    log_info "检查程序状态..."
    supervisorctl status listener
}

# 启动程序
start_program() {
    log_info "启动listener程序..."
    supervisorctl start listener
    
    # 等待几秒检查状态
    sleep 3
    check_status
}

# 停止程序
stop_program() {
    log_info "停止listener程序..."
    supervisorctl stop listener
    
    # 等待几秒检查状态
    sleep 3
    check_status
}

# 重启程序
restart_program() {
    log_info "重启listener程序..."
    supervisorctl restart listener
    
    # 等待几秒检查状态
    sleep 3
    check_status
}

# 查看日志
show_logs() {
    log_info "显示程序日志..."
    echo "=== 最近50行日志 ==="
    supervisorctl tail -f listener | head -50
}

# 主菜单
show_menu() {
    echo ""
    echo "请选择操作:"
    echo "1) 检查程序状态"
    echo "2) 启动程序"
    echo "3) 停止程序"
    echo "4) 重启程序"
    echo "5) 查看日志"
    echo "6) 退出"
    echo ""
}

# 主函数
main() {
    check_supervisor
    
    while true; do
        show_menu
        read -p "请输入选项 (1-6): " choice
        
        case $choice in
            1)
                check_status
                ;;
            2)
                start_program
                ;;
            3)
                stop_program
                ;;
            4)
                restart_program
                ;;
            5)
                show_logs
                ;;
            6)
                log_info "退出脚本"
                exit 0
                ;;
            *)
                log_error "无效选项，请重新选择"
                ;;
        esac
        
        echo ""
        read -p "按回车键继续..."
    done
}

# 如果传入了参数，直接执行对应操作
case "${1:-}" in
    "start")
        check_supervisor
        start_program
        ;;
    "stop")
        check_supervisor
        stop_program
        ;;
    "restart")
        check_supervisor
        restart_program
        ;;
    "status")
        check_supervisor
        check_status
        ;;
    "logs")
        check_supervisor
        show_logs
        ;;
    *)
        main
        ;;
esac 