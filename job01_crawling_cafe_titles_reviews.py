#job01_crawling_cafe_title
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
import datetime
from selenium import webdriver as wb  # 동적 사이트 수집
import time
from selenium.webdriver.common.action_chains import ActionChains

# webdriver사용 세팅
options = ChromeOptions()
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
options.add_argument('user_agent=' + user_agent)
options.add_argument('lang=ko_KR')

#크롤링할 지역과 url
local_names = ['성수', '신사', '잠실', '청담']
local_url = ['https://map.naver.com/p/search/%EC%84%B1%EC%88%98%20%EC%B9%B4%ED%8E%98?c=14.00,0,0,0,dh',
                  'https://map.naver.com/p/search/%EC%8B%A0%EC%82%AC%20%EC%B9%B4%ED%8E%98?searchType=place&c=15.00,0,0,0,dh',
                  'https://map.naver.com/p/search/%EC%9E%A0%EC%8B%A4%20%EC%B9%B4%ED%8E%98?searchType=place&c=14.00,0,0,0,dh',
                  'https://map.naver.com/p/search/%EC%B2%AD%EB%8B%B4%20%EC%B9%B4%ED%8E%98?searchType=place&c=15.00,0,0,0,dh']
try:
    for l in range(4): #원래는 4
        service = ChromeService(executable_path=ChromeDriverManager().install())
        driver = wb.Chrome(service=service, options=options)

        local_crawled_num = 0
        local_name = local_names[l]
        driver.get(local_url[l])
        driver.implicitly_wait(10)
        seng_su_page_xpath = '//*[@id="app-root"]/div/div[4]/div[2]/a[{}]'
        page_xpath = '//*[@id="app-root"]/div/div[3]/div[2]/a[{}]'
        cafe_titles = []
        reviews = []
        # 1, 2페이지 누르기
        for i in range(2, 4):
            previous_num = 50

            driver.switch_to.default_content() #프레임 초기화
            driver.switch_to.frame('searchIframe') #프레임 변경

            try:
                if i!=2:
                    driver.find_element(By.XPATH, page_xpath.format(i)).click()
                    driver.implicitly_wait(5)
                    time.sleep(1)

            except:
                print('페이지 클릭 오류')


            # 끝까지 스크롤
            scroll_div = driver.find_element(By.XPATH,'//*[@id="_pcmap_list_scroll_container"]')
            for j in range(6):
                driver.execute_script("arguments[0].scrollBy(0, 2000)", scroll_div) # 스크롤 하기
                driver.implicitly_wait(5)
                time.sleep(1)

            # 타이틀 담기
            re_title = re.compile('[^가-힣|a-z|A-Z|0-9]')
            title_tags = driver.find_elements(By.CLASS_NAME, 'TYaxT')

            for title_tag in title_tags:
                cafe_titles.append(re_title.sub(' ', title_tag.text))
            print('타이틀 이름들 : ', cafe_titles)
            print('타이틀 개수 : ', len(cafe_titles))

            # 가게 클릭
            store_tags = driver.find_elements(By.CLASS_NAME, 'TYaxT')
            for j in range(50):
                try:
                    store_tags[j].click()
                    driver.implicitly_wait(5)
                    time.sleep(1.5)
                except:
                    print('가게클릭 오류')

                #리뷰긁을 수 있는 프레임으로 변경
                driver.switch_to.default_content()
                driver.switch_to.frame('entryIframe')

                #리뷰메뉴 클릭
                try:
                    btn_lists = driver.find_elements(By.CLASS_NAME, 'veBoZ')
                    for btn_list in btn_lists:
                        if btn_list.text == '리뷰':
                             btn_list.click()
                    driver.implicitly_wait(5)
                    time.sleep(1)
                except:
                    print('리뷰메뉴 클릭 오류')

                review = ''
                count = 0
                #리뷰 클릭후 전체리뷰 긁어오기
                for k in range(100):
                    try:
                        review_objects = driver.find_elements(By.CLASS_NAME, 'xHaT3')
                        review_objects[k].click()
                        driver.implicitly_wait(5)
                        time.sleep(1)
                        review_object = review_objects[k].text
                        review = review + '/' + review_object
                    except:
                        count += 1
                        k -= 1
                        if count > 3:
                            print('리뷰가 더 이상 없습니다.')
                            break
                    # 더보기 버튼 클릭
                    if not (k+1) % 10:
                        try:
                            more_objects = driver.find_elements(By.CLASS_NAME, 'fvwqf')
                            more_objects[0].click()
                            driver.implicitly_wait(5)
                            time.sleep(1)
                        except:
                            print('더보기 버튼이 없습니다.')

                reviews.append(review)
                print('리뷰 수집한 가게 개수 : ', len(reviews))

                driver.switch_to.default_content()  # 프레임 초기화
                driver.switch_to.frame('searchIframe')  # 프레임 변경

                if (j+1) % 10 == 0:
                    local_crawled_num += 10
                    current_num = j+1
                    print('debug')
                    try:
                        df = pd.DataFrame({'cafe_titles':cafe_titles[previous_num:current_num], 'reviews':reviews})
                        df.to_csv('./crawling_data/{}_reviews{}.csv'.format(local_name, local_crawled_num), index=False)
                    except:
                        print('저장 오류')
                    previous_num = j+1
                    reviews = []

                if (j+1) % 50 == 0:
                    cafe_titles = []
        driver.close()
        driver.quit()
except Exception as e:
    print('무언가 오류가 났지만 걍 넘어가.', '\n', e)