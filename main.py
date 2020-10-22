from selenium import webdriver
from userInput import username, password
from selenium.common.exceptions import NoSuchElementException
from prettytable import PrettyTable
import schedule
import time
import datetime
from selenium.webdriver.common.alert import Alert

if __name__ == '__main__':
    def get_user_and_pass():
        print('Welcome to automate your binus schedule,\n'
              'Please input your username and password\nThis is a one time feature so be cautious when submitting.')
        u = input('username: ')
        p = input('password: ')
        fd = open('userInput.py', "w")
        data = ("username = '{}'\npassword = '{}'".format(u, p))
        fd.write(data)
        return [u, p]

    if username == '' and password == '':
        up = get_user_and_pass()
        username = up[0]
        password = up[1]

    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging', 'ignore-certificate-errors'])
    options.add_argument('headless')

    driver = webdriver.Chrome(executable_path='chromedriver.exe', options=options)

    pTable = PrettyTable()
    pTable.field_names = ['DATE', 'TIME', 'CLASS', 'MODE', 'COURSE', 'SESSION', 'LINK']
    pTable.align['COURSE'] = 'l'
    pTable.align['LINK'] = 'l'


    def input_table(d, t, cl, m, co, se, li):
        pTable.add_row([d, t, cl, m, co, se, li])


    def update_schedule():
        driver.implicitly_wait(10)
        driver.get('https://myclass.apps.binus.ac.id/Auth')
        # Login
        print('Signing account {}@binus.ac.id'.format(username))
        username_textbox = driver.find_element_by_id('Username')
        password_textbox = driver.find_element_by_id('Password')
        login_button = driver.find_element_by_id('btnSubmit')
        username_textbox.send_keys(username)
        password_textbox.send_keys(password)
        login_button.click()
        # Scan for tables
        tbody = driver.find_element_by_xpath('/html/body/div[1]/div/div/div/div[3]/div[2]/table/tbody')
        trs = tbody.find_elements_by_xpath('//tr')
        trl = 0
        while trl <= 7:
            trs = tbody.find_elements_by_xpath('//tr')
            trl = len(trs)
        pTable.clear_rows()
        print(trl)
        driver.implicitly_wait(0)
        print('Updating Table..')
        for j in range(6, trl):
            tr = trs[j]
            tds = tr.find_elements_by_tag_name('td')
            date_column = tds[0].text
            time_column = tds[1].text
            print(time_column)
            class_column = tds[2].text
            mode_column = tds[5].text
            course_column = tds[6].text
            session_column = tds[8].text
            try:
                lp = len(tr.find_elements_by_link_text('JOIN MEETING'))
                if lp > 0:  # Check if link is available
                    l_c = tr.find_elements_by_link_text('JOIN MEETING')
                    link_column = l_c[0].get_attribute('href')
                else:
                    link_column = '-'
            except NoSuchElementException:
                link_column = '-'
                print('NoSuchElementException initiated')
            input_table(date_column, time_column, class_column, mode_column, course_column, session_column, link_column)
        # Logout
        driver.get('https://myclass.apps.binus.ac.id/Auth/Logout')
        driver.get('data:,')


    def disable_table_artifacts():
        pTable.border = False
        pTable.header = False


    def enable_table_artifacts():
        pTable.border = True
        pTable.header = True


    def closest_meeting_table_date(i):
        disable_table_artifacts()
        a = i.get_string(fields=['DATE']).strip()
        enable_table_artifacts()
        return a


    def closest_meeting_table_time(i):
        disable_table_artifacts()
        b = i.get_string(fields=['TIME']).strip()[0:2]
        enable_table_artifacts()
        return b


    def get_closest_meeting():
        print('get_closest_meeting initiated:')
        now = datetime.datetime.now().strftime('%H')
        t = '-'
        for table in pTable:  # issue2 located
            date_and_time = closest_meeting_table_date(table)
            if date_and_time[0] == datetime.datetime.now().strftime('%d %b %Y'):  # if date is today
                print('Date matches')
                print(date_and_time[1])
                if date_and_time[1] == now:
                    print('Time matches')
                    t = table
        print(t)
        return t


    def date_matches(time_x):
        scheduledDate = get_table_data('DATE')
        scheduledTime = get_table_data('TIME')[0:2]
        todayDate = datetime.datetime.now().strftime('%d %b %Y')
        print('date_matches initiated:')
        print('{} == {} and {} == {}'.format(scheduledDate, todayDate, scheduledTime, time_x))
        if scheduledDate == todayDate and scheduledTime == time_x:
            print("Date and Time matched")
            return True
        else:
            print("Date and Time did not match")
            return False


    def is_there_link():
        print('Finding link..')
        link = get_table_data('LINK')
        if link == '-':
            print('No link found')
            return False
        else:
            return True


    def get_table_data(title):
        print('get_table_data initiated')
        disable_table_artifacts()
        a = ''
        try:
            a = get_closest_meeting().get_string(fields=[title]).strip()
        except AttributeError:
            print("No class this time")
        enable_table_artifacts()
        return a


    def get_class_link():
        print('Getting the link..')
        link = get_table_data('LINK')
        print('Link found: {0}'.format(link))
        return link


    def join_meeting(time_x):
        print('join_meeting initiated at {}:00'.format(time_x))
        if date_matches(time_x):
            print('Check if theres link')
            if is_there_link():
                link = get_class_link()
                print('Launching zoom..')
                launch_zoom_and_accept_link(link)


    def launch_zoom_and_accept_link(link):
        driver.implicitly_wait(5)
        driver.get(link)
        lunch = driver.find_element_by_link_text('launch meeting')
        lunch.click()
        time.sleep(2)
        Alert(driver).accept()
        driver.get('data:,')


    def scheduler_caller():
        t = datetime.datetime.now().strftime('%H')[0:2]
        join_meeting(t)


    def scheduler():
        schedule.every().day.at('06:45').do(update_schedule)
        schedule.every().day.at('07:00').do(scheduler_caller)
        schedule.every().day.at('09:00').do(scheduler_caller)
        schedule.every().day.at('11:00').do(scheduler_caller)
        schedule.every().day.at('13:00').do(scheduler_caller)
        schedule.every().day.at('15:00').do(scheduler_caller)
        schedule.every().day.at('17:00').do(scheduler_caller)


    update_schedule()
    print(pTable)
    print('Table Updated')
    scheduler()

    works = 0
    while True:
        if works == 0:
            print('Scheduler running..')
            works = 1
        schedule.run_pending()
        time.sleep(1)
