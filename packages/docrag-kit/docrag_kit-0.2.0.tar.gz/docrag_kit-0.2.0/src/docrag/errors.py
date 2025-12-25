"""Error handling and user feedback for DocRAG Kit."""

from typing import Optional
import sys


class ProgressIndicator:
    """Display progress indicators for long-running operations."""
    
    @staticmethod
    def start_operation(operation_name: str, emoji: str = "⏳") -> None:
        """
        Display the start of an operation.
        
        Args:
            operation_name: Name of the operation being performed
            emoji: Emoji to display (default: hourglass)
        """
        print(f"{emoji} {operation_name}...", flush=True)
    
    @staticmethod
    def operation_success(message: str, emoji: str = "SUCCESS:") -> None:
        """
        Display successful completion of an operation.
        
        Args:
            message: Success message to display
            emoji: Emoji to display (default: checkmark)
        """
        print(f"{emoji} {message}", flush=True)
    
    @staticmethod
    def operation_failure(message: str, emoji: str = "ERROR:") -> None:
        """
        Display failure of an operation.
        
        Args:
            message: Failure message to display
            emoji: Emoji to display (default: cross mark)
        """
        print(f"{emoji} {message}", flush=True)
    
    @staticmethod
    def operation_warning(message: str, emoji: str = "WARNING:") -> None:
        """
        Display a warning during an operation.
        
        Args:
            message: Warning message to display
            emoji: Emoji to display (default: warning sign)
        """
        print(f"{emoji} {message}", flush=True)
    
    @staticmethod
    def show_progress(current: int, total: int, prefix: str = "Progress") -> None:
        """
        Display progress for operations with known total count.
        
        Args:
            current: Current progress count
            total: Total count
            prefix: Prefix text for progress display
        """
        percentage = int((current / total) * 100) if total > 0 else 0
        bar_length = 30
        filled_length = int(bar_length * current / total) if total > 0 else 0
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        # Use carriage return to update same line
        sys.stdout.write(f'\r{prefix}: [{bar}] {percentage}% ({current}/{total})')
        sys.stdout.flush()
        
        # Print newline when complete
        if current >= total:
            print()
    
    @staticmethod
    def show_spinner(message: str, step: int = 0) -> None:
        """
        Display a simple spinner for indeterminate progress.
        
        Args:
            message: Message to display with spinner
            step: Current step for spinner animation
        """
        spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        spinner = spinner_chars[step % len(spinner_chars)]
        sys.stdout.write(f'\r{spinner} {message}')
        sys.stdout.flush()


class ErrorFormatter:
    """Format error messages with emoji indicators and helpful suggestions."""
    
    @staticmethod
    def format_error(
        error_type: str,
        reason: str,
        suggested_action: str,
        details: Optional[str] = None
    ) -> str:
        """
        Format an error message with emoji indicator, reason, and suggested action.
        
        Args:
            error_type: Type of error (e.g., "Configuration Error", "API Key Error")
            reason: Specific reason for the error
            suggested_action: What the user should do to fix it
            details: Optional additional details
        
        Returns:
            Formatted error message string
        """
        lines = [
            f"ERROR: {error_type}: {reason}",
            f"   {suggested_action}"
        ]
        
        if details:
            lines.append(f"   {details}")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_config_error(reason: str, suggested_action: str) -> str:
        """Format a configuration error message."""
        return ErrorFormatter.format_error(
            "Configuration Error",
            reason,
            suggested_action
        )
    
    @staticmethod
    def format_api_key_error(provider: str, reason: str) -> str:
        """
        Format an API key error message with provider-specific instructions.
        
        Args:
            provider: LLM provider name (openai or gemini)
            reason: Specific reason for the error
        
        Returns:
            Formatted error message with provider-specific instructions
        """
        if provider.lower() == 'openai':
            key_name = "OPENAI_API_KEY"
            get_key_url = "https://platform.openai.com/api-keys"
            instructions = (
                f"1. Get your API key from: {get_key_url}\n"
                f"   2. Add it to your .env file: {key_name}=your_key_here\n"
                "   3. Run the command again"
            )
        elif provider.lower() == 'gemini':
            key_name = "GOOGLE_API_KEY"
            get_key_url = "https://makersuite.google.com/app/apikey"
            instructions = (
                f"1. Get your API key from: {get_key_url}\n"
                f"   2. Add it to your .env file: {key_name}=your_key_here\n"
                "   3. Run the command again"
            )
        else:
            key_name = "API_KEY"
            instructions = "Add your API key to the .env file and try again"
        
        return ErrorFormatter.format_error(
            "API Key Error",
            reason,
            instructions
        )
    
    @staticmethod
    def get_api_key_instructions(provider: str) -> str:
        """
        Get detailed API key instructions for a specific provider.
        
        Args:
            provider: LLM provider name (openai or gemini)
        
        Returns:
            Detailed instructions for obtaining and configuring API key
        """
        if provider.lower() == 'openai':
            return """
🔑 OpenAI API Key Setup:

1. Visit: https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (it will only be shown once!)
5. Add to your .env file:
   OPENAI_API_KEY=sk-...your_key_here

TIP: Tips:
   - Keep your API key secure and never commit it to git
   - Monitor your usage at: https://platform.openai.com/usage
   - Set usage limits to avoid unexpected charges
"""
        elif provider.lower() == 'gemini':
            return """
🔑 Google Gemini API Key Setup:

1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API key"
4. Select or create a Google Cloud project
5. Copy the generated API key
6. Add to your .env file:
   GOOGLE_API_KEY=...your_key_here

TIP: Tips:
   - Keep your API key secure and never commit it to git
   - Gemini API has a generous free tier
   - Monitor your usage in Google Cloud Console
"""
        else:
            return "Unknown provider. Please check your configuration."
    
    @staticmethod
    def format_file_error(file_path: str, reason: str, suggested_action: str) -> str:
        """Format a file system error message."""
        return ErrorFormatter.format_error(
            "File Error",
            f"{file_path}: {reason}",
            suggested_action
        )
    
    @staticmethod
    def format_indexing_error(reason: str, suggested_action: str) -> str:
        """Format an indexing error message."""
        return ErrorFormatter.format_error(
            "Indexing Error",
            reason,
            suggested_action
        )
    
    @staticmethod
    def format_mcp_error(reason: str, suggested_action: str) -> str:
        """Format an MCP server error message."""
        return ErrorFormatter.format_error(
            "MCP Server Error",
            reason,
            suggested_action
        )


class ValidationWarnings:
    """Validation warnings for configuration parameters."""
    
    @staticmethod
    def check_chunk_size(chunk_size: int) -> Optional[str]:
        """
        Check if chunk size is within recommended range and return warning if not.
        
        Args:
            chunk_size: Configured chunk size
        
        Returns:
            Warning message if chunk size is outside recommended range, None otherwise
        """
        if chunk_size < 100:
            return (
                "WARNING:  Warning: chunk_size is too small (< 100 characters)\n"
                "   Small chunks may not provide enough context for meaningful search\n"
                "   Recommended: 500-2000 characters\n"
                "   \n"
                "   Предупреждение: chunk_size слишком маленький (< 100 символов)\n"
                "   Маленькие фрагменты могут не содержать достаточно контекста\n"
                "   Рекомендуется: 500-2000 символов"
            )
        elif chunk_size > 5000:
            return (
                "WARNING:  Warning: chunk_size is too large (> 5000 characters)\n"
                "   Large chunks may reduce search precision and increase costs\n"
                "   Recommended: 500-2000 characters\n"
                "   \n"
                "   Предупреждение: chunk_size слишком большой (> 5000 символов)\n"
                "   Большие фрагменты могут снизить точность поиска и увеличить затраты\n"
                "   Рекомендуется: 500-2000 символов"
            )
        return None
    
    @staticmethod
    def check_top_k(top_k: int) -> Optional[str]:
        """
        Check if top_k is valid and return warning if not.
        
        Args:
            top_k: Configured top_k value
        
        Returns:
            Warning message if top_k is invalid, None otherwise
        """
        if top_k < 1:
            return (
                "WARNING:  Warning: top_k must be at least 1\n"
                "   Using default value: 5"
            )
        return None
    
    @staticmethod
    def validate_all(chunk_size: int, top_k: int) -> list[str]:
        """
        Validate all configuration parameters and return list of warnings.
        
        Args:
            chunk_size: Configured chunk size
            top_k: Configured top_k value
        
        Returns:
            List of warning messages
        """
        warnings = []
        
        chunk_warning = ValidationWarnings.check_chunk_size(chunk_size)
        if chunk_warning:
            warnings.append(chunk_warning)
        
        top_k_warning = ValidationWarnings.check_top_k(top_k)
        if top_k_warning:
            warnings.append(top_k_warning)
        
        return warnings
