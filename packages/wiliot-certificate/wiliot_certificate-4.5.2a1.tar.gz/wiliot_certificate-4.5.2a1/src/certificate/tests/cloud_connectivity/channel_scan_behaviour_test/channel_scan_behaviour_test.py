from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
from certificate.ag.wlt_types_ag import OUTPUT_POWER_2_4_MAX
import certificate.cert_common as cert_common
import certificate.cert_mqtt as cert_mqtt
import certificate.cert_config as cert_config
import certificate.cert_gw_sim as cert_gw_sim
import os
import math
import pandas as pd
import plotly.express as px
import time
from collections import defaultdict


# DEFINES
CHANNELS = [37, 38, 39]  # channel to check in DUT
DEFAULT_WAIT_TIME = 5  # How much extra time to wait after the transmition is over
SCAN_TEST_INDICATOR = get_random_hex_str(6)  # Unique identifier for the pkt sent
ADV_DURATION = 20  # How long to transmit to the DUT
# cmd_ble_sm defines
BLE_SIM_RADIO_1MBPS = 1
BLE_SIM_SINGLE_UNIQUE_PKT = 1
SCAN_DUPLICATES = 1
BLE_SIM_ADV_37_38_39 = 0
UNIQUE_CONTENT = 1
PPS = 20

# HELPER FUNCTIONS


def interpolation(payload, next_payload, channel_pkt_counter):
    cur_pkt_num = int.from_bytes(bytes.fromhex(payload[-8:]), byteorder="little")
    next_pkt_num = int.from_bytes(bytes.fromhex(next_payload[-8:]), byteorder="little")
    diff = next_pkt_num - cur_pkt_num
    if diff > 1:
        channel_pkt_counter += diff - 1
    return channel_pkt_counter


def compute_channels_windows(timeline_df):
    """
    Build contiguous channel windows: for each run of the same channel, return (channel, start_ts, end_ts).
    The result is and array of these windows. For exmaple: [(37, 0.004), (38, 0.038), .....]
    """
    windows = []
    current_ch = timeline_df.iloc[0]['channel']
    start_ts = timeline_df.iloc[0]['timestamp_ms']

    for _, row in timeline_df.iloc[1:].iterrows():
        if row['channel'] != current_ch:
            windows.append((current_ch, start_ts))
            current_ch = row['channel']
            start_ts = row['timestamp_ms']

    windows.append((current_ch, start_ts))
    return windows


def compute_listening_stats(windows):
    per_channel_starts = defaultdict(list)
    avg_start_to_start_ms = {}

    for ch, start_ts in windows:
        per_channel_starts[ch].append(start_ts)

    # Calculating the avg for each channel of the compelte cycle it does (that inclues all channels listend to)
    for ch in CHANNELS:
        starts = sorted(per_channel_starts.get(ch, []))
        start_gaps = [curr - prev for prev, curr in zip(starts, starts[1:])]
        avg_start_to_start_ms[ch] = sum(start_gaps) / len(start_gaps) if start_gaps else 0

    return avg_start_to_start_ms


def analyze_listening_timeline(test, all_pkts_received_from_tester, num_of_sent_pkts, start_timestamp_ms):
    """
    Build a timeline graph and print channel listening percentages.
    """
    timeline_entries = []
    channel_pkt_counter = defaultdict(int)
    channel_cards = []

    # Parse data into {ts, channel pairs} - X and Y axis
    all_pkts_received_from_tester = sorted(all_pkts_received_from_tester, key=lambda pkt: float(pkt.get(TIMESTAMP)))
    for idx, pkt in enumerate(all_pkts_received_from_tester):
        payload = pkt.get(PAYLOAD)
        channel = int(payload[-10:-8], 16)
        time_stamp = float(pkt.get(TIMESTAMP))

        # Add dropped packts in the middle of listening windows to neglect it from not scanning window
        # Those complitions will not apear in the graph, only on % calculations
        # If there are packets dropped at the ed of a window - it can not detect that
        if idx < len(all_pkts_received_from_tester) - 1:
            next_pkt = all_pkts_received_from_tester[idx + 1]
            next_channel = int(next_pkt.get(PAYLOAD)[-10:-8], 16)
            if next_channel == channel:
                next_payload = next_pkt.get(PAYLOAD)
                channel_pkt_counter[channel] = interpolation(payload, next_payload, channel_pkt_counter[channel])

        timeline_entries.append({'timestamp_ms': time_stamp, 'channel': channel})
        channel_pkt_counter[channel] += 1

    if not timeline_entries or not channel_pkt_counter:
        utPrint("No packets were received; skipping timeline graph", "RED")
        test.rc = TEST_FAILED
        test.reason = "No packets were received in all channels"
        return

    # Create graph
    timeline_df = pd.DataFrame(timeline_entries).sort_values('timestamp_ms')
    timeline_df['relative_time_s'] = (timeline_df['timestamp_ms'] - start_timestamp_ms) / 1000
    timeline_path = os.path.join(ARTIFACTS_DIR, test.dir, 'channel_scan_behavior.html')
    color_map = {37: "#1f77b4", 38: "#ff7f0e", 39: "#2ca02c"}
    timeline_fig = px.scatter(timeline_df, x='relative_time_s', y='channel', color='channel', color_discrete_map=color_map,
                              title='Channel scanning timeline',
                              labels={'relative_time_s': 'Time (s)', 'channel': 'Scanning Channel'})
    timeline_fig.update_layout(height=350, yaxis=dict(tickmode='array', tickvals=CHANNELS, ticktext=[str(ch) for ch in CHANNELS],
                               range=[min(CHANNELS) - 0.5, max(CHANNELS) + 0.5]))
    timeline_fig.update_coloraxes(showscale=False)

    # Build contiguous channel windows and compute averages
    windows = compute_channels_windows(timeline_df[['timestamp_ms', 'channel']])
    avg_start_to_start_ms = compute_listening_stats(windows)
    positive_start_gaps = [v for v in avg_start_to_start_ms.values() if v > 0]
    avg_cycle_from_starts_ms = sum(positive_start_gaps) / len(positive_start_gaps) if positive_start_gaps else None

    # Build per-channel cards for the HTML summary
    for ch in CHANNELS:
        pct_recievied_vs_sent = channel_pkt_counter[ch] * 100 / num_of_sent_pkts
        cycle_ms = int(avg_start_to_start_ms[ch]) if int(avg_start_to_start_ms[ch]) != 0 else None
        duration_ms = int(pct_recievied_vs_sent * cycle_ms / 100) if cycle_ms else None
        # pct_recievied_vs_sent: packets on this channel / sent; cycle_ms: avg start-to-start; duration_ms: pct_recievied_vs_sent * cycle
        channel_cards.append({"title": f"Channel {ch}",
                              "pct_recievied_vs_sent": round(pct_recievied_vs_sent, 4),
                              "cycle_ms": cycle_ms,
                              "duration_ms": duration_ms})

    # Not‑scanning stats are the residual to 100% after the three channels
    # Interpolation smooths dropouts so this reflects actual not-scannning time
    observed_pct_recievied_vs_sent = sum(card["pct_recievied_vs_sent"] for card in channel_cards)
    channel_cards.append({"title": "Not scanning",
                          "pct_recievied_vs_sent": max(0, round(100 - observed_pct_recievied_vs_sent, 2)),
                          "cycle_ms": int(avg_cycle_from_starts_ms) if avg_cycle_from_starts_ms else None,
                          "duration_ms": int((max(0, round(100 - observed_pct_recievied_vs_sent, 2)) *
                                              (int(avg_cycle_from_starts_ms) if avg_cycle_from_starts_ms else 0)) / 100)
                          if avg_cycle_from_starts_ms else None})

    # Embed summary text into the HTML alongside the plot
    cards_html = "".join([
        (
            "<div style='flex:1; min-width:200px; border:1px solid #ddd; border-radius:8px; padding:12px; background:#fafafa;'>"
            f"<div style='font-weight:700; margin-bottom:8px;'>{card['title']}</div>"
            f"<div>% scanning: {card['pct_recievied_vs_sent']}% </div>"
            f"<div>Scan cycle: {card['cycle_ms']} ms </div>"
            f"<div>Scan duration: {card['duration_ms']} ms </div>"
            "</div>"
        )
        for card in channel_cards
    ])
    summary_html = (
        "<div style=\"font-family: Arial, sans-serif; font-size:16px; line-height:1.5; margin-bottom:16px;\">"
        f"<h3 style=\"margin:0 0 8px 0;\">Scan Summary</h3>"
        f"<div style='display:flex; gap:12px; margin-top:12px; flex-wrap:wrap;'>{cards_html}</div>"
        "</div>"
    )
    full_html = f"<html><head></head><body>{summary_html}{timeline_fig.to_html(full_html=False, include_plotlyjs='cdn')}</body></html>"
    with open(timeline_path, "w") as f:
        f.write(full_html)


def run(test):
    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    # Setup
    phase_run_print("Running scan channel behavior")
    all_messages_in_test = []
    all_data_pkts = []
    all_data_pkts_from_tester = []

    # Prepairation for advertisment
    cert_config.gw_action(test, f'{cert_gw_sim.BLE_SIM_INIT} 1', TESTER)  # Move BLE to sim mode
    delay = math.floor(1000 / PPS)
    upload_wait_time = test.dut.upload_wait_time + DEFAULT_WAIT_TIME
    payload = cert_common.generate_adv_payload(SCAN_TEST_INDICATOR, unique_pkt=True)

    # Transmitting packets on all channels
    utPrint(f"Transmitting in parallel on all 3 main channels for {ADV_DURATION} seconds", "WARNING")
    num_of_sent_pkts = ADV_DURATION * PPS
    strat_trans_time_ms = time.time() * 1000

    cert_config.gw_action(test, f'{cert_gw_sim.BLE_SIM} '
                          f'{payload} {SCAN_DUPLICATES} {OUTPUT_POWER_2_4_MAX} '
                          f'{BLE_SIM_ADV_37_38_39} {delay} {BLE_SIM_RADIO_1MBPS} {num_of_sent_pkts} {BLE_SIM_SINGLE_UNIQUE_PKT}',
                          TESTER)
    mqtt_scan_wait(test, ADV_DURATION + upload_wait_time)

    all_data_pkts_from_tester.extend(cert_mqtt.get_all_data_pkts(test.get_mqttc_by_target(DUT), indicator=SCAN_TEST_INDICATOR))
    all_data_pkts.extend(cert_mqtt.get_all_data_pkts(test.get_mqttc_by_target(DUT)))
    all_messages_in_test.extend(test.get_mqttc_by_target(DUT)._userdata[PKTS].data)

    cert_config.gw_action(test, f'{cert_gw_sim.BLE_SIM_INIT} 0', TESTER)
    time.sleep(1)  # To allow all packets to show in the log

    cert_mqtt.generate_log_file(test, 'channel_scan', target=DUT)
    cert_mqtt.generate_log_file(test, 'channel_scan_tester', target=TESTER)

    analyze_listening_timeline(test, all_data_pkts_from_tester, num_of_sent_pkts, strat_trans_time_ms)

    test = cert_common.wiliot_pkts_validation(test, all_messages_in_test, all_data_pkts)

    return cert_common.test_epilog(test)
