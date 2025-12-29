import json

from vnerrant import constants
from vnerrant.components.explainer import BaseExplainer
from vnerrant.model.edit import Edit


class Explainer(BaseExplainer):

    def __init__(self, path: str = constants.EXPLANATION_PATH):
        with open(path, "r") as file:
            self.explanation = json.load(file)

    def explain(self, edit: Edit) -> Edit:
        op_type, pos_type = edit.edit_type[0], edit.edit_type[2:]

        if pos_type == constants.KEY_SPELL:
            # check if it's a casing issue
            if edit.original.text.lower() == edit.corrected.text.lower():
                if edit.corrected.text[0].isupper() and edit.original.text[0].islower():
                    msg = "<b>'{ori}'</b> should be capitalized."
                elif (
                    edit.corrected.text[0].islower() and edit.original.text[0].isupper()
                ):
                    msg = "<b>'{ori}'</b> should not be capitalized."
                else:
                    msg = "The casing of the word <b>'{ori}'</b> is wrong."
            # then it should be a spacing issue
            else:
                if len(edit.original.text) - 1 == len(edit.corrected.text):
                    msg = "The word <b>'{ori}'</b> should not be written separately."
                elif len(edit.original.text) + 1 == len(edit.corrected.text):
                    msg = "The word <b>'{ori}'</b> should be separated into <b>'{cor}'</b>."
                else:
                    msg = "The word <b>'{ori}'</b> has orthography error."
        else:
            errant_info = (
                self.explanation[pos_type]
                if pos_type in self.explanation
                else self.explanation["Default"]
            )
            msg = (
                errant_info[op_type]
                if op_type in errant_info
                else self.explanation["Default"][op_type]
            )

        msg = (
            "<p>" + msg.format(ori=edit.original.text, cor=edit.corrected.text) + "</p>"
        )

        edit.explanation = msg
        return edit
