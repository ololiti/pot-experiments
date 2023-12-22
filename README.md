# pot-experiments
 experiments building on the program of thoughts paper

 results so far (on GSM8K)
 | Experiment | Model | Examples Given | Percent Accuracy | Percent Non-Null | Num Examples | Time to Run |
 |------------|-------|----------------|-------|------------------|---------------|-------------------|
 | basic 4-shot  | GPT-4 | 4 | 92.35%           | 100%             | 353          | |
 | basic 4-shot | GPT-3.5-turbo | 4 | 68%           | 100%             | 100          | |
 | majority answer from 5 runs | GPT 3.5 | 4 | 80% |100% | 100 | |
 | rerun until agree | GPT 3.5 | 4 | 74%| 100% | 100 | 12:26 |
 | teacher feedback when wrong |GPT 3.5 | 4 | 50% | 70% | 10 | |
 | teacher feedback w/ GPT-4 as teacher | GPT 3.5 |  4| 70% | 100% | 10 | |
 | re-generate when disagreement | GPT 3.5 | 4 | 60% | 90% | 10 | |
  | learning from mistakes | GPT 3.5 | variable | 76% | 98% | 100 | |
 | learning from mistakes w/ majority answer | GPT 3.5 | variable | 81% | 100% | 100 | |
  | basic 0-shot | GPT 3.5 | 0 | 50% | 60% | 10 | 0:44 |
 | basic 0-shot | GPT 4 | 0 | 80% | 100% | 100 | 3:29 |
 | basic 8-shot | GPT-3.5 | 8|  66% | 97% | 100 | |
 | majority answer from 5 runs | GPT 3.5 | 8 | 76% | 100% | 100 | |



(on AQUA)
  | Experiment | Model | Examples Given | Percent Accuracy | Percent Non-Null | Num Examples | Time to Run |
 |------------|-------|------------------|------------------|------------------|---------------|-----------|
 | basic 4-shot | GPT-4 | 4 | 77% | 92% | 100 | 24:35 |
 | basic 4-shot | GPT 3.5 | 4 | 52% | 80% | 100 | 6:40 |
 | majority answer from 5 runs | GPT 3.5 | 4 | | | |
