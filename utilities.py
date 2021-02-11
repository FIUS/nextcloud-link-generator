import sys
from pathlib import Path
import nclink.pyocclient.owncloud.owncloud as owncloud
import Levenshtein as stein
import datetime
import math
import clipboard
import datetime


class Nextcloud:

    def __init__(self, domain, username, password, remote_directory):
        self.oc = owncloud.Client(domain)
        self.oc.login(username, password)
        self.remote_directory = remote_directory
        print("Filling cache...")
        self.file_cache = (datetime.datetime.now(),
                           self.oc.list(self.remote_directory))
        print("Cache Done!")

    def get_links(self, lectures, link_expire_in_days=7, accuracy=8):
        next_week = datetime.datetime.now()+datetime.timedelta(days=link_expire_in_days)
        next_week_string = str(next_week.year)+"-" + \
            str(next_week.month)+"-"+str(next_week.day)
        print("Getting exams from server...")
        cache_time=datetime.datetime.now()-self.file_cache[0]
        print("Cache lifetime:",cache_time)
        if cache_time.min > 30:
            print("not using cache")
            self.file_cache = (datetime.datetime.now(),
                               self.oc.list(self.remote_directory))
        else:
            print("using cache")

        files = self.file_cache[1]

        print("Done...")
        output = {}
        for lecture in lectures:
            print("Searching for:", lecture)
            for f in files:
                if f.file_type == "dir":
                    split_path = f.path.split("/")

                    lecture_name_server = split_path[-2]

                    modified_lecture_name_server = lecture_name_server.replace(
                        "-", "")
                    modified_lecture = lecture.replace("-", "")

                    distance = stein.distance(
                        modified_lecture, modified_lecture_name_server)
                    if distance < accuracy or modified_lecture.lower() in modified_lecture_name_server.lower():
                        if distance <= 0:
                            distance = 1
                        link_info = self.oc.share_file_with_link(
                            f.path, expire_date=next_week_string)
                        output[lecture_name_server] = (
                            link_info.get_link(), 1/float(math.sqrt(distance)))
        print()
        return output


class Helper:
    @staticmethod
    def toClipboard(text):
        clipboard.copy(text)
