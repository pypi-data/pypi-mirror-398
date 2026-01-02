from setuptools import setup, find_packages

def get_libraries():
    return open("D:/Florest/Programming/Python/minecraftbotsapi/libraries.txt", 'r').readlines()

setup(name='minecraftbotsapi', version='1.2', description='Функции для создания своего бота в Minecraft!', long_description='Документацию Вы можете найти на Github! Для использования установите mineflayer, среду NodeJS.', author='florestdev', author_email='florestone4185@internet.ru', packages=find_packages(), python_requires='>=3.10', project_urls={"Social Resources": 'https://taplink.cc/florestone4185', 'GitHub of Project':"https://github.com/florestdev/minecraftbotsapi"}, install_requires=get_libraries())