import requests
import csv
import json
import re
import pytz
import pandas as pd 
from dotenv import load_dotenv
from datetime import datetime, timedelta
from config import NotionApiKeyConfig, DatabaseIdConfig
from pymongo import MongoClient

#Setting time
today = datetime.today()
first_day_of_current_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)    
last_month = first_day_of_current_month - timedelta(days=1)
previous_month_25_filter = last_month.replace(day=25).isoformat()
first_day_of_previous_month_filter = last_month.replace(day=1).isoformat()

class NotionApi:
    def __init__(self):
        load_dotenv()
        self.notion_api_key = NotionApiKeyConfig.NOTION_API_KEY
        self.database_ids = [
            DatabaseIdConfig.DATA_ANALYSIS_DATABASE_ID,
            DatabaseIdConfig.DESIGN_DATABASE_ID,
            # DatabaseIdConfig.FRONTEND_DATABASE_ID,
            # DatabaseIdConfig.AI_DATABASE_ID,
            # DatabaseIdConfig.BACKEND_DATABASE_ID,
            # DatabaseIdConfig.TRADING_DATABASE_ID,
            # DatabaseIdConfig.TRAVA_DATABASE_ID,
            # DatabaseIdConfig.CENTIC_DATABASE_ID,
            # DatabaseIdConfig.MAZIG_DATABASE_ID,
            # DatabaseIdConfig.TCV_DATABASE_ID,
            # DatabaseIdConfig.ORCHAI_DATABASE_ID,
            # DatabaseIdConfig.THORN_DATABASE_ID,
            # DatabaseIdConfig.TRUFY_DATABASE_ID, 
            # DatabaseIdConfig.DEVOPS_DATABASE_ID, 
            # DatabaseIdConfig.LOOMIX_DATABASE_ID, 
            # DatabaseIdConfig.STABLE_AI_AGENT_DATABASE_ID, 
        ]
        
    def get_api_headers(self, database_id):  
        headers = {
            'Authorization': f'Bearer {self.notion_api_key}',
            'Content-Type': 'application/json',
            'Notion-Version': '2021-05-13'
        }

        url = f'https://api.notion.com/v1/databases/{database_id}/query'

        data_filter = {
            "filter": {
                "property": "Time",
                "formula": {
                    "date": {
                        "on_or_after": first_day_of_previous_month_filter
                    }
                }
            }
        }
        return headers, url, data_filter  
        
    def get_notion_tasks_data(self, database_id):
        headers, url, data_filter = self.get_api_headers(database_id)
        tasks = []
        
        while True:
            response = requests.post(url, headers=headers, json=data_filter)
            
            if response.status_code == 200:
                response_data = response.json()
                results = response_data['results']
                
                for task in results:
                    end_time_data = task.get("properties", {}).get("Time", {}).get("date", {}).get("end", "")
                    status = task.get("properties", {}).get("Status", {}).get("status", {}).get("name", "")
                    assignees = task.get("properties", {}).get("Assignee", {}).get("people", [])
                    
                    if end_time_data and status == "Done" and assignees:
                        tasks.append(task)

                if "next_cursor" in response_data and response_data["next_cursor"] is not None:
                    data_filter["start_cursor"] = response_data["next_cursor"]
                else:
                    break
            else:
                print(f"Error: {response.status_code}, {response.text}")
                break
        
        return tasks

    #Summary of assignee
    def get_assignees(self, database_id):
        headers, url, data_filter = self.get_api_headers(database_id)
        assignees = set()  
        assignees_mapping = {}

        while True:
            response = requests.post(url, headers=headers, json=data_filter)
            if response.status_code == 200:
                response_data = response.json()
                tasks = response_data['results'] 
                
                for task in tasks:
                    assignee_list = task.get("properties", {}).get("Assignee", {}).get("people", [])
                    for assignee in assignee_list:
                        assignees.add(assignee['id'])
                        if assignee['id'] not in assignees_mapping:
                            assignees_mapping[assignee['id']] = assignee['name']

                if "next_cursor" in response_data and response_data["next_cursor"] is not None:
                    data_filter["start_cursor"] = response_data["next_cursor"]
                else:
                    break
            else:
                print(f"Error: {response.status_code}, {response.text}")
                break

        return assignees, assignees_mapping
 
    def work_matching(self, tasks, assignees, assignee_counts):
        #Setup time in the month
        today = datetime.today()
        today = today.replace(hour=23, minute=59, second=59, microsecond=999999)
        first_day_of_current_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)    
        last_month = first_day_of_current_month - timedelta(days=1)
        first_day_of_previous_month = last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        for task in tasks:    
            #From beginning of the month to present day
            if task.get("properties", {}).get("Time", {}):
                date_end = task.get("properties", {}).get("Time", {}).get("date", {}).get("end", "") 
                    
                if date_end:
                    date_end = datetime.fromisoformat(date_end)
                    
                    #Setup timezone
                    if date_end.tzinfo is not None:
                        date_end = date_end.replace(tzinfo=None)

                    if first_day_of_current_month.tzinfo is not None:
                        first_day_of_current_month = first_day_of_current_month.replace(tzinfo=None)

                    if today.tzinfo is not None:
                        today = today.replace(tzinfo=None)

                    if first_day_of_previous_month <= date_end <= today:
                        #Task status "done"
                        if task.get("properties", {}).get("Status", {}).get("status", {}).get("name", {}) in ["Done"]:    
                            #Count task for each assignee
                            if task.get("properties", {}).get("Assignee", {}).get("people", []):
                                peoples = task.get("properties", {}).get("Assignee", {}).get("people", [])
                                for people in peoples:
                                    assignee = people.get("id", {})
                                   
                                    if assignee in assignees:
                                        assignee_counts[assignee] += 1
                                        
        return assignee_counts

    #Average time working over tasks
    def convert_to_iso_format(self, datetime_str, hour, minute):
        iso_format_regex = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{2}:\d{2}$"
        
        if datetime_str is None:
            datetime_str = "2100-01-01"
            print("Time convert error")
        
        if re.match(iso_format_regex, datetime_str):
            #True format
            dt = datetime.fromisoformat(datetime_str)
            return dt.replace(tzinfo=None)
        else:
            #Wrong format
            dt = datetime.strptime(datetime_str, "%Y-%m-%d") 
            dt = dt.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return dt

    def working_times_over_tasks(self, tasks, assignees, assignee_counts):
        total_work_time_per_assignee = {assignee: timedelta(0) for assignee in assignees}
        work_start_time = datetime.strptime("08:30:00", "%H:%M:%S").time()
        work_end_time = datetime.strptime("18:00:00", "%H:%M:%S").time()
        lunch_start = datetime.strptime("12:00:00", "%H:%M:%S").time()
        lunch_end = datetime.strptime("13:30:00", "%H:%M:%S").time()

        for task in tasks:
            if task.get("properties", {}).get("Time", {}):
                date_start_str = task.get("properties", {}).get("Time", {}).get("date", {}).get("start", "")
                date_end_str = task.get("properties", {}).get("Time", {}).get("date", {}).get("end", "")
                
                if date_start_str and date_end_str:
                    date_start = self.convert_to_iso_format(date_start_str, 8, 30)
                    date_end = self.convert_to_iso_format(date_end_str, 8, 30)
                    #Working time per task
                    work_duration = timedelta(0)
                    
                    current_day = date_start.date()
                    while current_day <= date_end.date():
                        start_of_day = datetime.combine(current_day, work_start_time)
                        end_of_day = datetime.combine(current_day, work_end_time)
                        
                        #First day
                        if current_day == date_start.date():
                            task_start = max(date_start, start_of_day)
                        else:
                            task_start = start_of_day

                        #Last day
                        if current_day == date_end.date():
                            task_end = min(date_end, end_of_day)
                        else:
                            task_end = end_of_day

                        #Task done in day but don't have exactly time
                        if date_start == date_end:
                            task_start = start_of_day
                            task_end = date_end = self.convert_to_iso_format(date_end_str, 18, 0)

                        #Error start time > end time
                        if task_start >= task_end:
                            current_day += timedelta(days=1)
                            continue

                        if task_start.time() < lunch_end and task_end.time() > lunch_start:
                            overlap_start = max(task_start, datetime.combine(current_day, lunch_start))
                            overlap_end = min(task_end, datetime.combine(current_day, lunch_end))
                            lunch_overlap = max(overlap_end - overlap_start, timedelta(0))
                        else:
                            lunch_overlap = timedelta(0)

                        #Sum working time in day
                        daily_work_time = (task_end - task_start) - lunch_overlap
                        work_duration += daily_work_time
                        current_day += timedelta(days=1)

                    #Working time by each assignee
                    peoples = task.get("properties", {}).get("Assignee", {}).get("people", [])
                    for people in peoples:
                        assignee = people.get("id", {})
                        if assignee in assignees:
                            total_work_time_per_assignee[assignee] += work_duration

        #Working time over tasks by each assignee
        average_time_per_task = {}
        for assignee in assignees:
            task_count = assignee_counts.get(assignee, 0)
            total_time = total_work_time_per_assignee.get(assignee, timedelta(0))
            
            if task_count > 0:
                avg_time = total_time / task_count
            else:
                avg_time = timedelta(0)
            
            average_time_per_task[assignee] = avg_time

        return average_time_per_task, total_work_time_per_assignee
    
    #Summary of information
    def summarize_data_work_checking(self):
        #Create list assignees
        assignees_mapping = {}
        all_assignees = set()
        total_tasks = []
        data_list = []
                
        for database_id in self.database_ids:
            #All assignee information
            assignees, assignee_mapping_database = self.get_assignees(database_id=database_id)  
            
            for assignee_id, assignee_name in assignee_mapping_database.items():
                 if assignee_id not in assignees_mapping:
                    assignees_mapping[assignee_id] = assignee_name
            
            all_assignees.update(assignees)
            
            #All tasks information
            tasks = self.get_notion_tasks_data(database_id=database_id)        
            total_tasks.extend(tasks)
            
        print(f"List assignees mapping {json.dumps(assignees_mapping, indent=4)}")
        assignee_counts = {assignee_id: 0 for assignee_id in all_assignees}

        #Count task by each assignee
        assignee_counts = self.work_matching(total_tasks, assignees=all_assignees, assignee_counts=assignee_counts)

        #Average time over tasks
        average_time_per_task, total_work_time_per_assignee = self.working_times_over_tasks(total_tasks, assignees=all_assignees, assignee_counts=assignee_counts)
        
        #Summarize information
        for assignee_id in all_assignees:
            assignee_name = assignees_mapping.get(assignee_id, "Unknown assignee")
            task_count = assignee_counts.get(assignee_id, 0)
            time_per_task = average_time_per_task.get(assignee_id, timedelta(0))
            average_time = str(time_per_task).split(".")[0]
            total_time = total_work_time_per_assignee.get(assignee_id, timedelta(0))
            
            data_list.append(
                {
                    "Assignee" : assignee_name,
                    "Task": task_count,
                    "Average time": average_time,
                }
            )
            print(f"Assignee: {assignee_name} Task: {task_count}  Average time:{average_time} Total time: {total_time}")
            
        return data_list
        
    def export_to_csv_file(self, data_list):
        with open('assignee_task_count.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Nguoi thuc hien', 'Tong so task da hoan thanh', 'Thoi gian trung binh/task'])
            for data in data_list:
                writer.writerow([data["Assignee"], data["Task"], data["Average time"]])

        print("Data has been exported to file 'assignee_task_count.csv'.")

    
    #Checking code
    def checking_tasks(self):
        for database_id in self.database_ids:
            tasks = self.get_notion_tasks_data(database_id=database_id)
            thanh = "15bd872b-594c-81a8-af2a-00022819530a"
            for task in tasks:
                if task.get("properties", {}).get("Assignee", {}).get("people", []):
                    assignee = task.get("properties", {}).get("Assignee", {}).get("people", [])[0].get("id", {})
                    if thanh == assignee:
                        print(f"Du lieu tra ve:", json.dumps(task, indent=4))
                        # if(task.get("properties", {}).get("Time", {}).get("date", {}).get("end", "") == task.get("properties", {}).get("Time", {}).get("date", {}).get("start", "")):
                        date_temp = pd.to_timedelta("1 days 00:00:00")
                        print(f"Assignee: {assignee}")
                        date = task.get("properties", {}).get("Time", {}).get("date", {}).get("start", "")
                        start_day = self.convert_to_iso_format(date, 8, 30)
                        date_end = task.get("properties", {}).get("Time", {}).get("date", {}).get("end", "")
                        end_day = self.convert_to_iso_format(date_end, 8, 30)
                        date1 = pd.to_datetime(start_day)
                        date2 = pd.to_datetime(end_day)
                        # date1 = pd.to_datetime("2025-01-13 10:30:00")
                        # date2 = pd.to_datetime("2025-01-14 09:30:00")

                        # print(date2 - date1)
                        # print(f"ngay start: {date1},  ngay end: {date2}")
                        if(date1 == date2):
                            print("1111")
                        elif(date2 - date1 > date_temp):
                            print("2222")
                        # print(f"Du lieu tra ve Task:", json.dumps(task, indent=4))
                        # print(f"Du lieu tra ve Task:", json.dumps(task.get("properties", {}).get("", {}).get("title", {})[0].get("text"), indent=4))
                        # print(f"Dulieu status", json.dumps(task.get("properties", {}).get("Status", {}).get("status", {}).get("name", {}), indent=4))  
                        
                # if task.get("properties", {}).get("Task", {}).get("title", {}):
                #     if task.get("properties", {}).get("Task", {}).get("title", {})[0].get("text", {}).get("content", {}) == "Reply posting":
                #         print("task error:",json.dumps(task, indent=4))
                # else:
                #     print("task error:",json.dumps(task.get("properties", {}).get("Task", {}), indent=4))

    def write_mongo_db(self):
        client = MongoClient("mongodb://localhost:27017/")
        db = client["mydatabase"]
        collection = db["mycollection"]
        collection.delete_many({})
        for database_id in self.database_ids:
            tasks = self.get_notion_tasks_data(database_id=database_id)
            for task in tasks:
                insert_result = collection.insert_one(task)
                print(f"Inserted ID: {insert_result.inserted_id}")

if __name__ == "__main__":
    try:
        notion_api = NotionApi()
        notion_api.write_mongo_db()
        data = notion_api.summarize_data_work_checking()
        notion_api.export_to_csv_file(data)
        
    except Exception as e:
        print(f"An error occurred: {e}")
