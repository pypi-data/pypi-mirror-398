# Wordly

A python client to communicate with servers implementing the
[Dictionary Server Protocol](https://datatracker.ietf.org/doc/html/rfc2229)

If you are using `uv`, you may use `wordly` like so:

```
❯ uvx wordly recalcitrant
"Recalcitrant" gcide "The Collaborative International Dictionary of English v.0.48"
Recalcitrant \Re*cal"ci*trant\ (r[-e]*k[a^]l"s[i^]*trant), a.
   [L. recalcitrans, p. pr. of recalcitrare to kick back; pref.
   re- re- + calcitrare to kick, fr. calx heel. Cf.
   {Inculcate}.]
   Kicking back; recalcitrating; hence, showing repugnance or
   opposition; refractory.
   [1913 Webster]
.
```

## Getting Started

```
pip install wordly
```

## Usage

Once installed you may use wordly from the command line:

```
$ wordly programming
"programming" wn "WordNet (r) 3.0 (2006)"
programming
    n 1: setting an order and time for planned events [syn:
         {scheduling}, {programming}, {programing}]
    2: creating a sequence of instructions to enable the computer to
       do something [syn: {programming}, {programing}, {computer
       programming}, {computer programing}]
.
```

Or you may import `Word` from `wordly` in your scripts.

```py
from wordly import Word

w = Word("curious")

print(w.definition)
```
