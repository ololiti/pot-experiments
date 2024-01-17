import json
from openai import OpenAI
import argparse
import func_timeout
import math
from tqdm import tqdm
import time
from collections import Counter
from ask_user import ask_with_feedback



parser = argparse.ArgumentParser()
parser.add_argument("--name", default="test", type=str)
parser.add_argument("--data_file", default="gsm8K.json", type=str)
parser.add_argument("--num_examples", default=5, type=int)
parser.add_argument("--verbose", default=False, type=bool)
parser.add_argument("--system_prompt", default="gpt4-system0.txt", type=str)
parser.add_argument("--example_prompt", default="gpt3-gsm8k-fewshot0.txt", type=str)
parser.add_argument("--mode", default="normal", type=str)
parser.add_argument("--teacher_prompt", default="gpt3-teacher-prompt2.txt", type=str)
parser.add_argument("--mistake_prompt", default="gpt4-mistake-prompt.txt", type=str)
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

def ask_gpt(system_prompt, user_prompt, model="gpt-3.5-turbo", max_tokens=None):
    client = OpenAI(api_key=API_KEY)
    got_result = False
    while not got_result:
        try:
            if max_tokens is not None:
                result = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "system", "content": system_prompt},
                                {"role": "user", "content":  user_prompt}],
                    max_tokens=max_tokens
                )
            else:
                result = client.chat.completions.create(
                    model=model,
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
    answer1 = safe_execute(result1, verbose)
    answer2 = safe_execute(result2, verbose)
    if verbose:
        print(f"{result1}\n{result2}\nanswer 1: {answer1}, answer2: {answer2}")
    if answer1 is not None and answer2 is not None and abs(answer1 - answer2) < 0.001:
        return result1, answer1
    user_prompt2 = f"# Another student disagrees with your answer, and has the following solution: \n# Other Solution: \n{result2}\n\n# Please either code a new solution based on this information, or explain why the other student is incorrect. \n"
    client = OpenAI(api_key=API_KEY)
    got_result = False
    while not got_result:
        try:
            result = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[{"role": "system", "content": system_prompt},
                            {"role": "user", "content":  user_prompt},
                            {"role": "assistant", "content": result1},
                            {"role": "user", "content": user_prompt2}]
            )
            got_result = True
        except Exception as e:
            print(e)
            time.sleep(3)
    result = result.choices[0].message.content
    if verbose:
        print("Final Solution: ")
        print(result)
    executed_ans = safe_execute(result, verbose)
    if executed_ans == None:
        return result1, answer1
    return result, executed_ans

def ask_mistake(mistake_file, question, answer, verbose):
    with open(f"prompts/{mistake_file}", 'r') as f:
        sys_prompt = f.read()
    ex_prompt = "# Question: " + question + "\n\n" + "# Student Solution: \n" + answer
    result = ask_gpt(sys_prompt, ex_prompt, "gpt-4")
    if verbose:
        print(f"\n{result}")
    executed_ans = safe_execute(result, verbose)
    if executed_ans is not None:
        return result
    return None

def ask_teacher(teacher_prompt_file, question, answer):
    with open(f"prompts/{teacher_prompt_file}", 'r') as f:
        sys_prompt = f.read()
    ex_prompt = "# Question: " + question + "\n\n" + "# Student Solution: \n" + answer
    return ask_gpt(sys_prompt, ex_prompt, "gpt-4", 100)

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

# taken from the Program of Thought paper
def floatify_ans(ans):
    if ans is None:
        return None
    elif type(ans) == dict:
        ans = list(ans.values())[0]
    elif type(ans) == bool:
        ans = ans
    elif type(ans) in [list, tuple]:
        if not ans:
            return None
        else:
            try:
                ans = float(ans[0])
            except Exception:
                ans = str(ans[0])
    else:
        try:
            ans = float(ans)
        except Exception:
            ans = str(ans)
    return ans

# safe execute function taken from Program of Thought paper
def safe_execute(code_string: str, verbose, keys=None):
    def execute(x):
        try:
            exec(x)
            locals_ = locals()
            if keys is None:
                return locals_.get('ans', None)
            else:
                return [locals_.get(k, None) for k in keys]
        except Exception as e:
            if verbose:
                print(e)
            return None
    try:
        ans = func_timeout.func_timeout(5, execute, args=(code_string,))
    except func_timeout.FunctionTimedOut:
        ans = None

    return floatify_ans(ans)

def rerun(system_prompt, user_prompt, n, verbose):
    answers = Counter()
    for i in range(n):
        result = ask_gpt(system_prompt, user_prompt)
        if verbose:
            print(result)
        executed_ans = safe_execute(result, verbose)
        if executed_ans is not None:
            answers.update([executed_ans])
    if len(answers) == 0:
        return result, None
    return result, answers.most_common(1)[0][0], answers.most_common(1)[0][1]

def rerun_until_agree(system_prompt, user_prompt, verbose, max_runs=5):
    answers = Counter()
    for i in range(max_runs):
        result = ask_gpt(system_prompt, user_prompt)
        if verbose:
            print(result)
        executed_ans = safe_execute(result, verbose)
        if executed_ans is not None:
            answers.update([executed_ans])
            if answers.most_common(1)[0][1] > 1:
                return result, answers.most_common(1)[0][0], i
    if len(answers) == 0:
        return result, None, max_runs
    return result, answers.most_common(1)[0][0], max_runs

def run_test(verbose, name, test_data, prompts, reruns, mode, **kwargs):
    total = len(test_data)
    correct = 0
    non_null = 0
    gpt4_queries = 0
    system_prompt = prompts[0]
    ex_prompt = prompts[1]
    examples_in_ex_prompt = 2

    with open(f"prompts/examples-from-incorrect-gsm8k.txt", 'r') as f:
        other_ex_prompt = f.read()

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
        if mode == "student":
            result, executed_ans = pair_student(system_prompt, user_prompt, example["question"], verbose)
        elif reruns < 0:
            result, executed_ans, runs = rerun_until_agree(system_prompt, user_prompt, verbose)
        else:
            result, executed_ans, frequency = rerun(system_prompt, user_prompt, reruns, verbose)
        
        if verbose:
            print(f"executed answer: {executed_ans}, expected: {example['answer']}")

        tmp = {
            "question": example["question"],
            "correct answer": example["answer"],
            "response": result,
            "executed answer": executed_ans
        }

        if mode == "teacher":
            teacher_feedback = ask_teacher(kwargs["teacher_file"], example["question"], result)
            tmp["teacher feedback"] = teacher_feedback
            if verbose:
                    print("")
                    print(teacher_feedback)
                    print("")
            if not teacher_feedback.lower().startswith("correct"):
                new_result = ask_student(system_prompt, user_prompt, result, teacher_feedback)
                new_ans = safe_execute(new_result, verbose)
                if verbose:
                    print(new_result)
                    print(f"executed answer: {new_ans}, expected: {example['answer']}")
                if new_ans is not None:
                    # if none, prob just said "my old program was correct" or smth
                    executed_ans = new_ans

                tmp["old response"] = tmp["response"]
                tmp["response"] = new_result
                tmp["old executed answer"] = tmp["executed answer"]
                tmp["executed answer"] = new_ans
        elif mode == "mistake":
            if examples_in_ex_prompt < 8:
                teacher_result = ask_mistake(kwargs["mistake_file"], example["question"], result, verbose)
                if teacher_result is not None:
                    if teacher_result.startswith("#"):
                        teacher_result = teacher_result[teacher_result.find('\n')+1:]
                    ex_prompt = f"# Question: {example['question']}\n\n# Solution:\n{teacher_result}\n\n{ex_prompt}"
                    examples_in_ex_prompt += 1
                print(examples_in_ex_prompt)
        elif mode == "certainty":
            if examples_in_ex_prompt < 10 and frequency <= 0.4*reruns:
                new_user_prompt = generate_example(other_ex_prompt, example)
                gpt4_result = ask_gpt(system_prompt, new_user_prompt, model="gpt-4")
                gpt4_queries += 1
                new_ans = safe_execute(gpt4_result, verbose)
                if verbose:
                    print("")
                    print("# GPT-4 result: ")
                    print(gpt4_result)
                    print(new_ans)
                if new_ans is not None:
                    ex_prompt = f"{ex_prompt}\n\n# Question: {example['question']}\n\n# Solution:\n{gpt4_result}"
                    print(gpt4_result)
                    examples_in_ex_prompt += 1
                    executed_ans = new_ans
        elif mode == "hf":
            if examples_in_ex_prompt < 8 and frequency < 0.4*reruns:
                new_result = ask_with_feedback(system_prompt, user_prompt, example['question'], result)
                new_ans = safe_execute(new_result, verbose)
                if new_ans is not None:
                    ex_prompt = f"{ex_prompt}\n\n# Question: {example['question']}\n\n# Solution:\n{new_result}"
                    examples_in_ex_prompt += 1
                    executed_ans = new_ans
        
        if executed_ans is not None:
            non_null += 1
            if abs(executed_ans - example["answer"]) < 0.001:
                correct += 1
            
    
        
        total += 1
        progress.set_postfix({"accuracy": correct/total, "non-null": non_null/total, "gpt-4 queries": gpt4_queries}, refresh=True)
        writer.write(json.dumps(tmp) + '\n')
    writer.write(json.dumps({"final example prompt": ex_prompt}))
    writer.close()
    print()
    print(f"accuracy: {correct/total}")
    print(f"percent executed: {non_null/total}")

if __name__ == "__main__":
    test_data = load_data(args.data_file)[13:13+args.num_examples]
    prompts = load_prompt(args.system_prompt, args.example_prompt)
    run_test(args.verbose, args.name, test_data, prompts, args.best_of, args.mode, teacher_file=args.teacher_prompt, mistake_file=args.mistake_prompt)

    
        

