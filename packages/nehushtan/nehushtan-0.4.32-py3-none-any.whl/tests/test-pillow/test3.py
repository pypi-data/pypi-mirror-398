from nehushtan.score.NotationTextParser import NotationTextParser
from nehushtan.score.ScoreDrawer import ScoreDrawer
from nehushtan.score.ScoreDrawerOptions import ScoreDrawerOptions

text = """
~ 1=A 4/4 | 第一百零六首 | 主的复活
5-:MP 5 6 | 6 5 5- | 5- 4 6 | 6- 5- |
>1> 祂 躺卧 在坟墓  耶 稣我 救 主
6- 7 1> | 1> 5 5- | 6- 5 #4 | 5--- |
> 静 待晨 光重曙  耶 稣我 主
1 1_.:F 1__ 3 5_. 5__ | 1>-- 1>_. 2>__ | 3> 1> 2>._ 1>__ 7_. 6__ | 5-- |
>和> 祂从 坟墓已 起 来  胜 过 仇敌大 大的 奏 凯
7_. 1>__ | 2> 2> 2>_. 1>__ 2>_. 3>__ | 1> 6 5 |
> 祂 从 黑域起 来祂 是 得胜者
 5_. 5__ | 6 6 6_. 2>__ 2>_. 1>__ | 7:RIT 1> 2> 5_. 5__ | 3>-- |
> 活 着 掌权同 祂众 圣 徒联合祂 起 来  
2>_. 1>__ | 4>-- | 3>_. 2>__ | 1> 5 3>:>RIT 2> | 1>--- ||
> 祂 起 来   阿 利 路亚主起 来
>2> 兵丁徒然看守，耶稣我救主！
> < 石头徒然封口，耶稣我主！
>3= 死亡无法锁关，耶稣我救主！
> = 祂已打断栅栏，耶稣我主！
( 1 2 ) 3. 0_ | 5_. 6__ 7~ 1> | ( 5_ 3_ 1_ )3 5<-- ||
>测> 啊哈哈哈
"""

if __name__ == '__main__':
    parser = NotationTextParser(text=text)
    parser.parse()
    parser.debug()
    font_path = "/Users/leqee/code/Verbum/fonts/Arial Unicode.ttf"

    font2 = "/Users/leqee/code/Verbum/fonts/优设好身体/YSHaoShenTi-2.ttf"

    options = ScoreDrawerOptions(font_path, 50)
    options.set_lyric_font_path(font2)
    drawer = ScoreDrawer(parser.get_parsed_score_lines(), options)
    drawer.show("test3")
