import time
import logging
import comicking_openapi
import jikan_openapi
from datetime import datetime
from typing import Iterable
from urllib.parse import quote, urlparse

from .bot import Bot

class BotJikan:
    website_myanimelist_host = 'myanimelist.net'
    website_myanimelist_cdn_host = 'cdn.myanimelist.net'

    def __init__(
        self,
        bot: Bot,
        logger: logging.Logger
    ):
        self.bot = bot
        self.client = jikan_openapi.ApiClient()

        self.logger = logger

    def load(self, seeding: bool = True):
        if seeding:
            self.bot.authenticate()

        #
        # Website
        #

        api0 = comicking_openapi.WebsiteApi(self.bot.client)

        websites = {
            self.website_myanimelist_host: 'MyAnimeList',
            self.website_myanimelist_cdn_host: 'MyAnimeList CDN'
        }
        for k, v in websites.items():
            if k in self.bot.websites:
                continue

            try:
                api0.get_website(k)

                self.bot.websites.append(k)
            except comicking_openapi.ApiException as e:
                if seeding and e.status == 404:
                    self.bot.add_website(k, v)

                    time.sleep(2)
                else:
                    raise e

    def note(self, __lines: Iterable[str] | None = None):
        if __lines:
            self.logger.info(__lines)
            if self.bot.note_file: self.bot.note_file.writelines(__lines)

        if self.bot.note_file: self.bot.note_file.writelines("\n")

    def process(self, max_new_comic: int | None = None):
        self.note('#')
        self.note('# Started time %s' % time.ctime())
        self.note('#')
        self.note()

        self.load(True)

        self.scrap_comics_complete(max_new_comic)

        self.note()
        self.note('# Stopped time %s' % time.ctime())
        self.note()

    def __manga_complete(self, manga: jikan_openapi.Manga):
        comic_code, comic_exist = None, False

        if not manga.mal_id:
            return comic_code, comic_exist

        api0 = comicking_openapi.ComicApi(self.bot.client)

        response0 = api0.list_comic(
            external_link_href=[quote(f'{self.website_myanimelist_host}/manga/{manga.mal_id}')]
        )

        self.bot.authenticate()

        # Comic

        comic_published_from, comic_published_to = None, None

        if manga.published:
            manga_published = manga.published

            if manga_published.var_from:
                comic_published_from = datetime.fromisoformat(manga_published.var_from)

            if manga_published.to:
                comic_published_to = datetime.fromisoformat(manga_published.to)

        api1 = comicking_openapi.LinkApi(self.bot.client)

        if len(response0) < 1:
            response0Z = self.bot.add_comic(
                published_from=comic_published_from,
                published_to=comic_published_to,
                total_chapter=manga.chapters,
                total_volume=manga.volumes
            )

            # Comic External (MyAnimeList)

            comic_link = quote(f'{self.website_myanimelist_host}/manga/{manga.mal_id}')

            try:
                api1.get_link(comic_link)
            except comicking_openapi.ApiException as e:
                if e.status == 404:
                    self.bot.add_link(self.website_myanimelist_host, f'/manga/{manga.mal_id}')

                    time.sleep(2)
                else:
                    raise e

            self.bot.add_comic_external(
                response0Z.code,
                self.website_myanimelist_host,
                f'/manga/{manga.mal_id}',
                is_community=True
            )

            comic_code = response0Z.code
        else:
            if len(response0) > 1:
                self.note('Detected multiple comic with same MyAnimeList ID %s' % manga.mal_id)

            comic_code, comic_exist = response0[0].code, True

        comic_type = None

        if manga.type:
            comic_type = manga.type.lower().replace(' ', '-')

        # Comic Category (Comic Type)

        if not comic_exist and comic_type:
            if f'{self.bot.categorytype_comictype_code}:{comic_type}' in self.bot.categories:
                self.bot.add_comic_category(
                    comic_code,
                    self.bot.categorytype_comictype_code,
                    comic_type
                )
            else:
                self.note('Manga Type "%s" is skipped' % manga.type)

        # Comic Title

        if not comic_exist and manga.titles:
            if comic_type and comic_type in [
                self.bot.category_comictype_manhua_code,
                self.bot.category_comictype_manhwa_code
            ]:
                has_correct_title_language = False
                for title in manga.titles:
                    match comic_type:
                        case self.bot.category_comictype_manhua_code:
                            if title.type == 'Chinese':
                                has_correct_title_language = True
                        case self.bot.category_comictype_manhwa_code:
                            if title.type == 'Korean':
                                has_correct_title_language = True
                        case _:
                            pass

                if not has_correct_title_language:
                    for title in manga.titles:
                        if title.type == 'Japanese':
                            match comic_type:
                                case self.bot.category_comictype_manhua_code:
                                    title.type = 'Chinese'
                                case self.bot.category_comictype_manhwa_code:
                                    title.type = 'Korean'
                                case _:
                                    pass

                            self.note('Manga Title "%s" fix type to "%s"' % (title.title, title.type))

            for title in manga.titles:
                if not title.title:
                    continue

                languageLang = None
                match title.type:
                    case 'English':
                        languageLang = self.bot.language_english_lang
                    case 'Japanese':
                        languageLang = self.bot.language_japanese_lang
                    case 'Korean':
                        languageLang = self.bot.language_korean_lang
                    case 'Chinese':
                        languageLang = self.bot.language_chinese_lang
                    case _:
                        pass

                if languageLang not in self.bot.languages:
                    self.note('Manga Title "%s" Type "%s" is skipped' % (title.title, title.type))
                    continue

                self.bot.add_comic_title(
                    comic_code,
                    languageLang,
                    title.title
                )

                time.sleep(2)

        api2 = comicking_openapi.WebsiteApi(self.bot.client)
        api3 = comicking_openapi.ImageApi(self.bot.client)

        # Comic Cover

        if manga.images:
            if manga.images.jpg and manga.images.jpg.image_url:
                image = urlparse(manga.images.jpg.image_url)

                try:
                    api1.get_link(f'{self.website_myanimelist_cdn_host}{image.path}')
                except comicking_openapi.ApiException as e:
                    if e.status == 404:
                        self.bot.add_link(self.website_myanimelist_cdn_host, image.path)
                    else:
                        raise e

                response1Y = api3.list_image(
                    link_href=[quote(f'{self.website_myanimelist_cdn_host}{image.path}')]
                )
                if len(response1Y) > 0:
                    try:
                        api0.get_comic_cover(comic_code, response1Y[0].ulid)
                    except comicking_openapi.ApiException as e:
                        if e.status == 404:
                            self.bot.add_comic_cover(
                                comic_code,
                                response1Y[0].ulid
                            )
                        else:
                            raise e
                else:
                    response1Z = self.bot.add_image(
                        self.website_myanimelist_cdn_host,
                        image.path
                    )

                    self.bot.add_comic_cover(
                        comic_code,
                        response1Z.ulid
                    )


        # Comic Synopsis

        if not comic_exist and manga.synopsis:
            self.bot.add_comic_synopsis(
                comic_code,
                self.bot.language_english_lang,
                manga.synopsis,
                source='MyAnimeList'
            )

        # Comic Author

        """ api3 = comicking_openapi.PersonApi(self.client)

        if not comic_exist and manga.authors:
            for author in manga.authors:
                pass """

        # Comic Serialization

        """ if not comic_exist and manga.serializations:
            for serialization in manga.serializations:
                pass """

        # Comic Tag (Comic Status)

        if not comic_exist and manga.status:
            manga_status = manga.status

            match manga_status:
                case 'Discontinued':
                    manga_status = 'Cancelled'
                case 'Not yet published':
                    manga_status = 'Announced'
                case 'On Hiatus':
                    manga_status = 'Hiatus'
                case 'Publishing':
                    manga_status = 'Ongoing'
                case _:
                    pass

            comic_status = manga_status.lower().replace(' ', '-')

            if f'{self.bot.tagtype_comicstatus_code}:{comic_status}' in self.bot.tags:
                self.bot.add_comic_tag(
                    comic_code,
                    self.bot.tagtype_comicstatus_code,
                    comic_status
                )
            else:
                self.note('Manga Status "%s" is skipped' % manga_status)

        # Comic Category (Genre) / Tag (Comic)

        if not comic_exist and manga.genres:
            comic_tags = ('Award Winning')

            for genre in manga.genres:
                if not genre.name:
                    continue

                comic_tag_or_genre = genre.name.lower().replace(' ', '-')

                if genre.name in comic_tags:
                    if f'{self.bot.tagtype_comic_code}:{comic_tag_or_genre}' not in self.bot.tags:
                        self.bot.add_comic_tag(
                            comic_code,
                            self.bot.tagtype_comic_code,
                            comic_tag_or_genre
                        )
                    else:
                        self.note('Manga Genre "%s" is skipped' % genre.name)

                    continue

                if f'{self.bot.categorytype_genre_code}:{comic_tag_or_genre}' not in self.bot.categories:
                    self.note('Manga Genre "%s" is skipped' % genre.name)

                    continue

                self.bot.add_comic_category(
                    comic_code,
                    self.bot.categorytype_genre_code,
                    comic_tag_or_genre
                )

                time.sleep(2)

        if not comic_exist and manga.explicit_genres:
            for explicit_genre in manga.explicit_genres:
                if not explicit_genre.name:
                    continue

                comic_genre = explicit_genre.name.lower().replace(' ', '-')

                if f'{self.bot.categorytype_genre_code}:{comic_genre}' not in self.bot.categories:
                    self.note('Manga Explicit Genre "%s" is skipped' % explicit_genre.name)

                    continue

                self.bot.add_comic_category(
                    comic_code,
                    self.bot.categorytype_genre_code,
                    comic_genre
                )

                time.sleep(2)

        if not comic_exist and manga.themes:
            for theme in manga.themes:
                if not theme.name:
                    continue

                manga_theme_name = theme.name

                match manga_theme_name:
                    case 'Anthropomorphic':
                        manga_theme_name = 'Anthropomorphism'
                    case 'CGDCT':
                        manga_theme_name = 'Cute Girls Doing Cute Things'
                    case 'Crossdressing':
                        manga_theme_name = 'Cross-dressing'
                    case 'Idols (Female)':
                        manga_theme_name = 'Female Idol'
                    case 'Idols (Male)':
                        manga_theme_name = 'Male Idol'
                    case 'Super Power':
                        manga_theme_name = 'Superpower'
                    case _:
                        pass

                comic_genre = manga_theme_name.lower().replace(' ', '-')

                if f'{self.bot.categorytype_genre_code}:{comic_genre}' not in self.bot.categories:
                    self.note('Manga Theme "%s" is skipped' % manga_theme_name)

                    continue

                self.bot.add_comic_category(
                    comic_code,
                    self.bot.categorytype_genre_code,
                    comic_genre
                )

                time.sleep(2)

        if not comic_exist and manga.demographics:
            for demographic in manga.demographics:
                if not demographic.name:
                    continue

                comic_genre = demographic.name.lower().replace(' ', '-')

                if f'{self.bot.categorytype_genre_code}:{comic_genre}' not in self.bot.categories:
                    self.note('Manga Demographic "%s" is skipped' % demographic.name)

                    continue

                self.bot.add_comic_category(
                    comic_code,
                    self.bot.categorytype_genre_code,
                    comic_genre
                )

                time.sleep(2)

        api4 = jikan_openapi.MangaApi(self.client)

        # Comic External

        if not comic_exist:
            response2 = api4.get_manga_external(manga.mal_id)
            if response2.data:
                for external in response2.data:
                    url = urlparse(external.url)

                    if url.port:
                        self.note('Manga External "%s" skipped' % external.url)
                        continue

                    website_host = url.hostname
                    if not website_host:
                        continue

                    website_host = str(website_host)

                    if website_host.endswith('wikipedia.org'):
                        if website_host != 'en.wikipedia.org':
                            self.note('Manga External non-english Wikipedia "%s" skipped' % external.url)

                            continue

                        website_host = 'wikipedia.org'

                    if website_host not in self.bot.websites:
                        try:
                            api2.get_website(website_host)

                            self.bot.websites.append(website_host)
                        except comicking_openapi.ApiException as e:
                            if e.status == 404:
                                website_name = external.name

                                if not website_name or website_name == 'Official Site':
                                    website_name = website_host

                                self.bot.add_website(website_host, website_name)
                            else:
                                raise e

                        self.bot.websites.append(website_host)

                    relativeReference = str(url.path)

                    if url.query:
                        relativeReference += "?" + str(url.query)

                    try:
                        api1.get_link(f'{website_host}{relativeReference}')
                    except comicking_openapi.ApiException as e:
                        if e.status == 404:
                            self.bot.add_link(
                                website_host,
                                relativeReference if relativeReference else None
                            )
                        else:
                            raise e

                    self.bot.add_comic_external(
                        comic_code,
                        website_host,
                        relativeReference if relativeReference else None,
                        is_official=True if external.name == 'Official Site' else None
                    )

                    time.sleep(2)

        # Comic Character

        """ if not comic_exist:
            response3 = api4.get_manga_characters(manga.mal_id)
            if response3.data:
                for character in response3.data:
                    pass """

        # Comic Relation

        if not comic_exist:
            response4 = api4.get_manga_relations(manga.mal_id)
            if response4.data:
                manga_relations = response4.data.copy()

                for relation in response4.data:
                    if not relation.entry or not relation.relation:
                        continue

                    manga_relation_type_code = relation.relation.lower().replace(" ", "-")

                    if manga_relation_type_code not in self.bot.comicrelationtypes:
                        self.note('Manga Relation "%s" is skipped' % manga_relation_type_code)

                        continue

                    for mangaY in relation.entry:
                        if not mangaY.mal_id:
                            continue

                        response4Y = api4.get_manga_relations(mangaY.mal_id)
                        if response4Y.data:
                            manga_relations += response4Y.data

                        time.sleep(2)

                for relation in manga_relations:
                    if not relation.relation or not relation.entry:
                        continue

                    for mangaZ in relation.entry:
                        if not mangaZ.mal_id:
                            continue

                        manga_relation_type_code = relation.relation.lower().replace(" ", "-")

                        if manga_relation_type_code not in self.bot.comicrelationtypes:
                            self.note('Manga Relation "%s" is skipped' % manga_relation_type_code)

                            continue

                        response4Z = api0.list_comic(
                            external_link_href=[
                                quote(f'{self.website_myanimelist_host}/manga/{mangaZ.mal_id}')
                            ]
                        )
                        if len(response4Z) < 1:
                            continue

                        try:
                            api0.get_comic_relation(
                                comic_code,
                                manga_relation_type_code,
                                response4Z[0].code
                            )
                        except comicking_openapi.ApiException as e:
                            if e.status == 404:
                                self.bot.add_comic_relation(
                                    comic_code,
                                    manga_relation_type_code,
                                    response4Z[0].code
                                )
                            else:
                                raise e

                        time.sleep(2)

        return comic_code, comic_exist

    def scrap_comics_complete(
        self,
        max_new_comic: int | None = None
    ):
        api = jikan_openapi.MangaApi(self.client)

        comics_code: list[str] = []
        total_new_comic = 0

        page = 1
        while True:
            if max_new_comic and total_new_comic > max_new_comic - 1:
                break

            response = api.get_manga_search(
                page=page,
                order_by=jikan_openapi.MangaSearchQueryOrderby.POPULARITY,
                sort=jikan_openapi.SearchQuerySort.DESC
            )
            if not response.data:
                break

            for manga in response.data:
                if max_new_comic and total_new_comic > max_new_comic - 1:
                    break

                if not manga.mal_id:
                    continue

                if manga.type:
                    if self.bot.categorytype_comictype_code in self.bot.categorytypes:
                        comic_category_code = self.bot.categorytype_comictype_code
                        comic_category_code += ':' + manga.type.lower().replace(' ', '-')

                        if comic_category_code not in self.bot.categories:
                            continue
                    else:
                        if manga.type in ['Novel', 'Light Novel']:
                            continue
                else:
                    continue

                self.note()
                self.note('Check Jikan (MyAnimeList) manga ID %s' % manga.mal_id)

                comic_code, comic_exist = self.__manga_complete(manga)

                if comic_code:
                    comics_code.append(comic_code)

                self.note("Jikan (MyAnimeList) manga ID %s check complete" % manga.mal_id)
                self.note()

                if comic_code and not comic_exist:
                    total_new_comic += 1
                    time.sleep(5)

            page += 1
            time.sleep(3)

        return comics_code

    def get_or_add_comic_complete(
        self,
        id: int
    ):
        api = jikan_openapi.MangaApi(self.client)

        manga = None

        try:
            response = api.get_manga_by_id(id)

            if not response.data:
                return None

            manga = response.data
        except jikan_openapi.ApiException as e:
            if e.status == 404:
                return None
            else:
                raise e

        if not manga.mal_id:
            return None

        if manga.type:
            if self.bot.categorytype_comictype_code in self.bot.categorytypes:
                comic_category_code = self.bot.categorytype_comictype_code
                comic_category_code += ':' + manga.type.lower().replace(' ', '-')

                if comic_category_code not in self.bot.categories:
                    return None
            else:
                if manga.type in ['Novel', 'Light Novel']:
                    return None
        else:
            return None

        self.note('Check Jikan (MyAnimeList) manga ID %s' % manga.mal_id)

        comic_code = self.__manga_complete(manga)[0]

        self.note("Jikan (MyAnimeList) manga ID %s check complete" % manga.mal_id)

        return comic_code
