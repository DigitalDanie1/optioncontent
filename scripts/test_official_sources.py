import unittest
from datetime import date
from official_sources import parse_rss,parse_hypercall,parse_fomc
class SourceTests(unittest.TestCase):
 def test_feed_rejects_stale_future_and_other_hosts(self):
  def item(title,when,url):return f'<item><title>{title}</title><pubDate>{when}</pubDate><link>{url}</link></item>'
  feed='<rss><channel>'+item('Options','Fri, 06 Nov 2026 10:00:00 GMT','https://insights.derive.xyz/new/')+item('Stale','Thu, 01 Oct 2026 10:00:00 GMT','https://insights.derive.xyz/old/')+item('Future','Fri, 13 Nov 2026 10:00:00 GMT','https://insights.derive.xyz/future/')+item('Other','Fri, 06 Nov 2026 10:00:00 GMT','https://elsewhere.example/new/')+'</channel></rss>'
  self.assertEqual([x['title'] for x in parse_rss(feed,'Derive',date(2026,11,9),'https://insights.derive.xyz/rss/')],['Options'])
 def test_blog_rejects_undated_and_old_links(self):
  raw='<a href="/new/"><time>NOV 06, 2026</time><h2>Options vaults</h2></a><a href="/old/">OCT 01, 2026 Old options</a><a href="/none/">No date</a>'
  self.assertEqual([x['url'] for x in parse_hypercall(raw,date(2026,11,9))],['https://blog.hypercall.xyz/new/'])
 def test_fed_uses_correct_year_and_horizon(self):
  raw='<div class="panel"><h4>2026 FOMC Meetings</h4><div class="fomc-meeting"><div class="fomc-meeting__month">December</div><div class="fomc-meeting__date">8-9*</div></div></div>'
  self.assertEqual(parse_fomc(raw,date(2026,11,9)),[])
  self.assertEqual(parse_fomc(raw,date(2026,12,7))[0]['endDate'],'2026-12-09')
if __name__=='__main__':unittest.main()
