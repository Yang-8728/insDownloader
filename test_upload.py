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

# 修改Chrome路径配置，使用相对路径并添加错误处理
CHROME_PATH = os.environ.get("CHROME_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe")
CHROMEDRIVER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"tools\chromedriver-win64\chromedriver.exe")
MERGED_FOLDER = "merged_videos"
PROFILE_PATH = "selenium_profile"
TITLE_PREFIX = "测试投稿#"
SCREENSHOT_DIR = "screenshots"
SERIAL_NUMBER_FILE = "serial_number.txt"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def load_serial_number():
    return int(open(SERIAL_NUMBER_FILE).read()) if os.path.exists(SERIAL_NUMBER_FILE) else 1

def save_serial_number(num):
    with open(SERIAL_NUMBER_FILE, "w") as f:
        f.write(str(num))

def find_latest_video(folder):
    videos = glob.glob(os.path.join(folder, "*.mp4"))
    if not videos:
        raise FileNotFoundError("❌ merged 文件夹中没有找到视频")
    return max(videos, key=os.path.getmtime)


def init_browser():
    """初始化Chrome浏览器"""
    print(f"Chrome路径: {CHROME_PATH}")
    print(f"ChromeDriver路径: {CHROMEDRIVER_PATH}")
    
    # 确保存在配置目录
    os.makedirs(PROFILE_PATH, exist_ok=True)
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    options = Options()
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
        return driver, WebDriverWait(driver, 30)
    except Exception as e:
        print(f"浏览器初始化错误: {str(e)}")
        raise


def open_upload_page(driver):
    """打开B站投稿页面，等待用户手动完成登录"""
    driver.get("https://member.bilibili.com/platform/upload/video/")
    print("打开投稿页面中...")
    time.sleep(3)
    driver.execute_script("document.body.style.zoom='90%'")
    
    # 检查是否需要登录
    try:
        login_elements = driver.find_elements(By.XPATH, '//*[contains(text(), "扫码") or contains(text(), "登录")]')
        if login_elements:
            print("\n检测到需要登录B站")
            print("请在浏览器窗口完成扫码登录")
            
            # 等待用户手动完成登录
            input("完成登录后，按回车键继续...")
            
            # 额外等待一段时间，确保登录完全生效
            time.sleep(5)
            print("继续上传流程...")
    except Exception as e:
        print(f"检查登录状态时出错: {e}")
        # 继续执行，可能已经登录


def upload_video(driver, video_path):
    print("🕐 等待上传入口加载...")

    # 等待上传区域出现（用 class 更稳）
    upload_section = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "bcc-upload"))
    )

    # 查找文件上传 input
    upload_input = upload_section.find_element(By.XPATH, './/input[@type="file"]')

    # 判断 input 是否可见（有些情况它被隐藏了）
    driver.execute_script("arguments[0].style.display = 'block';", upload_input)

    upload_input.send_keys(video_path)
    print("✅ 已选择文件开始上传")



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
    input_box = driver.find_element(By.XPATH, '//input[@placeholder="请输入稿件标题"]')
    input_box.clear()
    input_box.send_keys(title)
    save_serial_number(serial + 1)
    print(f"✅ 已填写标题：{title}")


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


def upload_latest_merged_video():
    """上传最新合并的视频到B站"""
    start = time.time()
    driver = None
    success = False
    
    try:
        # 确保目录存在
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        
        video = find_latest_video(MERGED_FOLDER)
        print(f"找到视频: {video}")
        
        # 初始化浏览器
        driver, _ = init_browser()
        
        # 打开投稿页面并处理登录
        open_upload_page(driver)
        
        # 上传视频
        upload_video(driver, video)
        wait_for_upload_complete(driver)
        fill_title(driver)
        click_publish(driver)
        wait_for_publish_success(driver)
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
        if driver:
            # 添加选项让用户决定何时关闭浏览器
            try:
                close_browser = input("\n上传过程已完成。是否关闭浏览器？(y/n): ").lower().strip() == 'y'
                if close_browser:
                    driver.quit()
                    print("浏览器已关闭")
                else:
                    print("浏览器保持打开状态，请在完成后手动关闭")
                    # 不关闭浏览器，但返回结果
            except:
                # 如果出错，尝试关闭浏览器
                try:
                    driver.quit()
                except:
                    pass
        
        duration = time.time() - start
        print(f"总用时: {duration:.2f} 秒")
        return success


if __name__ == "__main__":
    upload_latest_merged_video()
