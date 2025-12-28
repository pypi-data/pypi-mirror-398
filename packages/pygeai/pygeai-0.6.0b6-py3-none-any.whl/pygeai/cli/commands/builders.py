

def build_help_text(available_commands: list, help_text_template: str):
    """
    Build help text using available commands.
    """
    available_commands_text = ""
    for command in available_commands:
        command_identifiers = ' or '.join(command.identifiers)
        command_help = f"{command_identifiers}\t\t{command.description}" if len(command_identifiers) > 10 else f"{command_identifiers}\t\t\t{command.description}"
        if command.options:
            command_options_text = ""
            for option in command.options:
                option_identifiers = ' or '.join(option.identifiers)
                command_options = f"{option_identifiers}\t\t{option.description}" if len(option_identifiers) > 10 else f"{option_identifiers}\t\t\t{option.description}"
                command_options_text += f"\t{command_options}\n    "

            available_commands_text += f"\n    {command_help}\n      {command_options_text}"
        else:
            available_commands_text += f"{command_help}\n    "

    help_text = help_text_template.format(available_commands=available_commands_text)

    return help_text
