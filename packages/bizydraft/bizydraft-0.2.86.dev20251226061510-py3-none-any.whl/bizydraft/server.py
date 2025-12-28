import os
from typing import Union

from loguru import logger

from .workflow_io import parse_workflow_io
try:
    import execution
    from server import PromptServer
except ImportError:
    logger.error(
        "Failed to import ComfyUI server modules, ensure PYTHONPATH is set correctly. (export PYTHONPATH=$PYTHONPATH:/path/to/ComfyUI)"
    )
    exit(1)
from aiohttp import web
from .resp import ErrResponse, JsonResponse, OKResponse

_API_PREFIX = "bizyair"
_SERVER_MODE_HC_FLAG = True

BIZYAIR_MAGIC_STRING = os.getenv("BIZYAIR_MAGIC_STRING", "QtDtsxAc8JI1bTb7")

if BIZYAIR_MAGIC_STRING == "QtDtsxAc8JI1bTb7":
    logger.warning(
        "BIZYAIR_MAGIC_STRING is not set, using default value. This is insecure and should be changed in production!"
    )


class BizyDraftServer:
    def __init__(self):
        BizyDraftServer.instance = self
        self.prompt_server = PromptServer.instance
        self.setup_routes()

    def setup_routes(self):
        @self.prompt_server.routes.get(f"/{_API_PREFIX}/are_you_alive")
        async def are_you_alive(request) -> Union[OKResponse, ErrResponse]:
            if _SERVER_MODE_HC_FLAG:
                return OKResponse()
            return ErrResponse(500)

        @self.prompt_server.routes.post(
            f"/{_API_PREFIX}/are_you_alive_{BIZYAIR_MAGIC_STRING}"
        )
        async def toggle_are_you_alive(request) -> OKResponse:
            global _SERVER_MODE_HC_FLAG
            _SERVER_MODE_HC_FLAG = not _SERVER_MODE_HC_FLAG
            return OKResponse()

        @self.prompt_server.routes.post(f"/{_API_PREFIX}/workflow_io")
        async def workflow_io(request) -> Union[JsonResponse, ErrResponse]:
            try:
                data = await request.json()
            except Exception as e:
                logger.error(f"解析 request.json() 失败: {e}")
                return ErrResponse(400)
            try:
                response = parse_workflow_io(data)
                return JsonResponse(200, response)
            except Exception as e:
                logger.error(f"parse_workflow_io 处理失败: {e}")
                return ErrResponse(500)
        
        @self.prompt_server.routes.post(f"/{_API_PREFIX}/workflow_valid")
        async def workflow_valid(request):
            logger.info("got workflow_valid request")
            json_data =  await request.json()
            json_data = self.prompt_server.trigger_on_prompt(json_data)

            if "number" in json_data:
                number = float(json_data['number'])
            else:
                number = self.number
                if "front" in json_data:
                    if json_data['front']:
                        number = -number

                self.number += 1

            if "prompt" in json_data:
                prompt = json_data["prompt"]
                prompt_id = str(json_data.get("prompt_id", uuid.uuid4()))

                partial_execution_targets = None
                if "partial_execution_targets" in json_data:
                    partial_execution_targets = json_data["partial_execution_targets"]

                valid = await execution.validate_prompt(prompt_id, prompt, partial_execution_targets)
                extra_data = {}
                if "extra_data" in json_data:
                    extra_data = json_data["extra_data"]

                if "client_id" in json_data:
                    extra_data["client_id"] = json_data["client_id"]
                if valid[0]:
                    sensitive = {}
                    for sensitive_val in execution.SENSITIVE_EXTRA_DATA_KEYS:
                        if sensitive_val in extra_data:
                            sensitive[sensitive_val] = extra_data.pop(sensitive_val)
                    response = {"prompt_id": prompt_id, "number": number, "node_errors": valid[3]}
                    return web.json_response(response)
                else:
                    logger.warning("invalid prompt: {}".format(valid[1]))
                    return web.json_response({"error": valid[1], "node_errors": valid[3]}, status=400)
            else:
                error = {
                    "type": "no_prompt",
                    "message": "No prompt provided",
                    "details": "No prompt provided",
                    "extra_info": {}
                }
                return web.json_response({"error": error, "node_errors": {}}, status=400)

    