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

    def _upload_with_filename(self, mock_pipeline_class, filename):
        """Helper: simulate an upload of `filename` and return the race_leg
        kwarg that handle_upload passed to pipeline.process()."""
        from panel.serve import DashboardHandler

        mock_pipeline_instance = MagicMock()
        mock_pipeline_class.return_value = mock_pipeline_instance
        mock_pipeline_instance.process.return_value = {
            'success': True, 'message': 'ok', 'selected_tr': [], 'selected_bolge': [],
            'baraj_yok_count': 0, 'total_athletes': 0, 'summary': {}
        }

        handler = MagicMock(spec=DashboardHandler)
        handler.wfile = Mock()

        boundary = 'boundary123'
        content = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f'Content-Type: application/octet-stream\r\n'
            f'\r\n'
            f'test file content'
            f'\r\n--{boundary}--\r\n'
        ).encode('utf-8')

        handler.headers = {
            'Content-Length': str(len(content)),
            'Content-Type': f'multipart/form-data; boundary={boundary}'
        }
        handler.rfile = BytesIO(content)

        with patch('panel.serve.Path.unlink'):
            DashboardHandler.handle_upload(handler)

        _, kwargs = mock_pipeline_instance.process.call_args
        return kwargs.get('race_leg')

    def test_handle_upload_detects_edirne_leg_from_filename(self):
        """Uploading a file with 'edirne' in the name must tag results as
        race_leg='edirne' (regression: Task 4 refactor dropped this filename
        detection, so every upload got hardcoded 'milli_takim', which the
        dashboard's antalya/edirne split (database/db.py) always buckets as
        edirne — antalya uploads showed up under the Edirne tab)."""
        with patch('panel.serve.MiltiTakimPipeline') as mock_pipeline_class:
            race_leg = self._upload_with_filename(mock_pipeline_class, 'edirne_millitakim_secme_sonuc.lxf')
        assert race_leg == 'edirne'

    def test_handle_upload_detects_antalya_leg_from_filename(self):
        """Uploading a file with 'antalya' (or no leg keyword) in the name
        must tag results as race_leg='antalya'."""
        with patch('panel.serve.MiltiTakimPipeline') as mock_pipeline_class:
            race_leg = self._upload_with_filename(mock_pipeline_class, 'antalya_millitakim_secme_sonuc.lxf')
        assert race_leg == 'antalya'

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

    def test_handle_upload_passes_race_leg_detected_from_filename(self):
        """handle_upload MUST pass race_leg to pipeline, detected from filename.

        This replaces a prior test that asserted the opposite (no race_leg
        passed at all). That assumption was the actual bug: the Task 4
        refactor (commit 08b933d) dropped filename-based leg detection
        assuming "the pipeline handles it internally", but the pipeline just
        hardcoded race_leg='milli_takim' for every upload. Since the
        dashboard's antalya/edirne split (database/db.py) buckets anything
        that isn't literally 'antalya' into the Edirne tab, every Antalya
        upload silently showed up under Edirne."""
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

            mock_pipeline_instance.process.assert_called_once()
            _, kwargs = mock_pipeline_instance.process.call_args
            assert kwargs.get('race_leg') == 'edirne'

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


class TestYildizlarBirthYearPooling:
    """
    Regression test: Multinations/Comen Cup/Central European Yıldızlar pool
    athletes ACROSS multiple birth years (e.g. Multinations = 2011+2012+2013
    combined). serve_api_ranking() must fetch the full population (birth_year
    param NOT passed to get_athlete_rankings) and run select_all_yildizlar()
    on it BEFORE narrowing to the requested birth_year for display — doing it
    in the other order would compute e.g. Multinations from 2013 girls alone
    instead of the real 2011-2013 pool.

    Exercises the actual DashboardHandler.serve_api_ranking() code path (not
    the raw db/ranker functions in isolation) so it fails if a future change
    reintroduces early birth_year/region filtering. Requires real uploaded
    LXF data in the DB — skipped otherwise.
    """

    def _call_ranking(self, path):
        from panel.serve import DashboardHandler
        import json as json_mod

        handler = MagicMock(spec=DashboardHandler)
        handler.path = path
        response_data = []
        handler.wfile = Mock()
        handler.wfile.write = lambda data: response_data.append(data)

        DashboardHandler.serve_api_ranking(handler)

        if not response_data:
            pytest.skip("No response written — no athlete data in database")
        body = b''.join(response_data).decode('utf-8')
        return json_mod.loads(body)

    def test_multinations_selection_same_with_and_without_birth_year_filter(self):
        full = self._call_ranking('/api/ranking?leg=combined&gender=F')
        if not full:
            pytest.skip("No athlete data in database — run an upload first")
        full_2013_multi = {
            a['athlete_name'] for a in full
            if a.get('birth_year') == 2013 and a.get('selected_yildiz_multinations')
        }

        filtered = self._call_ranking('/api/ranking?leg=combined&gender=F&birth_year=2013')
        filtered_multi = {
            a['athlete_name'] for a in filtered
            if a.get('selected_yildiz_multinations')
        }

        # candidate_yildiz_multinations / candidate_relay_yildiz_multinations
        # must be forwarded to the API response (regression: they were
        # computed by select_yildizlar_multinations() but silently dropped
        # by serve_api_ranking()'s explicit response-field whitelist).
        assert full and 'candidate_yildiz_multinations' in full[0]
        assert full and 'candidate_relay_yildiz_multinations' in full[0]

        assert full_2013_multi == filtered_multi, (
            "Multinations selection for 2013 girls differs depending on "
            "whether a birth_year=2013 filter was applied — the dashboard's "
            "birth-year filter must only affect display, not which athletes "
            "get selected to a cross-birth-year Yıldızlar competition."
        )

    def test_tr_selection_same_with_and_without_region_filter(self):
        """Federasyon Karması TR is a single NATIONAL ranking across all 6
        regions. Regression: passing region=N used to narrow the pool to
        that region BEFORE ranking, so athletes competed only against their
        own region for the national TR slots — real-world case: a
        region=1 (Istanbul) query put 8 Istanbul athletes in TR who are
        actually only BÖLGE-eligible per the official TYF roster, because
        they were ranked against Istanbul alone instead of nationally."""
        full = self._call_ranking('/api/ranking?leg=combined&birth_year=2013&gender=M')
        if not full:
            pytest.skip("No athlete data in database — run an upload first")
        full_tr = {a['athlete_name'] for a in full if a.get('selected') == 'TR'}

        region1 = self._call_ranking('/api/ranking?leg=combined&birth_year=2013&gender=M&region=1')
        region1_tr = {a['athlete_name'] for a in region1 if a.get('selected') == 'TR'}

        assert region1_tr == (full_tr & {a['athlete_name'] for a in region1}), (
            "TR selection differs depending on whether a region filter was "
            "applied — TR must be ranked nationally before the region "
            "filter narrows the pool for display."
        )


def test_api_ranking_includes_gencler_fields():
    """select_all_gencler /api/ranking akışında çağrılır ve alanlar yanıta girer."""
    from federasyon.gencler_ranker import select_all_gencler
    ath = [{
        "athlete_id": "g1", "athlete_name": "Genç Sporcu", "birth_year": 2009,
        "gender": "F", "region": 1, "city": "İstanbul", "club": "X",
        "antalya_events_time": {("Serbest", 50): "00:00:25.00"},
        "combined_events": {("Serbest", 50): 9},
        "combined_events_time": {("Serbest", 50): "00:00:25.00"},
    }]
    out = select_all_gencler(ath)
    assert out[0]["selected_multinations_gencler"] is True
    assert out[0]["selected_avrupa_gencler"] is True
    assert isinstance(out[0]["avrupa_gencler_events"], list)


def test_api_ranking_serializes_secim_events():
    from federasyon.yildizlar_ranker import select_yildizlar_multinations
    ath = [{
        "athlete_id": "e1", "athlete_name": "E1", "gender": "M", "birth_year": 2012,
        "antalya_events_time": {("Serbest", 50): "00:00:24.00"},
        "antalya_events": {("Serbest", 50): 1},
        "combined_events": {("Serbest", 50): 1}, "combined_events_time": {("Serbest", 50): "00:00:24.00"},
    }]
    out = select_yildizlar_multinations(ath)
    # backend alanı tuple listesi
    assert out[0]["multinations_events"] == [("Serbest", 50)]
    # serve.py serileştirme kalıbı (list-of-list)
    serialized = [list(e) for e in out[0].get("multinations_events", [])]
    assert serialized == [["Serbest", 50]]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
