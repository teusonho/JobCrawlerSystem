from DrissionPage import Chromium, ChromiumOptions

from ..settings import BROWSER_CONNECT
# BROWSER_CONNECT = 9222

def create_chrome():
    """启动浏览器初始化"""
    if isinstance(BROWSER_CONNECT, str):
        co = ChromiumOptions().set_browser_path(BROWSER_CONNECT)
        browser = Chromium(addr_or_opts=co)
    elif isinstance(BROWSER_CONNECT, int):
        browser = Chromium(BROWSER_CONNECT)  # chrome默认端口为9222
    else:
        raise TypeError("BROWSER_CONNECT参数类型错误")
    return browser

def get_cookies_by_boss(browser):
    """启动页面，获取boss直聘网的访客cookie，若启动的浏览器已保存登录状态，则获取该用户的cookie"""
    tab = browser.new_tab()
    # tab = browser.get_tab(0)
    url = "https://www.zhipin.com/web/geek/jobs?city=100010000&query=python"
    tab.get(url, retry=5, interval=1, timeout=10)
    error_ele = tab.ele("@text()=异常访问行为")
    if error_ele:
        return None
    job_list_ele = tab.ele("@@tag()=ul@@class=rec-job-list")
    job_list_ele.wait.displayed(timeout=10)
    cookies = tab.cookies().as_dict()
    tab.close()
    return cookies


if __name__ == "__main__":
    brower = create_chrome()
    r = get_cookies_by_boss(brower)
    print(r)
