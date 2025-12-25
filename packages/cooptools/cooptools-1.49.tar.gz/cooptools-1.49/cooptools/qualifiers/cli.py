from cooptools.cli.CliAtomicUserInteraction import CliAtomicUserInteraction as cli
from cooptools.qualifiers import qualifier as qual

def request_white_black_list_qualifier():
    white_lst = cli.request_use_list(
        use_prompt=f"Specify Whitelist? ",
        request_prompt="whitelist item: "
    )

    black_lst = cli.request_use_list(
        use_prompt=f"Specify Blacklist? ",
        request_prompt="blacklist item: "
    )

    return qual.WhiteBlackListQualifier(
        white_list=white_lst,
        black_list=black_lst
    )


def request_pattern_qualifier() -> qual.PatternMatchQualifier:
    id = cli.request_string("Id: ", default='NA')
    if id == 'NA': id = None

    all_regex = cli.request_use_list(
        use_prompt=f"Specify All Regex? ",
        request_prompt="All Regex: "
    )

    any_regex = cli.request_use_list(
        use_prompt=f"Specify Any Regex? ",
        request_prompt="Any Regex: "
    )

    return qual.PatternMatchQualifier(
        id=id,
        regex_all=all_regex,
        regex_any=any_regex,
        white_list_black_list_qualifier=request_white_black_list_qualifier()
    )