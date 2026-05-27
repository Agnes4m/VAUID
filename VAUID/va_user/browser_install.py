"""Playwright浏览器自动安装辅助模块"""

import os
import asyncio
import subprocess
from typing import Optional, AsyncIterator
from pathlib import Path

from gsuid_core.logger import logger

_DEFAULT_BROWSERS_PATH = str(Path.home() / ".cache" / "ms-playwright")
_PLAYWRIGHT_BROWSERS_PATH_STR = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", _DEFAULT_BROWSERS_PATH)
PLAYWRIGHT_BROWSERS_PATH = Path(_PLAYWRIGHT_BROWSERS_PATH_STR)


def get_chrome_headless_shell_executable() -> Optional[Path]:
    """获取chrome-headless-shell可执行文件路径"""
    chrome_shell_path = (
        PLAYWRIGHT_BROWSERS_PATH
        / "chromium_headless_shell-1208"
        / "chrome-headless-shell-linux64"
        / "chrome-headless-shell"
    )
    if chrome_shell_path.exists():
        return chrome_shell_path

    chromium_default = PLAYWRIGHT_BROWSERS_PATH / "chromium-1208" / "chrome-linux" / "chrome"
    if chromium_default.exists():
        return chromium_default
    return None


def is_browser_installed() -> bool:
    """检查浏览器是否已安装"""
    return get_chrome_headless_shell_executable() is not None


async def _read_stream(stream: asyncio.StreamReader) -> AsyncIterator[str]:
    """异步读取流"""
    while True:
        line = await stream.readline()
        if not line:
            break
        yield line.decode("utf-8", errors="replace").rstrip()


async def install_browsers(bot=None) -> bool:
    """执行playwright install安装浏览器"""
    logger.info("[Val] 正在安装浏览器 (playwright install)...")

    if bot:
        await bot.send("正在安装浏览器，请稍候...\n(首次安装可能需要3-5分钟)")

    try:
        process = await asyncio.create_subprocess_shell(
            "playwright install",
            stdout=asyncio.subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        full_output = []
        if process.stdout:
            async for line in _read_stream(process.stdout):
                full_output.append(line)
                logger.info(f"[Val] {line}")

        await process.wait()

        if process.returncode == 0:
            logger.info("[Val] 浏览器安装成功!")
            return True

        output_str = "\n".join(full_output)
        if "chromium" in output_str.lower() and (
            "downloaded" in output_str.lower() or "installing" in output_str.lower()
        ):
            logger.info("[Val] 浏览器安装完成")
            return True
        logger.error(f"[Val] 浏览器安装失败: returncode={process.returncode}")
        return False

    except FileNotFoundError:
        logger.error("[Val] 未找到playwright命令")
        if bot:
            await bot.send("❌ 未找到playwright命令！请先手动执行: pip install playwright")
        return False
    except Exception as e:
        logger.error(f"[Val] 安装浏览器时发生错误: {e}")
        if bot:
            await bot.send(f"❌ 安装浏览器时发生错误: {e}")
        return False


async def ensure_browser_available(bot=None) -> bool:
    """确保浏览器可用，不存在则自动安装"""
    if is_browser_installed():
        return True

    success = await install_browsers(bot)
    if success and bot:
        await bot.send("✅ 浏览器安装完成！正在重新尝试获取二维码...")
    return success


def is_browser_not_installed_error(error: Exception) -> bool:
    """判断错误是否由浏览器未安装导致"""
    error_str = str(error).lower()
    keywords = [
        "executable doesn't exist",
        "browser not installed",
        "chromium not installed",
        "no chromium found",
        "playwright browsers not installed",
        "no such file or directory",
        "failed to launch",
    ]
    return any(keyword in error_str for keyword in keywords)
