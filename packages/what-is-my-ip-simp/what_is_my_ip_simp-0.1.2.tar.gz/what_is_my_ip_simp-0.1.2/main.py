import requests
from bs4 import BeautifulSoup

URL = "https://ipv4.google.com/sorry/index"


    
class WhatIsMyIPObj:
    def __init__(self):
        web = requests.get(URL)
        soup = BeautifulSoup(web.text, "html5lib")
        div_all = soup.find_all("div")

        target_div = div_all[3]
        all_line = target_div.get_text("<br/>")
        splited_line = all_line.split("<br/>")
        address_line_splited = splited_line[0].split(": ")
        self.ip = address_line_splited[1]
        
    @property
    def my_ip(self):
        return self.ip

def main():
    ip = WhatIsMyIPObj()
    print("Your IP Address is: {0}".format(ip.my_ip))
    
if __name__ == "__main__":
    main()