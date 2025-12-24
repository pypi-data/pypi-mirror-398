# <img src='https://raw.githack.com/FortAwesome/Font-Awesome/master/svgs/solid/robot.svg' card_color='#40DBB0' width='50' height='50' style='vertical-align:bottom'/> FailureBbot
 
Extreme fallback, just complains it does not have a brain

## Usage

Spoken answers api

```python
from ovos_solver_failure_plugin import FailureSolver

d = FailureSolver()
sentence = d.spoken_answer("hello")
print(sentence)
# 404 brain not found
```
