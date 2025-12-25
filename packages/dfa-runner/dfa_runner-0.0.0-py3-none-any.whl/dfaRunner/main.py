from __future__ import annotations
import toml
import os
from pathlib import Path
import argparse


class StateError(Exception):
    pass


class LanguageError(Exception):
    pass


class DFAParseError(Exception):
    pass


class State:
    def __init__(self, name: str):
        if not isinstance(name, str):
            raise TypeError("Not type str")
        self.stateName = name

    def __eq__(self, other):
        return isinstance(other, State) and other.stateName == self.stateName


class StateTransition:
    def __init__(self, stateStart: State, stateEnd: State, transitionChar: str):
        if not isinstance(stateStart, State) or not isinstance(stateEnd, State):
            raise TypeError(f"Not type State")
        if not isinstance(transitionChar, str):
            raise TypeError("Not type str")
        self.stateStart = stateStart
        self.stateEnd = stateEnd
        self.transitionChar = transitionChar

    @classmethod
    def from_str(cls, string: str):
        string = string.replace("\n", "")
        string = string.replace("\t", "")
        string = string.replace(" ", "")
        if "-(" not in string or ")->" not in string:
            raise DFAParseError("Invalid State Transition Syntax")
        stateStart = State(string.split("-(")[0])
        stateEnd = State(string.split(")->")[1])
        transitionChar = string.split("-(")[1].split(")->")[0]
        return cls(stateStart, stateEnd, transitionChar)

    def toStr(self):
        return f"{self.stateStart.stateName}-({self.transitionChar})->{self.stateEnd.stateName}"


class DefiniteFiniteAutomata:

    def __init__(
        self,
        states: list,
        acceptingStates: list,
        startState: State,
        transitions: list,
        language: list,
        verbose=False,
    ):
        self.states = []
        self.accepting = []
        self.startState = None
        self.language = language
        self.transitions = []
        for state in states:
            if not isinstance(state, State):
                raise TypeError(f"Not type State, is type {type(state)}")
            if verbose:
                print(f"Appending {state.stateName} to states")
            self.states.append(state)

        for state in acceptingStates:
            if not isinstance(state, State):
                raise TypeError(f"Not type State, is type {type(state)}")
            if state not in states:
                raise StateError("Accepting state not found in states")
            if verbose:
                print(f"Appending {state.stateName} to accepting states")
            self.accepting.append(state)

        if not isinstance(startState, State):
            raise TypeError(f"Not type State, is type {type(state)}")
        if startState not in states:
            raise StateError("Starting state not found in states")
        if verbose:
            print(f"Setting {startState.stateName} to start state")
        self.startState = startState

        for transition in transitions:
            if not isinstance(transition, StateTransition):
                raise TypeError("Not type StateTransition")
            if transition.transitionChar not in language:
                raise LanguageError("Not in Language")
            if transition.stateStart in states and transition.stateEnd in states:
                index = states.index(transition.stateStart)
                state = states[index]
                if verbose:
                    print(f"Adding {transition.toStr()} to transitions")
                self.transitions.append(transition)
            else:
                raise StateError("Transition state not found in states")

    @classmethod
    def from_toml(cls, file: str, verbose=False):
        dfaToml = ""
        with open(file, "r") as f:
            dfaToml = toml.load(f)
        f.close()
        states = []
        acceptingStates = []
        transitions = []
        for entry in dfaToml["states"]:
            states.append(State(entry))
        for entry in dfaToml["accept"]:
            acceptingStates.append(State(entry))
        startState = State(dfaToml["start"])
        language = dfaToml["language"]
        for entry in dfaToml["transitions"]:
            transitions.append(StateTransition.from_str(entry))

        # states: list, acceptingStates: list, startState: State, transitions: list, language: list

        return cls(states, acceptingStates, startState, transitions, language)

    def testWord(self, word: str):
        state = self.startState
        for char in word:
            state = self.next(state, char)
        return state in self.accepting

    def testWordVerbose(self, word: str):
        state = self.startState
        print(f"{state.stateName} ", end="")
        for char in word:
            state = self.next(state, char)
            print(f"-> {state.stateName} ", end="")
        print("")
        return state in self.accepting

    def next(self, state, char: str):
        for trans in self.transitions:
            if trans.stateStart == state and trans.transitionChar == char:
                return trans.stateEnd

        raise LanguageError(f"{char} not in language")

    def getStates(self):
        stateList = []
        for state in self.states:
            stateList.append(str(state))
        return stateList

    def getAcceptingStates(self):
        stateList = []
        for state in self.accepting:
            stateList.append(str(state))
        return stateList

    def printTransitions(self):
        for transition in self.transitions:
            print(transition.toStr())


def cli():
    parser = argparse.ArgumentParser(
        description="Run words through A DFA specified in a given toml file"
    )
    parser.add_argument(
        "dfa", help="DFA in toml format (check examples folder for examples)"
    )
    parser.add_argument("word", help="The word to be tested through the DFA")
    args = parser.parse_args()
    path = Path(args.dfa)
    if not path.is_absolute():
        path = (Path(os.getcwd()) / path).resolve(strict=False)
    dfaFile = path
    dfa = DefiniteFiniteAutomata.from_toml(str(dfaFile))
    word = args.word
    print(f"Testing {word}")
    result = dfa.testWordVerbose(word)
    print(f"Result - {result}")
    return
