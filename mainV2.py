import csv
import re
import time
from bs4 import BeautifulSoup
from selenium import webdriver

quizzes_with_data = 0
quizzes_all = 0
url = "https://www.quisco.co/quizzes/"


def get_registrations(registration_list):
    registrations = []
    for squad in registration_list:
        registrations.append(squad)
    return registrations


def get_results(results_list):
    results = ["results"]
    squad = ""
    for i, result in enumerate(results_list, start=0):
        if i % 3 == 0:
            squad = result
        if i % 3 == 1:
            squad += f" {result}"
        if i % 3 == 2:
            results.append(squad + f" {result}")
    return results


def get_squad_info(squad_list, regres):
    if regres == "Waiting list":
        squads = get_registrations(squad_list)
    else:
        squads = get_results(squad_list)
    if len(squads) == 0:
        raise Exception("No results found")
    else:
        return squads


def get_quiz_info(info_list):
    for i, info in enumerate(info_list, start=0):
        if i == 0:
            quiz_edition = info
        elif info == "Results" or info == "Registrations":
            quiz_organizer = info_list[i + 1]
        elif info == "Category":
            category = info_list[i + 1]
        elif info == "Entry fee":
            entry_fee = info_list[i + 1]
        elif info == "Type":
            entry_type = info_list[i + 1]
        elif info == "Team members":
            squad_size = info_list[i + 1]
        elif info == "Duration":
            duration = info_list[i + 1]
        elif info == "Start":
            start = info_list[i + 1]
        elif info == "Location":
            location = f"{info_list[i + 1]}|{info_list[i + 2]}"
            return quiz_edition, quiz_organizer, category, entry_fee, squad_size, duration, start, location


def scrape_data(driver, url):
    driver.get(url)
    time.sleep(0.5)
    html_content = driver.page_source
    soup = BeautifulSoup(html_content, 'html.parser')
    spans = soup.find_all('span')
    pattern = r"^(Today|Tomorrow|Yesterday|[A-Za-z]{3})(,? \d{2}\.\d{2}(\.\d{4})?\.?)? @ \d{2}:\d{2}$"

    info_list = []
    squad_list = []
    i_start = 0
    i_stop = 0
    r_start = 0
    r_stop = 0
    regres = ""

    for index, span in enumerate(spans, start=0):
        if re.match(pattern, span.text.strip()) and index < 20:
            i_start = index - 1
        elif span.text.strip() == "Location":
            i_stop = index + 3
            info_list = [span.text.strip() for span in spans[i_start:i_stop]]
        elif span.text.strip() == "Waiting list" or span.text.strip() == "Results":
            regres = span.text.strip()
            r_start = index + 1
        elif span.text.strip() == "Visit us" and r_start != 0:
            r_stop = index
            squad_list = [span.text.strip() for span in spans[r_start:r_stop]]
            break

    quiz_organizer = ""
    quiz_edition = ""
    category = ""
    registration_fee = ""
    squad_member_count = ""
    length = ""
    start_time = ""
    location = ""
    squads = []
    try:
        quiz_edition, quiz_organizer, category, registration_fee, squad_member_count, length, start_time, location = get_quiz_info(info_list)
        squads = get_squad_info(squad_list, regres)
        print(f"Data fetched from {quiz_edition} by {quiz_organizer}")
        global quizzes_with_data
        quizzes_with_data = quizzes_with_data + 1
    except Exception:
        print(f"Cant fetch data from {url}")
    global quizzes_all
    quizzes_all = quizzes_all + 1
    return quiz_organizer, quiz_edition, category, registration_fee, squad_member_count, length, start_time, location, squads, regres


def main():
    driver = webdriver.Chrome()
    reg_filename = "regquiz.csv"
    res_filename = "resquiz.csv"

    with open(reg_filename, mode='w', newline='\n', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Organizer", "Edition", "Category", "Registration Fee", "Squad Member Count", "Length", "Start Time", "Location", "Squads"])

    with open(res_filename, mode='w', newline='\n', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Organizer", "Edition", "Category", "Registration Fee", "Squad Member Count", "Length", "Start Time", "Location", "Squads"])

    numbers = [i for i in range(0, 1800) if i != 585]
    for i in numbers:
        quiz_organizer, quiz_edition, category, registration_fee, squad_member_count, length, start_time, location, squads, regres = scrape_data(driver, url + str(i))
        if len(squads) > 3:
            if regres == "Waiting list":
                with open(reg_filename, mode='a', newline='\n', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow([quiz_organizer, quiz_edition, category, registration_fee, squad_member_count, length, start_time, location, squads])
            else:
                with open(res_filename, mode='a', newline='\n', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow([quiz_organizer, quiz_edition, category, registration_fee, squad_member_count, length, start_time, location, squads])

    driver.quit()
    print(f"Quizzes with data: {(quizzes_with_data/quizzes_all)*100}%")
    #store_results_to_db.main()


if __name__ == "__main__":
    main()
