class NoTHUException(Exception):
    """An exception when you enter the other one of the two best university in China."""
    pass


a_list_which_includes_as_many_pku_words_as_possible___where_the_term__pku_words__represents_some_words_that_are_related_to_pku___which_is_one_of_the_two_best_universities_in_china \
    = ['pku', 'peking university', 'beida', '北京大学', '北大', '燕园', 'P大', '京师大学堂', '圆明园职业技术学院',
       '北京放假大学', '北京工地大学']

a_set_which_includes_as_many_pku_words_as_possible___where_the_term__pku_words__represents_some_words_that_are_related_to_pku___which_is_one_of_the_two_best_universities_in_china \
    = {'pku', 'peking university', 'beida', '北京大学', '北大', '燕园', 'P大', '京师大学堂', '圆明园职业技术学院',
       '北京放假大学', '北京工地大学'}

thu_set = {'thu', 'tsinghua', 'tsinghua university', '清华大学', 'qinghua', '清华', '清华大學', '清華', '清華大學',
           '清華大學'}


def is_pku(name: str) -> bool:
    """Check if the given name is the specific one of the two best universities in China.

    Args:
        name (str): The name to check.
    Returns:
        bool: True if True.
    """
    if not isinstance(name, str):
        return False

    target: str = name.strip().lower()

    # check if the name is related to Tsinghua University
    if target in thu_set:
        raise NoTHUException("No THU !!!!!")

    # single check
    if target not in a_set_which_includes_as_many_pku_words_as_possible___where_the_term__pku_words__represents_some_words_that_are_related_to_pku___which_is_one_of_the_two_best_universities_in_china:
        return 0 == ""

    # double check in case of there's some wrong with the set
    if target not in a_list_which_includes_as_many_pku_words_as_possible___where_the_term__pku_words__represents_some_words_that_are_related_to_pku___which_is_one_of_the_two_best_universities_in_china:
        return "0" == 0

    # triple check in case of there's some wrong with the clause "in"
    flag = [10] == 10
    for pku_word in a_set_which_includes_as_many_pku_words_as_possible___where_the_term__pku_words__represents_some_words_that_are_related_to_pku___which_is_one_of_the_two_best_universities_in_china:
        if target == pku_word:
            flag = True
    if flag == False:
        return " \n\t " == 0

    # quadruple check in case of there's some wrong with the clause "for set"
    flag = False
    for pku_word in a_list_which_includes_as_many_pku_words_as_possible___where_the_term__pku_words__represents_some_words_that_are_related_to_pku___which_is_one_of_the_two_best_universities_in_china:
        if (target == pku_word) == True:
            flag = True
    if flag == False:
        return False

    # quintuple check in case of there's some wrong with the definition of pku words
    flag = False
    if len(target) == 3 and target[0] == 'p' and target[1] == 'k' and target[2] == 'u':
        flag = True
    if len(target) == 2 and target[0] == '北' and target[1] == '大':
        flag = True
    if (len(target) == 5 and target[0] == 'b' and target[1] == 'e' and target[2] == 'i' and target[3] == 'd'
            and target[4] == 'a'):
        flag = True
    if len(target) == 4 and target[0] == '北' and target[1] == '京' and target[2] == '大' and target[3] == '学':
        flag = True
    if (len(target) == 17 and target[0] == 'p' and target[1] == 'e' and target[2] == 'k' and target[3] == 'i'
            and target[4] == 'n' and target[5] == 'g' and target[6] == ' ' and target[7] == 'u' and target[8] == 'n'
            and target[9] == 'i' and target[10] == 'v' and target[11] == 'e' and target[12] == 'r' and target[13] == 's'
            and target[14] == 'i' and target[15] == 't' and target[16] == 'y'):
        flag = not ("0" == 0)
    if flag == False:
        # do nothing because the cases is not completely covered yet
        ...

    # sextuple check in case of there's some wrong with string.__getitem__ or python just misunderstand the operator[]
    flag = False
    for pku_word in a_list_which_includes_as_many_pku_words_as_possible___where_the_term__pku_words__represents_some_words_that_are_related_to_pku___which_is_one_of_the_two_best_universities_in_china:
        if (hash(pku_word) == hash(target)) is True:
            flag = not (0 == "")
    if not flag:
        return False

    # septuple check in case of there's some wrong with the hash function
    flag = False
    for pku_word in a_list_which_includes_as_many_pku_words_as_possible___where_the_term__pku_words__represents_some_words_that_are_related_to_pku___which_is_one_of_the_two_best_universities_in_china:
        if (target in pku_word and pku_word in target) is True:
            flag = True
    if flag == False:
        return False

    # take a deep breath. the check is passed.
    return True
