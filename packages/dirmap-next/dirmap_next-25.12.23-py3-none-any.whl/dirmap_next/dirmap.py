#!/usr/bin/env python3

'''
@Author: xxlin
@LastEditors: xxlin
@Date: 2019-04-10 13:27:59
@LastEditTime: 2023-07-25 15:56:04
'''

from pathlib import Path
import sys

from gevent import monkey
monkey.patch_all()
from .lib.controller.engine import run
from .lib.core.common import banner, outputscreen, setPaths
from .lib.core.data import cmdLineOptions, paths
from .lib.core.option import initOptions
from .lib.parse.cmdline import cmdLineParser




def main() -> None:
    """
    main fuction of dirmap 
    """
    # Make sure the version of python you are using is high enough
    if sys.version_info < (3, 8):
        outputscreen.error("Sorry, dirmap requires Python 3.8 or higher\n")
        sys.exit(1)
    # anyway output thr banner information
    banner() 

    # set paths of project 
    paths.ROOT_PATH = str(Path(__file__).parent)
    print(f" 输出：{Path(paths.ROOT_PATH) / 'output'}   \n 数据：{Path(paths.ROOT_PATH) / 'data' }  \n 配置：{Path(paths.ROOT_PATH) / 'dirmap.conf'}"  )
    setPaths()
    
    # received command >> cmdLineOptions
    cmdLineOptions.update(cmdLineParser().__dict__)
    
    # loader script,target,working way(threads? gevent?),output_file from cmdLineOptions
    # and send it to conf
    initOptions(cmdLineOptions) 

    # run!
    try:
        run()
    except KeyboardInterrupt:
        outputscreen.success("[+] exit")
        sys.exit(1)

if __name__ == "__main__":
    main()
