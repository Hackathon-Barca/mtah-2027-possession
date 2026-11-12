"""The aggregate-facts report, on synthetic files. No test reads match data."""

import io
import sys

from nolook import starter_facts


def test_tracking_stats_counts_ball_slots_and_objects(tmp_path):
    raw = tmp_path / "atd.txt"
    raw.write_text(
        "1:0.1,0.2,1.0;NaN,NaN,NaN;0.3,0.4,2.0:0.5,0.5,0.0\n"
        "2:NaN,NaN,NaN;NaN,NaN,NaN;0.3,0.4,2.0:NaN,NaN,NaN\n"
        "3:0.1,0.2,1.0;0.2,0.2,1.0;0.3,0.4,2.0:0.6,0.5,0.0\n"
        "\n")
    stats = starter_facts.tracking_stats(raw)
    assert stats["records"] == 3
    assert stats["slots"] == [3]
    assert stats["with_ball"] == 2
    assert stats["max_objects"] == 3
    assert abs(stats["mean_objects"] - 2.0) < 1e-9


def test_smart_tagging_counts_codes_and_groups(tmp_path):
    xml = tmp_path / "tags.xml"
    xml.write_text(
        "<file><ALL_INSTANCES>"
        "<instance><code>SET PIECES</code>"
        "<label><group>Team</group><text>N/A</text></label>"
        "<label><group>Type</group><text>Throw-in</text></label></instance>"
        "<instance><code>BUILD UP</code>"
        "<label><group>Team</group><text>Barcelona</text></label></instance>"
        "</ALL_INSTANCES></file>")
    codes, teams, types = starter_facts.smart_tagging_counts(xml)
    assert codes == {"SET PIECES": 1, "BUILD UP": 1}
    assert teams == {"N/A": 1, "Barcelona": 1}
    assert types == {"Throw-in": 1}


def test_compare_counts_flags_missing_and_unexpected_keys():
    out = io.StringIO()
    assert starter_facts.compare_counts("code", {"A": 2}, {"A": 2}, out)
    assert not starter_facts.compare_counts("code", {"A": 2, "B": 1}, {"A": 2}, out)
    assert not starter_facts.compare_counts("code", {}, {"A": 2}, out)
    assert "MISMATCH" in out.getvalue()


def test_metadata_summary_reports_schema_and_extra_ball_channels(tmp_path):
    meta = tmp_path / "atd.xml"
    meta.write_text(
        '<Main xmlns="urn:example"><Teams><Team id="T1"><Name>Secret FC</Name></Team></Teams>'
        '<Channels><Channel id="x"/><Channel id="y"/><Channel id="speed"/></Channels>'
        '<PlayerChannels><PlayerChannel id="p1_x" channelId="x"/></PlayerChannels>'
        '<SplitRegister><BallChannelRef channelId="x"/><BallChannelRef channelId="y"/>'
        '<BallChannelRef channelId="s"/>'
        '<BallChannelRef channelId="ball_status"/></SplitRegister></Main>')
    summary = starter_facts.metadata_summary(meta)
    assert summary["channels"] == ["speed", "x", "y"]
    assert summary["player_channels"] == ["x"]
    assert summary["ball_extra"] == ["ball_status"]
    assert summary["state_hints"] == ["ball_status"]
    assert summary["tags"]["Team"] == 1

    out = io.StringIO()
    meta_text = "\n".join(str(value) for value in summary.values())
    starter_facts.say(meta_text, out)
    assert "Secret FC" not in out.getvalue()  # element text never reaches the report


def test_machine_facts_are_available():
    assert starter_facts.total_ram_gb() > 0
    if sys.platform != "win32":
        assert starter_facts.peak_rss_mb() > 0
    out = io.StringIO()
    starter_facts.report_machine(out)
    assert "python" in out.getvalue()
