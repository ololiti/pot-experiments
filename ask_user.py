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
    if ans.lower() in ["w", "write"]:
        return "write"
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
        ans = input("# Either say yes, indicate the line number of the first incorrect step, or type 'w' to write it yourself: ")
        ans = parse_ans(ans, len(solution_lines))
    if ans == len(solution_lines):
        return True, False, ""
    new_start = ""
    if ans == "write":
        print("# Write your solution below. Type 'done' when you're done and 'restart' if you would like to restart.")
        while True:
            nextline = input("")
            if nextline.lower() == "done":
                return False, True, new_start
            elif nextline.lower() == "restart":
                new_start = ""
                print("# Restarting...")
            else:
                new_start += nextline + "\n"
    better_line = input("# What should this line say instead?\n")
    solution_lines[ans] = better_line
    new_start = "\n".join(solution_lines[:ans+1])
    return False, False, new_start

def ask_gpt(system_prompt, user_prompt, start, model="gpt-3.5-turbo"):
    client = OpenAI(api_key=API_KEY)
    got_result = False
    while not got_result:
        try:
            result = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system_prompt},
                            {"role": "user", "content":  user_prompt},
                            {"role": "assistant", "content":  start}]
            )
            got_result = True
        except Exception as e:
            print(e)
            time.sleep(3)
    result = result.choices[0].message.content
    return result

def ask_with_feedback(system_prompt, user_prompt, question, solution):
    correct, rewritten, new_start = find_error_line(question, solution)
    if rewritten:
        return new_start
    while not correct:
        solution = ask_gpt(system_prompt, user_prompt, new_start +"\n")
        solution = new_start + "\n" + solution
        correct, rewritten, new_start = find_error_line(question, solution)
        if rewritten:
            return new_start
    return solution
    