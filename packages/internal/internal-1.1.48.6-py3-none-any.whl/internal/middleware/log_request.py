import json
import logging
import time

from collections import defaultdict
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from ..const import CORRELATION_ID_HEADER_KEY_NAME


class LogRequestMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, logger: logging.Logger):
        super().__init__(app)
        self.app = app
        self.logger = logger

    async def dispatch(self, request: Request, call_next):
        # 记录请求的URL和参数
        url = request.url.path
        method = request.method
        headers = request.headers
        request_id = headers.get(CORRELATION_ID_HEADER_KEY_NAME, "")
        content_type = headers.get('content-type', '') or headers.get('Content-Type', '')
        is_multipart = 'multipart' in content_type.lower()

        query_params = request.query_params
        temp = defaultdict(list)
        for key, value in query_params.multi_items():
            temp[key].append(value)
        # 如果只有一個值就轉成單一值
        params = {k: v[0] if len(v) == 1 else v for k, v in temp.items()}

        body = await request.body()

        # 解碼 body 為字符串（如果不是 multipart）
        if is_multipart:
            body_str = "因上傳檔案不顯示body"
        else:
            try:
                # 嘗試使用 UTF-8 解碼
                body_str = body.decode('utf-8')
            except UnicodeDecodeError:
                # 如果解碼失敗，顯示原始 bytes
                body_str = str(body)

        request_info = {
            "request_id": request_id,
            "method": method,
            "url": url,
            "params": params,
            "body": body_str,
            "content_type": content_type,
            "user_agent": headers.get("user-agent", "")
        }
        self.logger.info(f"Request started: {json.dumps(request_info, ensure_ascii=False)}")

        # 记录请求处理时间
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            status_code = response.status_code

            # 记录成功响应
            response_info = {
                "request_id": request_id,
                "method": method,
                "url": url,
                "status_code": status_code,
                "process_time": round(process_time, 4)
            }

            self.logger.info(f"Request completed: {json.dumps(response_info, ensure_ascii=False)}")

            return response

        except Exception as e:
            process_time = time.time() - start_time

            # 记录异常
            error_info = {
                "request_id": request_id,
                "method": method,
                "url": url,
                "error": str(e),
                "process_time": round(process_time, 4)
            }

            self.logger.error(f"Request failed: {json.dumps(error_info, ensure_ascii=False)}")
            raise
