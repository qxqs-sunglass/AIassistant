import os
import pathlib


app_dict = {}
try:
    path = pathlib.Path.home().joinpath("Desktop")
except FileNotFoundError:
    path = pathlib.Path.home().joinpath("OneDrive\\Desktop")
except Exception as e:
    print(e)
    exit(0)
print(path)
for filename in os.listdir(path):
    name = filename.split(".")[0]
    if filename.endswith(".lnk"):
        app_dict[name] = f"{path}\\{filename}"
print(app_dict)
