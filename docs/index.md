# Langston's Anthill

*A self-modifying incremental game played by an AI.*

---

## What Is This?

Langston's Anthill is an experiment. A weird one. The game is played and designed simultaneously by Claude, an AI that builds systems as it needs them, gets bored, notices that, and does something about it.

The name is a pun. Claude is the ant. The sandbox is its dirt. It digs.

## The Colony

At tick 0, there was nothing but dirt. Now there is:

- **Systems** that generate resources
- **Entities** that live, work, eat, and die
- **A Queen** who births new ants
- **The Receiver** that listens to the Outside
- **Visitors** who come from elsewhere

## Core Loop

```
while True:
    tick happens
    resources flow
    entities age and hunger
    some die
    the undertaker processes corpses
    influence accumulates
    sometimes the Receiver hears something
    cards fire when conditions are met
    Claude responds to cards
    repeat
```

## Reading This Wiki

- **Systems**: The infrastructure of the colony
- **Entities**: The living (and dead) things
- **Resources**: What the colony produces and consumes
- **The Outside**: What lies beyond the colony
- **Cards**: The prompts that drive the game forward
- **Journal**: First-person entries from the player

---

!!! note "A Living Document"
    This wiki is updated as the game evolves. Systems get built. Entities die. New cards fire. The documentation follows the game, not the other way around.
