#!/usr/bin/env python3
"""
国家税务总局爬虫Web管理后台
提供可视化界面管理两个爬虫任务
"""

import asyncio
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import csv
import json
import zipfile
import shutil

from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# 动态导入爬虫模块
import sys
sys.path.insert(0, str(Path(__file__).parent))

from flfg_scraper.chinatax_scraper import scrape as flfg_scrape
from comments_scraper.chinatax_comments_scraper import scrape as comments_scrape, download_contents

# 导入法律法规详情下载功能
sys.path.insert(0, str(Path(__file__).parent / "flfg_scraper"))
from chinatax_scheduler import load_all_records, filter_records_not_downloaded, update_record_status
from chinatax_document_downloader import scrape_document

# 导入数据库配置
from config.db_config import get_db_cursor, DB_TYPE

# 导入CSV管理工具
from config.csv_manager import get_csv_path, list_csv_files as list_managed_csv_files, CSV_EXPORTS_DIR

# 导入日志管理工具
from config.log_manager import create_task_logger, finish_task_log, read_task_log, get_log_file_path

app = FastAPI(title="正鹏AI数据获取平台", version="1.0.0")

# 创建templates和static目录（如果不存在）
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

templates = Jinja2Templates(directory=str(templates_dir))


# 任务管理辅助函数
def save_task_to_db(task_data: Dict[str, Any]) -> None:
    """保存任务到数据库"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO tasks (
                    task_id, task_type, task_category, status, params,
                    message, result, error, csv_path, log_file, start_time, end_time
                ) VALUES (
                    %(task_id)s, %(task_type)s, %(task_category)s, %(status)s, %(params)s,
                    %(message)s, %(result)s, %(error)s, %(csv_path)s, %(log_file)s, %(start_time)s, %(end_time)s
                )
            """, {
                'task_id': task_data['task_id'],
                'task_type': task_data['type'],
                'task_category': task_data.get('category', 'unknown'),
                'status': task_data['status'],
                'params': json.dumps(task_data.get('params'), ensure_ascii=False),
                'message': task_data.get('message'),
                'result': json.dumps(task_data.get('result'), ensure_ascii=False) if task_data.get('result') else None,
                'error': task_data.get('error'),
                'csv_path': task_data.get('csv_path'),
                'log_file': task_data.get('log_file'),
                'start_time': task_data.get('start_time'),
                'end_time': task_data.get('end_time')
            })
    except Exception as e:
        print(f"保存任务到数据库失败: {e}")


def update_task_in_db(task_id: str, updates: Dict[str, Any]) -> None:
    """更新数据库中的任务状态"""
    try:
        with get_db_cursor() as cursor:
            set_clauses = []
            params = {'task_id': task_id}

            for key, value in updates.items():
                if key in ['status', 'message', 'error', 'csv_path', 'log_file', 'end_time']:
                    set_clauses.append(f"{key} = %({key})s")
                    params[key] = value
                elif key == 'result':
                    set_clauses.append("result = %(result)s")
                    params['result'] = json.dumps(value, ensure_ascii=False) if value else None

            if set_clauses:
                sql = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE task_id = %(task_id)s"
                cursor.execute(sql, params)
    except Exception as e:
        print(f"更新任务状态失败: {e}")


def load_tasks_from_db(limit: Optional[int] = None, status: Optional[str] = None, category: Optional[str] = None) -> List[Dict]:
    """从数据库加载任务"""
    try:
        with get_db_cursor() as cursor:
            conditions = []
            params = {}

            if status:
                conditions.append("status = %(status)s")
                params['status'] = status

            if category:
                conditions.append("task_category = %(category)s")
                params['category'] = category

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            limit_clause = f"LIMIT {limit}" if limit else ""

            sql = f"""
                SELECT task_id, task_type as type, task_category as category, status,
                       params, message, result, error, csv_path, log_file,
                       start_time, end_time
                FROM tasks
                {where_clause}
                ORDER BY start_time DESC
                {limit_clause}
            """
            cursor.execute(sql, params)
            tasks = cursor.fetchall()

            # 解析JSON字段
            for task in tasks:
                if task.get('params'):
                    task['params'] = json.loads(task['params'])
                if task.get('result'):
                    task['result'] = json.loads(task['result'])
                if task.get('start_time'):
                    task['start_time'] = task['start_time'].isoformat() if hasattr(task['start_time'], 'isoformat') else str(task['start_time'])
                if task.get('end_time'):
                    task['end_time'] = task['end_time'].isoformat() if hasattr(task['end_time'], 'isoformat') else str(task['end_time'])

            return tasks
    except Exception as e:
        print(f"从数据库加载任务失败: {e}")
        return []


# 任务状态存储（简单内存存储，生产环境应使用数据库）
task_status: Dict[str, Dict[str, Any]] = {}


class FlfgScraperRequest(BaseModel):
    """法律法规爬虫请求参数"""
    start_page: int = 1
    page_count: Optional[int] = None
    headless: bool = True


class CommentsScraperRequest(BaseModel):
    """留言爬虫请求参数"""
    start_page: int = 1
    max_pages: Optional[int] = None
    headless: bool = True
    auto_download: bool = False
    overwrite_db: bool = False  # 是否覆盖数据库已存在的记录


class DownloadContentRequest(BaseModel):
    """下载留言详情请求参数"""
    max_downloads: Optional[int] = None
    headless: bool = True


class FlfgDownloadRequest(BaseModel):
    """下载法律法规详情请求参数"""
    output_dir: str = "./flfg_downloads"
    max_downloads: Optional[int] = None
    headless: bool = True
    only_not_downloaded: bool = True


class FlfgBatchDownloadRequest(BaseModel):
    """批量下载法律法规详情请求参数（基于记录ID）"""
    record_ids: List[str]
    output_dir: str = "./flfg_downloads"
    headless: bool = True


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主页"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/flfg", response_class=HTMLResponse)
async def flfg_page(request: Request):
    """法律法规页面"""
    return templates.TemplateResponse("flfg.html", {"request": request})


@app.get("/comments", response_class=HTMLResponse)
async def comments_page(request: Request):
    """留言公开页面"""
    return templates.TemplateResponse("comments.html", {"request": request})


@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request):
    """任务管理页面"""
    return templates.TemplateResponse("tasks.html", {"request": request})


@app.get("/api/tasks")
async def get_tasks(status: Optional[str] = None, category: Optional[str] = None, limit: Optional[int] = None):
    """获取所有任务状态（从数据库）"""
    db_tasks = load_tasks_from_db(limit=limit, status=status, category=category)
    return {"tasks": db_tasks}


@app.get("/api/tasks/completed")
async def get_completed_tasks(category: Optional[str] = None, limit: int = 50):
    """获取已完成的任务列表"""
    completed_tasks = load_tasks_from_db(limit=limit, status='completed', category=category)
    return {"tasks": completed_tasks}


@app.get("/api/task/{task_id}")
async def get_task(task_id: str):
    """获取特定任务状态"""
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task_status[task_id]


@app.post("/api/flfg/scrape")
async def scrape_flfg(params: FlfgScraperRequest, background_tasks: BackgroundTasks):
    """启动法律法规爬虫任务"""
    task_id = f"flfg_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    log_file_path = str(get_log_file_path(task_id))

    task_data = {
        "task_id": task_id,
        "type": "法律法规爬虫",
        "category": "法律法规",
        "status": "running",
        "params": params.dict(),
        "start_time": datetime.now().isoformat(),
        "message": "任务启动中...",
        "result": None,
        "csv_path": None,
        "log_file": log_file_path
    }

    task_status[task_id] = task_data.copy()
    save_task_to_db(task_data)

    background_tasks.add_task(run_flfg_scraper, task_id, params)

    return {"task_id": task_id, "message": "任务已启动"}


@app.post("/api/comments/scrape")
async def scrape_comments(params: CommentsScraperRequest, background_tasks: BackgroundTasks):
    """启动留言爬虫任务"""
    task_id = f"comments_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    log_file_path = str(get_log_file_path(task_id))

    task_data = {
        "task_id": task_id,
        "type": "留言爬虫",
        "category": "留言公开",
        "status": "running",
        "params": params.dict(),
        "start_time": datetime.now().isoformat(),
        "message": "任务启动中...",
        "result": None,
        "csv_path": None,
        "log_file": log_file_path
    }

    task_status[task_id] = task_data.copy()
    save_task_to_db(task_data)

    background_tasks.add_task(run_comments_scraper, task_id, params)

    return {"task_id": task_id, "message": "任务已启动"}


@app.post("/api/comments/download")
async def download_comments_content(params: DownloadContentRequest, background_tasks: BackgroundTasks):
    """下载留言详情内容"""
    task_id = f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    log_file_path = str(get_log_file_path(task_id))

    task_data = {
        "task_id": task_id,
        "type": "下载留言详情",
        "category": "留言公开",
        "status": "running",
        "params": params.dict(),
        "start_time": datetime.now().isoformat(),
        "message": "任务启动中...",
        "result": None,
        "csv_path": None,
        "log_file": log_file_path
    }

    task_status[task_id] = task_data.copy()
    save_task_to_db(task_data)

    background_tasks.add_task(run_download_content, task_id, params)

    return {"task_id": task_id, "message": "任务已启动"}


@app.post("/api/flfg/download")
async def download_flfg_documents(params: FlfgDownloadRequest, background_tasks: BackgroundTasks):
    """下载法律法规详情文档"""
    task_id = f"flfg_download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    log_file_path = str(get_log_file_path(task_id))

    task_data = {
        "task_id": task_id,
        "type": "下载法律法规详情",
        "category": "法律法规",
        "status": "running",
        "params": params.dict(),
        "start_time": datetime.now().isoformat(),
        "message": "任务启动中...",
        "result": None,
        "csv_path": None,
        "log_file": log_file_path
    }

    task_status[task_id] = task_data.copy()
    save_task_to_db(task_data)

    background_tasks.add_task(run_flfg_download, task_id, params)

    return {"task_id": task_id, "message": "任务已启动"}


@app.post("/api/flfg/download-batch")
async def download_flfg_batch(params: FlfgBatchDownloadRequest, background_tasks: BackgroundTasks):
    """批量下载指定ID的法律法规详情文档"""
    task_id = f"flfg_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    log_file_path = str(get_log_file_path(task_id))

    task_data = {
        "task_id": task_id,
        "type": "批量下载法律法规",
        "category": "法律法规",
        "status": "running",
        "params": params.dict(),
        "start_time": datetime.now().isoformat(),
        "message": "任务启动中...",
        "result": None,
        "csv_path": None,
        "log_file": log_file_path
    }

    task_status[task_id] = task_data.copy()
    save_task_to_db(task_data)

    background_tasks.add_task(run_flfg_batch_download, task_id, params)

    return {"task_id": task_id, "message": "任务已启动"}


@app.get("/api/database/stats")
async def get_database_stats():
    """获取数据库统计信息"""
    try:
        stats = {
            "database_type": DB_TYPE,
            "tables": []
        }

        with get_db_cursor() as cursor:
            # 法律法规记录统计
            cursor.execute("SELECT COUNT(*) as total FROM flfg_records")
            flfg_total = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as total FROM flfg_records WHERE downloaded = 'N'")
            flfg_not_downloaded = cursor.fetchone()['total']

            stats["tables"].append({
                "name": "flfg_records",
                "display_name": "法律法规记录",
                "total_rows": flfg_total,
                "downloaded": flfg_total - flfg_not_downloaded,
                "not_downloaded": flfg_not_downloaded
            })

            # 留言记录统计
            cursor.execute("SELECT COUNT(*) as total FROM comment_records")
            comment_total = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as total FROM comment_records WHERE downloaded = 'N'")
            comment_not_downloaded = cursor.fetchone()['total']

            stats["tables"].append({
                "name": "comment_records",
                "display_name": "留言记录",
                "total_rows": comment_total,
                "downloaded": comment_total - comment_not_downloaded,
                "not_downloaded": comment_not_downloaded
            })

        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据库统计失败: {str(e)}")


@app.get("/api/files")
async def list_csv_files():
    """列出所有CSV文件（使用csv_exports目录）"""
    csv_files = []

    # 列出csv_exports目录的文件
    for csv_file in list_managed_csv_files():
        stats = csv_file.stat()

        # 读取行数
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                row_count = sum(1 for _ in f) - 1  # 减去表头
        except Exception:
            row_count = 0

        csv_files.append({
            "name": csv_file.name,
            "path": str(csv_file),
            "size": stats.st_size,
            "size_mb": round(stats.st_size / 1024 / 1024, 2),
            "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
            "rows": row_count
        })

    return {"files": sorted(csv_files, key=lambda x: x["modified"], reverse=True)}


@app.get("/api/records/flfg/preview")
async def preview_flfg_records(
    page: int = 1,
    page_size: int = 10,
    downloaded_filter: Optional[str] = None  # 'Y', 'N', 或 None (全部)
):
    """预览法律法规记录（支持分页、筛选和排序）"""
    try:
        offset = (page - 1) * page_size

        with get_db_cursor() as cursor:
            # 构建WHERE子句
            where_clause = ""
            params = []
            if downloaded_filter in ['Y', 'N']:
                where_clause = "WHERE downloaded = %s"
                params.append(downloaded_filter)

            # 获取总记录数
            count_sql = f"SELECT COUNT(*) as total FROM flfg_records {where_clause}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total']

            # 获取分页数据，按成文日期倒序排序（新的在前）
            data_sql = f"""
                SELECT id as 序号, title as 标题, document_no as 发文字号,
                       publish_date as 成文日期, link as 链接, downloaded as 是否下载,
                       created_at as 创建时间
                FROM flfg_records
                {where_clause}
                ORDER BY publish_date DESC, created_at DESC
                LIMIT {page_size} OFFSET {offset}
            """
            cursor.execute(data_sql, params)
            records = cursor.fetchall()

        total_pages = (total + page_size - 1) // page_size  # 向上取整

        return {
            "table": "flfg_records",
            "display_name": "法律法规记录",
            "records": records,
            "count": len(records),
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "downloaded_filter": downloaded_filter
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取记录失败: {str(e)}")


@app.get("/api/records/comments/preview")
async def preview_comment_records(
    page: int = 1,
    page_size: int = 10,
    downloaded_filter: Optional[str] = None  # 'Y', 'N', 或 None (全部)
):
    """预览留言记录（支持分页、筛选和排序）"""
    try:
        offset = (page - 1) * page_size

        with get_db_cursor() as cursor:
            # 构建WHERE子句
            where_clause = ""
            params = []
            if downloaded_filter in ['Y', 'N']:
                where_clause = "WHERE downloaded = %s"
                params.append(downloaded_filter)

            # 获取总记录数
            count_sql = f"SELECT COUNT(*) as total FROM comment_records {where_clause}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total']

            # 获取分页数据，按日期倒序排序（新的在前）
            data_sql = f"""
                SELECT id, question as 留言问题, date as 日期, link as 链接地址,
                       downloaded as 是否下载, question_content as 问的内容,
                       answer_content as 答的内容, created_at as 创建时间
                FROM comment_records
                {where_clause}
                ORDER BY date DESC, created_at DESC
                LIMIT {page_size} OFFSET {offset}
            """
            cursor.execute(data_sql, params)
            records = cursor.fetchall()

        total_pages = (total + page_size - 1) // page_size  # 向上取整

        return {
            "table": "comment_records",
            "display_name": "留言记录",
            "records": records,
            "count": len(records),
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "downloaded_filter": downloaded_filter
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取记录失败: {str(e)}")


@app.get("/api/files/{filename}/preview")
async def preview_csv(filename: str, limit: int = 10):
    """预览CSV文件内容"""
    csv_path = CSV_EXPORTS_DIR / filename

    if not csv_path.exists() or csv_path.suffix != '.csv':
        raise HTTPException(status_code=404, detail="文件不存在")

    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            headers = next(reader, [])
            rows = [row for _, row in zip(range(limit), reader)]

        return {
            "filename": filename,
            "headers": headers,
            "rows": rows,
            "preview_count": len(rows)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")


@app.get("/api/files/{filename}/download")
async def download_csv(filename: str):
    """下载CSV文件"""
    csv_path = CSV_EXPORTS_DIR / filename

    if not csv_path.exists() or csv_path.suffix != '.csv':
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=csv_path,
        filename=filename,
        media_type="text/csv"
    )


@app.get("/api/tasks/{task_id}/preview")
async def preview_task_records(task_id: str, limit: int = 10):
    """预览任务抓取的记录"""
    try:
        # 从数据库获取任务信息
        tasks = load_tasks_from_db()
        task = next((t for t in tasks if t['task_id'] == task_id), None)

        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 获取任务结果中保存的record_ids
        result = task.get('result', {})
        record_ids = result.get('record_ids', [])

        if not record_ids:
            return {
                "task_id": task_id,
                "display_name": task.get('type', '未知任务'),
                "records": [],
                "count": 0,
                "message": "该任务没有抓取记录"
            }

        # 限制预览数量
        preview_ids = record_ids[:limit]

        # 根据任务类型查询数据
        category = task.get('category', '')

        with get_db_cursor() as cursor:
            if category == "留言公开":
                # 构建IN查询
                placeholders = ','.join(['%s'] * len(preview_ids))
                cursor.execute(f"""
                    SELECT id, question as 留言问题, date as 日期, link as 链接地址,
                           downloaded as 是否下载, question_content as 问的内容,
                           answer_content as 答的内容
                    FROM comment_records
                    WHERE id IN ({placeholders})
                    ORDER BY created_at DESC
                """, preview_ids)
                records = cursor.fetchall()
            elif category == "法律法规":
                placeholders = ','.join(['%s'] * len(preview_ids))
                cursor.execute(f"""
                    SELECT id as 序号, title as 标题, document_no as 发文字号,
                           publish_date as 成文日期, link as 链接, downloaded as 是否下载
                    FROM flfg_records
                    WHERE id IN ({placeholders})
                    ORDER BY created_at DESC
                """, preview_ids)
                records = cursor.fetchall()
            else:
                raise HTTPException(status_code=400, detail="不支持的任务类型")

        return {
            "task_id": task_id,
            "display_name": task.get('type', '未知任务'),
            "total_records": len(record_ids),
            "records": records,
            "count": len(records)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览记录失败: {str(e)}")


@app.get("/api/tasks/{task_id}/export")
async def export_task_csv(task_id: str):
    """导出特定任务抓取的数据为CSV"""
    try:
        # 从数据库获取任务信息
        tasks = load_tasks_from_db()
        task = next((t for t in tasks if t['task_id'] == task_id), None)

        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 检查任务是否已有CSV文件
        if task.get('csv_path'):
            csv_path = Path(task['csv_path'])
            if csv_path.exists():
                return FileResponse(
                    path=csv_path,
                    filename=csv_path.name,
                    media_type="text/csv"
                )

        # 如果没有CSV文件，从数据库导出
        result = task.get('result', {})
        record_ids = result.get('record_ids', [])

        if not record_ids:
            raise HTTPException(status_code=404, detail="该任务没有抓取记录")

        category = task.get('category', '')

        # 使用新的CSV路径管理，生成唯一文件名
        csv_path = get_csv_path(f"export_{task_id}")

        with get_db_cursor() as cursor:
            if category == "法律法规":
                placeholders = ','.join(['%s'] * len(record_ids))
                cursor.execute(f"""
                    SELECT id as 序号, title as 标题, document_no as 发文字号,
                           publish_date as 成文日期, link as 链接, downloaded as 是否下载
                    FROM flfg_records
                    WHERE id IN ({placeholders})
                    ORDER BY created_at DESC
                """, record_ids)
            elif category == "留言公开":
                placeholders = ','.join(['%s'] * len(record_ids))
                cursor.execute(f"""
                    SELECT id, question as 留言问题, date as 日期,
                           link as 链接地址, downloaded as 是否下载,
                           question_content as 问的内容, answer_content as 答的内容
                    FROM comment_records
                    WHERE id IN ({placeholders})
                    ORDER BY created_at DESC
                """, record_ids)
            else:
                raise HTTPException(status_code=400, detail="不支持的任务类型")

            records = cursor.fetchall()

        # 写入CSV
        if records:
            with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=records[0].keys())
                writer.writeheader()
                writer.writerows(records)

        if not csv_path.exists():
            raise HTTPException(status_code=404, detail="导出失败")

        return FileResponse(
            path=csv_path,
            filename=csv_path.name,
            media_type="text/csv"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@app.get("/api/tasks/{task_id}/log")
async def get_task_log(task_id: str):
    """获取任务执行日志"""
    try:
        log_content = read_task_log(task_id)
        return {
            "task_id": task_id,
            "log_content": log_content,
            "log_file": str(get_log_file_path(task_id))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取日志失败: {str(e)}")


@app.get("/api/tasks/{task_id}/export-md")
async def export_task_markdown(task_id: str):
    """导出留言公开任务的问答内容为Markdown格式"""
    try:
        # 从数据库获取任务信息
        tasks = load_tasks_from_db()
        task = next((t for t in tasks if t['task_id'] == task_id), None)

        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 只支持留言公开类型
        category = task.get('category', '')
        if category != "留言公开":
            raise HTTPException(status_code=400, detail="此功能仅支持留言公开任务")

        # 获取记录ID
        result = task.get('result', {})
        record_ids = result.get('record_ids', [])

        if not record_ids:
            raise HTTPException(status_code=404, detail="该任务没有抓取记录")

        # 从数据库查询问答内容
        with get_db_cursor() as cursor:
            placeholders = ','.join(['%s'] * len(record_ids))
            cursor.execute(f"""
                SELECT question, question_content, answer_content, date
                FROM comment_records
                WHERE id IN ({placeholders})
                ORDER BY created_at DESC
            """, record_ids)
            records = cursor.fetchall()

        if not records:
            raise HTTPException(status_code=404, detail="未找到记录")

        # 生成Markdown内容
        md_content = f"# 留言公开问答资料\n\n"
        md_content += f"**导出时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n\n"
        md_content += f"**问答数量**: {len(records)}条\n\n"
        md_content += "---\n\n"

        for idx, record in enumerate(records, 1):
            question_title = record.get('question', '无标题')
            question_content = record.get('question_content', '无内容')
            answer_content = record.get('answer_content', '无答复')
            date = record.get('date', '')

            # 一问一答格式
            md_content += f"## 问题 {idx}\n\n"
            if date:
                md_content += f"**日期**: {date}\n\n"
            md_content += f"**标题**: {question_title}\n\n"
            md_content += f"**问**:\n\n{question_content}\n\n"
            md_content += f"**答**:\n\n{answer_content}\n\n"
            md_content += "---\n\n"  # 分隔符

        # 生成唯一的MD文件路径
        md_path = get_csv_path(f"qa_export_{task_id}").with_suffix('.md')

        # 写入文件
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        if not md_path.exists():
            raise HTTPException(status_code=500, detail="生成Markdown文件失败")

        return FileResponse(
            path=md_path,
            filename=md_path.name,
            media_type="text/markdown"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


class ExportRequest(BaseModel):
    """导出请求模型"""
    record_ids: List[str]


@app.post("/api/comments/export-selected-md")
async def export_selected_comments_markdown(request: ExportRequest):
    """导出选中的留言记录为Markdown格式"""
    try:
        if not request.record_ids:
            raise HTTPException(status_code=400, detail="未选择任何记录")

        # 从数据库查询问答内容
        with get_db_cursor() as cursor:
            placeholders = ','.join(['%s'] * len(request.record_ids))
            cursor.execute(f"""
                SELECT question, question_content, answer_content, date
                FROM comment_records
                WHERE id IN ({placeholders})
                ORDER BY created_at DESC
            """, request.record_ids)
            records = cursor.fetchall()

        if not records:
            raise HTTPException(status_code=404, detail="未找到记录")

        # 生成Markdown内容
        md_content = _generate_markdown_content(records, "选中记录")

        # 生成唯一的MD文件路径
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        md_path = get_csv_path(f"selected_qa_{timestamp}").with_suffix('.md')

        # 写入文件
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        return FileResponse(
            path=md_path,
            filename=md_path.name,
            media_type="text/markdown"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@app.get("/api/comments/export-all-md")
async def export_all_comments_markdown():
    """导出所有留言记录为Markdown格式"""
    try:
        # 从数据库查询所有问答内容
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT question, question_content, answer_content, date
                FROM comment_records
                ORDER BY created_at DESC
            """)
            records = cursor.fetchall()

        if not records:
            raise HTTPException(status_code=404, detail="数据库中没有记录")

        # 生成Markdown内容
        md_content = _generate_markdown_content(records, "全部记录")

        # 生成唯一的MD文件路径
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        md_path = get_csv_path(f"all_qa_{timestamp}").with_suffix('.md')

        # 写入文件
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        return FileResponse(
            path=md_path,
            filename=md_path.name,
            media_type="text/markdown"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@app.get("/api/comments/export-single-md/{record_id}")
async def export_single_comment_markdown(record_id: str):
    """导出单条留言记录为Markdown格式"""
    try:
        # 从数据库查询问答内容
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT question, question_content, answer_content, date
                FROM comment_records
                WHERE id = %s
            """, (record_id,))
            record = cursor.fetchone()

        if not record:
            raise HTTPException(status_code=404, detail="记录不存在")

        # 生成Markdown内容
        md_content = _generate_markdown_content([record], "单条记录")

        # 生成唯一的MD文件路径
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        md_path = get_csv_path(f"single_qa_{timestamp}").with_suffix('.md')

        # 写入文件
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        return FileResponse(
            path=md_path,
            filename=md_path.name,
            media_type="text/markdown"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


def _generate_markdown_content(records: List[Dict], export_type: str = "记录") -> str:
    """生成Markdown格式内容的辅助函数"""
    md_content = f"# 留言公开问答资料\n\n"
    md_content += f"**导出类型**: {export_type}\n\n"
    md_content += f"**导出时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n\n"
    md_content += f"**问答数量**: {len(records)}条\n\n"
    md_content += "---\n\n"

    for idx, record in enumerate(records, 1):
        question_title = record.get('question', '无标题')
        question_content = record.get('question_content', '无内容')
        answer_content = record.get('answer_content', '无答复')
        date = record.get('date', '')

        # 一问一答格式
        md_content += f"## 问题 {idx}\n\n"
        if date:
            md_content += f"**日期**: {date}\n\n"
        md_content += f"**标题**: {question_title}\n\n"
        md_content += f"**问**:\n\n{question_content}\n\n"
        md_content += f"**答**:\n\n{answer_content}\n\n"
        md_content += "---\n\n"  # 分隔符

    return md_content


async def run_flfg_scraper(task_id: str, params: FlfgScraperRequest):
    """后台运行法律法规爬虫"""
    # 创建任务日志记录器
    logger = create_task_logger(task_id, "法律法规爬虫")

    try:
        logger.info(f"任务参数: start_page={params.start_page}, page_count={params.page_count}, headless={params.headless}")

        task_status[task_id]["message"] = "正在爬取法律法规数据..."
        update_task_in_db(task_id, {"message": "正在爬取法律法规数据..."})
        logger.info("开始爬取法律法规数据...")

        result = await flfg_scrape(
            headless=params.headless,
            start_page=params.start_page,
            page_count=params.page_count
        )

        logger.info(f"爬取完成！新增 {result} 条记录")

        task_status[task_id].update({
            "status": "completed",
            "message": f"任务完成！新增 {result} 条记录",
            "result": {"new_records": result},
            "end_time": datetime.now().isoformat()
        })
        update_task_in_db(task_id, {
            "status": "completed",
            "message": f"任务完成！新增 {result} 条记录",
            "result": {"new_records": result},
            "end_time": datetime.now().isoformat()
        })

        finish_task_log(logger, task_id, "completed")

    except Exception as e:
        logger.error(f"任务执行失败: {str(e)}")
        logger.exception(e)

        task_status[task_id].update({
            "status": "failed",
            "message": f"任务失败: {str(e)}",
            "error": str(e),
            "end_time": datetime.now().isoformat()
        })
        update_task_in_db(task_id, {
            "status": "failed",
            "message": f"任务失败: {str(e)}",
            "error": str(e),
            "end_time": datetime.now().isoformat()
        })

        finish_task_log(logger, task_id, "failed")


async def run_comments_scraper(task_id: str, params: CommentsScraperRequest):
    """后台运行留言爬虫"""
    # 创建任务日志记录器
    logger = create_task_logger(task_id, "留言爬虫")

    try:
        logger.info(f"任务参数: start_page={params.start_page}, max_pages={params.max_pages}, headless={params.headless}, auto_download={params.auto_download}, overwrite_db={params.overwrite_db}")

        task_status[task_id]["message"] = "正在爬取留言数据..."
        update_task_in_db(task_id, {"message": "正在爬取留言数据..."})
        logger.info("开始爬取留言数据...")

        # 生成CSV文件路径（使用csv_manager）
        csv_path = get_csv_path(f"comments_{task_id}")

        new_count, actual_csv_path, all_records = await comments_scrape(
            headless=params.headless,
            start_page=params.start_page,
            max_pages=params.max_pages,
            auto_download=params.auto_download,
            csv_path=str(csv_path),
            overwrite_db=params.overwrite_db
        )

        logger.info(f"爬取完成！新增 {new_count} 条记录，本次共抓取 {len(all_records)} 条记录")
        if actual_csv_path:
            logger.info(f"CSV文件已保存: {actual_csv_path}")

        # 保存本次抓取的记录ID列表
        record_ids = [r.id for r in all_records]

        # 生成更清晰的任务完成消息
        skipped_count = len(all_records) - new_count
        if new_count == 0 and len(all_records) > 0:
            message = f"任务完成！本次抓取 {len(all_records)} 条记录，全部为重复记录（数据库中已存在）"
        elif skipped_count > 0:
            message = f"任务完成！本次抓取 {len(all_records)} 条记录：新增 {new_count} 条，跳过 {skipped_count} 条重复记录"
        else:
            message = f"任务完成！新增 {new_count} 条记录"

        task_status[task_id].update({
            "status": "completed",
            "message": message,
            "result": {
                "new_records": new_count,
                "total_scraped": len(all_records),
                "skipped_records": skipped_count,
                "record_ids": record_ids  # 保存本次抓取的记录ID列表
            },
            "csv_path": actual_csv_path,
            "end_time": datetime.now().isoformat()
        })
        update_task_in_db(task_id, {
            "status": "completed",
            "message": message,
            "result": {
                "new_records": new_count,
                "total_scraped": len(all_records),
                "skipped_records": skipped_count,
                "record_ids": record_ids
            },
            "csv_path": actual_csv_path,
            "end_time": datetime.now().isoformat()
        })

        finish_task_log(logger, task_id, "completed")

    except Exception as e:
        logger.error(f"任务执行失败: {str(e)}")
        logger.exception(e)

        task_status[task_id].update({
            "status": "failed",
            "message": f"任务失败: {str(e)}",
            "error": str(e),
            "end_time": datetime.now().isoformat()
        })
        update_task_in_db(task_id, {
            "status": "failed",
            "message": f"任务失败: {str(e)}",
            "error": str(e),
            "end_time": datetime.now().isoformat()
        })

        finish_task_log(logger, task_id, "failed")


async def run_download_content(task_id: str, params: DownloadContentRequest):
    """后台运行下载留言详情"""
    # 创建任务日志记录器
    logger = create_task_logger(task_id, "下载留言详情")

    try:
        logger.info(f"任务参数: max_downloads={params.max_downloads}, headless={params.headless}")

        task_status[task_id]["message"] = "正在下载留言详情..."
        update_task_in_db(task_id, {"message": "正在下载留言详情..."})
        logger.info("开始下载留言详情...")

        result = await download_contents(
            headless=params.headless,
            max_downloads=params.max_downloads
        )

        logger.info(f"下载完成！成功下载 {result} 条记录")

        task_status[task_id].update({
            "status": "completed",
            "message": f"任务完成！成功下载 {result} 条记录",
            "result": {"downloaded_count": result},
            "end_time": datetime.now().isoformat()
        })
        update_task_in_db(task_id, {
            "status": "completed",
            "message": f"任务完成！成功下载 {result} 条记录",
            "result": {"downloaded_count": result},
            "end_time": datetime.now().isoformat()
        })

        finish_task_log(logger, task_id, "completed")

    except Exception as e:
        logger.error(f"任务执行失败: {str(e)}")
        logger.exception(e)

        task_status[task_id].update({
            "status": "failed",
            "message": f"任务失败: {str(e)}",
            "error": str(e),
            "end_time": datetime.now().isoformat()
        })
        update_task_in_db(task_id, {
            "status": "failed",
            "message": f"任务失败: {str(e)}",
            "error": str(e),
            "end_time": datetime.now().isoformat()
        })

        finish_task_log(logger, task_id, "failed")


async def run_flfg_download(task_id: str, params: FlfgDownloadRequest):
    """后台运行法律法规详情下载"""
    # 创建任务日志记录器
    logger = create_task_logger(task_id, "下载法律法规详情")

    try:
        logger.info(f"任务参数: output_dir={params.output_dir}, max_downloads={params.max_downloads}, headless={params.headless}, only_not_downloaded={params.only_not_downloaded}")

        task_status[task_id]["message"] = "正在读取数据库记录..."
        update_task_in_db(task_id, {"message": "正在读取数据库记录..."})
        logger.info("正在读取数据库记录...")

        # 从数据库读取记录
        records = load_all_records()

        # 根据参数过滤记录
        if params.only_not_downloaded:
            records = filter_records_not_downloaded(records)
            logger.info(f"找到 {len(records)} 条未下载的记录")
            task_status[task_id]["message"] = f"找到 {len(records)} 条未下载的记录..."
            update_task_in_db(task_id, {"message": f"找到 {len(records)} 条未下载的记录..."})

        if not records:
            logger.info("没有需要下载的记录")
            task_status[task_id].update({
                "status": "completed",
                "message": "没有需要下载的记录",
                "result": {"downloaded_count": 0, "failed_count": 0},
                "end_time": datetime.now().isoformat()
            })
            update_task_in_db(task_id, {
                "status": "completed",
                "message": "没有需要下载的记录",
                "result": {"downloaded_count": 0, "failed_count": 0},
                "end_time": datetime.now().isoformat()
            })
            finish_task_log(logger, task_id, "completed")
            return

        # 限制下载数量
        if params.max_downloads:
            records = records[:params.max_downloads]
            logger.info(f"限制下载数量为 {params.max_downloads} 条")

        # 创建输出目录
        output_dir = Path(params.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 逐条下载
        success_count = 0
        fail_count = 0

        for i, record in enumerate(records, 1):
            url = record.get("链接", "")
            if not url:
                fail_count += 1
                continue

            task_status[task_id]["message"] = f"正在下载 {i}/{len(records)}: {record['标题']}"
            update_task_in_db(task_id, {"message": f"正在下载 {i}/{len(records)}: {record['标题']}"})
            logger.info(f"[{i}/{len(records)}] 下载: {record['标题']}")

            try:
                await scrape_document(
                    url=url,
                    base_output_dir=output_dir,
                    headless=params.headless
                )
                success_count += 1
                logger.info(f"  ✓ 下载成功")

                # 更新数据库状态
                update_record_status(record["序号"], "Y")

            except Exception as e:
                logger.error(f"  ✗ 下载失败: {str(e)}")
                fail_count += 1

        logger.info(f"下载完成！成功 {success_count} 条，失败 {fail_count} 条")

        task_status[task_id].update({
            "status": "completed",
            "message": f"任务完成！成功 {success_count} 条，失败 {fail_count} 条",
            "result": {"downloaded_count": success_count, "failed_count": fail_count},
            "end_time": datetime.now().isoformat()
        })
        update_task_in_db(task_id, {
            "status": "completed",
            "message": f"任务完成！成功 {success_count} 条，失败 {fail_count} 条",
            "result": {"downloaded_count": success_count, "failed_count": fail_count},
            "end_time": datetime.now().isoformat()
        })

        finish_task_log(logger, task_id, "completed")

    except Exception as e:
        logger.error(f"任务执行失败: {str(e)}")
        logger.exception(e)

        task_status[task_id].update({
            "status": "failed",
            "message": f"任务失败: {str(e)}",
            "error": str(e),
            "end_time": datetime.now().isoformat()
        })
        update_task_in_db(task_id, {
            "status": "failed",
            "message": f"任务失败: {str(e)}",
            "error": str(e),
            "end_time": datetime.now().isoformat()
        })

        finish_task_log(logger, task_id, "failed")


async def run_flfg_batch_download(task_id: str, params: FlfgBatchDownloadRequest):
    """后台运行批量下载指定ID的法律法规详情"""
    # 创建任务日志记录器
    logger = create_task_logger(task_id, "批量下载法律法规")

    try:
        logger.info(f"任务参数: record_ids={len(params.record_ids)}条, output_dir={params.output_dir}, headless={params.headless}")

        task_status[task_id]["message"] = f"正在读取 {len(params.record_ids)} 条记录..."
        update_task_in_db(task_id, {"message": f"正在读取 {len(params.record_ids)} 条记录..."})
        logger.info(f"正在读取 {len(params.record_ids)} 条记录...")

        # 从数据库读取指定ID的记录
        records = []
        with get_db_cursor() as cursor:
            placeholders = ','.join(['%s'] * len(params.record_ids))
            cursor.execute(f"""
                SELECT id as 序号, title as 标题, document_no as 发文字号,
                       publish_date as 成文日期, link as 链接, downloaded as 是否下载
                FROM flfg_records
                WHERE id IN ({placeholders})
            """, params.record_ids)
            records = cursor.fetchall()

        logger.info(f"找到 {len(records)} 条记录")

        if not records:
            logger.info("没有找到匹配的记录")
            task_status[task_id].update({
                "status": "completed",
                "message": "没有找到匹配的记录",
                "result": {"downloaded_count": 0, "failed_count": 0},
                "end_time": datetime.now().isoformat()
            })
            update_task_in_db(task_id, {
                "status": "completed",
                "message": "没有找到匹配的记录",
                "result": {"downloaded_count": 0, "failed_count": 0},
                "end_time": datetime.now().isoformat()
            })
            finish_task_log(logger, task_id, "completed")
            return

        # 创建输出目录
        output_dir = Path(params.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"输出目录: {output_dir}")

        # 逐条下载
        success_count = 0
        fail_count = 0

        for i, record in enumerate(records, 1):
            url = record.get("链接", "")
            if not url:
                logger.warning(f"[{i}/{len(records)}] 记录 {record['序号']} 没有链接，跳过")
                fail_count += 1
                continue

            task_status[task_id]["message"] = f"正在下载 {i}/{len(records)}: {record['标题']}"
            update_task_in_db(task_id, {"message": f"正在下载 {i}/{len(records)}: {record['标题']}"})
            logger.info(f"[{i}/{len(records)}] 下载: {record['标题']}")

            try:
                await scrape_document(
                    url=url,
                    base_output_dir=output_dir,
                    headless=params.headless
                )
                success_count += 1
                logger.info(f"  ✓ 下载成功")

                # 更新数据库状态
                update_record_status(record["序号"], "Y")

            except Exception as e:
                logger.error(f"  ✗ 下载失败: {str(e)}")
                fail_count += 1

        logger.info(f"批量下载完成！成功 {success_count} 条，失败 {fail_count} 条")

        task_status[task_id].update({
            "status": "completed",
            "message": f"任务完成！成功 {success_count} 条，失败 {fail_count} 条",
            "result": {"downloaded_count": success_count, "failed_count": fail_count},
            "end_time": datetime.now().isoformat()
        })
        update_task_in_db(task_id, {
            "status": "completed",
            "message": f"任务完成！成功 {success_count} 条，失败 {fail_count} 条",
            "result": {"downloaded_count": success_count, "failed_count": fail_count},
            "end_time": datetime.now().isoformat()
        })

        finish_task_log(logger, task_id, "completed")

    except Exception as e:
        logger.error(f"任务执行失败: {str(e)}")
        logger.exception(e)

        task_status[task_id].update({
            "status": "failed",
            "message": f"任务失败: {str(e)}",
            "error": str(e),
            "end_time": datetime.now().isoformat()
        })
        update_task_in_db(task_id, {
            "status": "failed",
            "message": f"任务失败: {str(e)}",
            "error": str(e),
            "end_time": datetime.now().isoformat()
        })

        finish_task_log(logger, task_id, "failed")


def _get_flfg_folder_path(record_id: str, title: str, link: str = "") -> Optional[Path]:
    """
    根据记录ID、标题和链接获取法律法规下载文件夹路径
    文件夹命名格式: {标题}_{URL中的数字ID}
    """
    downloads_dir = Path("./flfg_downloads")
    if not downloads_dir.exists():
        return None

    # 从link中提取数字ID（例如：c5243496 -> 5243496，取最后一个）
    folder_id = None
    if link:
        import re
        matches = re.findall(r'c(\d+)', link)
        if matches:
            folder_id = matches[-1]  # 取最后一个匹配

    # 尝试使用从URL提取的ID匹配文件夹
    if folder_id:
        folder_name = f"{title}_{folder_id}"
        folder_path = downloads_dir / folder_name
        if folder_path.exists() and folder_path.is_dir():
            return folder_path

    # 如果精确匹配失败，尝试模糊匹配（文件名可能被截断或有特殊字符处理）
    if folder_id:
        for item in downloads_dir.iterdir():
            if item.is_dir() and item.name.endswith(f"_{folder_id}"):
                return item

    # 最后尝试使用MD5 ID匹配（如果有的话）
    for item in downloads_dir.iterdir():
        if item.is_dir() and item.name.endswith(f"_{record_id}"):
            return item

    return None


def _create_zip_from_folders(folder_paths: List[Path], zip_path: Path) -> int:
    """
    将多个文件夹打包成一个ZIP文件
    返回打包的文件夹数量
    """
    packed_count = 0

    # 使用 UTF-8 编码支持中文文件名
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zipf:
        for folder_path in folder_paths:
            if not folder_path.exists():
                continue

            # 将文件夹及其内容添加到ZIP
            for file_path in folder_path.rglob('*'):
                if file_path.is_file():
                    # 保持文件夹结构
                    arcname = str(file_path.relative_to(folder_path.parent))
                    # 使用UTF-8模式写入，确保中文文件名正确处理
                    zipf.write(file_path, arcname)

            packed_count += 1

    return packed_count


@app.get("/api/flfg/export-single-zip/{record_id}")
async def export_single_flfg_zip(record_id: str):
    """导出单条法律法规记录的资料为ZIP"""
    try:
        # 从数据库获取记录信息
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT id as 序号, title as 标题, document_no as 发文字号,
                       publish_date as 成文日期, link as 链接, downloaded as 是否下载
                FROM flfg_records
                WHERE id = %s
            """, (record_id,))
            record = cursor.fetchone()

        if not record:
            raise HTTPException(status_code=404, detail="记录不存在")

        if record.get('是否下载') != 'Y':
            raise HTTPException(status_code=400, detail="该记录尚未下载，无法导出资料")

        # 获取文件夹路径
        folder_path = _get_flfg_folder_path(record_id, record['标题'], record.get('链接', ''))

        if not folder_path:
            raise HTTPException(status_code=404, detail="未找到下载的资料文件夹")

        # 生成ZIP文件路径
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"flfg_single_{timestamp}.zip"  # 使用英文文件名
        zip_path = CSV_EXPORTS_DIR / zip_filename

        # 创建ZIP文件
        packed = _create_zip_from_folders([folder_path], zip_path)

        if packed == 0:
            raise HTTPException(status_code=404, detail="无可导出的资料")

        return FileResponse(
            path=zip_path,
            filename=zip_filename,
            media_type="application/zip"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


class FlfgExportRequest(BaseModel):
    """法律法规资料导出请求模型"""
    record_ids: List[str]


@app.post("/api/flfg/export-selected-zip")
async def export_selected_flfg_zip(request: FlfgExportRequest):
    """导出选中的法律法规记录资料为ZIP"""
    try:
        if not request.record_ids:
            raise HTTPException(status_code=400, detail="未选择任何记录")

        # 从数据库获取记录信息
        folder_paths = []
        not_downloaded = []

        with get_db_cursor() as cursor:
            placeholders = ','.join(['%s'] * len(request.record_ids))
            cursor.execute(f"""
                SELECT id as 序号, title as 标题, link as 链接, downloaded as 是否下载
                FROM flfg_records
                WHERE id IN ({placeholders})
            """, request.record_ids)
            records = cursor.fetchall()

        for record in records:
            record_id = record['序号']
            title = record['标题']
            link = record.get('链接', '')

            if record.get('是否下载') != 'Y':
                not_downloaded.append(title)
                continue

            folder_path = _get_flfg_folder_path(record_id, title, link)
            if folder_path:
                folder_paths.append(folder_path)

        if not folder_paths:
            if not_downloaded:
                raise HTTPException(
                    status_code=400,
                    detail=f"选中的记录中有 {len(not_downloaded)} 条尚未下载，无法导出"
                )
            else:
                raise HTTPException(status_code=404, detail="未找到可导出的资料")

        # 生成ZIP文件路径
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"flfg_selected_{len(folder_paths)}_records_{timestamp}.zip"  # 使用英文文件名
        zip_path = CSV_EXPORTS_DIR / zip_filename

        # 创建ZIP文件
        packed = _create_zip_from_folders(folder_paths, zip_path)

        # 使用英文文件名返回，避免编码问题
        return FileResponse(
            path=str(zip_path),  # 转为字符串
            filename=zip_filename,
            media_type="application/zip",
            headers={
                "X-Export-Summary": f"Successfully exported {packed} records, skipped {len(not_downloaded)} undownloaded records"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@app.get("/api/flfg/export-all-zip")
async def export_all_flfg_zip():
    """导出所有已下载的法律法规记录资料为ZIP"""
    try:
        # 从数据库获取所有已下载的记录
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT id as 序号, title as 标题, link as 链接
                FROM flfg_records
                WHERE downloaded = 'Y'
                ORDER BY created_at DESC
            """)
            records = cursor.fetchall()

        if not records:
            raise HTTPException(status_code=404, detail="没有已下载的记录")

        # 收集文件夹路径
        folder_paths = []
        for record in records:
            folder_path = _get_flfg_folder_path(record['序号'], record['标题'], record.get('链接', ''))
            if folder_path:
                folder_paths.append(folder_path)

        if not folder_paths:
            raise HTTPException(status_code=404, detail="未找到可导出的资料文件夹")

        # 生成ZIP文件路径
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"flfg_all_{len(folder_paths)}_records_{timestamp}.zip"  # 使用英文文件名
        zip_path = CSV_EXPORTS_DIR / zip_filename

        # 创建ZIP文件
        packed = _create_zip_from_folders(folder_paths, zip_path)

        return FileResponse(
            path=str(zip_path),  # 转为字符串
            filename=zip_filename,
            media_type="application/zip",
            headers={
                "X-Export-Summary": f"Successfully exported {packed} records"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("正鹏AI数据获取平台")
    print("=" * 60)
    print("\n访问地址: http://localhost:8000")
    print("API文档: http://localhost:8000/docs\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
