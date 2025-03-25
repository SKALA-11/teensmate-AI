from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from pytube import Playlist
import os

'''
!pip instal youtube_transcript_api
!pip install pytube
'''

class YouTubeTranscriptExtractor:
    def __init__(self, output_folder="transcripts"):
        self.output_folder = output_folder
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

    def extract_transcripts_from_playlist(self, playlist_url):
        """
        주어진 유튜브 재생 목록에서 자막을 추출하여 텍스트 파일로 저장합니다.
        """
        playlist = Playlist(playlist_url)
        print(f"총 영상 수: {len(playlist.video_urls)}")

        for video_url in playlist.video_urls:
            try:
                video_id = self.extract_video_id(video_url)  # 비디오 ID 추출
                self._extract_and_save_transcript(video_id, video_url)
            except Exception as e:
                print(f"URL 처리 오류({video_url}): {e}")

    def _extract_and_save_transcript(self, video_id, video_url):
        """
        주어진 비디오 ID에 대해 자막을 추출하고 파일로 저장합니다.
        """
        # 파일 경로 설정
        file_path = os.path.join(self.output_folder, f"{video_id}.txt")

        if os.path.exists(file_path):
            print(f"자막 파일이 이미 존재합니다: {file_path}")
            return

        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])
            transcript = ' '.join([t['text'] for t in transcript_list])  # 자막 결합

            # 자막을 텍스트 파일로 저장
            file_path = os.path.join(self.output_folder, f"{video_id}.txt")
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(transcript)

            print(f"자막 저장 완료: {file_path}")

        except TranscriptsDisabled:
            print(f"자막 제공 안됨: {video_url}")
        except Exception as e:
            print(f"자막 추출 오류({video_url}): {e}")

    def extract_video_id(self, video_url):
        """
        유튜브 비디오 URL에서 video_id를 추출합니다.
        """
        if 'youtu.be' in video_url:
            return video_url.split('/')[-1]
        elif 'youtube.com/watch' in video_url:
            return video_url.split('v=')[-1]
        else:
            raise ValueError("유효하지 않은 URL 형식입니다.")
