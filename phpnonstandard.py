import requests
import sys
import re
from bs4 import BeautifulSoup
from colorama import Fore, Style, init

init(autoreset=True)

# A partial list of known standard extensions in PHP core or default builds
standard_modules = set(map(str.lower, [
    "Core", "date", "libxml", "openssl", "pcre", "zlib", "filter", "hash", "Reflection",
    "SPL", "session", "standard", "mysqlnd", "PDO", "tokenizer", "xml", "ctype", "dom",
    "fileinfo", "json", "mbstring", "Phar", "posix", "readline", "shmop", "SimpleXML",
    "sockets", "sodium", "sysvmsg", "sysvsem", "sysvshm", "xmlreader", "xmlwriter",
    "Zend OPcache", "cgi-fcgi", "xdebug", "intl", "gd", "curl", "mysqli", "pdo_mysql",
    "pdo_sqlite", "sqlite3", "exif", "iconv", "imap", "ftp"
]))

def clean(text):
    return re.sub(r'\s+', ' ', text.strip())

def extract_phpinfo(url):
    print(f"[+] Fetching phpinfo from: {url}\n")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"{Fore.RED}[ERROR] Failed to fetch phpinfo: {e}")
        sys.exit(1)

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all module headers
    print(f"{Fore.CYAN}==== PHP Modules ===={Style.RESET_ALL}")
    h2_modules = soup.find_all("h2")
    detected = []

    for h2 in h2_modules:
        module = clean(h2.text)
        module_lower = module.lower()

        # Skip known sections that aren't modules
        if module_lower in ['php credits', 'php license', 'configuration', 'apache environment']:
            continue

        detected.append(module)

        if module_lower not in standard_modules:
            print(f"{Fore.RED}[NONSTANDARD] {module}")
        else:
            print(f"{Fore.GREEN}[STANDARD]   {module}")

    # Now scan for nonstandard directives
    print(f"\n{Fore.CYAN}==== Custom Directives / INI Settings ===={Style.RESET_ALL}")
    found_directives = set()

    # Look at all tables with Directive headers
    directive_tables = soup.find_all('table')
    for table in directive_tables:
        if 'Directive' in table.text:
            rows = table.find_all('tr')[1:]
            for row in rows:
                cols = row.find_all('td')
                if len(cols) == 3:
                    directive = clean(cols[0].text)
                    found_directives.add(directive)

    # Known core INI settings from php.ini
    known_ini_directives = set(map(str.lower, [
        'display_errors', 'log_errors', 'error_reporting', 'memory_limit',
        'max_execution_time', 'post_max_size', 'upload_max_filesize',
        'file_uploads', 'expose_php', 'allow_url_fopen', 'allow_url_include',
        'session.save_path', 'session.use_cookies', 'session.name',
        'max_input_time', 'default_charset', 'disable_functions',
        'default_socket_timeout', 'user_agent', 'assert.active', 'assert.bail',
        'assert.warning', 'assert.exception'
    ]))

    for directive in sorted(found_directives):
        if directive.lower() not in known_ini_directives:
            print(f"{Fore.RED}[CUSTOM] {directive}")
        else:
            print(f"{Fore.GREEN}[CORE]   {directive}")

    print(f"\n{Fore.CYAN}==== Done ===={Style.RESET_ALL}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 phpinfo_extract_nonstandard.py http://target/phpinfo.php")
        sys.exit(1)

    extract_phpinfo(sys.argv[1])
