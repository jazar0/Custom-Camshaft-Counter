import random
class MasterMind:
    def __init__(self, name):
        self.codes = []
        self.name = name
        self.results = []
        for i in range(0,9):
            self.results.append((0,0))

        self.possibleCodes = ["RED", "GREEN", "BLUE", "YELLOW", "ORANGE", "PURPLE"]
        print("MasterMind Initialized")

    def newCode(self):
        self.codes = []
        for i in range(0,4):
            self.codes.append(self.possibleCodes[random.randint(0,len(self.possibleCodes)-1)])
        print("Codes:", self.codes)

    def getResults(self):
        return self.results

    def guess(self, iGuess, iRow):
        print("Answer:", self.codes)
        print("Guess:", iGuess)
        bMatch = True
        wGuess = iGuess.copy()
        wAnswer = self.codes.copy()
        oBlack = 0
        oWhite = 0
        if len(iGuess) != len(self.codes):
            print("Error: length of guess and codes must be the same")
        else:
            while bMatch:
                bMatch = False
                # check for black
                for i in range(0, len(iGuess)):
                    if wGuess[i] == wAnswer[i]:
                        oBlack += 1
                        wGuess[i] = "x"
                        wAnswer[i] = ""
                        bMatch = True
                for i in range(0, len(iGuess)):
                    for j in range(0, len(wAnswer)):
                        if wGuess[i] == wAnswer[j]:
                            oWhite += 1
                            wGuess[i] = "x"
                            wAnswer[j] = ""
                            bMatch = True

        print(f'Results are {oBlack} Black and {oWhite} White.')
        self.results[iRow]=(oBlack, oWhite)
        return oBlack, oWhite



