import sys
from pathlib import Path
import pyocclient.owncloud.owncloud as owncloud
import Levenshtein as stein
import datetime
import math

class Nextcloud:

    def __init__(self,domain,username,password,remote_directory):
        self.oc = owncloud.Client(domain)
        self.oc.login(username, password)
        self.remote_directory=remote_directory

    def get_links(self,lectures,link_expire_in_days=7):
        next_week = datetime.datetime.now()+datetime.timedelta(days=link_expire_in_days)
        next_week_string = str(next_week.year)+"-" + str(next_week.month)+"-"+str(next_week.day)

        files = self.oc.list(self.remote_directory)
        output={}
        for lecture in lectures:
            for f in files:
                if f.file_type == "dir":
                    split_path=f.path.split("/")
                    
                    lecture_name_server=split_path[-2]

                    modified_lecture_name_server=lecture_name_server.replace("-","")
                    modified_lecture=lecture.replace("-","")
                    
                    distance=stein.distance(modified_lecture, modified_lecture_name_server)
                    if distance < 10:
                        link_info=self.oc.share_file_with_link(
                            f.path, expire_date=next_week_string)
                        output[lecture_name_server]=(link_info.get_link(),1/float(math.sqrt(distance)))
        return output
                        
