import time
import requests
import re as regular
import sqlite3 as sql
from datetime import timedelta, date
from bs4 import BeautifulSoup as bsoup

DataBasePath = 'data.db'


def Setup():
    global DataBasePath

    start_date = date(int(input("YEAR: ")), int(input("MONTH: ")), int(input("DAY: ")))
    end_date = date(int(input("YEAR: ")), int(input("MONTH: ")), int(input("DAY: ")))
    DataBasePath = f'{input("DB_NAME: ")}.db'

    start_time = time.time()
    DB_FirstConnect()

    for single_date in DateRange(start_date, end_date):
        print(f'Today is {single_date.day} {single_date.month} {single_date.year}')
        UrlList = GetUrls(single_date.day, single_date.month, single_date.year)
        int_value = 1
        for url in UrlList:
            print(f'{int_value} / {len(UrlList)} | url = {url}')
            GetFullInfoAboutArticle(url)
            int_value += 1

    print("=== === === --- END END END END END --- === === ===")
    print("--- %s seconds ---" % (time.time() - start_time))


def DateRange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)


def GetUrls(day, month, year):
    url = f'https://echo.msk.ru/news/{year}/{month}/{day}/'
    page = requests.get(url)
    results = bsoup(page.text, 'lxml')

    List = []
    counter = 0  # [DEBUG]

    for element0 in results.find_all('div', class_='preview newsblock iblock'):
        for element1 in element0.find_all("h3"):
            for element2 in element1.find_all("a"):
                counter += 1
                List.append(element2.get('href'))
    print(f'Новостей: {counter}')  # [DEBUG]
    return List


def GetFullInfoAboutArticle(url):
    url = regular.sub('\D', '', url)
    NewsList = GetNews(url)
    DB_WriteData(NewsList, "articles")

    CommentsList = GetComments(url)
    DB_WriteData(CommentsList, "comments")

    ProfilesList = []
    for user_id in CommentsList[2]:
        ProfilesList.append(GetProfile(user_id))
    DB_WriteData(ProfilesList, "profiles")


def GetNews(article_id):
    url = f'https://echo.msk.ru/news/{article_id}-echo.html'
    page = requests.get(url)
    results = bsoup(page.text, 'lxml')

    # ### article_id ### #
    List = [regular.sub('\D', '', article_id), '', '', '', '', '', '', '']

    # ### title ### #
    for element0 in results.find_all('h1', itemprop='headline'):
        temp = regular.sub(r'\s+', ' ', element0.text)
        temp = temp.lstrip(' ')
        List[1] = temp

    # ### url ### #
    List[2] = url

    # ### date & time ### #
    for element0 in results.find_all('div', class_='date'):
        # ### date ### #
        for element1 in element0.find_all('span', class_=''):
            temp = regular.sub(r'\s+', ' ', element1.text)
            temp = temp.lstrip(' ')
            List[3] = temp
        # ### time ### #
        for element1 in element0.find_all('strong', class_='red'):
            temp = regular.sub(r'\s+', ' ', element1.text)
            List[4] = temp

    # ### views_count & comments_count ### #
    for element0 in results.find_all('div', class_='conthead news'):
        for element1 in element0.find_all('div', class_='meta right'):
            # ### views_count ### #
            for element2 in element1.find_all('a', class_='view'):
                for element3 in element2.find_all('span', class_='count'):
                    temp = regular.sub(r'\s+', ' ', element3.text)
                    temp = temp.lstrip(' ')
                    List[5] = temp
            # ### comments_count ### #
            for element2 in element1.find_all('a', class_='comm'):
                for element3 in element2.find_all('span', class_='count'):
                    temp = regular.sub(r'\s+', ' ', element3.text)
                    temp = temp.lstrip(' ')
                    List[6] = temp

    # ### context ### #
    for element0 in results.find_all('div', class_='typical', itemprop='articleBody'):
        temp = regular.sub(r'\s+', ' ', element0.text)
        temp = temp.lstrip(' ')
        List[7] = temp
    return List


def GetComments(article_id):
    url = f'https://echo.msk.ru/news/{article_id}-echo/comments.html#comments'
    page = requests.get(url)
    results = bsoup(page.text, 'lxml')

    pages_count = 1

    for element0 in results.find_all('div', class_='commentPage'):
        for element1 in element0.find_all('div', class_='pager'):
            pages_count = len(element1.find_all('a'))

    # ### article_id ### #
    List = article_id, [], [], [], [], [], [], []

    for i in range(pages_count):
        url = f'https://echo.msk.ru/elements/e{article_id}/comments_page/{i}.html'
        page = requests.get(url)
        results = bsoup(page.text, 'lxml')

        # ### comment_id ### #
        for element0 in results.find_all('div', class_='commBlock'):
            temp = regular.sub('\D', '', element0.get('id'))
            List[1].append(temp)

        # ### user_id ### #
        for element0 in results.find_all('div', class_='onecomm'):
            temp = element0.get('data-author')
            List[2].append(temp)

        # ### context ### #
        for element0 in results.find_all('p', class_='commtext'):
            temp = regular.sub(r'\s+', ' ', element0.text)
            temp = temp.lstrip(' ')
            List[3].append(temp)

        # ### date & time ### #
        for element0 in results.find_all('span', class_='datetime right'):
            temp = element0.text
            temp = temp.split(" | ")
            # ### date ### #
            List[4].append(temp[0])
            # ### time ### #
            List[5].append(temp[1])

        # ### level & connection ### #
        for element0 in results.find_all('body'):
            for element1 in element0.find_all('div', class_='onecomm'):
                Array = []
                String = str(element1).split(">")[0] + ">"
                Array.append(String)
                Parent = element1.find_parent()
                while Parent.name != 'html':
                    String = str(Parent).split(">")[0] + ">"
                    Array.append(String)
                    Parent = Parent.find_parent()
                Array.reverse()

                # ### level ### #
                List[6].append(str(len(Array) - 2))
                # ### connection ### #
                List[7].append((regular.sub('\D', '', Array[len(Array) - 3])))

        # ### REWRITE IT ### #
        for element0 in results.find_all('div', class_='cmnt-hidden'):
            value = List[2].index(element0.get('data-author'))
            List[1].pop(value)
            List[2].pop(value)
            List[6].pop(value)
            List[7].pop(value)
    return List


def GetProfile(user_id):
    url = f'https://echo.msk.ru/users/{user_id}/'
    page = requests.get(url)
    results = bsoup(page.text, 'lxml')

    # ### user_id ### #
    List = [user_id]

    # ### name & nickname ### #
    for element0 in results.find_all('div', class_='profile'):
        # ### name ### #
        for element1 in element0.find_all('h1'):
            temp = element1.text
            List.append(temp)
        # ### nickname ### #
        for element1 in element0.find_all('b', class_='login'):
            temp = element1.text
            List.append(temp)
        # ### registered_time & recommendations & views ### #
        temp1 = None
        temp2 = None
        for element1 in element0.find_all('div', class_='inf_rating'):
            for element2 in element1.find_all('span'):
                # ### registered_time ### #
                if "на сайте" in element2.text:
                    temp = regular.sub(r'\s+', ' ', element2.text)
                    temp = temp.lstrip(' ')
                    List.append(temp)
                # ### recommendations ### #
                if "рекоменд" in element2.text:
                    temp1 = regular.sub(r'\s+', ' ', element2.text)
                    temp1 = temp1.lstrip(' ')
                    temp1 = temp1[:temp1.find(' ')]
                    List.append(temp1)
                # ### views ### #
                if "просмотр" in element2.text:
                    temp2 = regular.sub(r'\s+', ' ', element2.text)
                    temp2 = temp2.lstrip(' ')
                    temp2 = temp2[:temp2.find(' ')]
                    List.append(temp2)
        if temp1 is None:
            List.append("")
            pass
        if temp2 is None:
            List.append("")
            pass

    url = f'https://echo.msk.ru/users/{user_id}/profile.html'
    page = requests.get(url)
    results = bsoup(page.text, 'lxml')

    # ### occupation & place_of_work & city ### #
    TempList = [[], []]
    for element0 in results.find_all('div', class_='column'):
        for element1 in element0.find_all('dt'):
            TempList[0].append(element1.text)
    for element0 in results.find_all('div', class_='column'):
        for element1 in element0.find_all('dd'):
            TempList[1].append(element1.text)

    try:
        value = TempList[0].index("Род занятий")
        List.append(TempList[1][value])
    except ValueError:
        List.append("")

    try:
        value = TempList[0].index("Место работы")
        List.append(TempList[1][value])
    except ValueError:
        List.append("")

    try:
        value = TempList[0].index("город")
        List.append(TempList[1][value])
    except ValueError:
        List.append("")

    if len(List) == 4:
        for i in range(5):
            List.append("")

    return List


def DB_FirstConnect():
    with sql.connect(DataBasePath) as connect:
        current = connect.cursor()

        current.execute("""CREATE TABLE IF NOT EXISTS articles (
            unique_id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            views_count TEXT NOT NULL,
            comments_count TEXT NOT NULL,
            context TEXT NOT NULL
        )""")

        current.execute("""CREATE TABLE IF NOT EXISTS comments (
            unique_id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id TEXT NOT NULL,
            comment_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            context TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            level TEXT NOT NULL,
            connection TEXT NOT NULL
        )""")

        current.execute("""CREATE TABLE IF NOT EXISTS profiles (
                    unique_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    nickname TEXT NOT NULL,
                    registered_time TEXT NOT NULL,
                    recommendations TEXT NOT NULL,
                    views TEXT NOT NULL,
                    occupation TEXT NOT NULL,
                    place_of_work TEXT NOT NULL,
                    city TEXT NOT NULL
                )""")


def DB_WriteData(List, table):
    if table == "articles":
        with sql.connect(DataBasePath) as connect:
            current = connect.cursor()
            current.execute("INSERT INTO articles (article_id, title, url, date, time, views_count, "
                            "comments_count, context) values(?,?,?,?,?,?,?,?)", (List[0], List[1], List[2],
                                                                                 List[3], List[4], List[5],
                                                                                 List[6], List[7]))
    if table == "comments":
        for i in range(len(List[1])):
            with sql.connect(DataBasePath) as connect:
                current = connect.cursor()
                current.execute(
                    "INSERT INTO comments (article_id, comment_id, user_id, context, date, time, level, "
                    "connection) values(?,?,?,?,?,?,?,?)", (List[0], List[1][i], List[2][i], List[3][i],
                                                            List[4][i], List[5][i], List[6][i], List[7][i]))
    if table == "profiles":
        for i in range(len(List)):
            if not DB_FindProfile(List[i][0]):
                with sql.connect(DataBasePath) as connect:
                    current = connect.cursor()
                    current.execute(
                        "INSERT INTO profiles (user_id, name, nickname, registered_time, recommendations, views, "
                        "occupation, place_of_work, city) values(?,?,?,?,?,?,?,?,?)", (List[i][0], List[i][1],
                                                                                       List[i][2], List[i][3],
                                                                                       List[i][4], List[i][5],
                                                                                       List[i][6], List[i][7],
                                                                                       List[i][8]))


def DB_FindArticle(article_id):
    with sql.connect(DataBasePath) as connect:
        current = connect.cursor()
        current.execute(f'SELECT * FROM articles WHERE article_id == {article_id}')
        result = current.fetchall()
        if not result:
            return False
        else:
            return True


def DB_FindComment(comment_id):
    with sql.connect(DataBasePath) as connect:
        current = connect.cursor()
        current.execute(f'SELECT * FROM comments WHERE comment_id == {comment_id}')
        result = current.fetchall()
        if not result:
            return False
        else:
            return True


def DB_FindProfile(user_id):
    with sql.connect(DataBasePath) as connect:
        current = connect.cursor()
        current.execute(f'SELECT * FROM profiles WHERE user_id == {user_id}')
        result = current.fetchall()
        if not result:
            return False
        else:
            return True


# Do Not Use Now !!!
def ReformatString(string):
    return (regular.sub(r'\s+', ' ', string)).lstrip(' ')

# Web Scraping
Setup()
