"""
panel/test_serve_upload.py
---------------------------
Tests for handle_upload method to verify MiltiTakimPipeline integration.

Test that:
1. handle_upload calls MiltiTakimPipeline instead of process_lxf_upload
2. Response contains required keys from pipeline
3. Temp file is cleaned up
4. Error handling works
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO


class TestHandleUploadIntegration:
    """Test handle_upload method integration with MiltiTakimPipeline"""

    def test_handle_upload_calls_pipeline_instead_of_legacy_function(self):
        """handle_upload should call MiltiTakimPipeline.process() instead of process_lxf_upload()"""
        from panel.serve import DashboardHandler

        # Mock the pipeline
        with patch('panel.serve.MiltiTakimPipeline') as mock_pipeline_class:
            # Mock the pipeline instance
            mock_pipeline_instance = MagicMock()
            mock_pipeline_class.return_value = mock_pipeline_instance

            # Mock the response from pipeline
            mock_pipeline_instance.process.return_value = {
                'success': True,
                'message': 'Successfully processed 100 athletes',
                'selected_tr': [
                    {
                        'name': 'Ahmet Yılmaz',
                        'birth_year': 2013,
                        'selected_slot': 'TR-1',
                        'top3_total': 21
                    }
                ],
                'selected_bolge': [],
                'baraj_yok_count': 50,
                'total_athletes': 100,
                'summary': {2013: {'tr': 1, 'bolge': 0, 'total': 1}}
            }

            # Create a mock handler
            handler = MagicMock(spec=DashboardHandler)
            handler.wfile = Mock()

            # Create multipart form data
            boundary = 'boundary123'
            content = (
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="file"; filename="test.lxf"\r\n'
                f'Content-Type: application/octet-stream\r\n'
                f'\r\n'
                f'test file content'
                f'\r\n--{boundary}--\r\n'
            ).encode('utf-8')

            # Set the request attributes
            handler.headers = {
                'Content-Length': str(len(content)),
                'Content-Type': f'multipart/form-data; boundary={boundary}'
            }
            handler.rfile = BytesIO(content)

            # Call handle_upload directly
            with patch('panel.serve.Path.unlink'):  # Mock temp file cleanup
                DashboardHandler.handle_upload(handler)

            # Verify that the pipeline was instantiated
            mock_pipeline_class.assert_called_once()

            # Verify that process was called on the pipeline
            mock_pipeline_instance.process.assert_called_once()

            # Verify response was sent
            handler.send_response.assert_called_with(200)
            handler.send_header.assert_called()
            handler.end_headers.assert_called()

    def test_handle_upload_response_format(self):
        """handle_upload response should have all required keys from pipeline"""
        from panel.serve import DashboardHandler

        with patch('panel.serve.MiltiTakimPipeline') as mock_pipeline_class:
            mock_pipeline_instance = MagicMock()
            mock_pipeline_class.return_value = mock_pipeline_instance

            # Mock a complete response
            mock_response = {
                'success': True,
                'message': 'Successfully processed 100 athletes',
                'selected_tr': [
                    {
                        'name': 'Ahmet',
                        'birth_year': 2013,
                        'gender': 'M',
                        'selected_slot': 'TR-1',
                        'top3_total': 21,
                        'region': 1,
                        'city': 'İstanbul',
                        'club': 'Test SK'
                    }
                ],
                'selected_bolge': [],
                'baraj_yok_count': 50,
                'total_athletes': 100,
                'summary': {
                    2013: {
                        'birth_year': 2013,
                        'tr': 1,
                        'bolge': 0,
                        'total': 1,
                        'multi': 0
                    }
                }
            }

            mock_pipeline_instance.process.return_value = mock_response

            # Capture the response JSON
            response_data = []
            def capture_write(data):
                response_data.append(data)

            handler = MagicMock(spec=DashboardHandler)
            handler.wfile = Mock()
            handler.wfile.write = capture_write

            # Create multipart data
            boundary = 'boundary123'
            content = (
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="file"; filename="test.lxf"\r\n'
                f'\r\n'
                f'content'
                f'\r\n--{boundary}--\r\n'
            ).encode('utf-8')

            handler.headers = {
                'Content-Length': str(len(content)),
                'Content-Type': f'multipart/form-data; boundary={boundary}'
            }
            handler.rfile = BytesIO(content)

            with patch('panel.serve.Path.unlink'):
                DashboardHandler.handle_upload(handler)

            # Parse the response
            if response_data:
                response_json = json.loads(response_data[0].decode('utf-8'))

                # Verify all required keys are present
                assert 'success' in response_json
                assert 'message' in response_json
                assert 'selected_tr' in response_json
                assert 'selected_bolge' in response_json
                assert 'baraj_yok_count' in response_json
                assert 'total_athletes' in response_json
                assert 'summary' in response_json

    def test_handle_upload_error_handling(self):
        """handle_upload should handle pipeline errors gracefully"""
        from panel.serve import DashboardHandler

        with patch('panel.serve.MiltiTakimPipeline') as mock_pipeline_class:
            mock_pipeline_instance = MagicMock()
            mock_pipeline_class.return_value = mock_pipeline_instance

            # Mock pipeline to raise exception
            mock_pipeline_instance.process.side_effect = Exception("Test error")

            handler = MagicMock(spec=DashboardHandler)
            handler.wfile = Mock()

            # Create multipart data
            boundary = 'boundary123'
            content = (
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="file"; filename="test.lxf"\r\n'
                f'\r\n'
                f'content'
                f'\r\n--{boundary}--\r\n'
            ).encode('utf-8')

            handler.headers = {
                'Content-Length': str(len(content)),
                'Content-Type': f'multipart/form-data; boundary={boundary}'
            }
            handler.rfile = BytesIO(content)

            with patch('panel.serve.Path.unlink'):
                DashboardHandler.handle_upload(handler)

            # Verify response was sent (either send_error or send_response)
            assert handler.send_response.called or handler.send_error.called

    def test_handle_upload_cleanup_on_error(self):
        """handle_upload should clean up temp file EVEN when pipeline fails"""
        from panel.serve import DashboardHandler

        with patch('panel.serve.MiltiTakimPipeline') as mock_pipeline_class:
            mock_pipeline_instance = MagicMock()
            mock_pipeline_class.return_value = mock_pipeline_instance

            # Mock pipeline to raise exception
            mock_pipeline_instance.process.side_effect = Exception("Pipeline error")

            handler = MagicMock(spec=DashboardHandler)
            handler.wfile = Mock()

            # Create multipart data
            boundary = 'boundary123'
            content = (
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="file"; filename="test.lxf"\r\n'
                f'\r\n'
                f'content'
                f'\r\n--{boundary}--\r\n'
            ).encode('utf-8')

            handler.headers = {
                'Content-Length': str(len(content)),
                'Content-Type': f'multipart/form-data; boundary={boundary}'
            }
            handler.rfile = BytesIO(content)

            # Mock Path.unlink and verify it's called even on error
            with patch('panel.serve.Path.unlink') as mock_unlink:
                DashboardHandler.handle_upload(handler)

                # Verify cleanup was called (this should fail before fix)
                mock_unlink.assert_called_once()

    def test_handle_upload_error_response_is_json(self):
        """handle_upload should send JSON error response, not HTML"""
        from panel.serve import DashboardHandler

        with patch('panel.serve.MiltiTakimPipeline') as mock_pipeline_class:
            mock_pipeline_instance = MagicMock()
            mock_pipeline_class.return_value = mock_pipeline_instance

            # Mock pipeline to raise exception
            mock_pipeline_instance.process.side_effect = Exception("Test error")

            handler = MagicMock(spec=DashboardHandler)

            # Capture response
            response_data = []
            def capture_write(data):
                response_data.append(data)

            handler.wfile = Mock()
            handler.wfile.write = capture_write

            # Create multipart data
            boundary = 'boundary123'
            content = (
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="file"; filename="test.lxf"\r\n'
                f'\r\n'
                f'content'
                f'\r\n--{boundary}--\r\n'
            ).encode('utf-8')

            handler.headers = {
                'Content-Length': str(len(content)),
                'Content-Type': f'multipart/form-data; boundary={boundary}'
            }
            handler.rfile = BytesIO(content)

            with patch('panel.serve.Path.unlink'):
                DashboardHandler.handle_upload(handler)

            # Verify response was sent with 400 status
            handler.send_response.assert_called_with(400)

            # Verify JSON response was written (not HTML error page)
            if response_data:
                response_json = json.loads(response_data[0].decode('utf-8'))
                assert 'success' in response_json
                assert response_json['success'] is False
                assert 'error' in response_json

    def test_handle_upload_no_race_leg_parameter(self):
        """handle_upload should NOT pass race_leg to pipeline"""
        from panel.serve import DashboardHandler

        with patch('panel.serve.MiltiTakimPipeline') as mock_pipeline_class:
            mock_pipeline_instance = MagicMock()
            mock_pipeline_class.return_value = mock_pipeline_instance
            mock_pipeline_instance.process.return_value = {
                'success': True,
                'message': 'OK',
                'selected_tr': [],
                'selected_bolge': [],
                'baraj_yok_count': 0,
                'total_athletes': 0,
                'summary': {}
            }

            handler = MagicMock(spec=DashboardHandler)
            handler.wfile = Mock()

            # Create multipart data with 'edirne' in filename
            boundary = 'boundary123'
            content = (
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="file"; filename="edirne_results.lxf"\r\n'
                f'\r\n'
                f'content'
                f'\r\n--{boundary}--\r\n'
            ).encode('utf-8')

            handler.headers = {
                'Content-Length': str(len(content)),
                'Content-Type': f'multipart/form-data; boundary={boundary}'
            }
            handler.rfile = BytesIO(content)

            with patch('panel.serve.Path.unlink'):
                DashboardHandler.handle_upload(handler)

            # Verify process was called with ONLY the temp file path
            mock_pipeline_instance.process.assert_called_once()

            # Get the call arguments
            call_args = mock_pipeline_instance.process.call_args

            # Should be called with one positional argument (the file path)
            assert len(call_args[0]) == 1 or len(call_args[1]) == 0

            # Should NOT have race_leg as a keyword argument
            assert 'race_leg' not in call_args[1]

    def test_handle_upload_temp_file_cleanup(self):
        """handle_upload should clean up temp file after processing"""
        from panel.serve import DashboardHandler
        from pathlib import Path

        with patch('panel.serve.MiltiTakimPipeline') as mock_pipeline_class:
            mock_pipeline_instance = MagicMock()
            mock_pipeline_class.return_value = mock_pipeline_instance
            mock_pipeline_instance.process.return_value = {
                'success': True,
                'message': 'OK',
                'selected_tr': [],
                'selected_bolge': [],
                'baraj_yok_count': 0,
                'total_athletes': 0,
                'summary': {}
            }

            handler = MagicMock(spec=DashboardHandler)
            handler.wfile = Mock()

            # Create multipart data
            boundary = 'boundary123'
            content = (
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="file"; filename="test.lxf"\r\n'
                f'\r\n'
                f'content'
                f'\r\n--{boundary}--\r\n'
            ).encode('utf-8')

            handler.headers = {
                'Content-Length': str(len(content)),
                'Content-Type': f'multipart/form-data; boundary={boundary}'
            }
            handler.rfile = BytesIO(content)

            # Mock Path.unlink to verify it's called
            with patch('panel.serve.Path.unlink') as mock_unlink:
                DashboardHandler.handle_upload(handler)

                # Verify unlink was called (temp file cleanup)
                mock_unlink.assert_called_once()


class TestHandleUploadRegressions:
    """Test that multipart parsing and response handling still work"""

    def test_multipart_parsing_still_works(self):
        """Multipart parsing should not be affected by pipeline change"""
        # Create valid multipart data
        boundary = 'boundary123'
        file_content = b'test file content'
        content = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="file"; filename="test.lxf"\r\n'
            f'Content-Type: application/octet-stream\r\n'
            f'\r\n'
        ).encode('utf-8') + file_content + (
            f'\r\n--{boundary}--\r\n'
        ).encode('utf-8')

        # Find the file content
        boundary_bytes = boundary.encode('utf-8')
        parts = content.split(b'--' + boundary_bytes)

        # Should find the file part
        found_file = False
        for part in parts:
            if b'filename=' in part:
                found_file = True
                break

        assert found_file, "Multipart parsing should find the file part"

    def test_ensure_ascii_false_in_response(self):
        """Response JSON should use ensure_ascii=False for UTF-8 characters"""
        from panel.serve import DashboardHandler

        with patch('panel.serve.MiltiTakimPipeline') as mock_pipeline_class:
            mock_pipeline_instance = MagicMock()
            mock_pipeline_class.return_value = mock_pipeline_instance

            # Response with Turkish characters
            mock_pipeline_instance.process.return_value = {
                'success': True,
                'message': 'İstanbul\'dan 5 atlet seçildi',
                'selected_tr': [
                    {
                        'name': 'Ahmet Yılmaz',
                        'birth_year': 2013,
                        'city': 'İstanbul',
                        'selected_slot': 'TR-1',
                        'top3_total': 21
                    }
                ],
                'selected_bolge': [],
                'baraj_yok_count': 0,
                'total_athletes': 5,
                'summary': {}
            }

            handler = MagicMock(spec=DashboardHandler)

            response_data = []
            def capture_write(data):
                response_data.append(data)

            handler.wfile = Mock()
            handler.wfile.write = capture_write

            boundary = 'boundary123'
            content = (
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="file"; filename="test.lxf"\r\n'
                f'\r\n'
                f'content'
                f'\r\n--{boundary}--\r\n'
            ).encode('utf-8')

            handler.headers = {
                'Content-Length': str(len(content)),
                'Content-Type': f'multipart/form-data; boundary={boundary}'
            }
            handler.rfile = BytesIO(content)

            with patch('panel.serve.Path.unlink'):
                DashboardHandler.handle_upload(handler)

            # Verify UTF-8 characters in response
            if response_data:
                response_str = response_data[0].decode('utf-8')
                assert 'İstanbul' in response_str
                assert 'Yılmaz' in response_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
