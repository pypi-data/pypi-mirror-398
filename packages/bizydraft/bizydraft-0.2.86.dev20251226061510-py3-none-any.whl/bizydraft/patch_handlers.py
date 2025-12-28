import asyncio
import math
import mimetypes
import os
import uuid
from io import BytesIO
from urllib.parse import unquote

from aiohttp import ClientSession, ClientTimeout, web
from loguru import logger
from PIL import Image

try:
    import execution
    from server import PromptServer

    comfy_server = PromptServer.instance
except ImportError:
    logger.error(
        "failed to import ComfyUI modules, ensure PYTHONPATH is set correctly. (export PYTHONPATH=$PYTHONPATH:/path/to/ComfyUI)"
    )
    exit(1)

BIZYDRAFT_MAX_FILE_SIZE = int(
    os.getenv("BIZYDRAFT_MAX_FILE_SIZE", 100 * 1024 * 1024)
)  # 100MB
BIZYDRAFT_REQUEST_TIMEOUT = int(
    os.getenv("BIZYDRAFT_REQUEST_TIMEOUT", 20 * 60)
)  # 20分钟
BIZYDRAFT_CHUNK_SIZE = int(os.getenv("BIZYDRAFT_CHUNK_SIZE", 1024 * 16))  # 16KB


async def view_image(request):

    logger.debug(f"Received request for /view with query: {request.rel_url.query}")
    if "filename" not in request.rel_url.query:
        logger.warning("'filename' not provided in query string, returning 404")
        return web.Response(status=404, text="'filename' not provided in query string")

    filename = request.rel_url.query["filename"]
    subfolder = request.rel_url.query.get("subfolder", "")
    channel = request.rel_url.query.get("channel", "rgba")
    preview = request.rel_url.query.get("preview", None)

    http_prefix_options = ("http:", "https:")

    if not filename.startswith(http_prefix_options) and "http" not in subfolder:
        logger.warning(
            f"Invalid filename format: {filename=}, {subfolder=} only URLs are supported"
        )
        return web.Response(
            status=400, text="Invalid filename format(only url supported)"
        )

    try:
        if "http" in subfolder:
            subfolder = subfolder[subfolder.find("http") :]
        subfolder = unquote(subfolder)
        if "https:/" in subfolder and not subfolder.startswith("https://"):
            subfolder = subfolder.replace("https:/", "https://", 1)
        if "http:/" in subfolder and not subfolder.startswith("http://"):
            subfolder = subfolder.replace("http:/", "http://", 1)

        # 构建完整URL
        full_url = (
            f"{subfolder}/{filename}"
            if not filename.startswith(http_prefix_options)
            else filename
        )

        # 获取原始文件名用于响应头
        original_filename = filename.split("/")[-1] if "/" in filename else filename

        content_type, _ = mimetypes.guess_type(full_url)

        timeout = ClientTimeout(total=BIZYDRAFT_REQUEST_TIMEOUT)
        async with ClientSession(timeout=timeout) as session:
            async with session.get(full_url) as resp:
                resp.raise_for_status()

                # 优先使用服务器返回的Content-Type，如果无法获取则使用猜测的类型
                final_content_type = (
                    resp.headers.get("Content-Type")
                    or content_type
                    or "application/octet-stream"
                )

                content_length = int(resp.headers.get("Content-Length", 0))
                if content_length > BIZYDRAFT_MAX_FILE_SIZE:
                    logger.warning(
                        f"File size {human_readable_size(content_length)} exceeds limit {human_readable_size(BIZYDRAFT_MAX_FILE_SIZE)}"
                    )
                    return web.Response(
                        status=413,
                        text=f"File size exceeds limit ({human_readable_size(BIZYDRAFT_MAX_FILE_SIZE)})",
                    )

                # 检查是否需要图像处理（preview或channel参数）
                is_image = final_content_type and final_content_type.startswith(
                    "image/"
                )
                needs_processing = is_image and (
                    preview is not None or channel != "rgba"
                )

                if needs_processing:
                    logger.debug(f"Image processing requested: {channel=}, {preview=}")
                    # 下载完整图像到内存
                    image_data = await resp.read()

                    # 检查实际大小
                    if len(image_data) > BIZYDRAFT_MAX_FILE_SIZE:
                        return web.Response(
                            status=413,
                            text=f"File size exceeds limit ({human_readable_size(BIZYDRAFT_MAX_FILE_SIZE)})",
                        )

                    # 使用PIL处理图像
                    with Image.open(BytesIO(image_data)) as img:
                        # 处理preview参数
                        if preview is not None:
                            preview_info = preview.split(";")
                            image_format = preview_info[0]
                            if image_format not in ["webp", "jpeg"] or "a" in channel:
                                image_format = "webp"
                            quality = 90
                            if preview_info[-1].isdigit():
                                quality = int(preview_info[-1])

                            buffer = BytesIO()
                            if image_format in ["jpeg"] or channel == "rgb":
                                img = img.convert("RGB")
                            img.save(buffer, format=image_format, quality=quality)
                            buffer.seek(0)

                            return web.Response(
                                body=buffer.read(),
                                content_type=f"image/{image_format}",
                                headers={
                                    "Content-Disposition": f'filename="{original_filename}"'
                                },
                            )

                        # 处理channel参数
                        if channel == "rgb":
                            logger.debug("Converting image to RGB (removing alpha)")
                            if img.mode == "RGBA":
                                r, g, b, a = img.split()
                                new_img = Image.merge("RGB", (r, g, b))
                            else:
                                new_img = img.convert("RGB")

                            buffer = BytesIO()
                            new_img.save(buffer, format="PNG")
                            buffer.seek(0)

                            return web.Response(
                                body=buffer.read(),
                                content_type="image/png",
                                headers={
                                    "Content-Disposition": f'filename="{original_filename}"'
                                },
                            )

                        elif channel == "a":
                            logger.debug("Extracting alpha channel only")
                            if img.mode == "RGBA":
                                _, _, _, a = img.split()
                            else:
                                a = Image.new("L", img.size, 255)

                            # 创建alpha通道图像
                            alpha_img = Image.new("RGBA", img.size)
                            alpha_img.putalpha(a)
                            alpha_buffer = BytesIO()
                            alpha_img.save(alpha_buffer, format="PNG")
                            alpha_buffer.seek(0)

                            return web.Response(
                                body=alpha_buffer.read(),
                                content_type="image/png",
                                headers={
                                    "Content-Disposition": f'filename="{original_filename}"'
                                },
                            )

                # 默认流式传输（无需处理或非图像文件）
                headers = {
                    "Content-Disposition": f'attachment; filename="{original_filename}"',
                    "Content-Type": final_content_type,
                }

                proxy_response = web.StreamResponse(headers=headers)
                await proxy_response.prepare(request)

                total_bytes = 0
                async for chunk in resp.content.iter_chunked(BIZYDRAFT_CHUNK_SIZE):
                    total_bytes += len(chunk)
                    if total_bytes > BIZYDRAFT_MAX_FILE_SIZE:
                        await proxy_response.write(b"")
                        return web.Response(
                            status=413,
                            text=f"File size exceeds limit during streaming ({human_readable_size(BIZYDRAFT_MAX_FILE_SIZE)})",
                        )
                    await proxy_response.write(chunk)

                return proxy_response

    except asyncio.TimeoutError:
        return web.Response(
            status=504,
            text=f"Request timed out (max {BIZYDRAFT_REQUEST_TIMEOUT//60} minutes)",
        )
    except Exception as e:
        logger.error(f"Error in view_image: {str(e)}", exc_info=True)
        return web.Response(
            status=502, text=f"Failed to fetch remote resource: {str(e)}"
        )


def human_readable_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


async def view_video(request):
    """处理VHS插件的viewvideo接口，支持从OSS URL加载视频"""
    logger.debug(
        f"Received request for /vhs/viewvideo with query: {request.rel_url.query}"
    )

    if "filename" not in request.rel_url.query:
        logger.warning("'filename' not provided in query string, returning 404")
        return web.Response(status=404, text="'filename' not provided in query string")

    # VHS插件的filename参数本身就是完整的URL（可能是URL编码的）
    filename = unquote(request.rel_url.query["filename"])

    http_prefix_options = ("http:", "https:")

    if not filename.startswith(http_prefix_options):
        logger.warning(f"Invalid filename format: {filename=}, only URLs are supported")
        return web.Response(
            status=400, text="Invalid filename format(only url supported)"
        )

    try:
        content_type, _ = mimetypes.guess_type(filename)

        timeout = ClientTimeout(total=BIZYDRAFT_REQUEST_TIMEOUT)
        async with ClientSession(timeout=timeout) as session:
            async with session.get(filename) as resp:
                resp.raise_for_status()

                # 优先使用服务器返回的Content-Type
                final_content_type = (
                    resp.headers.get("Content-Type")
                    or content_type
                    or "application/octet-stream"
                )

                content_length = int(resp.headers.get("Content-Length", 0))
                if content_length > BIZYDRAFT_MAX_FILE_SIZE:
                    logger.warning(
                        f"File size {human_readable_size(content_length)} exceeds limit {human_readable_size(BIZYDRAFT_MAX_FILE_SIZE)}"
                    )
                    return web.Response(
                        status=413,
                        text=f"File size exceeds limit ({human_readable_size(BIZYDRAFT_MAX_FILE_SIZE)})",
                    )

                headers = {
                    "Content-Disposition": f'attachment; filename="{uuid.uuid4()}"',
                    "Content-Type": final_content_type,
                }

                proxy_response = web.StreamResponse(headers=headers)
                await proxy_response.prepare(request)

                total_bytes = 0
                async for chunk in resp.content.iter_chunked(BIZYDRAFT_CHUNK_SIZE):
                    total_bytes += len(chunk)
                    if total_bytes > BIZYDRAFT_MAX_FILE_SIZE:
                        await proxy_response.write(b"")
                        return web.Response(
                            status=413,
                            text=f"File size exceeds limit during streaming ({human_readable_size(BIZYDRAFT_MAX_FILE_SIZE)})",
                        )
                    await proxy_response.write(chunk)

                return proxy_response

    except asyncio.TimeoutError:
        return web.Response(
            status=504,
            text=f"Request timed out (max {BIZYDRAFT_REQUEST_TIMEOUT//60} minutes)",
        )
    except Exception as e:
        return web.Response(
            status=502, text=f"Failed to fetch remote resource: {str(e)}"
        )

# deprecated
async def post_prompt(request):
    json_data = await request.json()

    json_data = comfy_server.trigger_on_prompt(json_data)

    if "prompt" in json_data:
        prompt = json_data["prompt"]
        prompt_id = str(json_data.get("prompt_id", uuid.uuid4()))
        partial_execution_targets = None
        if "partial_execution_targets" in json_data:
            partial_execution_targets = json_data["partial_execution_targets"]
        valid = await execution.validate_prompt(
            prompt_id, prompt, partial_execution_targets
        )

        if valid[0]:
            response = {
                "prompt_id": None,
                "number": None,
                "node_errors": valid[3],
            }
            logger.debug(f"Received POST request to /prompt with valid prompt")
            return web.json_response(response)
        else:
            logger.debug(
                f"Fail to validate prompt: {valid[1]=}, node_errors: {valid[3]=}"
            )
            return web.json_response(
                {"error": valid[1], "node_errors": valid[3]}, status=400
            )
    else:
        error = {
            "type": "no_prompt",
            "message": "No prompt provided",
            "details": "No prompt provided",
            "extra_info": {},
        }
        logger.debug(f"Received POST request to /prompt with no prompt: {error}")
        return web.json_response({"error": error, "node_errors": {}}, status=400)
