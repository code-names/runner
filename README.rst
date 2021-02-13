=====================
Code-names Bot Runner
=====================

Bot runner for code-names bots.

Running a game
==============

.. code-block:: python

   from runner import Game
   winner = Game.from_seed_and_commands(
       100,
       ('A', ['python', '-O', 'sample_clue_giver.py'], ['python', '-O', 'sample_guesser.py']),
       ('B', ['python', '-O', 'sample_clue_giver.py'], ['python', '-O', 'sample_guesser.py']),
   ).run()

Bot Interface (WIP)
===================

A bot reads commands over stdin and writes actions to stdout.
The format of the commands can be seen in the two sample bots.

TODO
====

- general code cleanup
- CLI
- make ``vocabulary``, ``TOTAL_CARDS``, and ``TEAM_CARDS`` configurable
- enforce guess count is less than the clue count
- shut down bot processes
