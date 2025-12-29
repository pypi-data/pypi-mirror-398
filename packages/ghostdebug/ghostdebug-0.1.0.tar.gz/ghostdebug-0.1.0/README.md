# ghostdebug

A simple backend debugger for Python inspired by Unity's Debug system

# installation
```bash
pip install ghostdebug
```
# Usage
First,import the Debug class:
```python
from ghostdebug import Debug
```
Create logs with different levels:
```python
Debug.Log("Number = 9",Debug.Info)
Debug.Log("Wrong input detected",Debug.Warn)
Debug.Log("An error detected",Debug.Error)
Debug.Log("Can't divide by zero",Debug.Error_Info)
```
Display all logs in console:
```python
Debug.Show(Debug.All)
```
Save logs into a file automatically named as log1.txt,log2.txt etc:
```python
Debug.Save_Log()
```