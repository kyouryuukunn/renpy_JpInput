init -1 python in JpInput:
    # 現在のカーソル位置の色設定
    cursor_color = "#0FF" 
    # モバイル版でもキーボード入力を有効にする
    allow_keyboard_in_mobile = False

    # 現在のカーソル位置
    pos = 0
    # 入力テキスト
    inputted_text = ""
    # 未確定位置
    preconverted_pos = [0, 0]
    ime_mode = None
    # 変換中テキスト
    preconverted_text = ""
    last_result = ""

    def jpinput(prompt, default='', with_none=None, linux_prompt='', mobile_prompt=''):
        #アクションの初期化は繰り返えし呼び出されるのでここで処理する
        jpinput_init(default)
        #開発用
        # return renpy.input(prompt, default=default, with_none=with_none, screen="jpinput")
        #ブラウザ含むモバイルでは日本語対応スクリーンキーボード、Win, macではその通常のinput関数を使用
        # Linuxでは日本語対応のインプットスクリーンを使用するが、変換、無変換等の日本語キーボードキーにショートカットを割り当てできないのでプロンプトに説明を入れる
        if renpy.mobile:
            if not mobile_prompt:
                mobile_prompt = prompt
            return renpy.input(mobile_prompt, default=default, with_none=with_none, screen="jpinput")
        elif renpy.linux:
            if not linux_prompt:
                linux_prompt = prompt
            return renpy.input(linux_prompt, default=default, with_none=with_none, screen="jpinput")
        else:
            return renpy.input(prompt, default=default, with_none=with_none, screen="input")

    def jpinput_init(default):
        global pos, inputted_text, preconverted_pos
        pos = len(default)
        preconverted_pos = [pos, pos]
        inputted_text = default + "{color=" + cursor_color + "}|{/color}"
        
    # ローマ字からひらがな、カタカナ変換
    def convert(text):
        global ime_mode, roma_table
        if ime_mode is None:
            return text
        else:
            result = ""
            while text:
                if 1 < len(text) and text[0] == text[0+1] and text[0] != 'n':
                    for i, hira, kana in roma_table:
                        if text[1:].startswith(i):
                            if ime_mode == "hira":
                                result += "っ" + hira
                            if ime_mode == "kana":
                                result += "ッ" + kana
                            text = text[len(i)+1:]
                            break
                    else:
                        result += text[0]
                        text = text[1:]
                else:
                    for i, hira, kana in roma_table:
                        if text.startswith(i):
                            if ime_mode == "hira":
                                result += hira
                            if ime_mode == "kana":
                                result += kana
                            text = text[len(i):]
                            break
                    else:
                        if 1 < len(text) and text[0] == 'n' and text[1] != 'y':
                            if ime_mode == "hira":
                                result += "ん"
                            if ime_mode == "kana":
                                result += "ン"
                            text = text[1:]
                        else:
                            result += text[0]
                            text = text[1:]

            return result

    # ひらがなから漢字変換
    def convert2(text):
        global preconverted_text, last_result

        if has_kana(text):
            result = preconverted_text = to_hira(text)
            return result

        if not preconverted_text:
            preconverted_text = text
        result = last_result = hira_to_kanji(preconverted_text, last_result)
        # 検索結果が見付からなければリセットしてカナへ
        if not result:
            result = to_kana(preconverted_text)
        return result

    def has_kana(text):
        global kana_table
        for i in text:
            if i in kana_table:
                return True
        else:
            return False

    def to_hira(text):
        global kana_table, hira_table
        result = ""
        for i in text:
            if i in kana_table:
                result += hira_table[kana_table.index(i)]
            else:
                result += i
        return result

    def to_kana(text):
        global kana_table, hira_table
        result = ""
        for i in text:
            if i in hira_table:
                result += kana_table[hira_table.index(i)]
            else:
                result += i
        return result

    def hira_to_kanji(text, last_result):
        global hennkan_table
        candidates = hennkan_table.get(text)
        if candidates:
            candidates = tuple(candidates)
            if last_result in candidates:
                last_index = candidates.index(last_result)
                if last_index+1 < len(candidates):
                    return candidates[last_index+1]
                else:
                    return ""
            else:
                return candidates[0]
        else:
            return ""

    def remove_tag(text):
        result = ""
        for i in text:
            if i == "[":
                result += "[["
            elif i == "{":
                result += "{{"
            else:
                result += i
        return result

    class JpInput(renpy.ui.Action):
        def __init__(self, key):
            self.key = key

        def __call__(self):
            global pos, inputted_text, preconverted_pos, ime_mode, cursor_color, preconverted_text, last_result

            # 初期値にもカーソルを表示する
            if inputted_text.find("{color=" + cursor_color + "}|{/color}") >= 0:
                inputted_text = inputted_text[:-len("{color=" + cursor_color + "}|{/color}")]

            cs = renpy.current_screen()

            if cs is None:
                return

            org_len = len(inputted_text)
            pre_start, pre_end = preconverted_pos
            if preconverted_text and self.key not in {"SPACE", "HENKAN", "RETURN"}:
                # 変換中に変換以外のなにかをしたら確定にする
                preconverted_text = ""
                last_result = ""
                pre_start =  pre_end = pos
            if self.key not in {"RETURN", "SPACE", "HENKAN", "HOME", "END", "LEFT", "RIGHT", "BACKSPACE", "DELETE"}:
                inputted_text = inputted_text[:pos] + self.key + inputted_text[pos:]
                inputted_text = inputted_text[:pre_start] + convert(inputted_text[pre_start:pre_end+1]) + inputted_text[pre_end+1:]

                pos_diff = len(inputted_text) - org_len
                if ime_mode is None:
                    pos += pos_diff
                    pre_start = pre_end = pos
                else:
                    pos += pos_diff
                    pre_end += pos_diff

            else:
                if self.key == "HENKAN":
                    inputted_text = inputted_text[:pre_start] + convert2(inputted_text[pre_start:pre_end+1]) + inputted_text[pre_end+1:]
                    pos_diff = len(inputted_text) - org_len
                    pre_end += pos_diff
                    pos = pre_end
                if self.key == "RETURN":
                    if pre_start == pre_end:
                        return inputted_text
                    else:
                        preconverted_text = ""
                        last_result = ""
                        pre_start =  pre_end = pos
                if self.key == "SPACE":
                    if pre_start == pre_end:
                        inputted_text = inputted_text[:pos] + " " + inputted_text[pos:]
                        inputted_text = inputted_text[:pre_start] + convert(inputted_text[pre_start:pre_end+1]) + inputted_text[pre_end+1:]
                        pos += 1
                        pre_start = pre_end = pos
                    else:
                        inputted_text = inputted_text[:pre_start] + convert2(inputted_text[pre_start:pre_end+1]) + inputted_text[pre_end+1:]
                        pos_diff = len(inputted_text) - org_len
                        pre_end += pos_diff
                        pos = pre_end
                if (self.key == "LEFT" and pos > 0) and (pre_start == pre_end or pos > pre_start):
                    if pre_start == pre_end:
                        pos -= 1
                        pre_start = pre_end = pos
                    else:
                        pos -= 1
                if (self.key == "RIGHT" and pos < len(inputted_text)) and (pre_start == pre_end or pos < pre_end):
                    if pre_start == pre_end:
                        pos += 1
                        pre_start = pre_end = pos
                    else:
                        pos += 1
                if (self.key == "HOME" and pos > 0) and (pre_start == pre_end or pos > pre_start):
                    if pre_start == pre_end:
                        pos = 0
                        pre_start = pre_end = pos
                    else:
                        pos = pre_start
                if (self.key == "END" and pos < len(inputted_text)) and (pre_start == pre_end or pos < pre_end):
                    if pre_start == pre_end:
                        pos = len(inputted_text)
                        pre_start = pre_end = pos
                    else:
                        pos = pre_end
                if self.key == "BACKSPACE" and pos > 0:
                    if pre_end > pre_start:
                        if pos > pre_start: # 変換中
                            inputted_text = inputted_text[:pos-1] + inputted_text[pos:]
                            pos -= 1
                            pre_end -= 1
                    else:
                        inputted_text = inputted_text[:pos-1] + inputted_text[pos:]
                        pos -= 1
                        pre_start = pre_end = pos
                if self.key == "DELETE" and pos < len(inputted_text):
                    if pre_end > pre_start:
                        if pos < pre_end: # 変換中
                            inputted_text = inputted_text[:pos] + inputted_text[pos+1:]
                            pre_end -= 1
                    else:
                        inputted_text = inputted_text[:pos] + inputted_text[pos+1:]

            if pos >= pre_end:
                formated_text = remove_tag(inputted_text[:pre_start]) + "{u}" + remove_tag(inputted_text[pre_start:pre_end]) + "{/u}" \
                                + "{color=" + cursor_color + "}|{/color}" + remove_tag(inputted_text[pos:])
            else:
                formated_text = remove_tag(inputted_text[:pre_start]) + "{u}" + remove_tag(inputted_text[pre_start:pos]) \
                                + "{color=" + cursor_color + "}|{/color}" + remove_tag(inputted_text[pos:pre_end]) + "{/u}" + remove_tag(inputted_text[pre_end:])
            cs.scope["jp_inputted_text"] = formated_text
            preconverted_pos = [pre_start, pre_end]
            renpy.restart_interaction()



##############################################################################
# jpinput
#
# input スクリーンの日本語語IME組み込み版
# quick_menuを組み込みでいるので使わない場合は削除すること
screen jpinput(prompt):
    default jp_inputted_text = renpy.get_widget_properties("input")["default"]
    default jp_input_allow_text = renpy.get_widget_properties("input")["allow"]
    default jp_input_exclude_text = renpy.get_widget_properties("input")["exclude"]
    default jp_input_length = renpy.get_widget_properties("input")["length"]
    if (not renpy.mobile) or (renpy.mobile and JpInput.allow_keyboard_in_mobile):
        key "a" action JpInput.JpInput("a")
        key "b" action JpInput.JpInput("b")
        key "c" action JpInput.JpInput("c")
        key "d" action JpInput.JpInput("d")
        key "e" action JpInput.JpInput("e")
        key "f" action JpInput.JpInput("f")
        key "g" action JpInput.JpInput("g")
        key "h" action JpInput.JpInput("h")
        key "i" action JpInput.JpInput("i")
        key "j" action JpInput.JpInput("j")
        key "k" action JpInput.JpInput("k")
        key "l" action JpInput.JpInput("l")
        key "m" action JpInput.JpInput("m")
        key "n" action JpInput.JpInput("n")
        key "o" action JpInput.JpInput("o")
        key "p" action JpInput.JpInput("p")
        key "q" action JpInput.JpInput("q")
        key "r" action JpInput.JpInput("r")
        key "s" action JpInput.JpInput("s")
        key "t" action JpInput.JpInput("t")
        key "u" action JpInput.JpInput("u")
        key "v" action JpInput.JpInput("v")
        key "w" action JpInput.JpInput("w")
        key "x" action JpInput.JpInput("x")
        key "y" action JpInput.JpInput("y")
        key "z" action JpInput.JpInput("z")
        key "A" action JpInput.JpInput("A")
        key "B" action JpInput.JpInput("B")
        key "C" action JpInput.JpInput("C")
        key "D" action JpInput.JpInput("D")
        key "E" action JpInput.JpInput("E")
        key "F" action JpInput.JpInput("F")
        key "G" action JpInput.JpInput("G")
        key "H" action JpInput.JpInput("H")
        key "I" action JpInput.JpInput("I")
        key "J" action JpInput.JpInput("J")
        key "K" action JpInput.JpInput("K")
        key "L" action JpInput.JpInput("L")
        key "M" action JpInput.JpInput("M")
        key "N" action JpInput.JpInput("N")
        key "O" action JpInput.JpInput("O")
        key "P" action JpInput.JpInput("P")
        key "Q" action JpInput.JpInput("Q")
        key "R" action JpInput.JpInput("R")
        key "S" action JpInput.JpInput("S")
        key "T" action JpInput.JpInput("T")
        key "U" action JpInput.JpInput("U")
        key "V" action JpInput.JpInput("V")
        key "W" action JpInput.JpInput("W")
        key "X" action JpInput.JpInput("X")
        key "Y" action JpInput.JpInput("Y")
        key "Z" action JpInput.JpInput("Z")
        key "1" action JpInput.JpInput("1")
        key "2" action JpInput.JpInput("2")
        key "3" action JpInput.JpInput("3")
        key "4" action JpInput.JpInput("4")
        key "5" action JpInput.JpInput("5")
        key "6" action JpInput.JpInput("6")
        key "7" action JpInput.JpInput("7")
        key "8" action JpInput.JpInput("8")
        key "9" action JpInput.JpInput("9")
        key "0" action JpInput.JpInput("0")
        key "`" action JpInput.JpInput("`")
        key "|" action JpInput.JpInput("|")
        key "-" action JpInput.JpInput("-")
        key "^" action JpInput.JpInput("^")
        key "\\" action JpInput.JpInput("\\")
        key "@" action JpInput.JpInput("@")
        key ";" action JpInput.JpInput(";")
        key ":" action JpInput.JpInput(":")
        key "!" action JpInput.JpInput("!")
        key "\""action JpInput.JpInput("\"")
        key "#" action JpInput.JpInput("#")
        key "$" action JpInput.JpInput("$")
        key "%" action JpInput.JpInput("%")
        key "&" action JpInput.JpInput("&")
        key "'" action JpInput.JpInput("'")
        key "(" action JpInput.JpInput("(")
        key ")" action JpInput.JpInput(")")
        key "~" action JpInput.JpInput("~")
        key "{" action JpInput.JpInput("{")
        key "}" action JpInput.JpInput("}")
        key "*" action JpInput.JpInput("*")
        key "+" action JpInput.JpInput("+")
        key "<" action JpInput.JpInput("<")
        key ">" action JpInput.JpInput(">")
        key "?" action JpInput.JpInput("?")
        key "/" action JpInput.JpInput("/")
        key "[" action JpInput.JpInput("[")
        key "]" action JpInput.JpInput("]")
        key "=" action JpInput.JpInput("=")
        key "K_UNDERSCORE" action JpInput.JpInput("_")
        key "K_SPACE" action JpInput.JpInput("SPACE")
        key "K_BACKSPACE" action JpInput.JpInput("BACKSPACE")
        key "K_DELETE" action JpInput.JpInput("DELETE")
        key "K_LEFT" action JpInput.JpInput("LEFT")
        key "K_RIGHT" action JpInput.JpInput("RIGHT")
        key "K_HOME" action JpInput.JpInput("HOME")
        key "K_END" action JpInput.JpInput("END")
        key "K_RETURN" action JpInput.JpInput("RETURN")
        key "K_F1" action ToggleVariable("JpInput.ime_mode", "hira", None)
        key "K_F2" action ToggleVariable("JpInput.ime_mode", "kana", None)
        key "K_F3" action JpInput.JpInput("HENKAN")

    if renpy.mobile:
        vbox:
            window style "input_window":
                yalign 0.1
                has vbox

                text prompt style "input_prompt"
                text jp_inputted_text style "input_text"
            use _jp_touch_keyboard
    else:
        window style "input_window":
            has vbox

            text prompt style "input_prompt"
            text jp_inputted_text style "input_text"

    use quick_menu


init -1:

    style _jp_touch_keyboard_button:
        hover_background "#f00"

    style _jp_touch_keyboard_button_text:
        color "#fff"
        outlines [ (absolute(3), "#000", absolute(0), absolute(0)) ]
        size gui._scale(55)
        min_width gui._scale(55)
        text_align 0.5

    screen _jp_touch_keyboard():
        zorder 100
        # style_prefix "_jp_touch_keyboard"
        tag screen_keyboard
        default shift_on = False
        style_prefix "_jp_touch_keyboard"
  

        showif shift_on:
            vbox:
                at _touch_keyboard
                spacing 20

                hbox:
                    textbutton "半/全" action ToggleVariable("JpInput.ime_mode", "hira", None)
                    textbutton "!"  action JpInput.JpInput('!')
                    textbutton "\"" action JpInput.JpInput('\"')
                    textbutton "#"  action JpInput.JpInput('#')
                    textbutton "$"  action JpInput.JpInput('$')
                    textbutton "%"  action JpInput.JpInput('%')
                    textbutton "&"  action JpInput.JpInput('&')
                    textbutton "'"  action JpInput.JpInput("'")
                    textbutton "("  action JpInput.JpInput('(')
                    textbutton ")"  action JpInput.JpInput(')')
                    textbutton " "  action NullAction()                          
                    textbutton "="  action JpInput.JpInput('=')
                    textbutton "~"  action JpInput.JpInput('~')
                    textbutton "|"  action JpInput.JpInput('|')
                    textbutton " BS " action JpInput.JpInput('BACKSPACE')
                    textbutton " Del " action JpInput.JpInput('DELETE')
                hbox:
                    xpos 0.15
                    textbutton "Q" action JpInput.JpInput("Q")
                    textbutton "W" action JpInput.JpInput("W")
                    textbutton "E" action JpInput.JpInput("E")
                    textbutton "R" action JpInput.JpInput("R")
                    textbutton "T" action JpInput.JpInput("T")
                    textbutton "Y" action JpInput.JpInput("Y")
                    textbutton "U" action JpInput.JpInput("U")
                    textbutton "I" action JpInput.JpInput("I")
                    textbutton "O" action JpInput.JpInput("O")
                    textbutton "P" action JpInput.JpInput("P")
                    textbutton "`" action JpInput.JpInput("`")
                    textbutton "{{" action JpInput.JpInput("{")
                hbox:
                    xpos 0.175
                    textbutton "A" action JpInput.JpInput("A")
                    textbutton "S" action JpInput.JpInput("S")
                    textbutton "D" action JpInput.JpInput("D")
                    textbutton "F" action JpInput.JpInput("F")
                    textbutton "G" action JpInput.JpInput("G")
                    textbutton "H" action JpInput.JpInput("H")
                    textbutton "J" action JpInput.JpInput("J")
                    textbutton "K" action JpInput.JpInput("K")
                    textbutton "L" action JpInput.JpInput("L")
                    textbutton "+" action JpInput.JpInput("+")
                    textbutton "*" action JpInput.JpInput("*")
                    textbutton "}" action JpInput.JpInput("}")
                    textbutton "RETURN" action JpInput.JpInput('RETURN')
                hbox:
                    textbutton "  Shift  " action ToggleLocalVariable("shift_on", True, False)
                    textbutton "Z"  action JpInput.JpInput('Z')
                    textbutton "X"  action JpInput.JpInput('X')
                    textbutton "C"  action JpInput.JpInput('C')
                    textbutton "V"  action JpInput.JpInput('V')
                    textbutton "B"  action JpInput.JpInput('B')
                    textbutton "N"  action JpInput.JpInput('N')
                    textbutton "M"  action JpInput.JpInput('M')
                    textbutton "<"  action JpInput.JpInput('<')
                    textbutton ">"  action JpInput.JpInput('>')
                    textbutton "?"  action JpInput.JpInput('?')
                    textbutton "_"  action JpInput.JpInput('_')
                    textbutton "  Shift " action ToggleLocalVariable("shift_on", True, False)
                hbox:
                    xalign 0.5
                    textbutton "SPACE " action JpInput.JpInput('SPACE')
                    textbutton " 変換" action JpInput.JpInput('HENKAN')
        else:
            vbox:
                at _touch_keyboard
                spacing 20
                hbox:
                    textbutton "半/全" action ToggleVariable("JpInput.ime_mode", "hira", None)
                    textbutton "1" action JpInput.JpInput('1')
                    textbutton "2"  action JpInput.JpInput('2')
                    textbutton "3"  action JpInput.JpInput('3')
                    textbutton "4"  action JpInput.JpInput('4')
                    textbutton "5"  action JpInput.JpInput('5')
                    textbutton "6"  action JpInput.JpInput('6')
                    textbutton "7"  action JpInput.JpInput('7')
                    textbutton "8"  action JpInput.JpInput('8')
                    textbutton "9"  action JpInput.JpInput('9')
                    textbutton "0"  action JpInput.JpInput('0')
                    textbutton "-"  action JpInput.JpInput('-')
                    textbutton "^"  action JpInput.JpInput('^')
                    textbutton "\\" action JpInput.JpInput('\\')
                    textbutton " BS " action JpInput.JpInput('BACKSPACE')
                    textbutton " Del " action JpInput.JpInput('DELETE')
                hbox:
                    xpos 0.15
                    textbutton "q" action JpInput.JpInput('q')
                    textbutton "w" action JpInput.JpInput('w')
                    textbutton "e" action JpInput.JpInput('e')
                    textbutton "r" action JpInput.JpInput('r')
                    textbutton "t" action JpInput.JpInput('t')
                    textbutton "y" action JpInput.JpInput('y')
                    textbutton "u" action JpInput.JpInput('u')
                    textbutton "i" action JpInput.JpInput('i')
                    textbutton "o" action JpInput.JpInput('o')
                    textbutton "p" action JpInput.JpInput('p')
                    textbutton "@" action JpInput.JpInput('@')
                    textbutton "[[" action JpInput.JpInput('[')
                hbox:
                    xpos 0.175
                    textbutton "a" action JpInput.JpInput('a')
                    textbutton "s" action JpInput.JpInput('s')
                    textbutton "d" action JpInput.JpInput('d')
                    textbutton "f" action JpInput.JpInput('f')
                    textbutton "g" action JpInput.JpInput('g')
                    textbutton "h" action JpInput.JpInput('h')
                    textbutton "j" action JpInput.JpInput('j')
                    textbutton "k" action JpInput.JpInput('k')
                    textbutton "l" action JpInput.JpInput('l')
                    textbutton ";" action JpInput.JpInput(';')
                    textbutton ":" action JpInput.JpInput(':')
                    textbutton "]" action JpInput.JpInput(']')
                    textbutton "RETURN" action JpInput.JpInput('RETURN')
                hbox:
                    textbutton "  Shift " action ToggleLocalVariable("shift_on", True, False)
                    textbutton "z"  action JpInput.JpInput('z')
                    textbutton "x"  action JpInput.JpInput('x')
                    textbutton "c"  action JpInput.JpInput('c')
                    textbutton "v"  action JpInput.JpInput('v')
                    textbutton "b"  action JpInput.JpInput('b')
                    textbutton "n"  action JpInput.JpInput('n')
                    textbutton "m"  action JpInput.JpInput('m')
                    textbutton ","  action JpInput.JpInput(',')
                    textbutton "."  action JpInput.JpInput('.')
                    textbutton "/"  action JpInput.JpInput('/')
                    textbutton "\\" action JpInput.JpInput('\\')
                    textbutton " ← " action JpInput.JpInput('LEFT')
                    textbutton " → " action JpInput.JpInput('RIGHT')
                hbox:
                    xalign 0.5
                    textbutton "SPACE " action JpInput.JpInput('SPACE')
                    textbutton " 変換" action JpInput.JpInput('HENKAN')
