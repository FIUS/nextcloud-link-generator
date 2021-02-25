import sys
from pathlib import Path
import nclink.pyocclient.owncloud.owncloud as owncloud
import Levenshtein as stein
import datetime
import math
import clipboard
import datetime
from nextcloud import NextCloud
from nextcloud.base import ShareType,Permission, datetime_to_expire_date
from urllib.parse import unquote
import nclink.config as config
import threading

class Nextcloud:

    def __init__(self, domain, username, password, remote_directory):
        #self.oc = owncloud.Client(domain)
        #self.oc.login(username, password)
        
        self.username=username
        self.remote_directory=remote_directory
        self.nc=NextCloud(domain,username,password,json_output=True)
        self.cache_thread_running=False
        self.remote_directory = remote_directory
        print("Filling cache...")
        self.file_cache = (datetime.datetime.now(),
                           self.get_dirs())
        self.link_cache={}
        
        print("Cache Done!")

    def link_from_server(self,folder,expire_days=7):
        expire_date = datetime_to_expire_date(datetime.datetime.now() + datetime.timedelta(days=expire_days))
        link=self.nc.create_share(folder, share_type=ShareType.PUBLIC_LINK.value)
        if link.is_ok:
            link_id=link.data['id']
            link_permissions=link.data['permissions']
            updated_link=self.nc.update_share(link_id, expire_date=expire_date) 
            if updated_link.is_ok:
                log_data=updated_link.data
                
                with open('links.log', 'a') as log_file:
                    logput = str(datetime.datetime.now())+" -> "
                    logput += " id: "+log_data['id']
                    logput += " expiration: "+log_data['expiration']
                    logput += " url: "+log_data['url']
                    logput += "\n"
                    
                    log_file.write(logput)

                return updated_link.data['url']
        return None
    
    def get_dirs(self):
        raw=self.nc.list_folders(self.username,path=self.remote_directory).data
        output_list=[]
        for dir in raw:
            strings=unquote(dir['href']).split("/")[5:-1]
            output_string=""
            for s in strings:
                output_string+="/"+s
            output_string+="/"
            output_list.append(output_string)
        return output_list[1:]

    def get_links(self, lectures, link_expire_in_days=7, accuracy=8, cache_callback=None, recursion=True):
        try:
            cache_time=datetime.datetime.now()-self.file_cache[0]
            print("Cache lifetime:",cache_time)
            
            if cache_time.total_seconds() > config.directory_cache_time:
                print("not using cache")
                self.file_cache = (datetime.datetime.now(),
                                self.get_dirs())
            else:
                print("using cache")
            
            if cache_callback is not None and recursion and not self.cache_thread_running:
                if len(self.link_cache)==0 or (datetime.datetime.now()-self.link_cache[self.link_cache.keys()[0]][0]).total_seconds()>config.file_cache_time:
                    self.cache_thread_running=True
                    cache_callback("The cache is being recreated, your request is processed parallel")
                    try:
                        params=([""],link_expire_in_days,accuracy,cache_callback,False)
                        threading._start_new_thread(self.get_links,params)
                    except Exception as e:
                        print(e)
                    

            files = self.file_cache[1]

            cache_counter=0
            fetch_counter=0
        except Exception as ex:
            print(ex)
        print("Done...")
        output = {}
        for lecture in lectures:
            print("Searching for:", lecture)
            counter=1
            for f in files:
                
                split_path = f.split("/")

                lecture_name_server = split_path[-2]

                modified_lecture_name_server = lecture_name_server.replace(
                    "-", "")
                modified_lecture = lecture.replace("-", "")

                distance = stein.distance(
                    modified_lecture, modified_lecture_name_server)
                if distance < accuracy or modified_lecture.lower() in modified_lecture_name_server.lower():
                    if distance <= 0:
                        distance = 1
                    if lecture_name_server in self.link_cache and (datetime.datetime.now()-self.link_cache[str(lecture_name_server)][0]).total_seconds()<config.file_cache_time:
                        print("Using cached Link")
                        cache_counter += 1
                        output[lecture_name_server] =(self.link_cache[str(lecture_name_server)][1],1/float(math.sqrt(distance)))
                        
                    else:
                        if not recursion:
                            print("Fetching link from server (cache thread)")
                        if recursion:
                            print("Fetching link from server (request)")
                        fetch_counter += 1
                        
                        link_info = self.link_from_server(f,expire_days=link_expire_in_days)
                        print("Done fetching")
                        
                        if not recursion:
                            percentage="{:.2f}".format((counter/len(files))*100)+"%"
                            # cache_callback("Caching progress: "+percentage)
                            counter+=1

                        self.link_cache[str(lecture_name_server)]=(datetime.datetime.now(),link_info)
                        output[lecture_name_server] = (link_info, 1/float(math.sqrt(distance)))
        if not recursion:
            self.cache_thread_running=False
            cache_callback("The cache has been recreated!")
        return output,cache_counter,fetch_counter


class Helper:
    @staticmethod
    def toClipboard(text):
        clipboard.copy(text)
