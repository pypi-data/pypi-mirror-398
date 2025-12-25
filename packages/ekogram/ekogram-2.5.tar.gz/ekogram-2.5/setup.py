from setuptools import setup

setup(
    name='ekogram',
    version='2.5',
    description='Lightweight library for working with Telegram Bot Api + Generate Images, Audio and Text',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/SiriRSST/Ekogram',
    author='Siri-Team',
    author_email='siriteamrs@gmail.com',
    license='MIT',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"],
    keywords=['telebot', 'bot', 'gram', 'pytelegrambotapi', 'telegram', 'ekogram', 'aiogram', 'gpt', 'freegpt', 'openai', 'ai'],
    packages=['ekogram'],
    install_requires=['requests', 'bs4'],
    project_urls={"Source": "https://github.com/SiriRSST/Ekogram"},
    python_requires='>=3.9'
)
