def apply_click_params(command, *click_params):
    for click_param in click_params:
        command = click_param(command)
    return command
