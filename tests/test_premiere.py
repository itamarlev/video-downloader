import unittest
from unittest.mock import patch
import yt_dlp
from core import downloader


def video(codec, height, name, audio='none'):
    return dict(format_id=name, url=f'https://example.com/{name}.mp4',
                ext='mp4', vcodec=codec, acodec=audio, height=height)


class PremiereTests(unittest.TestCase):
    def select(self, formats, quality='720p'):
        opts = downloader.build_ydl_opts(quality, '.', premiere_compatible=True)
        opts.update(quiet=True, no_warnings=True)
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.process_ie_result(dict(id='test', title='test', extractor='test', formats=formats), download=False)

    def test_prefers_h264_over_av1_and_vp9(self):
        info = self.select([
            video('avc1.64001f', 720, 'h264'),
            video('av01.0.05M.08', 720, 'av1'),
            video('vp9', 720, 'vp9'),
            dict(format_id='aac', url='https://example.com/audio.m4a', ext='m4a',
                 vcodec='none', acodec='mp4a.40.2'),
        ])
        self.assertEqual([f['format_id'] for f in info['requested_formats']], ['h264', 'aac'])

    def test_combined_stream_and_quality_cap(self):
        info = self.select([video('avc1.64001f', 360, 'low', 'mp4a.40.2'),
                            video('avc1.64001f', 1080, 'high', 'mp4a.40.2')])
        self.assertEqual(info['format_id'], 'low')

    def test_never_falls_back_to_incompatible_or_over_cap(self):
        for formats in ([video('av01', 720, 'av1', 'mp4a.40.2')],
                        [video('avc1.64001f', 1080, 'high', 'mp4a.40.2')],
                        [video('avc1.64001f', 720, 'opus', 'opus')]):
            with self.subTest(formats=formats), self.assertRaises(yt_dlp.utils.ExtractorError):
                self.select(formats)

    def test_all_quality_choices(self):
        for quality in downloader.QUALITY_OPTIONS[:-1]:
            with self.subTest(quality=quality):
                self.assertEqual(self.select([video('avc1.64001f', 360, 'ok', 'mp4a.40.2')], quality)['format_id'], 'ok')

    def test_separate_filename_and_audio_unchanged(self):
        opts = downloader.build_ydl_opts('720p', '.', premiere_compatible=True)
        self.assertIn('Premiere H264', opts['outtmpl'])
        self.assertEqual(downloader.build_ydl_opts('Audio Only (MP3)', '.', premiere_compatible=True),
                         downloader.build_ydl_opts('Audio Only (MP3)', '.'))

    def test_missing_ffmpeg(self):
        with patch('core.downloader.shutil.which', return_value=None):
            with self.assertRaisesRegex(downloader.DownloadError, 'FFmpeg not found'):
                downloader.open_client('720p', '.', premiere_compatible=True)

    def test_info_only_not_restricted(self):
        opts = downloader.build_ydl_opts('720p', '.', for_info_only=True, premiere_compatible=True)
        self.assertNotIn('vcodec^=avc1', opts['format'])


if __name__ == '__main__':
    unittest.main()
