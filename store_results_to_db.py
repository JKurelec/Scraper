import ast
from datetime import datetime, timedelta
import mysql.connector
import csv

reg_filename = "regquiz.csv"
res_filename = "resquiz.csv"


def convert_to_datetime(date_str):
    current_year = datetime.now().year

    # Handle keywords for relative dates
    if "Today" in date_str:
        date_str = datetime.now().strftime("%d.%m.") + date_str.split('@')[-1]
    elif "Tomorrow" in date_str:
        tomorrow = datetime.now() + timedelta(days=1)
        date_str = tomorrow.strftime("%d.%m.") + date_str.split('@')[-1]
    elif "Yesterday" in date_str:
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime("%d.%m.") + date_str.split('@')[-1]

    # Handle cases with specific date format including a comma (e.g., "Mon, 08.01. @ 20:00")
    elif "," in date_str:
        # Extract just the date and time parts, ignoring the day abbreviation
        date_part = date_str.split(", ")[1].split(" @ ")[0].strip()
        time_part = date_str.split(" @ ")[1].strip()
        if date_str.count('.') == 2:
            date_str = f"{date_part}{current_year} {time_part}"
        else:
            date_str = f"{date_part} {time_part}"

    # Handle cases with day abbreviations only (e.g., "Fri @ 20:00")
    elif any(day in date_str for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
        day_abbr, time_part = date_str.split(" @ ")
        day_num = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].index(day_abbr)

        today = datetime.now()
        target_date = today + timedelta((day_num - today.weekday() + 7) % 7)
        date_str = target_date.strftime("%d.%m. ") + time_part

    # Add the current year if not present in date_str
    if date_str.count('.') == 2:  # Example: "14.11. @ 20:00"
        date_str = date_str.replace('@', " ")
        date_str = f"{date_str.split('.')[0]}.{date_str.split('.')[1].strip()}.{current_year}. {date_str.split(' ')[-1].strip()}"
    else:
        date_str = date_str.replace("@ ", "")

    # Convert to datetime
    dt = datetime.strptime(date_str, "%d.%m.%Y. %H:%M")
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def read_csv(filename):
    with open(filename, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)
        data = []
        for row in reader:
            data.append(row)
        return data


def store_csv_row_to_db(conn, row):
    cursor = conn.cursor(prepared=True)
    try:
        #HANDLE ORGANIZERS
        select_query = "SELECT * FROM organizers WHERE name = %s"
        select_params = (row[0],)
        cursor.execute(select_query, select_params)
        results = cursor.fetchall()

        if len(results) == 0:
            insert_query = "INSERT INTO organizers (name) VALUES (%s)"
            insert_params = (row[0],)
            cursor.execute(insert_query, insert_params)
            conn.commit()
            print(f"Inserted organizer: {row[0]}")

        #HANDLE LOCATIONS
        select_query = "SELECT * FROM locations WHERE name = %s AND address = %s"
        select_params = (row[7].split('|')[0], row[7].split('|')[1])
        cursor.execute(select_query, select_params)
        results = cursor.fetchall()

        if len(results) == 0:
            insert_query = "INSERT INTO locations (name, address) VALUES (%s, %s)"
            insert_params = (row[7].split('|')[0], row[7].split('|')[1])
            cursor.execute(insert_query, insert_params)
            conn.commit()
            print(f"Inserted location: {row[7].split('|')[0]}, {row[7].split('|')[1]}")

        #HANDLE CATEGORIES
        select_query = "SELECT * FROM category WHERE name = %s"
        select_params = (row[2],)
        cursor.execute(select_query, select_params)
        results = cursor.fetchall()

        if len(results) == 0:
            insert_query = "INSERT INTO category (name) VALUES (%s)"
            insert_params = (row[2],)
            cursor.execute(insert_query, insert_params)
            conn.commit()
            print(f"Inserted category: {row[2]}")

        #HANDLE QUIZ_DURATIONS
        duration = int(row[5].split(" ")[0])
        select_query = "SELECT * FROM quiz_duration WHERE amount = %s"
        select_params = (duration,)
        cursor.execute(select_query, select_params)
        results = cursor.fetchall()

        if len(results) == 0:
            insert_query = "INSERT INTO quiz_duration (amount) VALUES (%s)"
            insert_params = (duration,)
            cursor.execute(insert_query, insert_params)
            conn.commit()
            print(f"Inserted duration: {duration}")

        #HANDLE REGISTRATION_FEES
        if row[3] != "Free":
            amount = float(row[3].split(" ")[0])
            reg_type = 3 if row[3].split(" ")[-1] == 'player' else 2
            select_query = "SELECT * FROM registration_fee WHERE amount = %s AND fee_type = %s"
            select_params = (amount, reg_type)
            cursor.execute(select_query, select_params)
            results = cursor.fetchall()

            if len(results) == 0:
                insert_query = "INSERT INTO registration_fee (amount, fee_type) VALUES (%s, %s)"
                insert_params = (amount, reg_type)
                cursor.execute(insert_query, insert_params)
                conn.commit()
                print(f"Inserted registration fee: {amount}, {reg_type}")

        #HANDLE EDITIONS
        select_query = "SELECT * FROM editions WHERE name = %s AND start_time = %s"
        select_params = (row[1], convert_to_datetime(row[6]))
        cursor.execute(select_query, select_params)
        results = cursor.fetchall()

        if len(results) == 0:
            insert_query = ("INSERT INTO editions (name, organizer, category, start_time, quiz_duration,"
                            "location, min_squad_size, max_squad_size) "
                            "VALUES (%s, (SELECT id FROM organizers WHERE name = %s), (SELECT id FROM category WHERE name = %s), %s,"
                            "(SELECT id FROM quiz_duration WHERE amount = %s), (SELECT id FROM locations WHERE name = %s AND address = %s),"
                            "%s, %s)")
            insert_params = (row[1], row[0], row[2], convert_to_datetime(row[6]), duration, row[7].split('|')[0], row[7].split('|')[1], row[4].split(" ")[0], row[4].split(" ")[-1])
            cursor.execute(insert_query, insert_params)
            conn.commit()
            print(f"Inserted edition: {row[1]}")

            if row[3] != "Free":
                update_query = "UPDATE editions SET registration_fee = (SELECT id FROM registration_fee WHERE amount = %s AND fee_type = %s) WHERE name = %s"
                update_params = (amount, reg_type, row[1])
                cursor.execute(update_query, update_params)
                conn.commit()
            else:
                update_query = "UPDATE editions SET registration_fee = 1"
                cursor.execute(update_query)
                conn.commit()

        squads = ast.literal_eval(row[8])
        if squads[0] == "results":
            #HANDLE SQUADS
            for squad in squads[1:]:
                select_query = "SELECT * FROM squads WHERE name = %s"
                select_params = (" ".join(squad.split(" ")[1:-1]),)
                cursor.execute(select_query, select_params)
                results = cursor.fetchall()

                if len(results) == 0:
                    insert_query = "INSERT INTO squads (name) VALUES (%s)"
                    insert_params = (" ".join(squad.split(" ")[1:-1]),)
                    cursor.execute(insert_query, insert_params)
                    conn.commit()
                    print(f"Inserted squad: {" ".join(squad.split(" ")[1:-1])}")

                #HANDLE RESULTS
                select_query = ("SELECT * FROM results WHERE edition = (SELECT id FROM editions WHERE name = %s AND start_time = %s)"
                                "AND squad = (SELECT id FROM squads WHERE name = %s)")
                select_params = (row[1], convert_to_datetime(row[6]), " ".join(squad.split(" ")[1:-1]))
                cursor.execute(select_query, select_params)
                results = cursor.fetchall()

                if len(results) == 0:
                    insert_query = ("INSERT INTO results (edition, squad, ranking, points) VALUES ((SELECT id FROM editions WHERE name = %s AND start_time = %s),"
                                    "(SELECT id FROM squads WHERE name = %s), %s, %s)")
                    insert_params = (row[1], convert_to_datetime(row[6]), " ".join(squad.split(" ")[1:-1]), int(squad.split(" ")[0]), float(squad.split(" ")[-1]))
                    cursor.execute(insert_query, insert_params)
                    conn.commit()
                    print(f"Inserted results for: {" ".join(squad.split(" ")[1:-1])}")
                else:
                    select_query = (
                        "SELECT * FROM results WHERE edition = (SELECT id FROM editions WHERE name = %s AND start_time = %s)"
                        "AND squad = (SELECT id FROM squads WHERE name = %s) AND points IS NOT NULL")
                    select_params = (row[1], convert_to_datetime(row[6]), " ".join(squad.split(" ")[1:-1]))
                    cursor.execute(select_query, select_params)
                    results = cursor.fetchall()

                    if len(results) == 0:
                        update_query = ("UPDATE results SET ranking = %s, points = %s WHERE edition = (SELECT id FROM editions WHERE name = %s AND start_time = %s) "
                                        "AND squad = (SELECT id FROM squads WHERE name = %s)")
                        update_params = (int(squad.split(" ")[0]), float(squad.split(" ")[-1]), row[1], convert_to_datetime(row[6]), " ".join(squad.split(" ")[1:-1]))
                        cursor.execute(update_query, update_params)
                        conn.commit()
                        print(f"Updated ranking for : {" ".join(squad.split(" ")[1:-1])}")
        else:
            #HANDLE SQUADS
            for squad in squads[1:]:
                select_query = "SELECT * FROM squads WHERE name = %s"
                select_params = (squad,)
                cursor.execute(select_query, select_params)
                results = cursor.fetchall()

                if len(results) == 0:
                    insert_query = "INSERT INTO squads (name) VALUES (%s)"
                    insert_params = (squad,)
                    cursor.execute(insert_query, insert_params)
                    conn.commit()
                    print(f"Inserted squad: {squad}")

                #HANDLE RESULTS
                select_query = ("SELECT * FROM results WHERE edition = (SELECT id FROM editions WHERE name = %s AND start_time = %s)"
                                "AND squad = (SELECT id FROM squads WHERE name = %s)")
                select_params = (row[1], convert_to_datetime(row[6]), squad)
                cursor.execute(select_query, select_params)
                results = cursor.fetchall()

                if len(results) == 0:
                    insert_query = ("INSERT INTO results (edition, squad) VALUES ((SELECT id FROM editions WHERE name = %s AND start_time = %s),"
                                    "(SELECT id FROM squads WHERE name = %s))")
                    insert_params = (row[1], convert_to_datetime(row[6]), squad)
                    cursor.execute(insert_query, insert_params)
                    conn.commit()
                    print(f"Inserted squad registration for: {squad}")

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    finally:
        if cursor:
            cursor.close()


def main():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="quiz_recommendation"
    )

    try:
        reg_data = read_csv(reg_filename)
        for row in reg_data:
            store_csv_row_to_db(conn, row)

        res_data = read_csv(res_filename)
        for row in res_data:
            store_csv_row_to_db(conn, row)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
    # test_dates = [
    #     "Today @ 20:00",
    #     "Tomorrow @ 20:00",
    #     "Yesterday, 12.11. @ 19:30",
    #     "Fri @ 20:00",
    #     "Mon, 08.01. @ 20:00",
    #     "14.11. @ 20:00",
    #     "14.11.2024. @ 20:00"
    # ]
    #
    # for test_date in test_dates:
    #     print(f"{test_date} -> {convert_to_datetime(test_date)}")
