#!/opt/local/bin/python
'''
  an incomplete reference of file extensions and mime types

  we use nested enums and single-character option tags.  this means that a filetype is `in`
  multiple enums at once.  for example:

      base.filetypes.FILE_IMAGE_JPEG in base.FileTypes                      # True

      base.filetypes.FILE_IMAGE_JPEG in base.filetypes.FileTypesImage       # also True

  regarding contenttype:  'text/' is by default iso-8859-1 encoded while 'application/' is
  default utf-8 encoded, meaning we should specify charset on anything that's 'text/'
'''

import base


class FileTypeOption(base.enums.StrOption):
  ''' augments our enum options with more methods '''

  def BestExtension(self):
    ''' returns the first, thus the best, extension for a filetype '''
    return hasattr(self, 'extensions') and self.extensions and self.extensions[0] or None

  def LongestExtension(self):
    ''' returns the longest extension for a filetype '''
    if hasattr(self, 'extensions'):
      extensions    = list(self.extensions)
      extensions.sort(key=lambda x: (-len(x), x))
      return extensions[0]

  def ContentType(self, add_charset=True):
    ''' Returns the contenttype for a filetype. '''
    mimetype        = hasattr(self, 'contenttype') and self.contenttype or ''
    if add_charset and mimetype.startswith('text/'):
      mimetype      += '; charset=utf-8'
    return mimetype or None

  def Parents(self):
    ''' returns a list of all the parents to the current filetype '''
    parents         = []
    while self.enum.parent:
      self          = self.enum.parent
      parents.append(self)
    return parents


class FileTypeEnum(base.Enum):
  ''' specializes the Enum class for file types '''

  stroption         = FileTypeOption

  def GetByExtension(self, ext):
    ''' retrieves a filetype by extension '''
    ext             = (ext or '').lower().strip('.')
    if ext:
      for option in self.by_tag.values():
        if hasattr(option, 'extensions') and ext in option.extensions:
          return option
    return FILE_UNKNOWN



FileTypeEnum.Define(('FILE', 'FileTypes'), (
    ('Unknown',   None),
))


FileTypes.DefineNested(('Archive',      'Z'), (
    {'extensions': ('tar', 'gz', 'tgz'),          'name': 'Tarball',      'contenttype': 'application/x-gzip'},
    {'extensions': ('zip',),                      'name': 'Zip',          'contenttype': 'application/zip'},
    {'extensions': ('webmanifest',),              'name': 'Manifest',     'contenttype': 'application/manifest+json'},
))


FileTypes.DefineNested(('Audio',), (
    {'extensions': ('wav',),                      'name': 'WAVE',         'contenttype': 'audio/wav'},
    {'extensions': ('mp3',),                      'name': 'MP3',          'contenttype': 'audio/mpeg'},
))


FileTypes.DefineNested(('Book',), (
    {'extensions': ('epub',),                     'name': 'ePub',         'contenttype': 'application/epub+zip'},
    {'extensions': ('mobi',),                     'name': 'Mobi',         'contenttype': 'application/x-mobipocket-ebook'},
))


FileTypes.DefineNested(('Certificate',  'K'), (
    {'extensions': ('key',),   'tag': 'p',        'name': 'Private Key',  'contenttype': 'application/x-pem-file'},
    {'extensions': ('crt',),   'tag': 'P',        'name': 'Public Key',   'contenttype': 'application/x-pem-file'},
    {'extensions': ('csr',),                      'name': 'Sign Request', 'contenttype': 'application/x-pem-file'},
    {'extensions': ('pem',),                      'name': 'Intermediate', 'contenttype': 'application/x-pem-file'},
))


FileTypes.DefineNested(('Code',), (
    {'extensions': ('py',),                       'name': 'Python',       'contenttype': 'text/x-python'},
    {'extensions': ('js',),                       'name': 'Javascript',   'contenttype': 'text/javascript'},
    {'extensions': ('rb',),                       'name': 'Ruby',         'contenttype': 'text/x-ruby'},
    {'extensions': ('css', 'scss'),               'name': 'CSS',          'contenttype': 'text/css'},
))


FileTypes.DefineNested(('Data',         'T'), (
    {'extensions': ('json',),                     'name': 'JSON',         'contenttype': 'application/json'},
    {'extensions': ('yaml',),                     'name': 'YAML',         'contenttype': 'application/x-yaml'},
    {'extensions': ('xml',),                      'name': 'XML',          'contenttype': 'text/xml'},
    {'extensions': ('csv',),                      'name': 'CSV',          'contenttype': 'application/x-csv'},
))


FileTypes.DefineNested(('Document',), (
    {'extensions': ('txt',),                      'name': 'Text',         'contenttype': 'text/plain'},
    {'extensions': ('md', 'rd'),                  'name': 'Markdown',     'contenttype': 'text/markdown'},
    {'extensions': ('lux',),                      'name': 'Lux',          'contenttype': 'text/markdown'},  # octoboxy
    {'extensions': ('html', 'htm'),               'name': 'HTML',         'contenttype': 'text/html'},
    {'extensions': ('xhtml',),                    'name': 'XHTML',        'contenttype': 'application/xhtml+xml'},
    {'extensions': ('pdf',),                      'name': 'PDF',          'contenttype': 'application/pdf'},
))


FileTypes.DefineNested(('Font',), (
    {'extensions': ('otf',),                      'name': 'OpenType',     'contenttype': 'font/otf'},
    {'extensions': ('eot',),                      'name': 'MS OpenType',  'contenttype': 'application/vnd.ms-fontobject'},
    {'extensions': ('ttf',),                      'name': 'TrueType',     'contenttype': 'font/ttf'},
    {'extensions': ('woff',),   'tag': 'w',       'name': 'OpenFont 1',   'contenttype': 'font/woff'},
    {'extensions': ('woff2',),  'tag': 'W',       'name': 'OpenFont 2',   'contenttype': 'font/woff2'},
))


FileTypes.DefineNested(('Image',), (
    {'extensions': ('webp',),                     'name': 'WebP',         'contenttype': 'image/webp'},
    {'extensions': ('png',),                      'name': 'PNG',          'contenttype': 'image/png'},
    {'extensions': ('jpg', 'jpeg'),               'name': 'JPEG',         'contenttype': 'image/jpeg'},
    {'extensions': ('gif',),                      'name': 'GIF',          'contenttype': 'image/gif'},
    {'extensions': ('ico',),                      'name': 'Icon',         'contenttype': 'image/x-icon'},
    {'extensions': ('svg',),                      'name': 'SVG',          'contenttype': 'image/svg+xml'},
))


FileTypes.DefineNested(('Video',), (
    {'extensions': ('mp4',),                      'name': 'MPEG',         'contenttype': 'video/mp4'},
    {'extensions': ('mov',),                      'name': 'Quicktime',    'contenttype': 'video/quicktime'},
    {'extensions': ('avi',),                      'name': 'AVI',          'contenttype': 'video/x-msvideo'},
    {'extensions': ('wmv',),                      'name': 'WMV',          'contenttype': 'video/x-ms-wmv'},
))


