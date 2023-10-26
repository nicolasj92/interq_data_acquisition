class NCTranslator:
    def __init__(self):
        self.states = [
            {
                "begin": 10015,
                "end": 10021,
                "program_state": {
                    "trigger": "program_start",
                    "process": "planfraesen",
                    "part": "bauteil_1",
                    "tool": "SPIKE_D50",
                },
                "visited": False,
            },
            {
                "begin": 10021,
                "end": 10029,
                "program_state": {
                    "trigger": "spike_stop",
                    "process": "planfraesen",
                    "part": "bauteil_1",
                    "tool": "SPIKE_D50",
                },
                "visited": False,
            },
            {
                "begin": 10029,
                "end": 10032,
                "program_state": {
                    "trigger": "spike_start",
                    "process": "aussenkontur_schruppen_schlichten",
                    "part": "bauteil_1",
                    "tool": "SPIKE_D10",
                },
                "visited": False,
            },
            {
                "begin": 10032,
                "end": 10038,
                "program_state": {
                    "trigger": "spike_stop",
                    "process": "aussenkontur_schruppen_schlichten",
                    "part": "bauteil_1",
                    "tool": "SPIKE_D10",
                },
                "visited": False,
            },
            {
                "begin": 10038,
                "end": 10041,
                "program_state": {
                    "trigger": "spike_start",
                    "process": "nut_seitlich",
                    "part": "bauteil_1",
                    "tool": "SPIKE_D6",
                },
                "visited": False,
            },
            {
                "begin": 10041,
                "end": 10049,
                "program_state": {
                    "trigger": "spike_stop",
                    "process": "nut_seitlich",
                    "part": "bauteil_1",
                    "tool": "SPIKE_D6",
                },
                "visited": False,
            },
            {
                "begin": 10049,
                "end": 10060,
                "program_state": {
                    "trigger": "section",
                    "process": "stufenbohrung",
                    "part": "bauteil_1",
                    "tool": "BO_6.6",
                },
                "visited": False,
            },
            {
                "begin": 10068,
                "end": 10083,
                "program_state": {
                    "trigger": "section",
                    "process": "endgraten_aussenkontur_bohrungen",
                    "part": "bauteil_1",
                    "tool": "EG_10",
                },
                "visited": False,
            },
            {
                "begin": 10097,
                "end": 10100,
                "program_state": {
                    "trigger": "section",
                    "process": "bohren_seitlich",
                    "part": "bauteil_1",
                    "tool": "BO_8.6",
                },
                "visited": False,
            },
            {
                "begin": 10107,
                "end": 10113,
                "program_state": {
                    "trigger": "section",
                    "process": "bohren_senken",
                    "part": "bauteil_1",
                    "tool": "EG_10",
                },
                "visited": False,
            },
            {
                "begin": 10120,
                "end": 10125,
                "program_state": {
                    "trigger": "section",
                    "process": "bohren",
                    "part": "bauteil_1",
                    "tool": "BO_5",
                },
                "visited": False,
            },
            {
                "begin": 10132,
                "end": 10141,
                "program_state": {
                    "trigger": "section",
                    "process": "gewinde_fraesen",
                    "part": "bauteil_1",
                    "tool": "SW_G_einachtel",
                },
                "visited": False,
            },
            {
                "begin": 10156,
                "end": 10166,
                "program_state": {
                    "trigger": "spike_start",
                    "process": "planfraesen",
                    "part": "bauteil_2",
                    "tool": "SPIKE_D50",
                },
                "visited": False,
            },
            {
                "begin": 10166,
                "end": 10174,
                "program_state": {
                    "trigger": "spike_stop",
                    "process": "planfraesen",
                    "part": "bauteil_2",
                    "tool": "SPIKE_D50",
                },
                "visited": False,
            },
            {
                "begin": 10174,
                "end": 10177,
                "program_state": {
                    "trigger": "spike_start",
                    "process": "kreistasche_fraesen",
                    "part": "bauteil_2",
                    "tool": "SPIKE_D10",
                },
                "visited": False,
            },
            {
                "begin": 10177,
                "end": 10184,
                "program_state": {
                    "trigger": "spike_stop",
                    "process": "kreistasche_fraesen",
                    "part": "bauteil_2",
                    "tool": "SPIKE_D10",
                },
                "visited": False,
            },
            {
                "begin": 10184,
                "end": 10200,
                "program_state": {
                    "trigger": "section",
                    "process": "bauteil_entgraten",
                    "part": "bauteil_2",
                    "tool": "EG_10",
                },
                "visited": False,
            },
            {
                "begin": 10207,
                "end": 10215,
                "program_state": {
                    "trigger": "program_end",
                    "process": "ringnut",
                    "part": "bauteil_2",
                    "tool": "SW_D40",
                },
                "visited": False,
            },
        ]

    def __call__(self, ncline):

        if ncline is None or len(ncline) < 2:
            return None
        else:
            ncnumber = int(ncline[1:])         

        for index, state in enumerate(self.states):
            if ncnumber >= state["begin"] and ncnumber <= state["end"]:
                if state["visited"] == False:
                    state["visited"] = True

                    # reset "visited" state of previous item, so that it can be accessed more than once per program run
                    #if index > 0:
                    #    self.states[index - 1]["visited"] == False
                    #else:
                    #    self.states[len(self.states) - 1]["visited"] == False
                    if state['program_state']['trigger'] == 'program_end':
                        for state in self.states:
                            state['visited'] = False
                
                    return state["program_state"]
               
        return None

