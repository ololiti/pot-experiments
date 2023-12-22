import json

with open("data/aqua_test.jsonl", "r") as f:
    with open("prompts/gpt4-aqua-fewshot2.txt", "w") as f1:
        lines_read = 0
        for line in f:
            tmp = json.loads(line)
            f1.write(f"# Question: {tmp['question']}\n")
            f1.write(f"# Answer Options: {tmp['options']}\n")
            f1.write(f"\n# Solution: \n\n")
            lines_read += 1
            if lines_read >= 8:
                break