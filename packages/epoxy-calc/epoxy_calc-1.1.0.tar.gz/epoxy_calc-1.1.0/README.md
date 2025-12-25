# On-the-sea epoxy calculator

I have ordered epoxy from https://hp-textiles.com, so there are two components that should be mixed by mass.  If having a super-exact scale, stable hands, stable working position and presuming it's possible to pour very exact quantities of components from the canisters then it's super-easy mixing very exact quantities of components.

Now in reality the scale has a 1g resolution rather than the 0.1g it ought to have when mixing small quantities of epoxy, but worse still, you're on a boat, there are waves, and the scale keeps jumping from -2g to 22g when you've attempted adding 10g of base into a jar.  And even if you're sure you've added 10g of base in the jar, when adding 6g of hardener it's easy to accidentally add 8g instead of 6g ... and then more base needs to be added.

## The problems

This small program attempts to solve three (four) problems:

* The scale showing different numbers each time one looks at it due to waves.  The program will take a series of readings, chop away the extremes and take the average of the remaining numbers.  It probably won't be perfect as the scale probably doesn't move linearly, but it's the best I can propose.
* The calculation problem.  It's easy enough to do the math in the head if adding 100g of base and then 60g of hardener.  It's usually also easy to do the math in the head if adding, say, 20g of base and then 12g of hardener.  Now, what if you've tried measuring 20g of base and ends up with 23.5g?  Of course, still possible to do the math in the head, but the computer is more reliable at that (and possibly faster).
* The overshoot calculation problem.  So you've added 23.5g of base, that means you should add 14.1g of hardener, but ... oups, now there is 16.5g of hardener in the jar.  How much more base is it needed to add?
* The 1g resolution of typical scales is too high when one wants to mix very small quantities of resin.  The proper solution to this is to buy a better scale, but when there are some waves and many measurements is taken, the end result (say, 6.3g, after many readings of 6g, and some few readings of 7g) may be closer to the truth than what the scale can show on a day without waves (6g).

(When mixing epoxy outdoors, there may also be a wind causing the readings to vary.  I'm not sure the algorithms here are good to use in windy environment)

## Installation

```bash
pip install epoxy-calc
```

Or with pipx:

```bash
pipx install epoxy-calc
```

## Usage

Run `epoxy-calc` from the command line. It will interactively ask you for minimum six readings of the tara, six readings of the tara + base total weight, then it will tell how much hardener to add, ask for six more readings of the total weight, tell how much base or hardener should be added, etc, all until the ratio is more or less correct.

## Future plans

Moved to [TODO.md](TODO.md)

