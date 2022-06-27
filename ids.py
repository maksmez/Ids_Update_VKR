import configparser
import os
from time import sleep
from selenium import webdriver
import warnings
from selenium.webdriver.common.keys import Keys
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
import time
import datetime
from yattag import Doc
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from cryptography.fernet import Fernet
import base64
import logging, logging.config

logging.config.fileConfig("config_ids.ini")
logger = logging.getLogger('IDS_Update')

password = ''
cipher = ''
pwd = os.getcwd()
folder_ids = pwd + '/ids'
Base = declarative_base()
engine = create_engine('sqlite:///' + pwd + '/IDS_db.db?check_same_thread=False')  # путь до БД
session_factory = sessionmaker(bind=engine)
session = scoped_session(session_factory)

config = configparser.ConfigParser(interpolation=None)
if not os.path.exists('config_ids.ini'):
    config["config"] = {
        "address_ids": "",
        "username_ids_update": "",
        "password_ids_update": "",
        "username_ids": "",
        "path_template": "",
        "host_server": "",
        "email_to": ""
    }
    with open("config_ids.ini", "w") as file_object:
        config.write(file_object)
    logger.error('Внимание! Нужно заполнить конфигурационный файл!')
    exit()
config.read("config_ids.ini", encoding="utf-8")
for value in config['config'].items():
    if value[1] == '':
        logger.error('Параметр '+value[0]+' не задан!')
        input()
        exit()
if not os.path.exists('ids'):
    os.mkdir('ids')
if not os.path.exists('report'):
    os.mkdir('report')
class Version_ids(Base):
    __tablename__ = 'Version'
    Id = Column(Integer, primary_key=True)
    Ip = Column(String, nullable=False)
    Ids_version = Column(String, nullable=False, default='')
    Time_license = Column(Integer, nullable=False)
    Name_base = Column(String, nullable=False, default='')

    def get_all():  # список всех ids
        p = session.query(Version_ids).all()
        version = []
        for o in p:
            version.append(o)
        return version

warnings.filterwarnings("ignore", category=DeprecationWarning)
profile = webdriver.FirefoxProfile()
profile.set_preference('browser.download.folderList', 2)
profile.set_preference('browser.download.manager.showWhenStarting', False)
profile.set_preference('browser.download.dir', folder_ids)
profile.set_preference('browser.download.useDownloadDir', True)
profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/octet-stream')
profile.set_preference('general.useragent.override', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36')

options = webdriver.FirefoxOptions()
options.headless = True
driver = webdriver.Firefox(firefox_profile=profile, options=options, executable_path='./geckodriver.exe')

def admin_report(logs):
    try:
        sleep(2)
        template_html = config['config']['path_template']
        with open(template_html, "rb") as file:
            data = file.read()
        template_html_copy = data.decode()
        doc, tag, text = Doc().tagtext()
        logger.info('Создаю отчет')
        with tag('h1'):
            text('Отчет по обновлению баз правил IDS от: ', str(datetime.datetime.now().strftime("%d.%m.%Y %H:%M")))
        time_html = doc.getvalue()
        if type(logs) != list:
            doc, tag, text = Doc().tagtext()
            with tag('h2', style='text-align: center; font-size: 1.8em; background-color: #009fff; padding: 10px; border-radius: 10px; width: 100%;'):
                text(logs)
            doc.stag('br')
            report_html = doc.getvalue()
        else:
            doc, tag, text = Doc().tagtext()
            with tag('h2', style='text-align: center; font-size: 1.8em; background-color: #009fff; padding: 10px; border-radius: 10px; width: 100%;'):
                text('Результаты обновления')
            with tag('table', style='width: 100%; border-right: 3px solid #009fff; border-left: 3px solid #009fff; border-top: 3px solid #009fff; border-collapse: collapse;'):
                with tag('tr', style='background-color: #009fff; text-align: center; font-size: 1.5em;'):
                    with tag('th', style='width: 8%;'):
                        text('Id')
                    with tag('th', style='width: 10%;'):
                        text('Ip адрес')
                    with tag('th', style='width: 20%;'):
                        text('Название базы')
                    with tag('th', style='width: 10%;'):
                        text('Версия')
                    with tag('th', style='width: 20%;'):
                        text('Срок лицензии')
                    with tag('th', style='width: auto;'):
                        text('Статус обновления')
                for i in logs:
                    with tag('tr', style='text-align: center; font-size: 1.3em; border: 1px solid #009fff;'):
                        style_background = ''
                        if logs.index(i) % 2 != 0:
                            style_background = 'background-color: #bcbcbc;'
                        style_error = ''
                        if i[5] != 'Не требуется обновление' and i[5] != 'Обновлено':
                            style_error = 'color: red;'
                        if i[5] == 'Обновлено':
                            style_error = 'color: green;'
                        with tag('td', style='width: 8%; padding: 3px; border-bottom: 3px solid #009fff; '+style_background+''):
                            text(i[0])
                        with tag('td', style='width: 10%; padding: 3px; border-bottom: 3px solid #009fff; '+style_background+''):
                            text(i[1])
                        with tag('td', style='width: 20%; padding: 3px; border-bottom: 3px solid #009fff; '+style_background+''):
                            text(i[2])
                        with tag('td', style='width: 10%; padding: 3px; border-bottom: 3px solid #009fff; '+style_background+''):
                            text(i[3])
                        with tag('td', style='width: 20%; padding: 3px; border-bottom: 3px solid #009fff; '+style_background+''):
                            text(datetime.datetime.utcfromtimestamp(i[4]).strftime('%d-%m-%Y'))
                        with tag('td', style='width: auto; padding: 3px; border-bottom: 3px solid #009fff; '+style_background+' '+style_error+''):
                            text(i[5])
            report_html = doc.getvalue()
            update_list = []
            for ids in logs:
                if time.time() + 2592000 > ids[4]:
                    update_list.append(ids)
            license_html = ''
            if update_list:
                doc, tag, text = Doc().tagtext()
                with tag('h2',style='text-align: center; font-size: 1.8em; background-color: #009fff; padding: 10px; border-radius: 10px; width: 100%;'):
                    text('Требуется обновление лицензии')
                with tag('table', style='width: 100%; border-right: 3px solid #009fff; border-left: 3px solid #009fff; border-top: 3px solid #009fff; border-collapse: collapse;'):
                    with tag('tr', style='background-color: #009fff; text-align: center; font-size: 1.5em;'):
                        with tag('th', style='width: 8%;'):
                            text('Id')
                        with tag('th', style='width: 10%;'):
                            text('Ip адрес')
                        with tag('th', style='width: 20%;'):
                            text('Название базы')
                        with tag('th', style='width: 20%;'):
                            text('Срок лицензии')
                        with tag('th', style='width: 20%;'):
                            text('Осталось дней')
                    for i in update_list:
                        with tag('tr', style='text-align: center; font-size: 1.3em; border: 1px solid #009fff;'):
                            with tag('td', style='width: 8%; padding: 3px; border-bottom: 3px solid #009fff;'):
                                text(i[0])
                            with tag('td', style='width: 8%; padding: 3px; border-bottom: 3px solid #009fff;'):
                                text(i[1])
                            with tag('td', style='width: 8%; padding: 3px; border-bottom: 3px solid #009fff;'):
                                text(i[2])
                            with tag('td', style='width: 8%; padding: 3px; border-bottom: 3px solid #009fff;'):
                                text(datetime.datetime.utcfromtimestamp(i[4]).strftime('%d-%m-%Y'))
                            with tag('td', style='width: 8%; padding: 3px; border-bottom: 3px solid #009fff;'):
                                text((datetime.datetime.utcfromtimestamp(i[4]) - datetime.datetime.utcfromtimestamp(time.time())).days)
                license_html = doc.getvalue()
        template_html_copy = template_html_copy.replace("[report_html]", report_html)
        template_html_copy = template_html_copy.replace("[time_html]", time_html)
        template_html_copy = template_html_copy.replace("[license_html]", license_html)
        logger.info('Отчет создан')
        f = open('report_ids.html', 'w', encoding="utf-8")
        f.write(template_html_copy)
        f.close()
    except Exception as e:
        logger.error('Произошла ошибка при составлении отчета ===== ' + str(e))
    try:
        logger.info('Отправляю отчет')
        HOST = config['config']['host_server']
        mail = MIMEMultipart("alternative")
        server = smtplib.SMTP(HOST)
        mail["Subject"] = 'Отчет по обновлению баз правил IDS'
        mail["From"] = 'python_ids@update.com'
        mail["To"] = config['config']['email_to']
        template = MIMEText(template_html_copy, "html")
        mail.attach(template)
        server.sendmail(mail["From"], mail["To"], mail.as_string())
        server.quit()
        logger.info('Отчет отправлен')
    except Exception as e:
        logger.error('Ошибка при отправке письма отчета ===== ' + str(e))
    
def check_password():
    global password
    global cipher
    if password == '':
        logger.info('Запрашиваю пароль')
        text = input('Введите пароль\n').encode()
        key = base64.b64encode(bytes(Fernet.generate_key().decode(), 'utf-8'))
        cipher = Fernet(base64.b64decode(key))
        password = cipher.encrypt(text)
        logger.info('Пароль сохранен')

def start():
    try:
        logger.info('Старт работы')
        global password
        global cipher
        check_password()
        logs = ''
        driver.implicitly_wait(10)
        for f in os.listdir(folder_ids):  #удаляем все файлы из папки
            os.remove(os.path.join(folder_ids,f))
        try:
            response = requests.get(config['config']['address_ids'])
            if response.status_code != 200:
                logs = 'Сайт с обновлениями недоступен. Код: ' + str(response.status_code)
                logger.critical('Сайт с обновлениями недоступен. Код: ' + str(response.status_code))
                admin_report(logs)
                exit()
        except Exception as e:
            logs = 'Сайт с обновлениями недоступен ' + str(e)
            logger.critical('Сайт с обновлениями недоступен ' + str(e))
            admin_report(logs)
            exit()
        driver.get(config['config']['address_ids'])
        driver.find_element_by_id('username').send_keys(config['config']['username_ids_update'])
        driver.find_element_by_id('password').send_keys(config['config']['password_ids_update'])
        driver.find_element_by_xpath("//div[contains(text(), 'Войти')]").click()
        driver.find_element_by_xpath("//div[contains(text(), 'Войти')]").click()
        driver.find_element_by_xpath("//button[@class = 'updateids-button button-light button-small    updateids-menubutton menu-closed']").click()
        driver.find_element_by_xpath("//button[@class = 'updateids-button button-light button-small    updateids-menubutton menu-closed']").click()
        logger.info('Авторизовался на сайте с обновлениями')
        version = session.query(Version_ids).first().Ids_version
        driver.find_element_by_xpath("//p[contains(text(), '"+str(version)+"')]").click()
        sleep(3)
        driver.find_element_by_class_name('updateids-update-link').click()  # скачивает самый первый файл из таблицы
        logger.info('Скачал файл с обновлениями')
        sleep(3)
        files = os.listdir(os.path.abspath(pwd+'/ids'))
        logs = []
        count_iter = -1
        for ids in Version_ids.get_all():
            count_iter = count_iter + 1
            response = requests.get('http://' + str(ids.Ip))
            if response.status_code != 200:
                logs.append([ids.Id, ids.Ip, ids.Name_base, ids.Ids_version, ids.Time_license, 'IDS недоступен. Код: '+str(response.status_code)+''])
                logger.warning('IDS недоступен. Код: '+str(response.status_code)+'')
                continue
            driver.get('http://' + ids.Ip)
            count_auth = 0
            logger.info('Подключаюсь к '++ids.Ip++'')
            while 1:
                if driver.find_element_by_id('textfield-1185-inputEl').is_displayed():
                    driver.find_element_by_id('textfield-1185-inputEl').send_keys(config['config']['username_ids'])
                    driver.find_element_by_id('textfield-1187-inputEl').send_keys(cipher.decrypt(password).decode())
                    sleep(1)
                    driver.find_element_by_id('button-1190-btnIconEl').click()
                    sleep(3)
                    count_auth = count_auth + 1
                else:
                    break
            if count_auth == 3:
                logs.append([ids.Id, ids.Ip, ids.Name_base, ids.Ids_version, ids.Time_license, 'Не смог авторизоваться'])
                logger.warning('Слишком много попыток авторизации. Пропуск')
                continue
            driver.refresh()
            logger.info('Авторизовался')
            sleep(5)
            date_lic = driver.find_element_by_xpath("//span[starts-with(text(), 'Расширенная лицензия')]").text
            time_lic = int(time.mktime(datetime.datetime.strptime(date_lic[-10::], "%d.%m.%Y").timetuple()))
            base_ids = session.query(Version_ids).filter(Version_ids.Ip == ids.Ip).first()
            base_ids.Time_license = time_lic
            session.add(base_ids)
            session.commit()
            logger.info('Обновил срок лицензии')
            if driver.find_elements_by_xpath("//span[contains(text(), 'Срок действия лицензии истек.')]"):
                status = 'Срок действия лицензии истек'
                logs.append([ids.Id, ids.Ip, ids.Name_base, ids.Ids_version, ids.Time_license, 'Срок действия лицензии истек'])
                logger.warning(status + 'Пропуск')
                continue
            if driver.find_elements_by_xpath("//span[contains(text(), 'Требуется обновить базу правил')]") and driver.find_element_by_xpath("//span[contains(text(), 'Требуется обновить базу правил')]").is_displayed():
                logger.info('Обновляю базу правил')
                driver.find_element_by_xpath("//span[contains(text(), 'Требуется обновить базу правил')]").click()
                driver.find_element_by_xpath("//span[contains(text(), 'Обновить')]").click()
                input = driver.find_element_by_id('fileuploadfield-2520-inputEl')
                driver.execute_script("arguments[0].removeAttribute('readonly')", input)
                driver.find_element_by_xpath("//input[@class = ' x-form-file-input']").send_keys(os.path.abspath(pwd+'/ids') + str(files[0]))
                input.send_keys(os.path.abspath(pwd+'/ids') + str(files[0]), Keys.ENTER)
                sleep(1)
                driver.find_element_by_id('button-2579-btnIconEl').click()
                sleep(1)
                driver.find_element_by_id('button-2579-btnIconEl').click()
                while driver.find_element_by_xpath("//div[contains(text(), 'Загрузка файла...')]").is_displayed():
                    sleep(10)
                driver.find_element_by_id('button-2580').click()
                logger.info('Загрузил файл, ожидание обновления')
                time_await = 0
                while 1:
                    if driver.find_element_by_xpath("//div[@class = 'front-inner']").is_displayed() or time_await > 30:
                        logs.append([ids.Id, ids.Ip, ids.Name_base, ids.Ids_version, ids.Time_license, 'Обновлено'])
                        break
                    else:
                        sleep(10)
                        time_await = time_await + 1
                if time_await > 30:
                    sleep(5)
                    status = str(driver.find_element_by_xpath("//div[@class = 'front-inner']").text)
                    logs.append([ids.Id, ids.Ip, ids.Name_base, ids.Ids_version, ids.Time_license, 'Ошибка при обновлении '+status+''])
                    logger.critical('Ошибка при обновлении '+status+'')
                    continue
            else:
                logs.append([ids.Id, ids.Ip, ids.Name_base, ids.Ids_version, ids.Time_license, 'Не требуется обновление'])
                logger.info('Не требуется обновление')
    except Exception as e:
        logger.error('Произошла ошибка! ===== ' + str(e))
        driver.__exit__()
        exit()
    admin_report(logs)
    logger.info('Завершение работы')
    driver.__exit__()
start()
