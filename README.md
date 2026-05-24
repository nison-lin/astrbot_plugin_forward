# 自动转发插件

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
[![nison-lin](https://img.shields.io/badge/GitHub-nison--lin-181717?logo=github)](https://github.com/nison-lin)

</div>

## 📕 背景

最开始，我只是想做一个自动搬史的bot，可是怎么让bot转发消息呢？我在插件市场找了半天，发现偌大一个插件市场，竟然没有一个最简单的转发插件（也可能是我没找到）。可是，饭可以不吃，史是不能不搬的。于是，我决定自己动手开发一个。这就是这个项目的由来。

ps：在我做完这个插件之后，我才发现原来插件市场是有搬史插件的，甚至是整个市场里star数最高的一个（果然bot的尽头是搬史吗）。好在本项目作为一个通用插件，具有更高的泛用性，因此无法被它替代。

另外，作为学生，本项目是本人第一个开源项目，如有粗陋之处，还请见谅。

## 🛠️ 功能

自动监测对应群聊是否出现满足条件的消息，并转发至其他群聊。

- **纯文本消息：**
  - 使用正则表达式自动匹配消息
  - 使用ai来判断该消息是否满足条件
- **图片消息：**
  - 仅支持使用ai来识别图片是否满足条件
  - 图片体积过大时自动压缩图片（这项功能的目的是节省token，因此只在发给ai时压缩图片，最终转发的仍是原图）
  - 图片尺寸过大时自动缩放图片（防止超出ai模型的尺寸限制）

## ❗ 注意

- 本插件的设计初衷是让bot成为一个自动转发（包括但不限于史，涩图）的机器人，因此不建议配置人格
- 不建议在配置本插件的同时配置其他插件。但该条仅作为建议，并未强制禁止
- 如果开启图片转发功能，默认对话模型必须配置为具有图片识别能力的模型

## ❓ 常见问题

1. 问题1：

   - Q：产生了这样的报错：Input error. Value error, Invalid chat format. Expected 'text' field in text type content part to be a string
   - A：配置的默认对话模型不支持图像识别（注意是默认对话模型，而不是默认图片转述模型）

2. 问题2：

   - Q：产生了这样的报错：input size exceed limit 2048x2048,current input:(1344,2240)
   - A：图片尺寸过大，建议打开图片尺寸上限功能

3. 问题3：

   - Q：为什么bot会回复群u的消息
   - A：由于平台源码的关系，在使用唤醒词或者只@不说话时会触发bot的自动回复。因此建议关掉配置文件中的这两项配置：
      ![alt text](image\readme.png)

## ✅ 待办

- [x] 优化图片存储逻辑，降低存储空间占用
- [ ] 添加根据文本模糊匹配功能
- [ ] 将简单的提示词改为function calling
- [ ] 添加聊天记录转发功能
- [ ] 添加统计功能

## ✍ 写在最后

欢迎提供建议！欢迎提交issue！欢迎一切对改进插件有益的行为！
