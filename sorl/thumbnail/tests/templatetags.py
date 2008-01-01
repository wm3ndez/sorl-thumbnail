import unittest
import os
import time
from PIL import Image
from django.conf import settings
from django.template import Template, Context, TemplateSyntaxError
from sorl.thumbnail.tests.classes import BaseTest, RELATIVE_PIC_NAME


class ThumbnailTagTest(BaseTest):
    def render_template(self, source):
        context = Context({
            'source': RELATIVE_PIC_NAME,
            'invalid_source': 'not%s' % RELATIVE_PIC_NAME})
        source = '{% load thumbnail %}' + source
        return Template(source).render(context)

    def testTagInvalid(self):
        basename = RELATIVE_PIC_NAME.replace('.', '_')

        # No args, or wrong number of args
        src = '{% thumbnail %}'
        self.assertRaises(TemplateSyntaxError, self.render_template, src)
        src = '{% thumbnail source %}'
        self.assertRaises(TemplateSyntaxError, self.render_template, src)
        src = '{% thumbnail source 80x80 Xas variable %}'
        self.assertRaises(TemplateSyntaxError, self.render_template, src)
        src = '{% thumbnail source 80x80 as variable X %}'
        self.assertRaises(TemplateSyntaxError, self.render_template, src)

        # Invalid size
        src = '{% thumbnail source 240xABC %}'
        self.assertRaises(TemplateSyntaxError, self.render_template, src)

        # Invalid option
        src = '{% thumbnail source 240xABC invalid %}'
        self.assertRaises(TemplateSyntaxError, self.render_template, src)

        # Invalid quality
        src = '{% thumbnail source 240xABC quality=a %}'
        self.assertRaises(TemplateSyntaxError, self.render_template, src)

        # Invalid source with THUMBNAIL_DEBUG = False
        src = '{% thumbnail invalid_source 80x80 %}'
        self.assertEqual(self.render_template(src), '')
        # ...and with THUMBNAIL_DEBUG = True
        self.change_settings.change({'DEBUG': True})
        self.assertRaises(TemplateSyntaxError, self.render_template, src)

    def testTag(self):
        expected_base = RELATIVE_PIC_NAME.replace('.', '_')

        # Basic
        output = self.render_template('src="'
            '{% thumbnail source 240x240 %}"')
        expected = '%s_240x240_q85.jpg' % expected_base
        expected_fn = os.path.join(settings.MEDIA_ROOT, expected)
        expected_url = ''.join((settings.MEDIA_URL, expected))
        self.verify_thumbnail((240, 180), expected_filename=expected_fn)
        self.assertEqual(output, 'src="%s"' % expected_url)

        # Variable does not exist
        output = self.render_template('{% thumbnail no_variable 80x80 %}')
        self.assertEqual(output, '')

        # On context
        output = self.render_template('height:'
            '{% thumbnail source 240x240 as thumb %}{{ thumb.height }}')
        self.assertEqual(output, 'height:180')

        # On context, variable does not exist
        output = self.render_template(
            '{% thumbnail no_variable 80x80 as thumb %}{{ thumb }}')
        self.assertEqual(output, '')

        # With options and quality
        output = self.render_template('src="'
            '{% thumbnail source 240x240 sharpen,crop,quality=95 %}"')
        # Note that the order of opts comes from VALID_OPTIONS to ensure a
        # consistent filename.
        expected = '%s_240x240_crop_sharpen_q95.jpg' % expected_base
        expected_fn = os.path.join(settings.MEDIA_ROOT, expected)
        expected_url = ''.join((settings.MEDIA_URL, expected))
        self.verify_thumbnail((240, 240), expected_filename=expected_fn)
        self.assertEqual(output, 'src="%s"' % expected_url)

        # With option and quality on context (also using its unicode method to
        # display the url)
        output = self.render_template(
            '{% thumbnail source 240x240 sharpen,crop,quality=95 as thumb %}'
            'width:{{ thumb.width }}, url:{{ thumb }}')
        self.assertEqual(output, 'width:240, url:%s' % expected_url)

byteunit_tests = """
>>> from sorl.thumbnail.templatetags.thumbnail import byteunit

>>> byteunit('abc')
'abc'
>>> byteunit(100, 'invalid')
100

>>> bytes = 20
>>> byteunit(bytes)
'20 B'
>>> byteunit(bytes, 'auto1000')
'20 B'

>>> bytes = 1001
>>> byteunit(bytes)
'1001 B'
>>> byteunit(bytes, 'auto1000')
'1 kB'

>>> bytes = 10100
>>> byteunit(bytes)
'9.9 KiB'

# Note that the decimal place is only used if < 10
>>> byteunit(bytes, 'auto1000')
'10 kB'

>>> bytes = 190000000
>>> byteunit(bytes)
'181 MiB'
>>> byteunit(bytes, 'auto1000')
'190 MB'

# 'auto*long' methods use pluralisation:
>>> byteunit(1, 'auto1024long')
'1 byte'
>>> byteunit(1, 'auto1000long')
'1 byte'
>>> byteunit(2, 'auto1024long')
'2 bytes'
>>> byteunit(0, 'auto1000long')
'0 bytes'

# Test all 'auto*long' output:
>>> for i in range(1,10):
...     print '%s, %s' % (byteunit(1024**i, 'auto1024long'), 
...                       byteunit(1000**i, 'auto1000long'))
1 kibibyte, 1 kilobyte
1 mebibyte, 1 megabyte
1 gibibyte, 1 gigabyte
1 tebibyte, 1 terabyte
1 pebibyte, 1 petabyte
1 exbibyte, 1 exabyte
1 zebibyte, 1 zettabyte
1 yobibyte, 1 yottabyte
1024 yobibytes, 1000 yottabytes

# Test all fixed outputs (eg 'kB' or 'MiB')
>>> from sorl.thumbnail.templatetags.thumbnail import byteunit_formats, byteunit_long_formats
>>> for f in byteunit_formats:
...     print '%s (%siB, %sB):' % (byteunit_long_formats[f], f.upper(), f)
...     for i in range(0, 10):
...         print ' %s, %s' % (byteunit(1024**i, '%siB' % f.upper()),
...                            byteunit(1000**i, '%sB' % f))
kilo (KiB, kB):
 0.0009765625, 0.001
 1.0, 1.0
 1024.0, 1000.0
 1048576.0, 1000000.0
 1073741824.0, 1000000000.0
 1.09951162778e+12, 1e+12
 1.12589990684e+15, 1e+15
 1.15292150461e+18, 1e+18
 1.18059162072e+21, 1e+21
 1.20892581961e+24, 1e+24
mega (MiB, MB):
 0.0, 1e-06
 0.0009765625, 0.001
 1.0, 1.0
 1024.0, 1000.0
 1048576.0, 1000000.0
 1073741824.0, 1000000000.0
 1.09951162778e+12, 1e+12
 1.12589990684e+15, 1e+15
 1.15292150461e+18, 1e+18
 1.18059162072e+21, 1e+21
giga (GiB, GB):
 0.0, 1e-09
 0.0, 1e-06
 0.0009765625, 0.001
 1.0, 1.0
 1024.0, 1000.0
 1048576.0, 1000000.0
 1073741824.0, 1000000000.0
 1.09951162778e+12, 1e+12
 1.12589990684e+15, 1e+15
 1.15292150461e+18, 1e+18
tera (TiB, TB):
 0.0, 1e-12
 0.0, 1e-09
 0.0, 1e-06
 0.0009765625, 0.001
 1.0, 1.0
 1024.0, 1000.0
 1048576.0, 1000000.0
 1073741824.0, 1000000000.0
 1.09951162778e+12, 1e+12
 1.12589990684e+15, 1e+15
peta (PiB, PB):
 0.0, 1e-15
 0.0, 1e-12
 0.0, 1e-09
 0.0, 1e-06
 0.0009765625, 0.001
 1.0, 1.0
 1024.0, 1000.0
 1048576.0, 1000000.0
 1073741824.0, 1000000000.0
 1.09951162778e+12, 1e+12
exa (EiB, EB):
 0.0, 1e-18
 0.0, 1e-15
 0.0, 1e-12
 0.0, 1e-09
 0.0, 1e-06
 0.0009765625, 0.001
 1.0, 1.0
 1024.0, 1000.0
 1048576.0, 1000000.0
 1073741824.0, 1000000000.0
zetta (ZiB, ZB):
 0.0, 1e-21
 0.0, 1e-18
 0.0, 1e-15
 0.0, 1e-12
 0.0, 1e-09
 0.0, 1e-06
 0.0009765625, 0.001
 1.0, 1.0
 1024.0, 1000.0
 1048576.0, 1000000.0
yotta (YiB, YB):
 0.0, 1e-24
 0.0, 1e-21
 0.0, 1e-18
 0.0, 1e-15
 0.0, 1e-12
 0.0, 1e-09
 0.0, 1e-06
 0.0009765625, 0.001
 1.0, 1.0
 1024.0, 1000.0
"""