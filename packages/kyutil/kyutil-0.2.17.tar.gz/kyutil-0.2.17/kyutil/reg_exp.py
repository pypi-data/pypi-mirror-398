APSCHEDULER_BEGIN_TIME = r"(.+?)-"
APSCHEDULER_END_TIME = r"-(.+?) "
APSCHEDULER_TIME = r" (.+)"

KS_REPOS = r"--(\S+)=(\S+)"
KS_PACKAGES = "%packages\n(.*\n)*%end"

LORAX_LOG_PKG = r".*INFO pylorax.dnfhelper:\s*\(\d+/\d+\)\s*(.*)"
BUILD_LOG_CMD = r".*CMD:\[(.*)]"
BUILD_PARAMS = r"^\s*([^:]*)\s*:\s*(.*)"
BUILD_LOG_STEP = r".*(【Step-\d+/\d+】.*)"

HTML_URL = 'href=\"([^?].*)\">.*</a>'
HTML_URL_SQLITE = r'href=\"([^?].*)\">.*-primary\.sqlite\.bz2</a>'
HTML_URL_SQLITE_URL = r'href=\"(.*?.primary.sqlite.*?)\"'

RPM_OUT_SOURCE_RPM = r"Source RPM *: *(.*\.src\.rpm)\n"

IP_REG = r'^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$'
URL_REG = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"

RPMS_END = r'^(.*?)(\.src)?(\.rpm)$'
RPM_NVR = r'^(.*?)(\.?[a-z]?)(\.[a-z]{2,}\d{1,})([\._].*)?$'
MBS_FLAG = r'^(.*?)(\.module[\+_][a-z]{2,}.*?[\+_]\w+[\+_]\w+)$'
URL_REPODATA_SQLITE = r'<a href=\"(.*?.primary.sqlite.*?)\"'
