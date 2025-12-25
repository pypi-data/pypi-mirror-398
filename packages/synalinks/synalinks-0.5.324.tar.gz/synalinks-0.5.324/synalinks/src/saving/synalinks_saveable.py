# Modified from: keras/src/saving/keras_saveable.py
# Original authors: François Chollet et al. (Keras Team)
# License Apache 2.0: (c) 2025 Yoan Sallami (Synalinks Team)


class SynalinksSaveable:
    def _obj_type(self):
        raise NotImplementedError(
            "SynalinksSaveable subclases must provide an implementation for `obj_type()`"
        )
