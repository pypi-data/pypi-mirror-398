"""
Unit tests for Joblet SDK exceptions
"""

import pytest

from joblet.exceptions import (
    AuthenticationError,
    ConnectionError,
    JobletException,
    JobNotFoundError,
    NetworkError,
    RuntimeNotFoundError,
    TimeoutError,
    ValidationError,
    VolumeError,
)


class TestJobletExceptions:
    """Test cases for Joblet SDK exception classes"""

    def test_joblet_exception_base_class(self):
        """Test JobletException as base class"""
        exception = JobletException("Base exception message")

        assert str(exception) == "Base exception message"
        assert isinstance(exception, Exception)

        # Test with no message
        exception_no_msg = JobletException()
        assert str(exception_no_msg) == ""

    def test_connection_error_inheritance(self):
        """Test ConnectionError inherits from JobletException"""
        exception = ConnectionError("Connection failed")

        assert str(exception) == "Connection failed"
        assert isinstance(exception, JobletException)
        assert isinstance(exception, Exception)

    def test_authentication_error_inheritance(self):
        """Test AuthenticationError inherits from JobletException"""
        exception = AuthenticationError("Authentication failed")

        assert str(exception) == "Authentication failed"
        assert isinstance(exception, JobletException)
        assert isinstance(exception, Exception)

    def test_job_not_found_error_inheritance(self):
        """Test JobNotFoundError inherits from JobletException"""
        exception = JobNotFoundError("Job not found")

        assert str(exception) == "Job not found"
        assert isinstance(exception, JobletException)
        assert isinstance(exception, Exception)

    def test_runtime_not_found_error_inheritance(self):
        """Test RuntimeNotFoundError inherits from JobletException"""
        exception = RuntimeNotFoundError("Runtime not found")

        assert str(exception) == "Runtime not found"
        assert isinstance(exception, JobletException)
        assert isinstance(exception, Exception)

    def test_network_error_inheritance(self):
        """Test NetworkError inherits from JobletException"""
        exception = NetworkError("Network operation failed")

        assert str(exception) == "Network operation failed"
        assert isinstance(exception, JobletException)
        assert isinstance(exception, Exception)

    def test_volume_error_inheritance(self):
        """Test VolumeError inherits from JobletException"""
        exception = VolumeError("Volume operation failed")

        assert str(exception) == "Volume operation failed"
        assert isinstance(exception, JobletException)
        assert isinstance(exception, Exception)

    def test_validation_error_inheritance(self):
        """Test ValidationError inherits from JobletException"""
        exception = ValidationError("Validation failed")

        assert str(exception) == "Validation failed"
        assert isinstance(exception, JobletException)
        assert isinstance(exception, Exception)

    def test_timeout_error_inheritance(self):
        """Test TimeoutError inherits from JobletException"""
        exception = TimeoutError("Operation timed out")

        assert str(exception) == "Operation timed out"
        assert isinstance(exception, JobletException)
        assert isinstance(exception, Exception)

    def test_exception_raising_and_catching(self):
        """Test raising and catching specific exceptions"""

        # Test ConnectionError
        with pytest.raises(ConnectionError) as exc_info:
            raise ConnectionError("Server unreachable")
        assert "Server unreachable" in str(exc_info.value)

        # Test JobNotFoundError
        with pytest.raises(JobNotFoundError) as exc_info:
            raise JobNotFoundError("Job 123 not found")
        assert "Job 123 not found" in str(exc_info.value)

        # Test RuntimeNotFoundError
        with pytest.raises(RuntimeNotFoundError) as exc_info:
            raise RuntimeNotFoundError("Python 3.11 not available")
        assert "Python 3.11 not available" in str(exc_info.value)

    def test_catching_base_exception(self):
        """Test catching specific exceptions as base JobletException"""

        # ConnectionError should be catchable as JobletException
        with pytest.raises(JobletException):
            raise ConnectionError("Connection failed")

        # JobNotFoundError should be catchable as JobletException
        with pytest.raises(JobletException):
            raise JobNotFoundError("Job not found")

        # NetworkError should be catchable as JobletException
        with pytest.raises(JobletException):
            raise NetworkError("Network error")

    def test_exception_with_format_strings(self):
        """Test exceptions with formatted messages"""
        job_id = "job-12345"

        exception = JobNotFoundError(f"Job {job_id} was not found in the system")
        assert "job-12345" in str(exception)
        assert "was not found in the system" in str(exception)

        # Test with multiple parameters
        host = "joblet.example.com"
        port = 50051

        exception = ConnectionError(f"Failed to connect to {host}:{port}")
        assert "joblet.example.com:50051" in str(exception)

    def test_exception_error_codes(self):
        """Test exceptions can carry additional error information"""

        # Test exception with additional attributes
        exception = ValidationError("Invalid runtime specification")
        exception.error_code = "INVALID_RUNTIME_SPEC"
        exception.details = {"spec": "invalid:spec", "reason": "invalid format"}

        assert str(exception) == "Invalid runtime specification"
        assert exception.error_code == "INVALID_RUNTIME_SPEC"
        assert exception.details["spec"] == "invalid:spec"

    def test_exception_chaining(self):
        """Test exception chaining (from another exception)"""

        with pytest.raises(ConnectionError) as exc_info:
            try:
                # Simulate an underlying error
                raise ValueError("Invalid certificate format")
            except ValueError as e:
                # Chain it with our custom exception
                raise ConnectionError("Failed to establish secure connection") from e

        # Verify the exception was chained
        assert str(exc_info.value) == "Failed to establish secure connection"
        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, ValueError)
        assert str(exc_info.value.__cause__) == "Invalid certificate format"

    def test_all_exceptions_importable(self):
        """Test all exceptions are properly importable"""
        # This test verifies the imports work correctly
        exceptions = [
            JobletException,
            ConnectionError,
            AuthenticationError,
            JobNotFoundError,
            RuntimeNotFoundError,
            NetworkError,
            VolumeError,
            ValidationError,
            TimeoutError,
        ]

        for exc_class in exceptions:
            # Verify each exception class is properly defined
            assert issubclass(exc_class, Exception)

            # Verify we can instantiate each exception
            instance = exc_class("test message")
            assert str(instance) == "test message"

    def test_exception_repr(self):
        """Test exception repr methods"""
        exception = JobNotFoundError("Job xyz not found")

        # The repr should include the class name and message
        repr_str = repr(exception)
        assert "JobNotFoundError" in repr_str
        assert "Job xyz not found" in repr_str

    def test_empty_message_exceptions(self):
        """Test exceptions with empty or None messages"""

        # Test with empty string
        exception = ConnectionError("")
        assert str(exception) == ""

        # Test with None (should convert to empty string)
        exception = NetworkError(None)
        # In Python, None as exception message becomes "None"
        assert str(exception) in ["None", ""]
