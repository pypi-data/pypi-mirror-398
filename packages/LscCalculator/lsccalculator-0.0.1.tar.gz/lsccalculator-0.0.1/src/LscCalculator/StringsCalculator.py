class StringsCalculator:
    def __init__(self):
        pass

    def addition(self, *addends):
        self.__init__()
        result = ""

        if type(addends[0]) is list:
            addends = addends[0]

        for addend in addends:
            result += addend

        return result


sc = SC = StringsCalculator

if __name__ == '__main__':
    print(sc().addition("123", "我是最棒的", "dfjik"))
