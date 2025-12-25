from django.contrib.auth.models import User

from itoutils.django.testing import assertSnapshotQueries


def test_assert_snapshot_queries(db, snapshot):
    with assertSnapshotQueries(snapshot):
        User.objects.count()
