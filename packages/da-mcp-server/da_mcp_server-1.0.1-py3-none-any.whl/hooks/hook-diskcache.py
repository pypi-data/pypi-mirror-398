# hooks/hook-diskcache.py
from PyInstaller.utils.hooks import collect_all, collect_submodules

# 收集所有 diskcache 相关的模块
datas, binaries, hiddenimports = collect_all('diskcache')

# 额外确保收集所有子模块
hiddenimports += collect_submodules('diskcache')

# 打印调试信息（打包时可以看到）
print("diskcache hidden imports:", hiddenimports)
print("diskcache datas:", len(datas))