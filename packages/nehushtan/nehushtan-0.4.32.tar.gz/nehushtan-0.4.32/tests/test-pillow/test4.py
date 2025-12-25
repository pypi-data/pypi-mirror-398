from nehushtan.score.NotationTextParser import NotationTextParser
from nehushtan.score.ScoreDrawer import ScoreDrawer
from nehushtan.score.ScoreDrawerOptions import ScoreDrawerOptions

if __name__ == '__main__':
    file = "/debug/score/00"
    parser = NotationTextParser(file=file)
    parser.parse()
    # parser.debug()
    font1 = "/Users/leqee/code/Verbum/fonts/Arial Unicode.ttf"
    font2 = "/Users/leqee/code/Verbum/fonts/FangZhengKaiTi-GBK/FangZhengKaiTi-GBK-1.ttf"

    options = ScoreDrawerOptions(font1, 50)
    options.set_lyric_font_path(font1)
    options.set_lyric_font_size(40)
    options.set_score_font_size(40)
    options.set_title_left_component_font_size(30)
    options.set_title_right_component_font_size(30)
    options.set_title_middle_component_font_size(70)

    options.set_total_cells_in_one_line(32)

    drawer = ScoreDrawer(parser.get_parsed_score_lines(), options)
    # drawer.show("test4")
    drawer.save("/Users/leqee/code/nehushtan/debug/score/book.png")
