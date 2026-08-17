from tracker import DOOR_ZONE_CX, DOOR_ZONE_CY, Track


def test_direction_approaching():
    t = Track(1, (400, 240), (0, 0, 0, 0))
    for i in range(15):
        alpha = i / 14
        t.history.append((int(400 + alpha*(DOOR_ZONE_CX-400)),
                          int(240 + alpha*(DOOR_ZONE_CY-240))))
    assert t.direction() == "approaching_door"

def test_direction_entering():
    t = Track(1, (DOOR_ZONE_CX, DOOR_ZONE_CY), (0, 0, 0, 0))
    for i in range(15):
        t.history.append((DOOR_ZONE_CX + i*15, DOOR_ZONE_CY + i*8))
    assert t.direction() == "entering_apartment"