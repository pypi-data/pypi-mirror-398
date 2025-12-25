"""WordPress CLI client for PraisonAIWP"""

import json
from typing import Any, Dict, List, Optional

from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.utils.exceptions import WPCLIError
from praisonaiwp.utils.logger import get_logger

logger = get_logger(__name__)


class WPClient:
    """WordPress CLI operations wrapper"""

    def __init__(
        self,
        ssh: SSHManager,
        wp_path: str,
        php_bin: str = 'php',
        wp_cli: str = '/usr/local/bin/wp',
        verify_installation: bool = True
    ):
        """
        Initialize WP Client

        Args:
            ssh: SSH Manager instance
            wp_path: WordPress installation path
            php_bin: PHP binary path (default: 'php')
            wp_cli: WP-CLI binary path (default: '/usr/local/bin/wp')
            verify_installation: Verify WP-CLI and WordPress are available (default: True)
        """
        self.ssh = ssh
        self.wp_path = wp_path
        self.php_bin = php_bin
        self.wp_cli = wp_cli

        logger.debug(f"Initialized WPClient for {wp_path}")

        # Verify installation if requested
        if verify_installation:
            self._verify_installation()

    def _verify_installation(self):
        """
        Verify WP-CLI and WordPress installation

        Raises:
            WPCLIError: If WP-CLI or WordPress not found
        """
        try:
            # Check if WP-CLI binary exists
            stdout, stderr = self.ssh.execute(f"test -f {self.wp_cli} && echo 'exists' || echo 'not found'")

            if 'not found' in stdout:
                raise WPCLIError(
                    f"WP-CLI not found at {self.wp_cli}\n"
                    f"\nInstallation instructions:\n"
                    f"1. Download: curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar\n"
                    f"2. Make executable: chmod +x wp-cli.phar\n"
                    f"3. Move to path: sudo mv wp-cli.phar {self.wp_cli}\n"
                    f"\nOr specify correct path with --wp-cli option"
                )

            # Check if WordPress directory exists
            stdout, stderr = self.ssh.execute(f"test -d {self.wp_path} && echo 'exists' || echo 'not found'")

            if 'not found' in stdout:
                raise WPCLIError(
                    f"WordPress installation not found at {self.wp_path}\n"
                    f"Please verify the WordPress path is correct."
                )

            # Check if wp-config.php exists
            stdout, stderr = self.ssh.execute(f"test -f {self.wp_path}/wp-config.php && echo 'exists' || echo 'not found'")

            if 'not found' in stdout:
                raise WPCLIError(
                    f"wp-config.php not found in {self.wp_path}\n"
                    f"This doesn't appear to be a valid WordPress installation."
                )

            # Test WP-CLI execution
            stdout, stderr = self.ssh.execute(f"cd {self.wp_path} && {self.php_bin} {self.wp_cli} --version")

            if stderr and ('command not found' in stderr.lower() or 'no such file' in stderr.lower()):
                raise WPCLIError(
                    f"Failed to execute WP-CLI\n"
                    f"Error: {stderr}\n"
                    f"\nPossible issues:\n"
                    f"1. PHP binary not found: {self.php_bin}\n"
                    f"2. WP-CLI not executable: {self.wp_cli}\n"
                    f"3. Missing PHP extensions (mysql, mysqli)\n"
                    f"\nFor Plesk servers, try: /opt/plesk/php/8.3/bin/php"
                )

            if 'WP-CLI' in stdout:
                logger.info(f"WP-CLI verified: {stdout.strip()}")
            else:
                logger.warning(f"WP-CLI verification returned unexpected output: {stdout}")

        except WPCLIError:
            raise
        except Exception as e:
            logger.warning(f"Could not verify WP-CLI installation: {e}")

    def wp(self, *args, **kwargs) -> Any:
        """
        Generic WP-CLI command executor - supports ANY WP-CLI command

        This method provides direct access to WP-CLI without needing specific wrapper methods.
        Arguments are automatically converted to WP-CLI flags and options.

        Args:
            *args: Command parts (e.g., 'post', 'list')
            **kwargs: Command options (converted to --key=value flags)
                     - Use True for boolean flags (e.g., porcelain=True -> --porcelain)
                     - Use format='json' for automatic JSON parsing
                     - Underscores in keys are converted to hyphens (dry_run -> --dry-run)

        Returns:
            Command output (string), or parsed JSON if format='json'

        Examples:
            # Create a user
            wp('user', 'create', 'john', 'john@example.com', role='editor', porcelain=True)

            # List posts
            posts = wp('post', 'list', status='publish', format='json')

            # Flush cache
            wp('cache', 'flush')

            # Search and replace
            wp('search-replace', 'old', 'new', dry_run=True)

            # Plugin operations
            wp('plugin', 'activate', 'akismet')
            wp('plugin', 'list', status='active', format='json')

        Raises:
            WPCLIError: If command fails
        """
        # Build command from args
        cmd_parts = list(args)

        # Add kwargs as flags/options
        auto_parse_json = False
        for key, value in kwargs.items():
            # Convert underscores to hyphens for WP-CLI convention
            flag_key = key.replace('_', '-')

            if value is True:
                # Boolean flag (e.g., --porcelain, --dry-run)
                cmd_parts.append(f"--{flag_key}")
            elif value is not False and value is not None:
                # Key-value option
                if flag_key == 'format' and value == 'json':
                    auto_parse_json = True

                # Escape single quotes in values
                escaped_value = str(value).replace("'", "'\\''")
                cmd_parts.append(f"--{flag_key}='{escaped_value}'")

        # Execute command
        cmd = ' '.join(cmd_parts)
        result = self._execute_wp(cmd)

        # Auto-parse JSON if format=json
        if auto_parse_json and result.strip():
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON output: {result[:100]}")
                return result

        return result.strip() if result else ""

    def _execute_wp(self, command: str) -> str:
        """
        Execute WP-CLI command (internal method)

        Args:
            command: WP-CLI command (without 'wp' prefix)

        Returns:
            Command output

        Raises:
            WPCLIError: If command fails
        """
        full_cmd = f"cd {self.wp_path} && {self.php_bin} {self.wp_cli} {command}"

        logger.debug(f"Executing WP-CLI: {command}")

        try:
            stdout, stderr = self.ssh.execute(full_cmd)
        except Exception as e:
            raise WPCLIError(f"Failed to execute WP-CLI command: {e}") from e

        # Check for common error patterns
        if stderr:
            error_lower = stderr.lower()

            if 'command not found' in error_lower:
                raise WPCLIError(
                    f"WP-CLI command not found\n"
                    f"Error: {stderr}\n"
                    f"\nPlease verify:\n"
                    f"1. WP-CLI is installed at: {self.wp_cli}\n"
                    f"2. PHP binary is correct: {self.php_bin}"
                )

            if 'no such file or directory' in error_lower:
                raise WPCLIError(
                    f"File or directory not found\n"
                    f"Error: {stderr}\n"
                    f"\nPlease verify:\n"
                    f"1. WordPress path: {self.wp_path}\n"
                    f"2. WP-CLI path: {self.wp_cli}"
                )

            if 'error:' in error_lower:
                # Don't log "Term doesn't exist" as error - it's expected when looking up categories by name
                if "term doesn't exist" not in error_lower:
                    logger.error(f"WP-CLI error: {stderr}")
                raise WPCLIError(f"WP-CLI error: {stderr}")

        return stdout.strip()

    def get_post(self, post_id: int, field: Optional[str] = None) -> Any:
        """
        Get post data

        Args:
            post_id: Post ID
            field: Specific field to retrieve (optional)

        Returns:
            Post data (dict if no field specified, str if field specified)
        """
        cmd = f"post get {post_id}"

        if field:
            cmd += f" --field={field}"
            result = self._execute_wp(cmd)
            return result
        else:
            cmd += " --format=json"
            result = self._execute_wp(cmd)
            return json.loads(result)

    def get_default_user(self) -> Optional[str]:
        """
        Get the default admin user (user with ID 1 or first admin user)

        Returns:
            User login name or None if not found
        """
        try:
            # Try to get user with ID 1 (typically the first admin)
            cmd = "user get 1 --field=user_login"
            result = self._execute_wp(cmd)
            return result.strip()
        except Exception:
            try:
                # Fallback: get first admin user
                cmd = "user list --role=administrator --field=user_login --format=csv"
                result = self._execute_wp(cmd)
                users = result.strip().split('\n')
                if users and users[0]:
                    return users[0]
            except Exception as e:
                logger.warning(f"Could not get default user: {e}")
        return None

    def create_post(self, **kwargs) -> int:
        """
        Create a new post

        Args:
            **kwargs: Post fields (post_title, post_content, post_status, etc.)

        Returns:
            Created post ID
        """
        # Auto-set author to default admin if not specified
        if 'post_author' not in kwargs:
            default_user = self.get_default_user()
            if default_user:
                kwargs['post_author'] = default_user
                logger.debug(f"Using default author: {default_user}")

        args = []
        for key, value in kwargs.items():
            # Escape single quotes in value
            escaped_value = str(value).replace("'", "'\\''")
            args.append(f"--{key}='{escaped_value}'")

        cmd = f"post create {' '.join(args)} --porcelain"
        result = self._execute_wp(cmd)

        post_id = int(result.strip())
        logger.info(f"Created post ID: {post_id}")

        return post_id

    def update_post(self, post_id: int, **kwargs) -> bool:
        """
        Update an existing post

        Args:
            post_id: Post ID to update
            **kwargs: Fields to update

        Returns:
            True if successful
        """
        args = []
        for key, value in kwargs.items():
            # Escape single quotes in value
            escaped_value = str(value).replace("'", "'\\''")
            args.append(f"--{key}='{escaped_value}'")

        cmd = f"post update {post_id} {' '.join(args)}"
        self._execute_wp(cmd)

        logger.info(f"Updated post ID: {post_id}")
        return True

    def delete_post(self, post_id: int, force: bool = False) -> bool:
        """
        Delete a post

        Args:
            post_id: Post ID to delete
            force: Skip trash and force deletion

        Returns:
            True if successful
        """
        force_flag = '--force' if force else ''
        cmd = f"post delete {post_id} {force_flag}"
        self._execute_wp(cmd)

        logger.info(f"Deleted post ID: {post_id}")
        return True

    def post_exists(self, post_id: int) -> bool:
        """
        Check if a post exists

        Args:
            post_id: Post ID to check

        Returns:
            True if post exists, False otherwise
        """
        try:
            cmd = f"post exists {post_id}"
            self._execute_wp(cmd)
            logger.debug(f"Post {post_id} exists")
            return True
        except WPCLIError:
            logger.debug(f"Post {post_id} does not exist")
            return False

    def get_post_meta(self, post_id: int, key: str = None) -> Any:
        """
        Get post meta value(s)

        Args:
            post_id: Post ID
            key: Meta key (if None, returns all meta)

        Returns:
            Meta value or dict of all meta
        """
        if key:
            cmd = f"post meta get {post_id} {key}"
            result = self._execute_wp(cmd)
            return result.strip()
        else:
            cmd = f"post meta list {post_id} --format=json"
            result = self._execute_wp(cmd)
            return json.loads(result)

    def set_post_meta(self, post_id: int, key: str, value: str) -> bool:
        """
        Set post meta value

        Args:
            post_id: Post ID
            key: Meta key
            value: Meta value

        Returns:
            True if successful
        """
        escaped_value = str(value).replace("'", "'\\''")
        cmd = f"post meta set {post_id} {key} '{escaped_value}'"
        self._execute_wp(cmd)
        logger.info(f"Set meta {key} for post {post_id}")
        return True

    def delete_post_meta(self, post_id: int, key: str) -> bool:
        """
        Delete post meta

        Args:
            post_id: Post ID
            key: Meta key

        Returns:
            True if successful
        """
        cmd = f"post meta delete {post_id} {key}"
        self._execute_wp(cmd)
        logger.info(f"Deleted meta {key} from post {post_id}")
        return True

    def update_post_meta(self, post_id: int, key: str, value: str) -> bool:
        """
        Update post meta value

        Args:
            post_id: Post ID
            key: Meta key
            value: Meta value

        Returns:
            True if successful
        """
        escaped_value = str(value).replace("'", "'\\''")
        cmd = f"post meta update {post_id} {key} '{escaped_value}'"
        self._execute_wp(cmd)
        logger.info(f"Updated meta {key} for post {post_id}")
        return True

    def list_users(self, **filters) -> List[Dict[str, Any]]:
        """
        List users with filters

        Args:
            **filters: Filters (role, search, etc.)

        Returns:
            List of user dictionaries
        """
        args = ["--format=json"]

        for key, value in filters.items():
            args.append(f"--{key}={value}")

        cmd = f"user list {' '.join(args)}"
        result = self._execute_wp(cmd)

        return json.loads(result)

    def get_user(self, user_id: int) -> Dict[str, Any]:
        """
        Get user details

        Args:
            user_id: User ID

        Returns:
            User dictionary
        """
        cmd = f"user get {user_id} --format=json"
        result = self._execute_wp(cmd)

        return json.loads(result)

    def create_user(self, username: str, email: str, **kwargs) -> int:
        """
        Create a new user

        Args:
            username: Username
            email: Email address
            **kwargs: Additional user fields (role, user_pass, display_name, etc.)

        Returns:
            User ID
        """
        args = [username, email]

        for key, value in kwargs.items():
            escaped_value = str(value).replace("'", "'\\''")
            args.append(f"--{key}='{escaped_value}'")

        cmd = f"user create {' '.join(args)} --porcelain"
        result = self._execute_wp(cmd)
        user_id = int(result.strip())
        logger.info(f"Created user {username} with ID {user_id}")
        return user_id

    def update_user(self, user_id: int, **kwargs) -> bool:
        """
        Update user fields

        Args:
            user_id: User ID
            **kwargs: User fields to update

        Returns:
            True if successful
        """
        args = [str(user_id)]

        for key, value in kwargs.items():
            escaped_value = str(value).replace("'", "'\\''")
            args.append(f"--{key}='{escaped_value}'")

        cmd = f"user update {' '.join(args)}"
        self._execute_wp(cmd)
        logger.info(f"Updated user {user_id}")
        return True

    def delete_user(self, user_id: int, reassign: int = None) -> bool:
        """
        Delete a user

        Args:
            user_id: User ID to delete
            reassign: User ID to reassign posts to (optional)

        Returns:
            True if successful
        """
        args = [str(user_id), "--yes"]

        if reassign is not None:
            args.append(f"--reassign={reassign}")

        cmd = f"user delete {' '.join(args)}"
        self._execute_wp(cmd)
        logger.info(f"Deleted user {user_id}")
        return True

    def get_option(self, option_name: str) -> str:
        """
        Get WordPress option value

        Args:
            option_name: Option name

        Returns:
            Option value
        """
        cmd = f"option get {option_name}"
        result = self._execute_wp(cmd)

        return result.strip()

    def set_option(self, option_name: str, value: str) -> bool:
        """
        Set WordPress option value

        Args:
            option_name: Option name
            value: Option value

        Returns:
            True if successful
        """
        escaped_value = str(value).replace("'", "'\\''")
        cmd = f"option set {option_name} '{escaped_value}'"
        self._execute_wp(cmd)
        logger.info(f"Set option {option_name}")
        return True

    def delete_option(self, option_name: str) -> bool:
        """
        Delete WordPress option

        Args:
            option_name: Option name

        Returns:
            True if successful
        """
        cmd = f"option delete {option_name}"
        self._execute_wp(cmd)
        logger.info(f"Deleted option {option_name}")
        return True

    def list_plugins(self, **filters) -> List[Dict[str, Any]]:
        """
        List installed plugins

        Args:
            **filters: Filters (status, etc.)

        Returns:
            List of plugin dictionaries
        """
        args = ["--format=json"]

        for key, value in filters.items():
            args.append(f"--{key}={value}")

        cmd = f"plugin list {' '.join(args)}"
        result = self._execute_wp(cmd)

        return json.loads(result)

    def list_themes(self, **filters) -> List[Dict[str, Any]]:
        """
        List installed themes

        Args:
            **filters: Filters (status, etc.)

        Returns:
            List of theme dictionaries
        """
        args = ["--format=json"]

        for key, value in filters.items():
            args.append(f"--{key}={value}")

        cmd = f"theme list {' '.join(args)}"
        result = self._execute_wp(cmd)

        return json.loads(result)

    def activate_plugin(self, plugin: str) -> bool:
        """
        Activate a plugin

        Args:
            plugin: Plugin slug or path

        Returns:
            True if successful
        """
        cmd = f"plugin activate {plugin}"
        self._execute_wp(cmd)
        logger.info(f"Activated plugin {plugin}")
        return True

    def deactivate_plugin(self, plugin: str) -> bool:
        """
        Deactivate a plugin

        Args:
            plugin: Plugin slug or path

        Returns:
            True if successful
        """
        cmd = f"plugin deactivate {plugin}"
        self._execute_wp(cmd)
        logger.info(f"Deactivated plugin {plugin}")
        return True

    def update_plugin(self, plugin: str = "all") -> bool:
        """
        Update one or all plugins

        Args:
            plugin: Plugin slug/path or "all" to update all plugins

        Returns:
            True if successful
        """
        if plugin == "all":
            cmd = "plugin update --all"
        else:
            cmd = f"plugin update {plugin}"
        self._execute_wp(cmd)
        logger.info(f"Updated plugin(s): {plugin}")
        return True

    def activate_theme(self, theme: str) -> bool:
        """
        Activate a theme

        Args:
            theme: Theme slug

        Returns:
            True if successful
        """
        cmd = f"theme activate {theme}"
        self._execute_wp(cmd)
        logger.info(f"Activated theme {theme}")
        return True

    def get_user_meta(self, user_id: int, key: str = None) -> Any:
        """
        Get user meta value(s)

        Args:
            user_id: User ID
            key: Meta key (optional, returns all if not specified)

        Returns:
            Meta value or list of all meta
        """
        if key:
            cmd = f"user meta get {user_id} {key}"
            result = self._execute_wp(cmd)
            return result.strip()
        else:
            cmd = f"user meta list {user_id} --format=json"
            result = self._execute_wp(cmd)
            return json.loads(result)

    def set_user_meta(self, user_id: int, key: str, value: str) -> bool:
        """
        Set user meta value

        Args:
            user_id: User ID
            key: Meta key
            value: Meta value

        Returns:
            True if successful
        """
        escaped_value = str(value).replace("'", "'\\''")
        cmd = f"user meta add {user_id} {key} '{escaped_value}'"
        self._execute_wp(cmd)
        logger.info(f"Set meta {key} for user {user_id}")
        return True

    def update_user_meta(self, user_id: int, key: str, value: str) -> bool:
        """
        Update user meta value

        Args:
            user_id: User ID
            key: Meta key
            value: Meta value

        Returns:
            True if successful
        """
        escaped_value = str(value).replace("'", "'\\''")
        cmd = f"user meta update {user_id} {key} '{escaped_value}'"
        self._execute_wp(cmd)
        logger.info(f"Updated meta {key} for user {user_id}")
        return True

    def delete_user_meta(self, user_id: int, key: str) -> bool:
        """
        Delete user meta

        Args:
            user_id: User ID
            key: Meta key

        Returns:
            True if successful
        """
        cmd = f"user meta delete {user_id} {key}"
        self._execute_wp(cmd)
        logger.info(f"Deleted meta {key} for user {user_id}")
        return True

    def flush_cache(self) -> bool:
        """
        Flush object cache

        Returns:
            True if successful
        """
        cmd = "cache flush"
        self._execute_wp(cmd)
        logger.info("Flushed cache")
        return True

    def get_cache_type(self) -> str:
        """
        Get cache type

        Returns:
            Cache type string
        """
        cmd = "cache type"
        result = self._execute_wp(cmd)
        return result.strip()

    def get_transient(self, key: str) -> str:
        """
        Get transient value

        Args:
            key: Transient key

        Returns:
            Transient value
        """
        cmd = f"transient get {key}"
        result = self._execute_wp(cmd)
        return result.strip()

    def set_transient(self, key: str, value: str, expiration: int = None) -> bool:
        """
        Set transient value

        Args:
            key: Transient key
            value: Transient value
            expiration: Expiration time in seconds (optional)

        Returns:
            True if successful
        """
        escaped_value = str(value).replace("'", "'\\''")
        cmd = f"transient set {key} '{escaped_value}'"
        if expiration:
            cmd += f" {expiration}"
        self._execute_wp(cmd)
        logger.info(f"Set transient {key}")
        return True

    def delete_transient(self, key: str) -> bool:
        """
        Delete transient

        Args:
            key: Transient key

        Returns:
            True if successful
        """
        cmd = f"transient delete {key}"
        self._execute_wp(cmd)
        logger.info(f"Deleted transient {key}")
        return True

    def list_menus(self) -> List[Dict[str, Any]]:
        """
        List navigation menus

        Returns:
            List of menu dictionaries
        """
        cmd = "menu list --format=json"
        result = self._execute_wp(cmd)
        return json.loads(result)

    def create_menu(self, name: str) -> int:
        """
        Create navigation menu

        Args:
            name: Menu name

        Returns:
            Menu ID
        """
        cmd = f"menu create '{name}' --porcelain"
        result = self._execute_wp(cmd)
        menu_id = int(result.strip())
        logger.info(f"Created menu {name} with ID {menu_id}")
        return menu_id

    def delete_menu(self, menu_id: int) -> bool:
        """
        Delete navigation menu

        Args:
            menu_id: Menu ID

        Returns:
            True if successful
        """
        cmd = f"menu delete {menu_id}"
        self._execute_wp(cmd)
        logger.info(f"Deleted menu {menu_id}")
        return True

    def add_menu_item(self, menu_id: int, **kwargs) -> int:
        """
        Add item to menu

        Args:
            menu_id: Menu ID
            **kwargs: Item properties (title, url, object-id, type, etc.)

        Returns:
            Menu item ID
        """
        args = []
        for key, value in kwargs.items():
            if isinstance(value, str):
                escaped_value = value.replace("'", "'\\''")
                args.append(f"--{key}='{escaped_value}'")
            else:
                args.append(f"--{key}={value}")

        cmd = f"menu item add-custom {menu_id} {' '.join(args)} --porcelain"
        result = self._execute_wp(cmd)
        item_id = int(result.strip())
        logger.info(f"Added menu item {item_id} to menu {menu_id}")
        return item_id

    def create_term(self, taxonomy: str, name: str, **kwargs) -> int:
        """
        Create a new term

        Args:
            taxonomy: Taxonomy name (category, post_tag, etc.)
            name: Term name
            **kwargs: Additional options (slug, description, parent, etc.)

        Returns:
            Term ID
        """
        args = []
        for key, value in kwargs.items():
            if isinstance(value, str):
                escaped_value = value.replace("'", "'\\''")
                args.append(f"--{key}='{escaped_value}'")
            else:
                args.append(f"--{key}={value}")

        escaped_name = name.replace("'", "'\\''")
        cmd = f"term create {taxonomy} '{escaped_name}' {' '.join(args)} --porcelain"
        result = self._execute_wp(cmd)
        term_id = int(result.strip())
        logger.info(f"Created term {name} in {taxonomy} with ID {term_id}")
        return term_id

    def delete_term(self, taxonomy: str, term_id: int) -> bool:
        """
        Delete a term

        Args:
            taxonomy: Taxonomy name
            term_id: Term ID

        Returns:
            True if successful
        """
        cmd = f"term delete {taxonomy} {term_id}"
        self._execute_wp(cmd)
        logger.info(f"Deleted term {term_id} from {taxonomy}")
        return True

    def update_term(self, taxonomy: str, term_id: int, **kwargs) -> bool:
        """
        Update a term

        Args:
            taxonomy: Taxonomy name
            term_id: Term ID
            **kwargs: Fields to update (name, slug, description, parent, etc.)

        Returns:
            True if successful
        """
        args = []
        for key, value in kwargs.items():
            if isinstance(value, str):
                escaped_value = value.replace("'", "'\\''")
                args.append(f"--{key}='{escaped_value}'")
            else:
                args.append(f"--{key}={value}")

        cmd = f"term update {taxonomy} {term_id} {' '.join(args)}"
        self._execute_wp(cmd)
        logger.info(f"Updated term {term_id} in {taxonomy}")
        return True

    def get_core_version(self) -> str:
        """
        Get WordPress core version

        Returns:
            WordPress version string
        """
        cmd = "core version"
        result = self._execute_wp(cmd)
        return result.strip()

    def core_is_installed(self) -> bool:
        """
        Check if WordPress is installed

        Returns:
            True if WordPress is installed
        """
        try:
            cmd = "core is-installed"
            self._execute_wp(cmd)
            return True
        except Exception:
            return False

    def import_media(self, file_path: str, post_id: int = None, **kwargs) -> int:
        """
        Import media file to WordPress

        Args:
            file_path: Path to media file
            post_id: Post ID to attach to (optional)
            **kwargs: Additional options (title, caption, alt, desc, etc.)

        Returns:
            Attachment ID
        """
        args = [f"'{file_path}'"]

        if post_id is not None:
            args.append(f"--post_id={post_id}")

        for key, value in kwargs.items():
            escaped_value = str(value).replace("'", "'\\''")
            args.append(f"--{key}='{escaped_value}'")

        args.append("--porcelain")

        cmd = f"media import {' '.join(args)}"
        result = self._execute_wp(cmd)
        attachment_id = int(result.strip())
        logger.info(f"Imported media {file_path} with ID {attachment_id}")
        return attachment_id

    def get_media_info(self, attachment_id: int, field: Optional[str] = None) -> Any:
        """
        Get media/attachment information

        Args:
            attachment_id: Attachment ID
            field: Specific field to retrieve (guid, post_title, post_mime_type, etc.)

        Returns:
            Attachment data (dict if no field specified, str if field specified)
        """
        return self.get_post(attachment_id, field=field)

    def get_media_url(self, attachment_id: int) -> str:
        """
        Get media URL

        Args:
            attachment_id: Attachment ID

        Returns:
            Media URL
        """
        url = self.get_post(attachment_id, field='guid')
        logger.info(f"Retrieved URL for attachment {attachment_id}: {url}")
        return url.strip()

    def list_media(self, post_id: int = None, **filters) -> List[Dict[str, Any]]:
        """
        List media/attachments

        Args:
            post_id: Filter by parent post ID (optional)
            **filters: Additional filters (mime_type, etc.)

        Returns:
            List of attachment dictionaries
        """
        list_filters = {'post_type': 'attachment'}

        if post_id is not None:
            list_filters['post_parent'] = post_id

        list_filters.update(filters)

        return self.list_posts(**list_filters)

    def list_comments(self, **filters) -> List[Dict[str, Any]]:
        """
        List comments with filters

        Args:
            **filters: Filters (status, post_id, etc.)

        Returns:
            List of comment dictionaries
        """
        args = ["--format=json"]

        for key, value in filters.items():
            args.append(f"--{key}={value}")

        cmd = f"comment list {' '.join(args)}"
        result = self._execute_wp(cmd)

        return json.loads(result)

    def get_comment(self, comment_id: int) -> Dict[str, Any]:
        """
        Get comment details

        Args:
            comment_id: Comment ID

        Returns:
            Comment dictionary
        """
        cmd = f"comment get {comment_id} --format=json"
        result = self._execute_wp(cmd)

        return json.loads(result)

    def create_comment(self, post_id: int, **kwargs) -> int:
        """
        Create a new comment

        Args:
            post_id: Post ID
            **kwargs: Comment fields (comment_content, comment_author, etc.)

        Returns:
            Comment ID
        """
        args = [str(post_id)]

        for key, value in kwargs.items():
            escaped_value = str(value).replace("'", "'\\''")
            args.append(f"--{key}='{escaped_value}'")

        args.append("--porcelain")

        cmd = f"comment create {' '.join(args)}"
        result = self._execute_wp(cmd)
        comment_id = int(result.strip())
        logger.info(f"Created comment {comment_id} on post {post_id}")
        return comment_id

    def update_comment(self, comment_id: int, **kwargs) -> bool:
        """
        Update comment fields

        Args:
            comment_id: Comment ID
            **kwargs: Comment fields to update

        Returns:
            True if successful
        """
        args = [str(comment_id)]

        for key, value in kwargs.items():
            escaped_value = str(value).replace("'", "'\\''")
            args.append(f"--{key}='{escaped_value}'")

        cmd = f"comment update {' '.join(args)}"
        self._execute_wp(cmd)
        logger.info(f"Updated comment {comment_id}")
        return True

    def delete_comment(self, comment_id: int, force: bool = False) -> bool:
        """
        Delete a comment

        Args:
            comment_id: Comment ID
            force: Bypass trash and force deletion

        Returns:
            True if successful
        """
        args = [str(comment_id)]

        if force:
            args.append("--force")

        cmd = f"comment delete {' '.join(args)}"
        self._execute_wp(cmd)
        logger.info(f"Deleted comment {comment_id}")
        return True

    def approve_comment(self, comment_id: int) -> bool:
        """
        Approve a comment

        Args:
            comment_id: Comment ID

        Returns:
            True if successful
        """
        cmd = f"comment approve {comment_id}"
        self._execute_wp(cmd)
        logger.info(f"Approved comment {comment_id}")
        return True

    def list_posts(
        self,
        post_type: str = 'post',
        **filters
    ) -> List[Dict[str, Any]]:
        """
        List posts with filters

        Args:
            post_type: Post type (default: 'post')
            **filters: Additional filters (post_status, etc.)

        Returns:
            List of post dictionaries
        """
        args = [f"--post_type={post_type}", "--format=json"]

        for key, value in filters.items():
            args.append(f"--{key}={value}")

        cmd = f"post list {' '.join(args)}"
        result = self._execute_wp(cmd)

        return json.loads(result)

    def db_query(self, query: str) -> str:
        """
        Execute database query

        Args:
            query: SQL query

        Returns:
            Query result as JSON string
        """
        # Escape query for shell
        escaped_query = query.replace('"', '\\"').replace('$', '\\$')
        cmd = f'db query "{escaped_query}" --format=json'

        return self._execute_wp(cmd)

    def search_replace(
        self,
        old: str,
        new: str,
        tables: Optional[List[str]] = None,
        dry_run: bool = False
    ) -> str:
        """
        Search and replace in database

        Args:
            old: Text to find
            new: Replacement text
            tables: Tables to search (optional)
            dry_run: Preview changes without applying

        Returns:
            Command output
        """
        cmd = f"search-replace '{old}' '{new}'"

        if tables:
            cmd += f" {' '.join(tables)}"

        if dry_run:
            cmd += " --dry-run"

        return self._execute_wp(cmd)

    def set_post_categories(self, post_id: int, category_ids: List[int]) -> bool:
        """
        Set post categories (replace all existing)

        Args:
            post_id: Post ID
            category_ids: List of category IDs

        Returns:
            True if successful
        """
        if not category_ids:
            logger.warning("No category IDs provided")
            return False

        # Join category IDs with comma
        cat_ids_str = ','.join(map(str, category_ids))
        cmd = f"post update {post_id} --post_category={cat_ids_str}"

        try:
            self._execute_wp(cmd)
            logger.info(f"Set categories {cat_ids_str} for post {post_id}")
        except WPCLIError as e:
            # WP-CLI sometimes reports "Term doesn't exist" but still sets the category
            # Verify if categories were actually set
            if "Term doesn't exist" in str(e):
                post_data = self.get_post(post_id)
                if post_data and 'post_category' in str(post_data):
                    logger.info(f"Categories {cat_ids_str} set successfully (ignoring WP-CLI warning)")
                    return True
            # Re-raise if it's a real error
            raise

        return True

    def add_post_category(self, post_id: int, category_id: int) -> bool:
        """
        Add a category to post (append)

        Args:
            post_id: Post ID
            category_id: Category ID to add

        Returns:
            True if successful
        """
        cmd = f"post term add {post_id} category {category_id}"

        self._execute_wp(cmd)
        logger.info(f"Added category {category_id} to post {post_id}")

        return True

    def remove_post_category(self, post_id: int, category_id: int) -> bool:
        """
        Remove a category from post

        Args:
            post_id: Post ID
            category_id: Category ID to remove

        Returns:
            True if successful
        """
        cmd = f"post term remove {post_id} category {category_id}"

        self._execute_wp(cmd)
        logger.info(f"Removed category {category_id} from post {post_id}")

        return True

    def list_categories(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all categories

        Args:
            search: Optional search query

        Returns:
            List of category dictionaries
        """
        cmd = "term list category --format=json --fields=term_id,name,slug,parent,count"

        if search:
            escaped_search = search.replace('"', '\\"')
            cmd += f' --search="{escaped_search}"'

        result = self._execute_wp(cmd)
        categories = json.loads(result)

        logger.debug(f"Found {len(categories)} categories")
        return categories

    def get_post_categories(self, post_id: int) -> List[Dict[str, Any]]:
        """
        Get categories for a specific post

        Args:
            post_id: Post ID

        Returns:
            List of category dictionaries
        """
        cmd = f"post term list {post_id} category --format=json --fields=term_id,name,slug,parent"

        result = self._execute_wp(cmd)
        categories = json.loads(result)

        logger.debug(f"Post {post_id} has {len(categories)} categories")
        return categories

    def get_category_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get category by name or slug

        Args:
            name: Category name or slug

        Returns:
            Category dictionary or None
        """
        try:
            # Try to get by slug first
            cmd = f"term get category '{name}' --format=json --fields=term_id,name,slug,parent"
            result = self._execute_wp(cmd)
            category = json.loads(result)

            logger.debug(f"Found category: {category}")
            return category
        except WPCLIError:
            # If not found by slug, search by name
            categories = self.list_categories(search=name)

            # Find exact match (case-insensitive)
            for cat in categories:
                if cat['name'].lower() == name.lower() or cat['slug'].lower() == name.lower():
                    return cat

            logger.warning(f"Category '{name}' not found")
            return None

    def get_category_by_id(self, category_id: int) -> Optional[Dict[str, Any]]:
        """
        Get category by ID

        Args:
            category_id: Category ID

        Returns:
            Category dictionary or None
        """
        try:
            cmd = f"term get category {category_id} --format=json --fields=term_id,name,slug,parent"
            result = self._execute_wp(cmd)
            category = json.loads(result)

            logger.debug(f"Found category: {category}")
            return category
        except WPCLIError:
            logger.warning(f"Category ID {category_id} not found")
            return None

    def get_config_param(self, param: str) -> Optional[str]:
        """
        Get WordPress configuration parameter

        Args:
            param: Configuration parameter name

        Returns:
            Parameter value or None
        """
        try:
            cmd = f"config get {param}"
            result = self._execute_wp(cmd)
            value = result.strip()

            logger.debug(f"Retrieved config {param}: {value}")
            return value if value else None
        except WPCLIError:
            logger.warning(f"Config parameter '{param}' not found")
            return None

    def set_config_param(self, param: str, value: str) -> bool:
        """
        Set WordPress configuration parameter

        Args:
            param: Configuration parameter name
            value: Parameter value

        Returns:
            True if successful, False otherwise
        """
        try:
            # Escape the value for shell
            escaped_value = value.replace("'", "'\\''")
            cmd = f"config set {param} '{escaped_value}'"
            self._execute_wp(cmd)

            logger.info(f"Set config {param} = {value}")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to set config {param}: {e}")
            return False

    def get_all_config(self) -> Dict[str, str]:
        """
        Get all WordPress configuration parameters

        Returns:
            Dictionary of all config parameters
        """
        try:
            cmd = "config list --format=json"
            result = self._execute_wp(cmd)
            config_data = json.loads(result)

            logger.debug(f"Retrieved {len(config_data)} config parameters")
            return config_data
        except WPCLIError as e:
            logger.error(f"Failed to get all config: {e}")
            return {}

    def create_config(self, params: Dict[str, str], force: bool = False) -> bool:
        """
        Create WordPress wp-config.php file

        Args:
            params: Configuration parameters
            force: Whether to overwrite existing config

        Returns:
            True if successful, False otherwise
        """
        try:
            # Build config creation command
            cmd_parts = ["config create"]

            if force:
                cmd_parts.append("--force")

            # Add parameters
            for key, value in params.items():
                if key.startswith('$'):
                    # Special parameters like $table_prefix
                    escaped_value = value.replace("'", "'\\''")
                    cmd_parts.append(f"--{key}='{escaped_value}'")
                else:
                    escaped_value = value.replace("'", "'\\''")
                    cmd_parts.append(f"--{key}='{escaped_value}'")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info("Created wp-config.php successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to create config: {e}")
            return False

    def get_config_path(self) -> Optional[str]:
        """
        Get WordPress configuration file path

        Returns:
            Config file path or None
        """
        try:
            cmd = "config path"
            result = self._execute_wp(cmd)
            path = result.strip()

            logger.debug(f"Config path: {path}")
            return path if path else None
        except WPCLIError:
            logger.warning("Could not get config path")
            return None

    def update_core(self, version: Optional[str] = None, force: bool = False) -> bool:
        """
        Update WordPress core

        Args:
            version: Specific version to update to (None for latest)
            force: Force update even if already up to date

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["core", "update"]

            if version:
                cmd_parts.append(f"--version={version}")

            if force:
                cmd_parts.append("--force")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"Updated WordPress core to version {version or 'latest'}")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to update WordPress core: {e}")
            return False

    def download_core(self, version: Optional[str] = None, path: Optional[str] = None) -> Optional[str]:
        """
        Download WordPress core

        Args:
            version: Specific version to download (None for latest)
            path: Download path (None for default)

        Returns:
            Download path or None if failed
        """
        try:
            cmd_parts = ["core", "download"]

            if version:
                cmd_parts.append(f"--version={version}")

            if path:
                cmd_parts.append(f"--path={path}")

            cmd = " ".join(cmd_parts)
            result = self._execute_wp(cmd)

            # Extract download path from result
            download_path = result.strip()
            logger.info(f"Downloaded WordPress core to {download_path}")
            return download_path
        except WPCLIError as e:
            logger.error(f"Failed to download WordPress core: {e}")
            return None

    def install_core(self, version: Optional[str] = None, force: bool = False) -> bool:
        """
        Install WordPress core

        Args:
            version: Specific version to install (None for latest)
            force: Force installation even if WordPress exists

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["core", "install"]

            if version:
                cmd_parts.append(f"--version={version}")

            if force:
                cmd_parts.append("--force")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"Installed WordPress core version {version or 'latest'}")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to install WordPress core: {e}")
            return False

    def verify_core(self) -> bool:
        """
        Verify WordPress core files

        Returns:
            True if valid, False otherwise
        """
        try:
            cmd = "core verify-checksums"
            self._execute_wp(cmd)

            logger.info("WordPress core files are valid")
            return True
        except WPCLIError as e:
            logger.error(f"WordPress core files are invalid: {e}")
            return False

    def check_core_update(self) -> Optional[Dict[str, Any]]:
        """
        Check for WordPress core updates

        Returns:
            Update information dictionary or None
        """
        try:
            cmd = "core check-update --format=json"
            result = self._execute_wp(cmd)

            if result.strip():
                update_info = json.loads(result)
                logger.debug(f"Core update info: {update_info}")
                return update_info
            else:
                logger.info("WordPress is up to date")
                return {}
        except WPCLIError as e:
            logger.error(f"Failed to check core updates: {e}")
            return None

    def list_cron_events(self) -> List[Dict[str, Any]]:
        """
        List WordPress cron events

        Returns:
            List of cron event dictionaries
        """
        try:
            cmd = "cron event list --format=json"
            result = self._execute_wp(cmd)
            events = json.loads(result)

            logger.debug(f"Retrieved {len(events)} cron events")
            return events
        except WPCLIError as e:
            logger.error(f"Failed to list cron events: {e}")
            return []

    def run_cron(self) -> bool:
        """
        Run WordPress cron events

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = "cron event run --due-now"
            self._execute_wp(cmd)

            logger.info("Executed cron events")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to run cron events: {e}")
            return False

    def schedule_cron_event(self, hook: str, recurrence: str, time: Optional[str] = None, args: Optional[str] = None) -> bool:
        """
        Schedule a WordPress cron event

        Args:
            hook: Hook name
            recurrence: Schedule recurrence
            time: Time for daily/twicedaily schedules
            args: Arguments to pass to hook

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["cron", "event", "schedule", hook, f"--recurrence={recurrence}"]

            if time:
                cmd_parts.append(f"--time={time}")

            if args:
                cmd_parts.append(f"--args={args}")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"Scheduled cron event '{hook}' with recurrence '{recurrence}'")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to schedule cron event: {e}")
            return False

    def delete_cron_event(self, hook: str) -> bool:
        """
        Delete a WordPress cron event

        Args:
            hook: Hook name to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = f"cron event delete {hook}"
            self._execute_wp(cmd)

            logger.info(f"Deleted cron event '{hook}'")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to delete cron event: {e}")
            return False

    def test_cron(self) -> bool:
        """
        Test WordPress cron system

        Returns:
            True if working, False otherwise
        """
        try:
            cmd = "cron test"
            result = self._execute_wp(cmd)

            # Check if cron is working
            if "SUCCESS" in result or "working" in result.lower():
                logger.info("WordPress cron system is working")
                return True
            else:
                logger.warning("WordPress cron system is not working")
                return False
        except WPCLIError as e:
            logger.error(f"Failed to test cron system: {e}")
            return False

    def list_taxonomies(self) -> List[Dict[str, Any]]:
        """
        List WordPress taxonomies

        Returns:
            List of taxonomy dictionaries
        """
        try:
            cmd = "taxonomy list --format=json"
            result = self._execute_wp(cmd)
            taxonomies = json.loads(result)

            logger.debug(f"Retrieved {len(taxonomies)} taxonomies")
            return taxonomies
        except WPCLIError as e:
            logger.error(f"Failed to list taxonomies: {e}")
            return []

    def get_taxonomy(self, taxonomy: str) -> Optional[Dict[str, Any]]:
        """
        Get WordPress taxonomy information

        Args:
            taxonomy: Taxonomy name

        Returns:
            Taxonomy dictionary or None
        """
        try:
            cmd = f"taxonomy get {taxonomy} --format=json"
            result = self._execute_wp(cmd)
            taxonomy_info = json.loads(result)

            logger.debug(f"Retrieved taxonomy info for {taxonomy}")
            return taxonomy_info
        except WPCLIError:
            logger.warning(f"Taxonomy '{taxonomy}' not found")
            return None

    def list_terms(self, taxonomy: str) -> List[Dict[str, Any]]:
        """
        List WordPress taxonomy terms

        Args:
            taxonomy: Taxonomy name

        Returns:
            List of term dictionaries
        """
        try:
            cmd = f"term list {taxonomy} --format=json"
            result = self._execute_wp(cmd)
            terms = json.loads(result)

            logger.debug(f"Retrieved {len(terms)} terms for {taxonomy}")
            return terms
        except WPCLIError as e:
            logger.error(f"Failed to list terms for {taxonomy}: {e}")
            return []

    def get_term(self, taxonomy: str, term_id: str) -> Optional[Dict[str, Any]]:
        """
        Get WordPress taxonomy term information

        Args:
            taxonomy: Taxonomy name
            term_id: Term ID

        Returns:
            Term dictionary or None
        """
        try:
            cmd = f"term get {taxonomy} {term_id} --format=json"
            result = self._execute_wp(cmd)
            term_info = json.loads(result)

            logger.debug(f"Retrieved term info for {term_id} in {taxonomy}")
            return term_info
        except WPCLIError:
            logger.warning(f"Term '{term_id}' not found in taxonomy '{taxonomy}'")
            return None



    def list_widgets(self) -> List[Dict[str, Any]]:
        """
        List WordPress widgets

        Returns:
            List of widget dictionaries
        """
        try:
            cmd = "widget list --format=json"
            result = self._execute_wp(cmd)
            widgets = json.loads(result)

            logger.debug(f"Retrieved {len(widgets)} widgets")
            return widgets
        except WPCLIError as e:
            logger.error(f"Failed to list widgets: {e}")
            return []

    def get_widget(self, widget_id: str) -> Optional[Dict[str, Any]]:
        """
        Get WordPress widget information

        Args:
            widget_id: Widget ID

        Returns:
            Widget dictionary or None
        """
        try:
            cmd = f"widget get {widget_id} --format=json"
            result = self._execute_wp(cmd)
            widget_info = json.loads(result)

            logger.debug(f"Retrieved widget info for {widget_id}")
            return widget_info
        except WPCLIError:
            logger.warning(f"Widget '{widget_id}' not found")
            return None

    def update_widget(self, widget_id: str, options: Dict[str, str]) -> bool:
        """
        Update a WordPress widget

        Args:
            widget_id: Widget ID
            options: Widget options to update

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["widget", "update", widget_id]

            # Add options
            for key, value in options.items():
                escaped_value = str(value).replace("'", "'\\''")
                cmd_parts.append(f"--{key}='{escaped_value}'")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"Updated widget '{widget_id}' with options: {list(options.keys())}")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to update widget: {e}")
            return False

    def list_roles(self) -> List[Dict[str, Any]]:
        """
        List WordPress user roles

        Returns:
            List of role dictionaries
        """
        try:
            cmd = "role list --format=json"
            result = self._execute_wp(cmd)
            roles = json.loads(result)

            logger.debug(f"Retrieved {len(roles)} roles")
            return roles
        except WPCLIError as e:
            logger.error(f"Failed to list roles: {e}")
            return []

    def get_role(self, role: str) -> Optional[Dict[str, Any]]:
        """
        Get WordPress role information

        Args:
            role: Role name

        Returns:
            Role dictionary or None
        """
        try:
            cmd = f"role get {role} --format=json"
            result = self._execute_wp(cmd)
            role_info = json.loads(result)

            logger.debug(f"Retrieved role info for {role}")
            return role_info
        except WPCLIError:
            logger.warning(f"Role '{role}' not found")
            return None

    def create_role(self, role_key: str, role_name: str, capabilities: Optional[str] = None) -> bool:
        """
        Create a WordPress user role

        Args:
            role_key: Role key/slug
            role_name: Role display name
            capabilities: Comma-separated list of capabilities

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["role", "create", role_key, f"'{role_name}'"]

            if capabilities:
                cmd_parts.append(f"--capabilities={capabilities}")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"Created role '{role_key}' with name '{role_name}'")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to create role: {e}")
            return False

    def delete_role(self, role: str) -> bool:
        """
        Delete a WordPress user role

        Args:
            role: Role name

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = f"role delete {role}"
            self._execute_wp(cmd)

            logger.info(f"Deleted role '{role}'")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to delete role: {e}")
            return False

    def scaffold_post_type(self, slug: str, label: Optional[str] = None,
                          public: Optional[str] = None, has_archive: Optional[str] = None,
                          supports: Optional[str] = None) -> bool:
        """
        Generate a custom post type

        Args:
            slug: Post type slug
            label: Post type label (optional)
            public: Whether public (optional)
            has_archive: Whether has archive (optional)
            supports: Supported features (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["scaffold", "post-type", slug]

            if label:
                cmd_parts.append(f"--label='{label}'")
            if public:
                cmd_parts.append(f"--public={public}")
            if has_archive:
                cmd_parts.append(f"--has_archive={has_archive}")
            if supports:
                cmd_parts.append(f"--supports={supports}")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"Generated post type '{slug}'")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to generate post type: {e}")
            return False

    def scaffold_taxonomy(self, slug: str, label: Optional[str] = None,
                         public: Optional[str] = None, hierarchical: Optional[str] = None,
                         post_types: Optional[str] = None) -> bool:
        """
        Generate a custom taxonomy

        Args:
            slug: Taxonomy slug
            label: Taxonomy label (optional)
            public: Whether public (optional)
            hierarchical: Whether hierarchical (optional)
            post_types: Associated post types (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["scaffold", "taxonomy", slug]

            if label:
                cmd_parts.append(f"--label='{label}'")
            if public:
                cmd_parts.append(f"--public={public}")
            if hierarchical:
                cmd_parts.append(f"--hierarchical={hierarchical}")
            if post_types:
                cmd_parts.append(f"--post_types={post_types}")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"Generated taxonomy '{slug}'")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to generate taxonomy: {e}")
            return False

    def scaffold_plugin(self, slug: str, plugin_name: Optional[str] = None,
                       plugin_uri: Optional[str] = None, author: Optional[str] = None) -> bool:
        """
        Generate a WordPress plugin

        Args:
            slug: Plugin slug
            plugin_name: Plugin name (optional)
            plugin_uri: Plugin URI (optional)
            author: Plugin author (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["scaffold", "plugin", slug]

            if plugin_name:
                cmd_parts.append(f"--plugin_name='{plugin_name}'")
            if plugin_uri:
                cmd_parts.append(f"--plugin_uri='{plugin_uri}'")
            if author:
                cmd_parts.append(f"--author='{author}'")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"Generated plugin '{slug}'")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to generate plugin: {e}")
            return False

    def scaffold_theme(self, slug: str, theme_name: Optional[str] = None,
                      theme_uri: Optional[str] = None, author: Optional[str] = None,
                      author_uri: Optional[str] = None) -> bool:
        """
        Generate a WordPress theme

        Args:
            slug: Theme slug
            theme_name: Theme name (optional)
            theme_uri: Theme URI (optional)
            author: Theme author (optional)
            author_uri: Author URI (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["scaffold", "theme", slug]

            if theme_name:
                cmd_parts.append(f"--theme_name='{theme_name}'")
            if theme_uri:
                cmd_parts.append(f"--theme_uri='{theme_uri}'")
            if author:
                cmd_parts.append(f"--author='{author}'")
            if author_uri:
                cmd_parts.append(f"--author_uri='{author_uri}'")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"Generated theme '{slug}'")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to generate theme: {e}")
            return False

    def start_server(self, host: str = "localhost", port: int = 8080,
                    config: Optional[str] = None, docroot: Optional[str] = None) -> str:
        """
        Start PHP development server

        Args:
            host: Host to bind to (default: localhost)
            port: Port to bind to (default: 8080)
            config: Path to PHP configuration file (optional)
            docroot: Document root path (optional)

        Returns:
            Server URL if successful, None otherwise
        """
        try:
            cmd_parts = ["server", f"--host={host}", f"--port={port}"]

            if config:
                cmd_parts.append(f"--config={config}")
            if docroot:
                cmd_parts.append(f"--docroot={docroot}")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"Started development server at http://{host}:{port}")
            return f"http://{host}:{port}"
        except WPCLIError as e:
            logger.error(f"Failed to start server: {e}")
            return None

    def open_shell(self) -> str:
        """
        Open interactive PHP shell

        Returns:
            Shell prompt string if successful, None otherwise
        """
        try:
            cmd = "shell"
            self._execute_wp(cmd)

            logger.info("Opened PHP shell")
            return "wp>"
        except WPCLIError as e:
            logger.error(f"Failed to open shell: {e}")
            return None

    def db_optimize(self) -> bool:
        """
        Optimize database

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = "db optimize"
            self._execute_wp(cmd)
            logger.info("Database optimized successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to optimize database: {e}")
            return False

    def db_repair(self) -> bool:
        """
        Repair database

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = "db repair"
            self._execute_wp(cmd)
            logger.info("Database repaired successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to repair database: {e}")
            return False

    def db_check(self) -> Dict[str, Any]:
        """
        Check database status

        Returns:
            Dictionary with database check results
        """
        try:
            cmd = "db check --format=json"
            result = self._execute_wp(cmd)

            import json
            check_data = json.loads(result)

            logger.info("Database check completed")
            return check_data
        except WPCLIError as e:
            logger.error(f"Failed to check database: {e}")
            return {"error": str(e)}

    def cache_flush(self, cache_type: Optional[str] = None) -> bool:
        """
        Flush WordPress cache

        Args:
            cache_type: Specific cache type to flush (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["cache", "flush"]
            if cache_type:
                cmd_parts.append(f"--{cache_type}")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info("Cache flushed successfully" + (f" ({cache_type})" if cache_type else ""))
            return True
        except WPCLIError as e:
            logger.error(f"Failed to flush cache: {e}")
            return False

    def cache_add(self, key: str, value: str, group: Optional[str] = None,
                  expire: Optional[int] = None) -> bool:
        """
        Add item to cache

        Args:
            key: Cache key
            value: Cache value
            group: Cache group (optional)
            expire: Expiration time in seconds (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["cache", "add", key, f"'{value}'"]

            if group:
                cmd_parts.append(f"--group={group}")
            if expire:
                cmd_parts.append(f"--expire={expire}")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"Cache item '{key}' added successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to add cache item: {e}")
            return False

    def cache_get(self, key: str, group: Optional[str] = None) -> Optional[str]:
        """
        Get item from cache

        Args:
            key: Cache key
            group: Cache group (optional)

        Returns:
            Cache value or None
        """
        try:
            cmd_parts = ["cache", "get", key]

            if group:
                cmd_parts.append(f"--group={group}")

            cmd = " ".join(cmd_parts)
            result = self._execute_wp(cmd)

            value = result.strip()
            return value if value else None
        except WPCLIError:
            return None

    def cache_delete(self, key: str, group: Optional[str] = None) -> bool:
        """
        Delete item from cache

        Args:
            key: Cache key
            group: Cache group (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["cache", "delete", key]

            if group:
                cmd_parts.append(f"--group={group}")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"Cache item '{key}' deleted successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to delete cache item: {e}")
            return False

    def cache_list(self, group: Optional[str] = None) -> Dict[str, Any]:
        """
        List cache items

        Args:
            group: Cache group (optional)

        Returns:
            Dictionary with cache items
        """
        try:
            cmd_parts = ["cache", "list", "--format=json"]

            if group:
                cmd_parts.append(f"--group={group}")

            cmd = " ".join(cmd_parts)
            result = self._execute_wp(cmd)

            import json
            cache_data = json.loads(result)

            logger.info("Cache list retrieved successfully")
            return cache_data
        except WPCLIError as e:
            logger.error(f"Failed to list cache: {e}")
            return {"error": str(e)}

    def rewrite_list(self, format_type: str = "table") -> Dict[str, Any]:
        """
        List WordPress rewrite rules

        Args:
            format_type: Output format (table, json)

        Returns:
            Dictionary with rewrite rules
        """
        try:
            cmd = f"rewrite list --format={format_type}"
            result = self._execute_wp(cmd)

            if format_type == "json":
                import json
                rewrite_data = json.loads(result)
            else:
                # Parse table format
                lines = result.strip().split('\n')
                rewrite_data = {"rules": []}
                for line in lines[2:]:  # Skip header lines
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            rewrite_data["rules"].append({
                                "match": parts[0],
                                "source": parts[1],
                                "query": " ".join(parts[2:]) if len(parts) > 2 else ""
                            })

            logger.info("Rewrite rules listed successfully")
            return rewrite_data
        except WPCLIError as e:
            logger.error(f"Failed to list rewrite rules: {e}")
            return {"error": str(e)}

    def rewrite_flush(self) -> bool:
        """
        Flush WordPress rewrite rules

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = "rewrite flush"
            self._execute_wp(cmd)

            logger.info("Rewrite rules flushed successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to flush rewrite rules: {e}")
            return False

    def rewrite_structure(self, structure: str, category_base: Optional[str] = None,
                          tag_base: Optional[str] = None) -> bool:
        """
        Update permalink structure

        Args:
            structure: Permalink structure
            category_base: Category base (optional)
            tag_base: Tag base (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["rewrite", "structure", f"'{structure}'"]

            if category_base:
                cmd_parts.append(f"--category-base='{category_base}'")
            if tag_base:
                cmd_parts.append(f"--tag-base='{tag_base}'")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"Permalink structure updated to: {structure}")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to update permalink structure: {e}")
            return False

    def rewrite_get(self, rewrite_type: str) -> Optional[str]:
        """
        Get rewrite rule by type

        Args:
            rewrite_type: Type of rewrite rule

        Returns:
            Rewrite rule or None
        """
        try:
            cmd = f"rewrite get {rewrite_type}"
            result = self._execute_wp(cmd)

            rule = result.strip()
            return rule if rule else None
        except WPCLIError:
            return None

    def rewrite_set(self, rewrite_type: str, rule: str) -> bool:
        """
        Set rewrite rule

        Args:
            rewrite_type: Type of rewrite rule
            rule: Rewrite rule

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = f"rewrite set {rewrite_type} '{rule}'"
            self._execute_wp(cmd)

            logger.info(f"Rewrite rule '{rewrite_type}' set successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to set rewrite rule: {e}")
            return False

    def sidebar_list(self) -> Dict[str, Any]:
        """
        List WordPress sidebars

        Returns:
            Dictionary with sidebar information
        """
        try:
            cmd = "sidebar list --format=json"
            result = self._execute_wp(cmd)

            import json
            sidebar_data = json.loads(result)

            logger.info("Sidebars listed successfully")
            return sidebar_data
        except WPCLIError as e:
            logger.error(f"Failed to list sidebars: {e}")
            return {"error": str(e)}

    def sidebar_get(self, sidebar_id: str) -> Optional[Dict[str, Any]]:
        """
        Get sidebar information by ID

        Args:
            sidebar_id: Sidebar ID

        Returns:
            Sidebar information or None
        """
        try:
            cmd = f"sidebar get {sidebar_id} --format=json"
            result = self._execute_wp(cmd)

            import json
            sidebar_info = json.loads(result)

            logger.debug(f"Retrieved sidebar info for {sidebar_id}")
            return sidebar_info
        except WPCLIError:
            logger.warning(f"Sidebar '{sidebar_id}' not found")
            return None

    def sidebar_update(self, sidebar_id: str, widgets: List[str]) -> bool:
        """
        Update sidebar with widgets

        Args:
            sidebar_id: Sidebar ID
            widgets: List of widget IDs to add to sidebar

        Returns:
            True if successful, False otherwise
        """
        try:
            if not widgets:
                cmd = f"sidebar update {sidebar_id}"
            else:
                widget_list = ",".join(widgets)
                cmd = f"sidebar update {sidebar_id} --widgets={widget_list}"

            self._execute_wp(cmd)

            logger.info(f"Sidebar '{sidebar_id}' updated successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to update sidebar: {e}")
            return False

    def sidebar_add_widget(self, sidebar_id: str, widget_id: str, position: Optional[int] = None) -> bool:
        """
        Add widget to sidebar

        Args:
            sidebar_id: Sidebar ID
            widget_id: Widget ID to add
            position: Position in sidebar (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["sidebar", "add-widget", sidebar_id, widget_id]

            if position is not None:
                cmd_parts.append(f"--position={position}")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"Widget '{widget_id}' added to sidebar '{sidebar_id}' successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to add widget to sidebar: {e}")
            return False

    def sidebar_remove_widget(self, sidebar_id: str, widget_id: str) -> bool:
        """
        Remove widget from sidebar

        Args:
            sidebar_id: Sidebar ID
            widget_id: Widget ID to remove

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = f"sidebar remove-widget {sidebar_id} {widget_id}"
            self._execute_wp(cmd)

            logger.info(f"Widget '{widget_id}' removed from sidebar '{sidebar_id}' successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to remove widget from sidebar: {e}")
            return False

    def sidebar_empty(self, sidebar_id: str) -> bool:
        """
        Empty all widgets from sidebar

        Args:
            sidebar_id: Sidebar ID

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = f"sidebar empty {sidebar_id}"
            self._execute_wp(cmd)

            logger.info(f"Sidebar '{sidebar_id}' emptied successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to empty sidebar: {e}")
            return False

    def post_type_list(self, format_type: str = "table") -> Dict[str, Any]:
        """
        List WordPress post types

        Args:
            format_type: Output format (table, json)

        Returns:
            Dictionary with post type information
        """
        try:
            cmd = f"post-type list --format={format_type}"
            result = self._execute_wp(cmd)

            if format_type == "json":
                import json
                post_type_data = json.loads(result)
            else:
                # Parse table format
                lines = result.strip().split('\n')
                post_type_data = {"post_types": []}
                for line in lines[2:]:  # Skip header lines
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            post_type_data["post_types"].append({
                                "name": parts[0],
                                "description": " ".join(parts[1:]) if len(parts) > 1 else ""
                            })

            logger.info("Post types listed successfully")
            return post_type_data
        except WPCLIError as e:
            logger.error(f"Failed to list post types: {e}")
            return {"error": str(e)}

    def post_type_get(self, post_type: str) -> Optional[Dict[str, Any]]:
        """
        Get post type information by name

        Args:
            post_type: Post type name

        Returns:
            Post type information or None
        """
        try:
            cmd = f"post-type get {post_type} --format=json"
            result = self._execute_wp(cmd)

            import json
            post_type_info = json.loads(result)

            logger.debug(f"Retrieved post type info for {post_type}")
            return post_type_info
        except WPCLIError:
            logger.warning(f"Post type '{post_type}' not found")
            return None

    def post_type_create(self, post_type: str, label: str, slug: Optional[str] = None,
                        public: Optional[str] = None, has_archive: Optional[str] = None,
                        supports: Optional[str] = None) -> bool:
        """
        Create a new post type

        Args:
            post_type: Post type name
            label: Post type label
            slug: Post type slug (optional)
            public: Whether public (optional)
            has_archive: Whether has archive (optional)
            supports: Supported features (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["post-type", "create", post_type, f"'{label}'"]

            if slug:
                cmd_parts.append(f"--slug='{slug}'")
            if public:
                cmd_parts.append(f"--public='{public}'")
            if has_archive:
                cmd_parts.append(f"--has_archive='{has_archive}'")
            if supports:
                cmd_parts.append(f"--supports='{supports}'")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"Post type '{post_type}' created successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to create post type: {e}")
            return False

    def post_type_delete(self, post_type: str, force: bool = False) -> bool:
        """
        Delete a post type

        Args:
            post_type: Post type name
            force: Force deletion

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["post-type", "delete", post_type]
            if force:
                cmd_parts.append("--force")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"Post type '{post_type}' deleted successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to delete post type: {e}")
            return False

    def post_type_update(self, post_type: str, **kwargs) -> bool:
        """
        Update a post type

        Args:
            post_type: Post type name
            **kwargs: Fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["post-type", "update", post_type]

            for key, value in kwargs.items():
                if value is not None:
                    escaped_value = str(value).replace("'", "'\\''")
                    cmd_parts.append(f"--{key}='{escaped_value}'")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"Post type '{post_type}' updated successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to update post type: {e}")
            return False

    def site_list(self, format_type: str = "table") -> Dict[str, Any]:
        """
        List WordPress multisite sites

        Args:
            format_type: Output format (table, json)

        Returns:
            Dictionary with site information
        """
        try:
            cmd = f"site list --format={format_type}"
            result = self._execute_wp(cmd)

            if format_type == "json":
                import json
                site_data = json.loads(result)
            else:
                # Parse table format
                lines = result.strip().split('\n')
                site_data = {"sites": []}
                for line in lines[2:]:  # Skip header lines
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            site_data["sites"].append({
                                "blog_id": parts[0],
                                "url": parts[1],
                                "last_updated": parts[2] if len(parts) > 2 else "",
                                "registered": parts[3] if len(parts) > 3 else ""
                            })

            logger.info("Sites listed successfully")
            return site_data
        except WPCLIError as e:
            logger.error(f"Failed to list sites: {e}")
            return {"error": str(e)}

    def site_get(self, site_id: str) -> Optional[Dict[str, Any]]:
        """
        Get site information by ID

        Args:
            site_id: Site ID or URL

        Returns:
            Site information or None
        """
        try:
            cmd = f"site get {site_id} --format=json"
            result = self._execute_wp(cmd)

            import json
            site_info = json.loads(result)

            logger.debug(f"Retrieved site info for {site_id}")
            return site_info
        except WPCLIError:
            logger.warning(f"Site '{site_id}' not found")
            return None

    def site_create(self, url: str, title: str, email: str,
                   site_id: Optional[str] = None,
                   private: Optional[bool] = None) -> bool:
        """
        Create a new site in multisite

        Args:
            url: Site URL
            title: Site title
            email: Admin email
            site_id: Site ID (optional)
            private: Whether private (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["site", "create", url, f"'{title}'", email]

            if site_id:
                cmd_parts.append(f"--site_id={site_id}")
            if private is not None:
                cmd_parts.append(f"--private={'true' if private else 'false'}")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"Site '{url}' created successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to create site: {e}")
            return False

    def site_delete(self, site_id: str, keep_tables: bool = False) -> bool:
        """
        Delete a site from multisite

        Args:
            site_id: Site ID or URL
            keep_tables: Whether to keep database tables

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["site", "delete", site_id]
            if keep_tables:
                cmd_parts.append("--keep-tables")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"Site '{site_id}' deleted successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to delete site: {e}")
            return False

    def site_update(self, site_id: str, **kwargs) -> bool:
        """
        Update a site in multisite

        Args:
            site_id: Site ID or URL
            **kwargs: Fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["site", "update", site_id]

            for key, value in kwargs.items():
                if value is not None:
                    escaped_value = str(value).replace("'", "'\\''")
                    cmd_parts.append(f"--{key}='{escaped_value}'")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"Site '{site_id}' updated successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to update site: {e}")
            return False

    def site_activate(self, site_id: str) -> bool:
        """
        Activate a site theme/plugins

        Args:
            site_id: Site ID or URL

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = f"site activate {site_id}"
            self._execute_wp(cmd)

            logger.info(f"Site '{site_id}' activated successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to activate site: {e}")
            return False

    def site_deactivate(self, site_id: str) -> bool:
        """
        Deactivate a site theme/plugins

        Args:
            site_id: Site ID or URL

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = f"site deactivate {site_id}"
            self._execute_wp(cmd)

            logger.info(f"Site '{site_id}' deactivated successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to deactivate site: {e}")
            return False

    def site_archive(self, site_id: str) -> bool:
        """
        Archive a site

        Args:
            site_id: Site ID or URL

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = f"site archive {site_id}"
            self._execute_wp(cmd)

            logger.info(f"Site '{site_id}' archived successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to archive site: {e}")
            return False

    def site_unarchive(self, site_id: str) -> bool:
        """
        Unarchive a site

        Args:
            site_id: Site ID or URL

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = f"site unarchive {site_id}"
            self._execute_wp(cmd)

            logger.info(f"Site '{site_id}' unarchived successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to unarchive site: {e}")
            return False

    def site_spam(self, site_id: str) -> bool:
        """
        Mark a site as spam

        Args:
            site_id: Site ID or URL

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = f"site spam {site_id}"
            self._execute_wp(cmd)

            logger.info(f"Site '{site_id}' marked as spam successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to mark site as spam: {e}")
            return False

    def site_unspam(self, site_id: str) -> bool:
        """
        Unmark a site as spam

        Args:
            site_id: Site ID or URL

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = f"site unspam {site_id}"
            self._execute_wp(cmd)

            logger.info(f"Site '{site_id}' unmarked as spam successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to unmark site as spam: {e}")
            return False

    def network_meta_get(self, meta_key: str) -> Optional[str]:
        """
        Get WordPress multisite network meta value

        Args:
            meta_key: Meta key to retrieve

        Returns:
            Meta value or None
        """
        try:
            cmd = f"network meta get {meta_key}"
            result = self._execute_wp(cmd)
            value = result.strip()
            return value if value else None
        except WPCLIError:
            logger.warning(f"Network meta key '{meta_key}' not found")
            return None

    def network_meta_set(self, meta_key: str, meta_value: str) -> bool:
        """
        Set WordPress multisite network meta value

        Args:
            meta_key: Meta key to set
            meta_value: Meta value to set

        Returns:
            True if successful, False otherwise
        """
        try:
            escaped_value = meta_value.replace("'", "'\\''")
            cmd = f"network meta set {meta_key} '{escaped_value}'"
            self._execute_wp(cmd)

            logger.info(f"Network meta '{meta_key}' set successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to set network meta: {e}")
            return False

    def network_meta_delete(self, meta_key: str) -> bool:
        """
        Delete WordPress multisite network meta

        Args:
            meta_key: Meta key to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = f"network meta delete {meta_key}"
            self._execute_wp(cmd)

            logger.info(f"Network meta '{meta_key}' deleted successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to delete network meta: {e}")
            return False

    def network_meta_list(self, format_type: str = "table") -> Dict[str, Any]:
        """
        List WordPress multisite network meta

        Args:
            format_type: Output format (table, json)

        Returns:
            Dictionary with network meta information
        """
        try:
            cmd = f"network meta list --format={format_type}"
            result = self._execute_wp(cmd)

            if format_type == "json":
                import json
                meta_data = json.loads(result)
            else:
                # Parse table format
                lines = result.strip().split('\n')
                meta_data = {"meta": []}
                for line in lines[2:]:  # Skip header lines
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            meta_data["meta"].append({
                                "meta_id": parts[0],
                                "meta_key": parts[1],
                                "meta_value": " ".join(parts[2:]) if len(parts) > 2 else ""
                            })

            logger.info("Network meta listed successfully")
            return meta_data
        except WPCLIError as e:
            logger.error(f"Failed to list network meta: {e}")
            return {"error": str(e)}

    def network_option_get(self, option_name: str) -> Optional[str]:
        """
        Get WordPress multisite network option value

        Args:
            option_name: Option name to retrieve

        Returns:
            Option value or None
        """
        try:
            cmd = f"network option get {option_name}"
            result = self._execute_wp(cmd)
            value = result.strip()
            return value if value else None
        except WPCLIError:
            logger.warning(f"Network option '{option_name}' not found")
            return None

    def network_option_set(self, option_name: str, option_value: str) -> bool:
        """
        Set WordPress multisite network option value

        Args:
            option_name: Option name to set
            option_value: Option value to set

        Returns:
            True if successful, False otherwise
        """
        try:
            escaped_value = option_value.replace("'", "'\\''")
            cmd = f"network option set {option_name} '{escaped_value}'"
            self._execute_wp(cmd)

            logger.info(f"Network option '{option_name}' set successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to set network option: {e}")
            return False

    def network_option_delete(self, option_name: str) -> bool:
        """
        Delete WordPress multisite network option

        Args:
            option_name: Option name to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = f"network option delete {option_name}"
            self._execute_wp(cmd)

            logger.info(f"Network option '{option_name}' deleted successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to delete network option: {e}")
            return False

    def network_option_list(self, format_type: str = "table") -> Dict[str, Any]:
        """
        List WordPress multisite network options

        Args:
            format_type: Output format (table, json)

        Returns:
            Dictionary with network options information
        """
        try:
            cmd = f"network option list --format={format_type}"
            result = self._execute_wp(cmd)

            if format_type == "json":
                import json
                options_data = json.loads(result)
            else:
                # Parse table format
                lines = result.strip().split('\n')
                options_data = {"options": []}
                for line in lines[2:]:  # Skip header lines
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            options_data["options"].append({
                                "option_name": parts[0],
                                "option_value": " ".join(parts[1:]) if len(parts) > 1 else ""
                            })

            logger.info("Network options listed successfully")
            return options_data
        except WPCLIError as e:
            logger.error(f"Failed to list network options: {e}")
            return {"error": str(e)}

    def super_admin_add(self, user_id: str) -> bool:
        """
        Add super admin to multisite

        Args:
            user_id: User ID or email

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = f"super-admin add {user_id}"
            self._execute_wp(cmd)

            logger.info(f"Super admin '{user_id}' added successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to add super admin: {e}")
            return False

    def super_admin_remove(self, user_id: str) -> bool:
        """
        Remove super admin from multisite

        Args:
            user_id: User ID or email

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = f"super-admin remove {user_id}"
            self._execute_wp(cmd)

            logger.info(f"Super admin '{user_id}' removed successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to remove super admin: {e}")
            return False

    def super_admin_list(self, format_type: str = "table") -> Dict[str, Any]:
        """
        List super admins in multisite

        Args:
            format_type: Output format (table, json)

        Returns:
            Dictionary with super admin information
        """
        try:
            cmd = f"super-admin list --format={format_type}"
            result = self._execute_wp(cmd)

            if format_type == "json":
                import json
                admin_data = json.loads(result)
            else:
                # Parse table format
                lines = result.strip().split('\n')
                admin_data = {"super_admins": []}
                for line in lines[2:]:  # Skip header lines
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            admin_data["super_admins"].append({
                                "user_id": parts[0],
                                "user_email": parts[1],
                                "user_login": parts[2] if len(parts) > 2 else ""
                            })

            logger.info("Super admins listed successfully")
            return admin_data
        except WPCLIError as e:
            logger.error(f"Failed to list super admins: {e}")
            return {"error": str(e)}

    def plugin_install(self, plugin_slug: str, version: str = None, force: bool = False) -> bool:
        """
        Install a WordPress plugin

        Args:
            plugin_slug: Plugin slug from WordPress repository
            version: Specific version to install (optional)
            force: Force installation even if already installed

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["plugin", "install", plugin_slug]
            if version:
                cmd_parts.extend(["--version", version])
            if force:
                cmd_parts.append("--force")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"Plugin '{plugin_slug}' installed successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to install plugin: {e}")
            return False

    def plugin_delete(self, plugin_slug: str, deactivate: bool = True) -> bool:
        """
        Delete a WordPress plugin

        Args:
            plugin_slug: Plugin slug or path
            deactivate: Whether to deactivate before deleting

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["plugin", "delete", plugin_slug]
            if deactivate:
                cmd_parts.append("--deactivate")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"Plugin '{plugin_slug}' deleted successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to delete plugin: {e}")
            return False

    def theme_install(self, theme_slug: str, version: str = None, force: bool = False) -> bool:
        """
        Install a WordPress theme

        Args:
            theme_slug: Theme slug from WordPress repository
            version: Specific version to install (optional)
            force: Force installation even if already installed

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["theme", "install", theme_slug]
            if version:
                cmd_parts.extend(["--version", version])
            if force:
                cmd_parts.append("--force")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"Theme '{theme_slug}' installed successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to install theme: {e}")
            return False

    def theme_delete(self, theme_slug: str, force: bool = False) -> bool:
        """
        Delete a WordPress theme

        Args:
            theme_slug: Theme slug or path
            force: Force deletion even if active

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["theme", "delete", theme_slug]
            if force:
                cmd_parts.append("--force")

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"Theme '{theme_slug}' deleted successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to delete theme: {e}")
            return False

    def user_create(self, username: str, email: str, password: str = None, role: str = "subscriber",
                   first_name: str = None, last_name: str = None, display_name: str = None) -> bool:
        """
        Create a WordPress user

        Args:
            username: Username
            email: Email address
            password: Password (optional, will generate if not provided)
            role: User role (default: subscriber)
            first_name: First name (optional)
            last_name: Last name (optional)
            display_name: Display name (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["user", "create", username, email]
            if password:
                cmd_parts.extend(["--user_pass", password])
            if role:
                cmd_parts.extend(["--role", role])
            if first_name:
                cmd_parts.extend(["--first_name", first_name])
            if last_name:
                cmd_parts.extend(["--last_name", last_name])
            if display_name:
                cmd_parts.extend(["--display_name", display_name])

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"User '{username}' created successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to create user: {e}")
            return False

    def user_delete(self, user_id: str, reassign: str = None) -> bool:
        """
        Delete a WordPress user

        Args:
            user_id: User ID or username
            reassign: User ID to reassign content to (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["user", "delete", user_id]
            if reassign:
                cmd_parts.extend(["--reassign", reassign])
            cmd_parts.append("--yes")  # Auto-confirm deletion

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"User '{user_id}' deleted successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to delete user: {e}")
            return False

    def user_update(self, user_id: str, **kwargs) -> bool:
        """
        Update a WordPress user

        Args:
            user_id: User ID or username
            **kwargs: User fields to update (email, password, role, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["user", "update", user_id]

            field_mapping = {
                'email': '--user_email',
                'password': '--user_pass',
                'role': '--role',
                'first_name': '--first_name',
                'last_name': '--last_name',
                'display_name': '--display_name',
                'nickname': '--nickname'
            }

            for field, value in kwargs.items():
                if field in field_mapping and value:
                    cmd_parts.extend([field_mapping[field], str(value)])

            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)

            logger.info(f"User '{user_id}' updated successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to update user: {e}")
            return False

    def comment_approve(self, comment_id: str) -> bool:
        """
        Approve a WordPress comment

        Args:
            comment_id: Comment ID

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = f"comment approve {comment_id}"
            self._execute_wp(cmd)
            
            logger.info(f"Comment '{comment_id}' approved successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to approve comment: {e}")
            return False

    def comment_unapprove(self, comment_id: str) -> bool:
        """
        Unapprove a WordPress comment

        Args:
            comment_id: Comment ID

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = f"comment unapprove {comment_id}"
            self._execute_wp(cmd)
            
            logger.info(f"Comment '{comment_id}' unapproved successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to unapprove comment: {e}")
            return False

    def comment_spam(self, comment_id: str) -> bool:
        """
        Mark a WordPress comment as spam

        Args:
            comment_id: Comment ID

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = f"comment spam {comment_id}"
            self._execute_wp(cmd)
            
            logger.info(f"Comment '{comment_id}' marked as spam successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to mark comment as spam: {e}")
            return False

    def comment_trash(self, comment_id: str) -> bool:
        """
        Move a WordPress comment to trash

        Args:
            comment_id: Comment ID

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = f"comment trash {comment_id}"
            self._execute_wp(cmd)
            
            logger.info(f"Comment '{comment_id}' moved to trash successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to trash comment: {e}")
            return False

    def media_upload(self, file_path: str, title: str = None, caption: str = None, alt_text: str = None) -> Optional[Dict[str, Any]]:
        """
        Upload a media file to WordPress

        Args:
            file_path: Local path to the file
            title: Media title (optional)
            caption: Media caption (optional)
            alt_text: Alt text for the media (optional)

        Returns:
            Media information or None if failed
        """
        try:
            cmd_parts = ["media", "import", file_path]
            if title:
                cmd_parts.extend(["--title", title])
            if caption:
                cmd_parts.extend(["--caption", caption])
            if alt_text:
                cmd_parts.extend(["--alt", alt_text])
            
            cmd = " ".join(cmd_parts)
            result = self._execute_wp(cmd)
            
            # Parse the result to get media info
            import json
            media_info = json.loads(result)
            
            logger.info(f"Media uploaded successfully: {media_info.get('url', 'Unknown')}")
            return media_info
        except WPCLIError as e:
            logger.error(f"Failed to upload media: {e}")
            return None

    def media_delete(self, media_id: str) -> bool:
        """
        Delete a media file from WordPress

        Args:
            media_id: Media ID

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = f"media delete {media_id} --yes"
            self._execute_wp(cmd)
            
            logger.info(f"Media '{media_id}' deleted successfully")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to delete media: {e}")
            return False

    def db_export(self, file_path: str, tables: str = None) -> bool:
        """
        Export WordPress database

        Args:
            file_path: Path to save the export file
            tables: Specific tables to export (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd_parts = ["db", "export", file_path]
            if tables:
                cmd_parts.extend(["--tables", tables])
            
            cmd = " ".join(cmd_parts)
            self._execute_wp(cmd)
            
            logger.info(f"Database exported successfully to: {file_path}")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to export database: {e}")
            return False

    def db_import(self, file_path: str) -> bool:
        """
        Import WordPress database

        Args:
            file_path: Path to the import file

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = f"db import {file_path}"
            self._execute_wp(cmd)
            
            logger.info(f"Database imported successfully from: {file_path}")
            return True
        except WPCLIError as e:
            logger.error(f"Failed to import database: {e}")
            return False
