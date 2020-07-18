from invoke import task, context
from pathlib import Path
from urllib.request import urlopen, Request, urljoin, urlparse, urlunparse
from urllib.error import HTTPError
from json import loads
from time import sleep, time
import webbrowser


@task(help={
    'host': 'The url of the nextcloud server.',
    'base-dir': 'The path to search for directories in the nextcloud server. (Can be changed later in config.py)',
})
def login(c, host, base_dir='/'):
    '''Login with the login flow v2 of nextcloud to get an app password.

    This will open a browser tab for you to login to.
    The app password will be written in config.py.
    '''
    url = urlparse(host)
    if (url.scheme is not None) and (url.scheme != 'https'):
        print('The connection to {} does not use the secure https protocol. Aborting login.'.format(url))

    # generate loginflow url
    nextcloud_host_url = urlunparse(('https', url.netloc, url.path, None, None, None))
    login_flow_url = urljoin(host, '/index.php/login/v2')

    # send request
    req = Request(url=login_flow_url, method='POST')
    req.add_header('User-Agent', 'nextcloud-link-generator')
    response = None
    with urlopen(req) as res:
        if res.status != 200:
            print("Could not start login flow!")
            return
        response = loads('\n'.join(map(lambda s: s.decode(), res.readlines())))
    print(response)

    webbrowser.open_new_tab(response['login'])

    poll_data = 'token=' + response['poll']['token']
    poll_req = Request(url=response['poll']['endpoint'], data=poll_data.encode(), method='POST')

    poll_response = None
    start = time()
    while (poll_response is None) and ((time() - start) < 300):
        try:
            with urlopen(poll_req) as res:
                if res.status == 200:
                    poll_response = loads('\n'.join(map(lambda s: s.decode(), res.readlines())))
                    break
                else:
                    print('Something went wrong with the login flow.')
                    return
        except HTTPError as e:
            status = e.getcode()
            if status == 404:
                sleep(1)
            else:
                print('Something went wrong with the login flow.')
                return
    else:
        print('Login took too long. Try again and be faster next time.')
        return

    if poll_response is None:
        print('Could not read app password!')
        return

    print(poll_response)

    with open("config.py", 'w') as outfile:
        outfile.write("user = '{}'\n".format(poll_response['loginName']))
        outfile.write("password = '{}'\n\n".format(poll_response['appPassword']))
        outfile.write("url = '{}'\n\n".format(poll_response['server']))
        outfile.write("base_dir = '{}'\n\n".format(base_dir))


@task(help={
    'no-cache': 'Bypass the cache and load everything from the server.',
})
def list_files(c, no_cache=False):
    '''List all directories in the basedir.'''
    import config
    from utilities import Nextcloud
    nc = Nextcloud(config.url, config.user, config.password, config.base_dir)
    for f in nc.get_filenames_with_path(no_cache=no_cache):
        print(f['filename'], f['path'])


@task(help={
    'lectures': 'A list of lecture names to search for. Seperate lectures with ",".',
    'exact': 'Only include exact substring matches (still ignores character case).',
    'no-cache': 'Bypass the cache and load everything from the server.',
})
def search(c, lectures, exact=False, no_cache=False):
    '''Search for directories in the basedir.'''
    import config
    from utilities import Nextcloud
    nc = Nextcloud(config.url, config.user, config.password, config.base_dir)
    for f in nc.get_files_for_lectures(lectures.split(','), exact_matches=exact, no_cache=no_cache):
        print(f['searchableFilename'], f['filename'], f['path'], sep='\t')

@task(help={
    'lectures': 'A list of lecture names to search for. Seperate lectures with ",".',
    'expiry': 'Nr. of days until links expire.',
    'exact': 'Only include exact substring matches (still ignores character case).',
    'no-cache': 'Bypass the cache and load everything from the server.',
})
def links(c, lectures, exact=False, no_cache=False, expiry=7):
    '''Generate share links for directories in the basedir.'''
    import config
    from utilities import Helper
    from tabulate import tabulate
    from utilities import Nextcloud
    nc = Nextcloud(config.url, config.user, config.password, config.base_dir)
    files = nc.get_files_for_lectures(lectures.split(','), exact_matches=exact, no_cache=no_cache)
    links = nc.get_links_for_files(files, link_expire_in_days=expiry)
    clipboard = ''
    table_content = []
    for exam, link in links.items():
        clipboard += '{exam}: {link}\n'.format(exam=exam, link=link)
        table_content.append([exam, link])
    table_content = sorted(table_content, key=lambda x: x[0])
    try:
        Helper.toClipboard(clipboard)
    except Exception:
        print(clipboard)
    header = ["Exam", "Link"]
    print(tabulate(table_content, headers=header))
