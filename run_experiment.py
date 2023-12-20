import json
from openai import OpenAI
import argparse
import func_timeout
import math
from tqdm import tqdm
import time
from collections import Counter




parser = argparse.ArgumentParser()
parser.add_argument("--name", default="test", type=str)
parser.add_argument("--data_file", default="gsm8K.json", type=str)
parser.add_argument("--num_examples", default=5, type=int)
parser.add_argument("--verbose", default=False, type=bool)
parser.add_argument("--system_prompt", default="gpt4-system0.txt", type=str)
parser.add_argument("--example_prompt", default="gpt3-gsm8k-fewshot0.txt", type=str)
parser.add_argument("--teacher", default=False, type=bool)
parser.add_argument("--teacher_prompt", default="gpt3-teacher-prompt2.txt", type=str)
parser.add_argument("--student", default=False, type=bool)
parser.add_argument("--best_of", default=1, type=int)

args = parser.parse_args()

def load_data(filename):
    with open(f"data/{filename}") as f:
        test_data = json.load(f)
    return test_data

def load_prompt(sys_filename, main_filename):
    with open(f"prompts/{sys_filename}", 'r') as f:
        sys_prompt = f.read()
    with open(f"prompts/{main_filename}", 'r') as f:
        ex_prompt = f.read()
    return sys_prompt, ex_prompt

def generate_example(ex_prompt, example):
    return ex_prompt + "\n\n" + "# Question: " + example["question"] + "\n\n" + "# Solution:" + "\n"

def ask_gpt(system_prompt, user_prompt, max_tokens=None):
    client = OpenAI(api_key=API_KEY)
    got_result = False
    while not got_result:
        try:
            if max_tokens is not None:
                result = client.chat.completions.create(
                    model='gpt-4',
                    messages=[{"role": "system", "content": system_prompt},
                                {"role": "user", "content":  user_prompt}],
                    max_tokens=max_tokens
                )
            else:
                result = client.chat.completions.create(
                    model='gpt-3.5-turbo',
                    messages=[{"role": "system", "content": system_prompt},
                                {"role": "user", "content":  user_prompt}]
                )
            got_result = True
        except Exception as e:
            print(e)
            time.sleep(3)
    result = result.choices[0].message.content
    return result

def pair_student(system_prompt, user_prompt, question, verbose):
    result1 = ask_gpt(system_prompt, user_prompt)
    result2 = ask_gpt(system_prompt, user_prompt)
    answer1 = safe_execute(result1)
    answer2 = safe_execute(result2)
    if verbose:
        print(f"{result1}\n{result2}\nanswer 1: {answer1}, answer2: {answer2}")
    if abs(answer1 - answer2) < 0.001:
        return result1, answer1
    system_prompt2 = system_prompt + "\n# Two students have attempted to write code to solve this math problem, but at least one of them has reasoned about the problem incorrectly."
    user_prompt2 = f"# Question: {question} \n\n# Student 1 Solution (possibly incorrect): \n{result1}\n# This gives an answer of {answer1}. \n\n# Student 2 Solution (possibly incorrect):\n{result1}\n# This gives an answer of {answer2}.\n\n# Question: {question} \n\n# Correct Solution: \n"
    result = ask_gpt(system_prompt2, user_prompt2)
    if verbose:
        print("Final Solution: ")
        print(result)
    executed_ans = safe_execute(result)
    return result, executed_ans



def ask_teacher(teacher_prompt_file, question, answer):
    with open(f"prompts/{teacher_prompt_file}", 'r') as f:
        sys_prompt = f.read()
    ex_prompt = "# Question: " + question + "\n\n" + "# Student Solution: \n" + answer
    return ask_gpt(sys_prompt, ex_prompt, 100)

def ask_student(system_prompt, user_prompt, orig_answer, teacher_feedback):
    teacher_response = "# A teacher has given you the following feedback on your answer. Please rewrite your Python code based on this feedback. \n # " + teacher_feedback
    teacher_response += "\n \n # Solution: \n"
    client = OpenAI(api_key=API_KEY)
    got_result = False
    while not got_result:
        try:
            result = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[{"role": "system", "content": system_prompt},
                            {"role": "user", "content":  user_prompt},
                            {"role": "assistant", "content": orig_answer},
                            {"role": "user", "content": teacher_response}]
            )
            got_result = True
        except Exception as e:
            print(e)
            time.sleep(3)
    result = result.choices[0].message.content
    return result

# safe execute function taken from Program of Thought paper
def safe_execute(code_string: str, keys=None):
    def execute(x):
        try:
            exec(x)
            locals_ = locals()
            if keys is None:
                return locals_.get('ans', None)
            else:
                return [locals_.get(k, None) for k in keys]
        except Exception:
            return None
    try:
        ans = func_timeout.func_timeout(5, execute, args=(code_string,))
    except func_timeout.FunctionTimedOut:
        ans = None

    return ans

def rerun(system_prompt, user_prompt, n):
    answers = Counter()
    for i in range(n):
        result = ask_gpt(system_prompt, user_prompt)
        executed_ans = safe_execute(result)
        if executed_ans is not None:
            answers.update([executed_ans])
    if len(answers) == 0:
        return result, None
    return result, answers.most_common(1)[0][0]

def run_test(verbose, name, test_data, prompts, reruns, teacher, other_student, **kwargs):
    total = len(test_data)
    correct = 0
    non_null = 0
    system_prompt = prompts[0]
    ex_prompt = prompts[1]

    print(f"num examples: {len(test_data)}")
    output_file = f"outputs/{name}.json"

    writer = open(output_file, 'w')
    writer.write(json.dumps({"system prompt": system_prompt, "few shot prompt": ex_prompt}) + "\n")

    total = 0
    progress = tqdm(test_data)
    for example in progress:
        user_prompt = generate_example(ex_prompt, example)
        if verbose:
            print("=================")
            print(example["question"])
            print("")
        if other_student:
            result, executed_ans = pair_student(system_prompt, user_prompt, example["question"], verbose)
        elif reruns == 1:
            result = ask_gpt(system_prompt, user_prompt)
            if verbose:
                print(result)
            executed_ans = safe_execute(result)
        else:
            result, executed_ans = rerun(system_prompt, user_prompt, reruns)
        current_correct = False
        if executed_ans is not None:
            non_null += 1
            if abs(executed_ans - example["answer"]) < 0.001:
                current_correct = True
                correct += 1
        if verbose:
            print(f"executed answer: {executed_ans}, expected: {example['answer']}")

        tmp = {
            "question": example["question"],
            "correct answer": example["answer"],
            "response": result,
            "executed answer": executed_ans
        }

        if teacher:
            teacher_feedback = ask_teacher(kwargs["teacher_file"], example["question"], result)
            tmp["teacher feedback"] = teacher_feedback
            if verbose:
                    print("")
                    print(teacher_feedback)
                    print("")
            if not teacher_feedback.lower().startswith("correct"):
                new_result = ask_student(system_prompt, user_prompt, result, teacher_feedback)
                executed_ans = safe_execute(new_result)
                if verbose:
                    print(new_result)
                    print(f"executed answer: {executed_ans}, expected: {example['answer']}")
                if executed_ans is not None:
                    if abs(executed_ans - example["answer"]) < 0.001:
                        correct += 1
                
                tmp["old response"] = tmp["response"]
                tmp["response"] = new_result
                tmp["old executed answer"] = tmp["executed answer"]
                tmp["executed answer"] = executed_ans
            
    
        
        total += 1
        progress.set_postfix({"accuracy": correct/total, "non-null": non_null/total}, refresh=True)
        writer.write(json.dumps(tmp) + '\n')
    
    writer.close()
    print()
    print(f"accuracy: {correct/total}")
    print(f"percent executed: {non_null/total}")

if __name__ == "__main__":
    test_data = load_data(args.data_file)[:args.num_examples]
    prompts = load_prompt(args.system_prompt, args.example_prompt)
    run_test(args.verbose, args.name, test_data, prompts, args.best_of, args.teacher, args.student, teacher_file=args.teacher_prompt)

    
        

