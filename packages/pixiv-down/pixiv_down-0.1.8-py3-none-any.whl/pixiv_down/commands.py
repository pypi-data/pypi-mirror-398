#!/usr/bin/env python

import datetime
import heapq
import logging
import os
import signal
import sys
import time
from argparse import ArgumentParser
from collections.abc import Generator
from getpass import getpass
from queue import Queue
from random import random
from threading import Thread

from pixiv_down import utils
from pixiv_down.crawler import Crawler, IllustFilter

# parse args
parser = ArgumentParser()

_download_types = [
    'artist',
    'iid',  # download illusts by illust id list
    'aid',  # download illusts by artist id list
    'tag',  # download illusts by tag name
    'rcmd',  # download illusts from recomments
    'follow',  # download illusts from follows
    'related',  # download related illusts of the specified illust
    'ranking',  # download daily ranking of the specified day
    'url',  # download image directly from URL
]

# bookmars and page count
parser.add_argument(
    '-b', dest='min_bookmarks', default=1000, type=int, help='The min bookmarks of illust (default: %(default)s)'
)
parser.add_argument(
    '-c', dest='max_page_count', default=10, type=int, help='The max page count of illust (default: %(default)s)'
)
parser.add_argument(
    '-q',
    dest='min_quality',
    type=int,
    help=('The min quality of illust, the quality eauals the num of bookmarks per 100 views (default: %(default)s)'),
)
parser.add_argument(
    '-a',
    dest='avatar',
    action='store_true',
    help='Download avatar of the specified artist',
)
parser.add_argument(
    '-A',
    dest='is_ai',
    default=None,
    type=lambda x: str(x).lower() in ['true', 'yes', 't', 'y'],
    help='Filter ai illusts, choices: y / n (default: ignore)',
)
parser.add_argument(
    '-v',
    dest='max_x_level',
    choices=[0, 2, 4, 6, 7],
    default=6,
    type=int,
    help='The max sex level of illust (default: %(default)s)',
)
parser.add_argument('-t', dest='tags_include', type=str, help='The tags to include in illusts')
parser.add_argument('-T', dest='tags_exclude', type=str, help='Exclude illusts with the specified tags')
parser.add_argument(
    '-n', dest='illust_num', default=500, type=int, help='Total number of illusts to download (default: %(default)s)'
)

# download options
parser.add_argument('-k', dest='keep_json', action='store_true', help='Keep the json result to files')
parser.add_argument(
    '-p',
    dest='path',
    type=str,
    default=os.getenv('PIXIV_DOWN', './pixdown'),
    help='The storage path of illusts (default: "%(default)s")',
)
parser.add_argument(
    '-r',
    dest='resolution',
    type=str,
    default='o',
    help=('The resolution of illusts: s / m / l / o (i.e., square / middle / large / origin, can set multiple)'),
)
parser.add_argument('-i', dest='interval', type=int, default=37, help='The interval of downloading')
parser.add_argument('--threads', dest='n_thread', type=int, default=16, help='The number of download threads')
parser.add_argument('-j', '--show-json', dest='show_json', type=str, help='Print the json result on stdout')

# date interval
parser.add_argument('-S', '--since', dest='since', type=str, help='The start date of illust for searching')
parser.add_argument('-B', '--before', dest='before', type=str, help='The end date of illust for searching')
parser.add_argument('--min_iid', dest='min_iid', type=int, help='The min iid of last update from follows')

# only download the newest illusts on ranking
parser.add_argument('--only_new', action='store_true', help='Only download the newest illusts from ranking')

# ignore options
parser.add_argument('-I', '--without_image', action='store_true', help="Don't download illusts")
parser.add_argument('--skip_aids', dest='skip_aids', type=str, help='Ignore artist ids, separated by `,`')
parser.add_argument('--skip_iids', dest='skip_iids', type=str, help='Ignore illust ids, separated by `,`')

# log level
parser.add_argument(
    '--log',
    dest='loglevel',
    type=str,
    default='info',
    choices=['debug', 'info', 'warn', 'error'],
    help='The log level (default: `%(default)s`)',
)

parser.add_argument(dest='download_type', choices=_download_types, help='The download types')

parser.add_argument(
    dest='args',
    nargs='*',
    help=('The positional args for download type, e.g., `artist ids`, `illust ids`, `artist ids`, `tag names`'),
)

args = parser.parse_args()


###############################################################################
#                               init the spider                               #
###############################################################################

# set logger
logging.basicConfig(format='[%(levelname)s] %(funcName)s: %(message)s')
loglevel = getattr(logging, args.loglevel.upper())
logging.root.setLevel(loglevel)

# parse illust resolution
if args.without_image:
    RESOLUTIONS = {'square': False, 'medium': False, 'large': False, 'origin': False}
else:
    _img_types = {'s': 'square', 'm': 'medium', 'l': 'large', 'o': 'origin'}
    RESOLUTIONS = {v: True if k in args.resolution else False for k, v in _img_types.items()}

# get the refresh_token
REFRESH_TOKEN = os.environ.get('PIXIV_TOKEN') or getpass('Please enter the refresh_token:')

# check the download path
if os.path.exists(args.path) and not os.path.isdir(args.path):
    print(f'`{args.path}` is not a directory.')
    sys.exit(1)
else:
    DOWNLOAD_DIR = args.path

# parse show_json option
if not args.show_json:
    JSON_FIELDS = []
else:
    JSON_FIELDS = args.show_json.split(',')


# login
ifilter = IllustFilter(
    max_count=args.max_page_count,
    min_bookmarks=args.min_bookmarks,
    min_quality=args.min_quality,
    is_ai=args.is_ai,
    max_x_level=args.max_x_level,
    since=args.since,
    before=args.before,
    min_iid=args.min_iid,
    tags_include=args.tags_include,
    tags_exclude=args.tags_exclude,
    skip_aids=args.skip_aids,
    skip_iids=args.skip_iids,
)
crawler = Crawler(refresh_token=REFRESH_TOKEN, download_dir=DOWNLOAD_DIR, ifilter=ifilter)
user = crawler.login()


################################################################################
#                                  downladers                                  #
################################################################################


def iter_args() -> Generator[tuple[int, str], None, None]:
    """遍历参数表，如果有文件则逐行读取"""
    num = 1
    for item in set(args.args):
        if os.path.isfile(item):
            with open(item) as fp:
                for line in fp:
                    yield num, line.strip()
                    num += 1
        else:
            yield num, item
            num += 1


def download_artist():
    if not args.args:
        logging.error('not specified the artist id list')
    else:
        for total, aid in iter_args():
            try:
                aid = int(aid)
                crawler.download_artist(aid, args.avatar)
                print(f'Fetched artist {aid:<10d}  {total=}')

                rdm = random()
                time.sleep(rdm / 2 if args.avatar else (rdm + 0.5))

            except (TypeError, ValueError) as e:
                print(f'Error with aid {aid}: {e}')
                continue


def download_illusts_by_aid():
    if not args.args:
        logging.error('not specified the illust id list')
    else:
        illusts = []
        for _, aid in iter_args():
            try:
                aid = int(aid)
            except (TypeError, ValueError):
                print(f'wrong artist id: {aid}')
                continue

            fetcher = crawler.ifetch_artist_artwork(aid, args.keep_json)
            for total, illust in enumerate(fetcher, start=1):
                illusts.append(illust)

                bk = illust.total_bookmarks / 1000
                print(f'iid={illust.id}  bookmark={bk:.1f}k  q={illust.quality}  {total=}')

                if JSON_FIELDS:
                    utils.print_json(illust, keys=JSON_FIELDS)
                    print('-' * 50, end='\n\n')

                if total >= args.illust_num:
                    break

        crawler.multi_download(illusts, n_thread=args.n_thread, **RESOLUTIONS)


def download_illusts_by_tag():
    if not args.args:
        logging.error('not specified the tag name')
    else:
        for _, tag in iter_args():
            print(f'scraping tag: {tag}')
            illusts = []
            fetcher = crawler.ifetch_tag(tag, False)
            for total, illust in enumerate(fetcher, start=1):
                if crawler.user.is_premium:
                    # 用户时会员时，按 popular_desc 排序，直接存放即可
                    if total <= args.illust_num:
                        illusts.append(illust)
                    else:
                        break
                else:
                    if len(illusts) < args.illust_num:
                        heapq.heappush(illusts, illust)
                    else:
                        heapq.heappushpop(illusts, illust)

                bk = illust.total_bookmarks / 1000
                print(f'iid={illust.id}  bookmark={bk:4.1f}k  {total=}')

            for illust in illusts:
                if JSON_FIELDS:
                    utils.print_json(illust, keys=JSON_FIELDS)
                    print('-' * 50, end='\n\n')

                if args.keep_json:
                    jsonfile = crawler.dir_json_illust.joinpath(f'{illust.id}.json')
                    utils.save_jsonfile(illust, jsonfile.as_posix())

            crawler.multi_download(illusts, n_thread=args.n_thread, **RESOLUTIONS)


def download_illusts_from_recommend():
    illusts = []
    fetcher = crawler.ifetch_recommend(args.keep_json)
    for total, illust in enumerate(fetcher, start=1):
        illusts.append(illust)

        bk = illust.total_bookmarks / 1000
        print(f'iid={illust.id}  bookmark={bk:.1f}k  q={illust.quality}  {total=}')

        if JSON_FIELDS:
            utils.print_json(illust, keys=JSON_FIELDS)
            print('-' * 50, end='\n\n')

        if total >= args.illust_num:
            break

    crawler.multi_download(illusts, n_thread=args.n_thread, **RESOLUTIONS)


def download_illusts_from_follows():
    illusts = []
    total = 0
    for illust in crawler.ifetch_follow(keep_json=args.keep_json):
        illusts.append(illust)

        # 打印进度
        total += 1
        bk = illust.total_bookmarks / 1000
        print(f'iid={illust.id}  bookmark={bk:.1f}k  q={illust.quality}  {total=}')

    crawler.multi_download(illusts, n_thread=args.n_thread, **RESOLUTIONS)


def download_illusts_by_related():
    if not args.args:
        logging.error('not specified the related illust id')
    else:
        for _, iid in iter_args():
            illusts = []
            try:
                iid = int(iid)
            except (TypeError, ValueError):
                print(f'wrong illust id: {iid}')
                continue

            fetcher = crawler.ifetch_related(iid, args.keep_json)
            for total, illust in enumerate(fetcher, start=1):
                illusts.append(illust)

                bk = illust.total_bookmarks / 1000
                print(f'iid={illust.id}  bookmark={bk:.1f}k  q={illust.quality}  {total=}')

                if JSON_FIELDS:
                    utils.print_json(illust, keys=JSON_FIELDS)
                    print('-' * 50, end='\n\n')

                if total >= args.illust_num:
                    break

            crawler.multi_download(illusts, n_thread=args.n_thread, **RESOLUTIONS)


def download_illusts_by_id():
    if not args.args:
        logging.error('not specified the illust id list')
    else:
        illusts = []
        new_fetched = 0
        for total, iid in iter_args():
            try:
                iid = int(iid)
                illust, is_new = crawler.fetch_illust(iid, args.keep_json)
            except (TypeError, ValueError) as e:
                print(e)
                continue
            else:
                if illust:
                    illusts.append(illust)
                    # 打印进度
                    bk = illust.total_bookmarks / 1000
                    print(f'{iid=}  bookmark={bk:.1f}k  q={illust.quality}  {total=}')
                    # 打印JSON字段
                    if JSON_FIELDS:
                        utils.print_json(illust, keys=JSON_FIELDS)
                        print('-' * 50, end='\n\n')
                new_fetched += int(is_new)
            if new_fetched != 0 and new_fetched % 30 == 0:
                time.sleep(args.interval)

        crawler.multi_download(illusts, n_thread=args.n_thread, **RESOLUTIONS)


def iget_days():
    for date in args.args:
        if ',' in date:
            start, end = date.split(',')
            try:
                start = datetime.date.fromisoformat(start)
                end = datetime.date.fromisoformat(end)
            except ValueError:
                continue

            while start <= end:
                yield start
                start += datetime.timedelta(1)
        else:
            try:
                yield datetime.date.fromisoformat(date)
            except ValueError:
                pass


def download_illust_from_ranking():
    for date in iget_days():
        if args.without_image:
            crawler.fetch_web_ranking(date, args.keep_json)
        else:
            illusts = []
            fetcher = crawler.ifetch_ranking(date, args.only_new, args.keep_json)
            for total, illust in enumerate(fetcher, start=1):
                illusts.append(illust)

                bk = illust.total_bookmarks / 1000
                print(f'iid={illust.id}  bookmark={bk:.1f}k  q={illust.quality}  {total=}')

                if JSON_FIELDS:
                    utils.print_json(illust, keys=JSON_FIELDS)
                    print('-' * 50, end='\n\n')

            crawler.multi_download(illusts, n_thread=args.n_thread, **RESOLUTIONS)
        print(f'Ranking {date} finished')


def download_illusts_by_url():
    url_q = Queue(args.n_thread * 2)
    thread_pool = []

    def download(n):
        while url := url_q.get():
            crawler.api.download(url, path=args.path)
        print(f'downloader-{n} exit', end='\x1b[K\n')

    # 创建并启动线程
    for n in range(args.n_thread):
        t = Thread(target=download, args=(n,), daemon=True)
        t.start()
        thread_pool.append(t)

    for num, url in iter_args():
        filename = os.path.basename(url)
        if os.path.exists(f'{args.path}/{filename}'):  # 检查是否已下载
            print(f'{num}. existed {filename}', end='\x1b[K\r')
        else:
            print(f'{num}. downloading {url}', end='\x1b[K\n')
            url_q.put(url)  # 将URL写入队列

    for _ in range(args.n_thread * 2):
        url_q.put(False)  # 向队列写入 False，使线程退出
    for t in thread_pool:
        t.join()


def signal_hander(*_):
    print('\nUser exit')
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, signal_hander)

    if args.download_type == 'artist':
        download_artist()
        print('============== artists fetched ==============\n\n')

    elif args.download_type == 'iid':
        # NOTE: 此模式下，会忽略 min_bookmarks，max_page_count，top，max_crawl 四个限制条件
        download_illusts_by_id()
        print('============== illusts fetched ==============\n\n')

    elif args.download_type == 'aid':
        download_illusts_by_aid()
        print('============== artist works fetched ==============\n\n')

    elif args.download_type == 'tag':
        download_illusts_by_tag()
        print('============== tag fetched ==============\n\n')

    elif args.download_type == 'rcmd':
        download_illusts_from_recommend()
        print('============== recommend fetched ==============\n\n')

    elif args.download_type == 'follow':
        download_illusts_from_follows()
        print('============== recommend fetched ==============\n\n')

    elif args.download_type == 'related':
        download_illusts_by_related()
        print('============== related fetched ==============\n\n')

    elif args.download_type == 'ranking':
        download_illust_from_ranking()
        print('============== ranking fetched ==============\n\n')

    elif args.download_type == 'url':
        download_illusts_by_url()
        print('============== urls fetched ==============\n\n')

    else:
        print('wrong type')
        sys.exit(1)


if __name__ == '__main__':
    main()
