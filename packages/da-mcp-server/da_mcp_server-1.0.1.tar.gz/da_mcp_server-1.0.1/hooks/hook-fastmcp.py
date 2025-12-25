from PyInstaller.utils.hooks import collect_submodules, collect_data_files,collect_all

datas, binaries, hiddenimports = collect_all('fastmcp')

# 打印调试信息（打包时可以看到）
print("fastmcp hidden imports:", hiddenimports)
print("fastmcp datas:", len(datas))