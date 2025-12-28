import base64
import json
import os
import re
import uuid
from http.cookies import SimpleCookie
from pathlib import Path
from time import time
from typing import Any, Dict

import aiohttp
import oss2
from aiohttp import web
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from loguru import logger
from werkzeug.utils import secure_filename

from bizydraft.env import BIZYAIR_API_KEY, BIZYDRAFT_SERVER

CLIPSPACE_TO_OSS_MAPPING = {}

private_key_pem = os.getenv(
    "RSA_PRIVATE_KEY",
    """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAuROqSPqhJlpv5R1wDl2sGuyA59Hf1y+VLR0w3cCyM6/WEQ4b
+TBFfM5HeCLc2YVDybc0ZJxsEqCXKpTweMlQg063ECK4961icF3xL8DRfXkwpUFJ
CfG24tLdXwWK3CJDb4RqGSyZm2F0mE/kqMpidsoJrXy24B4iSJrk5DGRSL1dChiL
vuvNNWPtdDHylormBxz2f8ePvvO8v/qsN+Xpxt7YirqWe5P2VavqMv66H7tItcZj
LMIFF2kV8rYF94tk6/jL/Hb7gG7ujG2p5ikG+sNhrzn0TsWdh97S6F9kTC5D1IkM
TXEhedXN1CQ4Z35TvIHxU1DBiax8t8mq/lF3rwIDAQABAoIBAQCvR8SaYWOF41jd
8MdTk7uPtDVRWB9auSHbHC5PllQvR3TBqk8r7V+iF+rwCHSJPgE5ZV0lfE+ORLFm
DrDAdEjgUwhlK71qNLdqHE50H3VIFCLSH8aAuH+wymwFtkYQvhKH5yxksyy3T9EQ
/3lbsnEWd7o6qEa6c0+c27WzuI4UCEdQpeSG+5UYHykC/Rdfc25wXTjeK8QSUcw4
Xlbt1O7omKAdrbSwbTValfqoUpKlAZ55nvJGqHnBWE5cvx9UHPooGWMUpq8004xb
sU42q2mDSEkRNE+irvc1FInxJ+gDk51Qem1r4Uy4pUnzyngXBFrp2XQazE/aVZSr
JG9fxfmBAoGBAN66SwUJg5LsRBFlPZTXzTLTzwXqm8e9ipKfe9dkuXX5Mx9mEbTd
mjZL1pHX0+YZAQu2V6dekvABFwEOnlvm0l0TopR1yyzA7PZK5ZUF0Tb9binLobO1
8G01Cp2jmrlarRGbwRdr9YXQ4ZKbvKUMevzYMIvPUFIkKQxHY/+x2IkRAoGBANS5
gDHwJ/voZTqqcJpn916MwhjsQvOmlNdDzqKe5FYd/DKb1X+tDAXK/sAFMOMj5Row
qCWu5G1T4f7DRY/BDXEU4u6YqcdokXTeZ45Z+fAZotcSit50T9gGoCTx8MMdeTUb
y4uY6cvCnd6x5PYOoBRL9QQX/ML7LX0S1Q2xL/S/AoGAfOQ/nuJ32hIMFSkNAAKG
eOLWan3kvnslUhSF8AD2EhYbuZaVhTLh/2JFPmCk3JjWwkeMHTjl8hjaWmhlGilz
emfBObhXpo/EEFNtK0QozcoMVPlvggMaf1JH0p9j6l3TQFVzT/vkoBXB92DGxlIa
QN/FURB9/KF0NwNtKnsCbdECgYARgUZUVa/koeYaosXrXtzTUf/y7xY/WJjs8e6C
IVMm5wbG3139SK8xltfJ02OHfX+v3QspNrAjcwCo50bFIpzJjm9yNOvbtfYqSNb6
ttrDcEifLC5zSdz8KOdqwuIOHFHKFgR081th4hz9o2P0/5UatnluIc8x+Ftw7GjN
3KPWnwKBgQCrt3Zs5eqDvFRmuB6d1uMFhAPqjrxnvdl3xhONnIopM4A62FLW4AoI
jpIg9K5YWK3nrROMWINH286CewjHXu2fhkhk1VPKo6Mz8bTqUoFZkI8cap/wfyqv
BMb5TNmgx+tp12pH2VNc/kC5c+GKi8VnNYx8K6gRzpZIIDfSUR10RQ==
-----END RSA PRIVATE KEY-----""",
)


class TokenExpiredError(Exception):
    """Exception raised when the token has expired."""

    pass


def decrypt(encrypted_message):
    try:
        if not encrypted_message or not isinstance(encrypted_message, str):
            raise ValueError("无效的加密消息")

        if "v4.public" in encrypted_message:
            return encrypted_message

        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(), password=None, backend=default_backend()
        )

        encrypted_bytes = base64.b64decode(encrypted_message)
        decrypted_bytes = private_key.decrypt(encrypted_bytes, padding.PKCS1v15())
        decrypted_str = decrypted_bytes.decode("utf-8")

        parsed_data = json.loads(decrypted_str)

        now = int(time() * 1000)  # Convert to milliseconds to match JavaScript
        if now - parsed_data["timestamp"] > parsed_data["expiresIn"]:
            raise TokenExpiredError("Token已过期")

        return parsed_data["data"]

    except Exception as error:
        logger.error(
            "解密失败:",
            {
                "message": str(error),
                "input": encrypted_message[:100] + "..." if encrypted_message else None,
            },
        )
        return None


async def get_upload_token(
    filename: str,
    api_key: str,
) -> Dict[str, Any]:
    from urllib.parse import quote

    # 对文件名进行URL编码，避免特殊字符导致问题
    encoded_filename = quote(filename, safe="")
    url = (
        f"{BIZYDRAFT_SERVER}/upload/token?file_name={encoded_filename}&file_type=inputs"
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                response.raise_for_status()


async def upload_filefield_to_oss(file_field, token_data):
    file_info = token_data["data"]["file"]
    storage_info = token_data["data"]["storage"]

    auth = oss2.StsAuth(
        file_info["access_key_id"],
        file_info["access_key_secret"],
        file_info["security_token"],
    )
    bucket = oss2.Bucket(
        auth, f"http://{storage_info['endpoint']}", storage_info["bucket"]
    )

    try:
        result = bucket.put_object(
            file_info["object_key"],  # OSS存储路径
            file_field.file,  # 直接使用文件流对象
            headers={
                "Content-Type": file_field.content_type,  # 保留原始MIME类型
                "Content-Disposition": f"attachment; filename={secure_filename(file_field.filename)}",
            },
        )

        if result.status == 200:
            return {
                "status": result.status,
                "url": f"https://{storage_info['bucket']}.{storage_info['endpoint']}/{file_info['object_key']}",
            }
        else:
            return {
                "status": result.status,
                "reason": f"OSS返回状态码: {result.status}",
            }

    except Exception as e:
        return {"status": 500, "reason": str(e)}


async def commit_file(object_key: str, filename: str, api_key: str):
    url = f"{BIZYDRAFT_SERVER}/input_resource/commit"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "object_key": object_key,
        "name": filename,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                return await response.json()
            response.raise_for_status()


async def upload_to_oss(post, api_key: str):
    from bizydraft.oss_utils import get_upload_token

    image = post.get("image")
    overwrite = post.get("overwrite")
    image_upload_type = post.get("type")
    subfolder = post.get("subfolder", "")
    logger.debug(f"{image=}, {overwrite=}, {image_upload_type=}, {subfolder=}")

    if not (image and image.file):
        return web.Response(status=400)

    original_frontend_filename = image.filename  # 保存前端发送的原始文件名
    filename = image.filename
    if not filename:
        return web.Response(status=400)

    should_clean, filename = clean_filename(filename)
    if should_clean:
        filename = f"{uuid.uuid4()}.{filename}"

    oss_token = await get_upload_token(filename, api_key)
    result = await upload_filefield_to_oss(image, oss_token)
    if result["status"] != 200:
        return web.Response(status=result["status"], text=result.get("reason", ""))
    logger.debug(f"upload file: {result['url']}")
    try:
        object_key = oss_token["data"]["file"]["object_key"]
        await commit_file(object_key, filename, api_key)
        logger.debug(f"sucess: commit {filename=}")
    except Exception as e:
        logger.error(f"Commit file failed: {e}")
        return web.Response(status=500, text=str(e))

    # 将 OSS URL 拆分成 filename 和 subfolder，以便前端正确构建 /api/view 请求
    # 例如: https://bizyair-prod.oss-cn-shanghai.aliyuncs.com/inputs/20250930/file.png
    oss_url = result["url"]
    oss_filename = oss_url.split("/")[-1]  # 获取最后一部分作为文件名
    oss_subfolder = "/".join(
        oss_url.split("/")[:-1]
    )  # 获取除文件名外的部分作为 subfolder

    if original_frontend_filename:
        CLIPSPACE_TO_OSS_MAPPING[original_frontend_filename] = oss_url
        logger.info(
            f"[OSS_MAPPING] Cached mapping: {original_frontend_filename} -> {oss_url}"
        )

    return web.json_response(
        {"name": oss_filename, "subfolder": oss_subfolder, "type": image_upload_type}
    )


def get_api_key(request):
    if BIZYAIR_API_KEY:
        return BIZYAIR_API_KEY

    cookies = request.headers.get("Cookie")
    if not cookies:
        return None

    try:
        cookie = SimpleCookie()
        cookie.load(cookies)

        bizy_token = cookie.get("bizy_token").value if "bizy_token" in cookie else None

        decrypted_token = decrypt(bizy_token)
        api_key = decrypted_token if decrypted_token else None

    except Exception as e:
        logger.error(f"error happens when get_api_key from cookies: {e}")
        return None

    return api_key


async def upload_image(request):
    logger.debug(f"Received request to upload image: {request.path}")
    api_key = get_api_key(request)
    if not api_key:
        return web.Response(status=403, text="No validated key found")
    post = await request.post()
    return await upload_to_oss(post, api_key)


async def upload_mask(request):
    """
    处理 mask editor 上传，将带 alpha 通道的图片上传到 OSS
    """
    import io
    import json
    import tempfile

    from PIL import Image
    from PIL.PngImagePlugin import PngInfo

    api_key = get_api_key(request)
    if not api_key:
        logger.error("[UPLOAD_MASK] No API key found")
        return web.Response(status=403, text="No validated key found")

    post = await request.post()

    # 获取上传的 mask 图片
    mask_image = post.get("image")
    if not (mask_image and mask_image.file):
        logger.error("[UPLOAD_MASK] No image provided in request")
        return web.Response(status=400, text="No image provided")

    # 保存前端发送的原始文件名，用于后续缓存映射
    original_frontend_filename = mask_image.filename

    # 获取原始图片引用
    original_ref_str = post.get("original_ref")

    if not original_ref_str:
        # 如果没有 original_ref，直接上传 mask
        return await upload_to_oss(post, api_key)

    try:
        from urllib.parse import unquote

        original_ref = json.loads(original_ref_str)
        original_filename = original_ref.get("filename")
        original_subfolder = original_ref.get("subfolder", "")

        if not original_filename:
            logger.error("[UPLOAD_MASK] No filename in original_ref")
            return web.Response(status=400, text="No filename in original_ref")

        # 构建完整的 OSS URL（类似 view_image 的逻辑）
        http_prefix_options = ("http:", "https:")

        if "http" in original_subfolder:
            # subfolder 中包含 URL 基础路径
            original_subfolder = original_subfolder[original_subfolder.find("http") :]
            original_subfolder = unquote(original_subfolder)
            if "https:/" in original_subfolder and not original_subfolder.startswith(
                "https://"
            ):
                original_subfolder = original_subfolder.replace(
                    "https:/", "https://", 1
                )
            if "http:/" in original_subfolder and not original_subfolder.startswith(
                "http://"
            ):
                original_subfolder = original_subfolder.replace("http:/", "http://", 1)
            original_url = f"{original_subfolder}/{original_filename}"
        elif original_filename.startswith(http_prefix_options):
            # filename 本身就是完整 URL
            original_url = original_filename
        elif (
            original_subfolder == "clipspace"
            and original_filename in CLIPSPACE_TO_OSS_MAPPING
        ):
            # 检查缓存：如果是 clipspace 文件且在缓存中，使用缓存的 OSS URL
            original_url = CLIPSPACE_TO_OSS_MAPPING[original_filename]
        else:
            # 不是 OSS URL 格式且不在缓存中，直接上传 mask 图片
            return await upload_to_oss(post, api_key)

        async with aiohttp.ClientSession() as session:
            async with session.get(original_url) as resp:
                if resp.status != 200:
                    logger.error(
                        f"[UPLOAD_MASK] Failed to download original image: {resp.status}"
                    )
                    return web.Response(
                        status=502,
                        text=f"Failed to download original image: {resp.status}",
                    )
                original_image_data = await resp.read()

        # 处理图片：应用 alpha 通道
        with Image.open(io.BytesIO(original_image_data)) as original_pil:
            # 保存元数据
            metadata = PngInfo()
            if hasattr(original_pil, "text"):
                for key in original_pil.text:
                    metadata.add_text(key, original_pil.text[key])

            # 转换为 RGBA
            original_pil = original_pil.convert("RGBA")

            # 读取上传的 mask
            mask_pil = Image.open(mask_image.file).convert("RGBA")

            # alpha copy - 从 mask 提取 alpha 通道并应用到原图
            new_alpha = mask_pil.getchannel("A")
            original_pil.putalpha(new_alpha)

            # 保存到临时文件
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                tmp_filepath = tmp_file.name
                original_pil.save(tmp_filepath, compress_level=4, pnginfo=metadata)

        # 准备上传到 OSS
        filename = f"clipspace-mask-{uuid.uuid4().hex[:8]}.png"
        # subfolder = post.get("subfolder", "clipspace")
        image_upload_type = post.get("type", "input")

        try:
            # 获取上传 token
            oss_token = await get_upload_token(filename, api_key)

            # 读取临时文件并上传
            with open(tmp_filepath, "rb") as f:
                # 创建一个类似 FileField 的对象
                class FileFieldLike:
                    def __init__(self, file_obj, filename, content_type):
                        self.file = file_obj
                        self.filename = filename
                        self.content_type = content_type

                file_field = FileFieldLike(f, filename, "image/png")
                result = await upload_filefield_to_oss(file_field, oss_token)

            if result["status"] != 200:
                logger.error(f"[UPLOAD_MASK] Upload failed: {result.get('reason', '')}")
                return web.Response(
                    status=result["status"], text=result.get("reason", "")
                )

            # Commit file
            object_key = oss_token["data"]["file"]["object_key"]
            await commit_file(object_key, filename, api_key)

            # 将 OSS URL 拆分成 filename 和 subfolder，以便前端正确构建 /api/view 请求
            oss_url = result["url"]
            oss_filename = oss_url.split("/")[-1]
            oss_subfolder = "/".join(oss_url.split("/")[:-1])

            if original_frontend_filename:
                CLIPSPACE_TO_OSS_MAPPING[original_frontend_filename] = oss_url

            response_data = {
                "name": oss_filename,
                "subfolder": oss_subfolder,
                "type": image_upload_type,
            }
            return web.json_response(response_data)

        finally:
            # 清理临时文件
            if os.path.exists(tmp_filepath):
                os.remove(tmp_filepath)

    except Exception as e:
        logger.error(f"[UPLOAD_MASK] ERROR processing mask upload: {e}", exc_info=True)
        return web.Response(status=500, text=f"Error processing mask: {str(e)}")


def _should_clean(name: str) -> bool:
    """True -> 包含非白名单字符；False -> 正常

    使用白名单机制：只允许安全字符（中英文、数字、下划线、连字符、点、空格）
    如果文件名包含白名单之外的字符，则需要清理
    """
    if not name:
        return False

    # 分离文件名和扩展名
    if "." not in name:
        return False

    # 白名单：允许中英文、数字、下划线、连字符、点、空格、圆括号
    safe_pattern = r"^[\w\u4e00-\u9fa5\s\-().]+$"

    return not bool(re.match(safe_pattern, name))


def clean_filename(bad: str) -> (bool, str):
    """对乱码串提取最后扩展名；正常串直接返回原值"""
    if not _should_clean(bad):
        return False, bad
    # 提取最后扩展名（含点）
    ext = re.search(r"(\.[\w]+)$", bad)
    return True, ext.group(1) if ext else bad
