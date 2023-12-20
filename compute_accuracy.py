import json

def process_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            total_count = 0
            correct_match_count = 0
            not_none_count = 0
            for line in file:
                item = json.loads(line)
                if 'correct answer' not in item or 'executed answer' not in item:
                    continue

                correct_answer = item['correct answer']
                executed_answer = item['executed answer']

                # Check if executed answer matches correct answer
                if executed_answer == correct_answer:
                    correct_match_count += 1
                else:
                    print(item['question'])
                    print(item['response'])
                    print(f"executed answer {item['executed answer']}, correct answer {item['correct answer']}")

                # Check if executed answer is not None
                if executed_answer is not None:
                    not_none_count += 1
                total_count += 1

        # Calculate percentages
        correct_match_percentage = (correct_match_count / total_count) * 100 if total_count > 0 else 0
        not_none_percentage = (not_none_count / total_count) * 100 if total_count > 0 else 0

        # Print results
        print(f"Percentage of dictionaries where executed answer matches correct answer: {correct_match_percentage:.2f}%")
        print(f"Percentage of dictionaries where executed answer is not None: {not_none_percentage:.2f}%")
        print(f"Total count: {total_count}")

    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON in the file: {file_path}")

# Prompt the user for the file path
json_file_path = input("Enter the path to the JSON file: ")
process_json_file(json_file_path)