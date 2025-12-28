from typing import Type

import simplejson as json

import seshat
from seshat.general.transformer_story.base import (
    BaseTransformerStory,
    BaseChallenge,
    Describable,
)
from seshat.utils.find_classes import find_classes


class GenerateStoryCommand:
    def generate(self):
        return json.dumps(
            {
                "transformers": self.get_doc(BaseTransformerStory),
                "challenges": self.get_doc(BaseChallenge),
            },
            indent=4,
            default=str,
            ignore_nan=True,
        )

    def get_doc(self, target: Type[Describable]):
        docs = []
        for d in find_classes(seshat, target):
            try:
                docs.append(d().generate_doc())
            except Exception:
                import traceback

                print(f"ERROR generating doc for {d}:")
                print(f"  Class: {d}")
                traceback.print_exc()
                raise
        return docs
