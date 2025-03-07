import unittest
import rss_reader
import sys
import datetime
import bs4


class TestParseArgs(unittest.TestCase):

    def setUp(self):
        self.fake_exit_status = None
        self.orig_sys_exit = sys.exit
        sys.exit = self._fake_sys_exit

    def _fake_sys_exit(self, status=0):
        self.fake_exit_status = status

    def tearDown(self):
        sys.exit = self.orig_sys_exit

    def test_empty(self):
        rss_reader.parse_args([])
        self.assertNotEqual(self.fake_exit_status, None)

    def test_only_url(self):
        args = rss_reader.parse_args(['mockurl'])
        self.assertFalse(args.json)
        self.assertFalse(args.verbose)
        self.assertEqual(args.source, 'mockurl')
        self.assertEqual(args.limit, None)

    def test_version(self):
        rss_reader.parse_args(['--version'])
        self.assertNotEqual(self.fake_exit_status, None)

    def test_json(self):
        args = rss_reader.parse_args(['--json', 'mockurl2'])
        self.assertTrue(args.json)
        self.assertFalse(args.verbose)
        self.assertEqual(args.source, 'mockurl2')
        self.assertEqual(args.limit, None)

    def test_verbose(self):
        args = rss_reader.parse_args(['--verbose', 'mockurl3'])
        self.assertFalse(args.json)
        self.assertTrue(args.verbose)
        self.assertEqual(args.source, 'mockurl3')
        self.assertEqual(args.limit, None)

    def test_limit(self):
        args = rss_reader.parse_args(['--limit', '10', 'mockurl4'])
        self.assertFalse(args.json)
        self.assertFalse(args.verbose)
        self.assertEqual(args.source, 'mockurl4')
        self.assertEqual(args.limit, 10)


class TestParseFeed(unittest.TestCase):

    SAMPLE_2_0 = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
   <channel>
      <title>Liftoff News</title>
      <link>http://liftoff.msfc.nasa.gov/</link>
      <description>Liftoff to Space Exploration.</description>
      <language>en-us</language>
      <pubDate>Tue, 10 Jun 2003 04:00:00 GMT</pubDate>
      <lastBuildDate>Tue, 10 Jun 2003 09:41:01 GMT</lastBuildDate>
      <docs>http://blogs.law.harvard.edu/tech/rss</docs>
      <generator>Weblog Editor 2.0</generator>
      <managingEditor>editor@example.com</managingEditor>
      <webMaster>webmaster@example.com</webMaster>
      <item>
         <title>Star City</title>
         <link>http://liftoff.msfc.nasa.gov/news/2003/news-starcity.asp</link>
         <description>&lt;img src="https://example.com/images/logo.png"&gt;How do Americans get ready to work with Russians aboard the International Space Station? They take a crash course in culture, language and protocol at Russia's &lt;a href="http://howe.iki.rssi.ru/GCTC/gctc_e.htm"&gt;Star City&lt;/a&gt;.</description>
         <pubDate>Tue, 03 Jun 2003 09:39:21 GMT</pubDate>
         <guid>http://liftoff.msfc.nasa.gov/2003/06/03.html#item573</guid>
      </item>
      <item>
         <description>Sky watchers in Europe, Asia, and parts of Alaska and Canada will experience a &lt;a href="http://science.nasa.gov/headlines/y2003/30may_solareclipse.htm"&gt;partial eclipse of the Sun&lt;/a&gt; on Saturday, May 31st.</description>
         <pubDate>Fri, 30 May 2003 11:06:42 GMT</pubDate>
         <guid>http://liftoff.msfc.nasa.gov/2003/05/30.html#item572</guid>
      </item>
      <item>
         <title>The Engine That Does More</title>
         <link>http://liftoff.msfc.nasa.gov/news/2003/news-VASIMR.asp</link>
         <description>Before man travels to Mars, NASA hopes to design new engines that will let us fly through the Solar System more quickly.  The proposed VASIMR engine would do that.</description>
         <pubDate>Tue, 27 May 2003 08:37:32 GMT</pubDate>
         <guid>http://liftoff.msfc.nasa.gov/2003/05/27.html#item571</guid>
      </item>
      <item>
         <title>Astronauts' Dirty Laundry</title>
         <link>http://liftoff.msfc.nasa.gov/news/2003/news-laundry.asp</link>
         <description>Compared to earlier spacecraft, the International Space Station has many luxuries, but laundry facilities are not one of them.  Instead, astronauts have other options.</description>
         <pubDate>Tue, 20 May 2003 08:56:02 GMT</pubDate>
         <guid>http://liftoff.msfc.nasa.gov/2003/05/20.html#item570</guid>
      </item>
   </channel>
</rss>"""

    def test_sample20(self):
        content = self.SAMPLE_2_0
        feed = rss_reader.parse_feed(content)
        self.assertEqual(feed['title'], 'Liftoff News')
        self.assertEqual(feed['link'], 'http://liftoff.msfc.nasa.gov/')
        self.assertEqual(feed['description'], 'Liftoff to Space Exploration.')
        self.assertEqual(len(feed['items']), 4)
        self.assertEqual(feed['items'][0]['title'], 'Star City')
        self.assertEqual(feed['items'][0]['link'], 'http://liftoff.msfc.nasa.gov/news/2003/news-starcity.asp')
        self.assertEqual(feed['items'][0]['pubDate'], datetime.datetime(2003, 6, 3, 9, 39, 21, tzinfo=datetime.timezone.utc))
        self.assertEqual(feed['items'][0]['description'], '[image 2]How do Americans get ready to work with Russians aboard the International Space Station? They take a crash course in culture, language and protocol at Russia\'s Star City[3].')
        self.assertEqual(len(feed['items'][0]['links']), 3)
        self.assertEqual(feed['items'][0]['links'][0], ('http://liftoff.msfc.nasa.gov/news/2003/news-starcity.asp', 'link'))
        self.assertEqual(feed['items'][0]['links'][1], ('https://example.com/images/logo.png', 'image'))
        self.assertEqual(feed['items'][0]['links'][2], ('http://howe.iki.rssi.ru/GCTC/gctc_e.htm', 'link'))

    def test_illformed(self):
        with self.assertRaises(ValueError):
            content = "Invalid RSS"
            rss_reader.parse_feed(content)

    def test_limit(self):
        content = self.SAMPLE_2_0
        feed = rss_reader.parse_feed(content)
        rss_reader.limit_feed(feed, 1)
        self.assertEqual(len(feed['items']), 1)

    def test_overlimit(self):
        content = self.SAMPLE_2_0
        feed = rss_reader.parse_feed(content)
        rss_reader.limit_feed(feed, 5)
        self.assertEqual(len(feed['items']), 4)

    def test_text(self):
        content = self.SAMPLE_2_0
        feed = rss_reader.parse_feed(content)
        rss_reader.limit_feed(feed, 1)
        text = rss_reader.format_text(feed)
        self.assertEqual(text,
                         "Feed: Liftoff News\n\nTitle: Star City\n"
                         "Date: Tue, 03 Jun 2003 09:39:21 +0000\n"
                         "Link: http://liftoff.msfc.nasa.gov/news/2003/news-starcity.asp\n\n"
                         "[image 2]How do Americans get ready to work with Russians aboard the International Space Station? They take a crash course in culture, language and protocol at Russia\'s Star City[3].\n\n"
                         "Links:\n[1]: http://liftoff.msfc.nasa.gov/news/2003/news-starcity.asp (link)\n"
                         "[2]: https://example.com/images/logo.png (image)\n"
                         "[3]: http://howe.iki.rssi.ru/GCTC/gctc_e.htm (link)\n")

    def test_json(self):
        content = self.SAMPLE_2_0
        feed = rss_reader.parse_feed(content)
        rss_reader.limit_feed(feed, 1)
        json = rss_reader.format_json(feed)
        self.maxDiff = None
        self.assertEqual(json,
                         '{\n "title": "Liftoff News",\n "link": "http://liftoff.msfc.nasa.gov/",\n'
                         ' "description": "Liftoff to Space Exploration.",\n "items": [\n'
                         '  {\n   "title": "Star City",\n   "pubDate": "Tue, 03 Jun 2003 09:39:21 +0000",\n'
                         '   "link": "http://liftoff.msfc.nasa.gov/news/2003/news-starcity.asp",\n'
                         '   "description": "<img src=\\"https://example.com/images/logo.png\\">How do Americans get ready to work with Russians aboard the International Space Station? They take a crash course in culture, language and protocol at Russia\'s <a href=\\"http://howe.iki.rssi.ru/GCTC/gctc_e.htm\\">Star City</a>.",\n'
                         '   "links": [\n'
                         '    [\n     "http://liftoff.msfc.nasa.gov/news/2003/news-starcity.asp",\n     "link"\n    ],\n'
                         '    [\n     "https://example.com/images/logo.png",\n     "image"\n    ],\n'
                         '    [\n     "http://howe.iki.rssi.ru/GCTC/gctc_e.htm",\n     "link"\n    ]\n'
                         '   ]\n  }\n ]\n}')


class TestAuxiliary(unittest.TestCase):

    def test_get_link(self):
        elem = bs4.BeautifulSoup('<enclosure url="http://www.scripting.com/mp3s/weatherReportSuite.mp3" length="12216320" type="audio/mpeg" />', 'lxml-xml').enclosure
        link = rss_reader.get_link(elem)
        self.assertEqual(link, ('http://www.scripting.com/mp3s/weatherReportSuite.mp3', 'audio'))

    def test_get_text(self):
        self.assertEqual(rss_reader.get_text(None), '')


class TextCache(unittest.TestCase):

    def test_merge_items(self):
        self.maxDiff = None
        alist = [
            {
                'title': 'A',
                'link': 'http://example.com/A',
                'description': 'Describe A',
                'pubDate': datetime.datetime.fromisoformat('2022-03-01T10:11:23+03:00')
            },
            {
                'title': 'B',
                'link': 'http://example.com/B',
                'description': 'Describe B',
                'pubDate': datetime.datetime.fromisoformat('2022-02-02T10:11:23+03:00')
            },
        ]
        blist = [
            {
                'title': 'B',
                'link': 'http://example.com/B',
                'description': 'Describe B',
                'pubDate': datetime.datetime.fromisoformat('2022-02-02T10:11:23+03:00')
            },
            {
                'title': 'C',
                'link': 'http://example.com/C',
                'description': 'Describe C',
                'pubDate': datetime.datetime.fromisoformat('2022-01-02T10:11:23+03:00')
            },
        ]
        rlist = [
            {
                'title': 'A',
                'link': 'http://example.com/A',
                'description': 'Describe A',
                'pubDate': datetime.datetime.fromisoformat('2022-03-01T10:11:23+03:00')
            },
            {
                'title': 'B',
                'link': 'http://example.com/B',
                'description': 'Describe B',
                'pubDate': datetime.datetime.fromisoformat('2022-02-02T10:11:23+03:00')
            },
            {
                'title': 'C',
                'link': 'http://example.com/C',
                'description': 'Describe C',
                'pubDate': datetime.datetime.fromisoformat('2022-01-02T10:11:23+03:00')
            },
        ]
        self.assertEqual(rss_reader.merge_items(alist, blist), rlist)

    def test_update_cache(self):
        cache = {
            'http://example.com/feedA': {
                'title': 'feed A',
                'description': 'Describe A',
                'link': 'http://example.com/feedA',
                'items': []
            }
        }
        feed = {
            'title': 'feed B',
            'description': 'Describe B',
            'link': 'http://example.com/feedB',
            'items': []
        }
        new_cache = {
            'http://example.com/feedA': {
                'title': 'feed A',
                'description': 'Describe A',
                'link': 'http://example.com/feedA',
                'items': []
            },
            'http://example.com/feedB': {
                'title': 'feed B',
                'description': 'Describe B',
                'link': 'http://example.com/feedB',
                'items': []
            }
        }
        rss_reader.update_cache(cache, 'http://example.com/feedB', feed)
        self.assertEqual(cache, new_cache)

    def test_lookup_cache(self):
        cache = {
            'http://example.com/feedA': {
                'title': 'feed A',
                'description': 'Describe A',
                'link': 'http://example.com/feedA',
                'items': []
            },
            'http://example.com/feedB': {
                'title': 'feed B',
                'description': 'Describe B',
                'link': 'http://example.com/feedB',
                'items': []
            }
        }
        self.assertEqual(
            rss_reader.lookup_cache(
                cache, 'http://example.com/feedA',
                datetime.datetime.fromisoformat('2022-06-01T01:00+03:00')),
            {
                'title': 'feed A',
                'description': 'Describe A',
                'link': 'http://example.com/feedA',
                'items': []
            }
        )


class TestFormatters(unittest.TestCase):

    def test_get_cached_image(self):
        feed = {
            'title': 'Feed A',
            'description': 'Describe A',
            'link': 'http://example.com/feedA',
            'items': [
                {
                    'title': 'A01',
                    'link': 'http://example.com/feedA',
                    'description': 'Describe A01',
                    'pubDate': datetime.datetime.fromisoformat('2022-01-02T10:11:23+03:00'),
                    'links': [('http://example.com/feedA', 'link'), ('http://example.com/image01.png', 'image')],
                    'images': {'http://example.com/image01.png': b'IMAGEDATA'}
                }
            ]
        }
        formatter = rss_reader.Formatters(feed)
        self.assertEqual(formatter._get_cached_image('http://example.com/image01.png').getvalue(), b'IMAGEDATA')
    
    def test_to_html(self):
        feed = {
            'title': 'Feed A',
            'description': 'Describe A',
            'link': 'http://example.com/feedA',
            'items': [
                {
                    'title': 'A01',
                    'link': 'http://example.com/feedA',
                    'description': 'Describe A01',
                    'description_raw': 'Describe A01',
                    'pubDate': datetime.datetime.fromisoformat('2022-01-02T10:11:23+03:00'),
                    'links': [('http://example.com/feedA', 'link'), ('http://example.com/image01.png', 'image')],
                    'images': {'http://example.com/image01.png': b'IMAGEDATA'}
                }
            ]
        }
        formatter = rss_reader.Formatters(feed)
        self.assertEqual(formatter.to_html,
                         b'<!DOCTYPE html>\n<html><head><meta charset="utf-8"/><title>Feed A</title></head>'
                         b'<body><h1>Feed A</h1><div>Describe A</div><h2>A01</h2><p>Sun, 02 Jan 2022 10:11:23 +0300</p>'
                         b'<div>Describe A01</div><ol><li><a href="http://example.com/feedA">link</a></li>'
                         b'<li><img height="100" src="http://example.com/image01.png" width="160"/></li></ol>'
                         b'</body></html>')