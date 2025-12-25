from cooptools.register import Register
from cooptools.ideas.actionItemTracker.dcs import ActionItem, ActionItemPriority, ActionItemCategory, ActionItemStatus, ActionItemMeta, Comment
from typing import Iterable, Dict

class ActionItemTracker:
    def __init__(self):
        self.ai_register = Register[ActionItem]()

    @property
    def ActionItems(self) -> Dict[str, ActionItem]:
        return self.ai_register.Registry

    def add(self, action_items: Iterable[ActionItem]):
        self.ai_register.register(
            to_register=action_items,
            ids=[x.id for x in action_items]
        )

    def _update(self,
                id: str,
                meta_updates: ActionItemMeta = None,
                override_meta: ActionItemMeta = None,
                new_comments: Iterable[Comment] = None
                ):
        to_update: ActionItem = self.ai_register.Registry[id]
        updated = to_update.with_(
            meta_updates=meta_updates,
            meta_override=override_meta,
            added_comments=new_comments
        )
        self.ai_register.unregister(ids=[id])
        self.ai_register.register(
            to_register=[updated],
            ids=[updated.get_id]
        )

    def update(self,
               id: str,
               new_status: ActionItemStatus = None,
               new_priority: ActionItemPriority = None,
               new_category: ActionItemCategory = None,
               new_owner: str = None,
               new_comments: Iterable[Comment] = None):
        self._update(
            id=id,
            meta_updates=ActionItemMeta(
                priority=new_priority,
                status=new_status,
                category=new_category,
                owner=new_owner,
            ),
            new_comments=new_comments
        )

if __name__ == "__main__":
    from pprint import pprint

    ait = ActionItemTracker()
    ait.add([
        ActionItem(id='1', meta=ActionItemMeta(priority=ActionItemPriority.HIGH, status=ActionItemStatus.ACTIVE, category=ActionItemCategory.NEW_REQUEST)),
        ActionItem(id='2', meta=ActionItemMeta(priority=ActionItemPriority.MEDIUM, status=ActionItemStatus.ACTIVE, category=ActionItemCategory.NEW_REQUEST)),
        ActionItem(id='3', meta=ActionItemMeta(priority=ActionItemPriority.LOW, status=ActionItemStatus.ACTIVE, category=ActionItemCategory.NEW_REQUEST)),
        ActionItem(id='4', meta=ActionItemMeta(priority=ActionItemPriority.CRITICAL, status=ActionItemStatus.ACTIVE, category=ActionItemCategory.NEW_REQUEST))
    ])

    pprint(ait.ai_register.Registry)

    ait._update(
        id='1',
        meta_updates=ActionItemMeta(
            owner='MAZZO'
        )
    )

    pprint(ait.ai_register.Registry)

    ait.update(
        id='2',
        new_comments=[
            Comment(
                who='me',
                text='tada'
            )
        ]
    )

    pprint(ait.ai_register.Registry)

