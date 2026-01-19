import os
import pathlib


app_dict = {}
path = pathlib.Path.home().joinpath("Desktop")
print(path)
for filename in os.listdir(path):
    name = filename.split(".")[0]
    if filename.endswith(".lnk"):
        app_dict[name] = f"{path}\\{filename}"
print(app_dict)
