# pot-experiments
 experiments building on the program of thoughts paper

 results so far (on GSM8K, with 4-shot training)
 | Experiment | Model | Percent Accuracy | Percent Non-Null | Num Examples |
 |------------|-------|-----------|------------------|---------------|
 | basic 4-shot  | GPT-4 | 92.35%           | 100%             | 353          |
 | basic 4-shot | GPT-3.5-turbo | 68%           | 100%             | 100          |
 | majority answer from 5 runs | GPT 3.5 | 80% |100% | 100 |
 | teacher feedback when wrong | GPT 3.5 | 50% | 70% | 10 |
 | teacher feedback w/ GPT-4 as teacher | GPT 3.5 | 70% | 100% | 10 |
 | re-generate when disagreement | GPT 3.5 | 60% | 90% | 10 |
 | learning from mistakes | GPT 3.5 | 76% | 98% | 100 |
 | learning from mistakes w/ majority answer | GPT 3.5 | 81% | 100% | 100 |
 
 results so far (on GSM8K, with 8-shot training)
  | Experiment | Model | Percent Accuracy | Percent Non-Null | Num Examples |
 |------------|-------|-----------|------------------|---------------|
 | basic 8-shot | GPT-3.5 | 66% | 97% | 100 |
 | majority answer from 5 runs | GPT 3.5 | 76% | 100% | 100 |
