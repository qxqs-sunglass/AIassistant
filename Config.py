# 请在此处配置相关参数
__version__ = "0.0.1"
__author__ = "@bilibili_秋天会有下雪天"

# 基础信息
LOOP_INTERVAL = 0.7
DEFAULT_PATH = "config\\"
PATH_DICT = {
    "BASIS": "basis.json"
}

# 系统提示词
SYSTEM_PROMPT: str = """
你是一个智能语音助手，回答要简洁、友好、有帮助。
你的特点是：
    1. 回答简洁明了，每句话不要太长
    2. 用友好、自然的语气
    3. 中文回答为主，偶尔可以夹杂英文术语
    4. 如果不懂就诚实说不知道
    5. 避免使用复杂格式，纯文本回复
"""

PROMPT_S = """
支持的操作类型(严格遵守)：
1. 系统控制：SYS_C (关机、重启、锁定)
2. 媒体控制：MEDIA_C (播放/暂停、下一首、上一首)
"""

PROMPT_E = """
指令格式：
{{"action": "操作类型", "command": "具体命令", "confidence": 信心度浮点数, "parameters": "额外参数(可选)"}}

规则：
1. action必须是"open_app"、"system_control"、"volume_control"、"media_control"、"key_press"、"network_query"中的一个
2. command必须是上述已知的命令或应用名称
3. confidence必须是0.0到1.0之间的浮点数
4. 如果用户要打开的应用不在已知列表中，command设为"unknown"
5. 对于天气查询，如果用户没有明确指定城市，parameters设为空字符串""
6. 对于搜索查询，parameters可以包含搜索关键词
7. 对于新闻查询，parameters可以包含新闻类型（如科技、体育等）
8. 对于包含城市的天气查询（如"北京天气"），parameters设为城市名（如"北京"）
9. 对于不包含城市的天气查询（如"天气如何"），parameters设为空字符串""
10. 对于"暂停"、"播放"、"暂停播放"等指令，command必须是"play_pause"
11. 对于"音量调至X"、"设置音量到X"等指令，command必须是"set_volume"，parameters设为数字（如"25"、"50"）

示例：
用户说："今天天气怎么样" → {{"action": "network_query", "command": "weather", "confidence": 0.95, "parameters": ""}}
用户说："北京天气" → {{"action": "network_query", "command": "weather", "confidence": 0.95, "parameters": "北京"}}
用户说："天气如何" → {{"action": "network_query", "command": "weather", "confidence": 0.95, "parameters": ""}}
用户说："暂停" → {{"action": "media_control", "command": "play_pause", "confidence": 0.98, "parameters": ""}}
用户说："播放" → {{"action": "media_control", "command": "play_pause", "confidence": 0.98, "parameters": ""}}
用户说："pause" → {{"action": "media_control", "command": "play_pause", "confidence": 0.98, "parameters": ""}}
用户说："下一首" → {{"action": "media_control", "command": "next", "confidence": 0.98, "parameters": ""}}
用户说："上一首" → {{"action": "media_control", "command": "previous", "confidence": 0.98, "parameters": ""}}
用户说："音量调至25" → {{"action": "volume_control", "command": "set_volume", "confidence": 0.95, "parameters": "25"}}
用户说："设置音量到50%" → {{"action": "volume_control", "command": "set_volume", "confidence": 0.95, "parameters": "50"}}
用户说："把音量调到75" → {{"action": "volume_control", "command": "set_volume", "confidence": 0.95, "parameters": "75"}}
用户说："静音" → {{"action": "volume_control", "command": "volume_mute", "confidence": 0.95, "parameters": ""}}

用户指令："{user_input}"

只输出JSON：
"""

DEPEND = """
# ========== 核心HTTP请求 ==========
requests>=2.31.0

# ========== 语音识别相关 ==========
SpeechRecognition>=3.10.0
# PyAudio在Windows需要特殊安装，见下面的说明
# pocketsphinx>=0.1.15  # 可选，离线语音识别

# ========== 语音合成相关 ==========
pyttsx3>=2.90

# ========== 音频处理 ==========
pyaudio>=0.2.11
wave>=0.0.2
sounddevice>=0.4.6
soundfile>=0.12.1

# ========== 数据处理 ==========
numpy>=1.24.0
"""

