from utilities import Nextcloud
from utilities import Helper
import config
import sys
from tabulate import tabulate
import getpass

if config.password is None:
    config.password = getpass.getpass()


nc = Nextcloud(config.url,
               config.user, config.password, config.base_dir)
if len(sys.argv) > 0:
    exams = nc.get_links(sys.argv[1:])[0]
    table = []
    clipboard = ""
    for exam in exams:
        clipboard += str(exam)+": " + str(exams[exam][0])+"\n"
        table.append([exam, exams[exam][0], "{:.2f}".format(exams[exam][1])])
    header = ["Exam", "Link", "Score"]
    table = sorted(table, key=lambda x: x[2], reverse=True)
    Helper.toClipboard(clipboard)
    print(tabulate(table, headers=header))
