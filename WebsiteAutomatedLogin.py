#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 17 21:58:51 2023

@author: calebwharton
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import yaml
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotInteractableException

def main():
    all_students_available_hours = get_all_students_available_hours()
    display_hangout_hours(all_students_available_hours)
    
def display_hangout_hours(all_students_available_hours):
    hangout_times = find_hangout_times(all_students_available_hours)
    (total_hangout_hours, days_hangout_hours) = find_total_hangout_hours(hangout_times)
    hangout_periods = get_hangout_periods(hangout_times)
    am_pm_time_hangout_periods = convert_hangout_period_ampm(hangout_periods)
    print_hangout_times(am_pm_time_hangout_periods, total_hangout_hours, days_hangout_hours)    
    
def get_all_students_available_hours():
    all_students_available_hours = {}
    number_of_students = get_number_students()
    which_semester = semester_view()
    for i in range(number_of_students):
        available_hours = free_hours()
        (timetable_element, driver) = get_student_data(which_semester)
        busy_hours = sort_data(timetable_element, driver)
        find_available_hours(busy_hours, available_hours)
        all_students_available_hours[f"student{i}"] = available_hours
    return all_students_available_hours
    
def get_student_data(which_semester):
        conf = load_yaml()
        sso_tuple = get_user_sso_input()
        update_yaml(sso_tuple, conf)
        write_update_yaml(conf)
        driver = webdriver.Chrome()
        timetable_element = run_data_grab(sso_tuple, driver, which_semester)
        return (timetable_element, driver)

def sort_data(timetable_element, driver):
    sort_hours_dict = sort_taken_hours(timetable_element)
    driver.quit()
    busy_hours = convert_times(sort_hours_dict)
    return busy_hours

def find_available_hours(busy_hours, available_hours):
    remove_busy_hours(busy_hours, available_hours)

def run_data_grab(sso_tuple, driver, which_semester):
    login_sso = ""
    manage = False 
    sem_view = False
    timetable_element = False
    format_change = False
    while login_sso != True: 
        if login_sso == False:
            conf = load_yaml()
            sso_tuple = retry_get_user_sso_input()
            update_yaml(sso_tuple, conf)
            write_update_yaml(conf)     
        login_sso = login("http://www.student.auckland.ac.nz/", "email", sso_tuple[0], 
                      "pass", sso_tuple[1], "loginbutton", driver)
    while manage is False:
        manage = click_manage_classes(driver)
    while sem_view is False:
        sem_view = view_sem(which_semester, driver)
    while format_change is False:
        format_change = change_format(driver)
    while timetable_element is False:
        timetable_element = grab_data(driver)
    return (timetable_element)

def get_number_students():
    number_of_students = ""
    while number_of_students.isdigit() == False:
        number_of_students = input("How many student's timetables \
                                   are you comparing: ")
    return int(number_of_students)

def free_hours():
    default_day = {"Monday" : [9, 10, 11, 12, 13, 14, 15, 16, 17],
                   "Tuesday" : [10, 11, 12, 13, 14, 15, 16, 17],
                   "Wednesday" : [10, 11, 12, 13, 14, 15, 16, 17],
                   "Thursday" : [10, 11, 12, 13, 14, 15, 16, 17],
                   "Friday" : [10, 11, 12, 13, 14, 15, 16, 17]}               
    day_dict = {"Monday" : [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 
                        14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24],
                "Tuesday" : [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 
                        14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24],
                "Wednesday" : [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 
                        14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24], 
                "Thursday" : [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,
                        14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24],
                "Friday" : [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,
                        14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]}
    default_or_custom = ""
    individual_or_same = ""
    while default_or_custom != "yes" and default_or_custom != "no":
        default_or_custom = input("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nDefault day length: 10am - 6pm\nAre you happy with this (yes/no): ").strip().lower()
    if default_or_custom == "no":
        while individual_or_same != "all" and individual_or_same != "individually":
            individual_or_same = input("Would you like to set the \
time for all days or set each individually (all/individual): ").strip().lower()
        if individual_or_same == "individual":
            for entry in day_dict:
                custom_each_day(entry, day_dict)
        elif individual_or_same == "all":
            custom_all_days(day_dict)
        return day_dict
                
    else:
        return default_day
    
def convert_24_hour(start_time, end_time):
    start_hour = int(start_time[:-2])  
    end_hour = int(end_time[:-2]) 
    
    # Determine if the time is in the morning or afternoon
    if start_time[-2:] == 'am' and start_hour == 12:
        start_hour = 0  # 12am is equivalent to 0 hour in 24-hour format
    elif start_time[-2:] == 'pm' and start_hour != 12:
        start_hour += 12  # Add 12 to convert from afternoon to 24-hour format

    if end_time[-2:] == 'am' and end_hour == 12:
        end_hour = 0  # 12am is equivalent to 0 hour in 24-hour format
    elif end_time[-2:] == 'pm' and end_hour != 12:
        end_hour += 12  # Add 12 to convert from afternoon to 24-hour format
    end_hour -= 1
    return (start_hour, end_hour)
    
def custom_each_day(entry, day_dict):
    confirm = ""
    while confirm != "yes":
        (start_time, end_time) = correct_start_end(entry)
        (start, end) = convert_24_hour(start_time, end_time)
        confirm = input(f"Type yes to confirm your start time for {entry} \
is {start_time} and you end time is {end_time}: ").strip().lower()
    for i in range(day_dict[entry].index(start)):
        day_dict[entry].pop(0)
    for i in range(len(day_dict[entry]) - day_dict[entry].index(end) - 1):
        day_dict[entry].pop(-1)
        
def custom_all_days(day_dict):
    confirm = ""
    while confirm != "yes":
        (start_time, end_time) = correct_start_end_all_days()
        (start, end) = convert_24_hour(start_time, end_time)
        confirm = input(f"Type yes to confirm your start time for everyday \
is {start_time} and you end time is {end_time}: ").strip().lower()
    for entry in day_dict:
        for i in range(day_dict[entry].index(start)):
            day_dict[entry].pop(0)
        for i in range(len(day_dict[entry]) - day_dict[entry].index(end) - 1):
            day_dict[entry].pop(-1)
    
def correct_start_end(entry):
    start_time = "   "
    end_time = "    "
    while (start_time[0].isdigit() == False or
           (len(start_time) != 4 and len(start_time) != 3) or 
           start_time[-1] != "m" or start_time[-2].isalpha() == False or 
           (start_time[0].isdigit() == False and start_time[0] != "a" 
            and start_time[0] != "p")): 
        start_time = input(f"What time does your {entry} start (format __am/pm): ")
    while (end_time[0].isdigit() == False or 
            (len(end_time) != 4 and len(end_time) != 3) or 
            end_time[-1] != "m" or end_time[-2].isalpha() == False or 
                   (len(end_time) != 4 and len(end_time) != 3) or 
                   end_time[-1] != "m" or end_time[-2].isalpha() == False or 
                   (end_time[0].isdigit() == False and end_time[0] != "a" 
                    and end_time[0] != "p")): 
         end_time = input("What time does your day end (format __am/pm): ")
    return (start_time, end_time)

def correct_start_end_all_days():
    start_time = "   "
    end_time = "    "
    while (start_time[0].isdigit() == False or
           (len(start_time) != 4 and len(start_time) != 3) or 
           start_time[-1] != "m" or start_time[-2].isalpha() == False or 
           (start_time[0].isdigit() == False and start_time[0] != "a" 
            and start_time[0] != "p")): 
        start_time = input("What time does your day start (format __am/pm): ")
    while (end_time[0].isdigit() == False or 
           (len(end_time) != 4 and len(end_time) != 3) or 
           end_time[-1] != "m" or end_time[-2].isalpha() == False or 
           (end_time[0].isdigit() == False and end_time[0] != "a" 
            and end_time[0] != "p")): 
         end_time = input("What time does your day end (format __am/pm): ")
    return (start_time, end_time)

def load_yaml():
#load yaml
    with open('loginDetails.yml', 'r') as file:
        conf = yaml.safe_load(file)
        return conf

def get_user_sso_input():
# Get user input for sso_email and sso_password
    sso_email = input("Enter your SSO email: ")
    sso_password = input("Enter your SSO password: ")
    return (sso_email, sso_password)

def retry_get_user_sso_input():
    # Get user input for sso_email and sso_password
    print("Your SSO email or password is incorrect, please re-enter")
    sso_email = input("Enter your SSO email: ")
    sso_password = input("Enter your SSO password: ")
    return (sso_email, sso_password)

def semester_view():
#Check which semester user wants to view, and forces to pick one or two
    which_semester = 0
    while which_semester != 1 and which_semester != 2:
        which_semester = int(input("Would you like to view semester 1 or 2? "))
    return which_semester

def update_yaml(sso_tuple, conf):
# Update the YAML file with the user input
    conf['sso_login']['sso_email'] = sso_tuple[0]
    conf['sso_login']['sso_password'] = sso_tuple[1]

def write_update_yaml(conf):
# Write the updated YAML to file
    with open('loginDetails.yml', 'w') as file:
        yaml.dump(conf, file)

def login(url, username, j_username, password, j_password, _eventId_proceed, driver):
   try:
       driver.get(url)
       driver.find_element(By.ID, "username").send_keys(j_username)
       driver.find_element(By.ID, "password").send_keys(j_password)
       driver.find_element(By.ID, "_eventId_proceed").click()
       try:
           driver.find_element(By.ID, "_eventId_proceed").click()
           return False
       except NoSuchElementException:   
           return True
   except TimeoutException or ElementNotInteractableException:
       return False

def click_manage_classes(driver):
    try:
        wait = WebDriverWait(driver, 5)
        timetable = wait.until(EC.presence_of_element_located((By.ID, "win0divPTNUI_LAND_REC_GROUPLET$11")))
        timetable.click()
        return True
    except TimeoutException or ElementNotInteractableException:
        return False

def view_sem(which_semester, driver):
#View either sem 1 or sem 2 based on earlier user input
    try:
        if which_semester == 1:
            #Open sem 1 tab
            wait = WebDriverWait(driver, 5)
            sem_one = wait.until(EC.presence_of_element_located((By.ID, "SSR_ENTRMCUR_VW_TERM_DESCR30$0")))
            sem_one.click()

        elif which_semester == 2:   
            #Open sem 2 tab
            wait = WebDriverWait(driver, 5)
            sem_two = wait.until(EC.presence_of_element_located((By.ID, "SSR_ENTRMCUR_VW_TERM_DESCR30$1")))
            sem_two.click()
        return True
    except TimeoutException or ElementNotInteractableException:
        return False
    
def change_format(driver):
    try:
#change to date list 
        wait = WebDriverWait(driver, 5)
        sem_two = wait.until(EC.presence_of_element_located((By.ID, "DERIVED_SSR_FL_SSR_VW_CLSCHD_OPT$81$_LBL")))
        sem_two.click()
        return True
    except TimeoutException or ElementNotInteractableException:
        return False

def grab_data(driver):
    try:
        wait = WebDriverWait(driver, 5)
        timetable_element = wait.until(EC.presence_of_element_located((By.ID, "win5div$ICField$7$")))
        return timetable_element
    except TimeoutException or ElementNotInteractableException:
        return False
  
def sort_taken_hours(timetable_element):
    day_dict = {"Monday" : [], "Tuesday" : [], "Wednesday" : [], "Thursday" : [], "Friday" : []}
    timetable_data = timetable_element.text.split('\n')
    for row in timetable_data:
        for entry in day_dict: 
            if entry[0] + entry[1] in row and len(row) == 16:
                row = list(row)
                row.pop(0)
                row.pop(0)
                row.pop(0)
                row = "".join(row)
                day_dict[entry].append(row)
    return day_dict
                
def convert_times(sort_hours_dict):
    busy_hours_dict = {"Monday" : [], "Tuesday" : [], "Wednesday" : [], "Thursday" : [], "Friday" : []}
    for entry in sort_hours_dict:
        for time in sort_hours_dict[entry]:
            busy_times = []
            (start_time, end_time) = time_formator(time)
            between_hours = end_time - start_time
            for i in range(between_hours):
                busy_times.append(start_time + i)
            busy_hours_dict[entry] = busy_hours_dict[entry] + busy_times
        busy_hours_dict[entry].sort()
    return busy_hours_dict
            
def time_formator(time):
    time = time.split(" - ")
    start_time = list(time[0])
    start_time.pop(-1)
    start_time.pop(-1)
    start_time.pop(-1)
    start_time = int("".join(start_time))
    end_time = list(time[1])
    end_time.pop(-1)
    end_time.pop(-1)
    end_time.pop(-1)
    end_time = int("".join(end_time))
    return (start_time, end_time)

def remove_busy_hours(busy_hours, available_hours):
    for day in available_hours:
        index_corrector = 0
        for i in range(len(available_hours[day])):
             if available_hours[day][i + index_corrector] in busy_hours[day]:
                available_hours[day].remove(available_hours[day][i + index_corrector])
                index_corrector -= 1
 
def find_hangout_times(all_students_available_hours):
    hangout_hours = {"Monday" : [], "Tuesday" : [], "Wednesday" : [], "Thursday" : [], "Friday" : []}
    for day in all_students_available_hours["student0"]:
        for hour in all_students_available_hours["student0"][day]:
            students_free = 0
            for entry in all_students_available_hours:
                   if hour in all_students_available_hours[entry][day]:
                       students_free += 1
            if students_free == len(all_students_available_hours):
                hangout_hours[day].append(hour)
    return hangout_hours
 
def find_total_hangout_hours(hangout_times):
    days = {"Monday" : [], "Tuesday" : [], "Wednesday" : [], "Thursday" : [], "Friday" : []}
    total = 0
    for day in days:
        days[day] = len(hangout_times[day])
    for day in days:
        total += days[day]
    return (total, days)
    
def get_hangout_periods(hangout_times):  
    print(hangout_times)
    all_hangout_periods = {"Monday" : [], "Tuesday" : [], "Wednesday" : [], "Thursday" : [], "Friday" : []}
    for day in hangout_times:
        hangout_periods = []
        start_hour = hangout_times[day][0]
        for i in range(len(hangout_times[day])):
            try:
                if hangout_times[day][i] + 1 != hangout_times[day][i + 1]:
                    hangout_periods.append([start_hour, hangout_times[day][i] + 1])
                    start_hour = hangout_times[day][i + 1]
            except IndexError:
                hangout_periods.append([start_hour, hangout_times[day][i] + 1])
        all_hangout_periods[day] += (hangout_periods)
    return all_hangout_periods
 
def convert_hangout_period_ampm(hangout_periods):
    converted_hangout_period = {"Monday" : [], "Tuesday" : [], "Wednesday" : [], "Thursday" : [], "Friday" : []}
    for day in hangout_periods:
        for pair in hangout_periods[day]:
            new_pair = []
            for hour in pair:
                if hour == 0:
                    hour = "12am"
                elif hour > 12:
                    hour = f"{hour - 12}pm"
                else:
                    hour = f"{hour}am"
                new_pair.append(hour)
            converted_hangout_period[day].append(new_pair)
    return converted_hangout_period
        
def print_hangout_times(am_pm_time_hangout_periods, total_hangout_hours, days_hangout_hours):
    for day in am_pm_time_hangout_periods:
        print(f"On {day}s you have time to hangout:")
        for entry in am_pm_time_hangout_periods[day]:   
            print(f"From {entry[0]} to {entry[1]}")
        print(f"\nTotal available hours on {day}: {str(days_hangout_hours[day])} hours\n")
    print(f"\nTotal Available hours during the week: {str(total_hangout_hours)} hours")

main()