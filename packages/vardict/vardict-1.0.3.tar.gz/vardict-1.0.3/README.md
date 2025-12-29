# vardict

### Introduction
With vardict, it is possible to build up a dicionnary based on variable names and their value.
For instance,
```
first_name = "John"
last_name = "Smith"
name = vardict(first_name, last_name)
```
Now, `name` will be `dict(first_name='John', last_name='Smith')`.

In the same call, additional keywords can be added:

```
name = vardict(first_name, last_name, age=21, nationality="FR")
```
Now, `name` will be `dict(first_name='John', last_name='Smith', age=21, nationality='FR')`.

This functionality is handy for calling functions with (many) keyword arguments, e.g. with salabim:
```
for x in range(1001,100):
    for y in range(701, 100):
        text = f'{x}-{y}'
        sim.Animatext(**vardict(x, y, text, angle=45)) # instead of sim.Animatext(**vardict(x=x, y=y, text=text, angle=45))
```
Note that only variables are allowed, so no literals or expressions.


### Usage
Importing can be done with
```
import vardict
```
or
```
from vardict import vardict
```

### Installation
Just install with `pip install vardict`.
