import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils import timezone
from conjunto.audit_log.models import ModelLogEntry
from conjunto.audit_log.registry import log_action_registry
from tests.test_app.models import Person

User = get_user_model()


@pytest.fixture(autouse=True)
def _register_actions():
    # Register actions for validation
    if not log_action_registry.action_exists("test_app.create"):
        log_action_registry.register_action("test_app.create", "Create", "Created")
    if not log_action_registry.action_exists("test_app.update"):
        log_action_registry.register_action("test_app.update", "Update", "Updated")


@pytest.fixture
def user1(db):
    return User.objects.create_user(
        username="user1", first_name="John", last_name="Doe"
    )


@pytest.fixture
def user2(db):
    return User.objects.create_user(username="user2")


@pytest.fixture
def person1(db):
    return Person.objects.create(name="Person 1")


@pytest.fixture
def person2(db):
    return Person.objects.create(name="Person 2")


@pytest.fixture
def ct_person(db):
    return ContentType.objects.get_for_model(Person)


@pytest.fixture
def entry1(user1, person1, ct_person):
    return ModelLogEntry.objects.create(
        content_type=ct_person,
        object_id=str(person1.pk),
        label="Person 1",
        action="test_app.create",
        user=user1,
        timestamp=timezone.now(),
        public=True,
    )


@pytest.fixture
def entry2(user2, person2, ct_person):
    return ModelLogEntry.objects.create(
        content_type=ct_person,
        object_id=str(person2.pk),
        label="Person 2",
        action="test_app.update",
        user=user2,
        timestamp=timezone.now(),
        public=False,
    )


@pytest.fixture
def all_entries(entry1, entry2):
    return [entry1, entry2]


@pytest.mark.django_db
class TestLogEntryQuerySet:
    def test_public(self, entry1, entry2):
        qs = ModelLogEntry.objects.all().public()
        assert qs.count() == 1
        assert entry1 in qs
        assert entry2 not in qs

    def test_get_actions(self, all_entries):
        actions = ModelLogEntry.objects.all().get_actions()
        assert actions == {"test_app.create", "test_app.update"}

    def test_get_user_ids(self, user1, user2, all_entries):
        user_ids = ModelLogEntry.objects.all().get_user_ids()
        assert user_ids == {user1.pk, user2.pk}

    def test_get_users(self, user1, user2, all_entries):
        users = ModelLogEntry.objects.all().get_users()
        assert users.count() == 2
        assert user1 in users
        assert user2 in users

    def test_get_content_type_ids(self, ct_person, all_entries):
        ct_ids = ModelLogEntry.objects.all().get_content_type_ids()
        assert ct_ids == {ct_person.id}

    def test_filter_on_content_type(self, ct_person, all_entries):
        qs = ModelLogEntry.objects.all().filter_on_content_type(ct_person)
        assert qs.count() == 2

    def test_with_instances(self, person1, person2, all_entries):
        qs = ModelLogEntry.objects.all().order_by("timestamp")
        entries_with_instances = list(qs.with_instances())
        assert len(entries_with_instances) == 2

        # Match entries by their action to be sure
        e1_tuple = next(
            t for t in entries_with_instances if t[0].action == "test_app.create"
        )
        e2_tuple = next(
            t for t in entries_with_instances if t[0].action == "test_app.update"
        )

        assert e1_tuple[1] == person1
        assert e2_tuple[1] == person2

    def test_with_instances_deleted_model(self, entry1, mocker):
        qs = ModelLogEntry.objects.filter(pk=entry1.pk)
        mocker.patch.object(ContentType, "model_class", return_value=None)

        entries_with_instances = list(qs.with_instances())
        assert len(entries_with_instances) == 1
        assert entries_with_instances[0][1] is None


@pytest.mark.django_db
class TestBaseLogEntryManager:
    def test_log_action(self, person1, user1):
        entry = ModelLogEntry.objects.log_action(
            instance=person1,
            action="test_app.update",
            user=user1,
            data={"key": "value"},
        )

        assert entry.action == "test_app.update"
        assert entry.user == user1
        assert entry.object_id == str(person1.pk)
        assert entry.data == {"key": "value"}
        assert entry.label == str(person1)

    def test_log_action_with_title(self, person1):
        entry = ModelLogEntry.objects.log_action(
            instance=person1, action="test_app.update", title="Custom Title"
        )
        assert entry.label == "Custom Title"

    def test_log_action_no_pk_raises_error(self):
        person = Person(name="No PK")
        with pytest.raises(
            ValueError,
            match="Attempted to log an action for object .* with empty primary key",
        ):
            ModelLogEntry.objects.log_action(instance=person, action="test_app.create")

    def test_viewable_by_user(self, user1, all_entries):
        # Superuser should see everything
        user1.is_superuser = True
        user1.save()
        assert ModelLogEntry.objects.viewable_by_user(user1).count() == 2

        # Normal user with no permissions should see nothing
        user1.is_superuser = False
        user1.save()
        # clear cached permissions
        if hasattr(user1, "_allowed_content_type_ids"):
            del user1._allowed_content_type_ids
        assert ModelLogEntry.objects.viewable_by_user(user1).count() == 0

        # User with permission for Person should see log entries for Person
        from django.contrib.auth.models import Permission

        ct = ContentType.objects.get_for_model(Person)
        perm = Permission.objects.filter(content_type=ct).first()
        user1.user_permissions.add(perm)
        # We need to refresh the user from DB to ensure permissions are loaded correctly
        user1 = User.objects.get(pk=user1.pk)
        # clear cached permissions
        if hasattr(user1, "_allowed_content_type_ids"):
            del user1._allowed_content_type_ids

        assert ModelLogEntry.objects.viewable_by_user(user1).count() == 2

    def test_get_for_model(self, all_entries):
        qs = ModelLogEntry.objects.get_for_model(Person)
        assert qs.count() == 2

        qs_none = ModelLogEntry.objects.get_for_model(User)
        assert qs_none.count() == 0

    def test_get_for_user(self, user1, entry1):
        qs = ModelLogEntry.objects.get_for_user(user1)
        assert qs.count() == 1
        assert qs.first() == entry1

    def test_for_instance(self, person1, entry1, entry2):
        qs = ModelLogEntry.objects.for_instance(person1)
        assert qs.count() == 1
        assert entry1 in qs
        assert entry2 not in qs


@pytest.mark.django_db
class TestBaseLogEntry:
    def test_user_display_name_with_user(self, entry1, entry2):
        assert entry1.user_display_name == "John Doe"
        assert entry2.user_display_name == "user2"

    def test_user_display_name_system(self):
        entry = ModelLogEntry(action="test_app.create", timestamp=timezone.now())
        assert entry.user_display_name == "system"

    def test_user_display_name_deleted_user(self, entry1, mocker):
        # Simulate deleted user while keeping user_id if DO_NOTHING
        entry1.user_id = 9999
        # Mocking the user property to return None, simulating a deleted user
        # where the ForeignKey still has the ID but the record is gone.
        # Actually, in Django, if you set user_id to something that doesn't exist,
        # accessing .user raises DoesNotExist if not null, or returns None if it was nulled.
        # But here on_delete=models.DO_NOTHING, so it tries to fetch it.

        mocker.patch.object(
            ModelLogEntry, "user", new_callable=mocker.PropertyMock, return_value=None
        )

        # Since it's a cached_property, we might need to clear it if it was accessed
        if "user_display_name" in entry1.__dict__:
            del entry1.user_display_name
        assert "user 9999 (deleted)" in entry1.user_display_name

    def test_object_verbose_name(self, entry1):
        assert entry1.object_verbose_name == "Person"

    def test_str(self, entry1):
        s = str(entry1)
        assert f"ModelLogEntry {entry1.pk}" in s
        assert "test_app.create" in s
        assert "Person" in s
        assert str(entry1.object_id) in s

    def test_message_and_comment(self, entry1):
        # We registered "test_app.create" with message "Created"
        assert entry1.message == "Created"
        assert entry1.comment == ""  # LogFormatter.format_comment defaults to ""

    def test_message_unknown_action(self):
        entry = ModelLogEntry(action="unknown", timestamp=timezone.now())
        assert entry.message == "Unknown unknown"

    def test_clean_validation(self):
        entry = ModelLogEntry(action="unknown", timestamp=timezone.now())
        with pytest.raises(ValidationError):
            entry.clean()

        entry.action = "test_app.create"
        entry.clean()  # Should not raise
