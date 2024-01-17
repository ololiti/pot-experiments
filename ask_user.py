import json
from openai import OpenAI
import argparse
import func_timeout
import math
from tqdm import tqdm
import time
from collections import Counter
import sympy
from sympy.solvers import solve
from sympy import Symbol, Eq
from sympy import simplify



def parse_ans(ans, num_lines):
    if ans.lower() in ["y", "yes"]:
        return num_lines
    if ans.isnumeric():
        ans = int(ans) - 1
        if 0 <= ans and ans < num_lines:
            return ans
    return None

def find_error_line(question, solution):
    print(f"# Question: {question}")
    print("")
    print("# The model generated the following code to solve this problem: ")
    print("")
    solution_lines = solution.split("\n")
    for i, line in enumerate(solution_lines):
        print(f"{i+1}. {line}")
    print("# Is the reasoning in this code correct?")
    ans = None
    while ans is None:
        ans = input("# Either say yes or indicate the line number of the first incorrect step: ")
        ans = parse_ans(ans, len(solution_lines))
    if ans == len(solution_lines):
        return True, ""
    better_line = input("# What should this line say instead?\n")
    solution_lines[ans] = better_line
    new_start = "\n".join(solution_lines[:ans])
    return False, new_start

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

def ask_with_feedback(system_prompt, user_prompt, question, solution):
    correct, new_start = find_error_line(solution)
    while not correct:
        solution = ask_gpt(system_prompt, user_prompt + new_start + "\n")
        solution = new_start + solution
        correct, new_start = find_error_line(question, solution)
    return solution
    