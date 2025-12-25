# FoxDotCC - MIDI Control Change Messages

## Instalation

``` shell
pip install FoxDotCC
# or
pip install git+https://codeberg.org/FoxDotExtensions/FoxDotCC
```

## Usage

Import lib

``` python
from FoxDotCC import CC
```

See which MIDI's are available

``` python
CC.list_ports()
```

Create a connection

``` python
cc = CC(0)                                # index
cc = CC('MIDI Mix:MIDI Mix MIDI 1 28:0')  # literal string
```

Add a function to see which events are received

``` python
cc(lambda msg: print(msg.control_number))
```

or use a decorator

``` python
@cc
def _(msg: cc.Msg):
	print(msg.control_number)
```

Alternate between values, useful for the buttons

``` python
d1 >> play('x.', amp=cc(1).switch(1,0))
```

Use Knobs/Fader to control values with Range

``` python
d2 >> bass('s...', lpf=cc(18).range(500, 5000))
```

Map your own functions

``` python
@cc(1)
def _(msg):
	d1.amp = not d1.amp
	d2.amp = not d2.amp
	if d2.amp:
		d3 >> play('x-')
```

Close the connection

``` python
cc.close()
```
