import sys
from pathlib import Path
import pyocclient.owncloud.owncloud as owncloud
import Levenshtein as stein
import datetime
import math
import clipboard


class Nextcloud:

    def __init__(self, domain, username, password, remote_directory):
        self.oc = owncloud.Client(domain)
        self.oc.login(username, password)
        self.remote_directory = remote_directory

    def get_links(self, lectures, link_expire_in_days=7, accuracy=8):
        next_week = datetime.datetime.now()+datetime.timedelta(days=link_expire_in_days)
        next_week_string = str(next_week.year)+"-" + \
            str(next_week.month)+"-"+str(next_week.day)
        print("Getting exams from server...")
        files = self.oc.list(self.remote_directory)
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