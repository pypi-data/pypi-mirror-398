from setuptools import setup, find_packages

def get_libraries():
    return open("D:/Florest/Programming/Python/florestbotfunctions/libraries.txt", 'r').readlines()

setup(name='florestbotfunctions', version='1.9.0', description='Функции бота Флореста в одной библиотеке.', long_description='Привет! Данная библиотека включает в себя функции из https://t.me/postbotflorestbot. Все функции, с удобным объяснением кода, только здесь. P.S. Это официальная библиотека от создателя бота - FlorestDev. Все функции предоставляются в ознакомительном порядке.', author='florestdev', author_email='florestone4185@internet.ru', packages=find_packages(), python_requires='>=3.10', project_urls={"Social Resources": 'https://taplink.cc/florestone4185', 'My bot':"https://t.me/postbotflorestbot", 'GitHub of Project':"https://github.com/florestdev/florestbotfunctions"}, install_requires=get_libraries())