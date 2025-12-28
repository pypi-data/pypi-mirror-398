#!/opt/local/bin/python
''' Helpers that relate to fuzzy hash values. '''

import hashlib

from ctypes         import c_longlong, c_ulonglong


def FuzzyHash(words):
  ''' Returns a 64-bit fuzzy hash of an (unsorted) list of text tokens.
      Only the first 32 tokens are used.
  '''
  # Today I learned: python's built in hash() function does not return the same results
  # for the same input across different runs of the program.
  def ShortHash(s):
    return hashlib.md5(s.encode('utf8', 'ignore')).digest()
  SLOTS           = 32
  slots           = [None for x in range(SLOTS)]
  free            = SLOTS
  accum           = 0
  for word in words:
    hashed        = ShortHash(word)
    onebyte       = hashed[0]
    slot          = onebyte & 31
    value         = onebyte >> 6
    while slots[slot] is not None:
      slot        = (slot + 1) % SLOTS
    slots[slot]   = value
    free          = free - 1
    if not free:
      break
  for value in slots:
    value         = value or 0
    accum         = (accum << 2) + value
  return c_longlong(accum).value


def FuzzyDistance(phash1, phash2):
  ''' Returns an integer metric of how distant the two FuzzyHash() values are from each other.
      0 means exact match while positive values represent increasing mis-match, up to MAX_FUZZYDISTANCE.

      Note: this implementation is not very fast.  If you're trying to search or filter lots of
      data, know that we keep a hamming_distance() function installed in our Postgres database,
      which will calculate this same result for you at the database level.
  '''
  a               = c_ulonglong(phash1).value
  b               = c_ulonglong(phash2).value
  return '{:b}'.format(a ^ b).count('1')

MAX_FUZZYDISTANCE   = 64


def FuzzySimilarity(fuzzyhash1, fuzzyhash2):
  ''' Calls FuzzyDistance() and converts the result into a float [0 .. 1] for [nosimilarity .. identity] '''
  return 1 - (FuzzyDistance(fuzzyhash1, fuzzyhash2) / MAX_FUZZYDISTANCE)


def SelectByFuzzyHashDistance(model, origin, threshold, fieldname='fuzzyhash'):
  ''' Queries { key: distance } for the closest N items in fuzzy hash space.

        model       - some model with a fuzzy hash field
        origin      - the original fuzzy hash value to search from
        threshold   - distance beyond this much is too much distance

      This relies on a custom hamming_distance() method installed in our server.
  '''
  from django.db  import connection

  db_table        = model._meta.db_table
  column_key      = model._meta.pk.column
  column_hash     = model._meta.get_field(fieldname).column

  QUERY           = ' '.join([x.strip() for x in '''
      SELECT
        {column_key},
        hamming_distance({origin}, {column_hash}) AS distance
      FROM
        {db_table}
      WHERE
          {column_hash} IS NOT NULL
        AND
          hamming_distance({origin}, {column_hash}) <= {threshold}
      ORDER BY distance;
      '''.splitlines()]).strip()
  query           = QUERY.format(db_table=db_table, column_key=column_key, column_hash=column_hash,
                    origin=origin, threshold=threshold)
  cursor          = connection.cursor()
  cursor.execute(query)
  results         = dict(cursor.fetchall())
  return results
