from .logs import logger, logstr
from .decorations import brk


def confirm_input(
    expect_val: str,
    op_name: str = "",
    ignore_case: bool = False,
    max_retries: int = None,
    raise_error: bool = True,
    comp_func: callable = None,
    exec_func: callable = None,
    *exec_args,
    **exec_kwargs,
) -> bool:
    comp_res = False
    if not op_name:
        op_name = exec_func.__name__ if exec_func else "operation"
    attempts = 0
    hint_prefix = ""
    while not comp_res:
        if isinstance(max_retries, int):
            hint_prefix = f"[{logstr.file(attempts + 1)}/{logstr.mesg(max_retries)}] "
            if attempts >= max_retries:
                logger.warn(f"× Exceed max_retries ({max_retries}). Stop confirm.")
                break
        input_val = input(
            logstr.note(
                f'> {hint_prefix}Type "{logstr.file(expect_val)}" to confirm {logstr.mesg(brk(op_name))}: '
            )
        )
        if comp_func:
            comp_res = comp_func(input_val, expect_val)
        else:
            if ignore_case:
                comp_res = input_val.lower() == expect_val.lower()
            else:
                comp_res = input_val == expect_val
        attempts += 1

    if comp_res:
        if exec_func:
            exec_func(*exec_args, **exec_kwargs)
        return True
    else:
        if raise_error:
            raise ValueError(f"Confirmation failed")
        return False
