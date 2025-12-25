from PySimpleGUI import LOOK_AND_FEEL_TABLE


class SimpleGuiTheme:

    def __init__(self, theme_name: str):
        self.__theme_name = theme_name

    def get_theme_name(self) -> str:
        return self.__theme_name

    @staticmethod
    def useSystemDefault():
        return SimpleGuiTheme("SystemDefault")

    @staticmethod
    def useSystemDefaultForReal():
        return SimpleGuiTheme("SystemDefaultForReal")

    @staticmethod
    def useSystemDefault1():
        return SimpleGuiTheme("SystemDefault1")

    @staticmethod
    def useMaterial1():
        return SimpleGuiTheme("Material1")

    @staticmethod
    def useMaterial2():
        return SimpleGuiTheme("Material2")

    @staticmethod
    def useReddit():
        return SimpleGuiTheme("Reddit")

    @staticmethod
    def useTopanga():
        return SimpleGuiTheme("Topanga")

    @staticmethod
    def useGreenTan():
        return SimpleGuiTheme("GreenTan")

    @staticmethod
    def useDark():
        return SimpleGuiTheme("Dark")

    @staticmethod
    def useLightGreen():
        return SimpleGuiTheme("LightGreen")

    @staticmethod
    def useDark2():
        return SimpleGuiTheme("Dark2")

    @staticmethod
    def useBlack():
        return SimpleGuiTheme("Black")

    @staticmethod
    def useTan():
        return SimpleGuiTheme("Tan")

    @staticmethod
    def useTanBlue():
        return SimpleGuiTheme("TanBlue")

    @staticmethod
    def useDarkTanBlue():
        return SimpleGuiTheme("DarkTanBlue")

    @staticmethod
    def useDarkAmber():
        return SimpleGuiTheme("DarkAmber")

    @staticmethod
    def useDarkBlue():
        return SimpleGuiTheme("DarkBlue")

    @staticmethod
    def useReds():
        return SimpleGuiTheme("Reds")

    @staticmethod
    def useGreen():
        return SimpleGuiTheme("Green")

    @staticmethod
    def useBluePurple():
        return SimpleGuiTheme("BluePurple")

    @staticmethod
    def usePurple():
        return SimpleGuiTheme("Purple")

    @staticmethod
    def useBlueMono():
        return SimpleGuiTheme("BlueMono")

    @staticmethod
    def useGreenMono():
        return SimpleGuiTheme("GreenMono")

    @staticmethod
    def useBrownBlue():
        return SimpleGuiTheme("BrownBlue")

    @staticmethod
    def useBrightColors():
        return SimpleGuiTheme("BrightColors")

    @staticmethod
    def useNeutralBlue():
        return SimpleGuiTheme("NeutralBlue")

    @staticmethod
    def useKayak():
        return SimpleGuiTheme("Kayak")

    @staticmethod
    def useSandyBeach():
        return SimpleGuiTheme("SandyBeach")

    @staticmethod
    def useTealMono():
        return SimpleGuiTheme("TealMono")

    @staticmethod
    def useDefault():
        return SimpleGuiTheme("Default")

    @staticmethod
    def useDefault1():
        return SimpleGuiTheme("Default1")

    @staticmethod
    def useDefaultNoMoreNagging():
        return SimpleGuiTheme("DefaultNoMoreNagging")

    @staticmethod
    def useGrayGrayGray():
        return SimpleGuiTheme("GrayGrayGray")

    @staticmethod
    def useLightBlue():
        return SimpleGuiTheme("LightBlue")

    @staticmethod
    def useLightGrey():
        return SimpleGuiTheme("LightGrey")

    @staticmethod
    def useLightGrey1():
        return SimpleGuiTheme("LightGrey1")

    @staticmethod
    def useDarkBrown():
        return SimpleGuiTheme("DarkBrown")

    @staticmethod
    def useLightGreen1():
        return SimpleGuiTheme("LightGreen1")

    @staticmethod
    def useDarkGrey():
        return SimpleGuiTheme("DarkGrey")

    @staticmethod
    def useLightGreen2():
        return SimpleGuiTheme("LightGreen2")

    @staticmethod
    def useDarkGrey1():
        return SimpleGuiTheme("DarkGrey1")

    @staticmethod
    def useDarkBlack():
        return SimpleGuiTheme("DarkBlack")

    @staticmethod
    def useLightBrown():
        return SimpleGuiTheme("LightBrown")

    @staticmethod
    def useLightBrown1():
        return SimpleGuiTheme("LightBrown1")

    @staticmethod
    def useDarkBlue1():
        return SimpleGuiTheme("DarkBlue1")

    @staticmethod
    def useDarkBrown1():
        return SimpleGuiTheme("DarkBrown1")

    @staticmethod
    def useDarkBlue2():
        return SimpleGuiTheme("DarkBlue2")

    @staticmethod
    def useDarkBrown2():
        return SimpleGuiTheme("DarkBrown2")

    @staticmethod
    def useDarkGreen():
        return SimpleGuiTheme("DarkGreen")

    @staticmethod
    def useLightBlue1():
        return SimpleGuiTheme("LightBlue1")

    @staticmethod
    def useLightPurple():
        return SimpleGuiTheme("LightPurple")

    @staticmethod
    def useLightBlue2():
        return SimpleGuiTheme("LightBlue2")

    @staticmethod
    def useLightGreen3():
        return SimpleGuiTheme("LightGreen3")

    @staticmethod
    def useDarkBlue3():
        return SimpleGuiTheme("DarkBlue3")

    @staticmethod
    def useLightGreen4():
        return SimpleGuiTheme("LightGreen4")

    @staticmethod
    def useLightGreen5():
        return SimpleGuiTheme("LightGreen5")

    @staticmethod
    def useLightBrown2():
        return SimpleGuiTheme("LightBrown2")

    @staticmethod
    def useLightBrown3():
        return SimpleGuiTheme("LightBrown3")

    @staticmethod
    def useLightBlue3():
        return SimpleGuiTheme("LightBlue3")

    @staticmethod
    def useLightBrown4():
        return SimpleGuiTheme("LightBrown4")

    @staticmethod
    def useDarkTeal():
        return SimpleGuiTheme("DarkTeal")

    @staticmethod
    def useDarkPurple():
        return SimpleGuiTheme("DarkPurple")

    @staticmethod
    def useLightGreen6():
        return SimpleGuiTheme("LightGreen6")

    @staticmethod
    def useDarkGrey2():
        return SimpleGuiTheme("DarkGrey2")

    @staticmethod
    def useLightBrown6():
        return SimpleGuiTheme("LightBrown6")

    @staticmethod
    def useDarkTeal1():
        return SimpleGuiTheme("DarkTeal1")

    @staticmethod
    def useLightBrown7():
        return SimpleGuiTheme("LightBrown7")

    @staticmethod
    def useDarkPurple1():
        return SimpleGuiTheme("DarkPurple1")

    @staticmethod
    def useDarkGrey3():
        return SimpleGuiTheme("DarkGrey3")

    @staticmethod
    def useLightBrown8():
        return SimpleGuiTheme("LightBrown8")

    @staticmethod
    def useDarkBlue4():
        return SimpleGuiTheme("DarkBlue4")

    @staticmethod
    def useLightBlue4():
        return SimpleGuiTheme("LightBlue4")

    @staticmethod
    def useDarkTeal2():
        return SimpleGuiTheme("DarkTeal2")

    @staticmethod
    def useDarkTeal3():
        return SimpleGuiTheme("DarkTeal3")

    @staticmethod
    def useDarkPurple5():
        return SimpleGuiTheme("DarkPurple5")

    @staticmethod
    def useDarkPurple2():
        return SimpleGuiTheme("DarkPurple2")

    @staticmethod
    def useDarkBlue5():
        return SimpleGuiTheme("DarkBlue5")

    @staticmethod
    def useLightGrey2():
        return SimpleGuiTheme("LightGrey2")

    @staticmethod
    def useLightGrey3():
        return SimpleGuiTheme("LightGrey3")

    @staticmethod
    def useDarkBlue6():
        return SimpleGuiTheme("DarkBlue6")

    @staticmethod
    def useDarkBlue7():
        return SimpleGuiTheme("DarkBlue7")

    @staticmethod
    def useLightBrown9():
        return SimpleGuiTheme("LightBrown9")

    @staticmethod
    def useDarkPurple3():
        return SimpleGuiTheme("DarkPurple3")

    @staticmethod
    def useLightBrown10():
        return SimpleGuiTheme("LightBrown10")

    @staticmethod
    def useDarkPurple4():
        return SimpleGuiTheme("DarkPurple4")

    @staticmethod
    def useLightBlue5():
        return SimpleGuiTheme("LightBlue5")

    @staticmethod
    def useDarkTeal4():
        return SimpleGuiTheme("DarkTeal4")

    @staticmethod
    def useLightTeal():
        return SimpleGuiTheme("LightTeal")

    @staticmethod
    def useDarkTeal5():
        return SimpleGuiTheme("DarkTeal5")

    @staticmethod
    def useLightGrey4():
        return SimpleGuiTheme("LightGrey4")

    @staticmethod
    def useLightGreen7():
        return SimpleGuiTheme("LightGreen7")

    @staticmethod
    def useLightGrey5():
        return SimpleGuiTheme("LightGrey5")

    @staticmethod
    def useDarkBrown3():
        return SimpleGuiTheme("DarkBrown3")

    @staticmethod
    def useLightBrown11():
        return SimpleGuiTheme("LightBrown11")

    @staticmethod
    def useDarkRed():
        return SimpleGuiTheme("DarkRed")

    @staticmethod
    def useDarkTeal6():
        return SimpleGuiTheme("DarkTeal6")

    @staticmethod
    def useDarkBrown4():
        return SimpleGuiTheme("DarkBrown4")

    @staticmethod
    def useLightYellow():
        return SimpleGuiTheme("LightYellow")

    @staticmethod
    def useDarkGreen1():
        return SimpleGuiTheme("DarkGreen1")

    @staticmethod
    def useLightGreen8():
        return SimpleGuiTheme("LightGreen8")

    @staticmethod
    def useDarkTeal7():
        return SimpleGuiTheme("DarkTeal7")

    @staticmethod
    def useDarkBlue8():
        return SimpleGuiTheme("DarkBlue8")

    @staticmethod
    def useDarkBlue9():
        return SimpleGuiTheme("DarkBlue9")

    @staticmethod
    def useDarkBlue10():
        return SimpleGuiTheme("DarkBlue10")

    @staticmethod
    def useDarkBlue11():
        return SimpleGuiTheme("DarkBlue11")

    @staticmethod
    def useDarkTeal8():
        return SimpleGuiTheme("DarkTeal8")

    @staticmethod
    def useDarkRed1():
        return SimpleGuiTheme("DarkRed1")

    @staticmethod
    def useLightBrown5():
        return SimpleGuiTheme("LightBrown5")

    @staticmethod
    def useLightGreen9():
        return SimpleGuiTheme("LightGreen9")

    @staticmethod
    def useDarkGreen2():
        return SimpleGuiTheme("DarkGreen2")

    @staticmethod
    def useLightGray1():
        return SimpleGuiTheme("LightGray1")

    @staticmethod
    def useDarkGrey4():
        return SimpleGuiTheme("DarkGrey4")

    @staticmethod
    def useDarkBlue12():
        return SimpleGuiTheme("DarkBlue12")

    @staticmethod
    def useDarkPurple6():
        return SimpleGuiTheme("DarkPurple6")

    @staticmethod
    def useDarkPurple7():
        return SimpleGuiTheme("DarkPurple7")

    @staticmethod
    def useDarkBlue13():
        return SimpleGuiTheme("DarkBlue13")

    @staticmethod
    def useDarkBrown5():
        return SimpleGuiTheme("DarkBrown5")

    @staticmethod
    def useDarkGreen3():
        return SimpleGuiTheme("DarkGreen3")

    @staticmethod
    def useDarkBlack1():
        return SimpleGuiTheme("DarkBlack1")

    @staticmethod
    def useDarkGrey5():
        return SimpleGuiTheme("DarkGrey5")

    @staticmethod
    def useLightBrown12():
        return SimpleGuiTheme("LightBrown12")

    @staticmethod
    def useDarkTeal9():
        return SimpleGuiTheme("DarkTeal9")

    @staticmethod
    def useDarkBlue14():
        return SimpleGuiTheme("DarkBlue14")

    @staticmethod
    def useLightBlue6():
        return SimpleGuiTheme("LightBlue6")

    @staticmethod
    def useDarkGreen4():
        return SimpleGuiTheme("DarkGreen4")

    @staticmethod
    def useDarkGreen5():
        return SimpleGuiTheme("DarkGreen5")

    @staticmethod
    def useDarkTeal10():
        return SimpleGuiTheme("DarkTeal10")

    @staticmethod
    def useDarkGrey6():
        return SimpleGuiTheme("DarkGrey6")

    @staticmethod
    def useDarkTeal11():
        return SimpleGuiTheme("DarkTeal11")

    @staticmethod
    def useLightBlue7():
        return SimpleGuiTheme("LightBlue7")

    @staticmethod
    def useLightGreen10():
        return SimpleGuiTheme("LightGreen10")

    @staticmethod
    def useDarkBlue15():
        return SimpleGuiTheme("DarkBlue15")

    @staticmethod
    def useDarkBlue16():
        return SimpleGuiTheme("DarkBlue16")

    @staticmethod
    def useDarkTeal12():
        return SimpleGuiTheme("DarkTeal12")

    @staticmethod
    def useLightBrown13():
        return SimpleGuiTheme("LightBrown13")

    @staticmethod
    def useDarkBlue17():
        return SimpleGuiTheme("DarkBlue17")

    @staticmethod
    def useDarkBrown6():
        return SimpleGuiTheme("DarkBrown6")

    @staticmethod
    def useDarkGreen6():
        return SimpleGuiTheme("DarkGreen6")

    @staticmethod
    def useDarkGreen7():
        return SimpleGuiTheme("DarkGreen7")

    @staticmethod
    def useDarkGrey7():
        return SimpleGuiTheme("DarkGrey7")

    @staticmethod
    def useDarkRed2():
        return SimpleGuiTheme("DarkRed2")

    @staticmethod
    def useLightGrey6():
        return SimpleGuiTheme("LightGrey6")

    @staticmethod
    def useHotDogStand():
        return SimpleGuiTheme("HotDogStand")

    @staticmethod
    def useDarkGrey8():
        return SimpleGuiTheme("DarkGrey8")

    @staticmethod
    def useDarkGrey9():
        return SimpleGuiTheme("DarkGrey9")

    @staticmethod
    def useDarkGrey10():
        return SimpleGuiTheme("DarkGrey10")

    @staticmethod
    def useDarkGrey11():
        return SimpleGuiTheme("DarkGrey11")

    @staticmethod
    def useDarkGrey12():
        return SimpleGuiTheme("DarkGrey12")

    @staticmethod
    def useDarkGrey13():
        return SimpleGuiTheme("DarkGrey13")

    @staticmethod
    def useDarkGrey14():
        return SimpleGuiTheme("DarkGrey14")

    @staticmethod
    def useDarkGrey15():
        return SimpleGuiTheme("DarkGrey15")

    @staticmethod
    def useDarkBrown7():
        return SimpleGuiTheme("DarkBrown7")

    @staticmethod
    def usePython():
        return SimpleGuiTheme("Python")

    @staticmethod
    def usePythonPlus():
        return SimpleGuiTheme("PythonPlus")


if __name__ == '__main__':
    for key in LOOK_AND_FEEL_TABLE.keys():
        print(f'@staticmethod\ndef use{key}():\n    return SimpleGuiTheme("{key}")\n\n')
