# import ruamel.yaml
import os

file = "/api/xx/sset/iiii?r=/home/index"
file2 = "/apix/bbb/uuuu/xxx?ss=yy"

print(file.split("/"))
print(file2.split("/"))
print("".split("/"))
print("/".split("/"))
# print(os.path.commonprefix([file, file2]))
print(os.path.commonpath([file, file2]))
print(len(os.path.commonpath([file, file2]).split("/")))

path = "/Users/jiyvn/Documents/oas/m2s/m2src/mitmproxy2swagger/mitmproxy2swagger.py"
base_dir = os.getcwd()
abs_path = os.path.join(base_dir, path)
print(f"abs_path: {abs_path}")
print(f"file with / removed: {file.removeprefix("/")}")
print(f"\"\" with / removed: {"".removeprefix("/")}")
print(f"\"\" with / removed: {"".removeprefix("/").split("/")}")
print(file.removeprefix("/").split("/"))

x = {
    "sxx": 1,
    "syy": 2
}
x.update({})
print(x)