#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Protocol Buffers - Google's data interchange format
# Copyright 2008 Google Inc.  All rights reserved.
# https://developers.google.com/protocol-buffers/
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.
#     * Neither the name of Google Inc. nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Tests for the pure Python decoder's recursion limit.

The pure Python decoder walks nested sub-messages, groups and unknown groups
with Python recursion, so a hostile payload of nested START_GROUP tags (or of
nested length-delimited sub-messages) used to exhaust the interpreter stack.
The decoder now carries a depth counter and raises message.DecodeError once
DEFAULT_RECURSION_LIMIT levels are exceeded.
"""

try:
  import unittest2 as unittest  #PY26
except ImportError:
  import unittest

import six

from google.protobuf import descriptor_pb2
from google.protobuf import descriptor_pool
from google.protobuf import message
from google.protobuf import message_factory
from google.protobuf import text_format
from google.protobuf import unittest_mset_pb2
from google.protobuf import unittest_mset_wire_format_pb2
from google.protobuf import unittest_pb2
from google.protobuf.internal import api_implementation
from google.protobuf.internal import decoder
from google.protobuf.internal import testing_refleaks
from google.protobuf.internal import wire_format


# The depth guard lives in the pure Python decoder only; the C++ backend has its
# own (differently worded) limit, so skip the message level assertions there.
_IS_PURE_PYTHON = api_implementation.Type() == 'python'

# A stream of identical START_GROUP tags: 0o23 == 0x13 packs field number 2 with
# wire type 3 (WIRETYPE_START_GROUP), so every byte opens one more group.
_NESTED_START_GROUPS = b'\023'


@testing_refleaks.TestCase
class DecoderRecursionTest(unittest.TestCase):

  def tearDown(self):
    # Make sure a test that raised the limit cannot leak it into another test.
    decoder.SetRecursionLimit(decoder.DEFAULT_RECURSION_LIMIT)

  def GenerateNestedProto(self, n):
    """Serializes a TestRecursiveMessage nested n levels deep."""
    msg = unittest_pb2.TestRecursiveMessage()
    sub = msg
    for _ in range(n):
      sub = sub.a
    sub.i = 1
    return msg.SerializeToString()

  def GenerateRepeatedNestedProto(self, n):
    """Serializes a NestedTestAllTypes nested n levels deep via a repeated field."""
    msg = unittest_pb2.NestedTestAllTypes()
    sub = msg
    for _ in range(n):
      sub = sub.repeated_child.add()
    sub.payload.optional_int32 = 1
    return msg.SerializeToString()

  def GenerateNestedGroupProto(self, cycles):
    """Serializes a TestMutualRecursionA whose recursion runs through a group.

    Each cycle costs four levels of decoder recursion: the SubGroup group, its
    sub_message, that message's `b`, and `b`'s `a`.  The innermost `bb` adds one
    more, so the deepest level reached is 4 * cycles + 1.
    """
    msg = unittest_pb2.TestMutualRecursionA()
    sub = msg
    for _ in range(cycles):
      sub = sub.subgroup.sub_message.b.a
    sub.bb.optional_int32 = 1
    return msg.SerializeToString()

  def testDefaultRecursionLimit(self):
    self.assertEqual(100, decoder.DEFAULT_RECURSION_LIMIT)
    self.assertEqual(decoder.DEFAULT_RECURSION_LIMIT, decoder._recursion_limit)

  def test_decode_unknown_group_field_too_many_levels(self):
    # 5 MB of nested START_GROUP tags: without the depth guard this recurses
    # until the interpreter stack is exhausted.
    data = memoryview(_NESTED_START_GROUPS * 5000000)
    six.assertRaisesRegex(
        self,
        message.DecodeError,
        'Error parsing message',
        decoder._DecodeUnknownField,
        data,
        1,
        wire_format.WIRETYPE_START_GROUP,
    )

  @unittest.skipIf(not _IS_PURE_PYTHON,
                   'the depth guard is pure Python only')
  def testUnknownGroupTooManyLevelsWhileParsing(self):
    # The same payload reached through the public parse entry point: field 2 of
    # TestAllTypes is not a group, so every tag lands on the unknown field path.
    msg = unittest_pb2.TestAllTypes()
    with self.assertRaises(message.DecodeError) as context:
      msg.ParseFromString(_NESTED_START_GROUPS * 1000)
    self.assertIn('Error parsing message', str(context.exception))
    self.assertIn('too many levels of nesting', str(context.exception))

  @unittest.skipIf(not _IS_PURE_PYTHON,
                   'the depth guard is pure Python only')
  def testSucceedOkSizedProto(self):
    msg = unittest_pb2.TestRecursiveMessage()
    msg.ParseFromString(self.GenerateNestedProto(100))
    # Walk the whole chain back down to prove 100 levels really were parsed.
    sub = msg
    for _ in range(100):
      sub = sub.a
    self.assertEqual(1, sub.i)

  @unittest.skipIf(not _IS_PURE_PYTHON,
                   'the depth guard is pure Python only')
  def testAssertOversizeProto(self):
    msg = unittest_pb2.TestRecursiveMessage()
    with self.assertRaises(message.DecodeError) as context:
      msg.ParseFromString(self.GenerateNestedProto(101))
    self.assertIn('Error parsing message', str(context.exception))
    self.assertIn('too many levels of nesting', str(context.exception))

  @unittest.skipIf(not _IS_PURE_PYTHON,
                   'the depth guard is pure Python only')
  def testSucceedOversizeProtoWithRaisedLimit(self):
    data = self.GenerateNestedProto(101)
    decoder.SetRecursionLimit(310)
    try:
      msg = unittest_pb2.TestRecursiveMessage()
      msg.ParseFromString(data)
    finally:
      decoder.SetRecursionLimit(decoder.DEFAULT_RECURSION_LIMIT)
    self.assertTrue(msg.HasField('a'))
    # And the default limit is back in force afterwards.
    with self.assertRaises(message.DecodeError):
      unittest_pb2.TestRecursiveMessage().ParseFromString(data)

  @unittest.skipIf(not _IS_PURE_PYTHON,
                   'the depth guard is pure Python only')
  def testRepeatedSubMessageTooManyLevels(self):
    # MessageDecoder's repeated branch is a separate recursion site from the
    # singular one exercised above.
    msg = unittest_pb2.NestedTestAllTypes()
    msg.ParseFromString(self.GenerateRepeatedNestedProto(20))
    sub = msg
    for _ in range(20):
      self.assertEqual(1, len(sub.repeated_child))
      sub = sub.repeated_child[0]
    self.assertEqual(1, sub.payload.optional_int32)

    with self.assertRaises(message.DecodeError) as context:
      unittest_pb2.NestedTestAllTypes().ParseFromString(
          self.GenerateRepeatedNestedProto(110))
    self.assertIn('Error parsing message', str(context.exception))
    self.assertIn('too many levels of nesting', str(context.exception))

  def GenerateNestedMessageSetProto(self, n):
    """Serializes a TestMessageSet nested n levels deep.

    TestMessageSetExtension1 carries a `recursive` field back to TestMessageSet,
    so the chain re-enters MessageSetItemDecoder's DecodeItem at every level.
    DecodeItem itself does not charge a level (it only forwards current_depth,
    as upstream does), so the depth charged is the one `recursive` sub-message
    per level.
    """
    msg = unittest_mset_wire_format_pb2.TestMessageSet()
    sub = msg
    ext = None
    for _ in range(n):
      ext = sub.Extensions[
          unittest_mset_pb2.TestMessageSetExtension1.message_set_extension]
      sub = ext.recursive
    # Merely reading Extensions[...] does not mark presence, so set a scalar on
    # the innermost extension: that propagates presence up the whole chain.
    ext.i = 1
    return msg.SerializeToString()

  @unittest.skipIf(not _IS_PURE_PYTHON,
                   'the depth guard is pure Python only')
  def testMessageSetItemTooManyLevels(self):
    # MessageSetItemDecoder.DecodeItem is registered straight into
    # _decoders_by_tag, so InternalParse calls it with current_depth like any
    # other field decoder -- it must accept the argument and forward it, or the
    # message-set wire format is both a TypeError and an unguarded recursion
    # path.
    cls = unittest_mset_wire_format_pb2.TestMessageSet
    msg = cls()
    msg.ParseFromString(self.GenerateNestedMessageSetProto(20))
    self.assertTrue(msg.HasExtension(
        unittest_mset_pb2.TestMessageSetExtension1.message_set_extension))

    with self.assertRaises(message.DecodeError) as context:
      cls().ParseFromString(self.GenerateNestedMessageSetProto(150))
    self.assertIn('Error parsing message', str(context.exception))
    self.assertIn('too many levels of nesting', str(context.exception))

  @unittest.skipIf(not _IS_PURE_PYTHON,
                   'the depth guard is pure Python only')
  def testGroupFieldTooManyLevels(self):
    msg = unittest_pb2.TestMutualRecursionA()
    # 20 cycles == 81 levels, comfortably under the limit.
    msg.ParseFromString(self.GenerateNestedGroupProto(20))
    self.assertTrue(msg.HasField('subgroup'))
    sub = msg
    for _ in range(20):
      sub = sub.subgroup.sub_message.b.a
    self.assertEqual(1, sub.bb.optional_int32)

    with self.assertRaises(message.DecodeError) as context:
      unittest_pb2.TestMutualRecursionA().ParseFromString(
          self.GenerateNestedGroupProto(30))
    self.assertIn('Error parsing message', str(context.exception))
    self.assertIn('too many levels of nesting', str(context.exception))


@testing_refleaks.TestCase
class RepeatedGroupDecoderRecursionTest(unittest.TestCase):
  """Covers GroupDecoder's repeated branch, its own recursion site.

  3.12.4's test protos have no self-recursive *repeated* group, so the message
  type is built from a descriptor at runtime the way OversizeProtosTest in
  message_test.py does, rather than by adding a .proto (which would also add a
  generated _pb2.py to the wheel).
  """

  @classmethod
  def setUpClass(cls):
    # Reference cycles between DescriptorPool and Message classes are not
    # detected, so build the class exactly once to keep the refleak checker
    # happy (same reasoning as message_test.OversizeProtosTest).
    file_desc = """
      name: "g/recursive_group.proto"
      package: "g"
      message_type {
        name: "RecursiveGroup"
        field {
          name: "child"
          number: 1
          label: LABEL_REPEATED
          type: TYPE_GROUP
          type_name: "g.RecursiveGroup"
        }
        field {
          name: "i"
          number: 2
          label: LABEL_OPTIONAL
          type: TYPE_INT32
        }
      }
    """
    pool = descriptor_pool.DescriptorPool()
    desc = descriptor_pb2.FileDescriptorProto()
    text_format.Parse(file_desc, desc)
    pool.Add(desc)
    cls.proto_cls = message_factory.MessageFactory(pool).GetPrototype(
        pool.FindMessageTypeByName('g.RecursiveGroup'))

  def tearDown(self):
    decoder.SetRecursionLimit(decoder.DEFAULT_RECURSION_LIMIT)

  def GenerateNestedRepeatedGroup(self, n):
    msg = self.proto_cls()
    sub = msg
    for _ in range(n):
      sub = sub.child.add()
    sub.i = 1
    return msg.SerializeToString()

  @unittest.skipIf(not _IS_PURE_PYTHON,
                   'the depth guard is pure Python only')
  def testRepeatedGroupWithinLimit(self):
    msg = self.proto_cls()
    msg.ParseFromString(self.GenerateNestedRepeatedGroup(100))
    sub = msg
    for _ in range(100):
      self.assertEqual(1, len(sub.child))
      sub = sub.child[0]
    self.assertEqual(1, sub.i)

  @unittest.skipIf(not _IS_PURE_PYTHON,
                   'the depth guard is pure Python only')
  def testRepeatedGroupTooManyLevels(self):
    data = self.GenerateNestedRepeatedGroup(101)
    with self.assertRaises(message.DecodeError) as context:
      self.proto_cls().ParseFromString(data)
    self.assertIn('Error parsing message', str(context.exception))
    self.assertIn('too many levels of nesting', str(context.exception))

    # Raising the limit lets the same payload through.
    decoder.SetRecursionLimit(310)
    try:
      self.proto_cls().ParseFromString(data)
    finally:
      decoder.SetRecursionLimit(decoder.DEFAULT_RECURSION_LIMIT)


if __name__ == '__main__':
  unittest.main()
