import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.select import Select

class name_finder():
    
    in_sep = "[ _.:*]"
    in_sep_dup = "[ _.:*/]+"
    out_sep = "."
    
    def __init__(self):
        self.driver = webdriver.Chrome(executable_path=r'C:\Users\neria\Downloads\python\chromedriver.exe')
        self.driver.get(self.url[0])
        self.driver.set_window_size(1600, 900)
        self.wait = WebDriverWait(self.driver, 5)
        self.vars = {}
        self.name = ''
        
    def __del__(self):
        self.driver.quit()
            
    def search_eng_name(self, name):
        if isinstance(name, str): # if a string covert to array
            name = re.sub(' ','.',name)
            name = name.split('.') # create array from name
            # if the is the first world combine with the seconed
            if name[0].casefold() == 'the': 
                name[0:2] = [' '.join(name[0:2])]
        self.name = name
        i = 1
        # use the first function to search on web
        name_eng = self.func[0]()
        # while the name didn't found go to next site function
        while not(name_eng)  and i < len(self.func):
            self.driver.get(self.url[i])
            name_eng = self.func[i]()
            i = i + 1
        self.driver.get(self.url[0]) # back to first site option
        return name_eng
    
#######################
# series_finder class #
#######################
    
class series_finder(name_finder):
    def __init__(self):
        self.url = ["https://www.sdarot.tw/"]
        self.func = [self.sdarot]
        # username = "stak68@gmail.com"
        # password = "friends6"
        super().__init__()
        self.sep_rep = lambda x:re.sub(name_finder.in_sep_dup,name_finder.out_sep,x)
        self.hyphen_rep = lambda x:re.sub('\.?-\.?','-',x) # remove dots around the hyphen
        
        # login
        username,password = self.login()
        if username and password:
            find_element = self.driver.find_element
            find_element(By.XPATH, "//button[@data-target='#loginForm']").click()
            find_element(By.NAME, "username").send_keys(username)
            self.wait.until(EC.element_to_be_clickable((By.NAME, "password")))
            find_element(By.NAME, "password").send_keys(password)
            find_element(By.XPATH, "//button[@name='submit_login']").click()
        
    def login(self):
        try:
            f = open("login.txt", "r")
            user_txt = f.readline()
            user = user_txt.split(':')[1].strip()
            password_txt = f.readline()
            password = password_txt.split(':')[1].strip()
        except:
            user = ''
            password = ''
        return user,password
        
        
    def sdarot(self):
        driver = self.driver
        name_array = self.name
        search_type = 'h4'
        name_eng = ""
        self.url_init_search = 'search?term='
        url_search = self.url[0] + self.url_init_search
        for i in range(len(name_array)):
            i_name = name_array[i]  # take the first word
            self.driver.get(url_search + i_name)
            time.sleep(0.5)
            # sometimes the page got an error and need to refresh
            err = driver.find_elements(By.XPATH,"//h1[text()='An error occurred.']")
            while err:
                time.sleep(0.2)
                driver.refresh()
                err = driver.find_elements(By.XPATH,"//h1[text()='An error occurred.']")
            results_eng = driver.find_elements(By.TAG_NAME, 'h5')
            
            if len(results_eng)>0:
                #replace all to '.' except at start,end and '-'
                if len(results_eng)==1:
                    print('*** stop ***')
                    pass
                else:
                    name = ".".join(name_array[i:])
                    isEng = re.search('[a-zA-Z]',name)
                    if isEng: # for english search
                        search_type = 'h5'
                    results = driver.find_elements(By.TAG_NAME, search_type) #check if there several results
                    # change name to spesific format (like input)
                    results = list(map(lambda x: self.hyphen_rep(self.sep_rep(x.get_attribute('textContent'))).strip('.'), results))
                    # search for partial match in results
                    idx = [j for j,iresult in enumerate(results) if name.casefold() in iresult.casefold().replace("'","")]
                    if len(idx) > 1: # if several result check for full match
                        idx = [j for j,iresult in enumerate(results) if name.casefold() == iresult.casefold().replace("'","")]
                    if idx: # if find match
                        idx = idx[0]
                        name_heb = [results[idx]]
                        if results[idx] != name: # web name not equal to search word
                            name_heb.append(name)
                        results_eng = list(map(lambda x: x.get_attribute('textContent'), results_eng))
                        name_eng = results_eng[idx]
                        break
                    else: # no match
                        continue
            else: # one result or no result
                try:
                    result = driver.find_element(By.XPATH,"//div[@class='poster']//h1//strong")
                except NoSuchElementException: # no results
                    continue
                else: # one result
                    name_heb = [re.search('.*(?= / )',result.text).group()]
                    if name_heb[0] != i_name:
                        name_heb.append(i_name)
                    name_eng = re.search('(?<= / ).*',result.text).group()
                    break
        if name_eng:
            return [name_eng, name_heb]
        else:
            return False
        
######################
# movie_finder class #
######################   
class movie_finder(name_finder):
    def __init__(self):
        self.url = ["https://www.fisheye.co.il/",
                          "https://www.google.co.il/"] 
        self.func = [self.fisheye, self.google]
        super().__init__()
    
    def fisheye(self):
        driver = self.driver
        name_array = self.name
        name_heb = ""
        search_bar = driver.find_element(By.ID, "movie_page_search") # seach bar
        search_btn = driver.find_element(By.XPATH,"//div[@id='fishey_search_movie_button']/span") # search button
        for i in range(len(name_array)):
            for j in range(i,len(name_array)):
                i_name = name_array[j]  # take the first word
                search_bar.send_keys(i_name)
                search_btn.click() # search button
                self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[@id='movie_search_res']//a"))) # wait for results
                name_opt = driver.find_elements(By.XPATH,"//div[@id='movie_search_res']//a") # read all results
                if len(name_opt) == 1: # if not results
                    break
                elif len(name_opt) > 2: #if more than one results
                    if j == len(name_array)-1: # if this is the full name
                        try:
                            name_opt = driver.find_element(By.XPATH,"//div[@id='movie_search_res']").find_element(
                                By.LINK_TEXT, search_bar.get_attribute('value')) # check if there is exectly macth name
                            name_heb = name_opt
                            break
                        except:
                            pass
                else: #if only one result
                    only_name = re.sub('\(.*\)','',name_opt[1].text)
                    if i_name in only_name:
                        name_heb = name_opt[1]
                        break
                search_bar.send_keys(" ")
            if name_heb:
                name_heb.click()
                break
            else:   
                search_bar.clear()
        if name_heb:
            try:
                name_eng = driver.find_element(By.CLASS_NAME, 'movie-titleeng').text # extract ENG name
            except:
                name_eng = False
        else:
            name_eng = False  
        return name_eng
    
    def google(self):
        driver = self.driver
        # driver.get(self.url[1])
        name_array = self.name
        
        search_bar = driver.find_element(By.XPATH, "//input[@title = 'חיפוש']") # seach bar
        search_bar.send_keys(" ".join(name_array))
        search_bar.send_keys(Keys.RETURN)
        driver.find_element(By.XPATH, "//span[text() = 'https://he.wikipedia.org']/ancestor::a").click()
        eng_link = driver.find_element(By.XPATH,"//a[contains(@href , 'https://en.wikipedia')]")
        name_eng = eng_link.get_attribute('title').split(' – ')
        name_eng = re.sub(' +',' ',re.sub('[:\(\) ]|film',' ',name_eng[0]).strip())
        
        return name_eng
    
######################
#        main        #
######################
                           
def main():
    # test = movie_finder()
    # name = test.search_eng_name('גנוב על העולם')
    test = series_finder()
    name = test.search_eng_name('הפוך')
    print(name)
                
if __name__ == "__main__":
    main()       