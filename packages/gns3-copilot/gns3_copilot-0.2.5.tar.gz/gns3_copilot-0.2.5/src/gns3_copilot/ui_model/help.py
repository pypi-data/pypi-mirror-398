"""
GNS3 Copilot Help and Configuration Guide Module.

This module provides a comprehensive bilingual help interface for GNS3 Copilot users,
offering detailed configuration guidance in both English and Chinese. It includes
step-by-step instructions for setting up GNS3 server connections, LLM model
configurations, and third-party platform integrations.

Features:
- Bilingual support (English/Chinese) with tabbed interface
- GNS3 server configuration guidance
- LLM model provider setup instructions
- Third-party platform integration examples (OpenRouter)
- Configuration validation and troubleshooting tips
- Step-by-step setup workflow

The help content is organized into clear sections covering all aspects of
GNS3 Copilot configuration, making it easy for users to properly set up
and configure the application for optimal functionality.
"""

import streamlit as st

tab1_en, tab2_zh = st.tabs(["Help", "帮助"])

with tab1_en:
    st.title("GNS3 Copilot Configuration Guide")

    st.header("🔧 GNS3 Server Configuration")
    st.markdown("""
    - **GNS3 Server Host** (Required) - GNS3 server address, e.g., 127.0.0.1
    - **GNS3 Server URL** (Required) - GNS3 server URL, e.g., http://127.0.0.1:3080
    - **GNS3 API Version** - Select API version: 2 or 3(Currently only GNS3 version 2.x is supported)
    - **GNS3 User** (Required for API v3) - GNS3 server username
    - **GNS3 Passwd** (Required for API v3) - GNS3 server password
    """)

    st.header("🤖 LLM Model Configuration")
    st.markdown("""
    - **Model Provider** (Required) - Model provider: deepseek, openai, anthropic, etc.
    - **Model Name** (Required) - Model name: deepseek-chat, gpt-4o-mini, etc.
    - **Model Temperature** - Controls output randomness, range 0.0-1.0
    - **Base Url** - Third-party platform API endpoint
    - **Model API Key** (Required) - Model provider's API key
    """)

    st.header("🐧 Other Settings")
    st.markdown("""
    - **Linux Console Username** - Linux device console username
    - **Linux Console Password** - Linux device console password
    """)

    st.header("🌐 Third-Party Platform Setup (OpenRouter Example)")
    st.code(
        """
Model Provider: openai
Base Url: https://openrouter.ai/api/v1
Model Name: openai/gpt-4o-mini
Model API Key: sk-or-v1-xxxxxxxxx
""",
        language="yaml",
    )

    st.header("⚠️ Important Notes")
    st.markdown("""
    1. **Fields marked with * are required**
    2. **Must click "Save Settings to .env" button after configuration**
    3. **Linux credentials required for Linux-related tools**
    4. **Valid API key and model configuration required for AI functionality**
    5. **For OpenRouter and similar platforms, set Model Provider to `openai`**
    """)

    st.header("📝 Configuration Steps")
    st.markdown("""
    1. Fill all required fields
    2. Adjust optional parameters as needed
    3. Click save button
    4. Restart application for changes to take effect
    """)

with tab2_zh:
    st.title("GNS3 Copilot 配置指南")

    st.header("🔧 GNS3 服务器配置")
    st.markdown("""
    - **GNS3 Server Host** (必填) - GNS3服务器地址，如：127.0.0.1
    - **GNS3 Server URL** (必填) - GNS3服务器URL，如：http://127.0.0.1:3080
    - **GNS3 API Version** - 选择API版本：2 或 3（目前仅使用gns3 2.x版本）
    - **GNS3 User** (API v3时必填) - GNS3服务器用户名
    - **GNS3 Passwd** (API v3时必填) - GNS3服务器密码
    """)

    st.header("🤖 LLM 模型配置")
    st.markdown("""
    - **Model Provider** (必填) - 模型提供商：deepseek, openai, anthropic等
    - **Model Name** (必填) - 模型名称：deepseek-chat, gpt-4o-mini等
    - **Model Temperature** - 控制输出随机性，范围0.0-1.0
    - **Base Url** - 第三方平台API地址，如OpenRouter
    - **Model API Key** (必填) - 模型提供商的API密钥
    """)

    st.header("🐧 其他设置")
    st.markdown("""
    - **Linux Console Username** - Linux设备控制台用户名
    - **Linux Console Password** - Linux设备控制台密码
    """)

    st.header("🌐 第三方平台配置 (OpenRouter示例)")
    st.code(
        """
Model Provider: openai
Base Url: https://openrouter.ai/api/v1
Model Name: openai/gpt-4o-mini
Model API Key: sk-or-v1-xxxxxxxxx
""",
        language="yaml",
    )

    st.header("⚠️ 重要提醒")
    st.markdown("""
    1. **带 * 的字段为必填项**
    2. **配置完成后必须点击 "Save Settings to .env" 按钮**
    3. **Linux凭据配置后才能使用Linux相关工具**
    4. **API密钥和模型配置正确才能使用AI功能**
    5. **使用OpenRouter等第三方平台时，Model Provider填 `openai`**
    """)

    st.header("📝 配置流程")
    st.markdown("""
    1. 填写所有必填字段
    2. 根据需要调整可选参数
    3. 点击保存按钮
    4. 重启应用使配置生效
    """)
