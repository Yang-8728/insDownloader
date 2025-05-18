#!/usr/bin/env python3
import os
import time
import glob
import random
import logging
import sys

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

# ==== 配置 / Configuration ====# Chrome浏览器和驱动路径 / Chrome browser and driver paths
CHROMEDRIVER_PATH = r"C:\Code\instagramDownloader\tools\chromedriver-win64\chromedriver.exe"
MERGED_FOLDER = r"C:\Code\instagramDownloader\merged"  # 合并视频目录 / Merged videos directory
PROFILE_PATH = r"C:\Code\instagramDownloader\selenium_profile"  # 浏览器配置文件目录 / Browser profile directory
TITLE_PREFIX = "海外离大谱#"  # 视频标题前缀 / Video title prefix
SCREENSHOT_DIR = "screenshots"  # 截图保存目录 / Screenshots directory
SERIAL_NUMBER_FILE = "serial_number.txt"  # 序列号记录文件 / Serial number record file
os.makedirs(SCREENSHOT_DIR, exist_ok=True)  # 确保截图目录存在 / Ensure screenshots directory exists

# 屏蔽日志输出 / Suppress log output
logging.getLogger("selenium").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("webdriver").setLevel(logging.ERROR)

# 重定向Chrome错误输出 / Redirect Chrome stderr output
os.environ["CHROME_LOG_FILE"] = os.devnull


def load_serial_number():
    """加载序列号，不存在则从20开始
    Load serial number, start from 20 if not exists"""
    return int(open(SERIAL_NUMBER_FILE).read()) if os.path.exists(SERIAL_NUMBER_FILE) else 20

def save_serial_number(num):
    """保存序列号到文件
    Save serial number to file"""
    with open(SERIAL_NUMBER_FILE, "w") as f:
        f.write(str(num))

def find_latest_video(folder):
    """查找指定文件夹中最新的视频文件
    Find the latest video file in the specified folder"""
    videos = glob.glob(os.path.join(folder, "*.mp4"))
    if not videos:
        raise FileNotFoundError("❌ merged 文件夹中没有找到视频")
    return max(videos, key=os.path.getmtime)  # 返回修改时间最新的视频 / Return the video with the latest modification time


def init_browser():
    """初始化Chrome浏览器，配置各种选项
    Initialize Chrome browser with various options"""
    options = Options()
    # 抑制浏览器日志输出 / Suppress browser log output
    options.add_argument("--log-level=3")  # 仅显示致命错误 / Show only fatal errors
    options.add_argument("--silent")
    options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,  # 禁用通知 / Disable notifications
        "browser.enable_spellchecking": False,  # 禁用拼写检查 / Disable spell checking
        "credentials_enable_service": False,     # 禁用密码保存提示 / Disable password save prompt
        "profile.password_manager_enabled": False # 禁用密码管理器 / Disable password manager
    })
    
    # 浏览器配置 / Browser configuration
    options.add_argument(f"--user-data-dir={PROFILE_PATH}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--window-size=960,1080")  # 设置窗口大小 / Set window size
    options.add_argument("--window-position=960,0")  # 设置窗口位置 / Set window position
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")  # 修复沙盒错误 / Fix sandbox errors
    options.add_argument("--disable-dev-shm-usage")  # 解决内存问题 / Solve memory issues
    
    # 禁用扩展和自动化信息条 / Disable extensions and automation info bar
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    
    service = Service(CHROMEDRIVER_PATH)
    service.log_path = os.devnull  # 禁用WebDriver日志 / Disable WebDriver logs
    
    # 捕获stderr / Capture stderr
    original_stderr = sys.stderr
    sys.stderr = open(os.devnull, 'w')
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
        # 禁用JavaScript控制台日志 / Disable JavaScript console logs
        driver.execute_script("console.log = function() {};")
        driver.execute_script("console.error = function() {};")
        driver.execute_script("console.warn = function() {};")
    finally:
        # 恢复stderr / Restore stderr
        sys.stderr.close()
        sys.stderr = original_stderr
    
    return driver, WebDriverWait(driver, 30)  # 返回驱动和等待对象 / Return driver and wait object


def open_upload_page(driver):
    """打开B站投稿页面
    Open Bilibili upload page"""
    driver.get("https://member.bilibili.com/platform/upload/video/")
    time.sleep(3)  # 等待页面加载 / Wait for page to load
    driver.execute_script("document.body.style.zoom='90%'")  # 缩小页面以便显示全部内容 / Zoom out to show all content


def upload_video(driver, video_path):
    """上传视频到B站
    Upload video to Bilibili"""
    # 等待上传区域出现 / Wait for upload area to appear
    upload_section = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "bcc-upload"))
    )
    # 查找文件上传输入元素 / Find file upload input element
    upload_input = upload_section.find_element(By.XPATH, './/input[@type="file"]')
    # 确保输入框可见 / Make sure input is visible
    driver.execute_script("arguments[0].style.display = 'block';", upload_input)
    # 发送文件路径 / Send file path
    upload_input.send_keys(video_path)


def wait_for_upload_complete(driver):
    """等待视频上传完成
    Wait for video upload to complete"""
    wait = WebDriverWait(driver, 600)  # 最多等待10分钟 / Wait for up to 10 minutes
    # 等待上传完成提示出现 / Wait for upload complete prompt
    wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(text(), "上传完成")]')))
    # 等待进度条消失 / Wait for progress bar to disappear
    wait.until_not(EC.presence_of_element_located((By.CSS_SELECTOR, ".el-progress__text, .uploading, .progress")))
    time.sleep(3)  # 额外等待以确保UI更新 / Additional wait to ensure UI updates


def fill_title(driver):
    """填写视频标题
    Fill video title"""
    # 等待标题输入框出现 / Wait for title input to appear
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.XPATH, '//input[@placeholder="请输入稿件标题"]'))
    )
    # 获取序列号并生成标题 / Get serial number and generate title
    serial = load_serial_number()
    title = f"{TITLE_PREFIX}{serial}"
    # 清空并填写标题 / Clear and fill title
    input_box = driver.find_element(By.XPATH, '//input[@placeholder="请输入稿件标题"]')
    input_box.clear()
    input_box.send_keys(title)
    # 保存下一个序列号 / Save next serial number
    save_serial_number(serial + 1)


def click_publish(driver):
    """点击立即投稿按钮
    Click the publish button"""
    # 寻找并点击投稿按钮 / Find and click publish button
    button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, '//span[contains(text(), "立即投稿")]'))
    )
    # 滚动到按钮位置 / Scroll to button position
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
    # 使用ActionChains点击以提高可靠性 / Use ActionChains to click for better reliability
    ActionChains(driver).move_to_element(button).pause(0.5).click().perform()


def wait_for_publish_success(driver):
    """等待投稿成功
    Wait for publish success"""
    try:
        # 等待成功提示 / Wait for success prompt
        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.XPATH, '//div[contains(text(), "稿件投递成功")]'))
        )
        # 截图保存成功状态 / Take screenshot of success state
        now = time.strftime("%Y%m%d_%H%M%S")
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, f"投稿成功_{now}.png"))
    except TimeoutException:
        # 超时不报错，继续流程 / Don't raise error on timeout, continue process
        pass


def upload_latest_merged_video(video_path=None):
    """上传最新合并的视频到B站
    Upload the latest merged video to Bilibili
    
    Args:
        video_path: 可选，指定要上传的视频路径，如果为None则自动查找最新视频
        
    Returns:
        (success, duration): 上传成功与否和用时
    """
    # 临时屏蔽stderr输出 / Suppress stderr output
    original_stderr = sys.stderr
    null_output = open(os.devnull, 'w')
    sys.stderr = null_output
    
    start = time.time()
    driver = None
    success = False
    
    try:
        # 查找最新视频或使用指定视频 / Find latest video or use specified video
        if video_path is None:
            video = find_latest_video(MERGED_FOLDER)
        else:
            # 确保是绝对路径 / Ensure absolute path
            video = os.path.abspath(video_path)
            if not os.path.exists(video):
                raise FileNotFoundError(f"指定的视频文件不存在: {video}")
        
        print(f"正在上传视频到哔哩哔哩: {os.path.basename(video)}")
        
        # 初始化浏览器 / Initialize browser
        driver, _ = init_browser()
        # 执行上传流程 / Execute upload process
        open_upload_page(driver)
        upload_video(driver, video)
        wait_for_upload_complete(driver)
        fill_title(driver)
        click_publish(driver)
        wait_for_publish_success(driver)
        
        success = True
    except FileNotFoundError as e:
        print(f"文件错误: {str(e)}")
    except Exception as e:
        print(f"上传失败: {str(e)}")
        if driver:
            # 截图记录失败状态 / Screenshot to record failure state
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, f"上传失败.png"))
    finally:
        # 关闭浏览器 / Close browser
        if driver:
            driver.quit()
        
        # 恢复stderr / Restore stderr
        sys.stderr = original_stderr
        null_output.close()
        
        # 显示结果 / Show result
        duration = time.time() - start
        if success:
            print(f"上传成功！用时{int(duration)}秒")  # Upload successful! Time used: X seconds
        else:
            print("上传失败，请检查错误信息")  # Upload failed, please check error message
        
        return success, duration
