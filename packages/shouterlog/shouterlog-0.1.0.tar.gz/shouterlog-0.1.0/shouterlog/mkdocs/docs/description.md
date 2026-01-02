```python
from shouterlog import Shouter
# optional
import logging
```

### 1. Initialize Shouter Class


```python
shouter = Shouter(
    # optional/ required
    supported_classes = (),
    # optionally 
    ## Formatting settings
    dotline_length = 50,
    auto_output_type_selection = True,
    show_function = True,
    show_traceback = False,
    # For saving records
    tears_persist_path = 'log_records.json',
    datetime_format = "%Y-%m-%d %H:%M:%S",
    # For saving env
    persist_env = False,
    env_persist_path = 'environment.dill',
    ## Logger settings
    logger = None,
    logger_name = 'Shouter',
    loggerLvl = logging.DEBUG,
    logger_format = '(%(asctime)s) : %(name)s : [%(levelname)s] : %(message)s'
)

```

### 2. Basic usage like logging


```python
shouter.debug(
    # optional
    dotline_length=30)
shouter.debug("This is a debug message!")
shouter.info("This is an info message!")
shouter.warning("This is a warning message!")
shouter.error("This is an error message!")
shouter.fatal("This is a fatal message!")
shouter.critical("This is a critical message!")
```

    (2025-12-26 02:51:24,703) : Shouter : [DEBUG] : _format_mess:==============================
    (2025-12-26 02:51:24,704) : Shouter : [DEBUG] : _format_mess:This is a debug message!
    (2025-12-26 02:51:24,704) : Shouter : [INFO] : _format_mess:This is an info message!
    (2025-12-26 02:51:24,704) : Shouter : [WARNING] : _format_mess:This is a warning message!
    (2025-12-26 02:51:24,705) : Shouter : [ERROR] : _format_mess:This is an error message!
    (2025-12-26 02:51:24,705) : Shouter : [CRITICAL] : _format_mess:This is a fatal message!
    (2025-12-26 02:51:24,705) : Shouter : [CRITICAL] : _format_mess:This is a critical message!


### 3. Using different output types


```python
# Different types of outputs
shouter.info(output_type="dline")
shouter.info(output_type="HEAD1", mess="Header Message")
```

    (2025-12-26 02:51:24,710) : Shouter : [INFO] : _format_mess:==================================================
    (2025-12-26 02:51:24,710) : Shouter : [INFO] : _format_mess:
    ==================================================
    -----------------Header Message----------------- 
    ==================================================


### 4. Custom logger configuration


```python
import logging

# Custom logger
custom_logger = logging.getLogger("CustomLogger")
custom_logger.setLevel(logging.INFO)

# Shouter with custom logger
shouter_with_custom_logger = Shouter(supported_classes=(), logger=custom_logger)
shouter_with_custom_logger.info(mess="Message with custom logger")
```

### 5. Backwards compatibility with existing loggers


```python
import logging
import attr #>=22.2.0

@attr.s
class ExampleClass:

    # Logger settings
    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Example Class')
    loggerLvl = attr.ib(default=logging.DEBUG)
    logger_format = attr.ib(default='(%(asctime)s) : %(name)s : [%(levelname)s] : %(message)s')

    def __attrs_post_init__(self):
        self.initialize_logger()

    def initialize_logger(self):

        """
        Initialize a logger for the class instance based on
        the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl,format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger
            
    def print_debug(self):
        
        self.logger.debug("This is a debug message!")
        
    def print_info(self):
        
        self.logger.info("This is a info message!")
        
    def print_warning(self):
        
        self.logger.warning("This is a warning message!")
        
    def print_error(self):
        
        self.logger.error("This is a error message!")
        
    def print_critical(self):
        
        self.logger.critical("This is a critical message!")
        
    def perform_action_chain_1(self):
        
        self.logger.debug("Action 1")
        self.print_debug()
                
        self.logger.debug("Action 2")
        self.print_error()
        
    def perform_action_chain_2(self):
                
        a = 1
        b = 'b'
        c = ['list']
        d = {'key' : 'value'}
        e = Shouter()
        
        self.logger.error("Saving env")
```


```python
ec = ExampleClass()

ec.print_debug()
ec.print_info()
ec.print_warning()
ec.print_error()
ec.print_critical()
```

    (2025-12-26 02:51:24,743) : Example Class : [DEBUG] : This is a debug message!
    (2025-12-26 02:51:24,744) : Example Class : [INFO] : This is a info message!
    (2025-12-26 02:51:24,744) : Example Class : [WARNING] : This is a warning message!
    (2025-12-26 02:51:24,744) : Example Class : [ERROR] : This is a error message!
    (2025-12-26 02:51:24,744) : Example Class : [CRITICAL] : This is a critical message!



```python
shouter_for_example_class = Shouter(
    supported_classes = (ExampleClass),
    tears_persist_path = 'log_records.json'
)

ec = ExampleClass(logger=shouter_for_example_class)

ec.print_debug()
ec.print_info()
ec.print_warning()
ec.print_error()
ec.print_critical()
ec.perform_action_chain_1()
```

    INFO:Shouter:ExampleClass.print_info:This is a info message!
    WARNING:Shouter:ExampleClass.print_warning:This is a warning message!
    ERROR:Shouter:ExampleClass.print_error:This is a error message!
    CRITICAL:Shouter:ExampleClass.print_critical:This is a critical message!
    ERROR:Shouter:ExampleClass.print_error:+ This is a error message!


### 6. Built-in records from Shouter usage


```python
shouter_for_example_class = Shouter(
    supported_classes = (ExampleClass),
    tears_persist_path = 'log_records.json'
)

ec = ExampleClass(logger=shouter_for_example_class)

ec.print_debug()
ec.perform_action_chain_1()
```

    ERROR:Shouter:ExampleClass.print_error:+ This is a error message!



```python
ec.logger.return_logged_tears()
```




    [{'datetime': '2025-12-26 02:51:24',
      'level': 'debug',
      'function': 'ExampleClass.print_debug',
      'mess': 'This is a debug message!',
      'line': 32,
      'lines': [32],
      'is_proc': False,
      'traceback': ['ExampleClass.print_debug']},
     {'datetime': '2025-12-26 02:51:24',
      'level': 'debug',
      'function': 'ExampleClass.perform_action_chain_1',
      'mess': 'Action 1',
      'line': 52,
      'lines': [52],
      'is_proc': False,
      'traceback': ['ExampleClass.perform_action_chain_1']},
     {'datetime': '2025-12-26 02:51:24',
      'level': 'debug',
      'function': 'ExampleClass.print_debug',
      'mess': 'This is a debug message!',
      'line': 32,
      'lines': [32, 53],
      'is_proc': False,
      'traceback': ['ExampleClass.print_debug',
       'ExampleClass.perform_action_chain_1']},
     {'datetime': '2025-12-26 02:51:24',
      'level': 'debug',
      'function': 'ExampleClass.perform_action_chain_1',
      'mess': 'Action 2',
      'line': 55,
      'lines': [55],
      'is_proc': False,
      'traceback': ['ExampleClass.perform_action_chain_1']},
     {'datetime': '2025-12-26 02:51:24',
      'level': 'error',
      'function': 'ExampleClass.print_error',
      'mess': 'This is a error message!',
      'line': 44,
      'lines': [44, 56],
      'is_proc': False,
      'traceback': ['ExampleClass.print_error',
       'ExampleClass.perform_action_chain_1']}]




```python
import pandas as pd

pd.DataFrame(ec.logger.return_logged_tears())
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>datetime</th>
      <th>level</th>
      <th>function</th>
      <th>mess</th>
      <th>line</th>
      <th>lines</th>
      <th>is_proc</th>
      <th>traceback</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>2025-12-26 02:51:24</td>
      <td>debug</td>
      <td>ExampleClass.print_debug</td>
      <td>This is a debug message!</td>
      <td>32</td>
      <td>[32]</td>
      <td>False</td>
      <td>[ExampleClass.print_debug]</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2025-12-26 02:51:24</td>
      <td>debug</td>
      <td>ExampleClass.perform_action_chain_1</td>
      <td>Action 1</td>
      <td>52</td>
      <td>[52]</td>
      <td>False</td>
      <td>[ExampleClass.perform_action_chain_1]</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2025-12-26 02:51:24</td>
      <td>debug</td>
      <td>ExampleClass.print_debug</td>
      <td>This is a debug message!</td>
      <td>32</td>
      <td>[32, 53]</td>
      <td>False</td>
      <td>[ExampleClass.print_debug, ExampleClass.perfor...</td>
    </tr>
    <tr>
      <th>3</th>
      <td>2025-12-26 02:51:24</td>
      <td>debug</td>
      <td>ExampleClass.perform_action_chain_1</td>
      <td>Action 2</td>
      <td>55</td>
      <td>[55]</td>
      <td>False</td>
      <td>[ExampleClass.perform_action_chain_1]</td>
    </tr>
    <tr>
      <th>4</th>
      <td>2025-12-26 02:51:24</td>
      <td>error</td>
      <td>ExampleClass.print_error</td>
      <td>This is a error message!</td>
      <td>44</td>
      <td>[44, 56]</td>
      <td>False</td>
      <td>[ExampleClass.print_error, ExampleClass.perfor...</td>
    </tr>
  </tbody>
</table>
</div>



### 7. Debugging capabilities of Shouter


```python
shouter_for_example_class = Shouter(
    supported_classes = (ExampleClass),
    tears_persist_path = 'log_records.json',
    persist_env = True,
    env_persist_path = 'environment.dill'
)

ec = ExampleClass(logger=shouter_for_example_class)

ec.print_debug()
ec.perform_action_chain_2()
```

    ERROR:Shouter:ExampleClass.perform_action_chain_2:Saving env
    WARNING:Shouter:Object 'self' could not have been serialized, when saving last words!



```python
ec.logger.return_last_words(
    # optional
    env_persist_path = 'environment.dill'
)
```




    {'a': 1,
     'b': 'b',
     'c': ['list'],
     'd': {'key': 'value'},
     'e': Shouter(supported_classes=(), dotline_length=50, auto_output_type_selection=True, show_function=True, show_traceback=False, tears_persist_path='log_records.json', env_persist_path='environment.dill', datetime_format='%Y-%m-%d %H:%M:%S', log_records=[], persist_env=False, lock=<unlocked _thread.lock object at 0x7669b4bc2400>, last_traceback=[], loggerLvl=20, logger_name=None, logger_format='%(levelname)s:%(name)s:%(message)s')}


