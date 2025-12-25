from thkit.pkg import check_package

try:
    check_package("ELATE", auto_install=True, git_repo="https://github.com/coudertlab/elate")
except Exception as e:
    print(e)
