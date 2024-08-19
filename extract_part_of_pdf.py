"""
Read PDF files and extract segments of PDF files

Usage:
  pdf_extract_part_of_pdf.py <folder_in> <folder_out>

  <folder_in>: file folder where data is extracted
  <folder_out>: file folder where data is extracted

Examples:
  pdf_extract_part_of_pdf.py line_2024.tsv LINE_2024

"""
from docopt import docopt
import fitz
import os
import pandas as pd
import re

def push_line_title():
    global parse_current_section_sequence
    global df
    global parse_current_type
    global parse_current_address
    global parse_current_address2
    global parse_current_area_square
    global parse_current_reason
    global parse_current_date
    global parse_current_date_receipt
    global parse_current_target_object
    global parse_current_target_direction
    global parse_current_position
    global parse_current_transaction
    global parse_current_right_hold_type
    global parse_current_cancel

    # parse reasons
    if parse_current_section == TYPE_OF_SECTION_TITLE:
        parse_reasons_title(parse_current_reason)
    elif parse_current_section == TYPE_OF_SECTION_RIGHT:
        parse_reasons_rights(parse_current_reason)
    else:
        print(f"not parsed - {parse_current_section,parse_current_section_sequence}")

    tmp_se = pd.Series({
        "id": parse_current_section_sequence,
        "type_of_section": parse_current_section,
        'type': parse_current_type,
        "type_of_transaction": parse_current_transaction,
        "type_of_ownership": parse_current_right_hold_type,
        "address": parse_current_address,
        "address2": parse_current_address2,
        "area_square": parse_current_area_square,
        "reason": parse_current_reason,
        "date": parse_current_date,
        'date_of_receipt': parse_current_date_receipt,
        "target_object" : parse_current_target_object,
        "target_direction":  parse_current_target_direction,
        "position": parse_current_position,
        "deleted": parse_current_cancel,
    }, index=columns)

    if parse_current_reason != LANGUAGE_RIGHT_TRANSFER_AT_THE_DATE:
        df = pd.concat([df, tmp_se.to_frame().T], ignore_index=True)
        parse_current_section_sequence = parse_current_section_sequence + 1
    parse_current_address2 = ""
    parse_current_type = ""
    parse_current_area_square = ""
    parse_current_reason = ""
    parse_current_date = ""
    parse_current_date_receipt = ""
    parse_current_target_object = ""
    parse_current_target_direction = ""
    parse_current_right_hold_type = ""
    parse_current_transaction = ""
    parse_current_position = 0
    parse_current_cancel = False

def parse_reasons_rights(in_text):
    global parse_current_target_object
    global parse_current_target_direction
    global parse_current_transaction
    global LANGUAGE_RIGHT_PURCHASE
    global LANGUAGE_RIGHT_BESTOW
    global LANGUAGE_RIGHT_INHERIT
    global LANGUAGE_RIGHT_OWNER
    global parse_current_right_hold_type
    global parse_owner
    global parse_current_stack_number
    global parse_current_reason
    global parse_current_date
    global parse_current_cancel

# detect opening
    if LANGUAGE_RIGHT_REASON in in_text[0:2]:

        if len([location for location in LANGUAGE_ERA_NAME if location in in_text]) > 0:

            components_blocks = re.findall(r'原因(..\d+年\d+月\d+日)', in_text)
            parse_current_date = "".join(components_blocks)
            in_text = in_text.replace(parse_current_date,"")
        in_text = in_text.replace(LANGUAGE_RIGHT_REASON, "")

    if LANGUAGE_RIGHT_BESTOW[0] in in_text[0:2]:
        parse_current_transaction = LANGUAGE_RIGHT_BESTOW[0]
        in_text = in_text[3:]
    elif LANGUAGE_RIGHT_PURCHASE[0] in in_text[0:2]:
        parse_current_transaction = LANGUAGE_RIGHT_PURCHASE[0]
        in_text = in_text[3:]
    elif LANGUAGE_RIGHT_INHERIT[0] in in_text[0:2]:
        parse_current_transaction = LANGUAGE_RIGHT_INHERIT[0]
        in_text = in_text[3:]
    elif LANGUAGE_RIGHT_MERGE in in_text:
        parse_current_transaction = LANGUAGE_RIGHT_MERGE
    elif LANGUAGE_RIGHT_DONATE in in_text:
        parse_current_transaction = LANGUAGE_RIGHT_DONATE

    if LANGUAGE_RIGHT_TRANSFER[0] in parse_current_type:
        parse_current_target_object = parse_current_type.replace(LANGUAGE_RIGHT_TRANSFER[0], "")
        parse_current_target_direction = "from"
    if LANGUAGE_RIGHT_TRANSFER[1] in parse_current_type:
        parse_current_target_object = parse_current_type.replace(LANGUAGE_RIGHT_TRANSFER[1], "")
        parse_current_target_direction = "from"

    # parse names
    if LANGUAGE_RIGHT_SHARED[0] == in_text[0:3] or LANGUAGE_RIGHT_OWNER[0] == in_text[0:3] or LANGUAGE_RIGHT_MERGE in in_text:
        if LANGUAGE_RIGHT_SHARED[0] == in_text[0:3]:
            parse_current_right_hold_type = LANGUAGE_RIGHT_SHARED[0]
            in_text = in_text.replace(LANGUAGE_RIGHT_SHARED[0], "")

            registration_order_number = re.findall(r'(順位\d+番の登記を移記)', in_text)
            if len(registration_order_number) > 0:
                in_text = in_text.replace(registration_order_number[0], "")

            address_lines = []
            address_item = {}
            split_address = in_text.split("\n")
            for address_in_text in split_address:
                find_share = re.findall(r'(\d+分の\d+)', address_in_text)
                find_address = re.findall(r'(.*?(都|道|府|県|市|区|町|村).*?)', address_in_text)
                if (len(find_address) != 0):
                    if 'address' not in address_item:
                        address_item['address'] = address_in_text
                    else:
                        address_item['address'] = address_item['address'] + address_in_text
                elif len(find_share) != 0:
                    if '持分' in address_in_text:
                        address_in_text_without_holding = address_in_text.replace("持分","")
                        address_item['share'] = address_in_text_without_holding
                    else:
                        address_item['share'] = address_in_text
                elif 'share' in address_item:
                    address_item['name'] = address_in_text
                    address_lines.append(address_item.copy())
                    address_item = {}
            in_text = ",".join(["::".join([a['address'],a['share'],a['name']]) for a in address_lines])
            if parse_current_cancel == True:
                count_cancel = in_text.count(CANCEL_BLOCK_STRING_CONSTANT)
                if count_cancel == in_text.count("::") - 1:
                    parse_current_cancel = False
            parse_current_reason = in_text


        elif LANGUAGE_RIGHT_OWNER[0] == in_text[0:3] or LANGUAGE_RIGHT_MERGE in in_text:

            parse_current_right_hold_type = LANGUAGE_RIGHT_OWNER[0]
            in_text = in_text.replace(LANGUAGE_RIGHT_OWNER[0], "")

            registration_order_number = re.findall(r'(順位\d+番の登記を移記)', in_text)
            if len(registration_order_number) > 0:
                in_text = in_text.replace(registration_order_number[0], "")
            if in_text[-1:] == "\n":
                in_text = in_text[:-1]
            split_address = in_text.split("\n")
            parse_current_reason = "".join(split_address[:-1])
            parse_current_reason = parse_current_reason + "///" + split_address[-1]

    else:
        # return_string = in_text
        return_type = "reason"
        if parse_current_reason == "":
            parse_current_reason = in_text
        else:
            parse_current_reason = in_text
    if parse_current_right_hold_type != "":
        parse_current_stack_number = parse_current_stack_number + 1

def parse_reasons_title(in_land_text):

    global parse_current_target_object
    global parse_current_target_direction
    global LANGUAGE_TITLE_MERGE_TITLE
    global LANGUAGE_TITLE_SPLIT
    global parse_current_reason
    global parse_current_date

    if len([location for location in LANGUAGE_ERA_NAME if location in in_land_text]) > 0:
        matches_components = re.findall(r'(?<=〔)[^〕]+(?=〕)', in_land_text)
        components_blocks = re.findall(r'.(..)(\d+)年(\d+)月(\d+)日〕', in_land_text)
        parse_current_date = "".join(matches_components)
        in_land_text = in_land_text.replace(parse_current_date,"")
        in_land_text = in_land_text.replace("〕","")
        in_land_text = in_land_text.replace("〔","")
    if in_land_text != "":
        verb_list = [a for row in [LANGUAGE_TITLE_SPLIT,
                                   LANGUAGE_TITLE_MERGE,
                                   LANGUAGE_RIGHT_INHERIT,
                                   LANGUAGE_TITLE_CHANGE,
                                   LANGUAGE_TITLE_MERGE_TITLE
                                   ] for a in row ]
        #から分筆
        if LANGUAGE_TITLE_SPLIT_NEW in in_land_text:
            parse_current_target_direction = "from"
            matches = re.findall(r'\d+番\d+', in_land_text)
            matches_components = re.findall(r'(\d+)番(\d+)', in_land_text)
            try:
                if len(matches_components[0]) ==0:
                    matches_components = re.findall(r'(\d+)番(\S)' + LANGUAGE_TITLE_SPLIT_NEW, in_land_text)
                # print( parse_current_address,  matches_components)
                parse_current_target_object = matches_components[0][0] + '番' + matches_components[0][1]
            except Exception as e:
                print(e)

        if HEADER_LAND_COLUMN_2 in in_land_text[0:2] or HEADER_LAND_COLUMN_3 in in_land_text[0:2] :
            #change reasons
            target_group_2 = False
            target_group_3 = False
            if HEADER_LAND_COLUMN_2 in in_land_text[0:2]:
                target_group_2 = True
                in_land_text = in_land_text.replace(HEADER_LAND_COLUMN_2, "")
            if HEADER_LAND_COLUMN_3 in in_land_text[0:2]:
                target_group_3 = True
                in_land_text = in_land_text.replace(HEADER_LAND_COLUMN_3, "")

            if len([a for a in verb_list if a in in_land_text]) == 0:
                # print(f"to check verbs: {in_land_text}")
                parse_current_reason = parse_current_reason + in_land_text
                return_string = in_land_text
                return_type = "reason"
                return return_type, return_string

            # First split by the Japanese comma
            parts = re.findall(r'[^、]+', in_land_text)
            # Further split each part by numeric transitions
            final_parts = []
            for part in parts:
                final_parts.extend(re.findall(r'\d+|[^0-9、]+', part))

            registration_order_number = re.findall(r'(順位\d+番の登記を移記)', in_land_text)
            if len(registration_order_number) > 0:
                in_land_text = in_land_text.replace(registration_order_number[0], "")


            for item in [a for row in [LANGUAGE_TITLE_SPLIT,
                                       LANGUAGE_TITLE_MERGE_TITLE,
                                       LANGUAGE_TITLE_MERGE] for a in row]:
                if item in in_land_text:
                    if item in LANGUAGE_TITLE_SPLIT:
                        parse_current_target_direction = "to"
                    elif item in LANGUAGE_TITLE_MERGE_TITLE:
                        parse_current_target_direction = "from"
                    elif item in LANGUAGE_TITLE_MERGE:
                        parse_current_target_direction = "from"
                    else:
                        parse_current_target_direction = "NA"
                    in_land_text = in_land_text.replace(item, "")
                    in_land_text = in_land_text.replace(parse_current_address,"")
                    in_land_text = in_land_text.replace("\n", "")
                    replacing_leading_address = re.findall(r'(\d+)番\d+', parse_current_address)[0] + "番"
                    if '同番' in in_land_text:
                        matches_components = re.findall(r'(\d+)番\d+', parse_current_address)
                        in_land_text = in_land_text.replace('同番',replacing_leading_address)
                    # missing leading address

                    components_without_leading_section_separator = re.findall(r'(\d+番\d+)', in_land_text)
                    temp_land_text = in_land_text
                    if len(components_without_leading_section_separator) > 0:
                        for replace_item in components_without_leading_section_separator:
                            temp_land_text = temp_land_text.replace(replace_item,"")
                    matches = re.findall(r'\d+', temp_land_text)
                    for replace_item in matches:
                        in_land_text = in_land_text.replace(replace_item,replacing_leading_address  + replace_item)
                    matches = re.findall(r'\d+番\d+', in_land_text)
                    matches_components = re.findall(r'(\d+)番(\d+)', in_land_text)
                    parse_current_target_object = ",".join(matches)

            for item in LANGUAGE_RIGHT_INHERIT:
                if item in in_land_text:
                    matches = re.findall(r'\d+番\d+', in_land_text)
            for item in LANGUAGE_TITLE_CHANGE:
                if item in in_land_text:
                    matches = re.findall(r'\d+番\d+', in_land_text)

def visitor_body(text, cm, tm, fontDict, fontSize,cancel_block):
    parts = []
    SEPARATOR_COLUMN = "│"
    SEPARATOR_COLUMN_BOLD = "┃"
    SEPARATOR_SECTION_START = '┏' #"━"
    SEPARATOR_SECTION_END = '┗'
    SEPARATOR_SECTION_LINE = "━"
    SEPARATOR_LINE = "─"
    SEPARATER_LINE_TERMINATOR = "┨"
    global parse_current_section
    global parse_current_section_sequence
    global parse_current_address
    global parse_current_address2
    global parse_current_type
    global parse_current_area_square
    global parse_current_reason
    global df
    global header_land_type_just_found
    global parse_current_date
    global parse_current_date_receipt
    global parse_current_target_object
    global parse_current_position
    global parse_current_cancel
    global parse_current_right_hold_type
    global CANCEL_BLOCK_STRING_CONSTANT
    global COLUMNS_HEADER_RIGHT_SECTION_OTSU
    global COLUMNS_HEADER_RIGHT_SECTION_KOU
    global parse_current_section_kou_otsu
    if text == "":
        return
    if len(text.replace(" ", "") ) == 0:
        return
    if cancel_block == True:
        parse_current_cancel = True

    if parse_current_section == None:
        if SEPARATOR_SECTION_START in text:
            parse_current_section = TYPE_OF_SECTION_NEUTRAL
    elif parse_current_section == TYPE_OF_SECTION_NEUTRAL:
        if SEPARATOR_LINE in text:
            if parse_current_reason != "":
                push_line_title()
        elif SEPARATOR_SECTION_END in text:
            push_line_title()
            parse_current_section = None
        elif COLUMNS_HEADER_RIGHT_SECTION_KOU in text:
            parse_current_section_kou_otsu = TYPE_OF_SECTION_RIGHT
        elif COLUMNS_HEADER_RIGHT_SECTION_OTSU in text:
            parse_current_section_kou_otsu = TYPE_OF_SECTION_RIGHT_OTSU
        elif SEPARATOR_COLUMN in text:
            # find header
            condensed_text = text.replace(" ","")
            condensed_text = condensed_text.replace("　","")
            condensed_text = condensed_text.replace("　","")
            if HEADER_LAND_TYPE in condensed_text and HEADER_LAND_ADDRESS_COLUMN in condensed_text:
                header_land_type_just_found = True
                parse_current_section = TYPE_OF_SECTION_TITLE
            elif COLUMNS_HEADER_RIGHT_PRIO in condensed_text and COLUMNS_HEADER_RIGHT_REASON in condensed_text:
                header_land_type_just_found = True
                if parse_current_section_kou_otsu == TYPE_OF_SECTION_RIGHT_OTSU:
                    parse_current_section = TYPE_OF_SECTION_RIGHT_OTSU
                else:
                    parse_current_section = TYPE_OF_SECTION_RIGHT
            # elif SEPARATOR_LINE in condensed_text:
            #     # print("line found")
            # elif structure_block_title in condensed_text:
            #     print("表題部")
            # elif header_land_type in condensed_text:
            #     print("header")
            # elif ( header_land_id_number in condensed_text ) or ( header_land_registered_area in condensed_text):
            #     print("地図番号")
            # elif header_land_address in condensed_text:
            #     print("所在")

    elif parse_current_section == TYPE_OF_SECTION_TITLE:
        if SEPARATOR_LINE in text:
            if parse_current_reason != "":
                push_line_title()
        elif SEPARATOR_SECTION_END in text:
            push_line_title()
            parse_current_section = None
        else:
            if header_land_type_just_found == True and SEPARATER_LINE_TERMINATOR in text:
                # skip one separator at the ver first one
                print("header end",end="")
                header_land_type_just_found = False
            else:
                condensed_text = text.replace(" ", "")
                condensed_text = condensed_text.replace("　", "")
                condensed_text = condensed_text.replace("　", "")

                if SEPARATOR_SECTION_LINE in condensed_text or SEPARATOR_LINE in condensed_text:
                    if parse_current_address != "":
                        print("section do not write",end="")
                        if (parse_current_reason == "") and (parse_current_date == ""):
                            print("blank linke")
                else:
                    Z_DIGIT = '１２３４５６７８９０'
                    H_DIGIT = '1234567890'
                    if parse_current_position == 0:
                        parse_current_position = tm[4]
                    z2h_digit = str.maketrans(Z_DIGIT, H_DIGIT)
                    symbol_previous = '\ue239'
                    symbol_decimal_point = '：'
                    try:
                        if len(condensed_text.split(SEPARATOR_COLUMN)) == 4:
                            (land_address,land_type,land_area_square,land_reasons) = condensed_text.split(SEPARATOR_COLUMN)
                        else:
                            unpacked_ = condensed_text.split(SEPARATOR_COLUMN)
                            if LANGUAGE_RIGHT_OWNER[0] in unpacked_[0]:
                                land_reasons = "現住所" +"///" + unpacked_[1]
                                parse_current_right_hold_type = LANGUAGE_RIGHT_OWNER[0]
                                land_address = ""
                                land_area_square = ""
                                land_type = ""
                    except Exception as e:
                        print(e)
                    land_address = land_address.replace(SEPARATOR_COLUMN,"") #remove leading |
                    land_address = land_address.replace(SEPARATOR_COLUMN_BOLD,"") #remove leading |
                    land_area_square = land_area_square.replace(symbol_previous,"") #remove leading |
                    land_area_square = land_area_square.replace(symbol_decimal_point,".")
                    land_area_square = land_area_square.translate(z2h_digit)
                    string_same_as_above = "\ue042\ue043\ue044"
                    if land_area_square == string_same_as_above + ".":
                        land_area_square = "同上"
                    elif len(land_area_square) == 1:
                        land_area_square = ""
                    elif land_area_square != "":
                        land_area_square = str(float(land_area_square))

                    land_reasons = land_reasons.replace(SEPARATOR_COLUMN_BOLD,"")
                    land_reasons = str(land_reasons).replace('┃\n',"")

                    if land_type != "" and land_type != string_same_as_above:
                        parse_current_type = land_type
                    if land_address != ""  and land_address != "┃" + string_same_as_above:
                        if parse_current_address == "":
                            parse_current_address = land_address
                        else:
                            parse_current_address2 = land_address
                    if land_area_square != ""  and land_area_square != string_same_as_above:
                        if land_area_square == "\n":
                            print("",end="")
                        elif land_area_square == ".":
                            print("",end="")
                        else:
                            parse_current_area_square = land_area_square

                    if parse_current_reason == "":
                        parse_current_reason = land_reasons
                    else:
                        parse_current_reason = parse_current_reason + "\n" + land_reasons


    elif parse_current_section == TYPE_OF_SECTION_RIGHT:
        if SEPARATOR_LINE in text:
            if parse_current_reason != "":
                push_line_title()
        elif SEPARATOR_SECTION_END in text:
            push_line_title()
            parse_current_section = None
        else:
            if header_land_type_just_found == True and SEPARATER_LINE_TERMINATOR in text:
                # skip one separator at the ver first one
                print("header end",end="")
                header_land_type_just_found = False
            else:
                condensed_text = text.replace(" ", "")
                condensed_text = condensed_text.replace("　", "")
                condensed_text = condensed_text.replace("　", "")

                if not ( SEPARATOR_SECTION_LINE in condensed_text or SEPARATOR_LINE in condensed_text):
                #     print()
                # else:
                    Z_DIGIT = '１２３４５６７８９０'
                    H_DIGIT = '1234567890'
                    if parse_current_position == 0:
                        parse_current_position = tm[4]
                    z2h_digit = str.maketrans(Z_DIGIT, H_DIGIT)
                    # symbol_previous = '\ue239'
                    # symbol_decimal_point = '：'
                    if len(condensed_text.split(SEPARATOR_COLUMN)) != 4:
                        print(f"no split:{condensed_text}")
                        return
                    (land_address,land_type,land_area_square,land_reasons) = condensed_text.split(SEPARATOR_COLUMN)
                    land_address = land_address.replace(SEPARATOR_COLUMN,"") #remove leading |
                    land_address = land_address.replace(SEPARATOR_COLUMN_BOLD,"") #remove leading |
                    land_reasons = land_reasons.replace(SEPARATOR_COLUMN_BOLD,"")
                    land_reasons = str(land_reasons).replace('┃\n',"")
                    string_same_as_above = "\ue042\ue043\ue044"
                    if land_type != "" and land_type != string_same_as_above:
                        parse_current_type = land_type
                    if land_address != ""  and land_address != "┃" + string_same_as_above:
                        if parse_current_address == "":
                            parse_current_address = land_address
                    if land_area_square != ""  and land_area_square != string_same_as_above:
                        if land_area_square == "\n":
                            print("",end="")
                        elif land_area_square == ".":
                            print("",end="")
                        elif parse_current_date_receipt == "":
                            parse_current_date_receipt = land_area_square

                    cancel_block_string= ""
                    if cancel_block == True:
                        cancel_block_string = CANCEL_BLOCK_STRING_CONSTANT
                    if parse_current_reason == "":
                        parse_current_reason = land_reasons + cancel_block_string
                    else:
                        parse_current_reason = parse_current_reason + "\n" + land_reasons + cancel_block_string

    text_all_content.append(text)
    text = ""
    condensed_text = ""
    return


if __name__ == '__main__':

    arguments = docopt(__doc__, version="0.1")
    folder_in = arguments["<folder_in>"]
    folder_out = arguments["<folder_out>"]

    files = os.listdir(folder_in)
    pdf_files = [f for f in files if f.upper().endswith(".PDF")]

    STRUCTURE_BLOCK_TITLE = '表題部'
    STRUCTURE_BLOCK_OWNER = '権利部'
    HEADER_LAND_COLUMN_2 = '②'
    HEADER_LAND_COLUMN_3 = '③'
    HEADER_LAND_ADDRESS_COLUMN = '①地番'
    HEADER_LAND_TYPE = '②地目'
    HEADER_LAND_AREA_SQUARE = '③地籍'
    HEADER_LAND_REASONS = '原因およびその日付'
    HEADER_LAND_ID_NUMBER = '地図番号'
    HEADER_LAND_REGISTERED_AREA = '筆界特定'
    HEADER_LAND_ADDRESS = '所在'

    COLUMNS_HEADER_RIGHT_PRIO = "順位番号"
    COLUMNS_HEADER_RIGHT_REASON = "登記の目的"
    COLUMNS_HEADER_RIGHT_DATE = "受付年月日・受付番号"
    COLUMNS_HEADER_RIGHT_HOLDER = "権利者その他の事項"
    COLUMNS_HEADER_RIGHT_SECTION_KOU = "甲区"
    COLUMNS_HEADER_RIGHT_SECTION_OTSU = "乙区"

    TYPE_OF_SECTION_NEUTRAL = "N"
    TYPE_OF_SECTION_TITLE = "title"
    TYPE_OF_SECTION_RIGHT = "right_kou"
    TYPE_OF_SECTION_RIGHT_OTSU = "right_otsu"

    LANGUAGE_TITLE_SPLIT_NEW = 'から分筆'
    LANGUAGE_TITLE_SPLIT = ['に分筆', '分筆']
    LANGUAGE_TITLE_MERGE = ['の一部を合併', '一部合併']
    LANGUAGE_TITLE_MERGE_TITLE = ['を合筆', '合筆']
    LANGUAGE_TITLE_CHANGE = ['地目変更']

    LANGUAGE_RIGHT_INHERIT = ['相続']
    LANGUAGE_RIGHT_BESTOW = ['贈与']
    LANGUAGE_RIGHT_PURCHASE= ['売買']

    LANGUAGE_RIGHT_REASON = '原因'
    LANGUAGE_RIGHT_MERGE = '合併'
    LANGUAGE_RIGHT_DONATE = '寄付'
    LANGUAGE_RIGHT_SPLIT = ['分の']
    LANGUAGE_RIGHT_SHARED = ['共有者']
    LANGUAGE_RIGHT_OWNER = ['所有者']
    LANGUAGE_RIGHT_TRANSFER = ['持分一部移転', '持分全部移転']
    LANGUAGE_RIGHT_TRANSFER_WRITTEN = '順位３番の登記を移記'
    LANGUAGE_RIGHT_TRANSFER_AT_THE_DATE = '平成１７年法務省令第１８号附則第３条第２項\nの規定により移記\n平成１８年１２月６日'
# right
# 住所移転
# title
# 錯誤

    LANGUAGE_ERA_NAME = ['昭和', '平成', '令和']
    CANCEL_BLOCK_STRING_CONSTANT = "<CANCEL_BLOCK>"

    parse_current_section = None
    parse_current_section_sequence = 0
    parse_current_address = ""
    parse_current_address2 = ""
    parse_current_type = ""
    parse_current_area_square = ""
    parse_current_reason = ""
    parse_current_date = ""
    parse_current_date_receipt = ""
    parse_current_target_object = ""
    parse_current_target_direction = ""
    parse_current_position = 0
    parse_current_transaction = ""
    parse_current_stack_number = 0
    parse_current_right_hold_type = ""
    parse_current_cancel = False
    parse_current_section_kou_otsu = ""

    header_land_type_just_found = False

    columns = ['id', 'parent_id', 'address','address2', 'type_of_section', 'type', 'type_of_transaction','type_of_ownership','date','date_of_receipt' ,'reason', 'area_square', 'share', 'name','target_object','target_direction','position','deleted']
    df = pd.DataFrame(columns=columns)

    text_all_content = []

    for pdf_file in pdf_files:
        df_single_lines = pd.DataFrame(columns)

        pdf_reader = fitz.open(os.path.join(folder_in,pdf_file))
        parse_current_address = ""
        parse_current_section = None

        for page in pdf_reader:
            block_number = [a['number'] for a in page.get_text("dict", sort=True)['blocks'] if 'ext' not in a][0]
            concatenated_blocks = [[a['spans'][0]['text'],[0,0,0,0,a['spans'][0]['bbox'][3]] ] for a in page.get_text("dict", sort=True)['blocks'][block_number]['lines']]
            cancel_blocks = [b['rect'] for b in page.get_drawings("rect")]

            for text,coord in concatenated_blocks:
                cancel_block = False
                cancel_blocks_within_1_pixel = [ a[3] for a in cancel_blocks if ( a[3] + 1) > coord[4] > ( a[3] - 1) ]
                if len(cancel_blocks_within_1_pixel) != 0:
                    cancel_block = True
                visitor_body(text,0,coord,0,0, cancel_block)
    all_text = "\n".join(text_all_content)
    print(all_text)
    if os.path.exists(folder_out) is False:
        os.mkdir(folder_out)
    with open(os.path.join(folder_out,'output_parsed_pdf_text.txt'), "w",encoding="utf-8") as f:
        f.writelines(all_text)
    df.to_csv(os.path.join(folder_out,'output_parsed_list.csv'),index=False,sep="\t")
    df['split_reason'] = df['reason'].str.split(',')
    df = df.explode('split_reason')
    df2 = df.copy()
    df3 = df.copy()
    if df['split_reason'].str.contains('::').sum() != 0:
        df2[['address2','share','name']] = df['split_reason'].str.split("::", expand=True)
        mask_deleted = df2['address2'].str.contains(CANCEL_BLOCK_STRING_CONSTANT)
        df2.loc[mask_deleted, 'deleted'] = "True_Partial"
        df2['address2'] = df2['address2'].str.replace(CANCEL_BLOCK_STRING_CONSTANT, "")
        df[df['type_of_ownership'] == '共有者'] = df2[df['type_of_ownership'] == '共有者']
    if df['split_reason'].str.contains("///").sum() != 0:
        df3[['address2','name']] = df['split_reason'].str.split("///", expand=True)

        mask_deleted = df3['address2'].str.contains(CANCEL_BLOCK_STRING_CONSTANT)
        df3.loc[mask_deleted, 'deleted'] = "True_Partial"
        df3['address2'] = df3['address2'].str.replace(CANCEL_BLOCK_STRING_CONSTANT, "")

        df[df['type_of_ownership'] == '所有者'] = df3[df['type_of_ownership'] == '所有者']
    df.to_csv(os.path.join(folder_out,'output_parsed_list_split.csv'),index=False,sep="\t")