from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_all

datas, binaries, hiddenimports = collect_all('requests')
# 额外确保收集所有子模块
hiddenimports += collect_submodules('requests')

# 打印调试信息（打包时可以看到）
print("requests hidden imports:", hiddenimports)
print("requests datas:", len(datas))