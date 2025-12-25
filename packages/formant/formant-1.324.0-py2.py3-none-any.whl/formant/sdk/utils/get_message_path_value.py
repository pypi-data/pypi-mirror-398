import re
from typing import Union, Dict, List

messagePathRegex = re.compile(
    r"^([a-zA-Z])([0-9a-zA-Z_])*(\[[0-9]+\])?(\.([a-zA-Z])([0-9a-zA-Z_])*(\[[0-9]+\])?)*"
)


def get_message_path_value(
    message,  # type: Union[Dict, object, List]
    messagePath,  # type: str
    raise_error=False,  # type: bool
):
    """
    Returns the message value at the end of the provided message path
    """
    if not messagePathRegex.fullmatch(messagePath):
        raise ValueError("Invalid message path in configuration: " + messagePath)

    # parse the message path
    steps = []
    for substring in messagePath.split("."):
        indexStart = None
        try:
            indexStart = substring.index("[")
        except ValueError:
            pass

        if indexStart:
            if indexStart == 0:
                steps.append(("indexing", substring))
            else:
                steps.append(("attribute", substring[:indexStart]))
                steps.append(("indexing", substring[indexStart:]))
        else:
            steps.append(("attribute", substring))

    # index based on the message path
    try:
        for step in steps:
            if step[0] == "attribute":
                if isinstance(message, dict):
                    message = message[step[1]]
                else:
                    message = getattr(message, step[1])
            elif step[0] == "indexing":
                indices = [int(s[1:]) for s in step[1].split("]")[:-1]]
                for index in indices:
                    if isinstance(message, List):
                        message = message[index]
                    else:
                        raise TypeError(
                            "%s object is not subscriptable" % type(message).__name__
                        )
    except (AttributeError, KeyError, TypeError) as e:
        if raise_error:
            raise e
        return None

    return message
