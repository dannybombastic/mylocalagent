import sys
import os

print("Python sys.path:")
for p in sys.path:
    print(p)

try:
    import azure_devops_mcp
    print("azure_devops_mcp package location:", azure_devops_mcp.__file__)
except ModuleNotFoundError:
    print("azure_devops_mcp package not found")

try:
    import mcp
    print("mcp package location:", mcp.__file__)
except ModuleNotFoundError:
    print("mcp package not found")

print("Contents of current working directory:")
for root, dirs, files in os.walk(".", topdown=True):
    for name in files:
        print(os.path.join(root, name))
