import os.path
import threading
import ctypes
import time

import requests
from bs4 import BeautifulSoup as bs
from urllib.parse import urlsplit, parse_qs, urlparse
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, url, folder_name):
        super(StoppableThread, self).__init__()
        self.url = url
        self.folder_name = folder_name
        self._stop_event = threading.Event()

    def run(self) -> None:
        self.download_f()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def get_id(self):

        # returns id of the respective thread
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id_, thread in threading._active.items():
            if thread is self:
                return id_

    def raise_exception(self):
        raise Exception(f'Forcefully closed. {self.get_id()}. Name: {self.name}')

    def download_f(self):
        url = self.url
        folder_name = self.folder_name
        print(f"URL: {url}")
        print(f"Keyword: {folder_name}")
        try:
            img_data = requests.get(url, allow_redirects=True, timeout=(5, 15))
        except Exception:
            try:
                img_data = requests.get(url, allow_redirects=True, verify=False, timeout=(5, 15))
            except Exception:
                return
        try:
            content_type = img_data.headers["content-type"].split("/")
        except Exception:
            return
        if content_type[0] == 'image':
            ext = content_type[1]
        else:
            return
        extension = ['.jpg', '.jpeg', '.png', 'gif']
        a = urlparse(url)
        print(a.path)
        file_name = os.path.basename(a.path)
        print("FileName:", file_name)
        if any(word in url.lower() for word in extension):
            print("Have Extension")
        else:
            file_name = f'{file_name}.{ext}'

        if folder_name not in os.listdir(os.path.abspath(f'./images')):
            os.mkdir(os.path.abspath(f'./images/{folder_name}'))

        while file_name in os.listdir(os.path.abspath(f'./images/{folder_name}')):
            file_name = file_name.split('.')
            file_name = file_name[0] + '1.' + file_name[-1]
        print(file_name)

        tried = 3
        while tried > 0:
            try:
                img_data = img_data.content
                with open(os.path.abspath(f'./images/{folder_name}/{file_name}'), 'wb') as handler:
                    handler.write(img_data)
                    handler.close()
                break
            except Exception as e:
                print(e)
                return


def main():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    driver = uc.Chrome(driver_executable_path=ChromeDriverManager().install(), options=options)

    keywords = []
    with open(os.path.abspath('./keywords.txt'), 'r', encoding='utf-8') as f:
        keyword_lines = [line.replace('\n', '') for line in f.readlines()]
        for line in keyword_lines:
            keywords.extend([keyword.strip() for keyword in line.split(',')])

    print(len(keywords))
    print(keywords)
    for keyword in keywords:
        driver.get('https://images.search.yahoo.com/')
        search_field = driver.find_element(By.CSS_SELECTOR, 'input[name="p"]')
        search_field.send_keys(keyword)

        search_btn = driver.find_element(By.CSS_SELECTOR, 'input[value="Search"]')
        search_btn.click()
        time.sleep(2)

        wait = WebDriverWait(driver, 10)
        i, page_to_download = 0, 10
        while i < page_to_download:
            print(f"Browsing {i+1}{'st' if i+1==1 else 'nd' if i+1==2 else 'rd' if i+1 == 3 else 'th' } page.")
            try:
                wait.until(expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, 'button[name="more-res"]')))
                driver.find_element(By.CSS_SELECTOR, 'button[name="more-res"]').click()
                i += 1
                time.sleep(5)
            except Exception:
                break

        time.sleep(5)
        res = driver.page_source

        soup = bs(res, 'lxml')

        ul = soup.select('ul#sres>li>a')
        links = []
        if ul is not None and len(ul):
            for a in ul:
                links.append('https://images.search.yahoo.com'+a['href'])
        print(len(links))

        image_urls = []
        for idx, link in enumerate(links):
            url = parse_qs(urlsplit(link).query)
            url = 'https://'+url.get('imgurl')[0]
            image_urls.append(url)

        # get_file_name(image_urls)
        # with open('links.txt', 'a', encoding="utf-8") as file:
        #     for link in image_urls:
        #         file.write(link + "\n")
        # exit()
        # image_urls = image_urls[-126:]
        threads_ori = []
        thread_per_run = 100

        if len(image_urls) < thread_per_run:
            range_to_run = len(image_urls)
        else:
            range_to_run = thread_per_run
        i = 0
        for j in range(i, i + range_to_run):
            print(image_urls[j])
            thread = StoppableThread(image_urls[j], keyword)
            thread.start()
            threads_ori.append(thread)

        i = thread_per_run
        while i < len(image_urls):
            for thread in threads_ori:
                if not thread.is_alive():
                    print(
                        '\n####################################################\n#######       Starting Thread For    #######\n#######  ' + thread.name + '    #######\n####################################################\n')
                    threads_ori.remove(thread)
                    try:
                        thread = StoppableThread(image_urls[i], keyword)
                        thread.start()
                        threads_ori.append(thread)
                    except IndexError:
                        print("No more threads!")
                        break
                    i += 1

                else:
                    print(
                        '\n####################################################\n#######     Waiting For       #######\n#######    ' + thread.name + '    #######\n####################################################\n')
            time.sleep(13)

        if any(thread.is_alive() for thread in threads_ori):
            for thread in threads_ori:
                if not thread.is_alive():
                    threads_ori.remove(thread)
                else:
                    thread.join()


if __name__ == '__main__':
    main()
