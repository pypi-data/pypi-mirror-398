from luqum.tree import (
    NONE_ITEM,
    UnknownOperation,
    AndOperation,
    NoneItem,
    OrOperation,
    Word,
    Phrase,
    Group,
    Prohibit,
)
from luqum.visitor import TreeTransformer


class FilterQueryTransformer(TreeTransformer):
    allowed = [
        UnknownOperation,
        AndOperation,
        OrOperation,
        Group,
        Prohibit,
        Phrase,
        Word,
        NoneItem,
    ]

    def visit_prohibit(self, node, context):
        """
        If a word is in a Prohibit (e.g. -word), we want to keep it,
        because it indicates that the word should not be
        present in the search results.
        """

        context["retain_words"] = True

        return self.generic_visit(node, context)

    def visit_word(self, node, context):
        """
        We remove all words that are not part of a phrase,
        except for those in a Prohibit (e.g. -word),
        because we're trying to limit the search to phrases and
        negations only.
        """

        if context.get("retain_words"):
            # If we're in a prohibit, we keep the word as it indicates
            # that the word should not be present in the search results.
            yield node
        else:
            yield NONE_ITEM

    def visit_or_operation(self, node, context):
        """
        If any child is a NoneItem, return NoneItem, e.g.
        OrOperation(NoneItem(), Phrase("test")) should return NoneItem,
        because NoneItem is effectively a wildcard that could match anything
        and an OR of that with anything else should still match anything.
        This removes OR in the case where one of the terms has been removed.
        """

        context["retain_words"] = True

        nodes = self.generic_visit(node, context)

        for n in nodes:
            if any(isinstance(child, NoneItem) for child in n.children):
                yield NONE_ITEM
            else:
                yield n

    def visit_and_operation(self, node, context):
        """
        If any child is a NoneItem, return the other children, e.g.
        AndOperation(NoneItem(), Phrase("test")) should return just Phrase("test").
        This removes AND in the case where one of the terms has been removed.
        """

        nodes = self.generic_visit(node, context)

        for n in nodes:
            if any(isinstance(child, NoneItem) for child in n.children):
                for child in n.children:
                    if not isinstance(child, NoneItem):
                        yield child
            else:
                yield n

    def generic_visit(self, node, context):
        nodes = super().generic_visit(node, context)

        for n in nodes:
            # Return NoneItem if all the children of the nodes are NoneItem
            if len(n.children) > 0 and all(
                isinstance(child, NoneItem) for child in n.children
            ):
                yield NONE_ITEM
            # If the node is not one of the allowed types,
            elif not isinstance(n, tuple(self.allowed)):
                # if the node has children,
                if len(n.children) > 0:
                    # yield them,
                    for child in n.children:
                        yield child
                else:
                    yield NONE_ITEM
            else:
                yield n

class WithoutNegationsTransformer(TreeTransformer):
    def visit_prohibit(self, node, context):
        yield NONE_ITEM
