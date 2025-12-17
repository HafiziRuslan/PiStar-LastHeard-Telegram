# CHANGELOG

All notable changes to this project will be documented in this file.

## [unreleased] - (2025-12-17T15:57:33.321614037+08:00)

### 📚 Documentation

- 📝 docs(changelog): update release note
- 📝 docs(changelog): update release note
- 📝 docs(changelog): update release note
- 📝 docs(changelog): update release note
- 📝 docs(changelog): update release note
- 📝 docs(changelog): update release note
- 📝 docs(changelog): update release note
- 📝 docs(changelog): update release note
- 📝 docs(changelog): update release note
- 📝 docs(changelog): update release note
- 📝 docs(changelog): update release note
- 📝 docs(changelog): update release note
- 📝 docs(README): update installation and prerequisites
- 📝 docs(changelog): update release note

### ⚙️ Miscellaneous Tasks

- 👷 ci(sync): update gitlab_url to include .git extension
- 👷 ci(sync): update git mirroring actions
- 👷 ci(sync): disable automatic repository creation
- 👷 ci(workflows): update sync and merge schedule configurations
- 🔧 chore(main.sh): clear extra spacing in log
- 🔧 chore(main.sh): improve uv installation message
- 🔧 chore(uv): remove uv self update
- 🔧 chore(install): remove uv shell completion from main script
- 🔧 chore(scripts): improve script output and date formatting
- 🔧 chore(scripts): update venv activation for cross-platform compatibility
- 🔧 chore(scripts): improve shell script output and activation

## [beta] - (2025-12-10T23:54:59+08:00)

### 🚀 Features

- ✨ feat(ci): add git cliff for changelog generation
- ✨ feat(config): add telegram topic id config
- ✨ feat(telegram): add topic id support for telegram channels
- ✨ feat(mmdvmlogline): enhance talkgroup name retrieval
- ✨ feat(parser): add user country and talkgroup name to log line
- ✨ feat(mmdvmlogline): enhance telegram messages with location and talkgroup
- ✨ feat(ci): add workflow to sync repository to gitlab
- ✨ feat(mmdvmlogline): enhance rssi display with color coding
- ✨ feat(mmdvmlogline): enhance log parsing and data representation
- ✨ feat(deps): add humanize package to requirements
- ✨ feat(log_processor): enhance MMDVM log parsing and telegram reporting
- ✨ feat(parser): enhance DMR log parsing
- ✨ feat(parser): enhance MMDVM log parsing and add DMR data support
- ✨ feat(parser): add support for YSF network data lines
- ✨ feat(telegram): enhance telegram bot with log monitoring
- ✨ feat(core): add d-star support and refactor main script
- ✨ feat(log): enhance mmdvm log parsing and telegram integration
- ✨ feat(main): add python shebang and load dotenv
- ✨ feat(main): add script to generate commit messages from diffs
- ✨ feat(mmdvmlogline): add dmr data support
- ✨ feat(parser): add rssi support for dmr rf lines
- ✨ feat(mmdvmlogline): add data blocks to dmr log parsing
- ✨ feat(mmdvmlogline): add rssi to MMDVMLogLine
- ✨ feat(main): enhance MMDVM log parsing and telegram message formatting
- ♻️ refactor(core): rename and reorganize main scripts

### 🐛 Bug Fixes

- 🐛 fix(main): correct radio id and qrz url generation
- 🐛 fix(main): correct telegram name and duration formatting
- 🐛 fix(log): improve duration formatting in log messages
- 🐛 fix(parser): handle missing talkgroup ID gracefully
- 🐛 fix(talkgroup): improve talkgroup name retrieval from file
- 🐛 fix(talkgroup): correct talkgroup name lookup logic
- 🐛 fix(parser): correct parsing of BM translation files
- 🐛 fix(main): correct talkgroup and caller id parsing
- 🐛 fix(log): handle index errors in talkgroup and caller ID lookups
- 🐛 fix(log): handle index errors when reading files
- 🐛 fix(main): resolve talkgroup name and caller location
- 🐛 fix(main): dynamically find talkgroup list files
- 🐛 fix(main): correct talkgroup and location formatting
- 🐛 fix(main): correct timestamp timezone handling
- 🐛 fix(log): correct timestamp timezone and duration format
- 🐛 fix(README): correct directory name in reboot command
- 🐛 fix(main): correct timestamp formatting in MMDVMLogLine
- 🐛 fix(log): correct timestamp formatting in log messages
- 🐛 fix(log): handle missing timestamp in log lines
- 🐛 fix(log): correct timezone handling for log entries
- 🐛 fix(log): correct kerchunk flag logic
- 🐛 fix(log): correct duration format in voice log
- 🐛 fix(main): correct timestamp timezone and format
- 🐛 fix(rssi): correct signal strength indicator display
- 🐛 fix(rssi): correct rssi display
- 🐛 fix(dmr): correct rssi calculation in mmdvm log
- 🐛 fix(log): display BER and PL only when they exist
- 🐛 fix(parser): correct duration and ber type to float
- 🐛 fix(log): fix duration format in voice log messages
- 🐛 fix(regex): correct DMR data line regex
- 🐛 fix(parser): correct YSF-D log parsing and remove redundant flags
- 🐛 fix(log): correct data types and improve formatting
- 🐛 fix(regex): allow alphanumeric chars in destination TG
- 🐛 fix(parser): correct destination parsing in MMDVMLogLine
- 🐛 fix(dmr): support dmr-d mode in log messages
- 🔧 chore: update gitignore and fix duration label
- 🐛 fix(main): correct timestamp format and disable link previews
- 🐛 fix(telegram): correct timestamp format and labels
- 🐛 fix(parser): improve DMR log parsing
- 🐛 fix(parser): improve DMR data header parsing
- 🐛 fix(mmdvmlogline): refine DMR log parsing and display
- 🐛 fix(regex): correct RSSI regex pattern to allow for / in value
- 🐛 fix(parser): handle missing values in log lines
- 🐛 fix(log): shorten voice log labels for readability
- 🐛 fix(parser): sanitize destination and rssi value
- 🐛 fix(log): correct voice call duration unit
- 🐛 fix(log): correct voice/data type assignment in log messages
- 🐛 fix(build): install dependencies after venv activation
- 🐛 fix(parser): refine DMR log parsing and message filtering
- 🐛 fix(main): improve error handling and logging
- 🐛 fix(parser): correct log parsing for D-Star entries
- 🐛 fix(README): correct path in reboot cron entry
- 🐛 fix(regex): correct MMDVM log regex for BER matching
- 🐛 fix(parser): remove rssi from dmr log parsing
- 🐛 fix(parser): correct parsing and improve log output for DMR lines
- 🐛 fix(dmr): correct packet loss label in log output
- 🐛 fix(regex): correct mmdvm log parsing
- 🐛 fix(regex): correct mmdvmlogline regex
- 🐛 fix(regex): correct duration matching for DMR logs
- 🐛 fix(regex): correct log regex
- 🐛 fix(regex): improve log parsing for MMDVM
- 🐛 fix(dmr): shorten packet loss label in MMDVM log
- 🐛 fix(log): correct unit symbols for telegram messages
- 🐛 fix(logging): correct packet loss percentage format
- 🐛 fix(regex): correct dmr log parsing and message formatting
- 🐛 fix(regex): correct rssi regex to allow negative values
- 🐛 fix(regex): correct mmvm log regex for voice transmissions
- 🐛 fix(regex): correct log parsing regex
- 🐛 fix(regex): correct optional group in mmvm log parsing
- 🐛 fix(regex): correct mmdvm log regex
- 🐛 fix(log): correct duration display in log messages
- 🐛 fix(regex): correct destination regex for talk group
- 🐛 fix(parser): correct DMR destination parsing
- Fix message formatting in MMDVM log actions and correct requirements.txt syntax

### 💼 Other

- Merge pull request #4 from iu2frl/develop
- Typo in string contains routine
- Merge pull request #3 from iu2frl/develop
- Ignoring time messages with a flag
- Looping in case of failure
- Merge pull request #2 from iu2frl/develop
- Reworking Telegram message
- Merge pull request #1 from iu2frl/develop
- Refactor Telegram bot and DStar logs observer to use async/await pattern
- Testing async processing
- Adding cron entry
- Updating readme
- Adding links and source to messages
- First commit

### 🚜 Refactor

- ♻️ refactor(log): replace qrz_url with url, support radioid.net
- ♻️ refactor(main): improve log parsing and message formatting
- ♻️ refactor(mmdvmlogline): change duration and ber to int
- ♻️ refactor(test): use main.py instead of main-mmdvm.py
- ♻️ refactor(main): rename load_dotenv to load_env_variables

### 📚 Documentation

- 📝 docs(readme): update readme with installation and usage instructions

### 🎨 Styling

- 💄 style(mmdvmlogline): improve log message formatting

### ⚙️ Miscellaneous Tasks

- 🔧 chore(scripts): improve virtual environment handling in main.sh
- 🔧 chore(settings): remove unused vscode settings
- 🔧 chore(vscode): add vscode settings for pylint
- Update README with MMDVM script details, and add main-dstargateway.py and main-mmdvm.py for log monitoring. Adjust requirements.txt for specific package versions.

---

generated using git-cliff - (2025-12-17T15:57:33.327421228+08:00)
