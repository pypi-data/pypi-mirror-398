import pytest
from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.db import models

from activity_tracker.context import (
    clear_actor,
    clear_request_metadata,
    mark_model_audited,
    set_actor,
    set_request_metadata,
)
from activity_tracker.models import ActivityLog
from activity_tracker.services import track_activity

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def enable_activity_tracker_settings():
    django_settings.ACTIVITY_TRACKER = {
        "ENABLED": True,
        "PERSIST": True,
        "TRACK_ANONYMOUS": True,
    }


class DummyModel(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        app_label = "tests"


class Dummy:
    pk = 1


def test_signal_skipped_when_model_marked_audited():
    mark_model_audited(Dummy)

    track_activity(
        action="EXPLICIT",
        target=Dummy(),
    )

    # The invariant: no duplicate logs
    assert ActivityLog.objects.count() <= 1


def test_track_activity_creates_log():
    user = User.objects.create_user(username="alice")

    activity = track_activity(
        action="TEST_ACTION",
        actor=user,
        metadata={"foo": "bar"},
    )

    assert activity is not None
    assert ActivityLog.objects.count() == 1
    assert activity.actor == user
    assert activity.action == "TEST_ACTION"


def test_explicit_actor_overrides_context():
    context_user = User.objects.create_user(username="context")
    explicit_user = User.objects.create_user(username="explicit")

    set_actor(context_user)

    activity = track_activity(
        action="OVERRIDE_TEST",
        actor=explicit_user,
    )

    clear_actor()

    assert activity.actor == explicit_user


def test_metadata_merge_order():
    user = User.objects.create_user(username="meta")

    set_request_metadata({"ip": "1.1.1.1", "source": "request"})

    activity = track_activity(
        action="META_TEST",
        actor=user,
        metadata={"source": "explicit", "reason": "manual"},
    )

    clear_request_metadata()

    assert activity.metadata["ip"] == "1.1.1.1"
    assert activity.metadata["source"] == "explicit"
    assert activity.metadata["reason"] == "manual"


def test_context_isolation():
    user = User.objects.create_user(username="ctx")

    set_request_metadata({"ip": "2.2.2.2"})

    activity1 = track_activity(action="A", actor=user)
    clear_request_metadata()

    activity2 = track_activity(action="B", actor=user)

    assert "ip" in activity1.metadata
    assert "ip" not in activity2.metadata
