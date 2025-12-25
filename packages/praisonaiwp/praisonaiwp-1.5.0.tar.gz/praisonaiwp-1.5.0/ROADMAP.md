# PraisonAI WPcli - Feature Roadmap

## Current Status (v1.4.3)

**WPClient Method Coverage: 28/61 (45.9%)**

### ✅ Implemented Features

1. **User Management** (5 methods)
   - `praisonaiwp user list/get/create/update/delete`

2. **Media Management** (3 methods)
   - `praisonaiwp media upload/url/get/list`

3. **Category Management** (7 methods)
   - `praisonaiwp category list/get/set/add/remove`

4. **Plugin Management** (4 methods)
   - `praisonaiwp plugin list/activate/deactivate/update`

5. **Post Management** (2 methods)
   - `praisonaiwp create/update`

6. **Search & List** (2 methods)
   - `praisonaiwp find/list`

7. **AI Integration** (SmartContentAgent)
   - Auto-routing, server detection, content generation

8. **MCP Support** (23 tools)
   - Model Context Protocol integration

---

## 🎯 Roadmap to 100% Coverage (34 Methods Remaining)

### Priority 1: Options Management (3 methods)
**Status:** Not Started  
**Estimated Time:** 1 hour

**Commands:**
- `praisonaiwp option get OPTION_NAME`
- `praisonaiwp option set OPTION_NAME VALUE`
- `praisonaiwp option delete OPTION_NAME`

**WPClient Methods:**
- `get_option()`
- `set_option()`
- `delete_option()`

**Files to Create:**
- `tests/cli/test_option_commands.py`
- `praisonaiwp/cli/commands/option.py`

---

### Priority 2: Post Meta Management (4 methods)
**Status:** Not Started  
**Estimated Time:** 1.5 hours

**Commands:**
- `praisonaiwp meta post-get POST_ID KEY`
- `praisonaiwp meta post-set POST_ID KEY VALUE`
- `praisonaiwp meta post-update POST_ID KEY VALUE`
- `praisonaiwp meta post-delete POST_ID KEY`

**WPClient Methods:**
- `get_post_meta()`
- `set_post_meta()`
- `update_post_meta()`
- `delete_post_meta()`

**Files to Create:**
- `tests/cli/test_meta_commands.py`
- `praisonaiwp/cli/commands/meta.py`

---

### Priority 3: Comment Management (6 methods)
**Status:** Not Started  
**Estimated Time:** 2 hours

**Commands:**
- `praisonaiwp comment list [--status STATUS] [--post-id ID]`
- `praisonaiwp comment get COMMENT_ID`
- `praisonaiwp comment create POST_ID --content TEXT --author NAME`
- `praisonaiwp comment update COMMENT_ID --content TEXT`
- `praisonaiwp comment delete COMMENT_ID`
- `praisonaiwp comment approve COMMENT_ID`

**WPClient Methods:**
- `list_comments()`
- `get_comment()`
- `create_comment()`
- `update_comment()`
- `delete_comment()`
- `approve_comment()`

**Files to Create:**
- `tests/cli/test_comment_commands.py`
- `praisonaiwp/cli/commands/comment.py`

---

### Priority 4: System Commands (4 methods)
**Status:** Not Started  
**Estimated Time:** 1 hour

**Commands:**
- `praisonaiwp system cache-flush`
- `praisonaiwp system cache-type`
- `praisonaiwp system version`
- `praisonaiwp system check-install`

**WPClient Methods:**
- `flush_cache()`
- `get_cache_type()`
- `get_core_version()`
- `core_is_installed()`

**Files to Create:**
- `tests/cli/test_system_commands.py`
- `praisonaiwp/cli/commands/system.py`

---

### Priority 5: User Meta Management (4 methods)
**Status:** Not Started  
**Estimated Time:** 1 hour

**Commands:**
- `praisonaiwp meta user-get USER_ID KEY`
- `praisonaiwp meta user-set USER_ID KEY VALUE`
- `praisonaiwp meta user-update USER_ID KEY VALUE`
- `praisonaiwp meta user-delete USER_ID KEY`

**WPClient Methods:**
- `get_user_meta()`
- `set_user_meta()`
- `update_user_meta()`
- `delete_user_meta()`

**Files to Enhance:**
- `tests/cli/test_meta_commands.py` (add user meta tests)
- `praisonaiwp/cli/commands/meta.py` (add user meta subcommands)

---

### Priority 6: Term/Taxonomy Management (3 methods)
**Status:** Not Started  
**Estimated Time:** 1 hour

**Commands:**
- `praisonaiwp category create NAME --taxonomy TAXONOMY`
- `praisonaiwp category update TERM_ID --name NAME`
- `praisonaiwp category delete TERM_ID`

**WPClient Methods:**
- `create_term()`
- `update_term()`
- `delete_term()`

**Files to Enhance:**
- `tests/cli/test_category_commands.py` (add term tests)
- `praisonaiwp/cli/commands/category.py` (add create/update/delete)

---

### Priority 7: Theme Management (2 methods)
**Status:** Not Started  
**Estimated Time:** 45 minutes

**Commands:**
- `praisonaiwp theme list`
- `praisonaiwp theme activate THEME_NAME`

**WPClient Methods:**
- `list_themes()`
- `activate_theme()`

**Files to Create:**
- `tests/cli/test_theme_commands.py`
- `praisonaiwp/cli/commands/theme.py`

---

### Priority 8: Menu Management (4 methods)
**Status:** Not Started  
**Estimated Time:** 1.5 hours

**Commands:**
- `praisonaiwp menu list`
- `praisonaiwp menu create MENU_NAME`
- `praisonaiwp menu delete MENU_ID`
- `praisonaiwp menu add-item MENU_ID --title TITLE --url URL`

**WPClient Methods:**
- `list_menus()`
- `create_menu()`
- `delete_menu()`
- `add_menu_item()`

**Files to Create:**
- `tests/cli/test_menu_commands.py`
- `praisonaiwp/cli/commands/menu.py`

---

### Priority 9: Transient Management (3 methods)
**Status:** Not Started  
**Estimated Time:** 1 hour

**Commands:**
- `praisonaiwp transient get KEY`
- `praisonaiwp transient set KEY VALUE --expiration SECONDS`
- `praisonaiwp transient delete KEY`

**WPClient Methods:**
- `get_transient()`
- `set_transient()`
- `delete_transient()`

**Files to Create:**
- `tests/cli/test_transient_commands.py`
- `praisonaiwp/cli/commands/transient.py`

---

### Priority 10: Post Utilities (4 methods)
**Status:** Not Started  
**Estimated Time:** 1 hour

**Commands:**
- `praisonaiwp post delete POST_ID [--force]`
- `praisonaiwp post exists POST_ID`
- `praisonaiwp db query 'SQL_QUERY'`
- `praisonaiwp user default` (get default admin user)

**WPClient Methods:**
- `delete_post()`
- `post_exists()`
- `db_query()`
- `get_default_user()`

**Files to Create:**
- `tests/cli/test_post_commands.py`
- `praisonaiwp/cli/commands/post.py`
- `praisonaiwp/cli/commands/db.py`

---

## 📋 Implementation Approach

### Test-Driven Development (TDD)

For each priority:

1. **Write Tests First** (Red)
   - Create test file with all test cases
   - Tests should fail initially

2. **Implement CLI Commands** (Green)
   - Create command file
   - Implement minimal code to pass tests
   - Register command in main.py

3. **Refactor & Verify**
   - Run tests and ensure all pass
   - Refactor code if needed
   - Update documentation

4. **Commit Changes**
   - Commit when all tests pass
   - Clear commit message with test results

---

## 📊 Milestones

### Version 1.5.0 - Complete CLI Coverage
**Target:** 100% WPClient method coverage (61/61 methods)  
**Status:** In Planning  
**Estimated Completion:** 10-15 hours of development

**Deliverables:**
- ✅ All 34 missing methods exposed via CLI
- ✅ Comprehensive test suite (~41 new tests)
- ✅ Complete documentation
- ✅ Updated README with all commands
- ✅ CHANGELOG with detailed release notes

---

## 🤝 Contributing

To implement any priority from this roadmap:

1. Follow the TDD approach outlined above
2. Ensure tests are written first
3. Maintain code style consistency
4. Update this roadmap when complete
5. Submit PR with test results

---

## 📞 Questions?

For questions about implementation or to claim a priority, please open an issue on GitHub.

**Last Updated:** December 22, 2025  
**Version:** 1.4.3
