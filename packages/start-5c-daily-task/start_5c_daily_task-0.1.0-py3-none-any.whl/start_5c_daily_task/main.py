import os
import time
from datetime import datetime
from time import sleep
import pyperclip
import glob
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
from tqdm import tqdm


def create_directory(working_dir):
    os.makedirs(working_dir, exist_ok=True)
    folders = ["CDRTRUE", "CDRAIS", "SUSPENSE", "REPORT_BANK", "REPORT_SUSPENSE"]

    for folder in folders:
        os.makedirs(os.path.join(working_dir, folder), exist_ok=True)


def wait_for_downloads(download_path, timeout=30):
    end_time = time.time() + timeout
    while time.time() < end_time:
        if not glob.glob(os.path.join(download_path, "*.crdownload")):
            return True
        time.sleep(0.5)
    return False


def add_day_overlay(working_dir):
    today = datetime.now().strftime("%Y-%m-%d")
    prefix = f"Screenshot {today}"
    suffix = ".png"

    files = [f for f in os.listdir(".") if f.startswith(prefix) and f.endswith(suffix) and os.path.isfile(f)]

    day_text = (datetime.now() - timedelta(days=1)).strftime("%d")

    for file in tqdm(files, desc=f"Add overlay to images"):
        img = Image.open(file).convert("RGBA")
        draw = ImageDraw.Draw(img)

        font_size = 48
        padding = 12
        bg_color = (0, 0, 0, 180)
        text_color = (255, 255, 255)

        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), day_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        x = (img.width - (text_w + padding * 2)) // 2
        y = 0

        draw.rectangle(
            (x, y, x + text_w + padding * 2, y + text_h + padding * 2 + 10),
            fill=bg_color,
        )
        draw.text(
            (x + padding, y + padding),
            day_text,
            font=font,
            fill=text_color,
        )

        img.save(os.path.join(working_dir, "REPORT_SUSPENSE", f"stamped_{file}"))


def main():
    working_dir = datetime.now().strftime("%Y%m%d")
    create_directory(working_dir)
    download_dir = os.path.abspath(working_dir)

    file1 = os.path.abspath("tj_ccib.crime_behavior_phone (tj_ccib.crime_behavior_phone).xlsx")
    file2 = os.path.abspath("tj_ccib_analyze.rp_telcoinfo_case (tj_ccib_analyze.rp_telcoinfo_case).xlsx")

    if not (os.path.exists(file1) and os.path.exists(file2)):
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 5C files are missing.")
        return

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    prefs = {"download.default_directory": download_dir, "download.prompt_for_download": False, "download.directory_upgrade": True, "profile.default_content_settings.popups": 0, "profile.default_content_setting_values.automatic_downloads": 1, "safebrowsing.enabled": True}
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get("https://policeadmin.com/5c/daily-report")

    driver.execute_script(
        """
            const style = document.createElement('style');
            style.type = 'text/css';
            style.innerHTML = '* { cursor: none !important; }';
            document.head.appendChild(style);
        """
    )

    wait = WebDriverWait(driver, 20)

    wait.until(lambda driver_elm: len(driver_elm.find_elements(By.XPATH, "//input[@type='file']")) >= 2)

    file_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
    file_inputs[0].send_keys(file1)
    file_inputs[1].send_keys(file2)

    copy_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'คัดลอก')]")))
    copy_btn.click()

    text = pyperclip.paste().strip("\r\n")
    with open(os.path.join(working_dir, "daily_report.txt"), "w", encoding="utf-8", newline="") as f:
        f.write(text)

    sleep(0.8)
    # ค้นหา div ที่มีสมาชิกเป็น h6 และ button เท่านั้น
    matched_divs = []
    divs = driver.find_elements(By.TAG_NAME, "div")

    for div in divs:
        children = div.find_elements(By.XPATH, "./*")
        if len(children) == 2 and set(c.tag_name for c in children) == {"h6", "button"}:
            matched_divs.append(div)

    # คลิกปุ่มภายใน div ที่ตรงกับเงื่อนไข
    for div in matched_divs:
        try:
            btn = div.find_element(By.TAG_NAME, "button")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            driver.execute_script("arguments[0].click();", btn)
            sleep(0.8)
        except Exception as e:
            print("Failed to click button in div:", e)
    wait_for_downloads(download_dir, timeout=60)
    driver.quit()
    add_day_overlay(working_dir)


if __name__ == "__main__":
    main()
