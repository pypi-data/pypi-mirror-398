from setuptools import setup, find_packages

# خواندن توضیحات طولانی از فایل README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='hutk',  # نام بسته
    version='1.0.4',  # نسخه بسته
    packages=find_packages(),
    description='A module for new programers or allameh helli school',  # توضیحات کوتاه
    long_description=long_description,  # توضیحات طولانی از فایل README.md
    long_description_content_type="text/markdown",  # نوع توضیحات (Markdown)
    author='M.P.Abdi',
    author_email='m.p.abdi90@gmail.com',
    python_requires='>= 3.6',  # حداقل نسخه پایتون مورد نیاز
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
)