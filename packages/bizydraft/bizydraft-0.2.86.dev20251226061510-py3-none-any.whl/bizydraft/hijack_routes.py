import json

from aiohttp import web
from loguru import logger

from bizydraft.oss_utils import upload_image, upload_mask
from bizydraft.patch_handlers import post_prompt, view_image, view_video

try:
    from server import PromptServer

    comfy_server = PromptServer.instance
except ImportError:
    logger.error(
        "failed to import ComfyUI modules, ensure PYTHONPATH is set correctly. (export PYTHONPATH=$PYTHONPATH:/path/to/ComfyUI)"
    )
    exit(1)


def hijack_routes_pre_add_routes():
    app = comfy_server.app

    async def custom_business_middleware(app, handler):
        routes_patch = {
            ("/view", "GET"): view_image,
            # ("/prompt", "POST"): post_prompt,
            ("/upload/image", "POST"): upload_image,
            ("/upload/mask", "POST"): upload_mask,
            # /api alias
            ("/api/view", "GET"): view_image,
            # ("/api/prompt", "POST"): post_prompt,
            ("/api/upload/image", "POST"): upload_image,
            ("/api/upload/mask", "POST"): upload_mask,
            # VHS plugin support
            ("/api/vhs/viewvideo", "GET"): view_video,
        }

        async def middleware_handler(request):
            if ((request.path, request.method) in routes_patch) or (
                (
                    "/api" + request.path,
                    request.method,
                )
                in routes_patch
            ):
                logger.debug(
                    f"Custom handler for {request.path} with method {request.method}"
                )
                new_handler = routes_patch[(request.path, request.method)]
                return await new_handler(request)

            return await handler(request)

        return middleware_handler

    # 覆盖 /settings 响应，修改设置 NodeIdBadgeMode 为 ShowAll显示id，将 LinkRenderMode 为（Spline=2），显示连线
    async def settings_response_middleware(app, handler):
        async def middleware_handler(request):
            if request.method == "GET":
                p = request.path
                if p == "/settings" or p == "/api/settings":
                    resp = await handler(request)
                    if getattr(resp, "content_type", None) == "application/json":
                        body_bytes = getattr(resp, "body", b"")
                        charset = getattr(resp, "charset", None) or "utf-8"
                        payload = json.loads(body_bytes.decode(charset))
                        if payload.get("Comfy.NodeBadge.NodeIdBadgeMode") != "ShowAll":
                            payload["Comfy.NodeBadge.NodeIdBadgeMode"] = "ShowAll"
                        if payload.get("Comfy.LinkRenderMode") != 2:
                            payload["Comfy.LinkRenderMode"] = 2
                        if payload.get("Comfy.VueNodes.Enabled") != False:
                            payload["Comfy.VueNodes.Enabled"] = False
                        return web.json_response(
                            payload, status=getattr(resp, "status", 200)
                        )
                    return resp
            return await handler(request)

        return middleware_handler

    async def access_control_middleware(app, handler):
        base_white_list = [
            "/prompt",
            "/view",
            "/upload/image",
            "/upload/mask",
            "/vhs/viewvideo",
            "/",
            "/ws",
            "/extensions",
            "/object_info",
            "/object_info/{node_class}",
            "/assets",
            "/users",
            "/settings",
            "/i18n",
            "/userdata",
        ]

        white_list = [
            *base_white_list,
            *(f"/api{path}" for path in base_white_list if path not in ("/", "/ws")),
        ]

        async def middleware_handler(request):
            is_allowed = any(
                request.path == path
                or (
                    request.path.startswith(path.replace("{node_class}", ""))
                    and path != "/"
                    and path != "/api/"
                )
                or ".css" in request.path
                for path in white_list
            )
            #  Access control check for /assets/GraphView-Y3xu9HJK.js.map: allowed
            logger.debug(
                f"Access control check for {request.path}: {'allowed' if is_allowed else 'blocked'}"
            )
            if not is_allowed and "/bizyair" not in request.path:
                logger.info(f"Blocked access to: {request.path}")
                return web.Response(status=403, text="Access Forbidden")

            return await handler(request)

        return middleware_handler

    app.middlewares.extend([custom_business_middleware, settings_response_middleware])

    logger.info("Optimized middleware setup complete.")


def hijack_routes_post_add_routes():
    # do someting after all routes are set up
    logger.info("Post-add routes hijack complete, all routes are set up.")
