# -*- coding: utf-8 -*-
"""
Ferdi (kulüpsüz) sporcuların bölge tespiti.

Bug: LXF'te "Ferdi" CLUB düğümü Excel kulüp haritasında bulunmadığı için
parser region=0 / city='Unknown' bırakıyordu. Oysa CLUB düğümü Türk plaka
kodunu (region="07" = Antalya) taşıyor. Bu bilgi bölge seçimine girmiyordu,
dolayısıyla Aliye Pazar gibi ferdi sporcular hiçbir bölge kotasına dahil
edilmiyordu.
"""
import zipfile

import pytest

from modules.lxf_parser import parse_lxf_file

_LENEX = """<?xml version="1.0" encoding="UTF-8"?>
<LENEX version="3.0">
  <MEETS>
    <MEET name="Test" city="Antalya" nation="TUR">
      <COURSE>LCM</COURSE>
      <SESSIONS>
        <SESSION number="1" date="2026-01-01">
          <EVENTS>
            <EVENT eventid="1" gender="F">
              <SWIMSTYLE distance="800" stroke="FREE" />
            </EVENT>
          </EVENTS>
        </SESSION>
      </SESSIONS>
      <CLUBS>
        <CLUB clubid="24" name="Ferdi" shortname="Ferdi" nation="TUR" region="07">
          <ATHLETES>
            <ATHLETE athleteid="190" lastname="Pazar" firstname="Aliye"
                     gender="F" birthdate="2013-03-08">
              <RESULTS>
                <RESULT eventid="1" swimtime="00:10:19.78" place="40" />
              </RESULTS>
            </ATHLETE>
          </ATHLETES>
        </CLUB>
      </CLUBS>
    </MEET>
  </MEETS>
</LENEX>
"""


@pytest.fixture
def ferdi_lxf(tmp_path):
    path = tmp_path / "ferdi.lxf"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("ferdi.lef", _LENEX)
    return str(path)


def test_ferdi_athlete_gets_region_from_club_plate_code(ferdi_lxf):
    athletes, _ = parse_lxf_file(ferdi_lxf)

    pazar = next(a for a in athletes if a["lastname"] == "Pazar")

    # region="07" plaka kodu = Antalya = 3. bölge
    assert pazar["region"] == 3
    assert pazar["city"] == "Antalya"
