#This is webcrawler code created by mting

from bs4 import BeautifulSoup as soup
import itertools
import numpy as np
import os
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
import winsound
import time

class GameDay:
    position = ""

    def __init__(self, starting_url, file_name, score_type):
        self.starting_url = starting_url
        self.browser = webdriver.Chrome(chrome_options=self.set_options())
        self.orginal = pd.read_excel("mmb.xlsx", sheet_name='Sheet1')
        self.score_type = score_type
        self.scores = []
        self.start_time = 0
        self.pass_count = 0
        self.estimate = 0

    def set_options(self):
        path_to_extension = r'C:\Users\mting\Desktop\3.31.2_0'
        chrome_options = Options()
        chrome_options.add_argument('load-extension=' + path_to_extension)
        return(chrome_options)
        
    def open(self):
        self.browser.create_options()
        self.browser.get(self.starting_url)
        i = 0
        self.start_time = time.time()
        print("Collecting data now")
        while i < self.orginal.shape[0]:
            global position
            position = self.orginal.iloc[i][0]
            self.search(self.orginal.iloc[i][1])
            self.time()
            i += 1
        self.orginal['Scores'] = self.scores
        self.browser.close()
        Combos(self.orginal).make_combos()
        
    def time(self):
        self.pass_count += 1
        self.estimate = time.time() - self.start_time
        estimate = self.estimate * (self.orginal.shape[0] - self.pass_count)
        hrs = int(estimate/3600)
        mins = int((estimate-(hrs*3600))/60)
        print("Estimated time until completion: %ihrs %imins" % (hrs, mins))
        self.start_time = time.time()
        return

    def search(self, name):
        search_bar = self.browser.find_element_by_id("search-box")
        search_bar.send_keys(name)
        search_bar.send_keys(Keys.RETURN)
        try:
            self.browser.find_element_by_link_text(name).click()
        except NoSuchElementException:
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
            print("Please help then press enter")
            input()
        except WebDriverException:
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
            print("Please help then press enter")
            input()
        self.get_data_from_page() 

    def get_data_from_page(self):
        titles = ["player-tournament-stats-summary", "player-tournament-stats-defensive", "player-tournament-stats-offensive", 
        "player-tournament-stats-passing", "player-tournament-stats-detailed"]
        clickable = ["Defensive", "Offensive", "Passing"]
        avg_final = []
        for index, item in enumerate(titles):
            if index > 0 and index < 4:
                time.sleep(1)
                try:
                    self.browser.find_element_by_link_text(clickable[index-1]).click()
                except WebDriverException:
                    tries = 0
                    while tries < 6:
                        time.sleep(5)
                        try: 
                            self.browser.find_element_by_link_text(clickable[index-1]).click()
                        except WebDriverException:
                            pass
                        finally:
                            tries += 1
                    winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
                    print("Please click " + clickable[index-1] + " then press enter")
                    input()
            if index == 4:
                time.sleep(1)
                try:
                    self.browser.find_element_by_link_text("Detailed").click()
                    select = Select(self.browser.find_element_by_id('category'))
                    select.select_by_value('saves')
                except NoSuchElementException:
                    tries = 0
                    while tries < 4:
                        time.sleep(5)
                        try:
                            select = Select(self.browser.find_element_by_id('category'))
                            select.select_by_value('saves')
                        except NoSuchElementException:
                            pass
                        finally:
                            tries += 1
                    winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
                    print("Help, I got stuck on saves")
                    input()
            time.sleep(1)
            innerHTML = self.browser.execute_script("return document.body.innerHTML")
            page_soup = soup(innerHTML, 'lxml')            
            g_data = page_soup.find_all("div", {"id" : item})
            try:
                for item in g_data:
                    table = item.find_all("tbody", {"id" : "player-table-statistics-body"})
                for item in table:
                    row = item.find_all("tr")
                raw_averages = row[len(row)-1]
                averages = []
                for item in raw_averages:
                    try:
                        if item.text == "-":
                            averages.append(0)
                        else:
                            averages.append(float(item.text))
                    except ValueError:
                        pass
                    except AttributeError:
                        pass
                if not averages:
                    avg_final.append([0]*10)
                else:
                    avg_final.append(averages)
            except UnboundLocalError:
                self.browser.find_element_by_link_text("Summary").click()
                self.get_data_from_page()
        data = []
        if avg_final[0][0] == 0:
            avg_final[0][0] = 1
        data.append((avg_final[0][0], avg_final[0][2], avg_final[3][3], avg_final[2][4], avg_final[3][6], avg_final[2][7], 
        avg_final[1][4], avg_final[1][2], avg_final[1][3], avg_final[0][4], avg_final[0][5], avg_final[3][4], avg_final[3][5], 
        avg_final[4][2]))
        global position
        self.scores.append(Data(data, self.score_type, position).calculate_score())
        return

class Data:    
    def __init__(self, data, score_type, position):
        self.avg_set = [[data[0][1]/data[0][0]], [data[0][2]], [data[0][3]], [data[0][4]], [data[0][5]], [data[0][6]], [data[0][7]], [data[0][8]], [data[0][9]/data[0][0]], [data[0][10]/data[0][0]], [data[0][13]]]
        self.AvgP = data[0][11]
        self.PSP = data[0][12]
        self.score_type = score_type
        self.position = position
        self.score_field = 5
        self.score_set = [[10, 6, 1, .75, 1, -.5, 1, .5, -1.5, -3, 2], [20, 12, 2, 1.5, 2, -1, 2, 1, -3, -6, 0], [22, 12, 2, 1.5, 2, -1, 2, 1, -3, -6, 0], [24, 15, 2, 1.5, 2, -1, 2, 1, -3, -6, 0], [26, 16, 2, 1.5, 2, -1, 2, 0, -3, -6, 3]]
        return

    def set_score(self):
        if self.score_type == "yes":
            self.score_field = 0
        elif self.position == "F":
            self.score_field = 1
        elif self.position == "M": 
            self.score_field = 2
        elif self.position == "D":
            self.score_field = 3
        else:
            self.score_field = 4

    def calculate_score(self):
        self.set_score()
        score = np.matmul(self.score_set[self.score_field], self.avg_set)
        if self.score_type != "yes":
            score = score + .05*(self.AvgP*(self.PSP*.01))
        return score

class Combos: 
    def __init__(self, data_frame):
        self.data_frame = data_frame
        self.one_percent = 0
        self.pass_count = 0
        self.start_time = 0
        self.estimate = 0
        return 

    def time(self):
        self.pass_count += 1
        elapsed = time.time() - self.start_time
        self.estimate = (elapsed+self.estimate)/self.pass_count
        estimate = self.estimate * (100 - self.pass_count)
        hrs = int(estimate/3600)
        mins = int((estimate-(hrs*3600))/60)
        print("Estimated time until completion: %ihrs %imins" % (hrs, mins))
        self.start_time = time.time()
        return
    
    def make_combos(self):
        team_roster = []
        data_set = []
        pass_count = 0
        high_score = 1
        index = 0
        while index < self.data_frame.shape[0]:
            data_set.append(self.data_frame.ix[index])
            index +=1 
        self.one_percent = int(len(list(itertools.combinations(range(0, self.data_frame.shape[0]), 6)))/100)
        self.start_time = time.time()
        print("Running combos now")
        for item in itertools.combinations(np.array(data_set), 6):
            if pass_count == self.one_percent:
                self.time()
                pass_count = 0
            current = np.sum(item, axis=0)
            if (current[4] > high_score or abs((current[4]-high_score)/high_score) < .1) and current[2] < 50001:
                if current[4] > high_score:
                    high_score = current[4]
                team_roster.append(np.array(current))
            pass_count +=1 
        print("Writing to file")
        if os.path.isfile("Output.txt"):
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
            print("Save your last Output file if you want it, press enter to generate new file")
            input()
            try: 
                os.remove("Output.txt")
            except FileNotFoundError:
                pass
        text_file = open("Output.txt", "w+")
        for index, item in enumerate(team_roster):
            string = item 
            for part in string:
                text_file.write("%s" % str(part))
            text_file.write("\n")
        text_file.write('\n' * 10)
        text_file.write(str(self.data_frame))
        text_file.close
        winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)

test = GameDay("https://www.whoscored.com/", "mmb", "no")
test.open()