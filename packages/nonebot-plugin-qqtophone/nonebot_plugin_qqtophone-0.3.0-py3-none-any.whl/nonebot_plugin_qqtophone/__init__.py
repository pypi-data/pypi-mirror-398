from asyncio import gather, sleep

import httpx
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Message
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="QQ查询",
    description="通过QQ号查询手机号",
    type="application",
    usage="开 [QQ号|@群友]",
    homepage="https://github.com/StillMisty/nonebot_plugin_qqtophone",
)


async def is_at_qq(args: Message = CommandArg()) -> bool:
    for seg in args:
        if seg.type == "at":
            return True
        if seg.type == "text":
            texts: str = seg.data["text"].strip()
            for text in texts.split():
                if text.isdigit() and 6 <= len(text) <= 12:
                    return True
    return False


qqtophone = on_command("开", priority=5, block=True, rule=is_at_qq)

_http_client = httpx.AsyncClient(
    timeout=10, limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
)
url = "https://zhonghechaxun.adm4n001.workers.dev/cx"


async def query_qq(qq: str) -> str:
    try:
        res = res = await _http_client.get(url, params={"text": qq})
        res.raise_for_status()
        data = res.json()
        if data.get("code") == 200:
            result_lines = []
            results: dict[str, list[dict[str, str]]] = data.get("results")
            for resultKey, resultVal in results.items():
                result_lines.append(f"【{resultKey}】")
                for vals in resultVal:
                    for key, val in vals.items():
                        result_lines.append(f"{key}：{val}")

            # 无返回结果
            if not result_lines:
                return "该账号信息未泄露"

            return "\n".join(result_lines)

        else:
            logger.error(f"未知错误，返回信息：{data}")
            return "查询失败：未知错误"
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e}")
        return f"查询失败：服务器错误，状态码{e.response.status_code}"
    except httpx.TimeoutException:
        return "查询失败：请求超时"
    except httpx.RequestError as e:
        logger.error(f"Request error occurred: {e}")
        return "查询失败：请稍后再试"
    except Exception:
        logger.exception("An unexpected error occurred")
        return "查询失败：发生未知错误"


@qqtophone.handle()
async def _(bot: Bot, args: Message = CommandArg()):
    qqs = set()
    for seg in args:
        if seg.type == "at":
            qqs.add(str(seg.data["qq"]))

        elif seg.type == "text":
            texts: str = seg.data["text"].strip()
            for text in texts.split():
                if text.isdigit() and 6 <= len(text) <= 12:
                    qqs.add(text)

    if not qqs:
        await qqtophone.finish("未提供有效的QQ号", at_sender=True)
        return

    tasks = [get_info(bot, qq) for qq in qqs]
    results = await gather(*tasks)
    msg_id = (await qqtophone.send("\n\n".join(results)))["message_id"]
    # 等待20秒后撤回消息
    await sleep(20)
    try:
        await bot.delete_msg(message_id=msg_id)
    except Exception as e:
        logger.exception(f"删除消息失败: {e}")


async def get_info(bot: Bot, qq: str) -> str:
    msg = await query_qq(qq)
    nickname = (await bot.get_stranger_info(user_id=int(qq)))["nickname"]
    return f"{nickname}\n{msg}"
