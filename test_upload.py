#!/usr/bin/env python3
import os
import time
import glob
import random

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

# ==== 配置 ====

# 更新路径配置，确保使用绝对路径

# 获取当前脚本所在的绝对路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 配置相对路径
CHROME_PATH = os.environ.get("CHROME_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe")
CHROMEDRIVER_PATH = os.path.join(SCRIPT_DIR, r"tools\chromedriver-win64\chromedriver.exe")
MERGED_FOLDER = os.path.join(SCRIPT_DIR, "merged_videos")
PROFILE_PATH = os.path.join(SCRIPT_DIR, "selenium_profile")
SCREENSHOT_DIR = os.path.join(SCRIPT_DIR, "screenshots")
SERIAL_NUMBER_FILE = os.path.join(SCRIPT_DIR, "serial_number.txt")

# 确保目录存在
os.makedirs(PROFILE_PATH, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(MERGED_FOLDER, exist_ok=True)

# 修改标题前缀
TITLE_PREFIX = "海外离大谱#"

def load_serial_number():
    return int(open(SERIAL_NUMBER_FILE).read()) if os.path.exists(SERIAL_NUMBER_FILE) else 1

def save_serial_number(num):
    with open(SERIAL_NUMBER_FILE, "w") as f:
        f.write(str(num))

def find_latest_video(folder):
    """查找最新的视频文件并返回其绝对路径"""
    # 确保使用绝对路径
    abs_folder = os.path.abspath(folder)
    videos = glob.glob(os.path.join(abs_folder, "*.mp4"))
    if not videos:
        raise FileNotFoundError(f"在 {abs_folder} 文件夹中没有找到视频")
    
    latest_video = max(videos, key=os.path.getmtime)
    print(f"找到视频文件: {latest_video}")
    return latest_video  # 已经是绝对路径

def init_browser():
    """初始化Chrome浏览器"""
    options = Options()
    # 添加新配置以抑制WebGL和GPU相关的控制台输出
    options.add_argument("--log-level=3")  # 只显示致命错误
    options.add_argument("--silent")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    # 添加额外的WebGL选项，避免警告
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-webgl")
    options.add_argument("--disable-webgl2")
    
    print(f"Chrome路径: {CHROME_PATH}")
    print(f"ChromeDriver路径: {CHROMEDRIVER_PATH}")
    
    # 确保存在配置目录
    os.makedirs(PROFILE_PATH, exist_ok=True)
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    options.binary_location = CHROME_PATH  # 明确指定Chrome可执行文件路径
    options.add_argument(f"--user-data-dir={os.path.abspath(PROFILE_PATH)}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--window-size=960,1080")
    options.add_argument("--window-position=960,0")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")  # 添加这个参数解决一些权限问题
    options.add_argument("--disable-dev-shm-usage")  # 解决内存问题
    
    # 检查ChromeDriver是否存在
    if not os.path.exists(CHROMEDRIVER_PATH):
        raise FileNotFoundError(f"ChromeDriver未找到: {CHROMEDRIVER_PATH}")
    
    service = Service(executable_path=CHROMEDRIVER_PATH)
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
        
        # 完全抑制Selenium日志输出
        import logging
        selenium_logger = logging.getLogger('selenium')
        selenium_logger.setLevel(logging.CRITICAL)  # 只显示严重错误
        
        # 重定向Chrome的stderr到/dev/null
        os.environ['CHROME_LOG_FILE'] = os.devnull
        
        return driver, WebDriverWait(driver, 30)
    except Exception as e:
        print(f"浏览器初始化错误: {str(e)}")
        raise


def is_logged_in(driver):
    """检查是否已经登录B站
    
    查找特定的已登录元素(如用户头像)或登录按钮来判断
    """
    try:
        # 尝试查找登录相关元素
        login_elements = driver.find_elements(By.XPATH, 
            '//div[contains(@class, "login-btn") or contains(text(), "登录") or contains(text(), "扫码")]')
        
        # 尝试查找已登录状态的元素(头像等)
        avatar_elements = driver.find_elements(By.XPATH, 
            '//img[contains(@class, "avatar") or contains(@class, "user-avatar")]')
        
        # 如果没有登录按钮但有头像，说明已登录
        if not login_elements and avatar_elements:
            return True
        
        # 如果检测到明确的投稿界面元素，也视为已登录
        upload_elements = driver.find_elements(By.XPATH, 
            '//div[contains(@class, "upload-btn") or contains(text(), "投稿") or contains(text(), "上传")]')
        if upload_elements:
            return True
            
        # 如果页面标题包含"创作中心"或"投稿"，也认为已登录
        if "创作中心" in driver.title or "投稿" in driver.title:
            return True
            
        return False
    except Exception as e:
        print(f"检查登录状态时出错: {e}")
        # 出错时保守处理，返回未登录
        return False


def open_upload_page(driver):
    """打开B站投稿页面，根据需要等待用户登录"""
    driver.get("https://member.bilibili.com/platform/upload/video/")
    print("打开投稿页面中...")
    time.sleep(5)  # 给页面更多加载时间
    
    # 缩放页面以便完整显示
    driver.execute_script("document.body.style.zoom='90%'")
    
    # 检查是否需要登录
    if not is_logged_in(driver):
        print("\n检测到需要登录B站")
        print("请在浏览器窗口完成扫码登录")
        
        # 等待用户手动完成登录
        input("完成登录后，按回车键继续...")
        
        # 额外等待一段时间，确保登录完全生效
        time.sleep(5)
        print("继续上传流程...")
    else:
        print("检测到已经登录B站，继续上传流程...")


def upload_video(driver, video_path):
    """上传视频到B站"""
    print("等待上传入口加载...")
    
    # 确保使用绝对路径
    abs_video_path = os.path.abspath(video_path)
    print(f"使用绝对文件路径: {abs_video_path}")

    # 等待上传区域出现（用 class 更稳）
    try:
        upload_section = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "bcc-upload"))
        )
        
        # 查找文件上传 input
        upload_input = upload_section.find_element(By.XPATH, './/input[@type="file"]')
        
        # 判断 input 是否可见（有些情况它被隐藏了）
        driver.execute_script("arguments[0].style.display = 'block';", upload_input)
        
        # 使用绝对路径
        upload_input.send_keys(abs_video_path)
        print("已选择文件开始上传")
        
    except Exception as e:
        print(f"选择上传文件失败: {e}")
        # 尝试直接点击上传按钮
        try:
            # 寻找并点击上传按钮
            upload_button = driver.find_element(By.XPATH, 
                '//div[contains(@class, "upload-btn") or contains(text(), "上传")]')
            upload_button.click()
            time.sleep(1)
            
            # 在文件对话框打开的情况下，使用pyautogui或其他方式输入文件路径
            print("已点击上传按钮，请手动选择文件")
            input("完成文件选择后，按回车键继续...")
        except:
            raise  # 重新抛出原始异常



def wait_for_upload_complete(driver):
    wait = WebDriverWait(driver, 600)
    print("🕐 等待『上传完成』提示...")

    wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(text(), "上传完成")]')))
    print("✅ 检测到『上传完成』")

    print("🕐 等待上传进度条消失...")
    wait.until_not(EC.presence_of_element_located((By.CSS_SELECTOR, ".el-progress__text, .uploading, .progress")))
    print("✅ 上传进度条已消失")

    time.sleep(3)  # 再等待UI反应几秒


def fill_title(driver):
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.XPATH, '//input[@placeholder="请输入稿件标题"]'))
    )
    serial = load_serial_number()
    title = f"{TITLE_PREFIX}{serial}"
    
    # 记录上传的视频信息到日志文件
    log_dir = "upload_logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "upload_history.log")
    
    # 获取当前时间和上传的视频信息
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    video_info = f"{now} | {title} | {os.path.basename(find_latest_video(MERGED_FOLDER))}"
    
    # 写入日志
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(video_info + "\n")
    
    # 更新UI和保存序号
    input_box = driver.find_element(By.XPATH, '//input[@placeholder="请输入稿件标题"]')
    input_box.clear()
    input_box.send_keys(title)
    save_serial_number(serial + 1)
    print(f"✅ 已填写标题：{title}")
    print(f"✅ 已记录上传信息到日志")


def click_publish(driver):
    print("🕐 尝试点击『立即投稿』按钮...")
    now = time.strftime("%Y%m%d_%H%M%S")
    driver.save_screenshot(os.path.join(SCREENSHOT_DIR, f"点击前_{now}.png"))

    button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, '//span[contains(text(), "立即投稿")]'))
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
    ActionChains(driver).move_to_element(button).pause(0.5).click().perform()
    print("✅ 成功点击『立即投稿』")


def wait_for_publish_success(driver):
    try:
        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.XPATH, '//div[contains(text(), "稿件投递成功")]'))
        )
        now = time.strftime("%Y%m%d_%H%M%S")
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, f"投稿成功_{now}.png"))
        print("🎉 投稿成功")
    except TimeoutException:
        print("⚠️ 未检测到『稿件投递成功』提示")


def format_duration(seconds):
    """将秒数格式化为易读的时间格式
    
    如果超过1分钟，显示为"x分y秒"，否则显示为"x秒"
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    
    if minutes > 0:
        return f"{minutes}分{secs}秒"
    else:
        return f"{secs}秒"

def upload_latest_merged_video():
    """上传最新合并的视频到B站"""
    start = time.time()
    driver = None
    success = False
    duration = 0
    
    try:
        print("\n=== 开始上传视频到B站 ===")
        video = find_latest_video(MERGED_FOLDER)
        print(f"找到视频: {os.path.basename(video)}")
        
        # 初始化浏览器
        driver, _ = init_browser()
        
        # 忽略浏览器输出，只显示我们的进度消息
        print("1. 打开B站上传页面...")
        open_upload_page(driver)
        
        print("2. 选择并上传视频文件...")
        upload_video(driver, video)
        
        print("3. 等待上传完成...")
        wait_for_upload_complete(driver)
        
        print("4. 填写标题信息...")
        fill_title(driver)
        
        print("5. 提交视频...")
        click_publish(driver)
        
        print("6. 等待投稿结果...")
        wait_for_publish_success(driver)
        
        print("✓ 视频上传成功！")
        success = True
        
    except FileNotFoundError as e:
        print(f"文件错误: {str(e)}")
    except Exception as e:
        print(f"上传过程出现错误: {str(e)}")
        if driver:
            now = time.strftime("%Y%m%d_%H%M%S")
            try:
                driver.save_screenshot(os.path.join(SCREENSHOT_DIR, f"上传失败_{now}.png"))
            except:
                pass
    finally:
        # 移除交互提示，直接关闭浏览器
        if driver:
            try:
                driver.quit()
                print("浏览器已关闭")
            except Exception as e:
                print(f"关闭浏览器时出错: {e}")
        
        duration = time.time() - start
        return success, duration  # 返回成功状态和用时


if __name__ == "__main__":
    upload_latest_merged_video()