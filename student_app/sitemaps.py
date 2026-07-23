from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'daily'

    def items(self):
        return [
            'home', 
            'help_center', 
            'privacy_policy', 
            'terms_of_service', 
            'leaderboard'
        ]

    def location(self, item):
        return reverse(item)
