# DatalogTestDriver
Test datalog parsers to see if they are accurate

## BYU CS236 Students
This code varies from the BYU CS236 projects in the following ways:
- The lexical analyzer uses regular expressions, rather than character by character parsing, to create tokens from an input file.
- the datalog parser was designed to literally interpret an arbitrary grammar and turn the tokens into a datalog program.  It will fail or succeed on the same test files as your code, but not always on the same exact token. 
- Query Evaluation, and all operations on relations(such as join and union) are implemented using Pandas. 
- The printing of Query evaluations is the most time consuming task in my code, and it has been multi-process-threaded (Pandas and numpy are not restricted by Python's Global Interpreter Lock) for speed.
- On project 5, the strongly connected components were calculated using the tarjan algorithm.  Therefore my rule evaluation order may be slightly different from what you are expected to produce.
- Every source file has it's own "main" and can be run individually.
- A QT Sandbox is included which will evaluate a Datalog grammar instantly. It is useful for gaining an understanding of datalog but will crash on large datalog programs.
- The test driver implements python's unit test framework to compare your binary's output to what my code produces.  This is the recommended way to run my code as it the most stable and complete.  Note that passing my test driver does not necessarily mean you will be able to pass off with the TA's. 
- Corner cases, Expressions, mismatched scheme/rule IDs, etc... are all handled in a way that made sense to me.  Many of these were overkill on my part but remember that you can make certain assumptions about what your input files will be from the specs.  

If you are a student doing this project in C++ then I suggest you read the specs and do it yourself from scratch.
Python is vastly different from c++ and it would be outrageously more difficult to port this code to C++ than to understand the project and do it yourself.  However, you are welcome to run the test driver to get an understanding of datalog and to test your own code
