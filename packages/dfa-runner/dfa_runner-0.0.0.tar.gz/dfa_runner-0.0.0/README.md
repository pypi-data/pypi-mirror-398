# dfaRunner

Run words through a Deterministic Finite Automaton (DFA) specified in a TOML file.

## TOML Format
Example of formatting here:

```toml
states = ["s", "q", "r"]
accept = ["q"]
start = "s"
language = ["a", "b"]
transitions = ["s-(a)->s", "s-(b)->q", "q-(a)->r", "q-(b)->q", "r-(a)->r", "r-(b)->r"]
