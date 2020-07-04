import os
import getpass

os.system("pip3 install python-Levenshtein")
os.system("pip3 install tabulate")
os.system("pip3 install clipboard")

def tryAgain(output):
    again = True
    while again:
        inp = input(output)
        if inp != "":
            return inp
        print("Can't be empty")

url = tryAgain("Enter the base url of your Nextcloud:\n")
base_dir = tryAgain("Enter the path to the directory to search in:\n")
username = tryAgain("Enter your Nextcloud username:\n")

password = getpass.getpass(prompt="Enter your Nextcloud password:\n")

with open("config.py", 'w') as outfile:
    outfile.write("user='")
    outfile.write(username)
    outfile.write("'\n")

    outfile.write("password=")
    if password=="":
        outfile.write("None")
    else:
        outfile.write("'")
        outfile.write(password)
        outfile.write("'")
    outfile.write("\n")

    outfile.write("url='")
    outfile.write(url)
    outfile.write("'\n")

    outfile.write("base_dir='")
    outfile.write(base_dir)
    outfile.write("'\n")


