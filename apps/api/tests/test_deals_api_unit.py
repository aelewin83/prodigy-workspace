from types import SimpleNamespace
from uuid import uuid4

from app.api import deals
from app.schemas.deal import DealCreate, DealUpdate


class FakeDB:
    def __init__(self):
        self.deleted = None
        self.committed = False

    def add(self, _obj):
        return None

    def commit(self):
        self.committed = True

    def refresh(self, _obj):
        return None

    def delete(self, obj):
        self.deleted = obj


def test_create_deal_assigns_fields(monkeypatch):
    fake_db = FakeDB()
    user_id = uuid4()

    monkeypatch.setattr(deals, "_assert_workspace_access", lambda *_args, **_kwargs: None)

    payload = DealCreate(
        workspace_id=uuid4(),
        name="Queens 24-Unit",
        address="31-18 37th St",
        asking_price=10_400_000,
    )
    result = deals.create_deal(payload=payload, db=fake_db, user=SimpleNamespace(id=user_id))

    assert result.name == payload.name
    assert result.address == payload.address
    assert result.asking_price == payload.asking_price
    assert result.created_by == user_id
    assert fake_db.committed is True


def test_update_deal_patches_fields(monkeypatch):
    fake_db = FakeDB()
    deal_obj = SimpleNamespace(name="Old", address="Old Addr", asking_price=100)

    monkeypatch.setattr(deals, "_get_deal_with_access", lambda *_args, **_kwargs: deal_obj)

    payload = DealUpdate(name="New Name", asking_price=200)
    result = deals.update_deal(
        deal_id=str(uuid4()),
        payload=payload,
        db=fake_db,
        user=SimpleNamespace(id=uuid4()),
    )

    assert result.name == "New Name"
    assert result.asking_price == 200
    assert result.address == "Old Addr"
    assert fake_db.committed is True


def test_delete_deal_deletes_entity(monkeypatch):
    fake_db = FakeDB()
    deal_obj = SimpleNamespace(id=uuid4())

    monkeypatch.setattr(deals, "_get_deal_with_access", lambda *_args, **_kwargs: deal_obj)

    deals.delete_deal(deal_id=str(uuid4()), db=fake_db, user=SimpleNamespace(id=uuid4()))

    assert fake_db.deleted == deal_obj
    assert fake_db.committed is True
