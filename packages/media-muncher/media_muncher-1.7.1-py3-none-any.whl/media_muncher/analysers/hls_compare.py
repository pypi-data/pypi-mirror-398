from m3u8 import Playlist
from media_muncher.handlers.hls import HLSHandler
from media_muncher.analysers.hls import HlsAnalyser


class HlsProfileComparer:
    def __init__(self) -> None:
        self.compatibility_map = {}

    def set_target(self, source_handler: HLSHandler):
        self.source_handler = source_handler
        self.source_analyser = HlsAnalyser(source_handler)

    def check_candidate(self, candidate_handler: HLSHandler):
        self.candidate_handler = candidate_handler
        self.candidate_analyser = HlsAnalyser(candidate_handler)

        # Reinitialise the compatibility map
        self.compatibility_map = {}

        # 1. Check renditions
        self._check_renditions()

        # Analyse results
        self._analyse_compatibility()
        return self.compatibility_map

    def _check_renditions(self):
        # TODO - rewrite all to use the Handler directly

        mappings = []
        matched_candidate_renditions = []

        # Check based on source renditions
        for playlist in self.source_handler.document.playlists:
            rendition_map = dict(source=playlist)
            mappings.append(rendition_map)

            source_codecs = self._extract_codecs(playlist)

            # Find all renditions that match the source rendition
            matching_playlists = [
                cand_playlist
                for cand_playlist in self.candidate_handler.document.playlists
                if self._extract_codecs(cand_playlist) == source_codecs
            ]
            matched_candidate_renditions.extend(matching_playlists)
            rendition_map["candidates"] = matching_playlists

        self.compatibility_map["renditions"] = mappings

        # List remaining renditions
        leftover = []
        for playlist in self.candidate_handler.document.playlists:
            if playlist not in matched_candidate_renditions:
                leftover.append(playlist)
        self.compatibility_map["additional_renditions"] = leftover

    def _analyse_compatibility(self):
        is_compatible = True

        if "renditions" in self.compatibility_map:
            for rendition in self.compatibility_map["renditions"]:
                if len(rendition["candidates"]) == 0:
                    is_compatible = False
                    break

        self.compatibility_map["is_compatible"] = is_compatible

    @staticmethod
    def _extract_codecs(playlist: Playlist):
        codecstring = playlist.stream_info.codecs
        return sorted([cs.strip().lower() for cs in codecstring.split(",")])
