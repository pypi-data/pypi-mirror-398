import datetime
import json
import logging
import os
import random
import time
from copy import copy
from functools import wraps
from itertools import product
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from typing import Any

import requests
from pixivpy3 import PixivError
from pixivpy3.aapi import AppPixivAPI  # type: ignore
from pixivpy3.utils import JsonDict  # type: ignore
from zhconv_rs import zhconv

from pixiv_down import utils as ut

# 关闭无关紧要的日志
for name, logger in logging.Logger.manager.loggerDict.items():
    if name.startswith('urllib3') and isinstance(logger, logging.Logger):
        logger.setLevel(logging.ERROR)


class User(JsonDict):
    pass


class Illust(JsonDict):
    """重写 __lt__ 方法，使 Illust key 进行排序"""

    id: int
    title: str
    caption: str
    create_date: str
    width: int
    height: int
    page_count: int
    total_bookmarks: int
    total_comments: int
    total_view: int
    restrict: int
    sanity_level: int
    x_restrict: int
    tags: list[dict]
    user: JsonDict

    illust_ai_type: int
    illust_book_style: int

    meta_single_page: dict
    image_urls: dict
    meta_pages: dict
    is_bookmarked: bool
    is_muted: bool
    series: Any
    tools: list
    type: str
    visible: bool

    def __lt__(self, other: 'Illust'):
        if self.total_bookmarks == other.total_bookmarks:
            return self.quality < other.quality
        else:
            return self.total_bookmarks < other.total_bookmarks

    @property
    def x_level(self) -> int:
        """敏感等级: 0, 2, 4, 6, 7"""
        return self.sanity_level + self.x_restrict

    @property
    def quality(self) -> int | float:
        """质量"""
        if not self.visible:
            return -1
        elif not self.total_view:
            return 0
        else:
            return round(self.total_bookmarks / self.total_view * 100, 2)

    def rtags(self) -> set[str]:
        """可读性更好的 tags"""
        return {self.readable_tag(t) for t in self.tags}

    @staticmethod
    def readable_tag(tag: dict) -> str:
        """可读性更好的 tag"""
        name, trans = tag['name'], tag['translated_name']

        if not trans:
            wd = name
        else:
            n_lang = ut.get_lang(name)
            t_lang = ut.get_lang(trans)

            if n_lang == 'jp':
                wd = trans
            elif t_lang == 'en':
                wd = name
            else:
                wd = trans
        return zhconv(wd, 'zh-Hans')


class IllustFilter:
    def __init__(
        self,
        max_count: int = 10,
        min_bookmarks: int = 1000,
        min_quality: float | None = None,
        is_ai: bool | None = None,
        max_x_level: int = 2,
        since: str | None = None,
        before: str | None = None,
        min_iid: int | None = None,
        tags_include: str | None = None,
        tags_exclude: str | None = None,
        skip_aids: str | None = None,
        skip_iids: str | None = None,
    ):
        self.max_count = max_count
        self.min_bookmarks = min_bookmarks
        self.min_quality = min_quality
        self.is_ai = is_ai
        self.max_x_level = max_x_level
        self.since = since
        self.before = before
        self.min_iid = min_iid
        self.tags_include = self.split_tags(tags_include)
        self.tags_exclude = self.split_tags(tags_exclude)
        self.skip_aids = self.split_ids(skip_aids)
        self.skip_iids = self.split_ids(skip_iids)

        self._date_sensitive = False  # 日期敏感，用于连续爬取时根据日期中断

    def copy(self):
        return copy(self)

    @staticmethod
    def split_ids(ids: str | None) -> set:
        if ids:
            if os.path.isfile(ids):
                with open(ids) as fp:
                    return {int(line) for line in fp if line.strip().isdecimal()}
            else:
                return {int(iid) for iid in ids.replace('，', ',').split(',') if iid.strip().isdecimal()}
        else:
            return set()

    @staticmethod
    def split_tags(tags: str | None) -> set:
        if tags:
            if os.path.isfile(tags):
                with open(tags) as fp:
                    return {tag.strip() for tag in fp if tag.strip()}
            else:
                return {tag.strip() for tag in tags.replace('，', ',').split(',') if tag.strip()}
        else:
            return set()

    def is_qualified(self, illust: Illust) -> bool:  # noqa: C901
        """检查质量是否合格"""
        # 硬指标：类型为 illust，且可访问
        if illust.type != 'illust':
            logging.debug(f'skip Illust({illust.id}): {illust.type=}')
            return False
        if not illust.visible:
            logging.debug(f'skip Illust({illust.id}): {illust.visible=}')
            return False

        if illust.page_count > self.max_count:
            logging.debug(f'skip Illust({illust.id}): {illust.page_count=}')
            return False
        if illust.total_bookmarks < self.min_bookmarks:
            logging.debug(f'skip Illust({illust.id}): {illust.total_bookmarks=}')
            return False
        if self.min_quality and illust.quality < self.min_quality:
            logging.debug(f'skip Illust({illust.id}): {illust.quality=}')
            return False
        # 检查 AI 属性
        if self.is_ai is False and illust.illust_ai_type == 2:
            logging.debug(f'skip Illust({illust.id}): {illust.illust_ai_type=}')
            return False
        elif self.is_ai is True and illust.illust_ai_type != 2:
            logging.debug(f'skip Illust({illust.id}): {illust.illust_ai_type=}')
            return False

        # 检查 max_x_level 范围
        if self.max_x_level < illust.x_level:
            logging.debug(f'skip Illust({illust.id}): {illust.x_level=}')
            return False

        # 检查时间属性
        if (
            (self.since and self.since > illust.create_date)
            or (self.before and self.before < illust.create_date)
            or (self.min_iid and self.min_iid > illust.id)
        ):
            if self._date_sensitive:
                raise TimeoutError
            else:
                return False

        # 检查要保护和要忽略的 Tag
        tags = illust.rtags()
        if self.tags_include:
            for include, tag in product(self.tags_include, tags):
                if include in tag:
                    break
            else:
                logging.debug(f'skip Illust({illust.id}): {tags=}')
                return False

        if self.tags_exclude:
            for exclude, tag in product(self.tags_exclude, tags):
                if exclude in tag:
                    logging.debug(f'skip Illust({illust.id}): {tags=}')
                    return False

        # 检查是否是需要跳过的 ID
        if illust.user.id in self.skip_aids or illust.id in self.skip_iids:
            logging.debug(f'skip Illust({illust.id}): skip aid or iid')
            return False

        return True


class NeedRetry(Exception):  # noqa: N818
    pass


class OffsetLimit(Exception):  # noqa: N818
    pass


default_filter = IllustFilter()


@ut.singleton
class Crawler:
    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        refresh_token: str | None = None,
        download_dir: str | None = None,
        ifilter: IllustFilter = default_filter,
    ):
        self.username = username
        self.password = password
        self.refresh_token = refresh_token
        self.base_dir = Path(download_dir or '').absolute()
        self.make_download_dirs()
        self.ifilter = ifilter

        self.api = AppPixivAPI()
        self.api.set_accept_language('zh-cn')
        self.decorate_apis_with_retry()

    @property
    def user(self) -> User:
        if not hasattr(self, '_user'):
            result = self.login()
            self._user = User(result['user'])
        return self._user

    @user.setter
    def user(self, user: User):
        self._user = user

    def make_download_dirs(self):
        dir_tree = {
            'json': ['illust', 'artist', 'ranking'],
            'img': ['square', 'medium', 'large', 'origin', 'avatar'],
        }
        self.base_dir.mkdir(0o755, parents=True, exist_ok=True)
        for key, values in dir_tree.items():
            lv1_dir = self.base_dir.joinpath(key)
            lv1_dir.mkdir(0o755, parents=True, exist_ok=True)
            for value in values:
                # 创建子目录
                lv2_dir = lv1_dir.joinpath(value)
                lv2_dir.mkdir(0o755, parents=True, exist_ok=True)

                # NOTE: 动态增加下载目录的属性，如: `dir_json_illust`
                setattr(self, f'dir_{key}_{value}', lv2_dir)

    def check_result(self, result):
        if 'error' in result:
            msg = result.error.message or result.error.user_message or ''
            if 'Rate Limit' in msg:
                # 访问太频繁被限制时
                raise NeedRetry('request rate limit')

            elif 'Please check your Access Token' in msg:
                # Access Token 失效，重新登录
                self.login()
                raise NeedRetry('access token expired, relogin')

            elif 'Offset must be no more than' in msg:
                logging.warning(msg)

            elif msg:
                logging.error(msg)

            else:
                logging.error(f'ApiError: {result.error}')  # 未知错误打印到日志

    def decorate_apis_with_retry(self):
        """给api接口增加自动重试装饰器"""
        wrapper = ut.retry(checker=self.check_result, exceptions=(NeedRetry, PixivError, json.JSONDecodeError))

        self.api.auth = wrapper(self.api.auth)
        self.api.illust_detail = wrapper(self.api.illust_detail)
        self.api.illust_ranking = wrapper(self.api.illust_ranking)
        self.api.illust_recommended = wrapper(self.api.illust_recommended)
        self.api.illust_related = wrapper(self.api.illust_related)
        self.api.login = wrapper(self.api.login)
        self.api.search_illust = wrapper(self.api.search_illust)
        self.api.user_bookmarks_illust = wrapper(self.api.user_bookmarks_illust)
        self.api.user_detail = wrapper(self.api.user_detail)
        self.api.user_illusts = wrapper(self.api.user_illusts)

    def login(self):
        """登录 Pixiv 账号
        Return: {
            "access_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "expires_in": 3600,
            "refresh_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "scope": "",
            "token_type": "bearer",
            "user": {
                "account": "xxxxxxxxx",
                "id": "xxxxxxxxx",
                "is_mail_authorized": true,
                "is_premium": false,
                "mail_address": "xxxxxx@xxx.com",
                "name": "FengPo",
                "profile_image_urls": {
                    "px_16x16": "https://i.pximg.net/.../xxx.png",
                    "px_170x170": "https://i.pximg.net/.../xxx.png",
                    "px_50x50": "https://i.pximg.net/.../xxx.png"
                },
                "x_restrict": 1
            }
        }
        """
        if self.refresh_token:
            logging.info('login by refresh_token')
            result = self.api.auth(refresh_token=self.refresh_token)
        else:
            logging.info('login by password')
            result = self.api.login(self.username, self.password)

        self.user = User(result['user'])

        logging.debug(f'access_token="{self.api.access_token}" refresh_token="{self.api.refresh_token}"')
        return result

    def fetch_illust(self, iid: int, keep_json=False):
        """获取 illust 数据
        Return: {
            "caption": "ジャケット＋メイド服を考えた人は天才。",
            "create_date": "2020-09-22T10:13:06+09:00",
            "height": 1250,
            "id": 84533965,
            "image_urls": {
                "square_medium": "https://i.pximg.net/.../84533965_p0_square1200.jpg"
                "medium": "https://i.pximg.net/.../84533965_p0_master1200.jpg",
                "large": "https://i.pximg.net/.../84533965_p0_master1200.jpg",
            },
            "is_bookmarked": false,
            "is_muted": false,

            // 仅多图时，此字段有值
            "meta_pages": [
                {
                    "image_urls": {
                        "square_medium": "https://i.pximg.net/.../86571617_p0_square1200.jpg"
                        "medium": "https://i.pximg.net/.../86571617_p0_master1200.jpg",
                        "large": "https://i.pximg.net/.../86571617_p0_master1200.jpg",
                        "original": "https://i.pximg.net/.../86571617_p0.jpg",
                    }
                },
                ...
            ],

            // 仅单图时，此字段有值
            "meta_single_page": {
                "original_image_url": "https://i.pximg.net/.../84533965_p0.jpg"
            },

            "page_count": 1,
            "restrict": 0,
            "sanity_level": 2,
            "series": null,
            "tags": [
                {
                    "name": "女の子",
                    "translated_name": "girl"
                },
                ...
            ],
            "title": "さぼりメイド",
            "tools": [],
            "total_bookmarks": 5133,
            "total_comments": 13,
            "total_view": 25590,
            "type": "illust",
            "user": {
                "account": "watoson117",
                "id": 887024,
                "is_followed": true,
                "name": "Puracotte＊ぷらこ",
                "profile_image_urls": {
                    "medium": "https://i.pximg.net/user-profile/img/2020/09/28/09/06/13/19428811_dcb45b4..._170.jpg"
                }
            },
            "visible": true,
            "width": 1000,
            "x_restrict": 0
        }
        """
        jsonfile: Path = self.dir_json_illust.joinpath(f'{iid}.json')  # type: ignore
        if jsonfile.exists():
            with jsonfile.open() as fp:
                return Illust(json.load(fp)), False
        else:
            result = self.api.illust_detail(iid)
            if 'illust' not in result:
                logging.error(f'not found: {iid=}')
                return None, False
            elif not result['illust']['visible']:
                logging.debug(json.dumps(result['illust'], sort_keys=True, indent=4))
                logging.error(f'not visible: {iid=}')
                return None, False
            else:
                illust = Illust(result['illust'])
                if keep_json:
                    ut.save_jsonfile(illust, filename=jsonfile.as_posix())
                return illust, True

    def ifetch(self, pixiv_api, keep_json=False):
        """NOTE: 特别注意，此函数并非普通装饰器，需手动调用"""

        @wraps(pixiv_api)
        def api_caller(**kwargs):  # 仅接受 kwargs 形式的参数
            il = None
            while True:
                result = pixiv_api(**kwargs)
                if not result or not result.illusts:
                    break

                for il in result.illusts:
                    il = Illust(il)

                    try:
                        if self.ifilter.is_qualified(il):
                            logging.debug(
                                f'fetched Illust({il.id}) created={il.create_date[:10]} bookmark={il.total_bookmarks}'
                            )
                            if keep_json:
                                jsonfile = self.dir_json_illust.joinpath(f'{il.id}.json')
                                ut.save_jsonfile(il, jsonfile.as_posix())
                            yield il
                    except TimeoutError:
                        result.next_url = None
                        break

                if result.next_url:
                    kwargs = self.api.parse_qs(next_url=result.next_url)  # 构造下一步参数
                    time.sleep(random.random() + random.randint(1, 3))
                    s_kwargs = ut.params_to_str(kwargs=kwargs)
                    logging.debug(f'request next page: {pixiv_api.__name__}({s_kwargs})')
                    continue
                else:
                    break

            # return the last one
            if il:
                return il  # noqa: B901
            else:
                s_kwargs = ut.params_to_str(kwargs=kwargs)
                logging.warning(f'no illust found: {pixiv_api.__name__}({s_kwargs})')

        return api_caller

    def download_illust(self, illust: dict, square=True, medium=False, large=False, origin=False):  # noqa: C901
        """下载 illust 图片"""
        if illust['page_count'] == 1:
            urls = illust['image_urls']
            if square:
                self.api.download(urls['square_medium'], path=self.dir_img_square)  # type: ignore
            if medium:
                self.api.download(urls['medium'], path=self.dir_img_medium)  # type: ignore
            if large:
                self.api.download(urls['large'], path=self.dir_img_large)  # type: ignore
            if origin:
                url = illust['meta_single_page']['original_image_url']
                self.api.download(url, path=self.dir_img_origin)  # type: ignore
        else:
            for item in illust['meta_pages']:
                urls = item['image_urls']
                if square:
                    self.api.download(urls['square_medium'], path=self.dir_img_square)  # type: ignore
                if medium:
                    self.api.download(urls['medium'], path=self.dir_img_medium)  # type: ignore
                if large:
                    self.api.download(urls['large'], path=self.dir_img_large)  # type: ignore
                if origin:
                    self.api.download(urls['original'], path=self.dir_img_origin)  # type: ignore

    def multi_download(self, illusts: list, square=False, medium=False, large=False, origin=True, n_thread=1):
        """下载多个 illusts"""
        total = len(illusts)
        if n_thread == 1:
            for num, illust in enumerate(illusts, start=1):
                logging.info(f'downloading progress: {num} / {total}')
                self.download_illust(illust, square, medium, large, origin)
        else:
            # 定义并填充任务队列
            task_q: Queue[Illust] = Queue()
            task_q.queue.extend(illusts)

            def download_from_queue():
                while True:
                    try:
                        illust = task_q.get(block=False)
                    except Empty:
                        return
                    # 打印进度
                    remain = len(task_q.queue)
                    logging.info(f'downloading {illust["id"]}\tremain {remain} / {total}')
                    # 下载
                    try:
                        self.download_illust(illust, square, medium, large, origin)
                    except Exception:
                        logging.info(f'download {illust["id"]} faild, retry later')
                        task_q.put(illust)  # 下载失败，还将 illust 返回队列

            # 定义并启动线程
            threads = [Thread(target=download_from_queue) for _ in range(n_thread)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

    def fetch_artist(self, aid, keep_json=False):
        """获取用户数据
        Return {
            "profile": {
                "address_id": 13,
                "background_image_url": "https://i.pximg.net/.../xxx.jpg",
                "birth": "",
                "birth_day": "07-20",
                "birth_year": 0,
                "country_code": "",
                "gender": "female",
                "is_premium": false,
                "is_using_custom_profile_image": true,
                "job": "技术关联",
                "job_id": 3,
                "pawoo_url": null,
                "region": "日本 東京都",
                "total_follow_users": 377,
                "total_illust_bookmarks_public": 1509,
                "total_illust_series": 0,
                "total_illusts": 186,
                "total_manga": 6,
                "total_mypixiv_users": 47,
                "total_novel_series": 0,
                "total_novels": 0,
                "twitter_account": "puracotte117",
                "twitter_url": "https://twitter.com/puracotte117",
                "webpage": null
            },
            "profile_publicity": {
                "birth_day": "public",
                "birth_year": "public",
                "gender": "public",
                "job": "public",
                "pawoo": true,
                "region": "public"
            },
            "user": {
                "account": "watoson117",
                "comment": "ぷらこと申します。\r\n時々イラストレーターをやっている会社員です。",
                "id": 887024,
                "is_followed": true,
                "name": "Puracotte＊ぷらこ",
                "profile_image_urls": {
                    "medium": "https://i.pximg.net/user-profile/.../xxx.jpg"
                }
            },
            "workspace": {
                "chair": "",
                "comment": "",
                "desk": "",
                "desktop": "",
                "monitor": "",
                "mouse": "",
                "music": "",
                "pc": "",
                "printer": "",
                "scanner": "",
                "tablet": "",
                "tool": "",
                "workspace_image_url": null
            }
        }
        """
        jsonfile = self.dir_json_artist.joinpath(f'{aid}.json')
        if jsonfile.exists():
            with jsonfile.open() as fp:
                artist = JsonDict(json.load(fp))
        else:
            artist = self.api.user_detail(aid)
            if artist and 'user' in artist:
                if keep_json:
                    ut.save_jsonfile(artist, filename=jsonfile.as_posix())
            else:
                raise ValueError(f"can't download {aid}: {artist}")

        return artist

    def download_artist(self, aid, avatar=True):
        artist = self.fetch_artist(aid, keep_json=True)
        if avatar:
            self.api.download(artist['user']['profile_image_urls']['medium'], path=self.dir_img_avatar)

    def fetch_web_ranking(self, date: datetime.date, keep_json=False):
        """从 Web 下载排行榜数据
        Return [
            {
                "attr": "original",
                "date": "2015年12月31日 00:09",
                "height": 810,
                "illust_book_style": "1",
                "illust_content_type": {
                    "antisocial": false,
                    "bl": false,
                    "drug": false,
                    "furry": false,
                    "grotesque": false,
                    "homosexual": false,
                    "lo": false,
                    "original": true,
                    "religion": false,
                    "sexual": 0,
                    "thoughts": false,
                    "violent": false,
                    "yuri": false
                },
                "illust_id": 54339949,
                "illust_page_count": "1",
                "illust_series": false,
                "illust_type": "0",
                "illust_upload_timestamp": 1451489068,
                "profile_img": "https://i.pximg.net/user-profile/img/2008/03/31/01/13/19/95581_886b0c6ea..._50.jpg",
                "rank": 1,
                "rating_count": 1689,
                "tags": [
                    "オリジナル",
                    "天使",
                    "空",
                    "透明感",
                    "ふつくしい",
                    "銀髪碧眼",
                    "女の子",
                    "銀髪",
                    "オリジナル50000users入り",
                    "横乳"
                ],
                "title": "70億人のゆめをみる",
                "url": "https://i.pximg.net/c/240x480/img-master/img/2015/12/31/00/24/28/5433..._p0_master1200.jpg",
                "user_id": 27517,
                "user_name": "藤ちょこ（藤原）",
                "view_count": 115439,
                "width": 572,
                "yes_rank": 2
            },
            ...
        ]
        """
        jsonfile: Path = self.dir_json_ranking.joinpath(f'{date:%Y%m%d}.json')  # type: ignore
        if jsonfile.exists():
            with jsonfile.open() as fp:
                ranking = json.load(fp)
        else:
            ranking = []
            base_url = 'https://www.pixiv.net/ranking.php'
            url_tmpl = f'{base_url}?mode=daily&content=illust&date={date:%Y%m%d}&p=%s&format=json'
            headers = {'Referer': base_url}

            next_page = 1
            while next_page:
                url = url_tmpl % next_page
                resp = requests.get(url, headers=headers, stream=True, timeout=60)
                if resp.status_code != 200:
                    if 'error' in resp.text:
                        logging.error(resp.json()['error'])
                    else:
                        logging.error(resp.text)
                    break
                result = resp.json()
                ranking.extend(result['contents'])
                next_page = result.get('next')

            if keep_json:
                ut.save_jsonfile(ranking, jsonfile.as_posix())

        return ranking

    def ifetch_ranking(self, date, only_new=True, keep_json=True):
        web_ranking = self.fetch_web_ranking(date, keep_json)
        for il in web_ranking:
            # 检查是否只下载当天的数据
            if only_new and int(il['yes_rank']) != 0:
                continue

            # 获取 Illust 详细数据
            illust, _ = self.fetch_illust(il['illust_id'], False)
            if illust and self.ifilter.is_qualified(illust):
                # 检查是否需要保存 json
                if keep_json:
                    jsonfile = self.dir_json_illust.joinpath(f'{illust.id}.json')
                    ut.save_jsonfile(illust, jsonfile.as_posix())

                logging.debug(
                    f'fetched Illust({illust.id}) created={illust.create_date[:10]} bookmark={illust.total_bookmarks}'
                )
                yield illust
            time.sleep(random.random() + random.randint(1, 3))

    def ifetch_artist_artwork(self, aid, keep_json=False):
        """迭代获取 artist 的 Illust"""
        user_illusts_api = self.ifetch(self.api.user_illusts, keep_json)
        return user_illusts_api(user_id=aid)

    def ifetch_tag(self, word, keep_json=False):
        """迭代获取 Tag 的 Illust"""
        search_illust_api = self.ifetch(self.api.search_illust, keep_json)

        if self.user.is_premium:
            yield from search_illust_api(word=word, sort='popular_desc')
        elif self.ifilter.since and self.ifilter.before:
            self.ifilter._date_sensitive = True
            yield from search_illust_api(
                word=word,
                sort='date_desc',
                start_date=self.ifilter.since,
                end_date=self.ifilter.before,
            )
        else:
            raise ValueError('user is not premium, and both start and end are None')

    def ifetch_follow(self, restrict='public', keep_json=False):
        """迭代获取关注作者的最新作品

        restrict: public / private
        """
        self.ifilter._date_sensitive = True
        illust_follow_api = self.ifetch(self.api.illust_follow, keep_json)
        return illust_follow_api(restrict=restrict)

    def ifetch_recommend(self, keep_json):
        """迭代获取推荐的 Illust"""
        illust_recommended_api = self.ifetch(self.api.illust_recommended, keep_json)
        return illust_recommended_api()

    def ifetch_related(self, iid, keep_json):
        """迭代获取某作品关联的 Illust"""
        illust_related_api = self.ifetch(self.api.illust_related, keep_json)
        return illust_related_api(illust_id=iid)
