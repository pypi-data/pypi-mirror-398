# nonebot-plugin-xiaohongshu

_✨ 基于 NoneBot2 的小红书去水印解析插件 ✨_

<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/bytedo/nonebot-plugin-xiaohongshu.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-xiaohongshu">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-xiaohongshu.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="python">

## 📖 介绍

这是一个用于 NoneBot2 的小红书解析插件,当发送包含小红书链接的消息时会自动解析并发送无水印的图片或视频。

**主要功能：**

- 🔗 **自动识别**：支持小红书分享链接
- 💧 **去水印**：自动提取高清无水印图片或视频
- 📦 **智能合并**：
  - 图片/视频数量 ≤ 3：直接发送媒体消息
  - 图片/视频数量 > 3：合并转发防止刷屏
- 🔌 **API 支持**：支持配置外部 API 接口，保证解析稳定性

## 💿 安装

**使用 nb-cli 安装**

```bash
nb plugin install nonebot-plugin-xiaohongshu
```

**使用 pip 安装**

```bash
pip install nonebot-plugin-xiaohongshu
```

## ⚙️ 配置（可选）

在 NoneBot2 项目的 `.env` 文件中添加以下配置（可选）：

| **配置项** | **类型** | **默认值**        | **说明**          |
| ---------------- | -------------- | ----------------------- | ----------------------- |
| `XHS_API_URL`  | str            | `https://example.com` | 小红书解析 API 接口地址 |

> **说明** ：
>
> 1. 插件默认使用免费公开 API，开箱即用。
> 2. 如遇到接口失效或解析失败，请[自行部署](https://alist.mu-jie.cc/Public/%E5%B0%8F%E7%BA%A2%E4%B9%A6%E8%A7%A3%E6%9E%90node%E6%BA%90%E7%A0%81.zip)小红书解析 API 并在 `.env` 中配置接口

## 🎉 使用

触发方式：

直接在群聊或私聊中发送包含小红书链接的消息即可。

## ⚠️ 免责声明

1. 本插件仅供学习和交流使用，请勿用于非法用途。
2. 插件核心功能依赖第三方 API，无法保证 100% 的可用性。
3. 任何因使用本插件产生的问题，开发者不承担任何责任。
4. 小红书数据版权归原作者所有。

## 许可证

MIT
