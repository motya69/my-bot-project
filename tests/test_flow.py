from bot.dialogs import FLOW

def test_start_has_two_branches():
    node = FLOW["start"]
    assert "next_by_button" in node
    mapping = node["next_by_button"]
    assert mapping["Шины"] == "t_entry"
    assert mapping["Диски"] == "w_entry"

def test_tires_branch_has_render_node():
    assert "t_show_offers" in FLOW
    assert FLOW["t_show_offers"]["action"] == "render_tire_offers"

def test_wheels_branch_has_render_node():
    assert "w_show_offers" in FLOW
    assert FLOW["w_show_offers"]["action"] == "render_wheels_offers"
