from PyInstaller.utils.hooks import collect_submodules, collect_data_files,collect_all

datas, binaries, hiddenimports = collect_all('docx')

# 额外确保收集所有子模块
hiddenimports += collect_submodules('docx')

# 打印调试信息（打包时可以看到）
print("docx hidden imports:", hiddenimports)
print("docx datas:", len(datas))