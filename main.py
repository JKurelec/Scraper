from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv

import store_results_to_db

url = 'https://www.quisco.co/quizzes/'
quiz_organizer_class = 'span.sc-a2faa76d-0.cCyssB'
quiz_edition_class = 'span.sc-e6e5baac-0.jjiIqv'
quiz_info_container_class = 'div.sc-53dc0414-0.fPEKRO'
quiz_info_div_class = 'div.sc-53dc0414-0.sc-505f766a-0.bHHNco.gAwQtN'
quiz_info_span_class = 'span.sc-a2faa76d-0.ieWKqb'
quiz_pub_span_class = 'span.sc-a2faa76d-0.hpNqMy'
quiz_address_span_class = 'span.sc-a2faa76d-0.kxwenS'
div_selector_class = 'div.sc-53dc0414-0.sc-505f766a-0.sc-7b394a83-0.bmxSZk.gDkoJh.dsmcBj'
results_or_registered_class = "span.sc-a2faa76d-0.dXxGYO.text"
quiz_capacity_div_class = 'div.sc-53dc0414-0.sc-505f766a-0.ificfc.dzZZmJ'
capacity_class = 'span.sc-a2faa76d-0.cBvpvC'
main_container_class = 'div.sc-53dc0414-0.eKFHqu'
items_class = 'div.sc-53dc0414-0.sc-505f766a-0.eJdapY.iHUgAB'
first_element_class = 'div.sc-53dc0414-0.sc-505f766a-0.gGRFtA.dzZZmJ'
first_span_class = 'span.sc-a2faa76d-0.hCwffr'
second_element_class = 'div.sc-53dc0414-0.sc-505f766a-0.cmGtso.dzZZmJ'
second_span_class = 'span.sc-a2faa76d-0.dAsCiR'
results_table_class = 'table.sc-dbb7b6ea-0.bKJnLi'

quizzes_with_data = 0
quizzes_all = 0


def configure_driver(headless=True):
    options = Options()
    options.headless = headless
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver


def get_quiz_organizer(driver):
    quiz_organizer_span = WebDriverWait(driver, 1).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, quiz_organizer_class))
    )
    return quiz_organizer_span.text


def get_quiz_info(driver):
    quiz_edition_span = WebDriverWait(driver, 1).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, quiz_edition_class))
    )
    quiz_edition = quiz_edition_span.text

    quiz_info_container = WebDriverWait(driver, 1).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, quiz_info_container_class))
    )
    quiz_info_divs = quiz_info_container.find_elements(By.CSS_SELECTOR, quiz_info_div_class)
    category = quiz_info_divs[0].find_element(By.CSS_SELECTOR, quiz_info_span_class).text
    if len(quiz_info_divs) > 6:
        registration_fee = quiz_info_divs[1].find_element(By.CSS_SELECTOR, quiz_info_span_class).text
        # squad_type = quiz_info_divs[2].find_element(By.CSS_SELECTOR, quiz_info_span_class).text
        squad_member_count = quiz_info_divs[3].find_element(By.CSS_SELECTOR, quiz_info_span_class).text
        length = quiz_info_divs[4].find_element(By.CSS_SELECTOR, quiz_info_span_class).text
        start_time = quiz_info_divs[5].find_element(By.CSS_SELECTOR, quiz_info_span_class).text
    else:
        registration_fee = "N/A"
        # squad_type = quiz_info_divs[1].find_element(By.CSS_SELECTOR, quiz_info_span_class).text
        squad_member_count = quiz_info_divs[2].find_element(By.CSS_SELECTOR, quiz_info_span_class).text
        length = quiz_info_divs[3].find_element(By.CSS_SELECTOR, quiz_info_span_class).text
        start_time = quiz_info_divs[4].find_element(By.CSS_SELECTOR, quiz_info_span_class).text

    quiz_address_span = WebDriverWait(driver, 1).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, quiz_address_span_class))
    )
    address = quiz_address_span.text

    quiz_pub_span = WebDriverWait(driver, 1).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, quiz_pub_span_class))
    )
    pub = quiz_pub_span.text

    location = f"{pub}|{address}"
    # return quiz_edition, category, registration_fee, squad_type, squad_member_count, length, start_time, location
    return quiz_edition, category, registration_fee, squad_member_count, length, start_time, location


def get_registered_squads(squads, driver):
    squads.append("registered")
    # quiz_capacity_div = WebDriverWait(driver, 1).until(
    #     EC.presence_of_element_located((By.CSS_SELECTOR, quiz_capacity_div_class))
    # )
    # capacity = quiz_capacity_div.find_elements(By.CSS_SELECTOR, capacity_class)[1].text

    try:
        show_all_button = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button.sc-514720fb-0.iXaxRq'))
        )
        if show_all_button.is_displayed():
            show_all_button.click()  # Click the button if it's present
    except Exception:
        pass

    main_container = WebDriverWait(driver, 1).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, main_container_class))
    )
    items = main_container.find_elements(By.CSS_SELECTOR, items_class)

    for item in items:
        first_element = item.find_element(By.CSS_SELECTOR, first_element_class)
        squad_name = first_element.find_element(By.CSS_SELECTOR, first_span_class).text
        second_element = item.find_element(By.CSS_SELECTOR, second_element_class)
        second_span = second_element.find_element(By.CSS_SELECTOR, second_span_class).text
        member_count = second_span.split(":")[1].strip()
        squads.append(squad_name + " " + member_count)

    return squads


def get_results_squads(squads, driver):
    squads.append("results")
    results_table = WebDriverWait(driver, 1).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, results_table_class))
    )
    results_body = results_table.find_element(By.TAG_NAME, 'tbody')
    rows = results_body.find_elements(By.TAG_NAME, 'tr')

    for row in rows:
        cells = row.find_elements(By.TAG_NAME, 'td')
        cell_data = ""
        for cell in cells:
            cell_text = cell.text.strip()
            if cell_text:
                cell_data += cell_text + " "
        squads.append(cell_data.strip())

    total_points = results_table.find_element(By.TAG_NAME, 'tfoot')
    total_points_row = total_points.find_elements(By.TAG_NAME, 'tr')[1]
    total_points_final = total_points_row.find_elements(By.TAG_NAME, 'th')[-1].text
    final = total_points_final.split(" ")[-1]
    if float(squads[1].split(" ")[-1]) > float(final):
        squads.append("0")
    else:
        squads.append(final)

    return squads


def get_squads_info(squads, driver):
    div_selector = WebDriverWait(driver, 1).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, div_selector_class))
    )
    div_selector.click()

    if div_selector.find_element(By.CSS_SELECTOR, results_or_registered_class).text.lower() == 'prijavljeni':
        return get_registered_squads(squads, driver)
    else:
        return get_results_squads(squads, driver)


def scrape_data(driver, url):
    driver.get(url)
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
        quiz_organizer = get_quiz_organizer(driver)
        # quiz_edition, category, registration_fee, squad_type, squad_member_count,length, start_time, location = get_quiz_info(driver)
        quiz_edition, category, registration_fee, squad_member_count, length, start_time, location = get_quiz_info(driver)
        squads = get_squads_info(squads, driver)
        print(f"Data fetched from {quiz_edition} by {quiz_organizer}")
        global quizzes_with_data
        quizzes_with_data = quizzes_with_data + 1
    except Exception:
        print(f"Cant fetch data from {url}")
    global quizzes_all
    quizzes_all = quizzes_all + 1
    return quiz_organizer, quiz_edition, category, registration_fee, squad_member_count, length, start_time, location, squads


def main():
    driver = configure_driver()
    reg_filename = "regquiz.csv"
    res_filename = "resquiz.csv"

    with open(reg_filename, mode='w', newline='\n', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Organizer", "Edition", "Category", "Registration Fee", "Squad Member Count", "Length", "Start Time", "Location", "Squads"])

    with open(res_filename, mode='w', newline='\n', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Organizer", "Edition", "Category", "Registration Fee", "Squad Member Count", "Length", "Start Time", "Location", "Squads", "Total points"])

    numbers = [i for i in range(0, 1700) if i != 585]
    for i in numbers:
        quiz_organizer, quiz_edition, category, registration_fee, squad_member_count, length, start_time, location, squads = scrape_data(driver, url + str(i))
        if len(squads) > 3:
            if squads[0] == "registered":
                with open(reg_filename, mode='a', newline='\n', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow([quiz_organizer, quiz_edition, category, registration_fee, squad_member_count, length, start_time, location, squads])
            else:
                with open(res_filename, mode='a', newline='\n', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    total_points = squads.pop(-1)
                    writer.writerow([quiz_organizer, quiz_edition, category, registration_fee, squad_member_count, length, start_time, location, squads, total_points])

    driver.quit()
    print(f"Quizzes with data: {(quizzes_with_data/quizzes_all)*100}%")
    store_results_to_db.main()


if __name__ == "__main__":
    main()
