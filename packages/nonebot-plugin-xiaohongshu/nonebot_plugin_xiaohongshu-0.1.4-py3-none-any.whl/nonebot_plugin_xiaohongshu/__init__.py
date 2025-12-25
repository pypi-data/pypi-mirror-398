import httpx
from typing import List, Optional, Dict, Any

from nonebot import on_regex, logger, get_plugin_config
from nonebot.plugin import PluginMetadata
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11 import (
    Bot, 
    Event, 
    GroupMessageEvent, 
    PrivateMessageEvent, 
    Message, 
    MessageSegment
)
from nonebot.params import RegexStr
from nonebot.exception import ActionFailed

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="小红书去水印解析",
    description="基于 NoneBot2 的小红书去水印解析插件",
    usage="直接在群聊或私聊中发送包含小红书链接的消息",
    type="application",
    homepage="https://github.com/bytedo/nonebot-plugin-xiaohongshu", 
    config=Config,
    supported_adapters={"~onebot.v11"},
)

plugin_config = get_plugin_config(Config)

XHS_REGEX = r"(https?://(?:xhslink\.com|www\.xiaohongshu\.com)/[a-zA-Z0-9/_]+)"

xhs_matcher = on_regex(XHS_REGEX, priority=10, block=False)

@xhs_matcher.handle()
async def handle_xhs(bot: Bot, event: Event, state: T_State, url: str = RegexStr()):
    origin_url = url.split('?')[0]
    
    try:
        # 获取数据
        note_data = await get_note_data(origin_url)
        
        if not note_data:
            await xhs_matcher.finish("解析失败：接口返回为空或文章已被删除。")

        title = note_data.get("title", "无标题")
        await xhs_matcher.send(Message(f"【{title}】"))

        # 收集所有的媒体片段 (图片+视频)
        media_segments = []
        
        # 处理视频
        if note_data.get("type") == "视频" or note_data.get("url"):
            video_url = note_data.get("url")
            if video_url:
                media_segments.append(MessageSegment.video(video_url))
        
        # 处理图片
        images = note_data.get("images", [])
        if images:
            for img_url in images:
                media_segments.append(MessageSegment.image(img_url))
        elif not media_segments and note_data.get("cover"):
             media_segments.append(MessageSegment.image(note_data.get("cover")))

        if not media_segments:
             await xhs_matcher.finish("解析成功，但未找到可发送的图片或视频。")

        if len(media_segments) > 3:
            await send_forward_msg_media_only(bot, event, media_segments)
        else:
            await send_normal_msg_media_only(media_segments)

    except ActionFailed as e:
        logger.warning(f"消息发送被风控或失败: {e}")
    except Exception as e:
        logger.error(f"XHS Plugin Error: {e}")
        await xhs_matcher.finish(f"解析出错：{str(e)}")


async def send_normal_msg_media_only(segments: List[MessageSegment]):
    """普通发送模式"""
    img_segs = [seg for seg in segments if seg.type == "image"]
    video_segs = [seg for seg in segments if seg.type == "video"]

    if img_segs:
        await xhs_matcher.send(Message(img_segs))
    
    for video in video_segs:
        await xhs_matcher.send(Message(video))


async def send_forward_msg_media_only(bot: Bot, event: Event, segments: List[MessageSegment]):
    """合并转发模式"""
    nodes = []
    
    for seg in segments:
        nodes.append(
            MessageSegment.node_custom(
                user_id=int(bot.self_id),
                nickname="小红书",
                content=Message(seg)
            )
        )

    if isinstance(event, GroupMessageEvent):
        await bot.call_api("send_group_forward_msg", group_id=event.group_id, messages=nodes)
    elif isinstance(event, PrivateMessageEvent):
        await bot.call_api("send_private_forward_msg", user_id=event.user_id, messages=nodes)
    else:
        await send_normal_msg_media_only(segments)


async def get_note_data(url: str) -> Optional[Dict[str, Any]]:
    """请求 API 获取数据"""
    api_url = plugin_config.xhs_api_url
    params = {"url": url}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(api_url, params=params, headers=headers)
            if resp.status_code == 200:
                res_json = resp.json()
                if res_json.get("code") == 200:
                    return res_json.get("data")
                else:
                    logger.error(f"API 返回错误: {res_json.get('msg')}")
            else:
                logger.error(f"API 状态码错误: {resp.status_code}")
        except Exception as e:
            logger.error(f"网络请求错误: {e}")
            return None
    return None