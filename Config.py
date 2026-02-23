# 请在此处配置相关参数
__version__ = "0.0.1"
__author__ = "@bilibili_秋天会有下雪天"

# 基础信息
LOOP_INTERVAL = 0.7
DEFAULT_PATH = "config\\"
PATH_DICT = {
    "BASIS": "basis.json",
    "OpenAI": "openai_basis.json"
}



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
sounddevice>=0.4.6
soundfile>=0.12.1

# ========== 数据处理 ==========
numpy>=1.24.0
"""

