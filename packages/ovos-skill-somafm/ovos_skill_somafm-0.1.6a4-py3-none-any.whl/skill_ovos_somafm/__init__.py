from os.path import join, dirname
from typing import Iterable

import radiosoma
from ovos_utils import classproperty
from ovos_utils.parse import fuzzy_match
from ovos_utils.process_utils import RuntimeRequirements
from ovos_utils.ocp import MediaType, PlaybackType, MediaEntry, Playlist
from ovos_workshop.decorators.ocp import ocp_search, ocp_featured_media
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill


class SomaFMSkill(OVOSCommonPlaybackSkill):

    def __init__(self, *args, **kwargs):
        super().__init__(supported_media=[MediaType.MUSIC, MediaType.RADIO, MediaType.GENERIC],
                         skill_icon=join(dirname(__file__), "res", "somafm.png"),
                         skill_voc_filename="somafm_skill",
                         *args, **kwargs)

    def initialize(self):
        # register with OCP to help classifier pick MediaType.RADIO
        self.register_ocp_keyword(MediaType.RADIO,
                                  "radio_station", [s.title for s in radiosoma.get_stations()])
        self.register_ocp_keyword(MediaType.RADIO,
                                  "radio_streaming_provider",
                                  ["SomaFM", "Soma FM", "Soma"])

    @classproperty
    def runtime_requirements(self):
        return RuntimeRequirements(internet_before_load=True,
                                   network_before_load=True,
                                   gui_before_load=False,
                                   requires_internet=True,
                                   requires_network=True,
                                   requires_gui=False,
                                   no_internet_fallback=False,
                                   no_network_fallback=False,
                                   no_gui_fallback=True)

    @ocp_featured_media()
    def featured_media(self) -> Playlist:
        pl = Playlist(media_type=MediaType.RADIO,
                      title="SomaFM (All stations)",
                      playback=PlaybackType.AUDIO,
                      image="https://somafm.com/img3/LoneDJsquare400.jpg",
                      skill_id=self.skill_id,
                      artist="SomaFM",
                      match_confidence=100,
                      skill_icon=self.skill_icon)
        pl += [MediaEntry(media_type=MediaType.RADIO,
                          uri=ch.direct_stream,
                          title=ch.title,
                          playback=PlaybackType.AUDIO,
                          image=ch.image,
                          skill_id=self.skill_id,
                          artist="SomaFM",
                          match_confidence=90,
                          length=-1,  # live stream
                          skill_icon=self.skill_icon)
               for ch in radiosoma.get_stations()]
        return pl

    @ocp_search()
    def ocp_somafm_playlist(self, phrase: str, media_type: MediaType) -> Iterable[Playlist]:
        phrase = self.remove_voc(phrase, "radio")
        if self.voc_match(phrase, "somafm", exact=media_type != MediaType.RADIO):
            yield self.featured_media()

    @ocp_search()
    def search_somafm(self, phrase, media_type) -> Iterable[MediaEntry]:
        base_score = 0

        if media_type == MediaType.RADIO:
            base_score += 20
        else:
            base_score -= 30

        if self.voc_match(phrase, "radio"):
            base_score += 10
            phrase = self.remove_voc(phrase, "radio")

        if self.voc_match(phrase, "somafm"):
            base_score += 30  # explicit request
            phrase = self.remove_voc(phrase, "somafm")

        for ch in radiosoma.get_stations():
            score = round(base_score + fuzzy_match(ch.title.lower(), phrase.lower()) * 100)
            if score < 60:
                continue
            yield MediaEntry(media_type=MediaType.RADIO,
                             uri=ch.direct_stream,
                             title=ch.title,
                             playback=PlaybackType.AUDIO,
                             image=ch.image,
                             skill_id=self.skill_id,
                             artist="SomaFM",
                             match_confidence=min(100, score),
                             length=-1,  # live stream
                             skill_icon=self.skill_icon)


if __name__ == "__main__":
    from ovos_utils.messagebus import FakeBus
    from ovos_utils.log import LOG

    LOG.set_level("DEBUG")

    s = SomaFMSkill(bus=FakeBus(), skill_id="t.fake")
    for r in s.ocp_somafm_playlist("somafm", MediaType.RADIO):
        print(r)
        # Playlist(title='SomaFM (All stations)', artist='SomaFM', position=0, image='https://somafm.com/img3/LoneDJsquare400.jpg', match_confidence=100, skill_id='t.fake', skill_icon='/home/miro/PycharmProjects/OCPSkills/skill-ovos-somafm/somafm.png', playback=<PlaybackType.AUDIO: 2>, media_type=<MediaType.RADIO: 7>)
    for r in s.search_somafm("secret agent", MediaType.RADIO):
        print(r)
        # MediaEntry(uri='http://ice2.somafm.com/beatblender-128-mp3', title='Beat Blender', artist='SomaFM', match_confidence=62, skill_id='t.fake', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.RADIO: 7>, length=-1, image='https://api.somafm.com/logos/512/beatblender512.png', skill_icon='/home/miro/PycharmProjects/OCPSkills/skill-ovos-somafm/somafm.png', javascript='')
        # MediaEntry(uri='http://ice2.somafm.com/deepspaceone-128-mp3', title='Deep Space One', artist='SomaFM', match_confidence=66, skill_id='t.fake', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.RADIO: 7>, length=-1, image='https://api.somafm.com/logos/512/deepspaceone512.png', skill_icon='/home/miro/PycharmProjects/OCPSkills/skill-ovos-somafm/somafm.png', javascript='')
        # MediaEntry(uri='http://ice2.somafm.com/illstreet-128-mp3', title='Illinois Street Lounge', artist='SomaFM', match_confidence=61, skill_id='t.fake', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.RADIO: 7>, length=-1, image='https://api.somafm.com/logos/512/illstreet512.png', skill_icon='/home/miro/PycharmProjects/OCPSkills/skill-ovos-somafm/somafm.png', javascript='')
        # MediaEntry(uri='http://ice2.somafm.com/secretagent-128-mp3', title='Secret Agent', artist='SomaFM', match_confidence=100, skill_id='t.fake', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.RADIO: 7>, length=-1, image='https://api.somafm.com/logos/512/secretagent512.png', skill_icon='/home/miro/PycharmProjects/OCPSkills/skill-ovos-somafm/somafm.png', javascript='')
