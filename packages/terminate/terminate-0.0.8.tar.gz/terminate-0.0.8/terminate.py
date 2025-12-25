from time import sleep
import traceback

# exit with status code 1
def __stop()->None:exit(1);

# exit or continue after answering prompt
def __ask(q: str)->None:
    if q=='n':raise Exception("Continued after Exception...");
    elif q=='y':__stop();
    else:print("Invalid Input!\n");a=input("exit? y/n\n");__ask(a);

# wait for some time and then exit
def __wait(t=5)->None:
    try:
        if type(t)!=int or t<0:__stop();
        print("Press Ctrl+C to continue...")
        for i in range(t):
            if i==t-1:print("1");sleep(0.5);print("exiting...");sleep(0.5);
            else:print(t-i);sleep(1);
        __stop()
    except KeyboardInterrupt:print("\n");

# choose how to exit
# r = "e": exit directly
#   = "c": don't exit
# 	= "w": wait and exit
# 	= "a": ask to exit
def retrn(r:str,e:str|TypeError|Exception,print_traceback=True)->None:
    '''
#### Function to handle exit
- **r**: 
    1. **'e'** - Exit directly
    2. **'c'** - Continue
    3. **'w'** - Wait for 5 seconds before exit
    4. **'a'** - Ask prompt before exit
- **e**: Error to print
    '''
    if print_traceback:traceback.print_exception(type(e), e, e.__traceback__);
    else:print((e.__class__.__name__ if e.__class__.__name__ !='str' else 'Error')+":",e);
    print()
    match r:
        case "e":__stop();
        case 'c':pass;
        case 'w':__wait();
        case 'a':a=input("exit? y/n\n");__ask(a);
        case _:print("Invalid argument: r => 'c'/'w'/'a'");a=input("exit? y/n\n");__ask(a);

