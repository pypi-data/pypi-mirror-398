# WiseNations

*NOTE*: This project is still in **development phase**, don't use it for actual production.

A simple library for NationStates RP stats management and evaluation.

## Getting started

WiseNations works with stat sheets
``` python
from wisenations import SheetManager

sm = SheetManager()
sm.new_sheet("s1")
my_sheet = sm.get_sheet("s1")

```

Let's add some stats...
``` python
my_stats = {
    "hp": "200",
    "speed": "10",
    "damage": '30',
    "attack_speed": "speed * 2.5"
}
my_sheet.add_stats(my_stats)
```

Output
``` bash
{'attack_speed': 'speed * 2.5', 'damage': '30', 'hp': '200', 'speed': '10'}
```

Evaluate expressions
``` python
result = my_sheet.solve_expressions()
print(result)
```

Output
``` bash
{'attack_speed': '25.0', 'damage': '30', 'hp': '200', 'speed': '10'}
```