I decided a long time ago that someday I wanted to give this talk because for a good long while, decorators seemed like magic. I could use them and even write them, but by following examples, not through a solid grasp of how they worked. So that's the context of this talk--I want to take you from knowing what decorators are _for_ but not necessarily knowing anything about their internals to being able to explain how decorators work and how to write one to someone else.

So--I'm gonna fake Socratic method this for a bit and hope it's not too smug--let's start at the absolute beginning: What is a decorator? My gut instinct here is to define a decorator by what it does, specifically, changing the behavior of a code object, most frequently a function, without changing the source code of that object. That pattern is in fact generally known in computer science as the decorator pattern or wrapper pattern, because the new behavior wraps the old. As an example, maybe you are interested in how long a function takes to execute. If you have access to that function's source, you could modify it, say get the time before the original function code and the time after and then log the difference:

```
import logging
import time

def my_timed_function(original_arg, original_kwarg=None):
    start_time = time.time()    
    # original body of function which uses
    # `original_arg` and `original_kwarg`
    end_time = time.time()
    logging.debug("Time in my_function is %s seconds", end_time-start_time)
    return original_return_value
```	

Or you could write a decorator to do the same thing and reuse it on a bunch of other functions, which has the convenient side effect of making it obvious that the timing is *extra* functionality and not inherent to what the function is intended to do:

```
import my_timer  # how does it work? mystery!

@my_timer
def original_function(original_arg, original_kwarg=None):
    # original body of function
    return original_return_value
```

That's a great functional (no pun intended) definition for a decorator, but not exactly especially illuminating in regards to how decorators achieve modifying code objects. You'll notice I keep saying "code object" for the decorated item when my example is a function. And sure, that's mostly because saying "code object" is more correct than saying "function" and I'm trying to avoid backpedaling later on. However, that choice of term is useful because, in Python, functions *are* objects. What does that mean? Well, it means they can be assigned to variables. It means they can be passed as arguments to other functions. And it means they can be used as return values from functions.

I have over 25 minutes left, let's just refactor that `my_timed_function` example a little bit. I _had_ just added timing code in the original body of the function, but if I instead pass the original function as an argument to a timing function, I can use the timing function to time _any_ function!

```
import logging
import time

def my_timing_function_wrapper(func, *func_args, **func_kwargs):
    start_time = time.time()
    value_to_return = func(*func_args, **func_kwargs)
    end_time = time.time()
    logging.debug("Time in %s is %s seconds", func.__name__, end_time-start_time)
    return value_to_return
```

I can use `my_timing_function_wrapper` to time any arbitrary function by calling it with the function and whatever arguments I want to pass to the function. For example, maybe I'm curious about the performance of list comprehensions vs for loops, so I write these two functions. They both perform the same operation, building lists with the same items that are in the input iteratable, but the first does that by repeatedly calling `append` in a loop and the second uses a list comprehension.

```
import my_timing_function_wrapper

def use_for_loop(test_data):
    new_data = []
    for item in test_data:
        new_data.append(item)
    return new_data

def use_list_comprehension(test_data):
    new_data = [item for item in test_data]
    return new_data
```

To time each one of these, I'd call `my_timing_function_wrapper` with the function and an iterable. I actually did this, with a list of 100,000 numbers as the test data, and was able to to see that list comprehensions are in fact faster than for loops:

```
> data = range(100000)
> new_loop_data = my_timing_function_wrapper(use_for_loop, data)
DEBUG:root:Time in use_for_loop is 0.010552 seconds
> new_comprehension_data = my_timing_function_wrapper(use_list_comprehension, data)
DEBUG:root:Time in use_list_comprehension is 0.005217 seconds
```

Well, great, we learned something from that little experiment. More pertinently, refactoring `my_timing_function_wrapper` to take the function to be timed as an argument allowed me to reuse the timing code on multiple functions, thus making the experiment possible in the first place.

What we really want to do, therefore, is refactor `my_timer` so that we can replace whatever function we want to be timed with a function returned by `my_timer`, so that we can call it at will and with arbitrary arguments and it will have the timing functionality:

```
import random
import time

import my_timer

def reticulate_splines(spline_one, spline_two, extra_splines=False):
    # reticulation
    return splines
	
reticulate_splines = my_timer(reticulate_splines)
```

I'll leave the details of how to achieve that refactor, because now we should really get back to decorators. But...I've been talking about them all along. It turns out that transforming a function in-place by replacing it with a function returned by a wrapper function is exactly how the decorator pattern is implemented in Python. Python 2.2 had a built-in classmethod decorator that worked just like this, where the method to be decorated was just replaced with a wrapped version, and Python 2.4 introduced the `@` syntax as syntactic sugar.

So in practice, a decorator works by taking a callable code object, returning a code object, and replacing the input object with the returned code object. Generally, many decorators look like this, where a new function is defined in the body of the decorator and returned by the decorator. A mild gotcha is that, because the returned object `new_function` is replacing `func`, `new_function` needs to have the same signature as `func`. Most people ensure that they don't get `TypeError` for bad signatures by using splatting the args and kwargs to `new_function`, which will match any given arguments.

However, it's entirely possible to construct decorators that behave strangely. The only grammatical requirement for a decorator is that it takes a single argument. We could write a decorator that returns the same object passed in to it, a decorator that replaces a function with something else that does not call the input function, or a decorator that does not return a callable object.




<closures>




I feel it's important to note that, although I've been framing decorators as extending behavior of what they decorate, and although the well-behaved decorators DO extend the behavior of the objects they decorate, we're not obliged to limit ourselves to extension. The only real requirement for a decorator to be a decorator is that it take a accept an object and return an object. We could, say, write a decorator that is a no-op:

```
def the_most_useful_decorator(func):
	return func
```
Or a decorator that completely ignores its input. For example, what's happening here:

```
import extra_serious

DOOM_CLOCK = 0

@extra_serious_widget
def set_doom_clock(disaster=False):
    global DOOM_CLOCK

    if disaster:
        DOOM_CLOCK = 0
    else:
        DOOM_CLOCK += 1

    return DOOM_CLOCK
```
Where we have a function that looks like it should modify a global variable based on a Boolean argument, but when you run it:

```
> set_doom_clock(False)
42
> set_doom_clock(True)
42
> set_doom_clock(False)
42
```
Well, that extra_serious_widget decorator is actually:

```
def extra_serious_widget(func):

	def the_answer_is_always_42(*args, **kwargs):
	    return 42
	
	return the_answer_is_always_42
```
...not very serious. But is it a decorator? Yes. Has `set_doom_clock` been decorated? Yes!

The general format of a decorator is:
* take a callable
* return a callable
* if you are creating the return callable inside the decorator, make sure it has the same signature as the callable that you are replacing. A way that many people achieve that is by splatting args and kwargs so that the decorator can be used in general applications.

That's it, right? That's the blueprint for a decorator, we're done. Except, no, there's still magic. Specifically, how does the wrapper function contain the scope of the wrapping function, how do the arguments for the wrapped function end up in the closure of the wrapping function, how does that syntactic sugar work, and why do so many people use @wraps?



<gotchas>
Decorator order
decorator arguments





old stuff 




I'm just going to go ahead and assert that, since `my_timed_function` behaves exactly the same as `original_function` decorated with `my_timer`, that `my_timed_function` is a decorated function--that is, it is a function whose behavior has been extended without modification of the original source. Furthermore, since a decorator's job is producing decorated functions, the decorated function `my_timed_function` is what the decorator `my_timer` should produce, or return.

Let's unpack that a bit, because I just said a lot and the word "decorate" has started to lose some meaning. There are a couple steps here that, put together, can be used to assemble a definition of the word "decorator" in terms of how it works instead of what it does.

Firstly:
`A decorated function is a function that has been decorated`. In the timing example, I've shown two examples of decorated functions, one that has been constructed and one that has been done by an actual decorator. [emoji DIY person and artist?]

Secondly,
`A decorator produces decorated functions.` If this seems like a tautology, let me show you what the `my_timer` decorator is actually doing:

`original_function = my_timer(original_function)`

Yep, that's right--the `my_timer` decorator is just a callable object that is taking `original_function` as an argument and producing, or rather _returning_ a decorated function, which is then bound to the reference `original_function`.

Add those together and you end up with a definition of a decorator in terms of _how_ it does what it does: it is just a callable code object, like the code objects it decorates, that accepts another callable as an argument and returns a code object, which is then bound to the name of the passed-in code object.

For example, if I had to speculate what `my_timer` looked like, I'd guess something like this:

```
import logging
import time

def my_timer(some_func):

    def my_timed_function(original_arg, original_kwarg=None):
        start_time = time.time()
 
        original_return_value = some_func(original_arg, original_kwarg=original_kwarg)

        end_time = time.time()
        logging.debug("Time in my_function is %s", end_time-start_time)

        return original_return_value

    return my_timed_function
```
Here, we have the decorator `my_timer` which is just a function that takes a function as an argument, constructs a new, *cough* decorated *cough* function, and returns that decorated function. The `my_timed_function` here is essentially the same as the one I showed you earlier.


Tricks & gotchas is something that would get a lot of interest, I would add it in.
- wraps
- ordering
- differences in decorators between python 2 & 3

Explain closures

Watch for filler words - so & uhm. Silence is ok.

```Timing, decoratated slide:
- important point: by using a decorator your timing function is *reusable* now, you don't need to repeat your timing code in other methods [addressed in a later point]```

```What is a function:
- There's a term for this - in Python functions are 'first class objects'```

```General stuff:
- instead of using logging for code examples, use print? it'll make the code simpler```

2:15pm start
hell yes first slide and description of the purpose of your talk is SO clear
```2:19pm "time this!" slide
code is a little wordy. don't need second comment```
2:21pm "what's a func?"
what's a code object though? if you wanna go there and explain what it is, maybe show an example? although i'm not sure it's strictly necessary to explain
2:22pm "back to timing"
transition between last slide and this one was confusing
```recommend cutting out this comparison of for loop vs list comp```
i didn't quite understand the framing/motivation for the next refactor
(don't remember what slide this was on) i like the point about one motivation of decorators being so you don't have to copy/paste code that you'd like to add to each function
2:25pm "final refactor"
```who's sandy mets?```
```spend more time here, this part was confusing to me```
2:26pm "back to decorators"
```remove text from PEP```
like the addition of the history of decorators
when were they added? seemed unclear if it was version 2.2 or not
2:28pm "general form"
```why do we have access to func in new_func? (edit: you answer this later!)```
```maybe planting a seed, like "you might be wondering why X, Y, and Z works! we'll cover those in a bit" so the audience doesn't get hung up on it?```
2:29pm "probably"
love the trash decorators examples, lol
```what error do you get with the black hole??? None isn't callable????```
2:31pm "open q's"
when are decorators applied? this part was confusing to me
maybe have an example with a print statements like "top of decorator", etc? and then show the output after importing and running the function?
that usually helps me understand what happens when, but might not work well in a talk context, so take that suggestion with a grain of salt
2:33pm "scope"
where you answered my question from before! what is this feature called where inner scope can reference variables in an outer scope?
is it similar to a more simple case, like a func referencing a constant that's defined globally? if so maybe try connecting the dots, that it's a similar thing, but referencing a function not a constant?
2:35pm "closure"
this part was confusing to me
2:36pm "how does @ work?"
my notes get worse starting here
@ is syntactic sugar for what? maybe show an example of equivalent code?
it's possible you did just that but i missed it
2:38pm "parsing sugar"
welp i didn't write any notes here
ast digression might not be worthwhile
2:40pm "decorators in brief"
didn't write any notes here either lol
could possibly use a bit more clarity around structure of talk/describe the structure in fewer words

