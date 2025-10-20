import csv
import json
from .base_dataset import BaseDataset
from examples.AgentScope import math_data, history_data

service_name = "answer_question"
class AgentscopeDataset(BaseDataset):
    def __init__(self, math_data_name, history_data_name):
        super().__init__()
        self.math_data_name = math_data_name
        self.history_data_name = history_data_name

        self.data_cache_math = {}
        self.data_cache_history = {}

        self.data_key = "question"
        self.data_index = {"math": 0, "history": 0}
        self.pre_is_math = False

    def cache_data(self):
        if self.math_data_name == "gsm8k":
            self.math_data_file = math_data
            self.data_cache_math[service_name] = self.get_math_data()

        if self.history_data_name == "mmlu":
            self.history_data_file = history_data
            self.data_cache_history[service_name] = self.get_history_data()



    def get_data_by_service_name(self, service_name: str, batch_size: int = 1):
        if service_name not in self.data_cache_math:
            raise ValueError(f"Unknown service name: {service_name}")

        data = None
        data_type = None

        if not self.pre_is_math:
            data_type = "math"
            data = self.data_cache_math[service_name]
            self.pre_is_math = not self.pre_is_math
        else:
            data_type = "history"
            data = self.data_cache_history[service_name]
            self.pre_is_math = not self.pre_is_math

        batch_result = {self.data_key: []}
        max_len = len(data[self.data_key])

        for i in range(batch_size):
            index = self.data_index[data_type]
            batch_result[self.data_key].append(data[self.data_key][index])

            new_index = index + 1
            if new_index >= max_len:
                new_index = 0

            self.data_index[data_type] = new_index

        return batch_result

    def get_math_data(self):
        jsonl_data = read_jsonl(self.math_data_file)
        questions_math = []
        for item in jsonl_data:
            questions_math.append(item["question"])

        print("math data len:", len(questions_math))

        return {self.data_key: questions_math}

    def get_history_data(self):
        questions_history = read_first_column_csv(self.history_data_file)

        print("history data len:", len(questions_history))

        return {self.data_key: questions_history}


def read_jsonl(file_path):
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                try:
                    json_obj = json.loads(line)
                    data.append(json_obj)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON on line: {line.strip()}. Error: {e}")
    except FileNotFoundError:
        print(f"File {file_path} not found.")
    return data

def read_first_column_csv(file_path):
    first_column = []
    with open(file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row:
                first_column.append(row[0])
    return first_column