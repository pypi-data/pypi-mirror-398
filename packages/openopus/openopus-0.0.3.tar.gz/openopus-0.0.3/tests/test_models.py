from openopus.models import Composer, Work


def test_composer_fields():
    c = Composer(id=1, name="Johann Sebastian Bach",
                 birth="1685-01-01", death="1750-01-01", epoch="Baroque",
                 portrait="")
    assert c.id == 1
    assert c.name == "Johann Sebastian Bach"
    assert c.birth == "1685-01-01"
    assert c.death == "1750-01-01"
    assert c.epoch == "Baroque"
    assert c.portrait == ""


def test_work_fields():
    w = Work(id=1, title="Goldberg Variations, BWV.988", genre="Keyboard")
    assert w.id == 1
    assert w.title == "Goldberg Variations, BWV.988"
    assert w.genre == "Keyboard"
