import os

__version__='0.2.0'
__path__=os.path.abspath(os.getcwd())

def parse_version_info(version_str):
    version_info = []
    for x in version_str.split('.'):
        if x.isdigit():
            version_info.append(int(x))
        elif x.find('rc') != -1:
            patch_version = x.split('rc')
            version_info.append(int(patch_version[0]))
            version_info.append(f'rc{patch_version[1]}')
    return tuple(version_info)

def hello():
    print("""
$$$$$$$\                                $$\      $$\ $$\       
$$  __$$\                               $$$\    $$$ |$$ |      
$$ |  $$ | $$$$$$\   $$$$$$$\  $$$$$$\  $$$$\  $$$$ |$$ |      
$$$$$$$\ | \____$$\ $$  _____|$$  __$$\ $$\$$\$$ $$ |$$ |      
$$  __$$\  $$$$$$$ |\$$$$$$\  $$$$$$$$ |$$ \$$$  $$ |$$ |      
$$ |  $$ |$$  __$$ | \____$$\ $$   ____|$$ |\$  /$$ |$$ |      
$$$$$$$  |\$$$$$$$ |$$$$$$$  |\$$$$$$$\ $$ | \_/ $$ |$$$$$$$$\ 
\_______/  \_______|\_______/  \_______|\__|     \__|\________|
                                      
    """)
    print("BaseML 提供了众多传统机器学习算法, 可以快速训练和应用各种算法模型")
    print("BaseML provides numerous traditional machine learning methods to quickly train and apply algorithms.")
    print("相关网址：")
    print("-文档网址 :  https://xedu.readthedocs.io")
    print("-官网网址 :  https://www.openinnolab.org.cn/pjEdu/xedu/baseedu")

version_info = parse_version_info(__version__)
