#!/usr/bin/python
# Copyright 2012 Google Inc.  All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License.  You may obtain a copy
# of the License at: http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distrib-
# uted under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
# OR CONDITIONS OF ANY KIND, either express or implied.  See the License for
# specific language governing permissions and limitations under the License.

"""Tests for publish.py."""

__author__ = 'kpy@google.com (Ka-Ping Yee)'

import model
import test_utils


class PublishTest(test_utils.BaseTest):
  """Tests for the publish.py request handler."""

  def setUp(self):
    super(PublishTest, self).setUp()
    test_utils.BecomeAdmin()
    self.map_object = model.Map.Create('{"title": "test map"}', 'xyz.com')
    self.map_id = self.map_object.id

  def testPost(self):
    """Tests the Publish handler."""
    self.DoPost('/foo.com/.publish', 'label=abc&map=%s' % self.map_id)
    entry = model.CatalogEntry.Get('foo.com', 'abc')
    self.assertEquals(self.map_id, entry.map_id)
    self.assertFalse(entry.is_listed)

  def testRepublish(self):
    """Verifies that the is_listed status of an existing entry is preserved."""
    # Publish an entry and make it listed.
    self.DoPost('/foo.com/.publish', 'label=abc&map=%s' % self.map_id)
    entry = model.CatalogEntry.Get('foo.com', 'abc')
    entry.is_listed = True
    entry.Put()

    # Add a new map version.
    vid = self.map_object.PutNewVersion('{"title": "new version"}')

    # Republish.
    self.DoPost('/foo.com/.publish', 'label=abc&map=%s' % self.map_id)

    # Confirm that the entry is still listed and points at the new version.
    entry = model.CatalogEntry.Get('foo.com', 'abc')
    self.assertTrue(entry.is_listed)
    self.assertEquals(vid, entry.model.map_version.key().id())
    self.assertEquals('{"title": "new version"}', entry.maproot_json)

  def testInvalidLabels(self):
    """Tests to makes sure invalid labels don't get published."""
    invalid_labels = ['', '!', 'f#oo', '?a', 'qwerty!', '9 3']
    for label in invalid_labels:
      self.DoPost('/foo.com/.publish',
                  'label=%s&map=%s' % (label, self.map_id), status=400)

  def testValidLabels(self):
    """Tests to makes sure valid labels do get published."""
    valid_labels = ['a', 'B', '2', 'a2', 'q-w_e-r_t-y', '93']
    for label in valid_labels:
      self.DoPost('/foo.com/.publish', 'label=%s&map=%s' % (label, self.map_id))
      entry = model.CatalogEntry.Get('foo.com', label)
      self.assertNotEqual(entry, None)
      self.assertEquals(self.map_id, entry.map_id)
      self.assertFalse(entry.is_listed)

  def testRemove(self):
    """Tests removal of a catalog entry."""
    model.CatalogEntry.Create('foo.com', 'abc', self.map_object)
    self.assertNotEqual(None, model.CatalogEntry.Get('foo.com', 'abc'))
    self.DoPost('/foo.com/.publish', 'label=abc&remove=1')
    self.assertEquals(None, model.CatalogEntry.Get('foo.com', 'abc'))

if __name__ == '__main__':
  test_utils.main()
