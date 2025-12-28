#!/opt/local/bin/python
''' Functions that probably make sense only inside Django '''

import base
import datetime
import random
import threading

from . import environment
environment.DeferImport('django.http')
environment.DeferImport('django.template')
environment.DeferImport('django.apps')
environment.DeferImport('django.db')
environment.DeferImport('django.db.models')


available           = False   # xyzzy - need a better way of setting/detecting this



def GetModelByName(name):
  ''' Retrieves any model in the system using appname.classname syntax.
      We rely on django's model registry instead of our own for two benefits:
        - the model name is *case insensitive*
        - the returned model may not be a derivative of our own base.models.Model
  '''
  if not name or not '.' in name:
    return None
  (app, name)     = name.split('.', 1)
  try:
    return apps.apps.get_model(app, name)
  except LookupError:
    pass


def SeedRandomForHttpRequest(request):
  ''' Given an HttpRequest, seed a random number generator unique to the current user. '''
  rand            = random.Random()
  if request and hasattr(request, 'session') and hasattr(request.session, 'session_key'):
    seed          = request.session.session_key
  else:
    seed          = None
  rand.seed(seed)
  return rand



def ApplyDjangoTemplate(filepath=None, raw=None, context={}, **more_context):
  ''' Applies the Django template engine to the text, returns the results. '''
  if not filepath and not raw or filepath and raw:
    raise AttributeError('Must provide filepath= or raw= but not both.')
  if isinstance(context, template.RequestContext):
    context     = context.flatten()
  else:
    pushed      = {}    # we MUST operate on a copy of the input dict, even if it was empty
    if context:
      pushed.update(context)
    context     = pushed
  context.update(more_context)
  request         = context.get('request') or base.utils.ThreadLocalDict().get('request') or http.HttpRequest()
  if filepath:
    return template.loader.render_to_string(filepath, context=context, request=request)
  return template.engines['django'].from_string(raw).render(context=context, request=request)



def RemoteIp(request):
  ''' It's easy to forget both halves when pulling the remote IP from a request;
      you should use this function instead.
  '''
  if not request:
    return None
  return request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR') or None



def SelectDistinct(column, table):
  ''' Does a raw SQL query to select distinct values from a given column in the DB. '''
  if isinstance(column, models.Field):
    column      = column.name
  if isinstance(table, type) and issubclass(table, models.Model):
    table       = table._meta.db_table
  with db.connection.cursor() as cursor:
    cursor.execute('SELECT DISTINCT {column} FROM {table} ORDER BY {column}'.format(column=column, table=table))
    return [x[0] for x in cursor.fetchall() if x]



class CachedQuery:
  ''' Wrapper for executing queries and caching the results.
      Can handle either model queries (querysets) or raw SQL statements.
  '''

  def __init__(self, query, seconds=None):
    ''' if specified, cache will be considere expired after so many seconds '''
    self.lock       = threading.RLock()
    self.lifespan   = seconds and datetime.timedelta(seconds=seconds) or None
    self.updated    = None
    self.results    = []
    self.model      = None
    self.query      = None
    self.raw        = None
    if isinstance(query, str):
      self.raw      = query
    elif query is not None:
      self.model    = query.model
      self.query    = query.query

  @property
  def expired(self):
    now             = base.utils.Now()
    with self.lock:
      if not self.updated:
        return True
      if self.lifespan:
        return (self.updated + self.lifespan) < now
      return False

  def Get(self):
    ''' Returns the query results, cached or fetched as needed. '''
    with self.lock:
      self.Update()
      return self.results

  def Expire(self):
    ''' Forces the next call to Get() or Update() to fetch instead of using the cache. '''
    with self.lock:
      self.updated  = None

  def Update(self):
    ''' Returns False if the cache is valid, or does a fetch to update the cache and returns True. '''
    with self.lock:
      if not self.expired:
        return False
      self.updated  = base.utils.Now()
      if self.model:
        qs          = self.model.objects.all()
        qs.query    = self.query
        self.results  = self.FinalizeResults(list(qs))
      elif self.raw:
        cursor      = db.connection.cursor()
        cursor.execute(self.raw)
        self.results  = self.FinalizeResults(cursor.fetchall())
    return True

  def FinalizeResults(self, results):
    ''' Called under lock to do any transforms on the results that a child class may need. '''
    return results or []
