# -*- coding: utf-8; -*-

from wuttaweb import diffs as mod
from wuttaweb.testing import WebTestCase, VersionWebTestCase


class TestWebDiff(WebTestCase):

    def make_diff(self, *args, **kwargs):
        return mod.WebDiff(self.config, *args, **kwargs)

    def test_render_html(self):
        old_data = {"foo": "bar"}
        new_data = {"foo": "baz"}
        diff = self.make_diff(old_data, new_data)
        html = diff.render_html()
        self.assertIn("<table", html)
        self.assertIn("<tr>", html)
        self.assertIn("&#39;bar&#39;", html)
        self.assertIn(f'style="background-color: {diff.old_color}"', html)
        self.assertIn("&#39;baz&#39;", html)
        self.assertIn(f'style="background-color: {diff.new_color}"', html)
        self.assertIn("</tr>", html)
        self.assertIn("</table>", html)


class TestVersionDiff(VersionWebTestCase):

    def make_diff(self, *args, **kwargs):
        return mod.VersionDiff(self.config, *args, **kwargs)

    def test_constructor(self):
        import sqlalchemy_continuum as continuum

        model = self.app.model
        user = model.User(username="fred")
        self.session.add(user)
        self.session.commit()
        user.username = "freddie"
        self.session.commit()
        self.session.delete(user)
        self.session.commit()

        txncls = continuum.transaction_class(model.User)
        vercls = continuum.version_class(model.User)
        versions = self.session.query(vercls).order_by(vercls.transaction_id).all()
        self.assertEqual(len(versions), 3)

        version = versions[0]
        diff = self.make_diff(version)
        self.assertEqual(diff.nature, "create")
        self.assertEqual(
            diff.fields,
            ["active", "person_uuid", "prevent_edit", "username", "uuid"],
        )

        version = versions[1]
        diff = self.make_diff(version)
        self.assertEqual(diff.nature, "update")
        self.assertEqual(
            diff.fields,
            ["active", "person_uuid", "prevent_edit", "username", "uuid"],
        )

        version = versions[2]
        diff = self.make_diff(version)
        self.assertEqual(diff.nature, "delete")
        self.assertEqual(
            diff.fields,
            ["active", "person_uuid", "prevent_edit", "username", "uuid"],
        )

    def test_render_version_value(self):
        import sqlalchemy_continuum as continuum

        model = self.app.model
        person = model.Person(full_name="Fred Flintstone")
        self.session.add(person)

        # create, update, delete user
        user = model.User(username="fred", person=person)
        self.session.add(user)
        self.session.commit()
        user.username = "freddie"
        self.session.commit()
        self.session.delete(user)
        self.session.commit()

        txncls = continuum.transaction_class(model.User)
        vercls = continuum.version_class(model.User)
        versions = self.session.query(vercls).order_by(vercls.transaction_id).all()
        self.assertEqual(len(versions), 3)

        # create (1st version)
        version = versions[0]
        diff = self.make_diff(version)
        self.assertEqual(diff.nature, "create")
        self.assertEqual(diff.render_old_value("username"), "")
        self.assertIn("fred", diff.render_new_value("username"))
        self.assertNotIn("freddie", diff.render_new_value("username"))
        self.assertEqual(diff.render_old_value("person_uuid"), "")
        # rendered person_uuid includes display name
        html = diff.render_new_value("person_uuid")
        self.assertIn(str(person.uuid), html)
        self.assertIn("Fred Flintstone", html)

        # update (2nd version)
        version = versions[1]
        diff = self.make_diff(version)
        self.assertEqual(diff.nature, "update")
        self.assertIn("fred", diff.render_old_value("username"))
        self.assertNotIn("freddie", diff.render_old_value("username"))
        self.assertIn("freddie", diff.render_new_value("username"))
        # rendered person_uuid includes display name
        html = diff.render_old_value("person_uuid")
        self.assertIn(str(person.uuid), html)
        self.assertIn("Fred Flintstone", html)
        html = diff.render_new_value("person_uuid")
        self.assertIn(str(person.uuid), html)
        self.assertIn("Fred Flintstone", html)

        # delete (3rd version)
        version = versions[2]
        diff = self.make_diff(version)
        self.assertEqual(diff.nature, "delete")
        self.assertIn("freddie", diff.render_old_value("username"))
        self.assertEqual(diff.render_new_value("username"), "")
        # rendered person_uuid includes display name
        html = diff.render_old_value("person_uuid")
        self.assertIn(str(person.uuid), html)
        self.assertIn("Fred Flintstone", html)
        self.assertEqual(diff.render_new_value("person_uuid"), "")
