import time
import requests
import logging
import comicking_openapi
from datetime import datetime
from io import TextIOWrapper
from typing import Iterable

class Bot:
    language_english_lang = 'en'
    language_japanese_lang = 'ja'
    language_korean_lang = 'ko'
    language_chinese_lang = 'zh'

    categorytype_comictype_code = 'comic-type'
    category_comictype_manhua_code = 'manhua'
    category_comictype_manhwa_code = 'manhwa'
    categorytype_genre_code = 'genre'

    tagtype_comic_code = 'comic'
    tagtype_comicstatus_code = 'comic-status'

    def __init__(
        self,
        base_comicking: str,
        oauth_issuer: str,
        oauth_client_id: str,
        oauth_client_secret: str,
        oauth_audience: str,
        logger: logging.Logger,
        note_file: TextIOWrapper | None = None
    ):
        self.client = comicking_openapi.ApiClient(configuration=comicking_openapi.Configuration(host=base_comicking))

        self.oauth_issuer = oauth_issuer
        self.oauth_client_id = oauth_client_id
        self.oauth_client_secret = oauth_client_secret
        self.oauth_audience = oauth_audience
        self.oauth_token_expires = time.time()

        self.languages: list[str] = []
        self.websites: list[str] = []
        self.categorytypes: list[str] = []
        self.categories: list[str] = []
        self.tagtypes: list[str] = []
        self.tags: list[str] = []
        self.comicrelationtypes: list[str] = []

        self.logger = logger
        self.note_file = note_file

    def load(self, seeding: bool = True):
        if seeding:
            self.authenticate()

        #
        # Language
        #

        api0 = comicking_openapi.LanguageApi(self.client)

        language_page = 1
        while True:
            response = api0.list_language_with_http_info(page=language_page, limit=15)

            if not response.data:
                break

            for language in response.data:
                self.languages.append(language.lang)

            language_total_count = 0

            if response.headers:
                for k, v in response.headers.items():
                    if k.lower() == 'x-total-count':
                        language_total_count = int(v)
                        break

            if len(self.languages) >= language_total_count:
                break

            time.sleep(1)
            language_page += 1

        if seeding:
            languages = {
                self.language_english_lang: 'English',
                self.language_japanese_lang: 'Japanese',
                self.language_korean_lang: 'Korean',
                self.language_chinese_lang: 'Chinese'
            }
            for k, v in languages.items():
                if k in self.languages:
                    continue

                result = self.add_language(k, v)
                if not result:
                    continue

                time.sleep(2)

        #
        # Category
        #

        api1 = comicking_openapi.CategoryApi(self.client)

        categorytype_page = 1
        while True:
            response = api1.list_category_type_with_http_info(page=categorytype_page, limit=15)

            if not response.data:
                break

            for categorytype in response.data:
                self.categorytypes.append(categorytype.code)

            categorytype_total_count = 0

            if response.headers:
                for k, v in response.headers.items():
                    if k.lower() == 'x-total-count':
                        categorytype_total_count = int(v)
                        break

            if len(self.categorytypes) >= categorytype_total_count:
                break

            time.sleep(1)
            categorytype_page += 1

        if seeding:
            categorytypes = {
                self.categorytype_comictype_code: 'Comic Type',
                self.categorytype_genre_code: 'Genre'
            }
            for k, v in categorytypes.items():
                if k in self.categorytypes:
                    continue

                result = self.add_categorytype(k, v)
                if not result:
                    continue

                time.sleep(2)

        # = = = = =

        category_page = 1
        while True:
            response = api1.list_category_with_http_info(page=category_page, limit=15)

            if not response.data:
                break

            for category in response.data:
                self.categories.append(f'{category.type_code}:{category.code}')

            category_total_count = 0

            if response.headers:
                for k, v in response.headers.items():
                    if k.lower() == 'x-total-count':
                        category_total_count = int(v)
                        break

            if len(self.categories) >= category_total_count:
                break

            time.sleep(1)
            category_page += 1

        if seeding and self.categorytype_comictype_code in self.categorytypes:
            category_comictypes = {
                'manga': 'Manga',
                'one-shot': 'One-shot',
                'doujinshi': 'Doujinshi',
                self.category_comictype_manhua_code: 'Manhua',
                self.category_comictype_manhwa_code: 'Manhwa'
            }
            for k, v in category_comictypes.items():
                if f'{self.categorytype_comictype_code}:{k}' in self.categories:
                    continue

                result = self.add_category(self.categorytype_comictype_code, k, v)
                if not result:
                    continue

                time.sleep(2)

        if seeding and self.categorytype_genre_code in self.categorytypes:
            category_genres = {
                'action': 'Action',
                'adventure': 'Adventure',
                'avant-garde': 'Avant-garde',
                'boys-love': 'Boys Love',
                'comedy': 'Comedy',
                'drama': 'Drama',
                'fantasy': 'Fantasy',
                'girls-love': 'Girls Love',
                'gourmet': 'Gourmet',
                'horror': 'Horror',
                'mystery': 'Mystery',
                'romance': 'Romance',
                'sci-fi': 'Sci-Fi',
                'slice-of-life': 'Slice of Life',
                'sports': 'Sports',
                'supernatural': 'Supernatural',
                'suspense': 'Suspense',

                'ecchi': 'Ecchi',
                'erotica': 'Erotica',
                'hentai': 'Hentai',

                'adult-cast': 'Adult Cast',
                'anthropomorphism': 'Anthropomorphism',
                'cute-girls-doing-cute-things': 'Cute Girls Doing Cute Things',
                'childcare': 'Childcare',
                'combat-sports': 'Combat Sports',
                'cross-dressing': 'Cross-dressing',
                'delinquents': 'Delinquents',
                'detective': 'Detective',
                'educational': 'Educational',
                'female-idol': 'Female Idol',
                'gag-humor': 'Gag Humor',
                'gore': 'Gore',
                'harem': 'Harem',
                'high-stakes-game': 'High Stakes Game',
                'historical': 'Historical',
                'isekai': 'Isekai',
                'iyashikei': 'Iyashikei',
                'love-polygon': 'Love Polygon',
                'magical-sex-shift': 'Magical Sex Shift',
                'mahou-shoujo': 'Mahou Shoujo',
                'male-idol': 'Male Idol',
                'martial-arts': 'Martial Arts',
                'mecha': 'Mecha',
                'medical': 'Medical',
                'memoir': 'Memoir',
                'military': 'Military',
                'music': 'Music',
                'mythology': 'Mythology',
                'organized-crime': 'Organized Crime',
                'otaku-culture': 'Otaku Culture',
                'parody': 'Parody',
                'performing-arts': 'Performing Arts',
                'pets': 'Pets',
                'psychological': 'Psychological',
                'racing': 'Racing',
                'reincarnation': 'Reincarnation',
                'reverse-harem': 'Reverse Harem',
                'romantic-subtext': 'Romantic Subtext',
                'samurai': 'Samurai',
                'school': 'School',
                'showbiz': 'Showbiz',
                'space': 'Space',
                'strategy-game': 'Strategy Game',
                'superpower': 'Superpower',
                'survival': 'Survival',
                'team-sports': 'Team Sports',
                'time-travel': 'Time Travel',
                'vampire': 'Vampire',
                'video-game': 'Video Game',
                'villainess': 'Villainess',
                'visual-arts': 'Visual Arts',
                'workplace': 'Workplace',

                'josei': 'Josei',
                'kids': 'Kids',
                'seinen': 'Seinen',
                'shoujo': 'Shoujo',
                'shounen': 'Shounen'
            }
            for k, v in category_genres.items():
                if f'{self.categorytype_genre_code}:{k}' in self.categories:
                    continue

                result = self.add_category(self.categorytype_genre_code, k, v)
                if not result:
                    continue

                time.sleep(2)

        #
        # Tag
        #

        api2 = comicking_openapi.TagApi(self.client)

        tagtype_page = 1
        while True:
            response = api2.list_tag_type_with_http_info(page=tagtype_page, limit=15)

            if not response.data:
                break

            for tagtype in response.data:
                self.tagtypes.append(tagtype.code)

            tagtype_total_count = 0

            if response.headers:
                for k, v in response.headers.items():
                    if k.lower() == 'x-total-count':
                        tagtype_total_count = int(v)
                        break

            if len(self.categorytypes) >= tagtype_total_count:
                break

            time.sleep(1)
            tagtype_page += 1

        if seeding:
            tagtypes = {
                self.tagtype_comic_code: 'Comic',
                self.tagtype_comicstatus_code: 'Comic Status'
            }
            for k, v in tagtypes.items():
                if k in self.tagtypes:
                    continue

                result = self.add_tagtype(k, v)
                if not result:
                    continue

                time.sleep(2)

        tag_page = 1
        while True:
            response = api2.list_tag_with_http_info(page=tag_page, limit=15)

            if not response.data:
                break

            for tag in response.data:
                self.tags.append(f'{tag.type_code}:{tag.code}')

            tag_total_count = 0

            if response.headers:
                for k, v in response.headers.items():
                    if k.lower() == 'x-total-count':
                        tag_total_count = int(v)
                        break

            if len(self.tags) >= tag_total_count:
                break

            time.sleep(1)
            tag_page += 1

        if seeding and self.tagtype_comic_code in self.tagtypes:
            tag_comics = {
                'award-winning': 'Award Winning'
            }
            for k, v in tag_comics.items():
                if f'{self.tagtype_comic_code}:{k}' in self.tags:
                    continue

                result = self.add_tag(self.tagtype_comic_code, k, v)
                if not result:
                    continue

                time.sleep(2)

        if seeding and self.tagtype_comicstatus_code in self.tagtypes:
            tag_comicstatuses = {
                'announced': 'Announced',
                'ongoing': 'Ongoing',
                'finished': 'Finished',
                'hiatus': 'Hiatus',
                'cancelled': 'Cancelled'
            }
            for k, v in tag_comicstatuses.items():
                if f'{self.tagtype_comicstatus_code}:{k}' in self.tags:
                    continue

                result = self.add_tag(self.tagtype_comicstatus_code, k, v)
                if not result:
                    continue

                time.sleep(2)

        #
        # Comic
        #

        api3 = comicking_openapi.ComicApi(self.client)

        comicrelationtype_page = 1
        while True:
            response = api3.list_comic_relation_type_with_http_info(page=comicrelationtype_page, limit=15)

            if not response.data:
                break

            for comicrelationtype in response.data:
                self.comicrelationtypes.append(comicrelationtype.code)

            comicrelationtype_total_count = 0

            if response.headers:
                for k, v in response.headers.items():
                    if k.lower() == 'x-total-count':
                        comicrelationtype_total_count = int(v)
                        break

            if len(self.comicrelationtypes) >= comicrelationtype_total_count:
                break

            time.sleep(1)
            comicrelationtype_page += 1

        if seeding:
            comicrelationtypes = {
                'alternative-setting': 'Alternative Setting',
                'alternative-version': 'Alternative Version',
                'character': 'Character',
                'full-story': 'Full Story',
                'other': 'Other',
                'parent-story': 'Parent Story',
                'prequel': 'Prequel',
                'sequel': 'Sequel',
                'side-story': 'Side Story',
                'spin-off': 'Spin-off',
                'summary': 'Summary'
            }
            for k, v in comicrelationtypes.items():
                if k in self.comicrelationtypes:
                    continue

                result = self.add_comicrelationtype(k, v)
                if not result:
                    continue

                time.sleep(2)

    def authenticate(self):
        if self.oauth_token_expires > time.time() + 300:
            return

        response = requests.post(
            f'{self.oauth_issuer}oauth/token',
            data={
                'grant_type': 'client_credentials',
                'client_id': self.oauth_client_id,
                'client_secret': self.oauth_client_secret,
                'audience': self.oauth_audience
            }
        )

        if not response.ok:
            raise RuntimeError('Bot authentication failed')

        token = response.json()

        config = self.client.configuration
        config.access_token = token['access_token']
        self.oauth_token_expires = time.time() + float(token['expires_in'])

        self.logger.info('ComicKing Bot authenticated')

    def note(self, __lines: Iterable[str] | None = None):
        if __lines:
            self.logger.info(__lines)
            if self.note_file: self.note_file.writelines(__lines)

        if self.note_file: self.note_file.writelines("\n")

    def add_language(
        self,
        lang: str,
        name: str
    ):
        api = comicking_openapi.LanguageApi(self.client)

        result = api.add_language(
            new_language=comicking_openapi.NewLanguage(
                lang=lang,
                name=name
            )
        )

        if lang not in self.languages:
            self.languages.append(lang)

        self.logger.info('Language "%s" added', lang)

        return result

    def add_website(
        self,
        host: str,
        name: str
    ):
        api = comicking_openapi.WebsiteApi(self.client)

        result = api.add_website(
            new_website=comicking_openapi.NewWebsite(
                host=host,
                name=name
            )
        )

        if host not in self.websites:
            self.websites.append(host)

        self.logger.info('Website "%s" added', host)

        return result

    def add_link(
        self,
        website_host: str,
        relative_reference: str | None = None
    ):
        api = comicking_openapi.LinkApi(self.client)

        result = api.add_link(
            new_link=comicking_openapi.NewLink(
                websiteHost=website_host,
                relativeReference=relative_reference
            )
        )

        self.logger.info('Link "%s" added', f'{website_host}{relative_reference}')

        return result

    def add_categorytype(
        self,
        code: str,
        name: str
    ):
        api = comicking_openapi.CategoryApi(self.client)

        result = api.add_category_type(
            new_generic_type=comicking_openapi.NewGenericType(
                code=code,
                name=name
            )
        )

        if code not in self.categorytypes:
            self.categorytypes.append(code)

        self.logger.info('Category Type "%s" added', code)

        return result

    def add_category(
        self,
        type_code: str,
        code: str,
        name: str
    ):
        api = comicking_openapi.CategoryApi(self.client)

        result = api.add_category(
            new_category=comicking_openapi.NewCategory(
                typeCode=type_code,
                code=code,
                name=name
            )
        )

        if f'{type_code}:{code}' not in self.categories:
            self.categories.append(f'{type_code}:{code}')

        self.logger.info('Category %s:%s added', type_code, code)

        return result

    def add_tagtype(
        self,
        code: str,
        name: str
    ):
        api = comicking_openapi.TagApi(self.client)

        result = api.add_tag_type(
            new_generic_type=comicking_openapi.NewGenericType(
                code=code,
                name=name
            )
        )

        if code not in self.tagtypes:
            self.tagtypes.append(code)

        self.logger.info('Tag Type "%s" added', code)

        return result

    def add_tag(
        self,
        type_code: str,
        code: str,
        name: str
    ):
        api = comicking_openapi.TagApi(self.client)

        result = api.add_tag(
            new_tag=comicking_openapi.NewTag(
                typeCode=type_code,
                code=code,
                name=name
            )
        )

        if f'{type_code}:{code}' not in self.tags:
            self.tags.append(f'{type_code}:{code}')

        self.logger.info('Tag %s:%s added', type_code, code)

        return result

    def add_comic(
        self,
        code: str | None = None,
        published_from: datetime | None = None,
        published_to: datetime | None = None,
        total_chapter: int | None = None,
        total_volume: int | None = None,
        nsfw: int | None = None,
        nsfl: int | None = None
    ):
        api = comicking_openapi.ComicApi(self.client)

        result = api.add_comic(
            new_comic=comicking_openapi.NewComic(
                code=code,
                publishedFrom=published_from,
                publishedTo=published_to,
                totalChapter=total_chapter,
                totalVolume=total_volume,
                nsfw=nsfw,
                nsfl=nsfl
            )
        )

        self.logger.info('Comic "%s" added', result.code)

        return result

    def add_comic_title(
        self,
        comic_code: str,
        language_lang: str,
        content: str,
        is_synonym: bool | None = None,
        is_latinized: bool | None = None
    ):
        api = comicking_openapi.ComicApi(self.client)

        result = api.add_comic_title(
            comic_code,
            new_comic_title=comicking_openapi.NewComicTitle(
                languageLang=language_lang,
                content=content,
                isSynonym=is_synonym,
                isLatinized=is_latinized
            )
        )

        self.logger.info(
            'Comic "%s" Title "%s" added',
            comic_code, content[:61] + '...'
        )

        return result

    def add_comic_cover(
        self,
        comic_code: str,
        link_website_host: str,
        link_relative_reference: str | None = None,
        hint: str | None = None
    ):
        api = comicking_openapi.ComicApi(self.client)

        result = api.add_comic_cover(
            comic_code,
            new_comic_cover=comicking_openapi.NewComicCover(
                linkWebsiteHost=link_website_host,
                linkRelativeReference=link_relative_reference,
                hint=hint
            )
        )

        self.logger.info(
            'Comic "%s" Cover "%s" added',
            comic_code, f'{link_website_host}{link_relative_reference}'
        )

        return result

    def add_comic_synopsis(
        self,
        comic_code: str,
        language_lang: str,
        content: str,
        version: str | None = None
    ):
        api = comicking_openapi.ComicApi(self.client)

        result = api.add_comic_synopsis(
            comic_code,
            new_comic_synopsis=comicking_openapi.NewComicSynopsis(
                languageLang=language_lang,
                content=content,
                version=version
            )
        )

        self.logger.info(
            'Comic "%s" Synopsis "%s" added',
            comic_code, content.replace('\r', '').replace('\n', ' ')[:61] + '...'
        )

        return result

    def add_comic_external(
        self,
        comic_code: str,
        link_website_host: str,
        link_relative_reference: str | None = None,
        is_official: bool | None = None,
        is_community: bool | None = None
    ):
        api = comicking_openapi.ComicApi(self.client)

        result = api.add_comic_external(
            comic_code,
            new_comic_external=comicking_openapi.NewComicExternal(
                linkWebsiteHost=link_website_host,
                linkRelativeReference=link_relative_reference,
                isOfficial=is_official,
                isCommunity=is_community
            )
        )

        self.logger.info(
            'Comic "%s" External "%s" added',
            comic_code, f'{link_website_host}{link_relative_reference}'
        )

        return result

    def add_comic_category(
        self,
        comic_code: str,
        type_code: str,
        code: str
    ):
        api = comicking_openapi.ComicApi(self.client)

        result = api.add_comic_category(
            comic_code,
            new_comic_category=comicking_openapi.NewComicCategory(
                categoryTypeCode=type_code,
                categoryCode=code
            )
        )

        self.logger.info(
            'Comic "%s" Category "%s" added',
            comic_code, f'{type_code}:{code}'
        )

        return result

    def add_comic_tag(
        self,
        comic_code: str,
        type_code: str,
        code: str
    ):
        api = comicking_openapi.ComicApi(self.client)

        result = api.add_comic_tag(
            comic_code,
            new_comic_tag=comicking_openapi.NewComicTag(
                tagTypeCode=type_code,
                tagCode=code
            )
        )

        self.logger.info(
            'Comic "%s" Tag "%s" added',
            comic_code, f'{type_code}:{code}'
        )

        return result

    def add_comicrelationtype(
        self,
        code: str,
        name: str
    ):
        api = comicking_openapi.ComicApi(self.client)

        result = api.add_comic_relation_type(
            new_generic_type=comicking_openapi.NewGenericType(
                code=code,
                name=name
            )
        )

        if code not in self.comicrelationtypes:
            self.comicrelationtypes.append(code)

        self.logger.info('Comic Relation Type "%s" added', code)

        return result

    def add_comic_relation(
        self,
        comic_code: str,
        type_code: str,
        child_code: str
    ):
        api = comicking_openapi.ComicApi(self.client)

        result = api.add_comic_relation(
            comic_code,
            new_comic_relation=comicking_openapi.NewComicRelation(
                typeCode=type_code,
                childCode=child_code
            )
        )

        self.logger.info(
            'Comic "%s" Relation "%s:%s" added',
            comic_code, type_code, child_code
        )

        return result
