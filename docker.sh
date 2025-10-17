#!/bin/bash

# 正鹏AI数据获取平台 Docker 管理脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
正鹏AI数据获取平台 Docker 管理脚本

用法: $0 [命令] [选项]

命令:
  start [db]        启动服务
                    db 可选: sqlite (默认), postgres, mysql

  stop              停止所有服务

  restart [db]      重启服务

  logs [service]    查看日志
                    service: 服务名称（可选）

  build             重新构建镜像

  ps                查看服务状态

  exec [service]    进入容器 Shell
                    service: 服务名称（默认: chinatax-scraper）

  backup            备份数据

  clean             清理未使用的容器和镜像

  destroy           停止并删除所有容器、网络和数据卷（谨慎使用！）

  help              显示此帮助信息

示例:
  $0 start                # 使用 SQLite 启动
  $0 start postgres       # 使用 PostgreSQL 启动
  $0 logs                 # 查看所有服务日志
  $0 logs chinatax-scraper  # 查看特定服务日志
  $0 exec                 # 进入默认容器
  $0 backup               # 备份数据

EOF
}

# 启动服务
start_service() {
    local db_type=${1:-sqlite}

    print_info "启动服务 (数据库: $db_type)..."

    case $db_type in
        sqlite)
            # 创建必要的目录
            mkdir -p data csv_exports flfg_downloads logs
            docker-compose up -d chinatax-scraper
            print_success "服务已启动"
            print_info "访问地址: http://localhost:8000"
            ;;
        postgres|postgresql)
            mkdir -p csv_exports flfg_downloads logs
            docker-compose --profile postgres up -d
            print_success "服务已启动"
            print_info "访问地址: http://localhost:8001"
            ;;
        mysql)
            mkdir -p csv_exports flfg_downloads logs
            docker-compose --profile mysql up -d
            print_success "服务已启动"
            print_info "访问地址: http://localhost:8002"
            ;;
        *)
            print_error "不支持的数据库类型: $db_type"
            print_info "支持的类型: sqlite, postgres, mysql"
            exit 1
            ;;
    esac
}

# 停止服务
stop_service() {
    print_info "停止服务..."
    docker-compose down
    print_success "服务已停止"
}

# 重启服务
restart_service() {
    local db_type=${1:-sqlite}
    print_info "重启服务..."
    stop_service
    sleep 2
    start_service "$db_type"
}

# 查看日志
view_logs() {
    local service=$1

    if [ -z "$service" ]; then
        print_info "查看所有服务日志 (Ctrl+C 退出)..."
        docker-compose logs -f
    else
        print_info "查看服务日志: $service (Ctrl+C 退出)..."
        docker-compose logs -f "$service"
    fi
}

# 重新构建镜像
rebuild_image() {
    print_info "重新构建镜像..."
    docker-compose build --no-cache
    print_success "镜像构建完成"
}

# 查看服务状态
show_status() {
    print_info "服务状态:"
    docker-compose ps
    echo ""
    print_info "容器资源使用:"
    docker stats --no-stream $(docker-compose ps -q 2>/dev/null) 2>/dev/null || echo "没有运行中的容器"
}

# 进入容器
exec_shell() {
    local service=${1:-chinatax-scraper}

    print_info "进入容器: $service"
    docker-compose exec "$service" /bin/bash || docker-compose exec "$service" /bin/sh
}

# 备份数据
backup_data() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="backups/${timestamp}"

    print_info "开始备份数据..."
    mkdir -p "$backup_dir"

    # 备份 SQLite 数据库
    if [ -f "data/chinatax.db" ]; then
        cp data/chinatax.db "$backup_dir/chinatax.db"
        print_success "SQLite 数据库已备份"
    fi

    # 备份 CSV 导出文件
    if [ -d "csv_exports" ] && [ "$(ls -A csv_exports)" ]; then
        cp -r csv_exports "$backup_dir/"
        print_success "CSV 文件已备份"
    fi

    # 备份下载的文档
    if [ -d "flfg_downloads" ] && [ "$(ls -A flfg_downloads)" ]; then
        cp -r flfg_downloads "$backup_dir/"
        print_success "下载文档已备份"
    fi

    # 备份日志
    if [ -d "logs" ] && [ "$(ls -A logs)" ]; then
        cp -r logs "$backup_dir/"
        print_success "日志文件已备份"
    fi

    print_success "备份完成: $backup_dir"
}

# 清理未使用的资源
clean_resources() {
    print_warning "清理未使用的 Docker 资源..."
    docker system prune -f
    print_success "清理完成"
}

# 销毁所有资源（危险操作）
destroy_all() {
    print_warning "警告: 此操作将删除所有容器、网络和数据卷！"
    read -p "确定要继续吗? (yes/no): " confirm

    if [ "$confirm" = "yes" ]; then
        print_info "销毁所有资源..."
        docker-compose down -v
        print_success "所有资源已删除"
    else
        print_info "操作已取消"
    fi
}

# 主函数
main() {
    local command=${1:-help}
    shift || true

    case $command in
        start)
            start_service "$@"
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service "$@"
            ;;
        logs)
            view_logs "$@"
            ;;
        build)
            rebuild_image
            ;;
        ps|status)
            show_status
            ;;
        exec|shell)
            exec_shell "$@"
            ;;
        backup)
            backup_data
            ;;
        clean)
            clean_resources
            ;;
        destroy)
            destroy_all
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
