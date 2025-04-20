import requests
import sys
import re
from colorama import Fore, Style, init
from bs4 import BeautifulSoup

# Init colorama
init(autoreset=True)

# Risky settings
risky_settings = {
    'expose_php': 'Info disclosure',
    'allow_url_fopen': 'Remote file access',
    'allow_url_include': 'Remote file inclusion (RFI)',
    'display_errors': 'Error disclosure',
    'log_errors': 'Log injection (via LFI)',
    'register_globals': 'Legacy variable injection',
    'session.use_trans_sid': 'Session ID in URL',
    'magic_quotes_gpc': 'Broken validation (deprecated)',
    'enable_dl': 'Dangerous extension loading',
    'file_uploads': 'Enables file uploads',
    'upload_tmp_dir': 'Temp path for uploads (check writable)',
    'open_basedir': 'Filesystem restriction (bad if OFF)',
    'disable_functions': 'Critical if empty or missing',
    'auto_prepend_file': 'Potential code injection',
    'auto_append_file': 'Potential code injection'
}

# Dangerous functions
dangerous_functions = [
    'system', 'exec', 'shell_exec', 'passthru', 'popen', 'proc_open',
    'eval', 'assert', 'include', 'require', 'include_once', 'require_once',
    'base64_decode', 'preg_replace', 'create_function', 'dl', 'curl_exec',
    'parse_ini_file', 'show_source'
]

def color_risk(setting, description, level='high'):
    if level == 'high':
        return f"{Fore.RED}[!] {setting}: {description}{Style.RESET_ALL}"
    elif level == 'medium':
        return f"{Fore.YELLOW}[-] {setting}: {description}{Style.RESET_ALL}"
    else:
        return f"{Fore.GREEN}[+] {setting}: {description}{Style.RESET_ALL}"

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 prog.py http://target/phpinfo.php")
        sys.exit(1)

    url = sys.argv[1]
    print(f"[+] Fetching phpinfo from: {url}\n")

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"{Fore.RED}[ERROR] Failed to fetch page: {e}")
        sys.exit(1)

    soup = BeautifulSoup(r.text, 'html.parser')
    text = soup.get_text().lower()

    # Check for risky php.ini settings
    print(f"{Fore.CYAN}==== Analyzing php.ini Settings ===={Style.RESET_ALL}")
    for setting, desc in risky_settings.items():
        if setting in text:
            match = re.search(rf'{setting}\s*</td><td class="v">(.*?)</td>', r.text, re.IGNORECASE)
            value = match.group(1) if match else 'present'
            if setting == 'disable_functions':
                if value.strip() == '' or value.strip().lower() == 'no value':
                    print(color_risk(setting, f"{desc} - Empty (dangerous)"))
                else:
                    print(color_risk(setting, f"{desc} - Functions disabled: {value}", level='medium'))
            elif value.lower() in ['on', 'enabled', '1']:
                print(color_risk(setting, f"{desc} - Enabled"))
            elif setting == 'open_basedir' and value.strip() == '':
                print(color_risk(setting, f"{desc} - Not set (dangerous)"))
            else:
                print(color_risk(setting, f"{desc} - {value}", level='medium'))
        else:
            print(color_risk(setting, "Not found", level='low'))

    # Check for dangerous functions not disabled
    print(f"\n{Fore.CYAN}==== Analyzing Dangerous PHP Functions ===={Style.RESET_ALL}")
    disabled_match = re.search(r'disable_functions\s*</td><td class="v">(.*?)</td>', r.text, re.IGNORECASE)
    disabled = disabled_match.group(1).split(',') if disabled_match else []

    for func in dangerous_functions:
        if func in disabled:
            print(color_risk(func, "Disabled", level='low'))
        else:
            print(color_risk(func, "Not disabled!", level='high'))

if __name__ == "__main__":
    main()
